"""Smarti API Tracker

Independent SQLite-backed usage analytics for SmartiAI Agent for Windows.

Backend:
- SQLite database in app data directory
- Fast non-blocking logging via background writer thread
- Retention cleanup
- Analytics helpers

UI:
- PyQt6 dashboard widget/page with:
  - top summary cards
  - weekly/monthly mini bar charts
  - provider/model split
  - peak usage hour
  - recent API calls table

Core integration (minimal):
    from .api_tracker import log_api_call

    def _log_usage(self, model_name, usage_dict):
        if not usage_dict or not model_name:
            return
        log_api_call(model_name, usage_dict)

If you later want richer telemetry, log_api_call also accepts optional kwargs:
    provider=..., duration_ms=..., success=..., error_text=...
"""

from __future__ import annotations

import datetime as _dt
import os
import queue
import sqlite3
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "APILogEntry",
    "APITracker",
    "APITrafficPage",
    "get_data_dir",
    "get_db_path",
    "get_tracker",
    "log_api_call",
    "get_analytics_snapshot",
    "build_api_tracker_page",
    "track_usage",
]

APP_NAME = "Smarti"
DB_FILENAME = "smarti_api_logs.db"
DEFAULT_RETENTION_DAYS = 90
DEFAULT_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
DEFAULT_REFRESH_INTERVAL_MS = 2000
_MAX_QUEUE_SIZE = 10000


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_data_dir() -> Path:
    """Return a writable app data directory for Smarti."""
    env_dir = os.environ.get("SMARTI_DATA_DIR")
    if env_dir:
        base = Path(env_dir).expanduser()
    else:
        if sys.platform.startswith("win"):
            appdata = os.environ.get("APPDATA")
            if appdata:
                base = Path(appdata) / APP_NAME
            else:
                base = Path.home() / "AppData" / "Roaming" / APP_NAME
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / APP_NAME
        else:
            xdg = os.environ.get("XDG_DATA_HOME")
            if xdg:
                base = Path(xdg) / APP_NAME
            else:
                base = Path.home() / ".local" / "share" / APP_NAME

    try:
        base.mkdir(parents=True, exist_ok=True)
        return base
    except Exception:
        fallback = Path(tempfile.gettempdir()) / APP_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_db_path() -> Path:
    return get_data_dir() / DB_FILENAME


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class APILogEntry:
    id: int
    ts: str
    model_name: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_ms: int
    success: int
    error_text: str


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

def _now_ts() -> float:
    return time.time()


def _start_of_day_ts(dt: Optional[_dt.datetime] = None) -> float:
    dt = dt or _dt.datetime.now()
    sod = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return sod.timestamp()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _truncate_text(text: Any, max_len: int = 1000) -> str:
    s = str(text or "")
    return s[:max_len]


def _normalize_model_name(model_name: Any) -> str:
    return str(model_name or "").strip() or "unknown"


def _infer_provider(model_name: str, explicit_provider: Optional[str] = None) -> str:
    if explicit_provider:
        return str(explicit_provider).strip() or "unknown"
    name = (model_name or "").strip().lower()
    if "gemini" in name:
        return "Gemini"
    if "gpt" in name or "openai" in name:
        return "OpenAI"
    if "claude" in name or "anthropic" in name:
        return "Anthropic"
    if "llama" in name or "ollama" in name:
        return "Local"
    if "mistral" in name:
        return "Mistral"
    if "cohere" in name:
        return "Cohere"
    if "deepseek" in name:
        return "DeepSeek"
    return "unknown"


def _usage_total(usage_dict: Dict[str, Any]) -> int:
    if not isinstance(usage_dict, dict):
        return 0
    if "total" in usage_dict:
        return _safe_int(usage_dict.get("total"), 0)
    return _safe_int(usage_dict.get("prompt"), 0) + _safe_int(usage_dict.get("completion"), 0)


def _usage_prompt(usage_dict: Dict[str, Any]) -> int:
    return _safe_int(usage_dict.get("prompt"), 0) if isinstance(usage_dict, dict) else 0


def _usage_completion(usage_dict: Dict[str, Any]) -> int:
    return _safe_int(usage_dict.get("completion"), 0) if isinstance(usage_dict, dict) else 0


class APITracker:
    """SQLite-backed usage tracker with async write queue."""

    _instance: Optional["APITracker"] = None
    _instance_lock = threading.Lock()

    def __init__(
        self,
        db_path: Optional[Path] = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        cleanup_interval_seconds: int = DEFAULT_CLEANUP_INTERVAL_SECONDS,
    ) -> None:
        self.db_path = Path(db_path) if db_path else get_db_path()
        self.retention_days = int(retention_days)
        self.cleanup_interval_seconds = int(cleanup_interval_seconds)

        self._queue: "queue.Queue[Tuple[str, str, int, int, int, int, int, str, float]]" = queue.Queue(
            maxsize=_MAX_QUEUE_SIZE
        )
        self._stop_event = threading.Event()
        self._db_lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        self._last_cleanup_at = 0.0
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name="SmartiAPITrackerWriter",
            daemon=True,
        )

        self._init_db()
        self._writer_thread.start()

    @classmethod
    def instance(cls) -> "APITracker":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # ----- DB plumbing -----

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30,
            check_same_thread=False,
            isolation_level=None,  # explicit transactions when needed
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn

    def _ensure_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def _init_db(self) -> None:
        with self._db_lock:
            conn = self._ensure_conn()
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    completion_tokens INTEGER NOT NULL DEFAULT 0,
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    success INTEGER NOT NULL DEFAULT 1,
                    error_text TEXT NOT NULL DEFAULT ''
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_ts ON api_logs(ts DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_provider_ts ON api_logs(provider, ts DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_model_ts ON api_logs(model_name, ts DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_logs_success_ts ON api_logs(success, ts DESC);")
            conn.commit()
            self._cleanup_if_due(force=True)

    def shutdown(self, wait: bool = True) -> None:
        self._stop_event.set()
        if wait and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=3.0)
        with self._db_lock:
            if self._conn is not None:
                try:
                    self._conn.commit()
                except Exception:
                    pass
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    # ----- Logging -----

    def log_api_call(
        self,
        model_name: str,
        usage_dict: Optional[Dict[str, Any]] = None,
        *,
        provider: Optional[str] = None,
        duration_ms: Optional[int] = None,
        success: Optional[bool] = True,
        error_text: Optional[str] = None,
    ) -> None:
        """Queue a usage record. Non-blocking in the normal path."""
        model_name = _normalize_model_name(model_name)
        if not model_name:
            return

        usage_dict = usage_dict or {}
        prompt_tokens = _usage_prompt(usage_dict)
        completion_tokens = _usage_completion(usage_dict)
        total_tokens = _usage_total(usage_dict)
        provider_name = _infer_provider(model_name, provider)
        duration = max(0, _safe_int(duration_ms, 0))
        success_int = 1 if (True if success is None else bool(success)) else 0
        error = _truncate_text(error_text, 1000)

        payload = (
            model_name,
            provider_name,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            duration,
            success_int,
            error,
            _now_ts(),
        )

        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            # Rare fallback: write synchronously so logs are not lost.
            self._insert_batch([payload])

    def _writer_loop(self) -> None:
        batch: List[Tuple[str, str, int, int, int, int, int, str, float]] = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.25)
                batch.append(item)
                self._queue.task_done()
            except queue.Empty:
                pass

            now = time.time()
            should_flush = bool(batch) and (
                len(batch) >= 100 or (now - last_flush) >= 0.5 or self._stop_event.is_set()
            )
            if should_flush:
                self._insert_batch(batch)
                batch.clear()
                last_flush = now

        if batch:
            self._insert_batch(batch)

    def _insert_batch(self, rows: Sequence[Tuple[str, str, int, int, int, int, int, str, float]]) -> None:
        if not rows:
            return

        with self._db_lock:
            conn = self._ensure_conn()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                conn.executemany(
                    """
                    INSERT INTO api_logs(
                        model_name,
                        provider,
                        prompt_tokens,
                        completion_tokens,
                        total_tokens,
                        duration_ms,
                        success,
                        error_text,
                        ts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    rows,
                )
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                # single retry using a fresh connection
                try:
                    fresh = self._connect()
                    fresh.execute("BEGIN IMMEDIATE;")
                    fresh.executemany(
                        """
                        INSERT INTO api_logs(
                            model_name,
                            provider,
                            prompt_tokens,
                            completion_tokens,
                            total_tokens,
                            duration_ms,
                            success,
                            error_text,
                            ts
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        rows,
                    )
                    fresh.commit()
                    fresh.close()
                except Exception:
                    pass

        self._cleanup_if_due()

    def _cleanup_if_due(self, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self._last_cleanup_at) < self.cleanup_interval_seconds:
            return

        cutoff = now - (self.retention_days * 86400)
        with self._db_lock:
            conn = self._ensure_conn()
            try:
                conn.execute("DELETE FROM api_logs WHERE ts < ?;", (cutoff,))
                conn.commit()
                self._last_cleanup_at = now
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

    # ----- Query helpers -----

    def _fetchall(self, query: str, params: Sequence[Any] = ()) -> List[sqlite3.Row]:
        with self._db_lock:
            conn = self._ensure_conn()
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            return list(rows)

    def _fetchone(self, query: str, params: Sequence[Any] = ()) -> Optional[sqlite3.Row]:
        rows = self._fetchall(query, params)
        return rows[0] if rows else None

    def get_recent_entries(self, limit: int = 5) -> List[APILogEntry]:
        rows = self._fetchall(
            """
            SELECT id, ts, model_name, provider, prompt_tokens, completion_tokens,
                   total_tokens, duration_ms, success, error_text
            FROM api_logs
            ORDER BY ts DESC, id DESC
            LIMIT ?;
            """,
            (int(limit),),
        )
        return [
            APILogEntry(
                id=_safe_int(row["id"]),
                ts=_dt.datetime.fromtimestamp(float(row["ts"])).isoformat(sep=" ", timespec="seconds"),
                model_name=str(row["model_name"]),
                provider=str(row["provider"]),
                prompt_tokens=_safe_int(row["prompt_tokens"]),
                completion_tokens=_safe_int(row["completion_tokens"]),
                total_tokens=_safe_int(row["total_tokens"]),
                duration_ms=_safe_int(row["duration_ms"]),
                success=_safe_int(row["success"]),
                error_text=str(row["error_text"] or ""),
            )
            for row in rows
        ]

    def get_rpm_10m(self) -> float:
        since = _now_ts() - 600
        row = self._fetchone("SELECT COUNT(*) AS c FROM api_logs WHERE ts >= ?;", (since,))
        count = _safe_int(row["c"] if row else 0)
        return round(count / 10.0, 2)

    def get_today_summary(self) -> Dict[str, int]:
        since = _start_of_day_ts()
        row = self._fetchone(
            """
            SELECT
                COUNT(*) AS requests,
                COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            WHERE ts >= ?;
            """,
            (since,),
        )
        return {
            "requests": _safe_int(row["requests"] if row else 0),
            "tokens": _safe_int(row["tokens"] if row else 0),
        }

    def get_month_summary(self) -> Dict[str, int]:
        since = _now_ts() - (30 * 86400)
        row = self._fetchone(
            """
            SELECT
                COUNT(*) AS requests,
                COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            WHERE ts >= ?;
            """,
            (since,),
        )
        return {
            "requests": _safe_int(row["requests"] if row else 0),
            "tokens": _safe_int(row["tokens"] if row else 0),
        }

    def get_weekly_summary(self) -> List[Dict[str, Any]]:
        since = _now_ts() - (7 * 86400)
        rows = self._fetchall(
            """
            SELECT
                date(ts, 'unixepoch', 'localtime') AS day,
                COUNT(*) AS requests,
                COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            WHERE ts >= ?
            GROUP BY day
            ORDER BY day ASC;
            """,
            (since,),
        )
        return [
            {"day": str(row["day"]), "requests": _safe_int(row["requests"]), "tokens": _safe_int(row["tokens"])}
            for row in rows
        ]

    def get_monthly_summary(self) -> List[Dict[str, Any]]:
        since = _now_ts() - (30 * 86400)
        rows = self._fetchall(
            """
            SELECT
                date(ts, 'unixepoch', 'localtime') AS day,
                COUNT(*) AS requests,
                COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            WHERE ts >= ?
            GROUP BY day
            ORDER BY day ASC;
            """,
            (since,),
        )
        return [
            {"day": str(row["day"]), "requests": _safe_int(row["requests"]), "tokens": _safe_int(row["tokens"])}
            for row in rows
        ]

    def get_hourly_profile(self, lookback_days: int = 30) -> List[Dict[str, Any]]:
        since = _now_ts() - (int(lookback_days) * 86400)
        rows = self._fetchall(
            """
            SELECT
                CAST(strftime('%H', ts, 'unixepoch', 'localtime') AS INTEGER) AS hour,
                COUNT(*) AS requests,
                COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            WHERE ts >= ?
            GROUP BY hour
            ORDER BY hour ASC;
            """,
            (since,),
        )
        by_hour = {
            _safe_int(row["hour"]): {
                "requests": _safe_int(row["requests"]),
                "tokens": _safe_int(row["tokens"]),
            }
            for row in rows
        }
        return [
            {
                "hour": hour,
                "requests": by_hour.get(hour, {}).get("requests", 0),
                "tokens": by_hour.get(hour, {}).get("tokens", 0),
            }
            for hour in range(24)
        ]

    def get_provider_split(self) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT provider, COUNT(*) AS requests, COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            GROUP BY provider
            ORDER BY requests DESC, provider ASC;
            """
        )
        total_requests = sum(_safe_int(row["requests"]) for row in rows) or 1
        return [
            {
                "provider": str(row["provider"]),
                "requests": _safe_int(row["requests"]),
                "tokens": _safe_int(row["tokens"]),
                "percent": round((_safe_int(row["requests"]) * 100.0) / total_requests, 2),
            }
            for row in rows
        ]

    def get_model_split(self) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT model_name, COUNT(*) AS requests, COALESCE(SUM(total_tokens), 0) AS tokens
            FROM api_logs
            GROUP BY model_name
            ORDER BY requests DESC, model_name ASC;
            """
        )
        total_requests = sum(_safe_int(row["requests"]) for row in rows) or 1
        return [
            {
                "model_name": str(row["model_name"]),
                "requests": _safe_int(row["requests"]),
                "tokens": _safe_int(row["tokens"]),
                "percent": round((_safe_int(row["requests"]) * 100.0) / total_requests, 2),
            }
            for row in rows
        ]

    def get_gemini_share(self) -> Dict[str, float]:
        rows = self._fetchall("SELECT provider, COUNT(*) AS requests FROM api_logs GROUP BY provider;")
        total = sum(_safe_int(row["requests"]) for row in rows) or 1
        gemini = 0
        for row in rows:
            provider = str(row["provider"]).strip().lower()
            if provider == "gemini" or "gemini" in provider:
                gemini += _safe_int(row["requests"])
        gemini_percent = round((gemini * 100.0) / total, 2)
        return {"gemini_percent": gemini_percent, "other_percent": round(100.0 - gemini_percent, 2)}

    def get_peak_usage_hour(self) -> Dict[str, Any]:
        rows = self._fetchall(
            """
            SELECT CAST(strftime('%H', ts, 'unixepoch', 'localtime') AS INTEGER) AS hour,
                   COUNT(*) AS requests
            FROM api_logs
            GROUP BY hour
            ORDER BY requests DESC, hour ASC
            LIMIT 1;
            """
        )
        if not rows:
            return {"hour": None, "requests": 0}
        return {"hour": _safe_int(rows[0]["hour"]), "requests": _safe_int(rows[0]["requests"])}

    def export_snapshot(self) -> Dict[str, Any]:
        return {
            "rpm_10m": self.get_rpm_10m(),
            "today": self.get_today_summary(),
            "month": self.get_month_summary(),
            "weekly": self.get_weekly_summary(),
            "monthly": self.get_monthly_summary(),
            "hourly_profile": self.get_hourly_profile(),
            "provider_split": self.get_provider_split(),
            "model_split": self.get_model_split(),
            "gemini_share": self.get_gemini_share(),
            "peak_usage_hour": self.get_peak_usage_hour(),
            "recent": [entry.__dict__ for entry in self.get_recent_entries(5)],
        }


def get_tracker() -> APITracker:
    return APITracker.instance()


def log_api_call(
    model_name: str,
    usage_dict: Optional[Dict[str, Any]] = None,
    *,
    provider: Optional[str] = None,
    duration_ms: Optional[int] = None,
    success: Optional[bool] = True,
    error_text: Optional[str] = None,
) -> None:
    get_tracker().log_api_call(
        model_name=model_name,
        usage_dict=usage_dict,
        provider=provider,
        duration_ms=duration_ms,
        success=success,
        error_text=error_text,
    )


def track_usage(model_name: str, usage_dict: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
    """Compatibility alias."""
    log_api_call(model_name, usage_dict, **kwargs)


def get_analytics_snapshot() -> Dict[str, Any]:
    return get_tracker().export_snapshot()


# ---------------------------------------------------------------------------
# UI (PyQt6)
# ---------------------------------------------------------------------------

QT_AVAILABLE = False
QtCore = QtGui = QtWidgets = None  # type: ignore[assignment]

try:
    from PyQt6 import QtCore as _QtCore
    from PyQt6 import QtGui as _QtGui
    from PyQt6 import QtWidgets as _QtWidgets

    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QT_AVAILABLE = True
except Exception:
    QT_AVAILABLE = False


def _format_int(n: Any) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"


def _chart_palette_color(widget: Any) -> Any:
    pal = widget.palette()
    return pal.highlight().color()


if QT_AVAILABLE:

    class _SnapshotWorker(QtCore.QObject):  # type: ignore[misc]
        snapshot_ready = QtCore.pyqtSignal(object)
        failed = QtCore.pyqtSignal(str)

        def run(self) -> None:
            try:
                snapshot = get_analytics_snapshot()
                self.snapshot_ready.emit(snapshot)
            except Exception as exc:
                self.failed.emit(str(exc))


    class _MiniBarChart(QtWidgets.QWidget):  # type: ignore[misc]
        def __init__(self, title: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
            super().__init__(parent)
            self._title = title
            self._rows: List[Dict[str, Any]] = []
            self._value_key = "requests"
            self.setMinimumHeight(170)
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )

        def set_rows(self, rows: List[Dict[str, Any]], value_key: str = "requests") -> None:
            self._rows = list(rows or [])
            self._value_key = value_key
            self.update()

        def paintEvent(self, event: Any) -> None:  # noqa: N802
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            rect = self.rect().adjusted(10, 10, -10, -10)
            painter.fillRect(self.rect(), self.palette().window())

            title_rect = QtCore.QRect(rect.x(), rect.y(), rect.width(), 20)
            painter.setPen(self.palette().text().color())
            painter.drawText(title_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, self._title)

            chart_rect = QtCore.QRect(rect.x(), rect.y() + 28, rect.width(), rect.height() - 28)
            if not self._rows:
                painter.drawText(chart_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "No data")
                return

            values = [max(0, _safe_int(r.get(self._value_key, 0))) for r in self._rows]
            max_v = max(values) if values else 1
            max_v = max(max_v, 1)

            bar_gap = 6
            n = len(values)
            bar_width = max(8, int((chart_rect.width() - (bar_gap * max(0, n - 1))) / max(1, n)))
            bar_width = min(bar_width, 40)

            accent = _chart_palette_color(self)
            for idx, row in enumerate(self._rows):
                v = max(0, _safe_int(row.get(self._value_key, 0)))
                bar_h = int((chart_rect.height() - 24) * (v / max_v))
                x = chart_rect.x() + idx * (bar_width + bar_gap)
                y = chart_rect.bottom() - bar_h - 16
                bar_rect = QtCore.QRect(x, y, bar_width, bar_h)

                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(accent)
                painter.drawRoundedRect(bar_rect, 4, 4)

                label = str(row.get("day", row.get("hour", idx)))
                painter.setPen(self.palette().text().color())
                painter.drawText(
                    QtCore.QRect(x - 6, chart_rect.bottom() - 12, bar_width + 12, 12),
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                    label[-10:],
                )
                painter.drawText(
                    QtCore.QRect(x - 6, y - 14, bar_width + 12, 12),
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                    str(v),
                )


    class APITrafficPage(QtWidgets.QWidget):  # type: ignore[misc]
        """Qt dashboard page for Smarti API usage."""

        def __init__(self, parent: Optional[QtWidgets.QWidget] = None, refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS):
            super().__init__(parent)
            self._refresh_interval_ms = int(refresh_interval_ms)
            self._worker_thread: Optional[QtCore.QThread] = None
            self._worker: Optional[_SnapshotWorker] = None
            self._build_ui()
            self._timer = QtCore.QTimer(self)
            self._timer.setInterval(self._refresh_interval_ms)
            self._timer.timeout.connect(self.refresh_async)
            self.refresh_async()
            self._timer.start()

        def _build_ui(self) -> None:
            self.setObjectName("APITrafficPage")
            root = QtWidgets.QVBoxLayout(self)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(10)

            header = QtWidgets.QHBoxLayout()
            title_box = QtWidgets.QVBoxLayout()
            title = QtWidgets.QLabel("API Tracker")
            title.setObjectName("trackerTitle")
            subtitle = QtWidgets.QLabel("Live usage, analytics, and recent calls")
            subtitle.setObjectName("trackerSubtitle")
            title_box.addWidget(title)
            title_box.addWidget(subtitle)
            header.addLayout(title_box)
            header.addStretch(1)
            self.status_label = QtWidgets.QLabel("Ready")
            self.status_label.setObjectName("trackerStatus")
            header.addWidget(self.status_label)
            root.addLayout(header)

            cards = QtWidgets.QGridLayout()
            cards.setSpacing(10)
            self.card_rpm = self._card("RPM (10m)", "0")
            self.card_today = self._card("Today", "0")
            self.card_month = self._card("This Month", "0")
            cards.addWidget(self.card_rpm, 0, 0)
            cards.addWidget(self.card_today, 0, 1)
            cards.addWidget(self.card_month, 0, 2)
            root.addLayout(cards)

            body = QtWidgets.QHBoxLayout()
            body.setSpacing(10)

            left = QtWidgets.QVBoxLayout()
            left.setSpacing(10)
            self.week_chart = _MiniBarChart("Weekly usage")
            self.month_chart = _MiniBarChart("Monthly usage")
            left.addWidget(self.week_chart)
            left.addWidget(self.month_chart)

            right = QtWidgets.QVBoxLayout()
            right.setSpacing(10)
            self.provider_box = self._info_panel("Provider split")
            self.peak_box = self._info_panel("Peak hour")
            right.addWidget(self.provider_box)
            right.addWidget(self.peak_box)

            body.addLayout(left, 3)
            body.addLayout(right, 2)
            root.addLayout(body, 1)

            section = QtWidgets.QLabel("Recent API calls")
            section.setObjectName("trackerSection")
            root.addWidget(section)

            self.recent_table = QtWidgets.QTableWidget(0, 8)
            self.recent_table.setHorizontalHeaderLabels(
                ["Time", "Model", "Provider", "Prompt", "Completion", "Total", "ms", "OK"]
            )
            self.recent_table.horizontalHeader().setStretchLastSection(True)
            self.recent_table.verticalHeader().setVisible(False)
            self.recent_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.recent_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.recent_table.setAlternatingRowColors(True)
            self.recent_table.setWordWrap(False)
            root.addWidget(self.recent_table, 2)

            self._apply_style()

        def _apply_style(self) -> None:
            palette = self.palette()
            bg = palette.window().color().name()
            fg = palette.windowText().color().name()
            accent = palette.highlight().color().name()
            muted = palette.mid().color().name()

            self.setStyleSheet(
                f"""
                QWidget#APITrafficPage {{
                    background: {bg};
                    color: {fg};
                }}
                QLabel#trackerTitle {{
                    font-size: 22px;
                    font-weight: 700;
                }}
                QLabel#trackerSubtitle {{
                    color: {muted};
                }}
                QLabel#trackerStatus {{
                    padding: 4px 10px;
                    border-radius: 10px;
                    background: rgba(127, 127, 127, 0.15);
                }}
                QLabel#trackerSection {{
                    font-size: 14px;
                    font-weight: 600;
                    margin-top: 4px;
                }}
                QFrame#trackerCard {{
                    border: 1px solid rgba(127, 127, 127, 0.25);
                    border-radius: 16px;
                    background: rgba(127, 127, 127, 0.08);
                }}
                QLabel#trackerCardTitle {{
                    font-size: 12px;
                    color: {muted};
                }}
                QLabel#trackerCardValue {{
                    font-size: 30px;
                    font-weight: 700;
                }}
                QFrame#infoCard {{
                    border: 1px solid rgba(127, 127, 127, 0.20);
                    border-radius: 16px;
                    background: rgba(127, 127, 127, 0.06);
                }}
                QLabel#miniTitle {{
                    font-size: 13px;
                    font-weight: 600;
                }}
                QLabel#miniText {{
                    color: {muted};
                }}
                QTableWidget {{
                    border: 1px solid rgba(127, 127, 127, 0.18);
                    border-radius: 12px;
                }}
                QHeaderView::section {{
                    background: rgba(127, 127, 127, 0.10);
                    padding: 6px;
                    border: none;
                }}
                """
            )

        def _card(self, title: str, value: str) -> QtWidgets.QFrame:
            frame = QtWidgets.QFrame()
            frame.setObjectName("trackerCard")
            layout = QtWidgets.QVBoxLayout(frame)
            layout.setContentsMargins(14, 14, 14, 14)
            label = QtWidgets.QLabel(title)
            label.setObjectName("trackerCardTitle")
            value_label = QtWidgets.QLabel(value)
            value_label.setObjectName("trackerCardValue")
            layout.addWidget(label)
            layout.addStretch(1)
            layout.addWidget(value_label)
            frame._value_label = value_label  # type: ignore[attr-defined]
            return frame

        def _info_panel(self, title: str) -> QtWidgets.QFrame:
            frame = QtWidgets.QFrame()
            frame.setObjectName("infoCard")
            layout = QtWidgets.QVBoxLayout(frame)
            layout.setContentsMargins(14, 14, 14, 14)
            t = QtWidgets.QLabel(title)
            t.setObjectName("miniTitle")
            v = QtWidgets.QLabel("—")
            v.setObjectName("miniText")
            v.setWordWrap(True)
            layout.addWidget(t)
            layout.addWidget(v)
            layout.addStretch(1)
            frame._value_label = v  # type: ignore[attr-defined]
            return frame

        def start_auto_refresh(self) -> None:
            self._timer.start()

        def stop_auto_refresh(self) -> None:
            self._timer.stop()

        def refresh_async(self) -> None:
            if self._worker_thread is not None:
                return  # avoid overlapping refreshes

            self._worker_thread = QtCore.QThread(self)
            self._worker = _SnapshotWorker()
            self._worker.moveToThread(self._worker_thread)

            self._worker_thread.started.connect(self._worker.run)
            self._worker.snapshot_ready.connect(self._on_snapshot_ready)
            self._worker.failed.connect(self._on_snapshot_failed)

            self._worker.snapshot_ready.connect(self._cleanup_worker)
            self._worker.failed.connect(self._cleanup_worker)

            self._worker_thread.start()

        @QtCore.pyqtSlot(object)
        def _on_snapshot_ready(self, snapshot: Dict[str, Any]) -> None:
            self.status_label.setText("Live")
            self.card_rpm._value_label.setText(str(snapshot.get("rpm_10m", 0)))  # type: ignore[attr-defined]
            self.card_today._value_label.setText(_format_int(snapshot.get("today", {}).get("requests", 0)))  # type: ignore[attr-defined]
            self.card_month._value_label.setText(_format_int(snapshot.get("month", {}).get("requests", 0)))  # type: ignore[attr-defined]

            provider_split = snapshot.get("provider_split", []) or []
            if provider_split:
                lines = [
                    f"{row['provider']}: {row['percent']}% ({_format_int(row['requests'])} req)"
                    for row in provider_split[:6]
                ]
            else:
                lines = ["No data yet"]
            self.provider_box._value_label.setText("\n".join(lines))  # type: ignore[attr-defined]

            peak = snapshot.get("peak_usage_hour", {}) or {}
            hour = peak.get("hour")
            if hour is None:
                peak_text = "No activity yet"
            else:
                peak_text = f"Usually busiest around {int(hour):02d}:00 with {_format_int(peak.get('requests', 0))} requests"
            self.peak_box._value_label.setText(peak_text)  # type: ignore[attr-defined]

            self.week_chart.set_rows(snapshot.get("weekly", []) or [], "requests")
            self.month_chart.set_rows(snapshot.get("monthly", []) or [], "requests")
            self._fill_recent(snapshot.get("recent", []) or [])

        @QtCore.pyqtSlot(str)
        def _on_snapshot_failed(self, message: str) -> None:
            self.status_label.setText(f"Error: {message[:120]}")

        @QtCore.pyqtSlot()
        def _cleanup_worker(self) -> None:
            if self._worker_thread is not None:
                self._worker_thread.quit()
                self._worker_thread.wait(1500)
            self._worker_thread = None
            self._worker = None

        def _fill_recent(self, rows: List[Dict[str, Any]]) -> None:
            self.recent_table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                values = [
                    row.get("ts", ""),
                    row.get("model_name", ""),
                    row.get("provider", ""),
                    _format_int(row.get("prompt_tokens", 0)),
                    _format_int(row.get("completion_tokens", 0)),
                    _format_int(row.get("total_tokens", 0)),
                    _format_int(row.get("duration_ms", 0)),
                    "Yes" if _safe_int(row.get("success", 0)) else "No",
                ]
                for c, value in enumerate(values):
                    item = QtWidgets.QTableWidgetItem(str(value))
                    self.recent_table.setItem(r, c, item)
            self.recent_table.resizeColumnsToContents()


    def build_api_tracker_page(parent: Optional[QtWidgets.QWidget] = None) -> APITrafficPage:
        return APITrafficPage(parent=parent)

else:

    class APITrafficPage:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("PyQt6 is required for the Smarti API tracker UI page.")


    def build_api_tracker_page(parent: Optional[Any] = None) -> Any:
        raise ImportError("PyQt6 is required for the Smarti API tracker UI page.")


if __name__ == "__main__":
    # Simple smoke test
    log_api_call("gemini-2.5-pro", {"prompt": 10, "completion": 20, "total": 30})
    print(get_analytics_snapshot())

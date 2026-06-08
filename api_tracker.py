"""
Smarti API Tracker
Independent SQLite-based usage analytics.
"""

import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timedelta

_DB_LOCK = threading.Lock()

DB_FILE = Path(__file__).resolve().parent / "smarti_api_logs.db"


def _get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize():
    with _DB_LOCK:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model_name TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0
        )
        """)

        conn.commit()
        conn.close()


initialize()


def cleanup_old_records(days=90):
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    with _DB_LOCK:
        conn = _get_conn()

        conn.execute(
            "DELETE FROM api_logs WHERE timestamp < ?",
            (cutoff,)
        )

        conn.commit()
        conn.close()


def track_usage(model_name, usage_dict):
    if not usage_dict or not model_name:
        return

    try:
        with _DB_LOCK:
            conn = _get_conn()

            conn.execute("""
            INSERT INTO api_logs
            (
                timestamp,
                model_name,
                prompt_tokens,
                completion_tokens,
                total_tokens
            )
            VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                str(model_name),
                int(usage_dict.get("prompt", 0)),
                int(usage_dict.get("completion", 0)),
                int(usage_dict.get("total", 0))
            ))

            conn.commit()
            conn.close()

        cleanup_old_records()

    except Exception:
        pass


def get_today_stats():
    today = datetime.now().strftime("%Y-%m-%d")

    conn = _get_conn()

    row = conn.execute("""
    SELECT
        COUNT(*) as requests,
        COALESCE(SUM(total_tokens),0) as tokens
    FROM api_logs
    WHERE date(timestamp)=?
    """, (today,)).fetchone()

    conn.close()

    return {
        "requests": row["requests"],
        "tokens": row["tokens"]
    }


def get_month_stats():
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()

    conn = _get_conn()

    row = conn.execute("""
    SELECT
        COUNT(*) as requests,
        COALESCE(SUM(total_tokens),0) as tokens
    FROM api_logs
    WHERE timestamp >= ?
    """, (cutoff,)).fetchone()

    conn.close()

    return {
        "requests": row["requests"],
        "tokens": row["tokens"]
    }


def get_weekly_stats():
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()

    conn = _get_conn()

    rows = conn.execute("""
    SELECT
        date(timestamp) as day,
        COUNT(*) as requests,
        COALESCE(SUM(total_tokens),0) as tokens
    FROM api_logs
    WHERE timestamp >= ?
    GROUP BY date(timestamp)
    ORDER BY day
    """, (cutoff,)).fetchall()

    conn.close()

    return [dict(r) for r in rows]


def get_top_models(limit=10):
    conn = _get_conn()

    rows = conn.execute("""
    SELECT
        model_name,
        COUNT(*) as requests,
        SUM(total_tokens) as tokens
    FROM api_logs
    GROUP BY model_name
    ORDER BY tokens DESC
    LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    return [dict(r) for r in rows]


def get_recent_calls(limit=5):
    conn = _get_conn()

    rows = conn.execute("""
    SELECT
        timestamp,
        model_name,
        total_tokens
    FROM api_logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    return [dict(r) for r in rows]

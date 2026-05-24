"""Shared imports, constants, and small helpers for Smarti."""
import os
import json
import subprocess
import webbrowser
import platform
import shutil
import urllib.parse
import zipfile
import threading
import time
import glob
import shlex
import unicodedata
import concurrent.futures
import requests
import re
import logging
import warnings
import sys
import io
import base64
import ast
import mimetypes
import importlib.util
import smtplib
import imaplib
import email
import html
import difflib
from email import policy as email_policy
from email.header import decode_header
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import formataddr, formatdate, getaddresses, make_msgid, parsedate_to_datetime
import copy
import hashlib
import winsound
import tempfile
import uuid
import ctypes
from datetime import datetime, timedelta
from pathlib import Path
import urllib3

LITELLM_INSTALLED = importlib.util.find_spec("litellm") is not None
KEYRING_INSTALLED = importlib.util.find_spec("keyring") is not None

def get_url(b64_str):
    return base64.b64decode(b64_str).decode('utf-8')

def get_keyring_module():
    if not KEYRING_INSTALLED:
        return None
    try:
        import keyring
        return keyring
    except Exception:
        return None

URL_OPENROUTER = "aHR0cHM6Ly9vcGVucm91dGVyLmFpL2FwaS92MQ=="
URL_GROQ = "aHR0cHM6Ly9hcGkuZ3JvcS5jb20vb3BlbmFpL3Yx"
URL_GEMINI_GEN = "aHR0cHM6Ly9nZW5lcmF0aXZlbGFuZ3VhZ2UuZ29vZ2xlYXBpcy5jb20vdjFiZXRhL21vZGVscy8="
URL_ANTHROPIC = "aHR0cHM6Ly9hcGkuYW50aHJvcGljLmNvbS92MS9tZXNzYWdlcw=="
URL_NPM = "aHR0cHM6Ly9yZWdpc3RyeS5ucG1qcy5vcmcvLS92MS9zZWFyY2g/dGV4dD0="
URL_TAVILY = "aHR0cHM6Ly9hcGkudGF2aWx5LmNvbS9zZWFyY2g="
URL_DDG = "aHR0cHM6Ly9kdWNrZHVja2dvLmNvbS8/cT0="
URL_GEMINI_MODELS = "aHR0cHM6Ly9nZW5lcmF0aXZlbGFuZ3VhZ2UuZ29vZ2xlYXBpcy5jb20vdjFiZXRhL21vZGVscz9rZXk9"
URL_OPENAI_MODELS = "aHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MS9tb2RlbHM="
URL_OPENROUTER_MODELS = "aHR0cHM6Ly9vcGVucm91dGVyLmFpL2FwaS92MS9tb2RlbHM="
URL_GROQ_MODELS = "aHR0cHM6Ly9hcGkuZ3JvcS5jb20vb3BlbmFpL3YxL21vZGVscw=="
URL_CLAWHUB_API = "aHR0cHM6Ly9jbGF3aHViLmFpL2FwaS92MQ=="

warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
WIN_CREATE_NO_WINDOW = 0x08000000
SMARTI_BROWSER_DEBUG_PORT = 49223
SMARTI_BROWSER_PROFILE_NAME = "SmartiChromeProfile"

class SmartiCancelled(Exception):
    pass

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QScrollArea, QFrame, QMenu, QLineEdit, 
                             QCheckBox, QFormLayout, QSizePolicy, QMessageBox, QComboBox, QSystemTrayIcon, QSlider, QStackedWidget, QStyleOptionButton, QStyle, QGraphicsOpacityEffect, QGraphicsEffect, QGraphicsDropShadowEffect, QFileDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QElapsedTimer, QRectF
from PyQt6.QtGui import QIcon, QFont, QPixmap, QCursor, QColor, QPainter, QPainterPath, QPen, QMovie, QTextOption, QPalette, QTextCursor, QLinearGradient, QBrush, QImage

DOCX_INSTALLED = importlib.util.find_spec("docx") is not None
PDF_INSTALLED = importlib.util.find_spec("PyPDF2") is not None
BS4_INSTALLED = importlib.util.find_spec("bs4") is not None
MARKDOWN_INSTALLED = importlib.util.find_spec("markdown") is not None
PILLOW_INSTALLED = importlib.util.find_spec("PIL") is not None
SPEECH_INSTALLED = importlib.util.find_spec("speech_recognition") is not None and importlib.util.find_spec("keyboard") is not None
TTS_INSTALLED = importlib.util.find_spec("gtts") is not None and importlib.util.find_spec("pygame") is not None

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(filename=os.path.join(APP_DIR, 'smarti_agent.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

SETTINGS_FILE = os.path.join(APP_DIR, "smarti_settings.json")
USAGE_FILE = os.path.join(APP_DIR, "smarti_usage.json")
MEMORY_FILE = os.path.join(APP_DIR, "smarti_memory.json")
MEMORY_EXPORT_FILE = os.path.join(APP_DIR, "smarti_memory.md")
TOOLS_DIR = os.path.join(APP_DIR, "custom_tools")
MCP_TOOLS_DIR = os.path.join(APP_DIR, "mcp_tools")
SKILLS_DIR = os.path.join(APP_DIR, "skills")
ASSETS_DIR = os.path.join(APP_DIR, "assets")
OUTPUTS_DIR = os.path.join(APP_DIR, "Smarti_Outputs")
MCP_CONFIG_FILE = os.path.join(APP_DIR, "mcp_config.json")
SKILL_LOG_FILE = os.path.join(APP_DIR, "smarti_skills.log")
AUDIT_LOG_FILE = os.path.join(APP_DIR, "smarti_audit.log")
SETTINGS_SCHEMA_VERSION = 2

def ensure_ui_svg_asset(filename, svg_text):
    try:
        os.makedirs(ASSETS_DIR, exist_ok=True)
        path = os.path.join(ASSETS_DIR, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg_text)
        return path.replace("\\", "/")
    except Exception:
        return ""

SENSITIVE_SETTING_KEYS = {
    "gemini_api_key", "openai_api_key", "anthropic_api_key", "openrouter_api_key",
    "groq_api_key", "tavily_api_key", "email_password", "email_address"
}
KEYRING_SERVICE = "SmartiAI"
SECRET_PREFIX = "DPAPI:"

SAFE_TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".py", ".pyw", ".log", ".ini", ".yaml",
    ".yml", ".html", ".css", ".js", ".ts", ".xml"
}

BLOCKED_WRITE_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".ps1", ".psm1", ".vbs", ".jscript",
    ".scr", ".com", ".msi", ".reg", ".lnk", ".hta", ".jar"
}

EXECUTABLE_OPEN_EXTENSIONS = BLOCKED_WRITE_EXTENSIONS | {
    ".appref-ms", ".cpl", ".msc", ".pif", ".scf", ".url", ".ws", ".wsf",
    ".wsh", ".ps2", ".ps2xml", ".psc1", ".psc2", ".msh", ".msh1",
    ".msh2", ".mshxml", ".msh1xml", ".msh2xml"
}

SAFE_OPEN_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log", ".ini", ".yaml", ".yml",
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg",
    ".mp3", ".wav", ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".html", ".htm", ".css", ".xml"
}

DEFAULT_MCP_ENV_ALLOWLIST = [
    "PATH", "Path", "PATHEXT", "SystemRoot", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "APPDATA", "LOCALAPPDATA", "USERPROFILE",
    "PROGRAMFILES", "PROGRAMFILES(X86)", "ProgramData", "PROCESSOR_ARCHITECTURE"
]

HIGH_RISK_TOOLS = {
    "system_command", "create_python_tool", "install_mcp", "run_mcp",
    "browser_automation", "computer_automation", "email_manager",
    "capture_screen", "save_screenshot_to_disk", "save_text_file",
    "read_local_document", "install_skill",
    "install_skill_requirements", "run_skill",
    "system_manager", "file_manager", "screen_manager",
    "automation_manager", "extension_manager", "memory_manager"
}

CAPABILITY_LABELS = {
    "file_read": "קריאת קבצים מקומיים",
    "file_search": "חיפוש קבצים ותוכן",
    "file_write": "כתיבת קבצים",
    "shell": "הרצת פקודות מערכת",
    "python_tool_create": "יצירת כלי מותאם אישית",
    "python_tool_run": "הרצת כלי מותאם אישית",
    "mcp_search": "חיפוש כלים חיצוניים",
    "mcp_install": "התקנת כלים חיצוניים",
    "mcp_run": "הרצת כלים חיצוניים",
    "skill_search": "חיפוש Skills",
    "skill_install": "התקנת Skills",
    "skill_run": "הרצת Skills",
    "network": "גישה לאינטרנט",
    "browser_open": "פתיחת דפדפן גלוי",
    "file_open": "פתיחת קבצים ותיקיות",
    "software_run": "הרצת תוכנה וקבצים",
    "browser_automation": "אוטומציית דפדפן",
    "computer_control": "אוטומציית מחשב דרך עץ הנגישות של Windows",
    "email": "דואר אלקטרוני",
    "screenshot": "צילום מסך",
    "software_open": "פתיחת תוכנות",
    "background_task": "משימות רקע",
    "audio": "שמע והקראה"
}

DEFAULT_POLICY_MATRIX = {
    "file_read": "ask",
    "file_search": "allow",
    "file_write": "ask",
    "shell": "ask",
    "python_tool_create": "ask",
    "python_tool_run": "ask",
    "mcp_search": "allow",
    "mcp_install": "ask",
    "mcp_run": "ask",
    "skill_search": "allow",
    "skill_install": "ask",
    "skill_run": "ask",
    "network": "ask",
    "browser_open": "allow",
    "file_open": "ask",
    "software_run": "ask",
    "browser_automation": "ask",
    "computer_control": "ask",
    "email": "ask",
    "screenshot": "ask",
    "software_open": "allow",
    "background_task": "ask",
    "audio": "allow"
}

AUTONOMY_PROFILES = {
    "locked_down": {
        "permission_level": 1,
        "policy_matrix": copy.deepcopy(DEFAULT_POLICY_MATRIX),
        "raw_shell_requires_approval": True,
        "marketplace_install_requires_approval": True,
        "require_approval_for_cloud_upload": True
    },
    "balanced": {
        "permission_level": 2,
        "policy_matrix": copy.deepcopy(DEFAULT_POLICY_MATRIX),
        "raw_shell_requires_approval": True,
        "marketplace_install_requires_approval": True,
        "require_approval_for_cloud_upload": True
    },
    "max_autonomy": {
        "permission_level": 3,
        "policy_matrix": {cap: "allow" for cap in DEFAULT_POLICY_MATRIX},
        "raw_shell_requires_approval": False,
        "marketplace_install_requires_approval": False,
        "require_approval_for_cloud_upload": False
    }
}

POLICY_ACTIONS = {"allow", "ask", "deny"}

DESTRUCTIVE_COMMAND_HINTS = [
    "remove-item", " rmdir", " del ", " rm ", " erase ", "format ",
    "diskpart", "bcdedit", "reg delete", "set-executionpolicy", "takeown ",
    "icacls ", "cipher /w", "stop-computer", "restart-computer"
]

SELF_PROTECTED_NAMES = {
    "mcp_tools", "custom_tools", "skills", "assets", "smarti_outputs",
    "smarti_core.pyw", "smarti_settings.json", "smarti_memory.json",
    "smarti_memory.md", "smarti_agent.log"
}

_CURRENT_SETTINGS_REF = {"settings": None}

def redact_sensitive_text(text, settings=None):
    if text is None: return ""
    safe = str(text)
    settings = settings or {}
    for key in SENSITIVE_SETTING_KEYS:
        value = str(settings.get(key, "") or "")
        if len(value) >= 4:
            safe = safe.replace(value, f"[REDACTED:{key}]")
    safe = re.sub(r'(?i)(api[_-]?key|token|password|secret|authorization)["\':=\s]+[^\s,;"]+', r'\1=[REDACTED]', safe)
    safe = re.sub(r'(?i)(key=)[^&\s]+', r'\1[REDACTED]', safe)
    safe = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED:email]', safe)
    safe = re.sub(r'C:\\Users\\[^\\\r\n]+', r'C:\\Users\\[USER]', safe)
    return safe

class SmartiRedactingFilter(logging.Filter):
    def filter(self, record):
        settings = _CURRENT_SETTINGS_REF.get("settings") or {}
        if settings.get("privacy_redact_logs", True):
            record.msg = redact_sensitive_text(record.getMessage(), settings)
            record.args = ()
        return True

logging.getLogger().addFilter(SmartiRedactingFilter())

def normalize_bool_text(value):
    return str(value).strip().lower() in {"כן", "true", "yes", "y", "1"}

def strip_code_fences(code):
    code = re.sub(r'^```[a-zA-Z0-9_-]*\n', '', str(code or ''))
    code = re.sub(r'\n```$', '', code).strip()
    return code

def safe_filename(name, default="tool"):
    raw = str(name or default).strip().replace(".pyw", "").replace(".py", "")
    raw = re.sub(r'[\\/:*?"<>|]+', "_", raw)
    raw = raw.strip(" ._") or default
    return raw[:80]

def mcp_pkg_to_file_stem(pkg_name):
    return safe_filename(str(pkg_name).replace("@", "").replace("/", "_"), "mcp_tool")

def guess_mime_type(path):
    mime, _ = mimetypes.guess_type(str(path or ""))
    return mime if mime and mime.startswith("image/") else "image/png"

def _dpapi_blob(data):
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    buf = ctypes.create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))), buf, DATA_BLOB

def dpapi_protect_text(text):
    if os.name != "nt":
        return None
    try:
        raw = str(text).encode("utf-8")
        blob_in, keepalive, DATA_BLOB = _dpapi_blob(raw)
        blob_out = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in), "Smarti secret", None, None, None, 0x01, ctypes.byref(blob_out)
        )
        if not ok:
            return None
        try:
            protected = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            return SECRET_PREFIX + base64.b64encode(protected).decode("ascii")
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    except Exception:
        return None

def dpapi_unprotect_text(value):
    if os.name != "nt" or not isinstance(value, str) or not value.startswith(SECRET_PREFIX):
        return value
    try:
        encrypted = base64.b64decode(value[len(SECRET_PREFIX):])
        blob_in, keepalive, DATA_BLOB = _dpapi_blob(encrypted)
        blob_out = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0x01, ctypes.byref(blob_out)
        )
        if not ok:
            return ""
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData).decode("utf-8", "replace")
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    except Exception:
        return ""

def parse_npm_package_spec(spec):
    spec = str(spec or "").strip()
    if not spec:
        return None, None, False
    version = None
    package = spec
    if spec.startswith("@"):
        slash = spec.find("/")
        if slash == -1:
            return None, None, False
        at_version = spec.rfind("@")
        if at_version > slash:
            package, version = spec[:at_version], spec[at_version + 1:]
    elif "@" in spec:
        package, version = spec.rsplit("@", 1)
    pkg_re = r'^(?:@[a-z0-9._-]+/)?[a-z0-9._-]+$'
    ver_re = r'^[0-9A-Za-z._~+:-]+$'
    if not re.match(pkg_re, package, flags=re.IGNORECASE):
        return None, None, False
    if version is not None and not re.match(ver_re, version):
        return None, None, False
    return package, version, version is not None


def file_sha256(path, max_bytes=None):
    h = hashlib.sha256()
    read_total = 0
    with open(path, "rb") as f:
        while True:
            if max_bytes and read_total >= max_bytes:
                break
            chunk_size = 1024 * 1024
            if max_bytes:
                chunk_size = min(chunk_size, max_bytes - read_total)
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            read_total += len(chunk)
    return h.hexdigest()


def deep_merge_defaults(defaults, loaded):
    result = copy.deepcopy(defaults)
    if not isinstance(loaded, dict):
        return result
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge_defaults(result[key], value)
        else:
            result[key] = value
    return result


def estimate_text_tokens(text):
    text = str(text or "")
    if not text.strip():
        return 0
    return max(1, int(len(text) / 4))



__all__ = [name for name in globals() if not name.startswith("__")]

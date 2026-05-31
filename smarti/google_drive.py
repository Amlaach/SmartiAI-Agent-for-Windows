"""Parked Google Drive OAuth and REST helpers for Smarti.

The module is kept for a future re-enable, but it is not imported at startup,
registered as a built-in tool, or exposed in the UI while OAuth is being reworked.
"""
from .common import *
from .attachments import attachment_cache_dir, attachment_from_path, GOOGLE_WORKSPACE_EXPORT_EXTENSIONS

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DRIVE_SCOPE_FULL = "https://www.googleapis.com/auth/drive"
GOOGLE_DRIVE_SCOPE_FILE = "https://www.googleapis.com/auth/drive.file"
GOOGLE_DRIVE_SCOPE_READONLY = "https://www.googleapis.com/auth/drive.readonly"

GOOGLE_APP_EXPORTS = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
    "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.drawing": ("image/png", ".png"),
}

GOOGLE_OAUTH_CLIENT_FILES = (
    "google_drive_oauth_client.json",
    "google_oauth_client.json",
    "client_secret.json",
)


class _OAuthTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def _urlsafe_b64(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _pkce_pair():
    verifier = _urlsafe_b64(secrets.token_bytes(48))
    challenge = _urlsafe_b64(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def _free_loopback_port(preferred=0):
    preferred = int(preferred or 0)
    if preferred:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", preferred))
                return preferred
        except Exception:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _drive_q_escape(value):
    return str(value or "").replace("\\", "\\\\").replace("'", "\\'")


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "SmartiOAuth/1.0"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_result = {key: values[0] if values else "" for key, values in params.items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = (
            "<!doctype html><meta charset='utf-8'>"
            "<title>Smarti Google Drive</title>"
            "<body style='font-family:Segoe UI,Arial;padding:32px;direction:rtl'>"
            "<h2>החיבור ל-Google Drive התקבל.</h2>"
            "<p>אפשר לחזור לסמארטי.</p>"
            "</body>"
        )
        self.wfile.write(body.encode("utf-8"))
        self.server.oauth_event.set()

    def log_message(self, format, *args):
        return


class GoogleDriveClient:
    def __init__(self, core):
        self.core = core

    def _setting(self, key, default=""):
        if key in {"google_drive_client_id", "google_drive_client_secret", "google_drive_refresh_token", "google_drive_access_token"}:
            return self.core._ensure_secret_loaded(key)
        return self.core.settings.get(key, default)

    def _oauth_client_config(self):
        client_id = self._setting("google_drive_client_id")
        client_secret = self._setting("google_drive_client_secret")
        if client_id:
            return {"client_id": client_id, "client_secret": client_secret, "source": "settings"}

        env_id = sanitize_secret_value(os.environ.get("SMARTI_GOOGLE_DRIVE_CLIENT_ID", ""))
        env_secret = sanitize_secret_value(os.environ.get("SMARTI_GOOGLE_DRIVE_CLIENT_SECRET", ""))
        if env_id:
            return {"client_id": env_id, "client_secret": env_secret, "source": "environment"}

        paths = []
        configured_path = str(self.core.settings.get("google_drive_oauth_client_file", "") or "").strip()
        if configured_path:
            paths.append(configured_path)
        for name in GOOGLE_OAUTH_CLIENT_FILES:
            paths.append(os.path.join(ASSETS_DIR, name))
            paths.append(os.path.join(APP_DIR, name))
        for path in paths:
            try:
                if not path or not os.path.exists(path):
                    continue
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                data = payload.get("installed") if isinstance(payload.get("installed"), dict) else payload
                data = data if isinstance(data, dict) else {}
                file_client_id = sanitize_secret_value(data.get("client_id", ""))
                if file_client_id:
                    return {
                        "client_id": file_client_id,
                        "client_secret": sanitize_secret_value(data.get("client_secret", "")),
                        "source": path,
                    }
            except Exception as e:
                logging.warning(f"Google Drive OAuth client config ignored ({path}): {e}")
        return {"client_id": "", "client_secret": "", "source": ""}

    def _client_id(self):
        return self._oauth_client_config().get("client_id", "")

    def _client_secret(self):
        return self._oauth_client_config().get("client_secret", "")

    def configured(self):
        return bool(self._client_id())

    def missing_setup_message(self):
        if not self._client_id():
            return (
                "Google Drive sign-in is not available in this Smarti build because no app OAuth client is bundled. "
                "Bundle assets/google_drive_oauth_client.json or set SMARTI_GOOGLE_DRIVE_CLIENT_ID for development builds."
            )
        return ""

    def _scope(self, readonly=False, picker=False):
        if readonly:
            return GOOGLE_DRIVE_SCOPE_READONLY
        if picker and bool(self.core.settings.get("google_drive_picker_file_scope", False)):
            return GOOGLE_DRIVE_SCOPE_FILE
        return str(self.core.settings.get("google_drive_scope") or GOOGLE_DRIVE_SCOPE_FULL)

    def _redirect_uri(self, port):
        return f"http://127.0.0.1:{int(port)}"

    def build_auth_url(self, port, *, readonly=False, picker=False, state=""):
        client_id = self._client_id()
        verifier, challenge = _pkce_pair()
        params = {
            "client_id": client_id,
            "redirect_uri": self._redirect_uri(port),
            "response_type": "code",
            "scope": self._scope(readonly=readonly, picker=picker),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state or secrets.token_urlsafe(18),
        }
        return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params), verifier, params["state"]

    def connect(self, *, timeout=180, readonly=False):
        missing = self.missing_setup_message()
        if missing:
            return False, missing
        try:
            port = _free_loopback_port(self.core.settings.get("google_drive_oauth_port", 0))
            event = threading.Event()
            with _OAuthTCPServer(("127.0.0.1", port), _OAuthCallbackHandler) as server:
                server.oauth_event = event
                server.oauth_result = {}
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                auth_url, verifier, state = self.build_auth_url(port, readonly=readonly)
                if not webbrowser.open(auth_url):
                    server.shutdown()
                    self.disconnect()
                    return False, "Could not open the Google sign-in page."
                if not event.wait(timeout):
                    server.shutdown()
                    self.disconnect()
                    return False, "Google sign-in was cancelled or timed out."
                server.shutdown()
                result = dict(server.oauth_result or {})
            if result.get("error"):
                self.disconnect()
                return False, f"Google OAuth error: {result.get('error')}"
            if result.get("state") and result.get("state") != state:
                self.disconnect()
                return False, "Google OAuth state mismatch; connection was rejected."
            code = result.get("code", "")
            if not code:
                self.disconnect()
                return False, "Google OAuth did not return an authorization code."
            ok, message = self.exchange_code(code, verifier, self._redirect_uri(port))
            if not ok:
                self.disconnect()
            return ok, message
        except Exception as e:
            self.disconnect()
            logging.exception("Google Drive OAuth failed")
            return False, f"Google Drive sign-in failed: {e}"

    def exchange_code(self, code, verifier, redirect_uri):
        data = {
            "client_id": self._client_id(),
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        client_secret = self._client_secret()
        if client_secret:
            data["client_secret"] = client_secret
        response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=30)
        if response.status_code >= 400:
            return False, self._error_text(response, "Google token exchange failed")
        payload = response.json()
        if payload.get("refresh_token"):
            self.core.settings["google_drive_refresh_token"] = sanitize_secret_value(payload.get("refresh_token"))
        self.core.settings["google_drive_access_token"] = sanitize_secret_value(payload.get("access_token", ""))
        self.core.settings["google_drive_token_expiry"] = int(time.time()) + int(payload.get("expires_in", 3600) or 3600) - 60
        self.core.settings["google_drive_connected_at"] = datetime.now().isoformat(timespec="seconds")
        self.core._save_settings()
        return True, "Google Drive connected."

    def disconnect(self):
        for key in ("google_drive_refresh_token", "google_drive_access_token", "google_drive_token_expiry", "google_drive_connected_at"):
            self.core.settings[key] = "" if key != "google_drive_token_expiry" else 0
        self.core._save_settings()
        return True

    def _access_token(self):
        token = self._setting("google_drive_access_token")
        expiry = int(self.core.settings.get("google_drive_token_expiry", 0) or 0)
        if token and expiry > int(time.time()) + 30:
            return token
        refresh_token = self._setting("google_drive_refresh_token")
        if not refresh_token:
            raise RuntimeError("Google Drive is not connected. Connect it from Settings.")
        data = {
            "client_id": self._client_id(),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        client_secret = self._client_secret()
        if client_secret:
            data["client_secret"] = client_secret
        response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(self._error_text(response, "Google token refresh failed"))
        payload = response.json()
        token = sanitize_secret_value(payload.get("access_token", ""))
        self.core.settings["google_drive_access_token"] = token
        self.core.settings["google_drive_token_expiry"] = int(time.time()) + int(payload.get("expires_in", 3600) or 3600) - 60
        self.core._save_settings()
        return token

    def _headers(self):
        return {"Authorization": f"Bearer {self._access_token()}"}

    def _error_text(self, response, prefix):
        try:
            payload = response.json()
            detail = payload.get("error", {})
            if isinstance(detail, dict):
                msg = detail.get("message") or detail.get("status") or str(detail)
            else:
                msg = str(detail)
        except Exception:
            msg = response.text[:500]
        return f"{prefix}: HTTP {response.status_code} - {msg}"

    def _request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        merged = self._headers()
        merged.update(headers or {})
        response = requests.request(method, url, headers=merged, timeout=kwargs.pop("timeout", 60), **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(self._error_text(response, "Google Drive request failed"))
        return response

    def about(self):
        params = {"fields": "user(displayName,emailAddress),storageQuota(limit,usage,usageInDrive,usageInDriveTrash)"}
        return self._request("GET", f"{DRIVE_API_BASE}/about", params=params).json()

    def list_files(self, query="", page_size=25, include_trashed=False, folder_id="", order_by="modifiedTime desc"):
        clauses = []
        if not include_trashed:
            clauses.append("trashed = false")
        if folder_id:
            clauses.append(f"'{_drive_q_escape(folder_id)}' in parents")
        query = str(query or "").strip()
        if query:
            escaped = _drive_q_escape(query)
            clauses.append(f"(name contains '{escaped}' or fullText contains '{escaped}')")
        q = " and ".join(clauses)
        params = {
            "pageSize": max(1, min(100, int(page_size or 25))),
            "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,webViewLink,iconLink,thumbnailLink,trashed,parents)",
            "orderBy": order_by,
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if q:
            params["q"] = q
        return self._request("GET", f"{DRIVE_API_BASE}/files", params=params).json().get("files", [])

    def get_metadata(self, file_id):
        params = {
            "fields": "id,name,mimeType,size,modifiedTime,webViewLink,webContentLink,iconLink,thumbnailLink,trashed,parents,capabilities",
            "supportsAllDrives": "true",
        }
        return self._request("GET", f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}", params=params).json()

    def _unique_download_path(self, directory, filename):
        os.makedirs(directory, exist_ok=True)
        filename = safe_filename(filename or "drive_file", "drive_file")
        base, ext = os.path.splitext(filename)
        candidate = os.path.join(directory, filename)
        index = 2
        while os.path.exists(candidate):
            candidate = os.path.join(directory, f"{base}-{index}{ext}")
            index += 1
        return candidate

    def download_file(self, file_id, target_dir="", export_mime=""):
        meta = self.get_metadata(file_id)
        mime_type = meta.get("mimeType", "")
        target_dir = target_dir or attachment_cache_dir("drive")
        if mime_type.startswith("application/vnd.google-apps."):
            export_mime, ext = GOOGLE_APP_EXPORTS.get(mime_type, ("application/pdf", GOOGLE_WORKSPACE_EXPORT_EXTENSIONS.get(mime_type, ".pdf")))
            name = os.path.splitext(meta.get("name") or "drive_document")[0] + ext
            url = f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}/export"
            response = self._request("GET", url, params={"mimeType": export_mime}, timeout=180, stream=True)
            saved_mime = export_mime
        else:
            name = meta.get("name") or "drive_file"
            url = f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}"
            response = self._request("GET", url, params={"alt": "media", "supportsAllDrives": "true"}, timeout=180, stream=True)
            saved_mime = mime_type or response.headers.get("Content-Type", "application/octet-stream")
        path = self._unique_download_path(target_dir, name)
        with open(path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        attachment = attachment_from_path(
            path,
            source="google_drive",
            source_id=file_id,
            original_name=meta.get("name") or os.path.basename(path),
            extra={"web_url": meta.get("webViewLink", ""), "drive_mime_type": mime_type, "mime_type": saved_mime},
        )
        if attachment:
            attachment["mime_type"] = saved_mime
        return {"metadata": meta, "path": path, "attachment": attachment}

    def upload_file(self, path, parent_id="", name=""):
        path = os.path.abspath(str(path or "").strip(' "\''))
        if not os.path.isfile(path):
            raise RuntimeError(f"Local file not found: {path}")
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        metadata = {"name": name or os.path.basename(path)}
        if parent_id:
            metadata["parents"] = [parent_id]
        files = {
            "metadata": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": (os.path.basename(path), open(path, "rb"), mime_type),
        }
        try:
            response = self._request(
                "POST",
                f"{DRIVE_UPLOAD_BASE}/files",
                params={"uploadType": "multipart", "fields": "id,name,mimeType,size,webViewLink"},
                files=files,
                timeout=180,
            )
            return response.json()
        finally:
            try:
                files["file"][1].close()
            except Exception:
                pass

    def update_file_content(self, file_id, path, name=""):
        path = os.path.abspath(str(path or "").strip(' "\''))
        if not os.path.isfile(path):
            raise RuntimeError(f"Local file not found: {path}")
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        metadata = {"name": name} if name else {}
        files = {
            "metadata": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": (os.path.basename(path), open(path, "rb"), mime_type),
        }
        try:
            response = self._request(
                "PATCH",
                f"{DRIVE_UPLOAD_BASE}/files/{urllib.parse.quote(str(file_id))}",
                params={"uploadType": "multipart", "fields": "id,name,mimeType,size,webViewLink", "supportsAllDrives": "true"},
                files=files,
                timeout=180,
            )
            return response.json()
        finally:
            try:
                files["file"][1].close()
            except Exception:
                pass

    def rename(self, file_id, name):
        return self._request(
            "PATCH",
            f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}",
            params={"fields": "id,name,mimeType,webViewLink", "supportsAllDrives": "true"},
            json={"name": str(name or "").strip()},
        ).json()

    def trash(self, file_id, trashed=True):
        return self._request(
            "PATCH",
            f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}",
            params={"fields": "id,name,trashed", "supportsAllDrives": "true"},
            json={"trashed": bool(trashed)},
        ).json()

    def copy(self, file_id, name="", parent_id=""):
        body = {}
        if name:
            body["name"] = name
        if parent_id:
            body["parents"] = [parent_id]
        return self._request(
            "POST",
            f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}/copy",
            params={"fields": "id,name,mimeType,webViewLink", "supportsAllDrives": "true"},
            json=body,
        ).json()

    def create_folder(self, name, parent_id=""):
        metadata = {"name": str(name or "New folder"), "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            metadata["parents"] = [parent_id]
        return self._request(
            "POST",
            f"{DRIVE_API_BASE}/files",
            params={"fields": "id,name,mimeType,webViewLink", "supportsAllDrives": "true"},
            json=metadata,
        ).json()

    def move(self, file_id, folder_id):
        meta = self.get_metadata(file_id)
        previous = ",".join(meta.get("parents", []) or [])
        params = {"addParents": folder_id, "fields": "id,name,parents,webViewLink", "supportsAllDrives": "true"}
        if previous:
            params["removeParents"] = previous
        return self._request("PATCH", f"{DRIVE_API_BASE}/files/{urllib.parse.quote(str(file_id))}", params=params).json()

    def open_web(self, file_id):
        meta = self.get_metadata(file_id)
        url = meta.get("webViewLink")
        if url:
            webbrowser.open(url)
        return meta

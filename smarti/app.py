"""Application entry point for Smarti."""
from .common import *
from .ui_styles import *
from .core import SmartiCore
from .chat import ChatWindow, AnimatedSplash
from .legal import LegalAgreementDialog, raw_settings_have_current_legal_acceptance, record_legal_acceptance
from .windows_notifications import ensure_windows_notification_identity
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

INSTANCE_SERVER_NAME = "SmartiAI-Agent-for-Windows"

def _startup_command():
    args = {str(arg or "").strip().lower() for arg in sys.argv[1:]}
    return "voice" if "--voice" in args or "/voice" in args else "show_new_chat"

def _send_command_to_existing_instance(command):
    socket = QLocalSocket()
    socket.connectToServer(INSTANCE_SERVER_NAME)
    if not socket.waitForConnected(180):
        return False
    socket.write(str(command or "show_new_chat").encode("utf-8"))
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True

def _create_instance_server():
    server = QLocalServer()
    if server.listen(INSTANCE_SERVER_NAME):
        return server
    QLocalServer.removeServer(INSTANCE_SERVER_NAME)
    if server.listen(INSTANCE_SERVER_NAME):
        return server
    logging.warning("Single-instance server could not start: %s", server.errorString())
    return None

def main():
    try:
        ensure_windows_notification_identity()
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(SMARTI_APP_AUMID)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(SMARTI_APP_DISPLAY_NAME)
    app.setApplicationDisplayName(SMARTI_APP_DISPLAY_NAME)
    app.setOrganizationName(SMARTI_APP_DISPLAY_NAME)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setCursorFlashTime(1000)
    app.setFont(QFont("Segoe UI", 10))
    app.setQuitOnLastWindowClosed(False)
    apply_app_theme(app)

    instance_command = _startup_command()
    if _send_command_to_existing_instance(instance_command):
        sys.exit(0)
    instance_server = _create_instance_server()

    migrate_legacy_runtime_state()
    accepted_legal_this_run = False
    if not raw_settings_have_current_legal_acceptance():
        legal_dialog = LegalAgreementDialog()
        if legal_dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        accepted_legal_this_run = True

    splash_size, border_width, radius = 220, 4, 5
    gif_path = os.path.join(ASSETS_DIR, "logo.gif")
    if not os.path.exists(gif_path):
        gif_candidates = [p for p in glob.glob(os.path.join(ASSETS_DIR, "logo*.gif")) if os.path.getsize(p) < 5_000_000]
        if gif_candidates: gif_path = gif_candidates[0]

    splash = AnimatedSplash(gif_path, os.path.join(ASSETS_DIR, "logo.png"), splash_size, ACCENT_COLOR, border_width, radius, BG_COLOR)
    splash.show()
    app.processEvents()

    core = SmartiCore()
    if accepted_legal_this_run:
        record_legal_acceptance(core)
    apply_app_theme(app, settings=core.settings)
    window = ChatWindow(core)
    if instance_server:
        window.attach_instance_server(instance_server)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

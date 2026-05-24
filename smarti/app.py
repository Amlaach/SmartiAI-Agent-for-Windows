"""Application entry point for Smarti."""
from .common import *
from .ui_styles import *
from .core import SmartiCore
from .chat import ChatWindow, AnimatedSplash


def main():
    try:
        myappid = 'amd.smarti.ai.agent.085'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setCursorFlashTime(1000)
    app.setFont(QFont("Segoe UI", 10))
    apply_app_theme(app)

    splash_size, border_width, radius = 220, 4, 5
    gif_path = os.path.join(ASSETS_DIR, "logo.gif")
    if not os.path.exists(gif_path):
        gif_candidates = [p for p in glob.glob(os.path.join(ASSETS_DIR, "logo*.gif")) if os.path.getsize(p) < 5_000_000]
        if gif_candidates: gif_path = gif_candidates[0]

    splash = AnimatedSplash(gif_path, os.path.join(ASSETS_DIR, "logo.png"), splash_size, ACCENT_COLOR, border_width, radius, BG_COLOR)
    splash.show()
    app.processEvents()

    core = SmartiCore()
    apply_app_theme(app, settings=core.settings)
    window = ChatWindow(core)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

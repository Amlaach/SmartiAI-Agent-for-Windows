"""Modular Smarti package."""

__all__ = ["SmartiCore", "ChatWindow", "AnimatedSplash", "main"]


def __getattr__(name):
    if name == "SmartiCore":
        from .core import SmartiCore
        return SmartiCore
    if name in {"ChatWindow", "AnimatedSplash"}:
        from .chat import AnimatedSplash, ChatWindow
        return {"ChatWindow": ChatWindow, "AnimatedSplash": AnimatedSplash}[name]
    if name == "main":
        from .app import main
        return main
    raise AttributeError(f"module 'smarti' has no attribute {name!r}")

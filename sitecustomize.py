"""Auto-load Smarti SSL compatibility hooks for child Python tools."""
import os

if os.environ.get("SMARTI_ALLOW_INSECURE_SSL") == "1":
    try:
        from smarti.ssl_compat import apply_insecure_ssl_compat

        apply_insecure_ssl_compat()
    except Exception:
        pass

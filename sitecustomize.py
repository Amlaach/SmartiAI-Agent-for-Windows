"""Auto-load Smarti SSL compatibility hooks for child Python tools."""
import os
import ssl


def _apply_inline_ssl_compat():
    original_default_https_context = getattr(ssl, "_create_default_https_context", ssl.create_default_context)
    original_create_default_context = ssl.create_default_context

    def enabled():
        return os.environ.get("SMARTI_ALLOW_INSECURE_SSL") == "1"

    def dynamic_default_https_context(*args, **kwargs):
        if enabled():
            return ssl._create_unverified_context(*args, **kwargs)
        return original_default_https_context(*args, **kwargs)

    def dynamic_create_default_context(*args, **kwargs):
        if enabled():
            return ssl._create_unverified_context(*args, **kwargs)
        return original_create_default_context(*args, **kwargs)

    ssl._create_default_https_context = dynamic_default_https_context
    ssl.create_default_context = dynamic_create_default_context

    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass

    try:
        import requests

        if not getattr(requests.Session, "_smarti_ssl_compat_patched", False):
            original_request = requests.Session.request
            original_merge = requests.Session.merge_environment_settings

            def request(self, method, url, **kwargs):
                if enabled():
                    kwargs["verify"] = False
                return original_request(self, method, url, **kwargs)

            def merge_environment_settings(self, url, proxies, stream, verify, cert):
                settings = original_merge(self, url, proxies, stream, verify, cert)
                if enabled():
                    settings["verify"] = False
                return settings

            requests.Session.request = request
            requests.Session.merge_environment_settings = merge_environment_settings
            requests.Session._smarti_ssl_compat_patched = True
    except Exception:
        pass

    try:
        import httpx

        if not getattr(httpx, "_smarti_ssl_compat_patched", False):
            original_request = httpx.request
            original_client_init = httpx.Client.__init__
            original_async_client_init = httpx.AsyncClient.__init__

            def httpx_request(method, url, **kwargs):
                if enabled():
                    kwargs["verify"] = False
                return original_request(method, url, **kwargs)

            def client_init(self, *args, **kwargs):
                if enabled():
                    kwargs["verify"] = False
                return original_client_init(self, *args, **kwargs)

            def async_client_init(self, *args, **kwargs):
                if enabled():
                    kwargs["verify"] = False
                return original_async_client_init(self, *args, **kwargs)

            httpx.request = httpx_request
            httpx.Client.__init__ = client_init
            httpx.AsyncClient.__init__ = async_client_init
            httpx._smarti_ssl_compat_patched = True
    except Exception:
        pass

    try:
        import aiohttp

        connector = getattr(aiohttp, "TCPConnector", None)
        if connector and not getattr(connector, "_smarti_ssl_compat_patched", False):
            original_init = connector.__init__

            def connector_init(self, *args, **kwargs):
                if enabled() and "ssl" not in kwargs:
                    kwargs["ssl"] = False
                return original_init(self, *args, **kwargs)

            connector.__init__ = connector_init
            connector._smarti_ssl_compat_patched = True
    except Exception:
        pass


if os.environ.get("SMARTI_ALLOW_INSECURE_SSL") == "1":
    try:
        from smarti.ssl_compat import apply_insecure_ssl_compat

        apply_insecure_ssl_compat()
    except Exception:
        _apply_inline_ssl_compat()

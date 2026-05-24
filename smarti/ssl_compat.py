"""SSL compatibility hooks controlled by SMARTI_ALLOW_INSECURE_SSL."""
import os
import ssl

_PATCHED = False
_ORIGINAL_DEFAULT_HTTPS_CONTEXT = getattr(ssl, "_create_default_https_context", ssl.create_default_context)
_ORIGINAL_CREATE_DEFAULT_CONTEXT = ssl.create_default_context


def _enabled():
    return os.environ.get("SMARTI_ALLOW_INSECURE_SSL") == "1"


def _unverified_context(*args, **kwargs):
    return ssl._create_unverified_context(*args, **kwargs)


def _dynamic_default_https_context(*args, **kwargs):
    if _enabled():
        return _unverified_context(*args, **kwargs)
    return _ORIGINAL_DEFAULT_HTTPS_CONTEXT(*args, **kwargs)


def _dynamic_create_default_context(*args, **kwargs):
    if _enabled():
        return _unverified_context(*args, **kwargs)
    return _ORIGINAL_CREATE_DEFAULT_CONTEXT(*args, **kwargs)


def _patch_requests():
    try:
        import requests
        import urllib3
    except Exception:
        return

    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass

    if getattr(requests.Session, "_smarti_ssl_compat_patched", False):
        return

    original_request = requests.Session.request
    original_merge = requests.Session.merge_environment_settings

    def request(self, method, url, **kwargs):
        if _enabled():
            kwargs["verify"] = False
        return original_request(self, method, url, **kwargs)

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        settings = original_merge(self, url, proxies, stream, verify, cert)
        if _enabled():
            settings["verify"] = False
        return settings

    requests.Session.request = request
    requests.Session.merge_environment_settings = merge_environment_settings
    requests.Session._smarti_ssl_compat_patched = True


def _patch_httpx():
    try:
        import httpx
    except Exception:
        return

    if getattr(httpx, "_smarti_ssl_compat_patched", False):
        return

    original_request = httpx.request
    original_client_init = httpx.Client.__init__
    original_async_client_init = httpx.AsyncClient.__init__

    def request(method, url, **kwargs):
        if _enabled():
            kwargs["verify"] = False
        return original_request(method, url, **kwargs)

    def client_init(self, *args, **kwargs):
        if _enabled():
            kwargs["verify"] = False
        return original_client_init(self, *args, **kwargs)

    def async_client_init(self, *args, **kwargs):
        if _enabled():
            kwargs["verify"] = False
        return original_async_client_init(self, *args, **kwargs)

    httpx.request = request
    httpx.Client.__init__ = client_init
    httpx.AsyncClient.__init__ = async_client_init
    httpx._smarti_ssl_compat_patched = True


def _patch_aiohttp():
    try:
        import aiohttp
    except Exception:
        return

    connector = getattr(aiohttp, "TCPConnector", None)
    if not connector or getattr(connector, "_smarti_ssl_compat_patched", False):
        return

    original_init = connector.__init__

    def connector_init(self, *args, **kwargs):
        if _enabled() and "ssl" not in kwargs:
            kwargs["ssl"] = False
        return original_init(self, *args, **kwargs)

    connector.__init__ = connector_init
    connector._smarti_ssl_compat_patched = True


def apply_insecure_ssl_compat():
    global _PATCHED
    if _PATCHED:
        return _enabled()

    ssl._create_default_https_context = _dynamic_default_https_context
    ssl.create_default_context = _dynamic_create_default_context
    _patch_requests()
    _patch_httpx()
    _patch_aiohttp()
    _PATCHED = True
    return _enabled()

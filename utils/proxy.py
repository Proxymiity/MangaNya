import requests

from utils import conf

proxies = conf.get("proxy", "proxies")


def available_for(target):
    available = []
    for p in proxies:
        if target in proxies[p]["targets"]:
            available.append(int(p))
    return available


def get_url(proxy, url):
    kinds = {
        "Proxymiity/php-cache": php_cache
    }
    proxy = proxies[str(proxy)]
    return kinds[proxy["kind"]](url, proxy)


def php_cache(url, settings):
    # Makes the client make the request instead of the backend
    if settings["client_side"]:
        params = {"token": settings["token"], "url": url}
        if not settings["load_mode"]:
            params["redirect"] = True
        if not settings["caching"]:
            params["live"] = True
        r = requests.Request("GET", f"{settings['url']}/cache", params=params)
        return r.prepare().url

    # Check if caching is enabled and resource exists on cache
    if settings["caching"]:
        api = _ppc_api(url, settings)
        if api["cached"]:
            if settings["load_mode"]:
                r = requests.Request("GET", f"{settings['url']}/", params={"hash": api["url_hash"]})
                return r.prepare().url
            return api["url"]

    # If the caching check wasn't enabled or returned false, cache it
    api = _ppc_api(url, settings, create=True)
    if settings["load_mode"]:
        r = requests.Request("GET", f"{settings['url']}/", params={"hash": api["url_hash"]})
        return r.prepare().url
    return api["url"]


def _ppc_api(url, settings, create=False):
    params = {"token": settings["token"], "url": url}
    if create:
        params["create"] = True
    r = requests.get(f"{settings['url']}/api", params=params)
    return r.json()

import hashlib
import logging
import string

import requests

try:
    import _pickle as pickle
except:
    import pickle

from urllib.parse import urljoin
from walrus import Database

db = Database()
cache = db.cache()


class BaseRequest:

    def __init__(self, session, type, path, cache_ttl=None):
        self.cache_ttl = cache_ttl if cache_ttl is not None else session.cache_ttl
        self.cache_on = bool(self.cache_ttl)
        self.session = session
        self.logger = session.logger
        self.type = type
        self.path = path
        self.send = self.method()
        if self.cache_on:
            deco = cache.cached(self.key_fn, timeout=self.cache_ttl, metrics=True)
            self.send = deco(self.send)
            self.cache = self.send
        f = string.Formatter()
        self.path_fields = tuple(t[1] for t in f.parse(self.path))

    def bust(self, *pathargs, **kw):
        path = self.path.format(*pathargs, **kw) if (
            pathargs or kw
        ) else self.path
        payload_kw = self.kw2payload(kw)
        payload = self.process_payload(payload_kw)
        self.cache.bust(path, **payload)

    def key_fn(self, a, k):
        return hashlib.md5(
            pickle.dumps((self.type, self.session.baseurl, a, k))
        ).hexdigest()

    def method(self):
        return getattr(self.session, self.type.lower())

    def process_payload(self, payload):
        return {'data': payload}

    def kw2payload(self, kw):
        return {k: v for k, v in kw.items() if k not in self.path_fields}

    def __call__(self, *pathargs, **kw):
        path = self.path.format(*pathargs, **kw) if (
            pathargs or kw
        ) else self.path
        payload_kw = self.kw2payload(kw)
        payload = self.process_payload(payload_kw)
        response = self.send(path, **payload)
        if not response.ok:
            if self.cache_on:
                self.cache.bust(path, **payload)
            self.logger.error("[%s] %s:", response.status_code, path)
        return response


class JSONRequest(BaseRequest):

    def process_payload(self, payload):
        return {'json': payload}


class PrefixedURLSession(requests.Session):

    def __init__(self, baseurl, *args, cache_ttl=0, logger=None, **kw):
        super(PrefixedURLSession, self).__init__(*args, **kw)
        self.baseurl = baseurl
        self.cache_ttl = cache_ttl
        self.logger = logger or logging.getLogger()
        self.__post_init__()

    def __post_init__(self):
        """
        Post init hook
        """

    def request(self, method, url, *args, **kw):
        url = urljoin(self.baseurl, url)
        response = super(PrefixedURLSession, self).request(method, url, *args, **kw)
        return response

    def GETRequest(self, path, cache_ttl=None):
        return BaseRequest(self, "GET", path, cache_ttl=cache_ttl)

    def POSTRequest(self, path, cache_ttl=None):
        return BaseRequest(self, "POST", path, cache_ttl=cache_ttl)

    def PATCHRequest(self, path, cache_ttl=None):
        return BaseRequest(self, "PATCH", path, cache_ttl=cache_ttl)

    def HEADRequest(self, path, cache_ttl=None):
        return BaseRequest(self, "HEAD", path, cache_ttl=cache_ttl)

    def DELETERequest(self, path, cache_ttl=None):
        return BaseRequest(self, "DELETE", path, cache_ttl=cache_ttl)

    def GETJSONRequest(self, path, cache_ttl=None):
        return JSONRequest(self, "GET", path, cache_ttl=cache_ttl)

    def POSTJSONRequest(self, path, cache_ttl=None):
        return JSONRequest(self, "POST", path, cache_ttl=cache_ttl)

    def PATCHJSONRequest(self, path, cache_ttl=None):
        return JSONRequest(self, "PATCH", path, cache_ttl=cache_ttl)

    def HEADJSONRequest(self, path, cache_ttl=None):
        return JSONRequest(self, "HEAD", path, cache_ttl=cache_ttl)

    def DELETEJSONRequest(self, path, cache_ttl=None):
        return JSONRequest(self, "DELETE", path, cache_ttl=cache_ttl)

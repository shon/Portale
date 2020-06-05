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


class BaseRequest:
    def __init__(self, session, type, path, cache_ttl=None):
        self.db = session.db
        self.session_cache = session.db.cache()

        self.cache_ttl = cache_ttl if cache_ttl is not None else session.cache_ttl
        self.cache_on = bool(self.cache_ttl)
        self.session = session
        self.logger = session.logger
        self.type = type
        self.path = path
        self.send = self.method()
        if self.cache_on:
            deco = self.session_cache.cached(self.key_fn, timeout=self.cache_ttl, metrics=True)
            self.send = deco(self.send)
            self.cache = self.send
        f = string.Formatter()
        self.path_fields = tuple(t[1] for t in f.parse(self.path))

    def bust(self, *pathargs, **kw):
        path = self.path.format(*pathargs, **kw) if (pathargs or kw) else self.path
        payload = self.kw2payload(kw)
        self.cache.bust(path, **payload)

    def key_fn(self, a, k):
        return hashlib.md5(
            pickle.dumps((self.type, self.session.baseurl, a, k))
        ).hexdigest()

    def method(self):
        return getattr(self.session, self.type.lower())

    def prep_payload(self, payload):
        return {"data": payload}

    def kw2payload(self, kw):
        params = kw.pop("params", {})
        data = {k: v for k, v in kw.items() if k not in self.path_fields}
        payload = self.prep_payload(data)
        if params:
            payload["params"] = params
        return payload

    def __call__(self, *pathargs, **kw):
        path = self.path.format(*pathargs, **kw) if (pathargs or kw) else self.path
        payload = self.kw2payload(kw)
        response = self.send(path, **payload)
        if not response.ok:
            if self.cache_on:
                self.cache.bust(path, **payload)
            self.logger.error("[%s] %s:", response.status_code, path)
        return response


class JSONRequest(BaseRequest):
    def prep_payload(self, payload):
        return {"json": payload}


class PrefixedURLSession(requests.Session):
    def __init__(self, baseurl, *args, headers=None, cache_ttl=0,
            logger=None, redis_host='localhost', redis_port=6379,
            redis_db=0, redis_password=None, redis_socket_timeout=None, **kw
        ):
        self.db = Database(
                    host=redis_host, port=redis_port,
                    db=redis_db, password=redis_password,
                    socket_timeout=redis_socket_timeout
                 )

        super(PrefixedURLSession, self).__init__(*args, **kw)
        self.baseurl = baseurl
        self.cache_ttl = cache_ttl
        self.logger = logger or logging.getLogger()
        if headers:
            self.headers.update(headers)
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

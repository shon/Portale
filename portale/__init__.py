import requests
import hashlib
import logging

try:
    import _pickle as pickle
except:
    import pickle
from urllib.parse import urljoin
from walrus import Database

db = Database()
cache = db.cache()


class BaseRequest:

    def __init__(self, session, type, path, timeout=None):
        self.timeout = timeout if timeout is not None else session.timeout
        self.cache_on = bool(self.timeout)
        self.session = session
        self.logger = session.logger
        self.type = type
        self.path = path
        self.send = self.method()
        if self.cache_on:
            deco = cache.cached(self.key_fn, timeout=self.timeout, metrics=True)
            self.send = deco(self.send)
            self.cache = self.send

    def bust(self, *pathargs, params=None, data=None, json=None, **pathkw):
        path = self.path.format(*pathargs, **pathkw) if (
            pathargs or pathkw
        ) else self.path
        self.cache.bust(path, params=params, data=data, json=json)

    def key_fn(self, a, k):
        return hashlib.md5(
            pickle.dumps((self.type, self.session.baseurl, a, k))
        ).hexdigest()

    def method(self):
        return getattr(self.session, self.type.lower())

    def process_response(self, resp):
        """
        Override to customize result
        """
        return resp

    def __call__(self, *pathargs, params=None, data=None, json=None, **pathkw):
        path = self.path.format(*pathargs, **pathkw) if (
            pathargs or pathkw
        ) else self.path
        response = self.send(path, params=params, data=data, json=json)
        if response.status_code != 200:
            if self.cache_on:
                self.cache.bust(path, params=params, data=data, json=json)
            # TODO: if self.raise_if_not_200::
            self.logger.error("[%s] %s:", response.status_code, path)
            response.raise_for_status()
        result = self.process_response(response)
        return result


class JSONRequest(BaseRequest):

    def process_response(self, resp):
        return resp.json()


class PrefixedURLSession(requests.Session):

    def __init__(self, baseurl, *args, timeout=0, logger=None, **kw):
        super(PrefixedURLSession, self).__init__(*args, **kw)
        self.baseurl = baseurl
        self.timeout = timeout
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

    def GETRequest(self, path, timeout=None):
        return BaseRequest(self, "GET", path, timeout=timeout)

    def POSTRequest(self, path, timeout=None):
        return BaseRequest(self, "POST", path, timeout=timeout)

    def PATCHRequest(self, path, timeout=None):
        return BaseRequest(self, "PATCH", path, timeout=timeout)

    def HEADRequest(self, path, timeout=None):
        return BaseRequest(self, "HEAD", path, timeout=timeout)

    def DELETERequest(self, path, timeout=None):
        return BaseRequest(self, "DELETE", path, timeout=timeout)

    def GETJSONRequest(self, path, timeout=None):
        return JSONRequest(self, "GET", path, timeout=timeout)

    def POSTJSONRequest(self, path, timeout=None):
        return JSONRequest(self, "POST", path, timeout=timeout)

    def PATCHJSONRequest(self, path, timeout=None):
        return JSONRequest(self, "PATCH", path, timeout=timeout)

    def HEADJSONRequest(self, path, timeout=None):
        return JSONRequest(self, "HEAD", path, timeout=timeout)

    def DELETEJSONRequest(self, path, timeout=None):
        return JSONRequest(self, "DELETE", path, timeout=timeout)

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

logger = logging.getLogger()


class PrefixedURLSession(requests.Session):

    def __init__(self, baseurl, *args, **kw):
        super(PrefixedURLSession, self).__init__(*args, **kw)
        self.baseurl = baseurl
        self.__post_init__()

    def __post_init__(self):
        """
        Post init hook
        """

    def request(self, method, url, *args, **kw):
        url = urljoin(self.baseurl, url)
        response = super(PrefixedURLSession, self).request(method, url, *args, **kw)
        return response


class BaseRequest:

    type = None  # any valid HTTP method string like GET, POST, PUT, PATCH etc.

    def __init__(self, session, path, timeout=0):
        self.session = session
        self.path = path
        self.cache_on = bool(timeout)
        self.timeout = timeout
        key_fn = lambda: self.path + ":"
        self.send = self.method()
        if self.cache_on:
            deco = cache.cached(self.key_fn, timeout=self.timeout, metrics=True)
            self.cache = deco(self.send)
            self.send = self.cache

    def key_fn(self, *args, **kw):
        return hashlib.md5(pickle.dumps((self.type, self.path, kw))).hexdigest()

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
            self.cache.bust(path, params=params, data=data, json=json)
            # TODO: if self.raise_if_not_200::
            logger.error("[%s] %s", resp.status_code, path)
            response.raise_for_status()
        result = self.process_response(response)
        return result


class GETRequest(BaseRequest):
    type = "GET"


class POSTRequest(BaseRequest):
    type = "POST"


class PATCHRequest(BaseRequest):
    type = "PATCH"


class GETJSONRequest(GETRequest):

    def process_response(self, resp):
        return resp.json()

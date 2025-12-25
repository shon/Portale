import hashlib
import logging
import pickle
import string
from urllib.parse import urljoin
import json

try:
    from pyreqwest.client import SyncClientBuilder
    from pyreqwest import errors as pyreqwest_errors

    pyreqwest_available = True
except ImportError:
    pyreqwest_available = False

import requests
from requests.structures import CaseInsensitiveDict
from requests.exceptions import (
    HTTPError,
    ConnectionError,
    Timeout,
    TooManyRedirects,
    RequestException,
)
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


class RequestFactoryMixin:
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


class PrefixedURLSessionRequests(requests.Session, RequestFactoryMixin):
    def __init__(self, baseurl, *args, headers=None, cache_ttl=0, logger=None, **kw):
        super(PrefixedURLSessionRequests, self).__init__(*args, **kw)
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
        response = super(PrefixedURLSessionRequests, self).request(
            method, url, *args, **kw
        )
        return response


if pyreqwest_available:

    class PyreqwestResponseWrapper:
        def __init__(self, response, url):
            self._content = bytes(response.bytes())
            self._status_code = response.status
            self.headers = CaseInsensitiveDict(response.headers)
            self.url = url
            self.encoding = "utf-8"  # A reasonable default

        @property
        def status_code(self):
            return self._status_code

        @property
        def ok(self):
            return self.status_code < 400

        @property
        def content(self):
            return self._content

        @property
        def text(self):
            return self._content.decode(self.encoding)

        def json(self, **kwargs):
            return json.loads(self.text, **kwargs)

        def raise_for_status(self):
            if not self.ok:
                raise HTTPError(f"{self.status_code} Client Error for url: {self.url}")

    class PrefixedURLSessionPyreqwest(RequestFactoryMixin):
        def __init__(
            self,
            baseurl,
            *args,
            headers=None,
            cache_ttl=0,
            logger=None,
            timeout=None,
            **kw,
        ):
            self.baseurl = baseurl
            self.cache_ttl = cache_ttl
            self.logger = logger or logging.getLogger()

            builder = SyncClientBuilder()
            if headers:
                builder = builder.default_headers(headers)
                self.headers = headers
            else:
                self.headers = {}

            if timeout:
                builder = builder.timeout(seconds=timeout)

            self._client = builder.build()
            self.__post_init__()

        def __post_init__(self):
            """
            Post init hook
            """

        def _request(self, method, url, params=None, data=None, json=None, **kwargs):
            full_url = urljoin(self.baseurl, url)
            request_builder = getattr(self._client, method.lower())(full_url)

            if params:
                request_builder = request_builder.query(params)
            if data:
                request_builder = request_builder.form(data)
            if json:
                request_builder = request_builder.json(json)

            try:
                response = request_builder.build().send()
                return PyreqwestResponseWrapper(response, full_url)
            except pyreqwest_errors.ConnectError as e:
                raise ConnectionError(e) from e
            except pyreqwest_errors.RequestTimeoutError as e:
                raise Timeout(e) from e
            except pyreqwest_errors.ReadTimeoutError as e:
                raise Timeout(e) from e
            except pyreqwest_errors.RedirectError as e:
                raise TooManyRedirects(e) from e
            except pyreqwest_errors.RequestError as e:
                raise RequestException(e) from e

        def get(self, url, **kwargs):
            return self._request("GET", url, **kwargs)

        def post(self, url, **kwargs):
            return self._request("POST", url, **kwargs)

        def patch(self, url, **kwargs):
            return self._request("PATCH", url, **kwargs)

        def head(self, url, **kwargs):
            return self._request("HEAD", url, **kwargs)

        def delete(self, url, **kwargs):
            return self._request("DELETE", url, **kwargs)

        def request(self, method, url, **kwargs):
            return self._request(method, url, **kwargs)

    PrefixedURLSession = PrefixedURLSessionPyreqwest
else:
    PrefixedURLSession = PrefixedURLSessionRequests

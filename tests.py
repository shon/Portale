import datetime
import os
import pytest
from portale import (
    PrefixedURLSession,
    PrefixedURLSessionRequests,
    pyreqwest_available,
)
from requests import exceptions as requests_exceptions

sessions = [PrefixedURLSessionRequests]
if pyreqwest_available:
    from portale import PrefixedURLSessionPyreqwest
    sessions.append(PrefixedURLSessionPyreqwest)


@pytest.fixture(params=sessions)
def session(request):
    return request.param(
        "https://eu.httpbin.org/",
        headers={"Authorization": "Auth Token"},
        cache_ttl=5,
    )


def test_session_selection():
    if pyreqwest_available:
        assert PrefixedURLSession == PrefixedURLSessionPyreqwest
    else:
        assert PrefixedURLSession == PrefixedURLSessionRequests


def test_set_cache_ttl(session):
    get_thing = session.GETJSONRequest("anything?thing={0}")
    assert get_thing.cache_ttl == 5
    get_thing = session.GETJSONRequest("anything?thing={0}", cache_ttl=10)
    assert get_thing.cache_ttl == 10
    get_thing = session.GETJSONRequest("anything?thing={0}", cache_ttl=0)
    assert get_thing.cache_ttl == 0
    res = get_thing("flask").json()
    assert res["args"]["thing"] == "flask"


def test_params_in_url(session):
    get_thing_by_name = session.GETRequest("anything?thing={name}")
    resp = get_thing_by_name(name="snake")
    assert {"thing": "snake"} == resp.json()["args"]
    print(resp.json())


def test_passing_params(session):
    get_thing_by_name = session.GETRequest("anything")
    resp = get_thing_by_name(params={"thing": "boa"})
    assert resp.url.endswith("?thing=boa")
    assert {"thing": "boa"} == resp.json()["args"]

    get_thing_by_name = session.POSTRequest("anything")
    resp = get_thing_by_name(params={"thing": "boa"}, a=1)
    assert resp.url.endswith("?thing=boa")
    assert {"thing": "boa"} == resp.json()["args"]


def test_cache_request(session):
    n = 2
    cache_ttl = 20
    long_request = session.GETJSONRequest("delay/{n}", cache_ttl=cache_ttl)
    assert long_request.cache_ttl == cache_ttl

    long_request.bust(
        n=n
    )  # resetting cache to ensure we don't use previous run's data
    then = datetime.datetime.now()
    long_request(n=n)
    now = datetime.datetime.now()
    assert (now - then).seconds >= n

    for i in range(9):
        then = datetime.datetime.now()
        long_request(n=n)
        now = datetime.datetime.now()
        assert (now - then).seconds < n

    long_request.bust(n=n)

    then = datetime.datetime.now()
    long_request(n=n)
    now = datetime.datetime.now()
    assert (now - then).seconds >= n

    assert long_request.cache.metrics["hits"]


def test_post_json(session):
    post_req = session.POSTJSONRequest("anything")
    data = {"a": 1, "b": 2}
    resp = post_req(**data)
    assert resp.json()["json"] == data


def test_url_subspost(session):
    post_req = session.POSTJSONRequest("anything/{category}")
    data = {"name": "The Tipping Point", "ISBN": " 0-316-34662-4"}
    resp = post_req(category="books", **data)
    assert resp.json()["json"] == data


def test_headers(session):
    get_headers = session.GETRequest("headers")
    resp = get_headers()
    assert session.headers["Authorization"] == resp.json()["headers"]["Authorization"]


def test_response_wrapper(session):
    get_thing = session.GETJSONRequest("anything?thing=test")
    resp = get_thing()
    assert resp.text is not None
    assert resp.content is not None
    assert resp.status_code == 200
    assert resp.ok
    resp.raise_for_status()


def test_raise_for_status(session):
    get_thing = session.GETJSONRequest("status/404")
    resp = get_thing()
    assert not resp.ok
    with pytest.raises(requests_exceptions.HTTPError):
        resp.raise_for_status()

if pyreqwest_available:
    def test_exception_wrapping():
        session = PrefixedURLSessionPyreqwest("http://localhost:12345")
        with pytest.raises(requests_exceptions.ConnectionError):
            session.GETRequest("anything")()

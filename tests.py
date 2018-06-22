import datetime
from portale import PrefixedURLSession

session = PrefixedURLSession("https://eu.httpbin.org/", timeout=5)


def test_set_timeout():
    get_thing = session.GETJSONRequest("anything?thing={0}")
    assert get_thing.timeout == 5
    get_thing = session.GETJSONRequest("anything?thing={0}", timeout=10)
    assert get_thing.timeout == 10
    get_thing = session.GETJSONRequest("anything?thing={0}", timeout=0)
    assert get_thing.timeout == 0
    res = get_thing("flask")
    assert res["args"]["thing"] == "flask"


def test_get_params():
    get_thing_by_name = session.GETRequest("anything?thing={name}")
    resp = get_thing_by_name(name="snake")
    assert '{"thing":"snake"}' in resp.text


def test_cache_request():
    n = 2
    timeout = 20
    long_request = session.GETJSONRequest("delay/{n}", timeout=timeout)
    assert long_request.timeout == timeout

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


def test_post_json():
    session = PrefixedURLSession("https://eu.httpbin.org/")
    post_req = session.POSTJSONRequest("anything")
    data = {"a": 1, "b": 2}
    resp = post_req(**data)
    assert resp["json"] == post_json


def test_url_subspost():
    session = PrefixedURLSession("https://eu.httpbin.org/")
    post_req = session.POSTJSONRequest("anything/{category}")
    data = {"name": "The Tipping Point", "ISBN": " 0-316-34662-4"}
    resp = post_req(category="books", **data)
    assert resp["json"] == data

import datetime
from portale import PrefixedURLSession

session = PrefixedURLSession("https://eu.httpbin.org/", cache_ttl=5)


def test_set_cache_ttl():
    get_thing = session.GETJSONRequest("anything?thing={0}")
    assert get_thing.cache_ttl == 5
    get_thing = session.GETJSONRequest("anything?thing={0}", cache_ttl=10)
    assert get_thing.cache_ttl == 10
    get_thing = session.GETJSONRequest("anything?thing={0}", cache_ttl=0)
    assert get_thing.cache_ttl == 0
    res = get_thing("flask")
    assert res["args"]["thing"] == "flask"


def test_get_params():
    get_thing_by_name = session.GETRequest("anything?thing={name}")
    resp = get_thing_by_name(name="snake")
    assert {"thing":"snake"} == resp.json()['args']


def test_cache_request():
    n = 2
    cache_ttl = 20
    long_request = session.GETJSONRequest("delay/{n}", cache_ttl=cache_ttl)
    assert long_request.cache_ttl == cache_ttl

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
    assert resp["json"] == data


def test_url_subspost():
    session = PrefixedURLSession("https://eu.httpbin.org/")
    post_req = session.POSTJSONRequest("anything/{category}")
    data = {"name": "The Tipping Point", "ISBN": " 0-316-34662-4"}
    resp = post_req(category="books", **data)
    assert resp["json"] == data

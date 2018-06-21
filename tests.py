import datetime
from portale import PrefixedURLSession

session = PrefixedURLSession("https://eu.httpbin.org/", timeout=5)


def test_get_params():
    get_thing = session.GETJSONRequest("anything?thing={0}")
    assert get_thing.timeout == 5
    get_thing = session.GETJSONRequest("anything?thing={0}", timeout=10)
    assert get_thing.timeout == 10
    get_thing = session.GETJSONRequest("anything?thing={0}", timeout=0)
    assert get_thing.timeout == 0
    res = get_thing("flask")
    assert res["args"]["thing"] == "flask"


def test_get_params2():
    get_thing_by_name = session.GETRequest("anything?thing={name}", timeout=10)
    resp = get_thing_by_name(name="snake")
    assert '{"thing":"snake"}' in resp.text


def test_cache_long_request():
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


def test_post():
    session = PrefixedURLSession("https://eu.httpbin.org/")
    post_req = session.POSTJSONRequest("anything")
    post_json = {"a": 1, "b": 2}
    resp = post_req(json=post_json)
    assert resp["json"] == post_json

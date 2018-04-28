import datetime
from portale import PrefixedURLSession

session = PrefixedURLSession('https://eu.httpbin.org/')


def test_get_params():
    get_thing = session.GETJSONRequest('anything?thing={0}', timeout=10)
    res = get_thing('flask')
    assert res['args']['thing'] == 'flask'


def test_cache_long_request():
    n = 2
    long_request = session.GETJSONRequest('delay/{n}', timeout=20)

    then = datetime.datetime.now()
    long_request(n=n)
    now = datetime.datetime.now()
    assert (now - then).seconds >= n

    for i in range(9):
        then = datetime.datetime.now()
        long_request(n=n)
        now = datetime.datetime.now()
        assert (now - then).seconds < n

    long_request.send.bust(n=n)

    then = datetime.datetime.now()
    long_request(n=n)
    now = datetime.datetime.now()
    assert (now - then).seconds >= n

    assert long_request.send.metrics['hits']

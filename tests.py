import datetime
from portale import PrefixedURLSession, GETJSONRequest

session = PrefixedURLSession('https://httpbin.org/')

def test_get_params():
    get_thing = GETJSONRequest(session, 'anything?thing={0}', timeout=10)
    res = get_thing('flask')
    assert res['args']['thing'] == 'flask'

def test_cache_long_request():
    n = 2
    long_request = GETJSONRequest(session, 'delay/{n}', timeout=20)

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

    print(long_request.send.metrics)

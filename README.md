# Portale

Portale is a minimalistic, requests-based HTTP/REST API client with a key advantage over other libraries: it allows a different cache timeout policy for each API.

## Simple Example

```python
from portale import PrefixedURLSession

session = PrefixedURLSession('https://httpbin.org/')

get_thing = session.GETRequest('anything?thing={0}', cache_ttl=10)
thing = get_thing('snake')

get_thing_by_name = session.GETRequest('anything?thing={name}', cache_ttl=10)
thing = get_thing_by_name(name='snake')

long_request = session.GETJSONRequest('delay/{n}', cache_ttl=20)
result1 = long_request(n=2).json()
result2 = long_request(n=2).json()  # cached response
```

## Cache

If `cache_ttl` is not specified in the `Request` initialization, the session's `cache_ttl` is used as the default for all APIs using that session.

```python
from portale import PrefixedURLSession

session = PrefixedURLSession('https://httpbin.org/', cache_ttl=10)
get_thing = session.GETRequest('anything?thing={0}')
long_request = session.GETJSONRequest('delay/{n}')
```

### Busting Cache

```python
long_request.cache.bust(n=n)
```

### Accessing Cache Metrics

```python
print(long_request.cache.metrics)
```

## Tests

To run the tests, use the following command:

```bash
python -m unittest tests
```

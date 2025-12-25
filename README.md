# Portale

Portale is a minimalistic, `requests`-based HTTP/REST API client with a key advantage over other libraries: it allows a different cache timeout policy for each API.

Additionally, Portale can use `pyreqwest` as a backend for improved performance. 🚀 If available, `portale` will prioritize it, with `requests` serving as a fallback.

## Installation

You can install Portale from PyPI:

```bash
pip install portale
```

To use the `pyreqwest` backend, install the `pyreqwest` extra:

```bash
pip install portale[pyreqwest]
```

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

## Cache 💾

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

## Tests 🧪

To run the tests, use the following command:

```bash
pytest tests.py
```

## Build and Upload

First, install `uv`:

```bash
pip install uv
```

To build the distribution, you can use the `uv build` command:

```bash
uv build
```

This will create the `dist` directory with the source and wheel distributions.

To upload the distribution to PyPI, you can use `uv publish`:

```bash
uv publish
```

It is recommended to set a PyPI token with the `UV_PUBLISH_TOKEN` environment variable.

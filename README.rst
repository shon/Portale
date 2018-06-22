Portale
=======

Portale is minimalistic requests based HTTP/REST API client. 

Advantage over other libraries: Allows different cache timeout policy for each API

Simple example
--------------

.. code-block:: python

    from portale import PrefixedURLSession

    session = PrefixedURLSession('https://httpbin.org/')

    get_thing = session.GETRequest('anything?thing={0}', cache_ttl=10)
    thing = get_thing('snake')

    get_thing_by_name = session.GETRequest('anything?thing={name}', cache_ttl=10)
    thing = get_thing_by_name(name='snake')

    long_request = session.GETJSONRequest('delay/{n}', cache_ttl=20)
    result1 = long_request(n=2)
    result2 = long_request(n=2)  # cached response


Cache 
-----
  

`cache_ttl` if not specified in Request initialization, session's cache_ttl is used as default cache_ttl for all the APIs using same session.

.. code-block:: python

    from portale import PrefixedURLSession

    session = PrefixedURLSession('https://httpbin.org/', cache_ttl=10)
    get_thing = session.GETRequest('anything?thing={0}')
    long_request = session.GETJSONRequest('delay/{n}')


Busting cache

.. code-block:: python

    long_request.cache.bust(n=n)

Access cache metrics

.. code-block:: python

    print(long_request.cache.metrics)


Tests
-----

.. code-block:: python

    nosetests -xv tests.py

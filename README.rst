Portale
=======

Portale is minimalistic requests based HTTP/REST API client. 

Advantage over other libraries: Allows different cache timeout policy for each API

Simple example
--------------

.. code-block:: python

    from portale import PrefixedURLSession

    session = PrefixedURLSession('https://httpbin.org/')

    get_thing = session.GETRequest('anything?thing={0}', timeout=10)
    long_request = session.GETJSONRequest('delay/{n}', timeout=20)

    thing = get_thing('snake')

    result = long_request(n=2)
    result = long_request(n=2)  # cached response


Cache 
-----
  

`timeout` if not specified in Request initialization, session's timeout is used as default timeout for all the APIs using same session.

.. code-block:: python

    from portale import PrefixedURLSession

    session = PrefixedURLSession('https://httpbin.org/', timeout=10)
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

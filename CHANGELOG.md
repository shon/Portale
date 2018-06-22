## 8.0.0

INCOMPATIBILITIES

 - `timeout` is renamed to `cache_ttl` to later avoid conflict with requests `timeout` parameter
 - sending payload is simplified and more natural
    - ~~`some_api(op=add, json={'a': 1, 'b': 2})`~~ to `some_api(op=add, a=1, b=2)`

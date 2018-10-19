## 0.9.0

INCOMPATIBILITIES

    - Removed `process_response` hook
    - JSONRequest classes no longer try to convert response to json
        - rationale:
            - keep responses consistent among all Request classes
            - keep Portale as close to requests as possible
    - Exceptions are no longer raised on failed request (such as 4xx/5xx)

## 0.8.0

INCOMPATIBILITIES

 - `timeout` is renamed to `cache_ttl` to later avoid conflict with requests `timeout` parameter
 - sending payload is simplified and more natural
    - ~~`some_api(op=add, json={'a': 1, 'b': 2})`~~ to `some_api(op=add, a=1, b=2)`

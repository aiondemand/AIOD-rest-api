# Behind a Proxy

The app should work without issue when deployed behind a proxy.
If you configured the proxy to remove a path prefix, then you will need to configure your proxy to add a `x-forwarded-prefix` header.
Otherwise, some endpoints may not function as expected.
This is currently predominantly relevant for the generated documentation pages and their authentication mechanisms.
Here are examples on how to configure a proxy with the `/aiod` prefix and add the correct header:

=== "Apache"

    ``` { .conf }
    <Location /aiod>
       ProxyPass http://localhost:8009
       ProxypassReverse http://localhost:8009
       RequestHeader set X-Forwarded-Prefix "/aiod"
       RequestHeader set X-Forwarded-Proto "https"
    </Location>
    ```

=== "nginx"

    ```
    server {
        location /aiod/ {
            proxy_pass http://app:8000/;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Forwarded-Prefix "/aiod";
        }
    }
    ```

!!! warning "Multiple Proxies"

    The REST API is not tested under multiple sequential or parallel proxies at the same time.
    For sequential proxies, so long as the `x-forwarded-prefix` is preserved and augmented to represent each layer,
    the REST API probably will work fine. For 'parallel' proxies (e.g., exposing the service both on `/aiod` and `/rest`)
    the API likely remains functional, but the OpenAPI spec (and thus swagger pages) will only work for the one which is
    requested first (see versioning.py::add_version_to_openapi).

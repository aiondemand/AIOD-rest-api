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

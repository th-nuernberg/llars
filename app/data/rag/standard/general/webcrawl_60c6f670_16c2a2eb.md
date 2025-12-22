# Configuring outgoing HTTP requests - Keycloak

# Configuring outgoing HTTP requests

Keycloak often needs to make requests to the applications and services that it secures. Keycloak manages these outgoing connections using an HTTP client. This guide shows how to configure the client, connection pool, proxy environment settings, timeouts, and more.

## Configuring trusted certificates for TLS connections

See Configuring trusted certificates for how
to configure a Keycloak Truststore so that Keycloak is able to perform outgoing requests using TLS.

## Client Configuration Command

The HTTP client that Keycloak uses for outgoing communication is highly configurable. To configure the Keycloak outgoing HTTP client, enter this command:
The following are the command options:
Maximum time in milliseconds until establishing a connection times out. Default: Not set.
Maximum time of inactivity between two data packets until a socket connection times out, in milliseconds. Default: 5000ms
Size of the connection pool for outgoing connections. Default: 128.
How many connections can be pooled per host. Default: 64.
Maximum connection time to live in milliseconds. Default: Not set.
Maximum time an idle connection stays in the connection pool, in milliseconds. Idle connections will be removed from the pool by a background cleaner thread. Set this option to -1 to disable this check. Default: 900000.
Enable or disable caching of cookies. Default: true.
File path to a Java keystore file. This keystore contains client certificates for mTLS.
Password for the client keystore. REQUIRED, when client-keystore is set.
Password for the private key of the client. REQUIRED, when client-keystore is set.
Specify proxy configurations for outgoing HTTP requests. For more details, see Proxy mappings for outgoing HTTP requests .
If an outgoing request requires HTTPS and this configuration option is set to true, you do not have to specify a truststore. This setting should be used only during development and never in production because it will disable verification of SSL certificates. Default: false.

## Proxy mappings for outgoing HTTP requests

To configure outgoing requests to use a proxy, you can use the following standard proxy environment variables to configure the proxy mappings: HTTP_PROXY , HTTPS_PROXY , and NO_PROXY .
- The HTTP_PROXY and HTTPS_PROXY variables represent the proxy server that is used for outgoing HTTP requests. Keycloak does not differentiate between the two variables. If you define both variables, HTTPS_PROXY takes precedence regardless of the actual scheme that the proxy server uses.
The HTTP_PROXY and HTTPS_PROXY variables represent the proxy server that is used for outgoing HTTP requests. Keycloak does not differentiate between the two variables. If you define both variables, HTTPS_PROXY takes precedence regardless of the actual scheme that the proxy server uses.
- The NO_PROXY variable defines a comma separated list of hostnames that should not use the proxy. For each hostname that you specify, all its subdomains are also excluded from using proxy.
The NO_PROXY variable defines a comma separated list of hostnames that should not use the proxy. For each hostname that you specify, all its subdomains are also excluded from using proxy.
The environment variables can be lowercase or uppercase. Lowercase takes precedence. For example, if you define both HTTP_PROXY and http_proxy , http_proxy is used.
In this example, the following results occur:
- All outgoing requests use the proxy https://www-proxy.acme.com:8080 except for requests to google.com or any subdomain of google.com, such as auth.google.com.
All outgoing requests use the proxy https://www-proxy.acme.com:8080 except for requests to google.com or any subdomain of google.com, such as auth.google.com.
- login.facebook.com and all its subdomains do not use the defined proxy, but groups.facebook.com uses the proxy because it is not a subdomain of login.facebook.com.
login.facebook.com and all its subdomains do not use the defined proxy, but groups.facebook.com uses the proxy because it is not a subdomain of login.facebook.com.

## Proxy mappings using regular expressions

An alternative to using environment variables for proxy mappings is to configure a comma-delimited list of proxy-mappings for outgoing requests sent by Keycloak. A proxy-mapping consists of a regex-based hostname pattern and a proxy-uri, using the format hostname-pattern;proxy-uri .
For example, consider the following regex:
You apply a regex-based hostname pattern by entering this command:
The backslash character \ is escaped again because micro-profile config is used to parse the array of mappings.
To determine the proxy for the outgoing HTTP request, the following occurs:
- The target hostname is matched against all configured hostname patterns.
The target hostname is matched against all configured hostname patterns.
- The proxy-uri of the first matching pattern is used.
The proxy-uri of the first matching pattern is used.
- If no configured pattern matches the hostname, no proxy is used.
If no configured pattern matches the hostname, no proxy is used.
When your proxy server requires authentication, include the credentials of the proxy user in the format username:password@ . For example:
In this example, the following occurs:
- The special value NO_PROXY for the proxy-uri is used, which means that no proxy is used for hosts matching the associated hostname pattern.
The special value NO_PROXY for the proxy-uri is used, which means that no proxy is used for hosts matching the associated hostname pattern.
- A catch-all pattern ends the proxy-mappings, providing a default proxy for all outgoing requests.
A catch-all pattern ends the proxy-mappings, providing a default proxy for all outgoing requests.

## Relevant options

truststore-paths List of pkcs12 (p12, pfx, or pkcs12 file extensions), PEM files, or directories containing those files that will be used as a system truststore. CLI: --truststore-paths Env: KC_TRUSTSTORE_PATHS
truststore-paths
List of pkcs12 (p12, pfx, or pkcs12 file extensions), PEM files, or directories containing those files that will be used as a system truststore.
CLI: --truststore-paths Env: KC_TRUSTSTORE_PATHS

---
Quelle: https://www.keycloak.org/server/outgoinghttp
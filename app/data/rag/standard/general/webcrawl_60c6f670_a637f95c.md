# Configuring a reverse proxy - Keycloak

# Configuring a reverse proxy

Distributed environments frequently require the use of a reverse proxy. Keycloak offers several options to securely integrate with such environments.

## Port to be proxied

Keycloak runs on the following ports by default:
- 8443 ( 8080 when you enable HTTP explicitly by --http-enabled=true )
8443 ( 8080 when you enable HTTP explicitly by --http-enabled=true )
The port 8443 (or 8080 if HTTP is enabled) is used for the Admin UI, Account Console, SAML and OIDC endpoints and the Admin REST API as described in the Configuring the hostname (v2) guide.
The port 9000 is used for management, which includes endpoints for health checks and metrics as described in the Configuring the Management Interface guide.
You only need to proxy port 8443 (or 8080 ) even when you use different host names for frontend/backend and administration as described at Configuring Keycloak for production . You should not proxy port 9000 as health checks and metrics use those ports directly, and you do not want to expose this information to external callers.
Keycloak will parse the reverse proxy headers based on the proxy-headers option which accepts several values:
- By default if the option is not specified, no reverse proxy headers are parsed. This should be used when no proxy is in use or with https passthrough.
By default if the option is not specified, no reverse proxy headers are parsed. This should be used when no proxy is in use or with https passthrough.
- forwarded enables parsing of the Forwarded header as per RFC7239 .
forwarded enables parsing of the Forwarded header as per RFC7239 .
- xforwarded enables parsing of non-standard X-Forwarded-* headers, such as X-Forwarded-For , X-Forwarded-Proto , X-Forwarded-Host , and X-Forwarded-Port .
xforwarded enables parsing of non-standard X-Forwarded-* headers, such as X-Forwarded-For , X-Forwarded-Proto , X-Forwarded-Host , and X-Forwarded-Port .
If you are using a reverse proxy for anything other than https passthrough and do not set the proxy-headers option, then by default you will see 403 Forbidden responses to requests via the proxy that perform origin checking.
For example:
If either forwarded or xforwarded is selected, make sure your reverse proxy properly sets and overwrites the Forwarded or X-Forwarded-* headers respectively. To set these headers, consult the documentation for your reverse proxy. Do not use forwarded or xforwarded with https passthrough. Misconfiguration will leave Keycloak exposed to security vulnerabilities.
Take extra precautions to ensure that the client address is properly set by your reverse proxy via the Forwarded or X-Forwarded-For headers.
If this header is incorrectly configured, rogue clients can set this header and trick Keycloak into thinking the client is connected from a different IP address than the actual address. This precaution can be more critical if you do any deny or allow listing of IP addresses.
When using the xforwarded setting, the X-Forwarded-Port takes precedence over any port included in the X-Forwarded-Host .
If the TLS connection is terminated at the reverse proxy (edge termination), enabling HTTP through the http-enabled setting is required.

## Different context-path on reverse proxy

Keycloak assumes it is exposed through the reverse proxy under the same context path as Keycloak is configured for. By default Keycloak is exposed through the root ( / ), which means it expects to be exposed through the reverse proxy on / as well.
You can use a full URL for the hostname option in these cases, for example using --hostname=https://my.keycloak.org/auth if Keycloak is exposed through the reverse proxy on /auth .
For more details on exposing Keycloak on different hostname or context-path incl. Administration REST API and Console, see Configuring the hostname (v2) .
Alternatively you can also change the context path of Keycloak itself to match the context path for the reverse proxy using the http-relative-path option, which will change the context-path of Keycloak itself to match the context path used by the reverse proxy.

## Enable sticky sessions

Typical cluster deployment consists of the load balancer (reverse proxy) and 2 or more Keycloak servers on private network.
For performance purposes, it may be useful if load balancer forwards all requests related to particular browser session to the same Keycloak backend node.
The reason is, that Keycloak is using Infinispan distributed cache under the covers for save data related to current authentication session and user session.
The Infinispan distributed caches are configured with limited number of owners. That means that session related data are stored only in some cluster nodes and the other nodes need to lookup the data remotely if they want to access it.
For example if authentication session with ID 123 is saved in the Infinispan cache on node1, and then node2 needs to lookup this session, it needs to send the request to node1 over the network to return the particular session entity.
It is beneficial if particular session entity is always available locally, which can be done with the help of sticky sessions. The workflow in the cluster environment with the public frontend load balancer and two backend Keycloak nodes can be like this:
- User sends initial request to see the Keycloak login screen
User sends initial request to see the Keycloak login screen
- This request is served by the frontend load balancer, which forwards it to some random node (eg. node1). Strictly said, the node doesn’t need to be random, but can be chosen according to some other criteria (client IP address etc). It all depends on the implementation and configuration of underlying load balancer (reverse proxy).
This request is served by the frontend load balancer, which forwards it to some random node (eg. node1). Strictly said, the node doesn’t need to be random, but can be chosen according to some other criteria (client IP address etc). It all depends on the implementation and configuration of underlying load balancer (reverse proxy).
- Keycloak creates authentication session with random ID (eg. 123) and saves it to the Infinispan cache.
Keycloak creates authentication session with random ID (eg. 123) and saves it to the Infinispan cache.
- Infinispan distributed cache assigns the primary owner of the session based on the hash of session ID. See Infinispan documentation for more details around this. Let’s assume that Infinispan assigned node2 to be the owner of this session.
Infinispan distributed cache assigns the primary owner of the session based on the hash of session ID. See Infinispan documentation for more details around this. Let’s assume that Infinispan assigned node2 to be the owner of this session.
- Keycloak creates the cookie AUTH_SESSION_ID with the format like <session-id>.<owner-node-id> . In our example case, it will be 123.node2 .
Keycloak creates the cookie AUTH_SESSION_ID with the format like <session-id>.<owner-node-id> . In our example case, it will be 123.node2 .
- Response is returned to the user with the Keycloak login screen and the AUTH_SESSION_ID cookie in the browser
Response is returned to the user with the Keycloak login screen and the AUTH_SESSION_ID cookie in the browser
From this point, it is beneficial if load balancer forwards all the next requests to the node2 as this is the node, who is owner of the authentication session with ID 123 and hence Infinispan can lookup this session locally. After authentication is finished, the authentication session is converted to user session, which will be also saved on node2 because it has same ID 123 .
The sticky session is not mandatory for the cluster setup, however it is good for performance for the reasons mentioned above. You need to configure your loadbalancer to stick over the AUTH_SESSION_ID cookie. The appropriate procedure to make this change depends on your loadbalancer.
If your proxy supports session affinity without processing cookies from backend nodes, you should set the spi-sticky-session-encoder--infinispan--should-attach-route option
to false in order to avoid attaching the node to cookies and just rely on the reverse proxy capabilities.
By default, the spi-sticky-session-encoder--infinispan--should-attach-route option value is true so that the node name is attached to
cookies to indicate to the reverse proxy the node that subsequent requests should be sent to.

## Exposed path recommendations

When using a reverse proxy, Keycloak only requires certain paths to be exposed.
The following table shows the recommended paths to expose.
Keycloak Path
Reverse Proxy Path
When exposing all paths, admin paths are exposed unnecessarily.
When exposing all paths, admin paths are exposed unnecessarily.
Exposed admin paths lead to an unnecessary attack vector.
Exposed admin paths lead to an unnecessary attack vector.
This path is needed to work correctly, for example, for OIDC endpoints.
This path is needed to work correctly, for example, for OIDC endpoints.
/resources/
/resources/
/resources/
/resources/
This path is needed to serve assets correctly. It may be served from a CDN instead of the Keycloak path.
This path is needed to serve assets correctly. It may be served from a CDN instead of the Keycloak path.
/.well-known/
/.well-known/
/.well-known/
/.well-known/
This path is needed to resolve Authorization Server Metadata and other information via RFC8414.
This path is needed to resolve Authorization Server Metadata and other information via RFC8414.
Exposed metrics lead to an unnecessary attack vector.
Exposed metrics lead to an unnecessary attack vector.
Exposed health checks lead to an unnecessary attack vector.
Exposed health checks lead to an unnecessary attack vector.
We assume you run Keycloak on the root path / on your reverse proxy/gateway’s public API.
If not, prefix the path with your desired one.
If you configured a http-relative-path on the server, proceed as follows to use discovery wih RFC8414: Configure a reverse proxy to map the /.well-known/ path without the prefix to the path with the prefix on the server.

## Trusted Proxies

To ensure that proxy headers are used only from proxies you trust, set the proxy-trusted-addresses option to a comma separated list of IP addresses (IPv4 or IPv6) or Classless Inter-Domain Routing (CIDR) notations.
For example:

## PROXY Protocol

The proxy-protocol-enabled option controls whether the server should use the HA PROXY protocol when serving requests from behind a proxy. When set to true, the remote address returned will be the one from the actual connecting client. The value cannot be true when using the proxy-headers option.
This is useful when running behind a compatible https passthrough proxy because the request headers cannot be manipulated.
For example:

## Enabling client certificate lookup

When the proxy is configured as a TLS termination proxy the client certificate information can be forwarded to the server through specific HTTP request headers and then used to authenticate
clients. You are able to configure how the server is going to retrieve client certificate information depending on the proxy you are using.
Client certificate lookup via a proxy header for X.509 authentication is considered security-sensitive. If misconfigured, a forged client certificate header can be used for authentication. Extra precautions need to be taken to ensure that the client certificate information can be trusted when passed via a proxy header. Double check your use case needs reencrypt or edge TLS termination which implies using a proxy header for client certificate lookup. TLS passthrough is recommended as a more secure option
when X.509 authentication is desired as it does not require passing the certificate via a proxy header. Client certificate lookup from a proxy header is applicable only to reencrypt
and edge TLS termination. If passthrough is not an option, implement the following security measures: Configure your network so that Keycloak is isolated and can accept connections only from the proxy. Make sure that the proxy overwrites the header that is configured in spi-x509cert-lookup--<provider>--ssl-client-cert option. Pay extra attention to the spi-x509cert-lookup--<provider>--trust-proxy-verification setting. Make sure you enable it only if you can trust your proxy to verify the client certificate.
Setting spi-x509cert-lookup--<provider>--trust-proxy-verification=true without the proxy verifying the client certificate chain will expose Keycloak to security vulnerability
when a forged client certificate can be used for authentication.
Client certificate lookup via a proxy header for X.509 authentication is considered security-sensitive. If misconfigured, a forged client certificate header can be used for authentication. Extra precautions need to be taken to ensure that the client certificate information can be trusted when passed via a proxy header.
- Double check your use case needs reencrypt or edge TLS termination which implies using a proxy header for client certificate lookup. TLS passthrough is recommended as a more secure option
when X.509 authentication is desired as it does not require passing the certificate via a proxy header. Client certificate lookup from a proxy header is applicable only to reencrypt
and edge TLS termination.
Double check your use case needs reencrypt or edge TLS termination which implies using a proxy header for client certificate lookup. TLS passthrough is recommended as a more secure option
when X.509 authentication is desired as it does not require passing the certificate via a proxy header. Client certificate lookup from a proxy header is applicable only to reencrypt
and edge TLS termination.
- If passthrough is not an option, implement the following security measures: Configure your network so that Keycloak is isolated and can accept connections only from the proxy. Make sure that the proxy overwrites the header that is configured in spi-x509cert-lookup--<provider>--ssl-client-cert option. Pay extra attention to the spi-x509cert-lookup--<provider>--trust-proxy-verification setting. Make sure you enable it only if you can trust your proxy to verify the client certificate.
Setting spi-x509cert-lookup--<provider>--trust-proxy-verification=true without the proxy verifying the client certificate chain will expose Keycloak to security vulnerability
when a forged client certificate can be used for authentication.
If passthrough is not an option, implement the following security measures:
- Configure your network so that Keycloak is isolated and can accept connections only from the proxy.
Configure your network so that Keycloak is isolated and can accept connections only from the proxy.
- Make sure that the proxy overwrites the header that is configured in spi-x509cert-lookup--<provider>--ssl-client-cert option.
Make sure that the proxy overwrites the header that is configured in spi-x509cert-lookup--<provider>--ssl-client-cert option.
- Pay extra attention to the spi-x509cert-lookup--<provider>--trust-proxy-verification setting. Make sure you enable it only if you can trust your proxy to verify the client certificate.
Setting spi-x509cert-lookup--<provider>--trust-proxy-verification=true without the proxy verifying the client certificate chain will expose Keycloak to security vulnerability
when a forged client certificate can be used for authentication.
Pay extra attention to the spi-x509cert-lookup--<provider>--trust-proxy-verification setting. Make sure you enable it only if you can trust your proxy to verify the client certificate.
Setting spi-x509cert-lookup--<provider>--trust-proxy-verification=true without the proxy verifying the client certificate chain will expose Keycloak to security vulnerability
when a forged client certificate can be used for authentication.
The server supports some of the most commons TLS termination proxies such as:
Apache HTTP Server
Apache HTTP Server
To configure how client certificates are retrieved from the requests you need to:
When configuring the HTTP headers, you need to make sure the values you are using correspond to the name of the headers
forwarded by the proxy with the client certificate information.
The available options for configuring a provider are:
Description
ssl-client-cert
ssl-client-cert
The name of the header holding the client certificate
The name of the header holding the client certificate
ssl-cert-chain-prefix
ssl-cert-chain-prefix
The prefix of the headers holding additional certificates in the chain and used to retrieve individual
certificates accordingly to the length of the chain. For instance, a value CERT_CHAIN will tell the server
to load additional certificates from headers CERT_CHAIN_0 to CERT_CHAIN_9 if certificate-chain-length is set to 10 .
The prefix of the headers holding additional certificates in the chain and used to retrieve individual
certificates accordingly to the length of the chain. For instance, a value CERT_CHAIN will tell the server
to load additional certificates from headers CERT_CHAIN_0 to CERT_CHAIN_9 if certificate-chain-length is set to 10 .
certificate-chain-length
certificate-chain-length
The maximum length of the certificate chain.
The maximum length of the certificate chain.
trust-proxy-verification
trust-proxy-verification
Enable trusting NGINX proxy certificate verification, instead of forwarding the certificate to Keycloak and verifying it in Keycloak.
Enable trusting NGINX proxy certificate verification, instead of forwarding the certificate to Keycloak and verifying it in Keycloak.
cert-is-url-encoded
cert-is-url-encoded
Whether the forwarded certificate is url-encoded or not. In NGINX, this corresponds to the $ssl_client_cert and $ssl_client_escaped_cert variables. This can also be used for the Traefik PassTlsClientCert middleware, as it sends the client certficate unencoded.
Whether the forwarded certificate is url-encoded or not. In NGINX, this corresponds to the $ssl_client_cert and $ssl_client_escaped_cert variables. This can also be used for the Traefik PassTlsClientCert middleware, as it sends the client certficate unencoded.

### Configuring the NGINX provider

The NGINX SSL/TLS module does not expose the client certificate chain. Keycloak’s NGINX certificate lookup provider rebuilds it by using the Keycloak truststore.
If you are using this provider, see Configuring trusted certificates for how
to configure a Keycloak Truststore.

## Relevant options

hostname Address at which is the server exposed. Can be a full URL, or just a hostname. When only hostname is provided, scheme, port and context path are resolved from the request. CLI: --hostname Env: KC_HOSTNAME Available only when hostname:v2 feature is enabled
Address at which is the server exposed.
Can be a full URL, or just a hostname. When only hostname is provided, scheme, port and context path are resolved from the request.
CLI: --hostname Env: KC_HOSTNAME
Available only when hostname:v2 feature is enabled
hostname-admin Address for accessing the administration console. Use this option if you are exposing the administration console using a reverse proxy on a different address than specified in the hostname option. CLI: --hostname-admin Env: KC_HOSTNAME_ADMIN Available only when hostname:v2 feature is enabled
hostname-admin
Address for accessing the administration console.
Use this option if you are exposing the administration console using a reverse proxy on a different address than specified in the hostname option.
CLI: --hostname-admin Env: KC_HOSTNAME_ADMIN
Available only when hostname:v2 feature is enabled
http-relative-path Set the path relative to / for serving resources. The path must start with a / . CLI: --http-relative-path Env: KC_HTTP_RELATIVE_PATH
http-relative-path
Set the path relative to / for serving resources.
The path must start with a / .
CLI: --http-relative-path Env: KC_HTTP_RELATIVE_PATH
/ (default)
/ (default)
proxy-headers The proxy headers that should be accepted by the server. Misconfiguration might leave the server exposed to security vulnerabilities. Takes precedence over the deprecated proxy option. CLI: --proxy-headers Env: KC_PROXY_HEADERS
proxy-headers
The proxy headers that should be accepted by the server.
Misconfiguration might leave the server exposed to security vulnerabilities. Takes precedence over the deprecated proxy option.
CLI: --proxy-headers Env: KC_PROXY_HEADERS
forwarded , xforwarded
forwarded , xforwarded
proxy-protocol-enabled Whether the server should use the HA PROXY protocol when serving requests from behind a proxy. When set to true, the remote address returned will be the one from the actual connecting client. Cannot be enabled when the proxy-headers is used. CLI: --proxy-protocol-enabled Env: KC_PROXY_PROTOCOL_ENABLED
proxy-protocol-enabled
Whether the server should use the HA PROXY protocol when serving requests from behind a proxy.
When set to true, the remote address returned will be the one from the actual connecting client. Cannot be enabled when the proxy-headers is used.
CLI: --proxy-protocol-enabled Env: KC_PROXY_PROTOCOL_ENABLED
true , false (default)
true , false (default)
proxy-trusted-addresses A comma separated list of trusted proxy addresses. If set, then proxy headers from other addresses will be ignored. By default all addresses are trusted. A trusted proxy address is specified as an IP address (IPv4 or IPv6) or Classless Inter-Domain Routing (CIDR) notation. Available only when proxy-headers is set. CLI: --proxy-trusted-addresses Env: KC_PROXY_TRUSTED_ADDRESSES
proxy-trusted-addresses
A comma separated list of trusted proxy addresses.
If set, then proxy headers from other addresses will be ignored. By default all addresses are trusted. A trusted proxy address is specified as an IP address (IPv4 or IPv6) or Classless Inter-Domain Routing (CIDR) notation. Available only when proxy-headers is set.
CLI: --proxy-trusted-addresses Env: KC_PROXY_TRUSTED_ADDRESSES

---
Quelle: https://www.keycloak.org/server/reverseproxy
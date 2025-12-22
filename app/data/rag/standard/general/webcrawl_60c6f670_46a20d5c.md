# Configuring the hostname (v2) - Keycloak

# Configuring the hostname (v2)

## The importance of setting the hostname option

By default, Keycloak mandates the configuration of the hostname option and does not dynamically resolve URLs. This is a security measure.
Keycloak freely discloses its own URLs, for instance through the OIDC Discovery endpoint, or as part of the password reset link in an email. If the hostname was dynamically interpreted from a hostname header, it could provide a potential attacker with an opportunity to manipulate a URL in the email, redirect a user to the attacker’s fake domain, and steal sensitive data such as action tokens, passwords, etc.
By explicitly setting the hostname option, we avoid a situation where tokens could be issued by a fraudulent issuer. The server can be started with an explicit hostname using the following command:
The examples start the Keycloak instance in production mode, which requires a public certificate and private key in order to secure communications. For more information, refer to the Configuring Keycloak for production .

## Defining specific parts of the hostname option

As demonstrated in the previous example, the scheme and port are not explicitly required. In such cases, Keycloak automatically handles these aspects. For instance, the server would be accessible at https://my.keycloak.org:8443 in the given example. However, a reverse proxy will typically expose Keycloak at the default ports, e.g. 443 . In that case it’s desirable to specify the full URL in the hostname option rather than keeping the parts of the URL dynamic. The server can then be started with:
Similarly, your reverse proxy might expose Keycloak at a different context path. It is possible to configure Keycloak to reflect that via the hostname and hostname-admin options. See the following example:

## Utilizing an internal URL for communication among clients

Keycloak has the capability to offer a separate URL for backchannel requests, enabling internal communication while maintaining the use of a public URL for frontchannel requests. Moreover, the backchannel is dynamically resolved based on incoming headers. Consider the following example:
In this manner, your applications, referred to as clients, can connect with Keycloak through your local network, while the server remains publicly accessible at https://my.keycloak.org .

## Using edge TLS termination

As you can observe, the HTTPS protocol is the default choice, adhering to Keycloak’s commitment to security best practices. However, Keycloak also provides the flexibility for users to opt for HTTP if necessary. This can be achieved simply by specifying the HTTP listener, consult the Configuring TLS for details. With an edge TLS-termination proxy you can start the server as follows:
The result of this configuration is that you can continue to access Keycloak at https://my.keycloak.org via HTTPS, while the proxy interacts with the instance using HTTP and port 8080 .

## Using a reverse proxy

When a proxy is forwarding http or reencrypted TLS requests, the proxy-headers option should be set. Depending on the hostname settings, some or all of the URL, may be dynamically determined.
If either forwarded or xforwarded is selected, make sure your reverse proxy properly sets and overwrites the Forwarded or X-Forwarded-* headers respectively. To set these headers, consult the documentation for your reverse proxy. Misconfiguration will leave Keycloak exposed to security vulnerabilities.

### Fully dynamic URLs.

For example if your reverse proxy correctly sets the Forwarded header, and you don’t want to hardcode the hostname, Keycloak can accommodate this. You simply need to initiate the server as follows:
With this configuration, the server respects the value set by the Forwarded header. This also implies that all endpoints are dynamically resolved.

### Partially dynamic URLs

The proxy-headers option can be also used to resolve the URL partially dynamically when the hostname option is not specified as a full URL. For example:
In this case, scheme, and port are resolved dynamically from X-Forwarded-* headers, while hostname is statically defined as my.keycloak.org .
The proxy-headers is still relevant even when the hostname is set to a full URL as the headers are used to determine the origin of the request. For example:
In this case, while nothing is dynamically resolved from the X-Forwarded-* headers, the X-Forwarded-* headers are used to determine the correct origin of the request.

## Exposing the Administration Console on a separate hostname

If you wish to expose the Admin Console on a different host, you can do so with the following command:
This allows you to access Keycloak at https://my.keycloak.org and the Admin Console at https://admin.my.keycloak.org:8443 , while the backend continues to use https://my.keycloak.org .
Keep in mind that hostname and proxy options do not change the ports on which the server listens. Instead it changes only the ports of static resources like JavaScript and CSS links, OIDC well-known endpoints, redirect URIs, etc. that will be used in front of the proxy. You need to use HTTP configuration options to change the actual ports the server is listening on. Refer to the All configuration for details.
Using the hostname-admin option does not prevent accessing the Administration REST API endpoints via the frontend URL specified by the hostname option. If you want to restrict access to the Administration REST API, you need to do it on the reverse proxy level. Administration Console implicitly accesses the API using the URL as specified by the hostname-admin option.

## Background - server endpoints

Keycloak exposes several endpoints, each with a different purpose. They are typically used for communication among applications or for managing the server. We recognize 3 main endpoint groups:
- Administration
Administration
If you want to work with either of these endpoints, you need to set the base URL. The base URL consists of a several parts:
- a scheme (e.g. https protocol)
a scheme (e.g. https protocol)
- a hostname (e.g. example.keycloak.org)
a hostname (e.g. example.keycloak.org)
- a port (e.g. 8443)
a port (e.g. 8443)
- a path (e.g. /auth)
a path (e.g. /auth)
The base URL for each group has an important impact on how tokens are issued and validated, on how links are created for actions that require the user to be redirected to Keycloak (for example, when resetting password through email links), and, most importantly, how applications will discover these endpoints when fetching the OpenID Connect Discovery Document from realms/{realm-name}/.well-known/openid-configuration .
Users and applications use the frontend URL to access Keycloak through a front channel. The front channel is a publicly accessible communication channel. For example browser-based flows (accessing the login page, clicking on the link to reset a password or binding the tokens) can be considered as frontchannel requests.
In order to make Keycloak accessible via the frontend URL, you need to set the hostname option:
The backend endpoints are those accessible through a public domain or through a private network. They’re related to direct backend communication between Keycloak and a client (an application secured by Keycloak). Such communication might be over a local network, avoiding a reverse proxy. Examples of the endpoints that belong to this group are the authorization endpoint, token and token introspection endpoint, userinfo endpoint, JWKS URI endpoint, etc.
The default value of hostname-backchannel-dynamic option is false , which means that the backchannel URLs are same as the frontchannel URLs. Dynamic resolution of backchannel URLs from incoming request headers can be enabled by setting the following options:
Note that hostname option must be set to a URL. For more information, refer to the Validations section below.

### Administration

Similarly to the base frontend URL, you can also set the base URL for resources and endpoints of the administration console. The server exposes the administration console and static resources using a specific URL. This URL is used for redirect URLs, loading resources (CSS, JS), Administration REST API etc. It can be done by setting the hostname-admin option:
Again, the hostname option must be set to a URL. For more information, refer to the Validations section below.

## Sources for resolving the URL

As indicated in the previous sections, URLs can be resolved in several ways: they can be dynamically generated, hardcoded, or a combination of both:
- Dynamic from an incoming request: Host header, scheme, server port, context path Proxy-set headers: Forwarded and X-Forwarded-*
Dynamic from an incoming request:
- Host header, scheme, server port, context path
Host header, scheme, server port, context path
- Proxy-set headers: Forwarded and X-Forwarded-*
Proxy-set headers: Forwarded and X-Forwarded-*
- Hardcoded: Server-wide config (e.g hostname , hostname-admin , etc.) Realm configuration for frontend URL
- Server-wide config (e.g hostname , hostname-admin , etc.)
Server-wide config (e.g hostname , hostname-admin , etc.)
- Realm configuration for frontend URL
Realm configuration for frontend URL

## Validations

- hostname URL and hostname-admin URL are verified that full URL is used, incl. scheme and hostname. Port is validated only if present, otherwise default port for given protocol is assumed (80 or 443).
hostname URL and hostname-admin URL are verified that full URL is used, incl. scheme and hostname. Port is validated only if present, otherwise default port for given protocol is assumed (80 or 443).
- In production profile ( kc.sh|bat start ), either --hostname or --hostname-strict false must be explicitly configured. This does not apply for dev profile ( kc.sh|bat start-dev ) where --hostname-strict false is the default value.
In production profile ( kc.sh|bat start ), either --hostname or --hostname-strict false must be explicitly configured.
- This does not apply for dev profile ( kc.sh|bat start-dev ) where --hostname-strict false is the default value.
This does not apply for dev profile ( kc.sh|bat start-dev ) where --hostname-strict false is the default value.
- If --hostname is not configured: hostname-backchannel-dynamic must be set to false. hostname-strict must be set to false.
If --hostname is not configured:
- hostname-backchannel-dynamic must be set to false.
hostname-backchannel-dynamic must be set to false.
- hostname-strict must be set to false.
hostname-strict must be set to false.
- If hostname-admin is configured, hostname must be set to a URL (not just hostname). Otherwise Keycloak would not know what is the correct frontend URL (incl. port etc.) when accessing the Admin Console.
If hostname-admin is configured, hostname must be set to a URL (not just hostname). Otherwise Keycloak would not know what is the correct frontend URL (incl. port etc.) when accessing the Admin Console.
- If hostname-backchannel-dynamic is set to true, hostname must be set to a URL (not just hostname). Otherwise Keycloak would not know what is the correct frontend URL (incl. port etc.) when being access via the dynamically resolved backchannel.
If hostname-backchannel-dynamic is set to true, hostname must be set to a URL (not just hostname). Otherwise Keycloak would not know what is the correct frontend URL (incl. port etc.) when being access via the dynamically resolved backchannel.
Additionally if hostname is configured, then hostname-strict is ignored.

## Troubleshooting

To troubleshoot the hostname configuration, you can use a dedicated debug tool which can be enabled as:
After Keycloak starts properly, open your browser and go to: http://mykeycloak:8080/realms/<your-realm>/hostname-debug

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
hostname-backchannel-dynamic Enables dynamic resolving of backchannel URLs, including hostname, scheme, port and context path. Set to true if your application accesses Keycloak via a private network. If set to true, hostname option needs to be specified as a full URL. CLI: --hostname-backchannel-dynamic Env: KC_HOSTNAME_BACKCHANNEL_DYNAMIC Available only when hostname:v2 feature is enabled
hostname-backchannel-dynamic
Enables dynamic resolving of backchannel URLs, including hostname, scheme, port and context path.
Set to true if your application accesses Keycloak via a private network. If set to true, hostname option needs to be specified as a full URL.
CLI: --hostname-backchannel-dynamic Env: KC_HOSTNAME_BACKCHANNEL_DYNAMIC
Available only when hostname:v2 feature is enabled
true , false (default)
true , false (default)
hostname-debug Toggles the hostname debug page that is accessible at /realms/master/hostname-debug. CLI: --hostname-debug Env: KC_HOSTNAME_DEBUG Available only when hostname:v2 feature is enabled
hostname-debug
Toggles the hostname debug page that is accessible at /realms/master/hostname-debug.
CLI: --hostname-debug Env: KC_HOSTNAME_DEBUG
Available only when hostname:v2 feature is enabled
true , false (default)
true , false (default)
hostname-strict Disables dynamically resolving the hostname from request headers. Should always be set to true in production, unless your reverse proxy overwrites the Host header. If enabled, the hostname option needs to be specified. CLI: --hostname-strict Env: KC_HOSTNAME_STRICT Available only when hostname:v2 feature is enabled
hostname-strict
Disables dynamically resolving the hostname from request headers.
Should always be set to true in production, unless your reverse proxy overwrites the Host header. If enabled, the hostname option needs to be specified.
CLI: --hostname-strict Env: KC_HOSTNAME_STRICT
Available only when hostname:v2 feature is enabled
true (default), false
true (default), false

---
Quelle: https://www.keycloak.org/server/hostname
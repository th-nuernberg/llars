# Configuring the Management Interface - Keycloak

# Configuring the Management Interface

The management interface allows accessing management endpoints via a different HTTP server than the primary one.
It provides the possibility to hide endpoints like /metrics or /health from the outside world and, therefore, hardens the security.
The most significant advantage might be seen in Kubernetes environments as the specific management port might not be exposed.

## Management interface configuration

The management interface is turned on when something is exposed on it.
Management endpoints such as /metrics and /health are exposed on the default management port 9000 when metrics and health are enabled.
The management interface provides a set of options and is fully configurable.
If management interface properties are not explicitly set, their values are automatically inherited from the default HTTP server.
In order to change the port for the management interface, you can use the Keycloak option http-management-port .

### Relative path

You can change the relative path of the management interface, as the prefix path for the management endpoints can be different.
You can achieve it via the Keycloak option http-management-relative-path .
For instance, if you set the CLI option --http-management-relative-path=/management , the metrics, and health endpoints will be accessed on the /management/metrics and /management/health paths.
User is automatically redirected to the path where Keycloak is hosted when the relative path is specified.
It means when the relative path is set to /management , and the user access localhost:9000/ , the page is redirected to localhost:9000/management .
If you do not explicitly set the value for it, the value from the http-relative-path property is used. For instance,
if you set the CLI option --http-relative-path=/auth , these endpoints are accessible on the /auth/metrics and /auth/health paths.

### TLS support

When the TLS is set for the default Keycloak server, by default the management interface will be accessible through HTTPS as well.
The management interface can run only either on HTTP or HTTPS, not both as for the main server.
If you do not want the management interface to use HTTPS, you may set the http-management-scheme option to http .
Specific Keycloak management interface options with the prefix https-management-* were provided for setting different TLS parameters for the management HTTP server. Their function is similar to their counterparts for the main HTTP server, for details see Configuring TLS .
When these options are not explicitly set, the TLS parameters are inherited from the default HTTP server.

### Disable Management interface

The management interface is automatically turned off when nothing is exposed on it.
Currently, only health checks and metrics are exposed on the management interface regardless.
If you want to disable exposing them on the management interface, set the Keycloak property legacy-observability-interface to true .
Exposing health and metrics endpoints on the default server is not recommended for security reasons, and you should always use the management interface.
Beware, the legacy-observability-interface option is deprecated and will be removed in future releases.
It only allows you to give more time for the migration.
Exposing health and metrics endpoints on the default server is not recommended for security reasons, and you should always use the management interface.
Beware, the legacy-observability-interface option is deprecated and will be removed in future releases.
It only allows you to give more time for the migration.

## Relevant options

http-management-health-enabled If health endpoints should be exposed on the management interface. If false, health endpoints will be exposed on the main interface. CLI: --http-management-health-enabled Env: KC_HTTP_MANAGEMENT_HEALTH_ENABLED Available only when health is enabled
http-management-health-enabled
If health endpoints should be exposed on the management interface.
If false, health endpoints will be exposed on the main interface.
CLI: --http-management-health-enabled Env: KC_HTTP_MANAGEMENT_HEALTH_ENABLED
Available only when health is enabled
true (default), false
true (default), false
http-management-port Port of the management interface. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --http-management-port Env: KC_HTTP_MANAGEMENT_PORT
http-management-port
Port of the management interface.
Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --http-management-port Env: KC_HTTP_MANAGEMENT_PORT
9000 (default)
9000 (default)
http-management-relative-path Set the path relative to / for serving resources from management interface. The path must start with a / . If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --http-management-relative-path Env: KC_HTTP_MANAGEMENT_RELATIVE_PATH
http-management-relative-path
Set the path relative to / for serving resources from management interface.
The path must start with a / . If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --http-management-relative-path Env: KC_HTTP_MANAGEMENT_RELATIVE_PATH
/ (default)
/ (default)
http-management-scheme Configures the management interface scheme. If inherited , the management interface will inherit the HTTPS settings of the main interface. If http , the management interface will be accessible via HTTP - it will not inherit HTTPS settings and cannot be configured for HTTPS. CLI: --http-management-scheme Env: KC_HTTP_MANAGEMENT_SCHEME
http-management-scheme
Configures the management interface scheme.
If inherited , the management interface will inherit the HTTPS settings of the main interface. If http , the management interface will be accessible via HTTP - it will not inherit HTTPS settings and cannot be configured for HTTPS.
CLI: --http-management-scheme Env: KC_HTTP_MANAGEMENT_SCHEME
http , inherited (default)
http , inherited (default)
https-management-certificate-file The file path to a server certificate or certificate chain in PEM format for the management server. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-certificate-file Env: KC_HTTPS_MANAGEMENT_CERTIFICATE_FILE Available only when http-management-scheme is inherited
https-management-certificate-file
The file path to a server certificate or certificate chain in PEM format for the management server.
If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-certificate-file Env: KC_HTTPS_MANAGEMENT_CERTIFICATE_FILE
Available only when http-management-scheme is inherited
https-management-certificate-key-file The file path to a private key in PEM format for the management server. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-certificate-key-file Env: KC_HTTPS_MANAGEMENT_CERTIFICATE_KEY_FILE Available only when http-management-scheme is inherited
https-management-certificate-key-file
The file path to a private key in PEM format for the management server.
If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-certificate-key-file Env: KC_HTTPS_MANAGEMENT_CERTIFICATE_KEY_FILE
Available only when http-management-scheme is inherited
https-management-certificates-reload-period Interval on which to reload key store, trust store, and certificate files referenced by https-management-* options for the management server. May be an ISO 8601 duration value, an integer number of seconds, or an integer followed by one of [ms, h, m, s, d]. Must be greater than 30 seconds. Use -1 to disable. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-certificates-reload-period Env: KC_HTTPS_MANAGEMENT_CERTIFICATES_RELOAD_PERIOD Available only when http-management-scheme is inherited
https-management-certificates-reload-period
Interval on which to reload key store, trust store, and certificate files referenced by https-management-* options for the management server.
May be an ISO 8601 duration value, an integer number of seconds, or an integer followed by one of [ms, h, m, s, d]. Must be greater than 30 seconds. Use -1 to disable. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-certificates-reload-period Env: KC_HTTPS_MANAGEMENT_CERTIFICATES_RELOAD_PERIOD
Available only when http-management-scheme is inherited
1h (default)
1h (default)
https-management-client-auth Configures the management interface to require/request client authentication. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-client-auth Env: KC_HTTPS_MANAGEMENT_CLIENT_AUTH
https-management-client-auth
Configures the management interface to require/request client authentication.
If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-client-auth Env: KC_HTTPS_MANAGEMENT_CLIENT_AUTH
none (default), request , required
none (default), request , required
https-management-key-store-file The key store which holds the certificate information instead of specifying separate files for the management server. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-key-store-file Env: KC_HTTPS_MANAGEMENT_KEY_STORE_FILE Available only when http-management-scheme is inherited
https-management-key-store-file
The key store which holds the certificate information instead of specifying separate files for the management server.
If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-key-store-file Env: KC_HTTPS_MANAGEMENT_KEY_STORE_FILE
Available only when http-management-scheme is inherited
https-management-key-store-password The password of the key store file for the management server. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-key-store-password Env: KC_HTTPS_MANAGEMENT_KEY_STORE_PASSWORD Available only when http-management-scheme is inherited
https-management-key-store-password
The password of the key store file for the management server.
If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-key-store-password Env: KC_HTTPS_MANAGEMENT_KEY_STORE_PASSWORD
Available only when http-management-scheme is inherited
password (default)
password (default)
legacy-observability-interface If metrics/health endpoints should be exposed on the main HTTP server (not recommended). If set to true, the management interface is disabled. CLI: --legacy-observability-interface Env: KC_LEGACY_OBSERVABILITY_INTERFACE DEPRECATED.
legacy-observability-interface
If metrics/health endpoints should be exposed on the main HTTP server (not recommended).
If set to true, the management interface is disabled.
CLI: --legacy-observability-interface Env: KC_LEGACY_OBSERVABILITY_INTERFACE
DEPRECATED.
true , false (default)
true , false (default)

---
Quelle: https://www.keycloak.org/server/management-interface
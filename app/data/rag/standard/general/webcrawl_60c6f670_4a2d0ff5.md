# Configuring trusted certificates for mTLS - Keycloak

# Configuring trusted certificates for mTLS

In order to properly validate client certificates and enable certain authentication methods like two-way TLS or mTLS, you can set
a trust store with all the certificates (and certificate chain) the server should be trusting. There are number of capabilities that rely
on this trust store to properly authenticate clients using certificates such as Mutual TLS and X.509 Authentication.

## Enabling mTLS

Authentication using mTLS is disabled by default. To enable mTLS certificate handling when Keycloak is the server and needs to validate
certificates from requests made to Keycloak endpoints, put the appropriate certificates in a truststore and use the following
command to enable mTLS:
Using the value required sets up Keycloak to always ask for certificates and fail if no certificate is provided in a request. By setting
the value to request , Keycloak will also accept requests without a certificate and only validate the correctness of a certificate if it exists.
The mTLS configuration and the truststore is shared by all Realms. It is not possible to configure different truststores for different Realms.
Management interface properties are inherited from the main HTTP server, including mTLS settings.
It means when mTLS is set, it is also enabled for the management interface.
To override the behavior, use the https-management-client-auth property.

## Using a dedicated truststore for mTLS

By default, Keycloak uses the System Truststore to validate certificates. See Configuring trusted certificates for details.
If you need to use a dedicated truststore for mTLS, you can configure the location of this truststore by running the following command:
Recognized file extensions for a truststore:
- .p12 , .pkcs12 , and .pfx for a pkcs12 file
.p12 , .pkcs12 , and .pfx for a pkcs12 file
- .jks , and .truststore for a jks file
.jks , and .truststore for a jks file
- .ca , .crt , and .pem for a pem file
.ca , .crt , and .pem for a pem file
If your truststore does not have an extension matching its file type, you will also need to set the https-key-store-type option.

## Additional resources

### Using mTLS for outgoing HTTP requests

Be aware that this is the basic certificate configuration for mTLS use cases where Keycloak acts as server. When Keycloak acts as client
instead, e.g. when Keycloak tries to get a token from a token endpoint of a brokered identity provider that is secured by mTLS, you need to set up
the HttpClient to provide the right certificates in the keystore for the outgoing request. To configure mTLS in these scenarios, see Configuring outgoing HTTP requests .

### Configuring X.509 Authentication

For more information on how to configure X.509 Authentication, see X.509 Client Certificate User Authentication section .

## Relevant options

https-client-auth Configures the server to require/request client authentication. CLI: --https-client-auth Env: KC_HTTPS_CLIENT_AUTH
https-client-auth
Configures the server to require/request client authentication.
CLI: --https-client-auth Env: KC_HTTPS_CLIENT_AUTH
none (default), request , required
none (default), request , required
https-trust-store-file The trust store which holds the certificate information of the certificates to trust. CLI: --https-trust-store-file Env: KC_HTTPS_TRUST_STORE_FILE
https-trust-store-file
The trust store which holds the certificate information of the certificates to trust.
CLI: --https-trust-store-file Env: KC_HTTPS_TRUST_STORE_FILE
https-trust-store-password The password of the trust store file. CLI: --https-trust-store-password Env: KC_HTTPS_TRUST_STORE_PASSWORD
https-trust-store-password
The password of the trust store file.
CLI: --https-trust-store-password Env: KC_HTTPS_TRUST_STORE_PASSWORD
https-trust-store-type The type of the trust store file. If not given, the type is automatically detected based on the file extension. If fips-mode is set to strict and no value is set, it defaults to BCFKS . CLI: --https-trust-store-type Env: KC_HTTPS_TRUST_STORE_TYPE
https-trust-store-type
The type of the trust store file.
If not given, the type is automatically detected based on the file extension. If fips-mode is set to strict and no value is set, it defaults to BCFKS .
CLI: --https-trust-store-type Env: KC_HTTPS_TRUST_STORE_TYPE
https-management-client-auth Configures the management interface to require/request client authentication. If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details. CLI: --https-management-client-auth Env: KC_HTTPS_MANAGEMENT_CLIENT_AUTH
https-management-client-auth
Configures the management interface to require/request client authentication.
If not given, the value is inherited from HTTP options. Relevant only when something is exposed on the management interface - see the guide for details.
CLI: --https-management-client-auth Env: KC_HTTPS_MANAGEMENT_CLIENT_AUTH
none (default), request , required
none (default), request , required

---
Quelle: https://www.keycloak.org/server/mutual-tls
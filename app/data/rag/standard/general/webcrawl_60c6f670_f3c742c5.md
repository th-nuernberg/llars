# Securing applications and services with OpenID Connect - Keycloak

# Securing applications and services with OpenID Connect

## Available Endpoints

As a fully-compliant OpenID Connect Provider implementation, Keycloak exposes a set of endpoints that applications
and services can use to authenticate and authorize their users.
This section describes some of the key endpoints that your application and service should use when
interacting with Keycloak.
The most important endpoint to understand is the well-known configuration endpoint. It lists endpoints and other configuration options relevant to the OpenID Connect implementation in Keycloak. The endpoint is:
To obtain the full URL, add the base URL for Keycloak and replace {realm-name} with the name of your realm. For example:
Some RP libraries retrieve all required endpoints from this endpoint, but for others you might need to list the endpoints individually.

#### Authorization endpoint

The authorization endpoint performs authentication of the end-user. This authentication is done by redirecting the user agent to this endpoint.
For more details see the Authorization Endpoint section in the OpenID Connect specification.

#### Token endpoint

The token endpoint is used to obtain tokens. Tokens can either be obtained by exchanging an authorization code or by supplying credentials directly depending on what flow is used.
The token endpoint is also used to obtain new access tokens when they expire.
For more details, see the Token Endpoint section in the OpenID Connect specification.

#### Userinfo endpoint

The userinfo endpoint returns standard claims about the authenticated user; this endpoint is protected by a bearer token.
For more details, see the Userinfo Endpoint section in the OpenID Connect specification.

#### Logout endpoint

The logout endpoint logs out the authenticated user.
The user agent can be redirected to the endpoint, which causes the active user session to be logged out. The user agent is then redirected back to the application.
This is described in more details in the RP-Initiated logout section of the Server administration guide .
The endpoint can also be invoked directly by the application. To invoke this endpoint directly, the refresh token needs to be included as well as the credentials required to authenticate the client.
However this is non-standard legacy format of the logout message supported only because of the legacy Keycloak OIDC Java adapters
or Elytron Wildfly OIDC adapter . It is not recommended to use it directly from your applications.
For logout users, it is recommended to use either OIDC/SAML protocol standard logout or Keycloak Admin console (or other way of admin REST API)
or Keycloak Account console (or other way of account REST API).

#### Certificate endpoint

The certificate endpoint returns the public keys enabled by the realm, encoded as a JSON Web Key (JWK). Depending on the realm settings, one or more keys can be enabled for verifying tokens. For more information, see the Server Administration Guide and the JSON Web Key specification .
For more details, see the OpenID Connect Discovery specification.

#### Introspection endpoint

The introspection endpoint is used to retrieve the active state of a token. In other words, you can use it to validate an access or refresh token.
This endpoint can only be invoked by confidential clients.
For more details on how to invoke on this endpoint, see OAuth 2.0 Token Introspection specification .
You can invoke an introspection endpoint with the HTTP header Accept: application/jwt instead of Accept: application/json . In case of application/jwt , the response
may contain the additional claim jwt with the full JWT access token, which can be useful especially if the token to be introspected was a lightweight access token . This requires that you enable Support JWT claim in Introspection Response on the client advanced settings, which triggers the token introspection.

#### Dynamic Client Registration endpoint

The dynamic client registration endpoint is used to dynamically register clients.
For more details, see the Using the client registration service guide and the OpenID Connect Dynamic Client Registration specification .

#### Token Revocation endpoint

The token revocation endpoint is used to revoke tokens. Both refresh tokens and access tokens are supported by this endpoint. When revoking a refresh token, the user consent for the corresponding client is also revoked.
For more details on how to invoke on this endpoint, see OAuth 2.0 Token Revocation specification .

#### Device Authorization endpoint

The device authorization endpoint is used to obtain a device code and a user code. It can be invoked by confidential or public clients.
For more details on how to invoke on this endpoint, see OAuth 2.0 Device Authorization Grant specification .

#### Backchannel Authentication endpoint

The backchannel authentication endpoint is used to obtain an auth_req_id that identifies the authentication request made by the client. It can only be invoked by confidential clients.
For more details on how to invoke on this endpoint, see OpenID Connect Client Initiated Backchannel Authentication Flow specification .
Also refer to other places of Keycloak documentation like Client Initiated Backchannel Authentication Grant section of this guide and Client Initiated Backchannel Authentication Grant section of Server Administration Guide.

## Supported Grant Types

This section describes the different grant types available to relaying parties.

### Authorization code

The Authorization Code flow redirects the user agent to Keycloak. Once the user has successfully authenticated with Keycloak, an
Authorization Code is created and the user agent is redirected back to the application. The application then uses the authorization code along with its
credentials to obtain an Access Token, Refresh Token and ID Token from Keycloak.
The flow is targeted towards web applications, but is also recommended for native applications, including mobile applications, where it is possible to embed
a user agent.
For more details refer to the Authorization Code Flow in the OpenID Connect specification.
The Implicit flow works similarly to the Authorization Code flow, but instead of returning an Authorization Code, the Access Token and ID Token is
returned. This approach reduces the need for the extra invocation to exchange the Authorization Code for an Access Token. However, it does not include a Refresh
Token. This results in the need to permit Access Tokens with a long expiration; however, that approach is not practical because it is very hard to invalidate these tokens. Alternatively, you can
require a new redirect to obtain a new Access Token once the initial Access Token has expired. The Implicit flow is useful if the application only wants to
authenticate the user and deals with logout itself.
You can instead use a Hybrid flow where both the Access Token and an Authorization Code are returned.
One thing to note is that both the Implicit flow and Hybrid flow have potential security risks as the Access Token may be leaked through web server logs and
browser history. You can somewhat mitigate this problem by using short expiration for Access Tokens.
For more details, see the Implicit Flow in the OpenID Connect specification.
Per current Best Current Practice for OAuth 2.0 Security (RFC 9700) , this flow SHOULD NOT be used.
This flow is removed from the future OAuth 2.1 specification .

### Resource Owner Password Credentials

Resource Owner Password Credentials, referred to as Direct Grant in Keycloak, allows exchanging user credentials for tokens.
Per current Best Current Practice for OAuth 2.0 Security (RFC 9700) ,
this flow MUST NOT be used, preferring alternative methods such as Device Authorization Grant or Authorization code .
The limitations of using this flow include:
- User credentials are exposed to the application
User credentials are exposed to the application
- Applications need login pages
Applications need login pages
- Application needs to be aware of the authentication scheme
Application needs to be aware of the authentication scheme
- Changes to authentication flow requires changes to application
Changes to authentication flow requires changes to application
- No support for identity brokering or social login
No support for identity brokering or social login
- Flows are not supported (user self-registration, required actions, and so on.)
Flows are not supported (user self-registration, required actions, and so on.)
Security concerns with this flow include:
- Involving more than Keycloak in handling of credentials
Involving more than Keycloak in handling of credentials
- Increased vulnerable surface area where credential leaks can happen
Increased vulnerable surface area where credential leaks can happen
- Creating an ecosystem where users trust another application for entering their credentials and not Keycloak
Creating an ecosystem where users trust another application for entering their credentials and not Keycloak
For a client to be permitted to use the Resource Owner Password Credentials grant, the client has to have the Direct Access Grants Enabled option enabled.
This flow is not included in OpenID Connect, but is a part of the OAuth 2.0 specification.
It is removed from the future OAuth 2.1 specification .
For more details, see the Resource Owner Password Credentials Grant chapter in the OAuth 2.0 specification.

#### Example using CURL

The following example shows how to obtain an access token for a user in the realm master with username user and password password . The example is using
the confidential client myclient :

### Client credentials

Client Credentials are used when clients (applications and services) want to obtain access on behalf of themselves rather than on behalf of a user. For example, these credentials can
 be useful for background services that apply changes to the system in general rather than for a specific user.
Keycloak provides support for clients to authenticate either with a secret or with public/private keys.
This flow is not included in OpenID Connect, but is a part of the OAuth 2.0 specification.
For more details, see the Client Credentials Grant chapter in the OAuth 2.0 specification.

### Device Authorization Grant

Device Authorization Grant is used by clients running on internet-connected devices that have limited input capabilities or lack a suitable browser.
- The application requests that Keycloak provide a device code and a user code.
The application requests that Keycloak provide a device code and a user code.
- Keycloak creates a device code and a user code.
Keycloak creates a device code and a user code.
- Keycloak returns a response including the device code and the user code to the application.
Keycloak returns a response including the device code and the user code to the application.
- The application provides the user with the user code and the verification URI. The user accesses a verification URI to be authenticated by using another browser.
The application provides the user with the user code and the verification URI. The user accesses a verification URI to be authenticated by using another browser.
- The application repeatedly polls Keycloak until Keycloak completes the user authorization.
The application repeatedly polls Keycloak until Keycloak completes the user authorization.
- If user authentication is complete, the application obtains the device code.
If user authentication is complete, the application obtains the device code.
- The application uses the device code along with its credentials to obtain an Access Token, Refresh Token and ID Token from Keycloak.
The application uses the device code along with its credentials to obtain an Access Token, Refresh Token and ID Token from Keycloak.
For more details, see the OAuth 2.0 Device Authorization Grant specification .

### Client Initiated Backchannel Authentication Grant

Client Initiated Backchannel Authentication Grant is used by clients who want to initiate the authentication flow by communicating with the OpenID Provider directly without redirect through the user’s browser like OAuth 2.0’s authorization code grant.
The client requests from Keycloak an auth_req_id that identifies the authentication request made by the client. Keycloak creates the auth_req_id.
After receiving this auth_req_id, this client repeatedly needs to poll Keycloak to obtain an Access Token, Refresh Token, and ID Token from Keycloak in return for the auth_req_id until the user is authenticated.
In case that client uses ping mode, it does not need to repeatedly poll the token endpoint, but it can wait for the notification sent by Keycloak to the specified Client Notification Endpoint.
The Client Notification Endpoint can be configured in the Keycloak Admin Console. The details of the contract for Client Notification Endpoint are described in the CIBA specification.
For more details, see OpenID Connect Client Initiated Backchannel Authentication Flow specification .
Also refer to other places of Keycloak documentation such as Backchannel Authentication Endpoint of this guide and Client Initiated Backchannel Authentication Grant section of Server Administration Guide.
For the details about FAPI CIBA compliance, see the FAPI section of this guide .

## Keycloak specific errors

Keycloak server can send errors to the client application in the OIDC authentication response with parameters error=temporarily_unavailable and error_description=authentication_expired .
Keycloak sends this error when a user is authenticated and has an SSO session, but the authentication session expired in the current browser tab and hence the Keycloak server cannot automatically do SSO
re-authentication of the user and redirect back to client with a successful response. When a client application receives this type of error, it is ideal to retry authentication immediately and send a new
OIDC authentication request to the Keycloak server, which should typically always authenticate the user due to the SSO session and redirect back. For more details, see
the Server Administration Guide .

## Financial-grade API (FAPI) Support

Keycloak makes it easier for administrators to make sure that their clients are compliant with these specifications:
- Financial-grade API Security Profile 1.0 - Part 1: Baseline
Financial-grade API Security Profile 1.0 - Part 1: Baseline
- Financial-grade API Security Profile 1.0 - Part 2: Advanced
Financial-grade API Security Profile 1.0 - Part 2: Advanced
- Financial-grade API: Client Initiated Backchannel Authentication Profile (FAPI CIBA)
Financial-grade API: Client Initiated Backchannel Authentication Profile (FAPI CIBA)
- FAPI 2.0 Security Profile (Final)
FAPI 2.0 Security Profile (Final)
- FAPI 2.0 Message Signing (Final)
FAPI 2.0 Message Signing (Final)
This compliance means that the Keycloak server will verify the requirements
for the authorization server, which are mentioned in the specifications. Keycloak adapters do not have any specific support for the FAPI, hence the required validations on the client (application)
side may need to be still done manually or through some other third-party solutions.

### FAPI client profiles

To make sure that your clients are FAPI compliant, you can configure Client Policies in your realm as described in the Server Administration Guide and link them to the global client profiles for FAPI support, which are automatically available in each realm. You can use either fapi-1-baseline or fapi-1-advanced profile based on which FAPI
profile you need your clients to conform with. You can use also profiles fapi-2-security-profile , fapi-2-dpop-security-profile , fapi-2-message-signing and fapi-2-dpop-message-signing for the compliance with FAPI 2.0 specifications.
In case you want to use Pushed Authorization Request (PAR) , it is recommended that your client use
both the fapi-1-baseline profile and fapi-1-advanced for PAR requests. Specifically, the fapi-1-baseline profile contains pkce-enforcer executor, which makes sure
that client use PKCE with secured S256 algorithm. This is not required for FAPI Advanced clients unless they use PAR requests.
In case you want to use CIBA in a FAPI compliant way, make sure that your clients use both fapi-1-advanced and fapi-ciba client profiles.
There is a need to use the fapi-1-advanced profile, or other client profile containing the requested executors, as the fapi-ciba profile contains just CIBA-specific executors.
When enforcing the requirements of the FAPI CIBA specification, there is a need for more requirements, such as enforcement of confidential clients or certificate-bound access tokens.

### Open Finance Brasil Financial-grade API Security Profile

Keycloak is compliant with the Open Finance Brasil Financial-grade API Security Profile 1.0 Implementers Draft 3 .
This one is stricter in some requirements than the FAPI 1 Advanced specification and hence it may be needed to configure Client Policies in the more strict way to enforce some of the requirements. Especially:
- If your client does not use PAR, make sure that it uses encrypted OIDC request objects. This can be achieved by using a client profile with the secure-request-object executor configured with Encryption Required enabled.
If your client does not use PAR, make sure that it uses encrypted OIDC request objects. This can be achieved by using a client profile with the secure-request-object executor configured with Encryption Required enabled.
- Make sure that for JWS, the client uses the PS256 algorithm. For JWE, the client should use the RSA-OAEP with A256GCM . This may need to be set in all the Client Settings where these algorithms are applicable.
Make sure that for JWS, the client uses the PS256 algorithm. For JWE, the client should use the RSA-OAEP with A256GCM . This may need to be set in all the Client Settings where these algorithms are applicable.

### Australia Consumer Data Right (CDR) Security Profile

Keycloak is compliant with the Australia Consumer Data Right Security Profile .
If you want to apply the Australia CDR security profile, you need to use fapi-1-advanced profile because the Australia CDR security profile is based on FAPI 1.0 Advanced security profile. If your client also applies PAR, make sure that client applies RFC 7637 Proof Key for Code Exchange (PKCE) because the Australia CDR security profile requires that you apply PKCE when applying PAR. This can be achieved by using a client profile with the pkce-enforcer executor.

### TLS considerations

As confidential information is being exchanged, all interactions shall be encrypted with TLS (HTTPS). Moreover, there are some requirements in the FAPI specification for
the cipher suites and TLS protocol versions used. To match these requirements, you can consider configure allowed ciphers. This configuration can be done by setting
the https-protocols and https-cipher-suites options. Keycloak uses TLSv1.3 by default and hence it is possibly not needed to change the default settings. However it
may be needed to adjust ciphers if you need to fall back to lower TLS version for some reason. For more details, see Configuring TLS guide.

## OAuth 2.1 Support

Keycloak makes it easier for administrators to make sure that their clients are compliant with these specifications:
- The OAuth 2.1 Authorization Framework - draft specification
The OAuth 2.1 Authorization Framework - draft specification
This compliance means that the Keycloak server will verify the requirements
for the authorization server, which are mentioned in the specifications. Keycloak adapters do not have any specific support for the OAuth 2.1, hence the required validations on the client (application)
side may need to be still done manually or through some other third-party solutions.

### OAuth 2.1 client profiles

To make sure that your clients are OAuth 2.1 compliant, you can configure Client Policies in your realm as described in the Server Administration Guide and link them to the global client profiles for OAuth 2.1 support, which are automatically available in each realm. You can use either oauth-2-1-for-confidential-client profile for confidential clients or oauth-2-1-for-public-client profile for public clients.
OAuth 2.1 specification is still a draft and it may change in the future. Hence the Keycloak built-in OAuth 2.1 client profiles can change as well.
When using OAuth 2.1 profile for public clients, it is recommended to use DPoP preview feature as described in the Server Administration Guide because DPoP binds an access token and a refresh token together with the public part of a client’s key pair. This binding prevents an attacker from using stolen tokens.

## Recommendations

This section describes some recommendations when securing your applications with Keycloak.

### Validating access tokens

If you need to manually validate access tokens issued by Keycloak, you can invoke the Introspection Endpoint .
The downside to this approach is that you have to make a network invocation to the Keycloak server. This can be slow and possibly overload the
server if you have too many validation requests going on at the same time. Keycloak issued access tokens are JSON Web Tokens (JWT) digitally signed and encoded using JSON Web Signature (JWS) .
Because they are encoded in this way, you can locally validate access tokens using the public key of the issuing realm. You can either hard code the
realm’s public key in your validation code, or lookup and cache the public key using the certificate endpoint with the Key ID (KID) embedded within the
JWS. Depending on what language you code in, many third party libraries exist and they can help you with JWS validation.

### Redirect URIs

When using the redirect based flows, be sure to use valid redirect uris for your clients. The redirect uris should be as specific as possible. This
especially applies to client-side (public clients) applications. Failing to do so could result in:
- Open redirects - this can allow attackers to create spoof links that looks like they are coming from your domain
Open redirects - this can allow attackers to create spoof links that looks like they are coming from your domain
- Unauthorized entry - when users are already authenticated with Keycloak, an attacker can use a public client where redirect uris have not be configured correctly to gain access by redirecting the user without the users knowledge
Unauthorized entry - when users are already authenticated with Keycloak, an attacker can use a public client where redirect uris have not be configured correctly to gain access by redirecting the user without the users knowledge
In production for web applications always use https for all redirect URIs. Do not allow redirects to http.
A few special redirect URIs also exist:
This redirect URI is useful for native applications and allows the native application to create a web server on a random port that can be used to obtain the
authorization code. This redirect uri allows any port. Note that per OAuth 2.0 for Native Apps , the use of localhost is not recommended and the IP literal 127.0.0.1 should be used instead.
If you cannot start a web server in the client (or a browser is not available), you can use the special urn:ietf:wg:oauth:2.0:oob redirect uri.
When this redirect uri is used, Keycloak displays a page with the code in the title and in a box on the page.
The application can either detect that the browser title has changed, or the user can copy and paste the code manually to the application.
With this redirect uri, a user can use a different device to obtain a code to paste back to the application.

---
Quelle: https://www.keycloak.org/securing-apps/oidc-layers
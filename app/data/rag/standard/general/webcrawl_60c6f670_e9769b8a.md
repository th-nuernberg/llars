# Enabling and disabling features - Keycloak

# Enabling and disabling features

Keycloak has packed some functionality in features, including some disabled features, such as Technology Preview and deprecated features. Other features are enabled by default, but you can disable them if they do not apply to your use of Keycloak.

## Enabling features

Some supported features, and all preview features, are disabled by default. To enable a feature, enter this command:
For example, to enable docker and token-exchange , enter this command:
To enable all preview features, enter this command:
Enabled feature may be versioned, or unversioned. If you use a versioned feature name, e.g. feature:v1, that exact feature version will be enabled as long as it still exists in the runtime. If you instead use an unversioned name, e.g. just feature, the selection of the particular supported feature version may change from release to release according to the following precedence:
- The highest default supported version
The highest default supported version
- The highest non-default supported version
The highest non-default supported version
- The highest deprecated version
The highest deprecated version
- The highest preview version
The highest preview version
- The highest experimental version
The highest experimental version

## Disabling features

To disable a feature that is enabled by default, enter this command:
For example to disable impersonation , enter this command:
It is not allowed to have a feature in both the features-disabled list and the features list.
When a feature is disabled all versions of that feature are disabled.

## Supported features

The following list contains supported features that are enabled by default, and can be disabled if not needed.
Description
account-api:v1
account-api:v1
Account Management REST API
Account Management REST API
Account Console version 3
Account Console version 3
admin-api:v1
admin-api:v1
admin-fine-grained-authz:v2
admin-fine-grained-authz:v2
Fine-Grained Admin Permissions version 2
Fine-Grained Admin Permissions version 2
New Admin Console
New Admin Console
authorization:v1
authorization:v1
Authorization Service
Authorization Service
OpenID Connect Client Initiated Backchannel Authentication (CIBA)
OpenID Connect Client Initiated Backchannel Authentication (CIBA)
client-policies:v1
client-policies:v1
Client configuration policies
Client configuration policies
device-flow:v1
device-flow:v1
OAuth 2.0 Device Authorization Grant
OAuth 2.0 Device Authorization Grant
OAuth 2.0 Demonstrating Proof-of-Possession at the Application Layer
OAuth 2.0 Demonstrating Proof-of-Possession at the Application Layer
hostname:v2
hostname:v2
Hostname Options V2
Hostname Options V2
impersonation:v1
impersonation:v1
Ability for admins to impersonate users
Ability for admins to impersonate users
kerberos:v1
kerberos:v1
New Login Theme
New Login Theme
opentelemetry:v1
opentelemetry:v1
OpenTelemetry Tracing
OpenTelemetry Tracing
organization:v1
organization:v1
Organization support within realms
Organization support within realms
OAuth 2.0 Pushed Authorization Requests (PAR)
OAuth 2.0 Pushed Authorization Requests (PAR)
passkeys:v1
passkeys:v1
persistent-user-sessions:v1
persistent-user-sessions:v1
Persistent online user sessions across restarts and upgrades
Persistent online user sessions across restarts and upgrades
recovery-codes:v1
recovery-codes:v1
Recovery codes
Recovery codes
rolling-updates:v1
rolling-updates:v1
Rolling Updates
Rolling Updates
step-up-authentication:v1
step-up-authentication:v1
Step-up Authentication
Step-up Authentication
token-exchange-standard:v2
token-exchange-standard:v2
Standard Token Exchange version 2
Standard Token Exchange version 2
update-email:v1
update-email:v1
Update Email Action
Update Email Action
user-event-metrics:v1
user-event-metrics:v1
Collect metrics based on user events
Collect metrics based on user events
web-authn:v1
web-authn:v1
W3C Web Authentication (WebAuthn)
W3C Web Authentication (WebAuthn)

### Disabled by default

The following list contains supported features that are disabled by default, and can be enabled if needed.
Description
Docker Registry protocol
Docker Registry protocol
FIPS 140-2 mode
FIPS 140-2 mode
multi-site:v1
multi-site:v1
Multi-site support
Multi-site support

## Preview features

Preview features are disabled by default and are not recommended for use in production.
These features may change or be removed at a future release.
Description
admin-fine-grained-authz:v1
admin-fine-grained-authz:v1
Fine-Grained Admin Permissions
Fine-Grained Admin Permissions
client-auth-federated:v1
client-auth-federated:v1
Authenticates client based on assertions issued by identity provider
Authenticates client based on assertions issued by identity provider
client-secret-rotation:v1
client-secret-rotation:v1
Client Secret Rotation
Client Secret Rotation
Mapped Diagnostic Context (MDC) information in logs
Mapped Diagnostic Context (MDC) information in logs
rolling-updates:v2
rolling-updates:v2
Rolling Updates for patch releases
Rolling Updates for patch releases
Write custom authenticators using JavaScript
Write custom authenticators using JavaScript
SPIFFE trust relationship provider
SPIFFE trust relationship provider
token-exchange:v1
token-exchange:v1
Token Exchange Service
Token Exchange Service

## Deprecated features

The following list contains deprecated features that will be removed in a future release. These features are disabled by default.
Description
instagram-broker:v1
instagram-broker:v1
Instagram Identity Broker
Instagram Identity Broker
Legacy Login Theme
Legacy Login Theme
logout-all-sessions:v1
logout-all-sessions:v1
Logout all sessions logs out only regular sessions
Logout all sessions logs out only regular sessions
passkeys-conditional-ui-authenticator:v1
passkeys-conditional-ui-authenticator:v1
Passkeys conditional UI authenticator
Passkeys conditional UI authenticator

## Relevant options

features Enables a set of one or more features. CLI: --features Env: KC_FEATURES
Enables a set of one or more features.
CLI: --features Env: KC_FEATURES
account-api[:v1] , account[:v3] , admin-api[:v1] , admin-fine-grained-authz[:v1,v2] , admin[:v2] , authorization[:v1] , ciba[:v1] , client-auth-federated[:v1] , client-policies[:v1] , client-secret-rotation[:v1] , client-types[:v1] , clusterless[:v1] , db-tidb[:v1] , declarative-ui[:v1] , device-flow[:v1] , docker[:v1] , dpop[:v1] , dynamic-scopes[:v1] , fips[:v1] , hostname[:v2] , impersonation[:v1] , instagram-broker[:v1] , ipa-tuura-federation[:v1] , kerberos[:v1] , kubernetes-service-accounts[:v1] , log-mdc[:v1] , login[:v2,v1] , logout-all-sessions[:v1] , multi-site[:v1] , oid4vc-vci[:v1] , opentelemetry[:v1] , organization[:v1] , par[:v1] , passkeys-conditional-ui-authenticator[:v1] , passkeys[:v1] , persistent-user-sessions[:v1] , preview , quick-theme[:v1] , recovery-codes[:v1] , rolling-updates[:v1,v2] , scripts[:v1] , spiffe[:v1] , step-up-authentication[:v1] , token-exchange-external-internal[:v2] , token-exchange-standard[:v2] , token-exchange[:v1] , transient-users[:v1] , update-email[:v1] , user-event-metrics[:v1] , web-authn[:v1] , workflows[:v1]
account-api[:v1] , account[:v3] , admin-api[:v1] , admin-fine-grained-authz[:v1,v2] , admin[:v2] , authorization[:v1] , ciba[:v1] , client-auth-federated[:v1] , client-policies[:v1] , client-secret-rotation[:v1] , client-types[:v1] , clusterless[:v1] , db-tidb[:v1] , declarative-ui[:v1] , device-flow[:v1] , docker[:v1] , dpop[:v1] , dynamic-scopes[:v1] , fips[:v1] , hostname[:v2] , impersonation[:v1] , instagram-broker[:v1] , ipa-tuura-federation[:v1] , kerberos[:v1] , kubernetes-service-accounts[:v1] , log-mdc[:v1] , login[:v2,v1] , logout-all-sessions[:v1] , multi-site[:v1] , oid4vc-vci[:v1] , opentelemetry[:v1] , organization[:v1] , par[:v1] , passkeys-conditional-ui-authenticator[:v1] , passkeys[:v1] , persistent-user-sessions[:v1] , preview , quick-theme[:v1] , recovery-codes[:v1] , rolling-updates[:v1,v2] , scripts[:v1] , spiffe[:v1] , step-up-authentication[:v1] , token-exchange-external-internal[:v2] , token-exchange-standard[:v2] , token-exchange[:v1] , transient-users[:v1] , update-email[:v1] , user-event-metrics[:v1] , web-authn[:v1] , workflows[:v1]
features-disabled Disables a set of one or more features. CLI: --features-disabled Env: KC_FEATURES_DISABLED
features-disabled
Disables a set of one or more features.
CLI: --features-disabled Env: KC_FEATURES_DISABLED
account , account-api , admin , admin-api , admin-fine-grained-authz , authorization , ciba , client-auth-federated , client-policies , client-secret-rotation , client-types , clusterless , db-tidb , declarative-ui , device-flow , docker , dpop , dynamic-scopes , fips , impersonation , instagram-broker , ipa-tuura-federation , kerberos , kubernetes-service-accounts , log-mdc , login , logout-all-sessions , multi-site , oid4vc-vci , opentelemetry , organization , par , passkeys , passkeys-conditional-ui-authenticator , persistent-user-sessions , preview , quick-theme , recovery-codes , rolling-updates , scripts , spiffe , step-up-authentication , token-exchange , token-exchange-external-internal , token-exchange-standard , transient-users , update-email , user-event-metrics , web-authn , workflows
account , account-api , admin , admin-api , admin-fine-grained-authz , authorization , ciba , client-auth-federated , client-policies , client-secret-rotation , client-types , clusterless , db-tidb , declarative-ui , device-flow , docker , dpop , dynamic-scopes , fips , impersonation , instagram-broker , ipa-tuura-federation , kerberos , kubernetes-service-accounts , log-mdc , login , logout-all-sessions , multi-site , oid4vc-vci , opentelemetry , organization , par , passkeys , passkeys-conditional-ui-authenticator , persistent-user-sessions , preview , quick-theme , recovery-codes , rolling-updates , scripts , spiffe , step-up-authentication , token-exchange , token-exchange-external-internal , token-exchange-standard , transient-users , update-email , user-event-metrics , web-authn , workflows

---
Quelle: https://www.keycloak.org/server/features
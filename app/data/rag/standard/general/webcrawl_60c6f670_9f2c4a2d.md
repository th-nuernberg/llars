# All provider configuration - Keycloak

# All provider configuration

## authentication-sessions

spi-authentication-sessions--infinispan--auth-sessions-limit The maximum number of concurrent authentication sessions per RootAuthenticationSession. CLI: --spi-authentication-sessions--infinispan--auth-sessions-limit Env: KC_SPI_AUTHENTICATION_SESSIONS__INFINISPAN__AUTH_SESSIONS_LIMIT
spi-authentication-sessions--infinispan--auth-sessions-limit
The maximum number of concurrent authentication sessions per RootAuthenticationSession.
CLI: --spi-authentication-sessions--infinispan--auth-sessions-limit Env: KC_SPI_AUTHENTICATION_SESSIONS__INFINISPAN__AUTH_SESSIONS_LIMIT
300 (default) or any int
300 (default) or any int
spi-authentication-sessions--remote--auth-sessions-limit The maximum number of concurrent authentication sessions per RootAuthenticationSession. CLI: --spi-authentication-sessions--remote--auth-sessions-limit Env: KC_SPI_AUTHENTICATION_SESSIONS__REMOTE__AUTH_SESSIONS_LIMIT
spi-authentication-sessions--remote--auth-sessions-limit
The maximum number of concurrent authentication sessions per RootAuthenticationSession.
CLI: --spi-authentication-sessions--remote--auth-sessions-limit Env: KC_SPI_AUTHENTICATION_SESSIONS__REMOTE__AUTH_SESSIONS_LIMIT
300 (default) or any int
300 (default) or any int
spi-authentication-sessions--remote--max-retries The maximum number of retries if an error occurs. A value of zero or less disable any retries. CLI: --spi-authentication-sessions--remote--max-retries Env: KC_SPI_AUTHENTICATION_SESSIONS__REMOTE__MAX_RETRIES
spi-authentication-sessions--remote--max-retries
The maximum number of retries if an error occurs.
A value of zero or less disable any retries.
CLI: --spi-authentication-sessions--remote--max-retries Env: KC_SPI_AUTHENTICATION_SESSIONS__REMOTE__MAX_RETRIES
10 (default) or any int
10 (default) or any int
spi-authentication-sessions--remote--retry-base-time The base back-off time in milliseconds. CLI: --spi-authentication-sessions--remote--retry-base-time Env: KC_SPI_AUTHENTICATION_SESSIONS__REMOTE__RETRY_BASE_TIME
spi-authentication-sessions--remote--retry-base-time
The base back-off time in milliseconds.
CLI: --spi-authentication-sessions--remote--retry-base-time Env: KC_SPI_AUTHENTICATION_SESSIONS__REMOTE__RETRY_BASE_TIME
10 (default) or any int
10 (default) or any int

## brute-force-protector

### default-brute-force-detector

spi-brute-force-protector--default-brute-force-detector--allow-concurrent-requests If concurrent logins are allowed by the brute force protection. CLI: --spi-brute-force-protector--default-brute-force-detector--allow-concurrent-requests Env: KC_SPI_BRUTE_FORCE_PROTECTOR__DEFAULT_BRUTE_FORCE_DETECTOR__ALLOW_CONCURRENT_REQUESTS
spi-brute-force-protector--default-brute-force-detector--allow-concurrent-requests
If concurrent logins are allowed by the brute force protection.
CLI: --spi-brute-force-protector--default-brute-force-detector--allow-concurrent-requests Env: KC_SPI_BRUTE_FORCE_PROTECTOR__DEFAULT_BRUTE_FORCE_DETECTOR__ALLOW_CONCURRENT_REQUESTS
true , false (default)
true , false (default)

## cache-embedded

spi-cache-embedded--default--action-tokens-owners Sets the number of owners for the actionTokens distributed cache. It defines the number of copies of your data in the cluster. CLI: --spi-cache-embedded--default--action-tokens-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__ACTION_TOKENS_OWNERS
spi-cache-embedded--default--action-tokens-owners
Sets the number of owners for the actionTokens distributed cache.
It defines the number of copies of your data in the cluster.
CLI: --spi-cache-embedded--default--action-tokens-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__ACTION_TOKENS_OWNERS
any Integer
any Integer
spi-cache-embedded--default--authentication-sessions-owners Sets the number of owners for the authenticationSessions distributed cache. It defines the number of copies of your data in the cluster. CLI: --spi-cache-embedded--default--authentication-sessions-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__AUTHENTICATION_SESSIONS_OWNERS
spi-cache-embedded--default--authentication-sessions-owners
Sets the number of owners for the authenticationSessions distributed cache.
It defines the number of copies of your data in the cluster.
CLI: --spi-cache-embedded--default--authentication-sessions-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__AUTHENTICATION_SESSIONS_OWNERS
any Integer
any Integer
spi-cache-embedded--default--authorization-max-count The maximum number of entries that can be stored in-memory by the authorization cache. CLI: --spi-cache-embedded--default--authorization-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__AUTHORIZATION_MAX_COUNT
spi-cache-embedded--default--authorization-max-count
The maximum number of entries that can be stored in-memory by the authorization cache.
CLI: --spi-cache-embedded--default--authorization-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__AUTHORIZATION_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--authorization-revisions-max-count The maximum number of entries that can be stored in-memory by the authorizationRevisions cache. CLI: --spi-cache-embedded--default--authorization-revisions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__AUTHORIZATION_REVISIONS_MAX_COUNT
spi-cache-embedded--default--authorization-revisions-max-count
The maximum number of entries that can be stored in-memory by the authorizationRevisions cache.
CLI: --spi-cache-embedded--default--authorization-revisions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__AUTHORIZATION_REVISIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--client-sessions-max-count The maximum number of entries that can be stored in-memory by the clientSessions cache. CLI: --spi-cache-embedded--default--client-sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CLIENT_SESSIONS_MAX_COUNT
spi-cache-embedded--default--client-sessions-max-count
The maximum number of entries that can be stored in-memory by the clientSessions cache.
CLI: --spi-cache-embedded--default--client-sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CLIENT_SESSIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--client-sessions-owners Sets the number of owners for the clientSessions distributed cache. It defines the number of copies of your data in the cluster. CLI: --spi-cache-embedded--default--client-sessions-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CLIENT_SESSIONS_OWNERS
spi-cache-embedded--default--client-sessions-owners
Sets the number of owners for the clientSessions distributed cache.
It defines the number of copies of your data in the cluster.
CLI: --spi-cache-embedded--default--client-sessions-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CLIENT_SESSIONS_OWNERS
any Integer
any Integer
spi-cache-embedded--default--config-file Defines the file from which cache configuration should be loaded from. The configuration file is relative to the conf/ directory. CLI: --spi-cache-embedded--default--config-file Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CONFIG_FILE
spi-cache-embedded--default--config-file
Defines the file from which cache configuration should be loaded from.
The configuration file is relative to the conf/ directory.
CLI: --spi-cache-embedded--default--config-file Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CONFIG_FILE
spi-cache-embedded--default--crl-max-count The maximum number of entries that can be stored in-memory by the crl cache. CLI: --spi-cache-embedded--default--crl-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CRL_MAX_COUNT
spi-cache-embedded--default--crl-max-count
The maximum number of entries that can be stored in-memory by the crl cache.
CLI: --spi-cache-embedded--default--crl-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__CRL_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--keys-max-count The maximum number of entries that can be stored in-memory by the keys cache. CLI: --spi-cache-embedded--default--keys-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__KEYS_MAX_COUNT
spi-cache-embedded--default--keys-max-count
The maximum number of entries that can be stored in-memory by the keys cache.
CLI: --spi-cache-embedded--default--keys-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__KEYS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--login-failures-owners Sets the number of owners for the loginFailures distributed cache. It defines the number of copies of your data in the cluster. CLI: --spi-cache-embedded--default--login-failures-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__LOGIN_FAILURES_OWNERS
spi-cache-embedded--default--login-failures-owners
Sets the number of owners for the loginFailures distributed cache.
It defines the number of copies of your data in the cluster.
CLI: --spi-cache-embedded--default--login-failures-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__LOGIN_FAILURES_OWNERS
any Integer
any Integer
spi-cache-embedded--default--machine-name The name of the physical machine where this instance runs. It can be set if multiple Keycloak instances are running in the same physical machines. Infinispan takes into consideration this value to keep the backup data spread between different machines. CLI: --spi-cache-embedded--default--machine-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__MACHINE_NAME
spi-cache-embedded--default--machine-name
The name of the physical machine where this instance runs.
It can be set if multiple Keycloak instances are running in the same physical machines. Infinispan takes into consideration this value to keep the backup data spread between different machines.
CLI: --spi-cache-embedded--default--machine-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__MACHINE_NAME
spi-cache-embedded--default--metrics-histograms-enabled Enable histograms for metrics for the embedded caches. CLI: --spi-cache-embedded--default--metrics-histograms-enabled Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__METRICS_HISTOGRAMS_ENABLED
spi-cache-embedded--default--metrics-histograms-enabled
Enable histograms for metrics for the embedded caches.
CLI: --spi-cache-embedded--default--metrics-histograms-enabled Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__METRICS_HISTOGRAMS_ENABLED
true , false (default)
true , false (default)
spi-cache-embedded--default--network-bind-address IP address used by clustering transport. By default, SITE_LOCAL is used. CLI: --spi-cache-embedded--default--network-bind-address Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_BIND_ADDRESS
spi-cache-embedded--default--network-bind-address
IP address used by clustering transport.
By default, SITE_LOCAL is used.
CLI: --spi-cache-embedded--default--network-bind-address Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_BIND_ADDRESS
spi-cache-embedded--default--network-bind-port The Port the clustering transport will bind to. By default, port 7800 is used. CLI: --spi-cache-embedded--default--network-bind-port Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_BIND_PORT
spi-cache-embedded--default--network-bind-port
The Port the clustering transport will bind to.
By default, port 7800 is used.
CLI: --spi-cache-embedded--default--network-bind-port Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_BIND_PORT
any Integer
any Integer
spi-cache-embedded--default--network-external-address IP address that other instances in the cluster should use to contact this node. Set only if it is different to cache-embedded-network-bind-address, for example when this instance is behind a firewall. CLI: --spi-cache-embedded--default--network-external-address Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_EXTERNAL_ADDRESS
spi-cache-embedded--default--network-external-address
IP address that other instances in the cluster should use to contact this node.
Set only if it is different to cache-embedded-network-bind-address, for example when this instance is behind a firewall.
CLI: --spi-cache-embedded--default--network-external-address Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_EXTERNAL_ADDRESS
spi-cache-embedded--default--network-external-port Port that other instances in the cluster should use to contact this node. Set only if it is different to cache-embedded-network-bind-port, for example when this instance is behind a firewall CLI: --spi-cache-embedded--default--network-external-port Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_EXTERNAL_PORT
spi-cache-embedded--default--network-external-port
Port that other instances in the cluster should use to contact this node.
Set only if it is different to cache-embedded-network-bind-port, for example when this instance is behind a firewall
CLI: --spi-cache-embedded--default--network-external-port Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NETWORK_EXTERNAL_PORT
any Integer
any Integer
spi-cache-embedded--default--node-name Sets the name of the current node. This is a friendly name to make logs, etc. make more sense. CLI: --spi-cache-embedded--default--node-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NODE_NAME
spi-cache-embedded--default--node-name
Sets the name of the current node.
This is a friendly name to make logs, etc. make more sense.
CLI: --spi-cache-embedded--default--node-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__NODE_NAME
spi-cache-embedded--default--offline-client-sessions-max-count The maximum number of entries that can be stored in-memory by the offlineClientSessions cache. CLI: --spi-cache-embedded--default--offline-client-sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__OFFLINE_CLIENT_SESSIONS_MAX_COUNT
spi-cache-embedded--default--offline-client-sessions-max-count
The maximum number of entries that can be stored in-memory by the offlineClientSessions cache.
CLI: --spi-cache-embedded--default--offline-client-sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__OFFLINE_CLIENT_SESSIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--offline-sessions-max-count The maximum number of entries that can be stored in-memory by the offlineSessions cache. CLI: --spi-cache-embedded--default--offline-sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__OFFLINE_SESSIONS_MAX_COUNT
spi-cache-embedded--default--offline-sessions-max-count
The maximum number of entries that can be stored in-memory by the offlineSessions cache.
CLI: --spi-cache-embedded--default--offline-sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__OFFLINE_SESSIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--rack-name The name of the rack where this instance runs. It can be set if multiple Keycloak instances are running in the same physical rack. Infinispan takes into consideration this value to keep the backup data spread between different racks. CLI: --spi-cache-embedded--default--rack-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__RACK_NAME
spi-cache-embedded--default--rack-name
The name of the rack where this instance runs.
It can be set if multiple Keycloak instances are running in the same physical rack. Infinispan takes into consideration this value to keep the backup data spread between different racks.
CLI: --spi-cache-embedded--default--rack-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__RACK_NAME
spi-cache-embedded--default--realm-revisions-max-count The maximum number of entries that can be stored in-memory by the realmRevisions cache. CLI: --spi-cache-embedded--default--realm-revisions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__REALM_REVISIONS_MAX_COUNT
spi-cache-embedded--default--realm-revisions-max-count
The maximum number of entries that can be stored in-memory by the realmRevisions cache.
CLI: --spi-cache-embedded--default--realm-revisions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__REALM_REVISIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--realms-max-count The maximum number of entries that can be stored in-memory by the realms cache. CLI: --spi-cache-embedded--default--realms-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__REALMS_MAX_COUNT
spi-cache-embedded--default--realms-max-count
The maximum number of entries that can be stored in-memory by the realms cache.
CLI: --spi-cache-embedded--default--realms-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__REALMS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--sessions-max-count The maximum number of entries that can be stored in-memory by the sessions cache. CLI: --spi-cache-embedded--default--sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__SESSIONS_MAX_COUNT
spi-cache-embedded--default--sessions-max-count
The maximum number of entries that can be stored in-memory by the sessions cache.
CLI: --spi-cache-embedded--default--sessions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__SESSIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--sessions-owners Sets the number of owners for the sessions distributed cache. It defines the number of copies of your data in the cluster. CLI: --spi-cache-embedded--default--sessions-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__SESSIONS_OWNERS
spi-cache-embedded--default--sessions-owners
Sets the number of owners for the sessions distributed cache.
It defines the number of copies of your data in the cluster.
CLI: --spi-cache-embedded--default--sessions-owners Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__SESSIONS_OWNERS
any Integer
any Integer
spi-cache-embedded--default--site-name The name of the site (availability zone) where this instance runs. It can be set if running Keycloak in different availability zones. Infinispan takes into consideration this value to keep the backup data spread between different sites. CLI: --spi-cache-embedded--default--site-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__SITE_NAME
spi-cache-embedded--default--site-name
The name of the site (availability zone) where this instance runs.
It can be set if running Keycloak in different availability zones. Infinispan takes into consideration this value to keep the backup data spread between different sites.
CLI: --spi-cache-embedded--default--site-name Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__SITE_NAME
spi-cache-embedded--default--user-revisions-max-count The maximum number of entries that can be stored in-memory by the userRevisions cache. CLI: --spi-cache-embedded--default--user-revisions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__USER_REVISIONS_MAX_COUNT
spi-cache-embedded--default--user-revisions-max-count
The maximum number of entries that can be stored in-memory by the userRevisions cache.
CLI: --spi-cache-embedded--default--user-revisions-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__USER_REVISIONS_MAX_COUNT
any Integer
any Integer
spi-cache-embedded--default--users-max-count The maximum number of entries that can be stored in-memory by the users cache. CLI: --spi-cache-embedded--default--users-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__USERS_MAX_COUNT
spi-cache-embedded--default--users-max-count
The maximum number of entries that can be stored in-memory by the users cache.
CLI: --spi-cache-embedded--default--users-max-count Env: KC_SPI_CACHE_EMBEDDED__DEFAULT__USERS_MAX_COUNT
any Integer
any Integer

## cache-remote

spi-cache-remote--default--auth-realm Specifies the Infinispan server realm to be used for authentication. CLI: --spi-cache-remote--default--auth-realm Env: KC_SPI_CACHE_REMOTE__DEFAULT__AUTH_REALM
spi-cache-remote--default--auth-realm
Specifies the Infinispan server realm to be used for authentication.
CLI: --spi-cache-remote--default--auth-realm Env: KC_SPI_CACHE_REMOTE__DEFAULT__AUTH_REALM
default (default) or any String
default (default) or any String
spi-cache-remote--default--backup-sites Configures a list of backup sites names to where the external Infinispan cluster backups the Keycloak data. CLI: --spi-cache-remote--default--backup-sites Env: KC_SPI_CACHE_REMOTE__DEFAULT__BACKUP_SITES
spi-cache-remote--default--backup-sites
Configures a list of backup sites names to where the external Infinispan cluster backups the Keycloak data.
CLI: --spi-cache-remote--default--backup-sites Env: KC_SPI_CACHE_REMOTE__DEFAULT__BACKUP_SITES
spi-cache-remote--default--client-intelligence Specifies the level of intelligence the Hot Rod client should have. CLI: --spi-cache-remote--default--client-intelligence Env: KC_SPI_CACHE_REMOTE__DEFAULT__CLIENT_INTELLIGENCE
spi-cache-remote--default--client-intelligence
Specifies the level of intelligence the Hot Rod client should have.
CLI: --spi-cache-remote--default--client-intelligence Env: KC_SPI_CACHE_REMOTE__DEFAULT__CLIENT_INTELLIGENCE
BASIC , TOPOLOGY_AWARE , HASH_DISTRIBUTION_AWARE (default)
BASIC , TOPOLOGY_AWARE , HASH_DISTRIBUTION_AWARE (default)
spi-cache-remote--default--connection-pool-exhausted-action Specifies what happens when asking for a connection from a server’s pool, and that pool is exhausted. CLI: --spi-cache-remote--default--connection-pool-exhausted-action Env: KC_SPI_CACHE_REMOTE__DEFAULT__CONNECTION_POOL_EXHAUSTED_ACTION
spi-cache-remote--default--connection-pool-exhausted-action
Specifies what happens when asking for a connection from a server’s pool, and that pool is exhausted.
CLI: --spi-cache-remote--default--connection-pool-exhausted-action Env: KC_SPI_CACHE_REMOTE__DEFAULT__CONNECTION_POOL_EXHAUSTED_ACTION
EXCEPTION , WAIT , CREATE_NEW (default)
EXCEPTION , WAIT , CREATE_NEW (default)
spi-cache-remote--default--connection-pool-max-active Sets the maximum number of connections per Infinispan server instance. CLI: --spi-cache-remote--default--connection-pool-max-active Env: KC_SPI_CACHE_REMOTE__DEFAULT__CONNECTION_POOL_MAX_ACTIVE
spi-cache-remote--default--connection-pool-max-active
Sets the maximum number of connections per Infinispan server instance.
CLI: --spi-cache-remote--default--connection-pool-max-active Env: KC_SPI_CACHE_REMOTE__DEFAULT__CONNECTION_POOL_MAX_ACTIVE
16 (default) or any Integer
16 (default) or any Integer
spi-cache-remote--default--hostname The hostname of the external Infinispan cluster. CLI: --spi-cache-remote--default--hostname Env: KC_SPI_CACHE_REMOTE__DEFAULT__HOSTNAME
spi-cache-remote--default--hostname
The hostname of the external Infinispan cluster.
CLI: --spi-cache-remote--default--hostname Env: KC_SPI_CACHE_REMOTE__DEFAULT__HOSTNAME
spi-cache-remote--default--password The password for the authentication to the external Infinispan cluster. It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-username is required as well. CLI: --spi-cache-remote--default--password Env: KC_SPI_CACHE_REMOTE__DEFAULT__PASSWORD
spi-cache-remote--default--password
The password for the authentication to the external Infinispan cluster.
It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-username is required as well.
CLI: --spi-cache-remote--default--password Env: KC_SPI_CACHE_REMOTE__DEFAULT__PASSWORD
spi-cache-remote--default--port The port of the external Infinispan cluster. CLI: --spi-cache-remote--default--port Env: KC_SPI_CACHE_REMOTE__DEFAULT__PORT
spi-cache-remote--default--port
The port of the external Infinispan cluster.
CLI: --spi-cache-remote--default--port Env: KC_SPI_CACHE_REMOTE__DEFAULT__PORT
11222 (default) or any Integer
11222 (default) or any Integer
spi-cache-remote--default--properties-file Path to the properties file with the Hot Rod client configuration. CLI: --spi-cache-remote--default--properties-file Env: KC_SPI_CACHE_REMOTE__DEFAULT__PROPERTIES_FILE
spi-cache-remote--default--properties-file
Path to the properties file with the Hot Rod client configuration.
CLI: --spi-cache-remote--default--properties-file Env: KC_SPI_CACHE_REMOTE__DEFAULT__PROPERTIES_FILE
spi-cache-remote--default--sasl-mechanism Selects the SASL mechanism to use for the connection to the Infinispan server. CLI: --spi-cache-remote--default--sasl-mechanism Env: KC_SPI_CACHE_REMOTE__DEFAULT__SASL_MECHANISM
spi-cache-remote--default--sasl-mechanism
Selects the SASL mechanism to use for the connection to the Infinispan server.
CLI: --spi-cache-remote--default--sasl-mechanism Env: KC_SPI_CACHE_REMOTE__DEFAULT__SASL_MECHANISM
SCRAM-SHA-512 (default) or any String
SCRAM-SHA-512 (default) or any String
spi-cache-remote--default--tls-enabled Enable TLS support to communicate with a secured remote Infinispan server. Recommended to be enabled in production. CLI: --spi-cache-remote--default--tls-enabled Env: KC_SPI_CACHE_REMOTE__DEFAULT__TLS_ENABLED
spi-cache-remote--default--tls-enabled
Enable TLS support to communicate with a secured remote Infinispan server.
Recommended to be enabled in production.
CLI: --spi-cache-remote--default--tls-enabled Env: KC_SPI_CACHE_REMOTE__DEFAULT__TLS_ENABLED
true (default), false
true (default), false
spi-cache-remote--default--tls-sni-hostname Specifies the TLS SNI hostname for the connection to the Infinispan server. CLI: --spi-cache-remote--default--tls-sni-hostname Env: KC_SPI_CACHE_REMOTE__DEFAULT__TLS_SNI_HOSTNAME
spi-cache-remote--default--tls-sni-hostname
Specifies the TLS SNI hostname for the connection to the Infinispan server.
CLI: --spi-cache-remote--default--tls-sni-hostname Env: KC_SPI_CACHE_REMOTE__DEFAULT__TLS_SNI_HOSTNAME
spi-cache-remote--default--username The username for the authentication to the external Infinispan cluster. It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-password is required as well. CLI: --spi-cache-remote--default--username Env: KC_SPI_CACHE_REMOTE__DEFAULT__USERNAME
spi-cache-remote--default--username
The username for the authentication to the external Infinispan cluster.
It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-password is required as well.
CLI: --spi-cache-remote--default--username Env: KC_SPI_CACHE_REMOTE__DEFAULT__USERNAME

## ciba-auth-channel

### ciba-http-auth-channel

spi-ciba-auth-channel--ciba-http-auth-channel--http-authentication-channel-uri The HTTP(S) URI of the authentication channel. CLI: --spi-ciba-auth-channel--ciba-http-auth-channel--http-authentication-channel-uri Env: KC_SPI_CIBA_AUTH_CHANNEL__CIBA_HTTP_AUTH_CHANNEL__HTTP_AUTHENTICATION_CHANNEL_URI
spi-ciba-auth-channel--ciba-http-auth-channel--http-authentication-channel-uri
The HTTP(S) URI of the authentication channel.
CLI: --spi-ciba-auth-channel--ciba-http-auth-channel--http-authentication-channel-uri Env: KC_SPI_CIBA_AUTH_CHANNEL__CIBA_HTTP_AUTH_CHANNEL__HTTP_AUTHENTICATION_CHANNEL_URI

## connections-http-client

spi-connections-http-client--default--client-key-password The key password. CLI: --spi-connections-http-client--default--client-key-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CLIENT_KEY_PASSWORD
spi-connections-http-client--default--client-key-password
The key password.
CLI: --spi-connections-http-client--default--client-key-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CLIENT_KEY_PASSWORD
-1 (default) or any string
-1 (default) or any string
spi-connections-http-client--default--client-keystore The file path of the key store from where the key material is going to be read from to set-up TLS connections. CLI: --spi-connections-http-client--default--client-keystore Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CLIENT_KEYSTORE
spi-connections-http-client--default--client-keystore
The file path of the key store from where the key material is going to be read from to set-up TLS connections.
CLI: --spi-connections-http-client--default--client-keystore Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CLIENT_KEYSTORE
spi-connections-http-client--default--client-keystore-password The key store password. CLI: --spi-connections-http-client--default--client-keystore-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CLIENT_KEYSTORE_PASSWORD
spi-connections-http-client--default--client-keystore-password
The key store password.
CLI: --spi-connections-http-client--default--client-keystore-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CLIENT_KEYSTORE_PASSWORD
spi-connections-http-client--default--connection-pool-size Assigns maximum total connection value. CLI: --spi-connections-http-client--default--connection-pool-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CONNECTION_POOL_SIZE
spi-connections-http-client--default--connection-pool-size
Assigns maximum total connection value.
CLI: --spi-connections-http-client--default--connection-pool-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CONNECTION_POOL_SIZE
spi-connections-http-client--default--connection-ttl-millis Sets maximum time, in milliseconds, to live for persistent connections. CLI: --spi-connections-http-client--default--connection-ttl-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CONNECTION_TTL_MILLIS
spi-connections-http-client--default--connection-ttl-millis
Sets maximum time, in milliseconds, to live for persistent connections.
CLI: --spi-connections-http-client--default--connection-ttl-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__CONNECTION_TTL_MILLIS
-1 (default) or any long
-1 (default) or any long
spi-connections-http-client--default--disable-cookies Disables state (cookie) management.
spi-connections-http-client--default--disable-cookies
Disables state (cookie) management.
true (default), false
true (default), false
spi-connections-http-client--default--disable-trust-manager Disable trust management and hostname verification. NOTE this is a security hole, so only set this option if you cannot or do not want to verify the identity of the host you are communicating with. CLI: --spi-connections-http-client--default--disable-trust-manager Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__DISABLE_TRUST_MANAGER
spi-connections-http-client--default--disable-trust-manager
Disable trust management and hostname verification.
NOTE this is a security hole, so only set this option if you cannot or do not want to verify the identity of the host you are communicating with.
CLI: --spi-connections-http-client--default--disable-trust-manager Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__DISABLE_TRUST_MANAGER
true , false (default)
true , false (default)
spi-connections-http-client--default--establish-connection-timeout-millis When trying to make an initial socket connection, what is the timeout? CLI: --spi-connections-http-client--default--establish-connection-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__ESTABLISH_CONNECTION_TIMEOUT_MILLIS
spi-connections-http-client--default--establish-connection-timeout-millis
When trying to make an initial socket connection, what is the timeout?
CLI: --spi-connections-http-client--default--establish-connection-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__ESTABLISH_CONNECTION_TIMEOUT_MILLIS
-1 (default) or any long
-1 (default) or any long
spi-connections-http-client--default--max-connection-idle-time-millis Sets the time, in milliseconds, for evicting idle connections from the pool. CLI: --spi-connections-http-client--default--max-connection-idle-time-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__MAX_CONNECTION_IDLE_TIME_MILLIS
spi-connections-http-client--default--max-connection-idle-time-millis
Sets the time, in milliseconds, for evicting idle connections from the pool.
CLI: --spi-connections-http-client--default--max-connection-idle-time-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__MAX_CONNECTION_IDLE_TIME_MILLIS
900000 (default) or any long
900000 (default) or any long
spi-connections-http-client--default--max-consumed-response-size Maximum size of a response consumed by the client (to prevent denial of service) CLI: --spi-connections-http-client--default--max-consumed-response-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__MAX_CONSUMED_RESPONSE_SIZE
spi-connections-http-client--default--max-consumed-response-size
Maximum size of a response consumed by the client (to prevent denial of service)
CLI: --spi-connections-http-client--default--max-consumed-response-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__MAX_CONSUMED_RESPONSE_SIZE
10000000 (default) or any long
10000000 (default) or any long
spi-connections-http-client--default--max-pooled-per-route Assigns maximum connection per route value. CLI: --spi-connections-http-client--default--max-pooled-per-route Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__MAX_POOLED_PER_ROUTE
spi-connections-http-client--default--max-pooled-per-route
Assigns maximum connection per route value.
CLI: --spi-connections-http-client--default--max-pooled-per-route Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__MAX_POOLED_PER_ROUTE
64 (default) or any int
64 (default) or any int
spi-connections-http-client--default--proxy-mappings Denotes the combination of a regex based hostname pattern and a proxy-uri in the form of hostnamePattern;proxyUri. CLI: --spi-connections-http-client--default--proxy-mappings Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__PROXY_MAPPINGS
spi-connections-http-client--default--proxy-mappings
Denotes the combination of a regex based hostname pattern and a proxy-uri in the form of hostnamePattern;proxyUri.
CLI: --spi-connections-http-client--default--proxy-mappings Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__PROXY_MAPPINGS
spi-connections-http-client--default--reuse-connections If connections should be reused. CLI: --spi-connections-http-client--default--reuse-connections Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__REUSE_CONNECTIONS
spi-connections-http-client--default--reuse-connections
If connections should be reused.
CLI: --spi-connections-http-client--default--reuse-connections Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__REUSE_CONNECTIONS
true (default), false
true (default), false
spi-connections-http-client--default--socket-timeout-millis Socket inactivity timeout. CLI: --spi-connections-http-client--default--socket-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__SOCKET_TIMEOUT_MILLIS
spi-connections-http-client--default--socket-timeout-millis
Socket inactivity timeout.
CLI: --spi-connections-http-client--default--socket-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__DEFAULT__SOCKET_TIMEOUT_MILLIS
5000 (default) or any long
5000 (default) or any long

### opentelemetry

spi-connections-http-client--opentelemetry--client-key-password The key password. CLI: --spi-connections-http-client--opentelemetry--client-key-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CLIENT_KEY_PASSWORD
spi-connections-http-client--opentelemetry--client-key-password
The key password.
CLI: --spi-connections-http-client--opentelemetry--client-key-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CLIENT_KEY_PASSWORD
-1 (default) or any string
-1 (default) or any string
spi-connections-http-client--opentelemetry--client-keystore The file path of the key store from where the key material is going to be read from to set-up TLS connections. CLI: --spi-connections-http-client--opentelemetry--client-keystore Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CLIENT_KEYSTORE
spi-connections-http-client--opentelemetry--client-keystore
The file path of the key store from where the key material is going to be read from to set-up TLS connections.
CLI: --spi-connections-http-client--opentelemetry--client-keystore Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CLIENT_KEYSTORE
spi-connections-http-client--opentelemetry--client-keystore-password The key store password. CLI: --spi-connections-http-client--opentelemetry--client-keystore-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CLIENT_KEYSTORE_PASSWORD
spi-connections-http-client--opentelemetry--client-keystore-password
The key store password.
CLI: --spi-connections-http-client--opentelemetry--client-keystore-password Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CLIENT_KEYSTORE_PASSWORD
spi-connections-http-client--opentelemetry--connection-pool-size Assigns maximum total connection value. CLI: --spi-connections-http-client--opentelemetry--connection-pool-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CONNECTION_POOL_SIZE
spi-connections-http-client--opentelemetry--connection-pool-size
Assigns maximum total connection value.
CLI: --spi-connections-http-client--opentelemetry--connection-pool-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CONNECTION_POOL_SIZE
spi-connections-http-client--opentelemetry--connection-ttl-millis Sets maximum time, in milliseconds, to live for persistent connections. CLI: --spi-connections-http-client--opentelemetry--connection-ttl-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CONNECTION_TTL_MILLIS
spi-connections-http-client--opentelemetry--connection-ttl-millis
Sets maximum time, in milliseconds, to live for persistent connections.
CLI: --spi-connections-http-client--opentelemetry--connection-ttl-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__CONNECTION_TTL_MILLIS
-1 (default) or any long
-1 (default) or any long
spi-connections-http-client--opentelemetry--disable-cookies Disables state (cookie) management.
spi-connections-http-client--opentelemetry--disable-cookies
Disables state (cookie) management.
true (default), false
true (default), false
spi-connections-http-client--opentelemetry--disable-trust-manager Disable trust management and hostname verification. NOTE this is a security hole, so only set this option if you cannot or do not want to verify the identity of the host you are communicating with. CLI: --spi-connections-http-client--opentelemetry--disable-trust-manager Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__DISABLE_TRUST_MANAGER
spi-connections-http-client--opentelemetry--disable-trust-manager
Disable trust management and hostname verification.
NOTE this is a security hole, so only set this option if you cannot or do not want to verify the identity of the host you are communicating with.
CLI: --spi-connections-http-client--opentelemetry--disable-trust-manager Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__DISABLE_TRUST_MANAGER
true , false (default)
true , false (default)
spi-connections-http-client--opentelemetry--establish-connection-timeout-millis When trying to make an initial socket connection, what is the timeout? CLI: --spi-connections-http-client--opentelemetry--establish-connection-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__ESTABLISH_CONNECTION_TIMEOUT_MILLIS
spi-connections-http-client--opentelemetry--establish-connection-timeout-millis
When trying to make an initial socket connection, what is the timeout?
CLI: --spi-connections-http-client--opentelemetry--establish-connection-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__ESTABLISH_CONNECTION_TIMEOUT_MILLIS
-1 (default) or any long
-1 (default) or any long
spi-connections-http-client--opentelemetry--max-connection-idle-time-millis Sets the time, in milliseconds, for evicting idle connections from the pool. CLI: --spi-connections-http-client--opentelemetry--max-connection-idle-time-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__MAX_CONNECTION_IDLE_TIME_MILLIS
spi-connections-http-client--opentelemetry--max-connection-idle-time-millis
Sets the time, in milliseconds, for evicting idle connections from the pool.
CLI: --spi-connections-http-client--opentelemetry--max-connection-idle-time-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__MAX_CONNECTION_IDLE_TIME_MILLIS
900000 (default) or any long
900000 (default) or any long
spi-connections-http-client--opentelemetry--max-consumed-response-size Maximum size of a response consumed by the client (to prevent denial of service) CLI: --spi-connections-http-client--opentelemetry--max-consumed-response-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__MAX_CONSUMED_RESPONSE_SIZE
spi-connections-http-client--opentelemetry--max-consumed-response-size
Maximum size of a response consumed by the client (to prevent denial of service)
CLI: --spi-connections-http-client--opentelemetry--max-consumed-response-size Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__MAX_CONSUMED_RESPONSE_SIZE
10000000 (default) or any long
10000000 (default) or any long
spi-connections-http-client--opentelemetry--max-pooled-per-route Assigns maximum connection per route value. CLI: --spi-connections-http-client--opentelemetry--max-pooled-per-route Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__MAX_POOLED_PER_ROUTE
spi-connections-http-client--opentelemetry--max-pooled-per-route
Assigns maximum connection per route value.
CLI: --spi-connections-http-client--opentelemetry--max-pooled-per-route Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__MAX_POOLED_PER_ROUTE
64 (default) or any int
64 (default) or any int
spi-connections-http-client--opentelemetry--proxy-mappings Denotes the combination of a regex based hostname pattern and a proxy-uri in the form of hostnamePattern;proxyUri. CLI: --spi-connections-http-client--opentelemetry--proxy-mappings Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__PROXY_MAPPINGS
spi-connections-http-client--opentelemetry--proxy-mappings
Denotes the combination of a regex based hostname pattern and a proxy-uri in the form of hostnamePattern;proxyUri.
CLI: --spi-connections-http-client--opentelemetry--proxy-mappings Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__PROXY_MAPPINGS
spi-connections-http-client--opentelemetry--reuse-connections If connections should be reused. CLI: --spi-connections-http-client--opentelemetry--reuse-connections Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__REUSE_CONNECTIONS
spi-connections-http-client--opentelemetry--reuse-connections
If connections should be reused.
CLI: --spi-connections-http-client--opentelemetry--reuse-connections Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__REUSE_CONNECTIONS
true (default), false
true (default), false
spi-connections-http-client--opentelemetry--socket-timeout-millis Socket inactivity timeout. CLI: --spi-connections-http-client--opentelemetry--socket-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__SOCKET_TIMEOUT_MILLIS
spi-connections-http-client--opentelemetry--socket-timeout-millis
Socket inactivity timeout.
CLI: --spi-connections-http-client--opentelemetry--socket-timeout-millis Env: KC_SPI_CONNECTIONS_HTTP_CLIENT__OPENTELEMETRY__SOCKET_TIMEOUT_MILLIS
5000 (default) or any long
5000 (default) or any long

## connections-jpa

spi-connections-jpa--quarkus--initialize-empty Initialize database if empty. If set to false the database has to be manually initialized. If you want to manually initialize the database set migrationStrategy to manual which will create a file with SQL commands to initialize the database. CLI: --spi-connections-jpa--quarkus--initialize-empty Env: KC_SPI_CONNECTIONS_JPA__QUARKUS__INITIALIZE_EMPTY
spi-connections-jpa--quarkus--initialize-empty
Initialize database if empty.
If set to false the database has to be manually initialized. If you want to manually initialize the database set migrationStrategy to manual which will create a file with SQL commands to initialize the database.
CLI: --spi-connections-jpa--quarkus--initialize-empty Env: KC_SPI_CONNECTIONS_JPA__QUARKUS__INITIALIZE_EMPTY
true (default), false
true (default), false
spi-connections-jpa--quarkus--migration-export Path for where to write manual database initialization/migration file. CLI: --spi-connections-jpa--quarkus--migration-export Env: KC_SPI_CONNECTIONS_JPA__QUARKUS__MIGRATION_EXPORT
spi-connections-jpa--quarkus--migration-export
Path for where to write manual database initialization/migration file.
CLI: --spi-connections-jpa--quarkus--migration-export Env: KC_SPI_CONNECTIONS_JPA__QUARKUS__MIGRATION_EXPORT
spi-connections-jpa--quarkus--migration-strategy Strategy to use to migrate database. Valid values are update, manual and validate. Update will automatically migrate the database schema. Manual will export the required changes to a file with SQL commands that you can manually execute on the database. Validate will simply check if the database is up-to-date. CLI: --spi-connections-jpa--quarkus--migration-strategy Env: KC_SPI_CONNECTIONS_JPA__QUARKUS__MIGRATION_STRATEGY
spi-connections-jpa--quarkus--migration-strategy
Strategy to use to migrate database.
Valid values are update, manual and validate. Update will automatically migrate the database schema. Manual will export the required changes to a file with SQL commands that you can manually execute on the database. Validate will simply check if the database is up-to-date.
CLI: --spi-connections-jpa--quarkus--migration-strategy Env: KC_SPI_CONNECTIONS_JPA__QUARKUS__MIGRATION_STRATEGY
update (default), manual , validate
update (default), manual , validate

### keycloak-password

spi-credential--keycloak-password--validations-counter-tags Comma-separated list of tags to be used when publishing password validation counter metric. CLI: --spi-credential--keycloak-password--validations-counter-tags Env: KC_SPI_CREDENTIAL__KEYCLOAK_PASSWORD__VALIDATIONS_COUNTER_TAGS
spi-credential--keycloak-password--validations-counter-tags
Comma-separated list of tags to be used when publishing password validation counter metric.
CLI: --spi-credential--keycloak-password--validations-counter-tags Env: KC_SPI_CREDENTIAL__KEYCLOAK_PASSWORD__VALIDATIONS_COUNTER_TAGS
realm , algorithm , hashing_strength , outcome
realm , algorithm , hashing_strength , outcome

## crl-storage

spi-crl-storage--infinispan--cache-time Interval in seconds that the CRL is cached. The next update time of the CRL is always a minimum if present.
Zero or a negative value means CRL is cached until the next update time specified in the CRL (or infinite if the
CRL does not contain the next update). CLI: --spi-crl-storage--infinispan--cache-time Env: KC_SPI_CRL_STORAGE__INFINISPAN__CACHE_TIME
spi-crl-storage--infinispan--cache-time
Interval in seconds that the CRL is cached.
The next update time of the CRL is always a minimum if present.
Zero or a negative value means CRL is cached until the next update time specified in the CRL (or infinite if the
CRL does not contain the next update).
CLI: --spi-crl-storage--infinispan--cache-time Env: KC_SPI_CRL_STORAGE__INFINISPAN__CACHE_TIME
-1 (default) or any int
-1 (default) or any int
spi-crl-storage--infinispan--min-time-between-requests Minimum interval in seconds between two requests to retrieve the CRL. The CRL is not updated
from the URL again until this minimum time has passed since the previous refresh. In theory
this option is never used if the CRL is refreshed correctly in the next update time.
The interval should be a positive number. Default 10 seconds. CLI: --spi-crl-storage--infinispan--min-time-between-requests Env: KC_SPI_CRL_STORAGE__INFINISPAN__MIN_TIME_BETWEEN_REQUESTS
spi-crl-storage--infinispan--min-time-between-requests
Minimum interval in seconds between two requests to retrieve the CRL.
The CRL is not updated
from the URL again until this minimum time has passed since the previous refresh. In theory
this option is never used if the CRL is refreshed correctly in the next update time.
The interval should be a positive number. Default 10 seconds.
CLI: --spi-crl-storage--infinispan--min-time-between-requests Env: KC_SPI_CRL_STORAGE__INFINISPAN__MIN_TIME_BETWEEN_REQUESTS
10 (default) or any int
10 (default) or any int
spi-datastore--legacy--allow-migrate-existing-database-to-snapshot By default, it is not allowed to run the snapshot/development server against the database, which was previously migrated to some officially released server version. As an attempt of doing this indicates that you are trying to run development server against production database, which can result in a loss or corruption of data, and also does not allow upgrading. If it is really intended, you can use this option, which will allow to use nightly/development server against production database when explicitly switch to true. This option is recommended just in the development environments and should be never used in the production! CLI: --spi-datastore--legacy--allow-migrate-existing-database-to-snapshot Env: KC_SPI_DATASTORE__LEGACY__ALLOW_MIGRATE_EXISTING_DATABASE_TO_SNAPSHOT
spi-datastore--legacy--allow-migrate-existing-database-to-snapshot
By default, it is not allowed to run the snapshot/development server against the database, which was previously migrated to some officially released server version.
As an attempt of doing this indicates that you are trying to run development server against production database, which can result in a loss or corruption of data, and also does not allow upgrading. If it is really intended, you can use this option, which will allow to use nightly/development server against production database when explicitly switch to true. This option is recommended just in the development environments and should be never used in the production!
CLI: --spi-datastore--legacy--allow-migrate-existing-database-to-snapshot Env: KC_SPI_DATASTORE__LEGACY__ALLOW_MIGRATE_EXISTING_DATABASE_TO_SNAPSHOT
true , false (default)
true , false (default)
spi-dblock--jpa--lock-wait-timeout The maximum time to wait when waiting to release a database lock. CLI: --spi-dblock--jpa--lock-wait-timeout Env: KC_SPI_DBLOCK__JPA__LOCK_WAIT_TIMEOUT
spi-dblock--jpa--lock-wait-timeout
The maximum time to wait when waiting to release a database lock.
CLI: --spi-dblock--jpa--lock-wait-timeout Env: KC_SPI_DBLOCK__JPA__LOCK_WAIT_TIMEOUT

## device-representation

### device-representation

spi-device-representation--device-representation--cache-size Sets the maximum number of parsed user-agent values in the local cache. CLI: --spi-device-representation--device-representation--cache-size Env: KC_SPI_DEVICE_REPRESENTATION__DEVICE_REPRESENTATION__CACHE_SIZE
spi-device-representation--device-representation--cache-size
Sets the maximum number of parsed user-agent values in the local cache.
CLI: --spi-device-representation--device-representation--cache-size Env: KC_SPI_DEVICE_REPRESENTATION__DEVICE_REPRESENTATION__CACHE_SIZE
2048 (default) or any Integer
2048 (default) or any Integer

## events-listener

spi-events-listener--email--exclude-events A comma-separated list of events that should not be sent via email to the user’s account. CLI: --spi-events-listener--email--exclude-events Env: KC_SPI_EVENTS_LISTENER__EMAIL__EXCLUDE_EVENTS
spi-events-listener--email--exclude-events
A comma-separated list of events that should not be sent via email to the user’s account.
CLI: --spi-events-listener--email--exclude-events Env: KC_SPI_EVENTS_LISTENER__EMAIL__EXCLUDE_EVENTS
authreqid_to_token , authreqid_to_token_error , client_delete , client_delete_error , client_info , client_info_error , client_initiated_account_linking , client_initiated_account_linking_error , client_login , client_login_error , client_register , client_register_error , client_update , client_update_error , code_to_token , code_to_token_error , custom_required_action , custom_required_action_error , delete_account , delete_account_error , execute_action_token , execute_action_token_error , execute_actions , execute_actions_error , federated_identity_link , federated_identity_link_error , federated_identity_override_link , federated_identity_override_link_error , grant_consent , grant_consent_error , identity_provider_first_login , identity_provider_first_login_error , identity_provider_link_account , identity_provider_link_account_error , identity_provider_login , identity_provider_login_error , identity_provider_post_login , identity_provider_post_login_error , identity_provider_response , identity_provider_response_error , identity_provider_retrieve_token , identity_provider_retrieve_token_error , impersonate , impersonate_error , introspect_token , introspect_token_error , invalid_signature , invalid_signature_error , invite_org , invite_org_error , login , login_error , logout , logout_error , oauth2_device_auth , oauth2_device_auth_error , oauth2_device_code_to_token , oauth2_device_code_to_token_error , oauth2_device_verify_user_code , oauth2_device_verify_user_code_error , oauth2_extension_grant , oauth2_extension_grant_error , permission_token , permission_token_error , pushed_authorization_request , pushed_authorization_request_error , refresh_token , refresh_token_error , register , register_error , register_node , register_node_error , remove_credential , remove_credential_error , remove_federated_identity , remove_federated_identity_error , remove_totp , remove_totp_error , reset_password , reset_password_error , restart_authentication , restart_authentication_error , revoke_grant , revoke_grant_error , send_identity_provider_link , send_identity_provider_link_error , send_reset_password , send_reset_password_error , send_verify_email , send_verify_email_error , token_exchange , token_exchange_error , unregister_node , unregister_node_error , update_consent , update_consent_error , update_credential , update_credential_error , update_email , update_email_error , update_password , update_password_error , update_profile , update_profile_error , update_totp , update_totp_error , user_disabled_by_permanent_lockout , user_disabled_by_permanent_lockout_error , user_disabled_by_temporary_lockout , user_disabled_by_temporary_lockout_error , user_info_request , user_info_request_error , validate_access_token , validate_access_token_error , verify_email , verify_email_error , verify_profile , verify_profile_error
authreqid_to_token , authreqid_to_token_error , client_delete , client_delete_error , client_info , client_info_error , client_initiated_account_linking , client_initiated_account_linking_error , client_login , client_login_error , client_register , client_register_error , client_update , client_update_error , code_to_token , code_to_token_error , custom_required_action , custom_required_action_error , delete_account , delete_account_error , execute_action_token , execute_action_token_error , execute_actions , execute_actions_error , federated_identity_link , federated_identity_link_error , federated_identity_override_link , federated_identity_override_link_error , grant_consent , grant_consent_error , identity_provider_first_login , identity_provider_first_login_error , identity_provider_link_account , identity_provider_link_account_error , identity_provider_login , identity_provider_login_error , identity_provider_post_login , identity_provider_post_login_error , identity_provider_response , identity_provider_response_error , identity_provider_retrieve_token , identity_provider_retrieve_token_error , impersonate , impersonate_error , introspect_token , introspect_token_error , invalid_signature , invalid_signature_error , invite_org , invite_org_error , login , login_error , logout , logout_error , oauth2_device_auth , oauth2_device_auth_error , oauth2_device_code_to_token , oauth2_device_code_to_token_error , oauth2_device_verify_user_code , oauth2_device_verify_user_code_error , oauth2_extension_grant , oauth2_extension_grant_error , permission_token , permission_token_error , pushed_authorization_request , pushed_authorization_request_error , refresh_token , refresh_token_error , register , register_error , register_node , register_node_error , remove_credential , remove_credential_error , remove_federated_identity , remove_federated_identity_error , remove_totp , remove_totp_error , reset_password , reset_password_error , restart_authentication , restart_authentication_error , revoke_grant , revoke_grant_error , send_identity_provider_link , send_identity_provider_link_error , send_reset_password , send_reset_password_error , send_verify_email , send_verify_email_error , token_exchange , token_exchange_error , unregister_node , unregister_node_error , update_consent , update_consent_error , update_credential , update_credential_error , update_email , update_email_error , update_password , update_password_error , update_profile , update_profile_error , update_totp , update_totp_error , user_disabled_by_permanent_lockout , user_disabled_by_permanent_lockout_error , user_disabled_by_temporary_lockout , user_disabled_by_temporary_lockout_error , user_info_request , user_info_request_error , validate_access_token , validate_access_token_error , verify_email , verify_email_error , verify_profile , verify_profile_error
spi-events-listener--email--include-events A comma-separated list of events that should be sent via email to the user’s account. CLI: --spi-events-listener--email--include-events Env: KC_SPI_EVENTS_LISTENER__EMAIL__INCLUDE_EVENTS
spi-events-listener--email--include-events
A comma-separated list of events that should be sent via email to the user’s account.
CLI: --spi-events-listener--email--include-events Env: KC_SPI_EVENTS_LISTENER__EMAIL__INCLUDE_EVENTS
authreqid_to_token , authreqid_to_token_error , client_delete , client_delete_error , client_info , client_info_error , client_initiated_account_linking , client_initiated_account_linking_error , client_login , client_login_error , client_register , client_register_error , client_update , client_update_error , code_to_token , code_to_token_error , custom_required_action , custom_required_action_error , delete_account , delete_account_error , execute_action_token , execute_action_token_error , execute_actions , execute_actions_error , federated_identity_link , federated_identity_link_error , federated_identity_override_link , federated_identity_override_link_error , grant_consent , grant_consent_error , identity_provider_first_login , identity_provider_first_login_error , identity_provider_link_account , identity_provider_link_account_error , identity_provider_login , identity_provider_login_error , identity_provider_post_login , identity_provider_post_login_error , identity_provider_response , identity_provider_response_error , identity_provider_retrieve_token , identity_provider_retrieve_token_error , impersonate , impersonate_error , introspect_token , introspect_token_error , invalid_signature , invalid_signature_error , invite_org , invite_org_error , login , login_error , logout , logout_error , oauth2_device_auth , oauth2_device_auth_error , oauth2_device_code_to_token , oauth2_device_code_to_token_error , oauth2_device_verify_user_code , oauth2_device_verify_user_code_error , oauth2_extension_grant , oauth2_extension_grant_error , permission_token , permission_token_error , pushed_authorization_request , pushed_authorization_request_error , refresh_token , refresh_token_error , register , register_error , register_node , register_node_error , remove_credential , remove_credential_error , remove_federated_identity , remove_federated_identity_error , remove_totp , remove_totp_error , reset_password , reset_password_error , restart_authentication , restart_authentication_error , revoke_grant , revoke_grant_error , send_identity_provider_link , send_identity_provider_link_error , send_reset_password , send_reset_password_error , send_verify_email , send_verify_email_error , token_exchange , token_exchange_error , unregister_node , unregister_node_error , update_consent , update_consent_error , update_credential , update_credential_error , update_email , update_email_error , update_password , update_password_error , update_profile , update_profile_error , update_totp , update_totp_error , user_disabled_by_permanent_lockout , user_disabled_by_permanent_lockout_error , user_disabled_by_temporary_lockout , user_disabled_by_temporary_lockout_error , user_info_request , user_info_request_error , validate_access_token , validate_access_token_error , verify_email , verify_email_error , verify_profile , verify_profile_error
authreqid_to_token , authreqid_to_token_error , client_delete , client_delete_error , client_info , client_info_error , client_initiated_account_linking , client_initiated_account_linking_error , client_login , client_login_error , client_register , client_register_error , client_update , client_update_error , code_to_token , code_to_token_error , custom_required_action , custom_required_action_error , delete_account , delete_account_error , execute_action_token , execute_action_token_error , execute_actions , execute_actions_error , federated_identity_link , federated_identity_link_error , federated_identity_override_link , federated_identity_override_link_error , grant_consent , grant_consent_error , identity_provider_first_login , identity_provider_first_login_error , identity_provider_link_account , identity_provider_link_account_error , identity_provider_login , identity_provider_login_error , identity_provider_post_login , identity_provider_post_login_error , identity_provider_response , identity_provider_response_error , identity_provider_retrieve_token , identity_provider_retrieve_token_error , impersonate , impersonate_error , introspect_token , introspect_token_error , invalid_signature , invalid_signature_error , invite_org , invite_org_error , login , login_error , logout , logout_error , oauth2_device_auth , oauth2_device_auth_error , oauth2_device_code_to_token , oauth2_device_code_to_token_error , oauth2_device_verify_user_code , oauth2_device_verify_user_code_error , oauth2_extension_grant , oauth2_extension_grant_error , permission_token , permission_token_error , pushed_authorization_request , pushed_authorization_request_error , refresh_token , refresh_token_error , register , register_error , register_node , register_node_error , remove_credential , remove_credential_error , remove_federated_identity , remove_federated_identity_error , remove_totp , remove_totp_error , reset_password , reset_password_error , restart_authentication , restart_authentication_error , revoke_grant , revoke_grant_error , send_identity_provider_link , send_identity_provider_link_error , send_reset_password , send_reset_password_error , send_verify_email , send_verify_email_error , token_exchange , token_exchange_error , unregister_node , unregister_node_error , update_consent , update_consent_error , update_credential , update_credential_error , update_email , update_email_error , update_password , update_password_error , update_profile , update_profile_error , update_totp , update_totp_error , user_disabled_by_permanent_lockout , user_disabled_by_permanent_lockout_error , user_disabled_by_temporary_lockout , user_disabled_by_temporary_lockout_error , user_info_request , user_info_request_error , validate_access_token , validate_access_token_error , verify_email , verify_email_error , verify_profile , verify_profile_error

### jboss-logging

spi-events-listener--jboss-logging--error-level The log level for error messages. CLI: --spi-events-listener--jboss-logging--error-level Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__ERROR_LEVEL
spi-events-listener--jboss-logging--error-level
The log level for error messages.
CLI: --spi-events-listener--jboss-logging--error-level Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__ERROR_LEVEL
debug , error , fatal , info , trace , warn (default)
debug , error , fatal , info , trace , warn (default)
spi-events-listener--jboss-logging--include-representation When "true" the "representation" field with the JSON admin object is also added to the message. The realm should be also configured to include representation for the admin events. CLI: --spi-events-listener--jboss-logging--include-representation Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__INCLUDE_REPRESENTATION
spi-events-listener--jboss-logging--include-representation
When "true" the "representation" field with the JSON admin object is also added to the message.
The realm should be also configured to include representation for the admin events.
CLI: --spi-events-listener--jboss-logging--include-representation Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__INCLUDE_REPRESENTATION
true , false (default)
true , false (default)
spi-events-listener--jboss-logging--quotes The quotes to use for values, it should be one character like " or '. Use "none" if quotes are not needed. CLI: --spi-events-listener--jboss-logging--quotes Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__QUOTES
spi-events-listener--jboss-logging--quotes
The quotes to use for values, it should be one character like " or '.
Use "none" if quotes are not needed.
CLI: --spi-events-listener--jboss-logging--quotes Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__QUOTES
" (default) or any string
" (default) or any string
spi-events-listener--jboss-logging--sanitize If true the log messages are sanitized to avoid line breaks. If false messages are not sanitized. CLI: --spi-events-listener--jboss-logging--sanitize Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SANITIZE
spi-events-listener--jboss-logging--sanitize
If true the log messages are sanitized to avoid line breaks.
If false messages are not sanitized.
CLI: --spi-events-listener--jboss-logging--sanitize Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SANITIZE
true (default), false
true (default), false
spi-events-listener--jboss-logging--success-level The log level for success messages. CLI: --spi-events-listener--jboss-logging--success-level Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SUCCESS_LEVEL
spi-events-listener--jboss-logging--success-level
The log level for success messages.
CLI: --spi-events-listener--jboss-logging--success-level Env: KC_SPI_EVENTS_LISTENER__JBOSS_LOGGING__SUCCESS_LEVEL
debug (default), error , fatal , info , trace , warn
debug (default), error , fatal , info , trace , warn
spi-export--dir--dir Directory to export to CLI: --spi-export--dir--dir Env: KC_SPI_EXPORT__DIR__DIR
spi-export--dir--dir
Directory to export to
CLI: --spi-export--dir--dir Env: KC_SPI_EXPORT__DIR__DIR
spi-export--dir--realm-name Realm to export CLI: --spi-export--dir--realm-name Env: KC_SPI_EXPORT__DIR__REALM_NAME
spi-export--dir--realm-name
Realm to export
CLI: --spi-export--dir--realm-name Env: KC_SPI_EXPORT__DIR__REALM_NAME
spi-export--dir--users-export-strategy Users export strategy CLI: --spi-export--dir--users-export-strategy Env: KC_SPI_EXPORT__DIR__USERS_EXPORT_STRATEGY
spi-export--dir--users-export-strategy
Users export strategy
CLI: --spi-export--dir--users-export-strategy Env: KC_SPI_EXPORT__DIR__USERS_EXPORT_STRATEGY
DIFFERENT_FILES (default) or any string
DIFFERENT_FILES (default) or any string
spi-export--dir--users-per-file Users per exported file CLI: --spi-export--dir--users-per-file Env: KC_SPI_EXPORT__DIR__USERS_PER_FILE
spi-export--dir--users-per-file
Users per exported file
CLI: --spi-export--dir--users-per-file Env: KC_SPI_EXPORT__DIR__USERS_PER_FILE
50 (default) or any int
50 (default) or any int

### single-file

spi-export--single-file--file File to export to CLI: --spi-export--single-file--file Env: KC_SPI_EXPORT__SINGLE_FILE__FILE
spi-export--single-file--file
File to export to
CLI: --spi-export--single-file--file Env: KC_SPI_EXPORT__SINGLE_FILE__FILE
spi-export--single-file--realm-name Realm to export CLI: --spi-export--single-file--realm-name Env: KC_SPI_EXPORT__SINGLE_FILE__REALM_NAME
spi-export--single-file--realm-name
Realm to export
CLI: --spi-export--single-file--realm-name Env: KC_SPI_EXPORT__SINGLE_FILE__REALM_NAME
spi-group--jpa--escape-slashes-in-group-path If true slashes / in group names are escaped with the character ~ when converted to paths. CLI: --spi-group--jpa--escape-slashes-in-group-path Env: KC_SPI_GROUP__JPA__ESCAPE_SLASHES_IN_GROUP_PATH
spi-group--jpa--escape-slashes-in-group-path
If true slashes / in group names are escaped with the character ~ when converted to paths.
CLI: --spi-group--jpa--escape-slashes-in-group-path Env: KC_SPI_GROUP__JPA__ESCAPE_SLASHES_IN_GROUP_PATH
true , false (default)
true , false (default)
spi-group--jpa--searchable-attributes The list of attributes separated by comma that are allowed in client attribute searches. CLI: --spi-group--jpa--searchable-attributes Env: KC_SPI_GROUP__JPA__SEARCHABLE_ATTRIBUTES
spi-group--jpa--searchable-attributes
The list of attributes separated by comma that are allowed in client attribute searches.
CLI: --spi-group--jpa--searchable-attributes Env: KC_SPI_GROUP__JPA__SEARCHABLE_ATTRIBUTES
spi-import--dir--dir Directory to import from CLI: --spi-import--dir--dir Env: KC_SPI_IMPORT__DIR__DIR
spi-import--dir--dir
Directory to import from
CLI: --spi-import--dir--dir Env: KC_SPI_IMPORT__DIR__DIR
spi-import--dir--realm-name Realm to export CLI: --spi-import--dir--realm-name Env: KC_SPI_IMPORT__DIR__REALM_NAME
spi-import--dir--realm-name
Realm to export
CLI: --spi-import--dir--realm-name Env: KC_SPI_IMPORT__DIR__REALM_NAME
spi-import--dir--strategy Strategy for import: IGNORE_EXISTING, OVERWRITE_EXISTING CLI: --spi-import--dir--strategy Env: KC_SPI_IMPORT__DIR__STRATEGY
spi-import--dir--strategy
Strategy for import: IGNORE_EXISTING, OVERWRITE_EXISTING
CLI: --spi-import--dir--strategy Env: KC_SPI_IMPORT__DIR__STRATEGY

### single-file

spi-import--single-file--file File to import from CLI: --spi-import--single-file--file Env: KC_SPI_IMPORT__SINGLE_FILE__FILE
spi-import--single-file--file
File to import from
CLI: --spi-import--single-file--file Env: KC_SPI_IMPORT__SINGLE_FILE__FILE
spi-import--single-file--realm-name Realm to export CLI: --spi-import--single-file--realm-name Env: KC_SPI_IMPORT__SINGLE_FILE__REALM_NAME
spi-import--single-file--realm-name
Realm to export
CLI: --spi-import--single-file--realm-name Env: KC_SPI_IMPORT__SINGLE_FILE__REALM_NAME
spi-import--single-file--strategy Strategy for import: IGNORE_EXISTING, OVERWRITE_EXISTING CLI: --spi-import--single-file--strategy Env: KC_SPI_IMPORT__SINGLE_FILE__STRATEGY
spi-import--single-file--strategy
Strategy for import: IGNORE_EXISTING, OVERWRITE_EXISTING
CLI: --spi-import--single-file--strategy Env: KC_SPI_IMPORT__SINGLE_FILE__STRATEGY

## jgroups-mtls

spi-jgroups-mtls--default--enabled Encrypts the network communication between Keycloak servers. If no additional parameters about a keystore and truststore are provided, ephemeral key pairs and certificates are created and rotated automatically, which is recommended for standard setups. CLI: --spi-jgroups-mtls--default--enabled Env: KC_SPI_JGROUPS_MTLS__DEFAULT__ENABLED
spi-jgroups-mtls--default--enabled
Encrypts the network communication between Keycloak servers.
If no additional parameters about a keystore and truststore are provided, ephemeral key pairs and certificates are created and rotated automatically, which is recommended for standard setups.
CLI: --spi-jgroups-mtls--default--enabled Env: KC_SPI_JGROUPS_MTLS__DEFAULT__ENABLED
true (default), false
true (default), false
spi-jgroups-mtls--default--keystore-file The Keystore file path. The Keystore must contain the certificate to use by the TLS protocol. By default, it looks up cache-mtls-keystore.p12 under conf/ directory. CLI: --spi-jgroups-mtls--default--keystore-file Env: KC_SPI_JGROUPS_MTLS__DEFAULT__KEYSTORE_FILE
spi-jgroups-mtls--default--keystore-file
The Keystore file path.
The Keystore must contain the certificate to use by the TLS protocol. By default, it looks up cache-mtls-keystore.p12 under conf/ directory.
CLI: --spi-jgroups-mtls--default--keystore-file Env: KC_SPI_JGROUPS_MTLS__DEFAULT__KEYSTORE_FILE
spi-jgroups-mtls--default--keystore-password The password to access the Keystore. CLI: --spi-jgroups-mtls--default--keystore-password Env: KC_SPI_JGROUPS_MTLS__DEFAULT__KEYSTORE_PASSWORD
spi-jgroups-mtls--default--keystore-password
The password to access the Keystore.
CLI: --spi-jgroups-mtls--default--keystore-password Env: KC_SPI_JGROUPS_MTLS__DEFAULT__KEYSTORE_PASSWORD
any Password
any Password
spi-jgroups-mtls--default--rotation Rotation period in days of automatic JGroups MTLS certificates. CLI: --spi-jgroups-mtls--default--rotation Env: KC_SPI_JGROUPS_MTLS__DEFAULT__ROTATION
spi-jgroups-mtls--default--rotation
Rotation period in days of automatic JGroups MTLS certificates.
CLI: --spi-jgroups-mtls--default--rotation Env: KC_SPI_JGROUPS_MTLS__DEFAULT__ROTATION
30 (default) or any Integer
30 (default) or any Integer
spi-jgroups-mtls--default--truststore-file The Truststore file path. It should contain the trusted certificates or the Certificate Authority that signed the certificates. By default, it lookup cache-mtls-truststore.p12 under conf/ directory. CLI: --spi-jgroups-mtls--default--truststore-file Env: KC_SPI_JGROUPS_MTLS__DEFAULT__TRUSTSTORE_FILE
spi-jgroups-mtls--default--truststore-file
The Truststore file path.
It should contain the trusted certificates or the Certificate Authority that signed the certificates. By default, it lookup cache-mtls-truststore.p12 under conf/ directory.
CLI: --spi-jgroups-mtls--default--truststore-file Env: KC_SPI_JGROUPS_MTLS__DEFAULT__TRUSTSTORE_FILE
spi-jgroups-mtls--default--truststore-password The password to access the Truststore. CLI: --spi-jgroups-mtls--default--truststore-password Env: KC_SPI_JGROUPS_MTLS__DEFAULT__TRUSTSTORE_PASSWORD
spi-jgroups-mtls--default--truststore-password
The password to access the Truststore.
CLI: --spi-jgroups-mtls--default--truststore-password Env: KC_SPI_JGROUPS_MTLS__DEFAULT__TRUSTSTORE_PASSWORD
any Password
any Password

## load-balancer-check

spi-load-balancer-check--remote--poll-interval The Remote caches poll interval, in milliseconds, for connection availability CLI: --spi-load-balancer-check--remote--poll-interval Env: KC_SPI_LOAD_BALANCER_CHECK__REMOTE__POLL_INTERVAL
spi-load-balancer-check--remote--poll-interval
The Remote caches poll interval, in milliseconds, for connection availability
CLI: --spi-load-balancer-check--remote--poll-interval Env: KC_SPI_LOAD_BALANCER_CHECK__REMOTE__POLL_INTERVAL
5000 (default) or any int
5000 (default) or any int

## login-protocol

### openid-connect

spi-login-protocol--openid-connect--add-req-params-fail-fast Whether the fail-fast strategy should be enforced in case if the limit for some standard OIDC parameter or additional OIDC parameter is not met for the parameters sent to the OIDC authentication request. If false, then all additional request parameters to not meet the configuration are silently ignored. If true, an exception will be raised and OIDC authentication request will not be allowed. CLI: --spi-login-protocol--openid-connect--add-req-params-fail-fast Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_FAIL_FAST
spi-login-protocol--openid-connect--add-req-params-fail-fast
Whether the fail-fast strategy should be enforced in case if the limit for some standard OIDC parameter or additional OIDC parameter is not met for the parameters sent to the OIDC authentication request.
If false, then all additional request parameters to not meet the configuration are silently ignored. If true, an exception will be raised and OIDC authentication request will not be allowed.
CLI: --spi-login-protocol--openid-connect--add-req-params-fail-fast Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_FAIL_FAST
true , false (default)
true , false (default)
spi-login-protocol--openid-connect--add-req-params-max-number Maximum number of additional request parameters sent to the OIDC authentication request. As 'additional request parameter' is meant some custom parameter not directly treated as standard OIDC/OAuth2 protocol parameter. Additional parameters might be useful for example to add custom claims to the OIDC token (in case that also particular protocol mappers are configured). CLI: --spi-login-protocol--openid-connect--add-req-params-max-number Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_MAX_NUMBER
spi-login-protocol--openid-connect--add-req-params-max-number
Maximum number of additional request parameters sent to the OIDC authentication request.
As 'additional request parameter' is meant some custom parameter not directly treated as standard OIDC/OAuth2 protocol parameter. Additional parameters might be useful for example to add custom claims to the OIDC token (in case that also particular protocol mappers are configured).
CLI: --spi-login-protocol--openid-connect--add-req-params-max-number Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_MAX_NUMBER
5 (default) or any int
5 (default) or any int
spi-login-protocol--openid-connect--add-req-params-max-overall-size Maximum size of all additional request parameters values together. See add-req-params-max-number for more details about additional request parameters CLI: --spi-login-protocol--openid-connect--add-req-params-max-overall-size Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_MAX_OVERALL_SIZE
spi-login-protocol--openid-connect--add-req-params-max-overall-size
Maximum size of all additional request parameters values together.
See add-req-params-max-number for more details about additional request parameters
CLI: --spi-login-protocol--openid-connect--add-req-params-max-overall-size Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_MAX_OVERALL_SIZE
2147483647 (default) or any int
2147483647 (default) or any int
spi-login-protocol--openid-connect--add-req-params-max-size Maximum size of single additional request parameter value See add-req-params-max-number for more details about additional request parameters CLI: --spi-login-protocol--openid-connect--add-req-params-max-size Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_MAX_SIZE
spi-login-protocol--openid-connect--add-req-params-max-size
Maximum size of single additional request parameter value See add-req-params-max-number for more details about additional request parameters
CLI: --spi-login-protocol--openid-connect--add-req-params-max-size Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__ADD_REQ_PARAMS_MAX_SIZE
2000 (default) or any int
2000 (default) or any int
spi-login-protocol--openid-connect--req-params-default-max-size Maximum default length of the standard OIDC parameter sent to the OIDC authentication request. This applies to most of the standard parameters like for example state , nonce etc. The exception is login_hint parameter, which has maximum length of 255 characters. CLI: --spi-login-protocol--openid-connect--req-params-default-max-size Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__REQ_PARAMS_DEFAULT_MAX_SIZE
spi-login-protocol--openid-connect--req-params-default-max-size
Maximum default length of the standard OIDC parameter sent to the OIDC authentication request.
This applies to most of the standard parameters like for example state , nonce etc. The exception is login_hint parameter, which has maximum length of 255 characters.
CLI: --spi-login-protocol--openid-connect--req-params-default-max-size Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__REQ_PARAMS_DEFAULT_MAX_SIZE
4000 (default) or any int
4000 (default) or any int
spi-login-protocol--openid-connect--req-params-max-size--login_hint Maximum length of the standard OIDC authentication request parameter overriden for the specified parameter. Useful if some standard OIDC parameter should have different limit than req-params-default-max-size . It is needed to add the name of the parameter after this prefix into the configuration. In this example, the login_hint parameter is used, but this format is supported for any known standard OIDC/OAuth2 parameter. CLI: --spi-login-protocol--openid-connect--req-params-max-size--login_hint Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__REQ_PARAMS_MAX_SIZE__LOGIN_HINT
spi-login-protocol--openid-connect--req-params-max-size--login_hint
Maximum length of the standard OIDC authentication request parameter overriden for the specified parameter.
Useful if some standard OIDC parameter should have different limit than req-params-default-max-size . It is needed to add the name of the parameter after this prefix into the configuration. In this example, the login_hint parameter is used, but this format is supported for any known standard OIDC/OAuth2 parameter.
CLI: --spi-login-protocol--openid-connect--req-params-max-size--login_hint Env: KC_SPI_LOGIN_PROTOCOL__OPENID_CONNECT__REQ_PARAMS_MAX_SIZE__LOGIN_HINT

## login-failure

spi-login-failure--remote--max-retries The maximum number of retries if an error occurs. A value of zero or less disable any retries. CLI: --spi-login-failure--remote--max-retries Env: KC_SPI_LOGIN_FAILURE__REMOTE__MAX_RETRIES
spi-login-failure--remote--max-retries
The maximum number of retries if an error occurs.
A value of zero or less disable any retries.
CLI: --spi-login-failure--remote--max-retries Env: KC_SPI_LOGIN_FAILURE__REMOTE__MAX_RETRIES
10 (default) or any int
10 (default) or any int
spi-login-failure--remote--retry-base-time The base back-off time in milliseconds. CLI: --spi-login-failure--remote--retry-base-time Env: KC_SPI_LOGIN_FAILURE__REMOTE__RETRY_BASE_TIME
spi-login-failure--remote--retry-base-time
The base back-off time in milliseconds.
CLI: --spi-login-failure--remote--retry-base-time Env: KC_SPI_LOGIN_FAILURE__REMOTE__RETRY_BASE_TIME
10 (default) or any int
10 (default) or any int

## mapped-diagnostic-context

spi-mapped-diagnostic-context--default--mdc-keys Comma-separated list of MDC keys to add to the Mapped Diagnostic Context. CLI: --spi-mapped-diagnostic-context--default--mdc-keys Env: KC_SPI_MAPPED_DIAGNOSTIC_CONTEXT__DEFAULT__MDC_KEYS
spi-mapped-diagnostic-context--default--mdc-keys
Comma-separated list of MDC keys to add to the Mapped Diagnostic Context.
CLI: --spi-mapped-diagnostic-context--default--mdc-keys Env: KC_SPI_MAPPED_DIAGNOSTIC_CONTEXT__DEFAULT__MDC_KEYS
realmName , clientId , userId , ipAddress , org , sessionId , authenticationSessionId , authenticationTabId
realmName , clientId , userId , ipAddress , org , sessionId , authenticationSessionId , authenticationTabId

## password-hashing

spi-password-hashing--argon2--cpu-cores Maximum parallel CPU cores to use for hashing CLI: --spi-password-hashing--argon2--cpu-cores Env: KC_SPI_PASSWORD_HASHING__ARGON2__CPU_CORES
spi-password-hashing--argon2--cpu-cores
Maximum parallel CPU cores to use for hashing
CLI: --spi-password-hashing--argon2--cpu-cores Env: KC_SPI_PASSWORD_HASHING__ARGON2__CPU_CORES
spi-password-hashing--argon2--hash-length Hash length CLI: --spi-password-hashing--argon2--hash-length Env: KC_SPI_PASSWORD_HASHING__ARGON2__HASH_LENGTH
spi-password-hashing--argon2--hash-length
Hash length
CLI: --spi-password-hashing--argon2--hash-length Env: KC_SPI_PASSWORD_HASHING__ARGON2__HASH_LENGTH
32 (default) or any int
32 (default) or any int
spi-password-hashing--argon2--iterations Iterations CLI: --spi-password-hashing--argon2--iterations Env: KC_SPI_PASSWORD_HASHING__ARGON2__ITERATIONS
spi-password-hashing--argon2--iterations
CLI: --spi-password-hashing--argon2--iterations Env: KC_SPI_PASSWORD_HASHING__ARGON2__ITERATIONS
5 (default) or any int
5 (default) or any int
spi-password-hashing--argon2--memory Memory size (KB) CLI: --spi-password-hashing--argon2--memory Env: KC_SPI_PASSWORD_HASHING__ARGON2__MEMORY
spi-password-hashing--argon2--memory
Memory size (KB)
CLI: --spi-password-hashing--argon2--memory Env: KC_SPI_PASSWORD_HASHING__ARGON2__MEMORY
7168 (default) or any int
7168 (default) or any int
spi-password-hashing--argon2--parallelism Parallelism CLI: --spi-password-hashing--argon2--parallelism Env: KC_SPI_PASSWORD_HASHING__ARGON2__PARALLELISM
spi-password-hashing--argon2--parallelism
Parallelism
CLI: --spi-password-hashing--argon2--parallelism Env: KC_SPI_PASSWORD_HASHING__ARGON2__PARALLELISM
1 (default) or any int
1 (default) or any int
spi-password-hashing--argon2--type Type CLI: --spi-password-hashing--argon2--type Env: KC_SPI_PASSWORD_HASHING__ARGON2__TYPE
spi-password-hashing--argon2--type
CLI: --spi-password-hashing--argon2--type Env: KC_SPI_PASSWORD_HASHING__ARGON2__TYPE
id (default), d , i
id (default), d , i
spi-password-hashing--argon2--version Version CLI: --spi-password-hashing--argon2--version Env: KC_SPI_PASSWORD_HASHING__ARGON2__VERSION
spi-password-hashing--argon2--version
CLI: --spi-password-hashing--argon2--version Env: KC_SPI_PASSWORD_HASHING__ARGON2__VERSION
1.3 (default), 1.0
1.3 (default), 1.0

## public-key-storage

spi-public-key-storage--infinispan--max-cache-time Maximum interval in seconds that keys are cached when they are retrieved via all keys methods. When all keys for the entry are retrieved there is no way to detect if a key is missing (different to the case when the key is retrieved via ID for example). In that situation this option forces a refresh from time to time. This time can be overriden by the protocol (for example using cacheDuration or validUntil in the SAML descriptor). Default 24 hours. CLI: --spi-public-key-storage--infinispan--max-cache-time Env: KC_SPI_PUBLIC_KEY_STORAGE__INFINISPAN__MAX_CACHE_TIME
spi-public-key-storage--infinispan--max-cache-time
Maximum interval in seconds that keys are cached when they are retrieved via all keys methods.
When all keys for the entry are retrieved there is no way to detect if a key is missing (different to the case when the key is retrieved via ID for example). In that situation this option forces a refresh from time to time. This time can be overriden by the protocol (for example using cacheDuration or validUntil in the SAML descriptor). Default 24 hours.
CLI: --spi-public-key-storage--infinispan--max-cache-time Env: KC_SPI_PUBLIC_KEY_STORAGE__INFINISPAN__MAX_CACHE_TIME
86400 (default) or any int
86400 (default) or any int
spi-public-key-storage--infinispan--min-time-between-requests Minimum interval in seconds between two requests to retrieve the new public keys. The server will always try to download new public keys when a single key is requested and not found. However it will avoid the download if the previous refresh was done less than 10 seconds ago (by default). This behavior is used to avoid DoS attacks against the external keys endpoint. CLI: --spi-public-key-storage--infinispan--min-time-between-requests Env: KC_SPI_PUBLIC_KEY_STORAGE__INFINISPAN__MIN_TIME_BETWEEN_REQUESTS
spi-public-key-storage--infinispan--min-time-between-requests
Minimum interval in seconds between two requests to retrieve the new public keys.
The server will always try to download new public keys when a single key is requested and not found. However it will avoid the download if the previous refresh was done less than 10 seconds ago (by default). This behavior is used to avoid DoS attacks against the external keys endpoint.
CLI: --spi-public-key-storage--infinispan--min-time-between-requests Env: KC_SPI_PUBLIC_KEY_STORAGE__INFINISPAN__MIN_TIME_BETWEEN_REQUESTS
10 (default) or any int
10 (default) or any int

## required-action

### CONFIGURE_RECOVERY_AUTHN_CODES

spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--max_auth_age Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_RECOVERY_AUTHN_CODES__MAX_AUTH_AGE
spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--max_auth_age Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_RECOVERY_AUTHN_CODES__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String
spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--warning_threshold When user has smaller amount of remaining recovery codes on his account than the value configured here, account console will show warning to the user, which will recommend him to setup new set of recovery codes. CLI: --spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--warning_threshold Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_RECOVERY_AUTHN_CODES__WARNING_THRESHOLD
spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--warning_threshold
When user has smaller amount of remaining recovery codes on his account than the value configured here, account console will show warning to the user, which will recommend him to setup new set of recovery codes.
CLI: --spi-required-action--CONFIGURE_RECOVERY_AUTHN_CODES--warning_threshold Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_RECOVERY_AUTHN_CODES__WARNING_THRESHOLD
4 (default) or any Integer
4 (default) or any Integer

### CONFIGURE_TOTP

spi-required-action--CONFIGURE_TOTP--add-recovery-codes If this option is enabled, the user will be required to configure recovery codes following the OTP configuration. If the user already has recovery codes configured, Keycloak will not ask for setting them up.
As a prerequisite, enable the recovery codes required action and enable recovery codes in your authentication flow. CLI: --spi-required-action--CONFIGURE_TOTP--add-recovery-codes Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_TOTP__ADD_RECOVERY_CODES
spi-required-action--CONFIGURE_TOTP--add-recovery-codes
If this option is enabled, the user will be required to configure recovery codes following the OTP configuration.
If the user already has recovery codes configured, Keycloak will not ask for setting them up.
As a prerequisite, enable the recovery codes required action and enable recovery codes in your authentication flow.
CLI: --spi-required-action--CONFIGURE_TOTP--add-recovery-codes Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_TOTP__ADD_RECOVERY_CODES
true , false (default)
true , false (default)
spi-required-action--CONFIGURE_TOTP--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--CONFIGURE_TOTP--max_auth_age Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_TOTP__MAX_AUTH_AGE
spi-required-action--CONFIGURE_TOTP--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--CONFIGURE_TOTP--max_auth_age Env: KC_SPI_REQUIRED_ACTION__CONFIGURE_TOTP__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### TERMS_AND_CONDITIONS

spi-required-action--TERMS_AND_CONDITIONS--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--TERMS_AND_CONDITIONS--max_auth_age Env: KC_SPI_REQUIRED_ACTION__TERMS_AND_CONDITIONS__MAX_AUTH_AGE
spi-required-action--TERMS_AND_CONDITIONS--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--TERMS_AND_CONDITIONS--max_auth_age Env: KC_SPI_REQUIRED_ACTION__TERMS_AND_CONDITIONS__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### UPDATE_EMAIL

spi-required-action--UPDATE_EMAIL--email-resend-cooldown-seconds Minimum delay in seconds before another email verification email can be sent. CLI: --spi-required-action--UPDATE_EMAIL--email-resend-cooldown-seconds Env: KC_SPI_REQUIRED_ACTION__UPDATE_EMAIL__EMAIL_RESEND_COOLDOWN_SECONDS
spi-required-action--UPDATE_EMAIL--email-resend-cooldown-seconds
Minimum delay in seconds before another email verification email can be sent.
CLI: --spi-required-action--UPDATE_EMAIL--email-resend-cooldown-seconds Env: KC_SPI_REQUIRED_ACTION__UPDATE_EMAIL__EMAIL_RESEND_COOLDOWN_SECONDS
30 (default) or any String
30 (default) or any String
spi-required-action--UPDATE_EMAIL--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--UPDATE_EMAIL--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_EMAIL__MAX_AUTH_AGE
spi-required-action--UPDATE_EMAIL--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--UPDATE_EMAIL--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_EMAIL__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String
spi-required-action--UPDATE_EMAIL--verify-email If enabled, the user will be forced to verify the email regardless if email verification is enabled at the realm level or not. Otherwise, verification will be based on the realm level setting. CLI: --spi-required-action--UPDATE_EMAIL--verify-email Env: KC_SPI_REQUIRED_ACTION__UPDATE_EMAIL__VERIFY_EMAIL
spi-required-action--UPDATE_EMAIL--verify-email
If enabled, the user will be forced to verify the email regardless if email verification is enabled at the realm level or not.
Otherwise, verification will be based on the realm level setting.
CLI: --spi-required-action--UPDATE_EMAIL--verify-email Env: KC_SPI_REQUIRED_ACTION__UPDATE_EMAIL__VERIFY_EMAIL
true , false (default)
true , false (default)

### UPDATE_PASSWORD

spi-required-action--UPDATE_PASSWORD--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--UPDATE_PASSWORD--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_PASSWORD__MAX_AUTH_AGE
spi-required-action--UPDATE_PASSWORD--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--UPDATE_PASSWORD--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_PASSWORD__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### UPDATE_PROFILE

spi-required-action--UPDATE_PROFILE--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--UPDATE_PROFILE--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_PROFILE__MAX_AUTH_AGE
spi-required-action--UPDATE_PROFILE--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--UPDATE_PROFILE--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_PROFILE__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### VERIFY_EMAIL

spi-required-action--VERIFY_EMAIL--email-resend-cooldown-seconds Minimum delay in seconds before another email verification email can be sent. CLI: --spi-required-action--VERIFY_EMAIL--email-resend-cooldown-seconds Env: KC_SPI_REQUIRED_ACTION__VERIFY_EMAIL__EMAIL_RESEND_COOLDOWN_SECONDS
spi-required-action--VERIFY_EMAIL--email-resend-cooldown-seconds
Minimum delay in seconds before another email verification email can be sent.
CLI: --spi-required-action--VERIFY_EMAIL--email-resend-cooldown-seconds Env: KC_SPI_REQUIRED_ACTION__VERIFY_EMAIL__EMAIL_RESEND_COOLDOWN_SECONDS
30 (default) or any String
30 (default) or any String
spi-required-action--VERIFY_EMAIL--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--VERIFY_EMAIL--max_auth_age Env: KC_SPI_REQUIRED_ACTION__VERIFY_EMAIL__MAX_AUTH_AGE
spi-required-action--VERIFY_EMAIL--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--VERIFY_EMAIL--max_auth_age Env: KC_SPI_REQUIRED_ACTION__VERIFY_EMAIL__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### VERIFY_PROFILE

spi-required-action--VERIFY_PROFILE--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--VERIFY_PROFILE--max_auth_age Env: KC_SPI_REQUIRED_ACTION__VERIFY_PROFILE__MAX_AUTH_AGE
spi-required-action--VERIFY_PROFILE--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--VERIFY_PROFILE--max_auth_age Env: KC_SPI_REQUIRED_ACTION__VERIFY_PROFILE__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### delete_credential

spi-required-action--delete_credential--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--delete_credential--max_auth_age Env: KC_SPI_REQUIRED_ACTION__DELETE_CREDENTIAL__MAX_AUTH_AGE
spi-required-action--delete_credential--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--delete_credential--max_auth_age Env: KC_SPI_REQUIRED_ACTION__DELETE_CREDENTIAL__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String
spi-required-action--idp_link--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--idp_link--max_auth_age Env: KC_SPI_REQUIRED_ACTION__IDP_LINK__MAX_AUTH_AGE
spi-required-action--idp_link--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--idp_link--max_auth_age Env: KC_SPI_REQUIRED_ACTION__IDP_LINK__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### update_user_locale

spi-required-action--update_user_locale--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--update_user_locale--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_USER_LOCALE__MAX_AUTH_AGE
spi-required-action--update_user_locale--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--update_user_locale--max_auth_age Env: KC_SPI_REQUIRED_ACTION__UPDATE_USER_LOCALE__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### webauthn-register

spi-required-action--webauthn-register--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--webauthn-register--max_auth_age Env: KC_SPI_REQUIRED_ACTION__WEBAUTHN_REGISTER__MAX_AUTH_AGE
spi-required-action--webauthn-register--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--webauthn-register--max_auth_age Env: KC_SPI_REQUIRED_ACTION__WEBAUTHN_REGISTER__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

### webauthn-register-passwordless

spi-required-action--webauthn-register-passwordless--max_auth_age Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate. This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console. CLI: --spi-required-action--webauthn-register-passwordless--max_auth_age Env: KC_SPI_REQUIRED_ACTION__WEBAUTHN_REGISTER_PASSWORDLESS__MAX_AUTH_AGE
spi-required-action--webauthn-register-passwordless--max_auth_age
Configures the duration in seconds this action can be used after the last authentication before the user is required to re-authenticate.
This parameter is used just in the context of AIA when the kc_action parameter is available in the request, which is for instance when user himself updates his password in the account console.
CLI: --spi-required-action--webauthn-register-passwordless--max_auth_age Env: KC_SPI_REQUIRED_ACTION__WEBAUTHN_REGISTER_PASSWORDLESS__MAX_AUTH_AGE
300 (default) or any String
300 (default) or any String

## resource-encoding

spi-resource-encoding--gzip--excluded-content-types A space separated list of content-types to exclude from encoding. CLI: --spi-resource-encoding--gzip--excluded-content-types Env: KC_SPI_RESOURCE_ENCODING__GZIP__EXCLUDED_CONTENT_TYPES
spi-resource-encoding--gzip--excluded-content-types
A space separated list of content-types to exclude from encoding.
CLI: --spi-resource-encoding--gzip--excluded-content-types Env: KC_SPI_RESOURCE_ENCODING__GZIP__EXCLUDED_CONTENT_TYPES
image/png image/jpeg (default) or any string
image/png image/jpeg (default) or any string

## security-profile

spi-security-profile--default--name Name for the security configuration file to use. File name .json is searched in classapth and conf installation folder. CLI: --spi-security-profile--default--name Env: KC_SPI_SECURITY_PROFILE__DEFAULT__NAME
spi-security-profile--default--name
Name for the security configuration file to use.
File name .json is searched in classapth and conf installation folder.
CLI: --spi-security-profile--default--name Env: KC_SPI_SECURITY_PROFILE__DEFAULT__NAME

## single-use-object

spi-single-use-object--infinispan--persist-revoked-tokens If revoked tokens are stored persistently across restarts CLI: --spi-single-use-object--infinispan--persist-revoked-tokens Env: KC_SPI_SINGLE_USE_OBJECT__INFINISPAN__PERSIST_REVOKED_TOKENS
spi-single-use-object--infinispan--persist-revoked-tokens
If revoked tokens are stored persistently across restarts
CLI: --spi-single-use-object--infinispan--persist-revoked-tokens Env: KC_SPI_SINGLE_USE_OBJECT__INFINISPAN__PERSIST_REVOKED_TOKENS
true (default), false
true (default), false
spi-single-use-object--remote--persist-revoked-tokens If revoked tokens are stored persistently across restarts CLI: --spi-single-use-object--remote--persist-revoked-tokens Env: KC_SPI_SINGLE_USE_OBJECT__REMOTE__PERSIST_REVOKED_TOKENS
spi-single-use-object--remote--persist-revoked-tokens
If revoked tokens are stored persistently across restarts
CLI: --spi-single-use-object--remote--persist-revoked-tokens Env: KC_SPI_SINGLE_USE_OBJECT__REMOTE__PERSIST_REVOKED_TOKENS
true (default), false
true (default), false

## sticky-session-encoder

spi-sticky-session-encoder--infinispan--should-attach-route If the route should be attached to cookies to reflect the node that owns a particular session. CLI: --spi-sticky-session-encoder--infinispan--should-attach-route Env: KC_SPI_STICKY_SESSION_ENCODER__INFINISPAN__SHOULD_ATTACH_ROUTE
spi-sticky-session-encoder--infinispan--should-attach-route
If the route should be attached to cookies to reflect the node that owns a particular session.
CLI: --spi-sticky-session-encoder--infinispan--should-attach-route Env: KC_SPI_STICKY_SESSION_ENCODER__INFINISPAN__SHOULD_ATTACH_ROUTE
true (default), false
true (default), false
spi-sticky-session-encoder--remote--should-attach-route If the route should be attached to cookies to reflect the node that owns a particular session. CLI: --spi-sticky-session-encoder--remote--should-attach-route Env: KC_SPI_STICKY_SESSION_ENCODER__REMOTE__SHOULD_ATTACH_ROUTE
spi-sticky-session-encoder--remote--should-attach-route
If the route should be attached to cookies to reflect the node that owns a particular session.
CLI: --spi-sticky-session-encoder--remote--should-attach-route Env: KC_SPI_STICKY_SESSION_ENCODER__REMOTE__SHOULD_ATTACH_ROUTE
true (default), false
true (default), false
spi-storage--ldap--secure-referral Allow only secure LDAP referrals (deprecated) CLI: --spi-storage--ldap--secure-referral Env: KC_SPI_STORAGE__LDAP__SECURE_REFERRAL
spi-storage--ldap--secure-referral
Allow only secure LDAP referrals (deprecated)
CLI: --spi-storage--ldap--secure-referral Env: KC_SPI_STORAGE__LDAP__SECURE_REFERRAL
true (default), false
true (default), false
spi-truststore--file--file DEPRECATED: The file path of the trust store from where the certificates are going to be read from to validate TLS connections. CLI: --spi-truststore--file--file Env: KC_SPI_TRUSTSTORE__FILE__FILE
spi-truststore--file--file
DEPRECATED: The file path of the trust store from where the certificates are going to be read from to validate TLS connections.
CLI: --spi-truststore--file--file Env: KC_SPI_TRUSTSTORE__FILE__FILE
spi-truststore--file--hostname-verification-policy DEPRECATED: The hostname verification policy. CLI: --spi-truststore--file--hostname-verification-policy Env: KC_SPI_TRUSTSTORE__FILE__HOSTNAME_VERIFICATION_POLICY
spi-truststore--file--hostname-verification-policy
DEPRECATED: The hostname verification policy.
CLI: --spi-truststore--file--hostname-verification-policy Env: KC_SPI_TRUSTSTORE__FILE__HOSTNAME_VERIFICATION_POLICY
ANY , WILDCARD , STRICT , DEFAULT (default)
ANY , WILDCARD , STRICT , DEFAULT (default)
spi-truststore--file--password DEPRECATED: The trust store password. CLI: --spi-truststore--file--password Env: KC_SPI_TRUSTSTORE__FILE__PASSWORD
spi-truststore--file--password
DEPRECATED: The trust store password.
CLI: --spi-truststore--file--password Env: KC_SPI_TRUSTSTORE__FILE__PASSWORD
spi-truststore--file--type DEPRECATED: Type of the truststore. If not provided, the type would be detected based on the truststore file extension or platform default type. CLI: --spi-truststore--file--type Env: KC_SPI_TRUSTSTORE__FILE__TYPE
spi-truststore--file--type
DEPRECATED: Type of the truststore.
If not provided, the type would be detected based on the truststore file extension or platform default type.
CLI: --spi-truststore--file--type Env: KC_SPI_TRUSTSTORE__FILE__TYPE

## user-profile

### declarative-user-profile

spi-user-profile--declarative-user-profile--admin-read-only-attributes Array of regular expressions to identify fields that should be treated read-only so administrators can’t change them. CLI: --spi-user-profile--declarative-user-profile--admin-read-only-attributes Env: KC_SPI_USER_PROFILE__DECLARATIVE_USER_PROFILE__ADMIN_READ_ONLY_ATTRIBUTES
spi-user-profile--declarative-user-profile--admin-read-only-attributes
Array of regular expressions to identify fields that should be treated read-only so administrators can’t change them.
CLI: --spi-user-profile--declarative-user-profile--admin-read-only-attributes Env: KC_SPI_USER_PROFILE__DECLARATIVE_USER_PROFILE__ADMIN_READ_ONLY_ATTRIBUTES
any MultivaluedString
any MultivaluedString
spi-user-profile--declarative-user-profile--max-email-local-part-length To set user profile max email local part length CLI: --spi-user-profile--declarative-user-profile--max-email-local-part-length Env: KC_SPI_USER_PROFILE__DECLARATIVE_USER_PROFILE__MAX_EMAIL_LOCAL_PART_LENGTH
spi-user-profile--declarative-user-profile--max-email-local-part-length
To set user profile max email local part length
CLI: --spi-user-profile--declarative-user-profile--max-email-local-part-length Env: KC_SPI_USER_PROFILE__DECLARATIVE_USER_PROFILE__MAX_EMAIL_LOCAL_PART_LENGTH
spi-user-profile--declarative-user-profile--read-only-attributes Array of regular expressions to identify fields that should be treated read-only so users can’t change them. CLI: --spi-user-profile--declarative-user-profile--read-only-attributes Env: KC_SPI_USER_PROFILE__DECLARATIVE_USER_PROFILE__READ_ONLY_ATTRIBUTES
spi-user-profile--declarative-user-profile--read-only-attributes
Array of regular expressions to identify fields that should be treated read-only so users can’t change them.
CLI: --spi-user-profile--declarative-user-profile--read-only-attributes Env: KC_SPI_USER_PROFILE__DECLARATIVE_USER_PROFILE__READ_ONLY_ATTRIBUTES
any MultivaluedString
any MultivaluedString

## user-sessions

spi-user-sessions--infinispan--max-batch-size Maximum size of a batch (only applicable to persistent sessions CLI: --spi-user-sessions--infinispan--max-batch-size Env: KC_SPI_USER_SESSIONS__INFINISPAN__MAX_BATCH_SIZE
spi-user-sessions--infinispan--max-batch-size
Maximum size of a batch (only applicable to persistent sessions
CLI: --spi-user-sessions--infinispan--max-batch-size Env: KC_SPI_USER_SESSIONS__INFINISPAN__MAX_BATCH_SIZE
4 (default) or any int
4 (default) or any int
spi-user-sessions--infinispan--offline-client-session-cache-entry-lifespan-override Override how long offline client sessions should be kept in memory in seconds (deprecated, to be removed in Keycloak 27) CLI: --spi-user-sessions--infinispan--offline-client-session-cache-entry-lifespan-override Env: KC_SPI_USER_SESSIONS__INFINISPAN__OFFLINE_CLIENT_SESSION_CACHE_ENTRY_LIFESPAN_OVERRIDE
spi-user-sessions--infinispan--offline-client-session-cache-entry-lifespan-override
Override how long offline client sessions should be kept in memory in seconds (deprecated, to be removed in Keycloak 27)
CLI: --spi-user-sessions--infinispan--offline-client-session-cache-entry-lifespan-override Env: KC_SPI_USER_SESSIONS__INFINISPAN__OFFLINE_CLIENT_SESSION_CACHE_ENTRY_LIFESPAN_OVERRIDE
spi-user-sessions--infinispan--offline-session-cache-entry-lifespan-override Override how long offline user sessions should be kept in memory in seconds (deprecated, to be removed in Keycloak 27) CLI: --spi-user-sessions--infinispan--offline-session-cache-entry-lifespan-override Env: KC_SPI_USER_SESSIONS__INFINISPAN__OFFLINE_SESSION_CACHE_ENTRY_LIFESPAN_OVERRIDE
spi-user-sessions--infinispan--offline-session-cache-entry-lifespan-override
Override how long offline user sessions should be kept in memory in seconds (deprecated, to be removed in Keycloak 27)
CLI: --spi-user-sessions--infinispan--offline-session-cache-entry-lifespan-override Env: KC_SPI_USER_SESSIONS__INFINISPAN__OFFLINE_SESSION_CACHE_ENTRY_LIFESPAN_OVERRIDE
spi-user-sessions--infinispan--use-batches Enable or disable batch writes to the database. Enabled by default with the persistent-user-sessions Feature CLI: --spi-user-sessions--infinispan--use-batches Env: KC_SPI_USER_SESSIONS__INFINISPAN__USE_BATCHES
spi-user-sessions--infinispan--use-batches
Enable or disable batch writes to the database.
Enabled by default with the persistent-user-sessions Feature
CLI: --spi-user-sessions--infinispan--use-batches Env: KC_SPI_USER_SESSIONS__INFINISPAN__USE_BATCHES
true , false (default)
true , false (default)
spi-user-sessions--infinispan--use-caches Enable or disable caches. Enabled by default unless the external feature to use only external remote caches is used CLI: --spi-user-sessions--infinispan--use-caches Env: KC_SPI_USER_SESSIONS__INFINISPAN__USE_CACHES
spi-user-sessions--infinispan--use-caches
Enable or disable caches.
Enabled by default unless the external feature to use only external remote caches is used
CLI: --spi-user-sessions--infinispan--use-caches Env: KC_SPI_USER_SESSIONS__INFINISPAN__USE_CACHES
true , false
true , false
spi-user-sessions--remote--batch-size Batch size when streaming session from the remote cache CLI: --spi-user-sessions--remote--batch-size Env: KC_SPI_USER_SESSIONS__REMOTE__BATCH_SIZE
spi-user-sessions--remote--batch-size
Batch size when streaming session from the remote cache
CLI: --spi-user-sessions--remote--batch-size Env: KC_SPI_USER_SESSIONS__REMOTE__BATCH_SIZE
1024 (default) or any int
1024 (default) or any int
spi-user-sessions--remote--max-retries The maximum number of retries if an error occurs. A value of zero or less disable any retries. CLI: --spi-user-sessions--remote--max-retries Env: KC_SPI_USER_SESSIONS__REMOTE__MAX_RETRIES
spi-user-sessions--remote--max-retries
The maximum number of retries if an error occurs.
A value of zero or less disable any retries.
CLI: --spi-user-sessions--remote--max-retries Env: KC_SPI_USER_SESSIONS__REMOTE__MAX_RETRIES
10 (default) or any int
10 (default) or any int
spi-user-sessions--remote--retry-base-time The base back-off time in milliseconds. CLI: --spi-user-sessions--remote--retry-base-time Env: KC_SPI_USER_SESSIONS__REMOTE__RETRY_BASE_TIME
spi-user-sessions--remote--retry-base-time
The base back-off time in milliseconds.
CLI: --spi-user-sessions--remote--retry-base-time Env: KC_SPI_USER_SESSIONS__REMOTE__RETRY_BASE_TIME
10 (default) or any int
10 (default) or any int

### oauth-authorization-server

spi-well-known--oauth-authorization-server--include-client-scopes If client scopes should be used to calculate the list of supported scopes. CLI: --spi-well-known--oauth-authorization-server--include-client-scopes Env: KC_SPI_WELL_KNOWN__OAUTH_AUTHORIZATION_SERVER__INCLUDE_CLIENT_SCOPES
spi-well-known--oauth-authorization-server--include-client-scopes
If client scopes should be used to calculate the list of supported scopes.
CLI: --spi-well-known--oauth-authorization-server--include-client-scopes Env: KC_SPI_WELL_KNOWN__OAUTH_AUTHORIZATION_SERVER__INCLUDE_CLIENT_SCOPES
true (default), false
true (default), false
spi-well-known--oauth-authorization-server--openid-configuration-override The file path from where the metadata should be loaded from. You can use an absolute file path or, if the file is in the server classpath, use the classpath: prefix to load the file from the classpath. CLI: --spi-well-known--oauth-authorization-server--openid-configuration-override Env: KC_SPI_WELL_KNOWN__OAUTH_AUTHORIZATION_SERVER__OPENID_CONFIGURATION_OVERRIDE
spi-well-known--oauth-authorization-server--openid-configuration-override
The file path from where the metadata should be loaded from.
You can use an absolute file path or, if the file is in the server classpath, use the classpath: prefix to load the file from the classpath.
CLI: --spi-well-known--oauth-authorization-server--openid-configuration-override Env: KC_SPI_WELL_KNOWN__OAUTH_AUTHORIZATION_SERVER__OPENID_CONFIGURATION_OVERRIDE

### openid-configuration

spi-well-known--openid-configuration--include-client-scopes If client scopes should be used to calculate the list of supported scopes. CLI: --spi-well-known--openid-configuration--include-client-scopes Env: KC_SPI_WELL_KNOWN__OPENID_CONFIGURATION__INCLUDE_CLIENT_SCOPES
spi-well-known--openid-configuration--include-client-scopes
If client scopes should be used to calculate the list of supported scopes.
CLI: --spi-well-known--openid-configuration--include-client-scopes Env: KC_SPI_WELL_KNOWN__OPENID_CONFIGURATION__INCLUDE_CLIENT_SCOPES
true (default), false
true (default), false
spi-well-known--openid-configuration--openid-configuration-override The file path from where the metadata should be loaded from. You can use an absolute file path or, if the file is in the server classpath, use the classpath: prefix to load the file from the classpath. CLI: --spi-well-known--openid-configuration--openid-configuration-override Env: KC_SPI_WELL_KNOWN__OPENID_CONFIGURATION__OPENID_CONFIGURATION_OVERRIDE
spi-well-known--openid-configuration--openid-configuration-override
The file path from where the metadata should be loaded from.
You can use an absolute file path or, if the file is in the server classpath, use the classpath: prefix to load the file from the classpath.
CLI: --spi-well-known--openid-configuration--openid-configuration-override Env: KC_SPI_WELL_KNOWN__OPENID_CONFIGURATION__OPENID_CONFIGURATION_OVERRIDE

---
Quelle: https://www.keycloak.org/server/all-provider-config
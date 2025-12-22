# All configuration - Keycloak

# All configuration

cache Defines the cache mechanism for high-availability. By default in production mode, a ispn cache is used to create a cluster between multiple server nodes. By default in development mode, a local cache disables clustering and is intended for development and testing purposes. CLI: --cache Env: KC_CACHE
Defines the cache mechanism for high-availability.
By default in production mode, a ispn cache is used to create a cluster between multiple server nodes. By default in development mode, a local cache disables clustering and is intended for development and testing purposes.
CLI: --cache Env: KC_CACHE
ispn (default), local
ispn (default), local
cache-config-file Defines the file from which cache configuration should be loaded from. The configuration file is relative to the conf/ directory. CLI: --cache-config-file Env: KC_CACHE_CONFIG_FILE
cache-config-file
Defines the file from which cache configuration should be loaded from.
The configuration file is relative to the conf/ directory.
CLI: --cache-config-file Env: KC_CACHE_CONFIG_FILE
cache-config-mutate Determines whether changes to the default cache configurations are allowed. This is only recommended for advanced use-cases where the default cache configurations are proven to be problematic. The only supported way to change the default cache configurations is via the other cache-…​ options. CLI: --cache-config-mutate Env: KC_CACHE_CONFIG_MUTATE
cache-config-mutate
Determines whether changes to the default cache configurations are allowed.
This is only recommended for advanced use-cases where the default cache configurations are proven to be problematic. The only supported way to change the default cache configurations is via the other cache-…​ options.
CLI: --cache-config-mutate Env: KC_CACHE_CONFIG_MUTATE
true , false (default)
true , false (default)
cache-embedded-authorization-max-count The maximum number of entries that can be stored in-memory by the authorization cache. CLI: --cache-embedded-authorization-max-count Env: KC_CACHE_EMBEDDED_AUTHORIZATION_MAX_COUNT
cache-embedded-authorization-max-count
The maximum number of entries that can be stored in-memory by the authorization cache.
CLI: --cache-embedded-authorization-max-count Env: KC_CACHE_EMBEDDED_AUTHORIZATION_MAX_COUNT
cache-embedded-client-sessions-max-count The maximum number of entries that can be stored in-memory by the clientSessions cache. CLI: --cache-embedded-client-sessions-max-count Env: KC_CACHE_EMBEDDED_CLIENT_SESSIONS_MAX_COUNT Available only when embedded Infinispan clusters configured
cache-embedded-client-sessions-max-count
The maximum number of entries that can be stored in-memory by the clientSessions cache.
CLI: --cache-embedded-client-sessions-max-count Env: KC_CACHE_EMBEDDED_CLIENT_SESSIONS_MAX_COUNT
Available only when embedded Infinispan clusters configured
cache-embedded-crl-max-count The maximum number of entries that can be stored in-memory by the crl cache. CLI: --cache-embedded-crl-max-count Env: KC_CACHE_EMBEDDED_CRL_MAX_COUNT
cache-embedded-crl-max-count
The maximum number of entries that can be stored in-memory by the crl cache.
CLI: --cache-embedded-crl-max-count Env: KC_CACHE_EMBEDDED_CRL_MAX_COUNT
cache-embedded-keys-max-count The maximum number of entries that can be stored in-memory by the keys cache. CLI: --cache-embedded-keys-max-count Env: KC_CACHE_EMBEDDED_KEYS_MAX_COUNT
cache-embedded-keys-max-count
The maximum number of entries that can be stored in-memory by the keys cache.
CLI: --cache-embedded-keys-max-count Env: KC_CACHE_EMBEDDED_KEYS_MAX_COUNT
cache-embedded-mtls-enabled Encrypts the network communication between Keycloak servers. If no additional parameters about a keystore and truststore are provided, ephemeral key pairs and certificates are created and rotated automatically, which is recommended for standard setups. CLI: --cache-embedded-mtls-enabled Env: KC_CACHE_EMBEDDED_MTLS_ENABLED Available only when a TCP based cache-stack is used
cache-embedded-mtls-enabled
Encrypts the network communication between Keycloak servers.
If no additional parameters about a keystore and truststore are provided, ephemeral key pairs and certificates are created and rotated automatically, which is recommended for standard setups.
CLI: --cache-embedded-mtls-enabled Env: KC_CACHE_EMBEDDED_MTLS_ENABLED
Available only when a TCP based cache-stack is used
true (default), false
true (default), false
cache-embedded-mtls-key-store-file The Keystore file path. The Keystore must contain the certificate to use by the TLS protocol. By default, it looks up cache-mtls-keystore.p12 under conf/ directory. CLI: --cache-embedded-mtls-key-store-file Env: KC_CACHE_EMBEDDED_MTLS_KEY_STORE_FILE Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-key-store-file
The Keystore file path.
The Keystore must contain the certificate to use by the TLS protocol. By default, it looks up cache-mtls-keystore.p12 under conf/ directory.
CLI: --cache-embedded-mtls-key-store-file Env: KC_CACHE_EMBEDDED_MTLS_KEY_STORE_FILE
Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-key-store-password The password to access the Keystore. CLI: --cache-embedded-mtls-key-store-password Env: KC_CACHE_EMBEDDED_MTLS_KEY_STORE_PASSWORD Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-key-store-password
The password to access the Keystore.
CLI: --cache-embedded-mtls-key-store-password Env: KC_CACHE_EMBEDDED_MTLS_KEY_STORE_PASSWORD
Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-rotation-interval-days Rotation period in days of automatic JGroups MTLS certificates. CLI: --cache-embedded-mtls-rotation-interval-days Env: KC_CACHE_EMBEDDED_MTLS_ROTATION_INTERVAL_DAYS Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-rotation-interval-days
Rotation period in days of automatic JGroups MTLS certificates.
CLI: --cache-embedded-mtls-rotation-interval-days Env: KC_CACHE_EMBEDDED_MTLS_ROTATION_INTERVAL_DAYS
Available only when property 'cache-embedded-mtls-enabled' is enabled
30 (default)
30 (default)
cache-embedded-mtls-trust-store-file The Truststore file path. It should contain the trusted certificates or the Certificate Authority that signed the certificates. By default, it lookup cache-mtls-truststore.p12 under conf/ directory. CLI: --cache-embedded-mtls-trust-store-file Env: KC_CACHE_EMBEDDED_MTLS_TRUST_STORE_FILE Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-trust-store-file
The Truststore file path.
It should contain the trusted certificates or the Certificate Authority that signed the certificates. By default, it lookup cache-mtls-truststore.p12 under conf/ directory.
CLI: --cache-embedded-mtls-trust-store-file Env: KC_CACHE_EMBEDDED_MTLS_TRUST_STORE_FILE
Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-trust-store-password The password to access the Truststore. CLI: --cache-embedded-mtls-trust-store-password Env: KC_CACHE_EMBEDDED_MTLS_TRUST_STORE_PASSWORD Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-mtls-trust-store-password
The password to access the Truststore.
CLI: --cache-embedded-mtls-trust-store-password Env: KC_CACHE_EMBEDDED_MTLS_TRUST_STORE_PASSWORD
Available only when property 'cache-embedded-mtls-enabled' is enabled
cache-embedded-network-bind-address IP address used by clustering transport. By default, SITE_LOCAL is used. CLI: --cache-embedded-network-bind-address Env: KC_CACHE_EMBEDDED_NETWORK_BIND_ADDRESS Available only when Infinispan clustered embedded is enabled
cache-embedded-network-bind-address
IP address used by clustering transport.
By default, SITE_LOCAL is used.
CLI: --cache-embedded-network-bind-address Env: KC_CACHE_EMBEDDED_NETWORK_BIND_ADDRESS
Available only when Infinispan clustered embedded is enabled
cache-embedded-network-bind-port The Port the clustering transport will bind to. By default, port 7800 is used. CLI: --cache-embedded-network-bind-port Env: KC_CACHE_EMBEDDED_NETWORK_BIND_PORT Available only when Infinispan clustered embedded is enabled
cache-embedded-network-bind-port
The Port the clustering transport will bind to.
By default, port 7800 is used.
CLI: --cache-embedded-network-bind-port Env: KC_CACHE_EMBEDDED_NETWORK_BIND_PORT
Available only when Infinispan clustered embedded is enabled
cache-embedded-network-external-address IP address that other instances in the cluster should use to contact this node. Set only if it is different to cache-embedded-network-bind-address, for example when this instance is behind a firewall. CLI: --cache-embedded-network-external-address Env: KC_CACHE_EMBEDDED_NETWORK_EXTERNAL_ADDRESS Available only when Infinispan clustered embedded is enabled
cache-embedded-network-external-address
IP address that other instances in the cluster should use to contact this node.
Set only if it is different to cache-embedded-network-bind-address, for example when this instance is behind a firewall.
CLI: --cache-embedded-network-external-address Env: KC_CACHE_EMBEDDED_NETWORK_EXTERNAL_ADDRESS
Available only when Infinispan clustered embedded is enabled
cache-embedded-network-external-port Port that other instances in the cluster should use to contact this node. Set only if it is different to cache-embedded-network-bind-port, for example when this instance is behind a firewall CLI: --cache-embedded-network-external-port Env: KC_CACHE_EMBEDDED_NETWORK_EXTERNAL_PORT Available only when Infinispan clustered embedded is enabled
cache-embedded-network-external-port
Port that other instances in the cluster should use to contact this node.
Set only if it is different to cache-embedded-network-bind-port, for example when this instance is behind a firewall
CLI: --cache-embedded-network-external-port Env: KC_CACHE_EMBEDDED_NETWORK_EXTERNAL_PORT
Available only when Infinispan clustered embedded is enabled
cache-embedded-offline-client-sessions-max-count The maximum number of entries that can be stored in-memory by the offlineClientSessions cache. CLI: --cache-embedded-offline-client-sessions-max-count Env: KC_CACHE_EMBEDDED_OFFLINE_CLIENT_SESSIONS_MAX_COUNT Available only when embedded Infinispan clusters configured
cache-embedded-offline-client-sessions-max-count
The maximum number of entries that can be stored in-memory by the offlineClientSessions cache.
CLI: --cache-embedded-offline-client-sessions-max-count Env: KC_CACHE_EMBEDDED_OFFLINE_CLIENT_SESSIONS_MAX_COUNT
Available only when embedded Infinispan clusters configured
cache-embedded-offline-sessions-max-count The maximum number of entries that can be stored in-memory by the offlineSessions cache. CLI: --cache-embedded-offline-sessions-max-count Env: KC_CACHE_EMBEDDED_OFFLINE_SESSIONS_MAX_COUNT Available only when embedded Infinispan clusters configured
cache-embedded-offline-sessions-max-count
The maximum number of entries that can be stored in-memory by the offlineSessions cache.
CLI: --cache-embedded-offline-sessions-max-count Env: KC_CACHE_EMBEDDED_OFFLINE_SESSIONS_MAX_COUNT
Available only when embedded Infinispan clusters configured
cache-embedded-realms-max-count The maximum number of entries that can be stored in-memory by the realms cache. CLI: --cache-embedded-realms-max-count Env: KC_CACHE_EMBEDDED_REALMS_MAX_COUNT
cache-embedded-realms-max-count
The maximum number of entries that can be stored in-memory by the realms cache.
CLI: --cache-embedded-realms-max-count Env: KC_CACHE_EMBEDDED_REALMS_MAX_COUNT
cache-embedded-sessions-max-count The maximum number of entries that can be stored in-memory by the sessions cache. CLI: --cache-embedded-sessions-max-count Env: KC_CACHE_EMBEDDED_SESSIONS_MAX_COUNT Available only when embedded Infinispan clusters configured
cache-embedded-sessions-max-count
The maximum number of entries that can be stored in-memory by the sessions cache.
CLI: --cache-embedded-sessions-max-count Env: KC_CACHE_EMBEDDED_SESSIONS_MAX_COUNT
Available only when embedded Infinispan clusters configured
cache-embedded-users-max-count The maximum number of entries that can be stored in-memory by the users cache. CLI: --cache-embedded-users-max-count Env: KC_CACHE_EMBEDDED_USERS_MAX_COUNT
cache-embedded-users-max-count
The maximum number of entries that can be stored in-memory by the users cache.
CLI: --cache-embedded-users-max-count Env: KC_CACHE_EMBEDDED_USERS_MAX_COUNT
cache-metrics-histograms-enabled Enable histograms for metrics for the embedded caches. CLI: --cache-metrics-histograms-enabled Env: KC_CACHE_METRICS_HISTOGRAMS_ENABLED Available only when metrics are enabled
cache-metrics-histograms-enabled
Enable histograms for metrics for the embedded caches.
CLI: --cache-metrics-histograms-enabled Env: KC_CACHE_METRICS_HISTOGRAMS_ENABLED
Available only when metrics are enabled
true , false (default)
true , false (default)
cache-remote-backup-sites Configures a list of backup sites names to where the external Infinispan cluster backups the Keycloak data. CLI: --cache-remote-backup-sites Env: KC_CACHE_REMOTE_BACKUP_SITES Available only when remote host is set
cache-remote-backup-sites
Configures a list of backup sites names to where the external Infinispan cluster backups the Keycloak data.
CLI: --cache-remote-backup-sites Env: KC_CACHE_REMOTE_BACKUP_SITES
Available only when remote host is set
cache-remote-host The hostname of the external Infinispan cluster. Available only when feature multi-site or clusterless is set. CLI: --cache-remote-host Env: KC_CACHE_REMOTE_HOST
cache-remote-host
The hostname of the external Infinispan cluster.
Available only when feature multi-site or clusterless is set.
CLI: --cache-remote-host Env: KC_CACHE_REMOTE_HOST
cache-remote-password The password for the authentication to the external Infinispan cluster. It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-username is required as well. CLI: --cache-remote-password Env: KC_CACHE_REMOTE_PASSWORD Available only when remote host is set
cache-remote-password
The password for the authentication to the external Infinispan cluster.
It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-username is required as well.
CLI: --cache-remote-password Env: KC_CACHE_REMOTE_PASSWORD
Available only when remote host is set
cache-remote-port The port of the external Infinispan cluster. CLI: --cache-remote-port Env: KC_CACHE_REMOTE_PORT Available only when remote host is set
cache-remote-port
The port of the external Infinispan cluster.
CLI: --cache-remote-port Env: KC_CACHE_REMOTE_PORT
Available only when remote host is set
11222 (default)
11222 (default)
cache-remote-tls-enabled Enable TLS support to communicate with a secured remote Infinispan server. Recommended to be enabled in production. CLI: --cache-remote-tls-enabled Env: KC_CACHE_REMOTE_TLS_ENABLED Available only when remote host is set
cache-remote-tls-enabled
Enable TLS support to communicate with a secured remote Infinispan server.
Recommended to be enabled in production.
CLI: --cache-remote-tls-enabled Env: KC_CACHE_REMOTE_TLS_ENABLED
Available only when remote host is set
true (default), false
true (default), false
cache-remote-username The username for the authentication to the external Infinispan cluster. It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-password is required as well. CLI: --cache-remote-username Env: KC_CACHE_REMOTE_USERNAME Available only when remote host is set
cache-remote-username
The username for the authentication to the external Infinispan cluster.
It is optional if connecting to an unsecure external Infinispan cluster. If the option is specified, cache-remote-password is required as well.
CLI: --cache-remote-username Env: KC_CACHE_REMOTE_USERNAME
Available only when remote host is set
cache-stack Define the default stack to use for cluster communication and node discovery. Defaults to jdbc-ping if not set. CLI: --cache-stack Env: KC_CACHE_STACK Available only when 'cache' type is set to 'ispn' Use 'jdbc-ping' instead by leaving it unset Deprecated values: azure , ec2 , google , jdbc-ping-udp , kubernetes , tcp , udp
cache-stack
Define the default stack to use for cluster communication and node discovery.
Defaults to jdbc-ping if not set.
CLI: --cache-stack Env: KC_CACHE_STACK
Available only when 'cache' type is set to 'ispn'
Use 'jdbc-ping' instead by leaving it unset Deprecated values: azure , ec2 , google , jdbc-ping-udp , kubernetes , tcp , udp
jdbc-ping , kubernetes (deprecated), jdbc-ping-udp (deprecated), tcp (deprecated), udp (deprecated), ec2 (deprecated), azure (deprecated), google (deprecated), or any
jdbc-ping , kubernetes (deprecated), jdbc-ping-udp (deprecated), tcp (deprecated), udp (deprecated), ec2 (deprecated), azure (deprecated), google (deprecated), or any
config-keystore Specifies a path to the KeyStore Configuration Source. CLI: --config-keystore Env: KC_CONFIG_KEYSTORE
config-keystore
Specifies a path to the KeyStore Configuration Source.
CLI: --config-keystore Env: KC_CONFIG_KEYSTORE
config-keystore-password Specifies a password to the KeyStore Configuration Source. CLI: --config-keystore-password Env: KC_CONFIG_KEYSTORE_PASSWORD
config-keystore-password
Specifies a password to the KeyStore Configuration Source.
CLI: --config-keystore-password Env: KC_CONFIG_KEYSTORE_PASSWORD
config-keystore-type Specifies a type of the KeyStore Configuration Source. CLI: --config-keystore-type Env: KC_CONFIG_KEYSTORE_TYPE
config-keystore-type
Specifies a type of the KeyStore Configuration Source.
CLI: --config-keystore-type Env: KC_CONFIG_KEYSTORE_TYPE
PKCS12 (default)
PKCS12 (default)
db The database vendor. In production mode the default value of dev-file is deprecated, you should explicitly specify the db instead. Named key: db-kind-<datasource> CLI: --db Env: KC_DB
The database vendor.
In production mode the default value of dev-file is deprecated, you should explicitly specify the db instead.
Named key: db-kind-<datasource>
CLI: --db Env: KC_DB
dev-file (default), dev-mem , mariadb , mssql , mysql , oracle , postgres , tidb
dev-file (default), dev-mem , mariadb , mssql , mysql , oracle , postgres , tidb
db-debug-jpql Add JPQL information as comments to SQL statements to debug JPA SQL statement generation. Named key: db-debug-jpql-<datasource> CLI: --db-debug-jpql Env: KC_DB_DEBUG_JPQL
db-debug-jpql
Add JPQL information as comments to SQL statements to debug JPA SQL statement generation.
Named key: db-debug-jpql-<datasource>
CLI: --db-debug-jpql Env: KC_DB_DEBUG_JPQL
true , false (default)
true , false (default)
db-driver The fully qualified class name of the JDBC driver. If not set, a default driver is set accordingly to the chosen database. Named key: db-driver-<datasource> CLI: --db-driver Env: KC_DB_DRIVER
The fully qualified class name of the JDBC driver.
If not set, a default driver is set accordingly to the chosen database.
Named key: db-driver-<datasource>
CLI: --db-driver Env: KC_DB_DRIVER
db-log-slow-queries-threshold Log SQL statements slower than the configured threshold with logger org. hibernate.SQL_SLOW and log-level info. Named key: db-log-slow-queries-threshold-<datasource> CLI: --db-log-slow-queries-threshold Env: KC_DB_LOG_SLOW_QUERIES_THRESHOLD
db-log-slow-queries-threshold
Log SQL statements slower than the configured threshold with logger org.
hibernate.SQL_SLOW and log-level info.
Named key: db-log-slow-queries-threshold-<datasource>
CLI: --db-log-slow-queries-threshold Env: KC_DB_LOG_SLOW_QUERIES_THRESHOLD
10000 (default)
10000 (default)
db-password The password of the database user. Named key: db-password-<datasource> CLI: --db-password Env: KC_DB_PASSWORD
db-password
The password of the database user.
Named key: db-password-<datasource>
CLI: --db-password Env: KC_DB_PASSWORD
db-pool-initial-size The initial size of the connection pool. Named key: db-pool-initial-size-<datasource> CLI: --db-pool-initial-size Env: KC_DB_POOL_INITIAL_SIZE
db-pool-initial-size
The initial size of the connection pool.
Named key: db-pool-initial-size-<datasource>
CLI: --db-pool-initial-size Env: KC_DB_POOL_INITIAL_SIZE
db-pool-max-lifetime The maximum time a connection remains in the pool, after which it will be closed upon return and replaced as necessary. May be an ISO 8601 duration value, an integer number of seconds, or an integer followed by one of [ms, h, m, s, d]. CLI: --db-pool-max-lifetime Env: KC_DB_POOL_MAX_LIFETIME
db-pool-max-lifetime
The maximum time a connection remains in the pool, after which it will be closed upon return and replaced as necessary.
May be an ISO 8601 duration value, an integer number of seconds, or an integer followed by one of [ms, h, m, s, d].
CLI: --db-pool-max-lifetime Env: KC_DB_POOL_MAX_LIFETIME
db-pool-max-size The maximum size of the connection pool. Named key: db-pool-max-size-<datasource> CLI: --db-pool-max-size Env: KC_DB_POOL_MAX_SIZE
db-pool-max-size
The maximum size of the connection pool.
Named key: db-pool-max-size-<datasource>
CLI: --db-pool-max-size Env: KC_DB_POOL_MAX_SIZE
100 (default)
100 (default)
db-pool-min-size The minimal size of the connection pool. Named key: db-pool-min-size-<datasource> CLI: --db-pool-min-size Env: KC_DB_POOL_MIN_SIZE
db-pool-min-size
The minimal size of the connection pool.
Named key: db-pool-min-size-<datasource>
CLI: --db-pool-min-size Env: KC_DB_POOL_MIN_SIZE
db-schema The database schema to be used. Named key: db-schema-<datasource> CLI: --db-schema Env: KC_DB_SCHEMA
The database schema to be used.
Named key: db-schema-<datasource>
CLI: --db-schema Env: KC_DB_SCHEMA
db-url The full database JDBC URL. If not provided, a default URL is set based on the selected database vendor. For instance, if using postgres , the default JDBC URL would be jdbc:postgresql://localhost/keycloak . Named key: db-url-full-<datasource> CLI: --db-url Env: KC_DB_URL
The full database JDBC URL.
If not provided, a default URL is set based on the selected database vendor. For instance, if using postgres , the default JDBC URL would be jdbc:postgresql://localhost/keycloak .
Named key: db-url-full-<datasource>
CLI: --db-url Env: KC_DB_URL
db-url-database Sets the database name of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored. Named key: db-url-database-<datasource> CLI: --db-url-database Env: KC_DB_URL_DATABASE
db-url-database
Sets the database name of the default JDBC URL of the chosen vendor.
If the db-url option is set, this option is ignored.
Named key: db-url-database-<datasource>
CLI: --db-url-database Env: KC_DB_URL_DATABASE
db-url-host Sets the hostname of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored. Named key: db-url-host-<datasource> CLI: --db-url-host Env: KC_DB_URL_HOST
db-url-host
Sets the hostname of the default JDBC URL of the chosen vendor.
If the db-url option is set, this option is ignored.
Named key: db-url-host-<datasource>
CLI: --db-url-host Env: KC_DB_URL_HOST
db-url-port Sets the port of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored. Named key: db-url-port-<datasource> CLI: --db-url-port Env: KC_DB_URL_PORT
db-url-port
Sets the port of the default JDBC URL of the chosen vendor.
If the db-url option is set, this option is ignored.
Named key: db-url-port-<datasource>
CLI: --db-url-port Env: KC_DB_URL_PORT
db-url-properties Sets the properties of the default JDBC URL of the chosen vendor. Make sure to set the properties accordingly to the format expected by the database vendor, as well as appending the right character at the beginning of this property value. If the db-url option is set, this option is ignored. Named key: db-url-properties-<datasource> CLI: --db-url-properties Env: KC_DB_URL_PROPERTIES
db-url-properties
Sets the properties of the default JDBC URL of the chosen vendor.
Make sure to set the properties accordingly to the format expected by the database vendor, as well as appending the right character at the beginning of this property value. If the db-url option is set, this option is ignored.
Named key: db-url-properties-<datasource>
CLI: --db-url-properties Env: KC_DB_URL_PROPERTIES
db-username The username of the database user. Named key: db-username-<datasource> CLI: --db-username Env: KC_DB_USERNAME
db-username
The username of the database user.
Named key: db-username-<datasource>
CLI: --db-username Env: KC_DB_USERNAME

## Database - additional datasources

db-debug-jpql-<datasource> Used for named <datasource>. Add JPQL information as comments to SQL statements to debug JPA SQL statement generation. CLI: --db-debug-jpql-<datasource> Env: KC_DB_DEBUG_JPQL_<DATASOURCE>
db-debug-jpql-<datasource>
Used for named <datasource>.
Add JPQL information as comments to SQL statements to debug JPA SQL statement generation.
CLI: --db-debug-jpql-<datasource> Env: KC_DB_DEBUG_JPQL_<DATASOURCE>
true , false (default)
true , false (default)
db-driver-<datasource> Used for named <datasource>. The fully qualified class name of the JDBC driver. If not set, a default driver is set accordingly to the chosen database. CLI: --db-driver-<datasource> Env: KC_DB_DRIVER_<DATASOURCE>
db-driver-<datasource>
Used for named <datasource>.
The fully qualified class name of the JDBC driver. If not set, a default driver is set accordingly to the chosen database.
CLI: --db-driver-<datasource> Env: KC_DB_DRIVER_<DATASOURCE>
db-enabled-<datasource> If the named datasource <datasource> should be enabled at runtime. CLI: --db-enabled-<datasource> Env: KC_DB_ENABLED_<DATASOURCE>
db-enabled-<datasource>
If the named datasource <datasource> should be enabled at runtime.
CLI: --db-enabled-<datasource> Env: KC_DB_ENABLED_<DATASOURCE>
true (default), false
true (default), false
db-kind-<datasource> Used for named <datasource>. The database vendor. In production mode the default value of dev-file is deprecated, you should explicitly specify the db instead. CLI: --db-kind-<datasource> Env: KC_DB_KIND_<DATASOURCE>
db-kind-<datasource>
Used for named <datasource>.
The database vendor. In production mode the default value of dev-file is deprecated, you should explicitly specify the db instead.
CLI: --db-kind-<datasource> Env: KC_DB_KIND_<DATASOURCE>
dev-file , dev-mem , mariadb , mssql , mysql , oracle , postgres , tidb
dev-file , dev-mem , mariadb , mssql , mysql , oracle , postgres , tidb
db-log-slow-queries-threshold-<datasource> Used for named <datasource>. Log SQL statements slower than the configured threshold with logger org.hibernate.SQL_SLOW and log-level info. CLI: --db-log-slow-queries-threshold-<datasource> Env: KC_DB_LOG_SLOW_QUERIES_THRESHOLD_<DATASOURCE>
db-log-slow-queries-threshold-<datasource>
Used for named <datasource>.
Log SQL statements slower than the configured threshold with logger org.hibernate.SQL_SLOW and log-level info.
CLI: --db-log-slow-queries-threshold-<datasource> Env: KC_DB_LOG_SLOW_QUERIES_THRESHOLD_<DATASOURCE>
10000 (default)
10000 (default)
db-password-<datasource> Used for named <datasource>. The password of the database user. CLI: --db-password-<datasource> Env: KC_DB_PASSWORD_<DATASOURCE>
db-password-<datasource>
Used for named <datasource>.
The password of the database user.
CLI: --db-password-<datasource> Env: KC_DB_PASSWORD_<DATASOURCE>
db-pool-initial-size-<datasource> Used for named <datasource>. The initial size of the connection pool. CLI: --db-pool-initial-size-<datasource> Env: KC_DB_POOL_INITIAL_SIZE_<DATASOURCE>
db-pool-initial-size-<datasource>
Used for named <datasource>.
The initial size of the connection pool.
CLI: --db-pool-initial-size-<datasource> Env: KC_DB_POOL_INITIAL_SIZE_<DATASOURCE>
db-pool-max-size-<datasource> Used for named <datasource>. The maximum size of the connection pool. CLI: --db-pool-max-size-<datasource> Env: KC_DB_POOL_MAX_SIZE_<DATASOURCE>
db-pool-max-size-<datasource>
Used for named <datasource>.
The maximum size of the connection pool.
CLI: --db-pool-max-size-<datasource> Env: KC_DB_POOL_MAX_SIZE_<DATASOURCE>
100 (default)
100 (default)
db-pool-min-size-<datasource> Used for named <datasource>. The minimal size of the connection pool. CLI: --db-pool-min-size-<datasource> Env: KC_DB_POOL_MIN_SIZE_<DATASOURCE>
db-pool-min-size-<datasource>
Used for named <datasource>.
The minimal size of the connection pool.
CLI: --db-pool-min-size-<datasource> Env: KC_DB_POOL_MIN_SIZE_<DATASOURCE>
db-schema-<datasource> Used for named <datasource>. The database schema to be used. CLI: --db-schema-<datasource> Env: KC_DB_SCHEMA_<DATASOURCE>
db-schema-<datasource>
Used for named <datasource>.
The database schema to be used.
CLI: --db-schema-<datasource> Env: KC_DB_SCHEMA_<DATASOURCE>
db-url-database-<datasource> Used for named <datasource>. Sets the database name of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored. CLI: --db-url-database-<datasource> Env: KC_DB_URL_DATABASE_<DATASOURCE>
db-url-database-<datasource>
Used for named <datasource>.
Sets the database name of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored.
CLI: --db-url-database-<datasource> Env: KC_DB_URL_DATABASE_<DATASOURCE>
db-url-full-<datasource> Used for named <datasource>. The full database JDBC URL. If not provided, a default URL is set based on the selected database vendor. For instance, if using postgres , the default JDBC URL would be jdbc:postgresql://localhost/keycloak . CLI: --db-url-full-<datasource> Env: KC_DB_URL_FULL_<DATASOURCE>
db-url-full-<datasource>
Used for named <datasource>.
The full database JDBC URL. If not provided, a default URL is set based on the selected database vendor. For instance, if using postgres , the default JDBC URL would be jdbc:postgresql://localhost/keycloak .
CLI: --db-url-full-<datasource> Env: KC_DB_URL_FULL_<DATASOURCE>
db-url-host-<datasource> Used for named <datasource>. Sets the hostname of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored. CLI: --db-url-host-<datasource> Env: KC_DB_URL_HOST_<DATASOURCE>
db-url-host-<datasource>
Used for named <datasource>.
Sets the hostname of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored.
CLI: --db-url-host-<datasource> Env: KC_DB_URL_HOST_<DATASOURCE>
db-url-port-<datasource> Used for named <datasource>. Sets the port of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored. CLI: --db-url-port-<datasource> Env: KC_DB_URL_PORT_<DATASOURCE>
db-url-port-<datasource>
Used for named <datasource>.
Sets the port of the default JDBC URL of the chosen vendor. If the db-url option is set, this option is ignored.
CLI: --db-url-port-<datasource> Env: KC_DB_URL_PORT_<DATASOURCE>
db-url-properties-<datasource> Used for named <datasource>. Sets the properties of the default JDBC URL of the chosen vendor. Make sure to set the properties accordingly to the format expected by the database vendor, as well as appending the right character at the beginning of this property value. If the db-url option is set, this option is ignored. CLI: --db-url-properties-<datasource> Env: KC_DB_URL_PROPERTIES_<DATASOURCE>
db-url-properties-<datasource>
Used for named <datasource>.
Sets the properties of the default JDBC URL of the chosen vendor. Make sure to set the properties accordingly to the format expected by the database vendor, as well as appending the right character at the beginning of this property value. If the db-url option is set, this option is ignored.
CLI: --db-url-properties-<datasource> Env: KC_DB_URL_PROPERTIES_<DATASOURCE>
db-username-<datasource> Used for named <datasource>. The username of the database user. CLI: --db-username-<datasource> Env: KC_DB_USERNAME_<DATASOURCE>
db-username-<datasource>
Used for named <datasource>.
The username of the database user.
CLI: --db-username-<datasource> Env: KC_DB_USERNAME_<DATASOURCE>

## Transaction

transaction-xa-enabled If set to true, XA datasources will be used. Named key: transaction-xa-enabled-<datasource> CLI: --transaction-xa-enabled Env: KC_TRANSACTION_XA_ENABLED
transaction-xa-enabled
If set to true, XA datasources will be used.
Named key: transaction-xa-enabled-<datasource>
CLI: --transaction-xa-enabled Env: KC_TRANSACTION_XA_ENABLED
true , false (default)
true , false (default)
transaction-xa-enabled-<datasource> If set to true, XA for <datasource> datasource will be used. CLI: --transaction-xa-enabled-<datasource> Env: KC_TRANSACTION_XA_ENABLED_<DATASOURCE>
transaction-xa-enabled-<datasource>
If set to true, XA for <datasource> datasource will be used.
CLI: --transaction-xa-enabled-<datasource> Env: KC_TRANSACTION_XA_ENABLED_<DATASOURCE>
true (default), false
true (default), false
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

## Hostname v2

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
http-accept-non-normalized-paths If the server should accept paths that are not normalized according to RFC3986 or that contain a double slash ( // ). While accepting those requests might be relevant for legacy applications, it is recommended to disable it to allow for more concise URL filtering. CLI: --http-accept-non-normalized-paths Env: KC_HTTP_ACCEPT_NON_NORMALIZED_PATHS DEPRECATED.
http-accept-non-normalized-paths
If the server should accept paths that are not normalized according to RFC3986 or that contain a double slash ( // ).
While accepting those requests might be relevant for legacy applications, it is recommended to disable it to allow for more concise URL filtering.
CLI: --http-accept-non-normalized-paths Env: KC_HTTP_ACCEPT_NON_NORMALIZED_PATHS
DEPRECATED.
true , false (default)
true , false (default)
http-enabled Enables the HTTP listener. Enabled by default in development mode. Typically not enabled in production unless the server is fronted by a TLS termination proxy. CLI: --http-enabled Env: KC_HTTP_ENABLED
http-enabled
Enables the HTTP listener.
Enabled by default in development mode. Typically not enabled in production unless the server is fronted by a TLS termination proxy.
CLI: --http-enabled Env: KC_HTTP_ENABLED
true , false (default)
true , false (default)
http-host The HTTP Host. CLI: --http-host Env: KC_HTTP_HOST
The HTTP Host.
CLI: --http-host Env: KC_HTTP_HOST
0.0.0.0 (default)
0.0.0.0 (default)
http-max-queued-requests Maximum number of queued HTTP requests. Use this to shed load in an overload situation. Excess requests will return a "503 Server not Available" response. CLI: --http-max-queued-requests Env: KC_HTTP_MAX_QUEUED_REQUESTS
http-max-queued-requests
Maximum number of queued HTTP requests.
Use this to shed load in an overload situation. Excess requests will return a "503 Server not Available" response.
CLI: --http-max-queued-requests Env: KC_HTTP_MAX_QUEUED_REQUESTS
http-metrics-histograms-enabled Enables a histogram with default buckets for the duration of HTTP server requests. CLI: --http-metrics-histograms-enabled Env: KC_HTTP_METRICS_HISTOGRAMS_ENABLED Available only when metrics are enabled
http-metrics-histograms-enabled
Enables a histogram with default buckets for the duration of HTTP server requests.
CLI: --http-metrics-histograms-enabled Env: KC_HTTP_METRICS_HISTOGRAMS_ENABLED
Available only when metrics are enabled
true , false (default)
true , false (default)
http-metrics-slos Service level objectives for HTTP server requests. Use this instead of the default histogram, or use it in combination to add additional buckets. Specify a list of comma-separated values defined in milliseconds. Example with buckets from 5ms to 10s: 5,10,25,50,250,500,1000,2500,5000,10000 CLI: --http-metrics-slos Env: KC_HTTP_METRICS_SLOS Available only when metrics are enabled
http-metrics-slos
Service level objectives for HTTP server requests.
Use this instead of the default histogram, or use it in combination to add additional buckets. Specify a list of comma-separated values defined in milliseconds. Example with buckets from 5ms to 10s: 5,10,25,50,250,500,1000,2500,5000,10000
CLI: --http-metrics-slos Env: KC_HTTP_METRICS_SLOS
Available only when metrics are enabled
http-pool-max-threads The maximum number of threads. If this is not specified then it will be automatically sized to the greater of 4 * the number of available processors and 50. For example if there are 4 processors the max threads will be 50. If there are 48 processors it will be 192. CLI: --http-pool-max-threads Env: KC_HTTP_POOL_MAX_THREADS
http-pool-max-threads
The maximum number of threads.
If this is not specified then it will be automatically sized to the greater of 4 * the number of available processors and 50. For example if there are 4 processors the max threads will be 50. If there are 48 processors it will be 192.
CLI: --http-pool-max-threads Env: KC_HTTP_POOL_MAX_THREADS
http-port The used HTTP port. CLI: --http-port Env: KC_HTTP_PORT
The used HTTP port.
CLI: --http-port Env: KC_HTTP_PORT
8080 (default)
8080 (default)
http-relative-path Set the path relative to / for serving resources. The path must start with a / . CLI: --http-relative-path Env: KC_HTTP_RELATIVE_PATH
http-relative-path
Set the path relative to / for serving resources.
The path must start with a / .
CLI: --http-relative-path Env: KC_HTTP_RELATIVE_PATH
/ (default)
/ (default)
https-certificate-file The file path to a server certificate or certificate chain in PEM format. CLI: --https-certificate-file Env: KC_HTTPS_CERTIFICATE_FILE
https-certificate-file
The file path to a server certificate or certificate chain in PEM format.
CLI: --https-certificate-file Env: KC_HTTPS_CERTIFICATE_FILE
https-certificate-key-file The file path to a private key in PEM format. CLI: --https-certificate-key-file Env: KC_HTTPS_CERTIFICATE_KEY_FILE
https-certificate-key-file
The file path to a private key in PEM format.
CLI: --https-certificate-key-file Env: KC_HTTPS_CERTIFICATE_KEY_FILE
https-certificates-reload-period Interval on which to reload key store, trust store, and certificate files referenced by https-* options. May be an ISO 8601 duration value, an integer number of seconds, or an integer followed by one of [ms, h, m, s, d]. Must be greater than 30 seconds. Use -1 to disable. CLI: --https-certificates-reload-period Env: KC_HTTPS_CERTIFICATES_RELOAD_PERIOD
https-certificates-reload-period
Interval on which to reload key store, trust store, and certificate files referenced by https-* options.
May be an ISO 8601 duration value, an integer number of seconds, or an integer followed by one of [ms, h, m, s, d]. Must be greater than 30 seconds. Use -1 to disable.
CLI: --https-certificates-reload-period Env: KC_HTTPS_CERTIFICATES_RELOAD_PERIOD
1h (default)
1h (default)
https-cipher-suites The cipher suites to use. If none is given, a reasonable default is selected. CLI: --https-cipher-suites Env: KC_HTTPS_CIPHER_SUITES
https-cipher-suites
The cipher suites to use.
If none is given, a reasonable default is selected.
CLI: --https-cipher-suites Env: KC_HTTPS_CIPHER_SUITES
https-client-auth Configures the server to require/request client authentication. CLI: --https-client-auth Env: KC_HTTPS_CLIENT_AUTH
https-client-auth
Configures the server to require/request client authentication.
CLI: --https-client-auth Env: KC_HTTPS_CLIENT_AUTH
none (default), request , required
none (default), request , required
https-key-store-file The key store which holds the certificate information instead of specifying separate files. CLI: --https-key-store-file Env: KC_HTTPS_KEY_STORE_FILE
https-key-store-file
The key store which holds the certificate information instead of specifying separate files.
CLI: --https-key-store-file Env: KC_HTTPS_KEY_STORE_FILE
https-key-store-password The password of the key store file. CLI: --https-key-store-password Env: KC_HTTPS_KEY_STORE_PASSWORD
https-key-store-password
The password of the key store file.
CLI: --https-key-store-password Env: KC_HTTPS_KEY_STORE_PASSWORD
password (default)
password (default)
https-key-store-type The type of the key store file. If not given, the type is automatically detected based on the file extension. If fips-mode is set to strict and no value is set, it defaults to BCFKS . CLI: --https-key-store-type Env: KC_HTTPS_KEY_STORE_TYPE
https-key-store-type
The type of the key store file.
If not given, the type is automatically detected based on the file extension. If fips-mode is set to strict and no value is set, it defaults to BCFKS .
CLI: --https-key-store-type Env: KC_HTTPS_KEY_STORE_TYPE
https-port The used HTTPS port. CLI: --https-port Env: KC_HTTPS_PORT
The used HTTPS port.
CLI: --https-port Env: KC_HTTPS_PORT
8443 (default)
8443 (default)
https-protocols The list of protocols to explicitly enable. If a value is not supported by the JRE / security configuration, it will be silently ignored. CLI: --https-protocols Env: KC_HTTPS_PROTOCOLS
https-protocols
The list of protocols to explicitly enable.
If a value is not supported by the JRE / security configuration, it will be silently ignored.
CLI: --https-protocols Env: KC_HTTPS_PROTOCOLS
TLSv1.3 , TLSv1.2 , or any
TLSv1.3 , TLSv1.2 , or any
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

## HTTP Access log

http-access-log-enabled If HTTP access logging is enabled. By default this will log records in console. CLI: --http-access-log-enabled Env: KC_HTTP_ACCESS_LOG_ENABLED
http-access-log-enabled
If HTTP access logging is enabled.
By default this will log records in console.
CLI: --http-access-log-enabled Env: KC_HTTP_ACCESS_LOG_ENABLED
true , false (default)
true , false (default)
http-access-log-exclude A regular expression that can be used to exclude some paths from logging. For instance, /realms/my-realm/.* will exclude all subsequent endpoints for realm my-realm from the log. CLI: --http-access-log-exclude Env: KC_HTTP_ACCESS_LOG_EXCLUDE Available only when HTTP Access log is enabled
http-access-log-exclude
A regular expression that can be used to exclude some paths from logging.
For instance, /realms/my-realm/.* will exclude all subsequent endpoints for realm my-realm from the log.
CLI: --http-access-log-exclude Env: KC_HTTP_ACCESS_LOG_EXCLUDE
Available only when HTTP Access log is enabled
http-access-log-pattern The HTTP access log pattern. You can use the available named formats, or use custom format described in Quarkus documentation. CLI: --http-access-log-pattern Env: KC_HTTP_ACCESS_LOG_PATTERN Available only when HTTP Access log is enabled
http-access-log-pattern
The HTTP access log pattern.
You can use the available named formats, or use custom format described in Quarkus documentation.
CLI: --http-access-log-pattern Env: KC_HTTP_ACCESS_LOG_PATTERN
Available only when HTTP Access log is enabled
common (default), combined , long , or any
common (default), combined , long , or any
health-enabled If the server should expose health check endpoints. If enabled, health checks are available at the /health , /health/ready and /health/live endpoints. CLI: --health-enabled Env: KC_HEALTH_ENABLED
health-enabled
If the server should expose health check endpoints.
If enabled, health checks are available at the /health , /health/ready and /health/live endpoints.
CLI: --health-enabled Env: KC_HEALTH_ENABLED
true , false (default)
true , false (default)
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
metrics-enabled If the server should expose metrics. If enabled, metrics are available at the /metrics endpoint. CLI: --metrics-enabled Env: KC_METRICS_ENABLED
metrics-enabled
If the server should expose metrics.
If enabled, metrics are available at the /metrics endpoint.
CLI: --metrics-enabled Env: KC_METRICS_ENABLED
true , false (default)
true , false (default)
proxy-headers The proxy headers that should be accepted by the server.
proxy-headers
The proxy headers that should be accepted by the server.
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
vault Enables a vault provider. CLI: --vault Env: KC_VAULT
Enables a vault provider.
CLI: --vault Env: KC_VAULT
file , keystore
file , keystore
vault-dir If set, secrets can be obtained by reading the content of files within the given directory. CLI: --vault-dir Env: KC_VAULT_DIR
If set, secrets can be obtained by reading the content of files within the given directory.
CLI: --vault-dir Env: KC_VAULT_DIR
vault-file Path to the keystore file. CLI: --vault-file Env: KC_VAULT_FILE
Path to the keystore file.
CLI: --vault-file Env: KC_VAULT_FILE
vault-pass Password for the vault keystore. CLI: --vault-pass Env: KC_VAULT_PASS
Password for the vault keystore.
CLI: --vault-pass Env: KC_VAULT_PASS
vault-type Specifies the type of the keystore file. CLI: --vault-type Env: KC_VAULT_TYPE
Specifies the type of the keystore file.
CLI: --vault-type Env: KC_VAULT_TYPE
PKCS12 (default)
PKCS12 (default)
log Enable one or more log handlers in a comma-separated list. CLI: --log Env: KC_LOG
Enable one or more log handlers in a comma-separated list.
CLI: --log Env: KC_LOG
console , file , syslog
console , file , syslog
log-async Indicates whether to log asynchronously to all handlers. CLI: --log-async Env: KC_LOG_ASYNC
Indicates whether to log asynchronously to all handlers.
CLI: --log-async Env: KC_LOG_ASYNC
true , false (default)
true , false (default)
log-console-async Indicates whether to log asynchronously to console. If not set, value from the parent property log-async is used. CLI: --log-console-async Env: KC_LOG_CONSOLE_ASYNC Available only when Console log handler is activated
log-console-async
Indicates whether to log asynchronously to console.
If not set, value from the parent property log-async is used.
CLI: --log-console-async Env: KC_LOG_CONSOLE_ASYNC
Available only when Console log handler is activated
true , false (default)
true , false (default)
log-console-async-queue-length The queue length to use before flushing writing when logging to console. CLI: --log-console-async-queue-length Env: KC_LOG_CONSOLE_ASYNC_QUEUE_LENGTH Available only when Console log handler is activated and asynchronous logging is enabled
log-console-async-queue-length
The queue length to use before flushing writing when logging to console.
CLI: --log-console-async-queue-length Env: KC_LOG_CONSOLE_ASYNC_QUEUE_LENGTH
Available only when Console log handler is activated and asynchronous logging is enabled
512 (default)
512 (default)
log-console-color Enable or disable colors when logging to console. CLI: --log-console-color Env: KC_LOG_CONSOLE_COLOR Available only when Console log handler is activated
log-console-color
Enable or disable colors when logging to console.
CLI: --log-console-color Env: KC_LOG_CONSOLE_COLOR
Available only when Console log handler is activated
true , false (default)
true , false (default)
log-console-format The format of unstructured console log entries. If the format has spaces in it, escape the value using "<format>". CLI: --log-console-format Env: KC_LOG_CONSOLE_FORMAT Available only when Console log handler is activated
log-console-format
The format of unstructured console log entries.
If the format has spaces in it, escape the value using "<format>".
CLI: --log-console-format Env: KC_LOG_CONSOLE_FORMAT
Available only when Console log handler is activated
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
log-console-include-mdc Include mdc information in the console log. If the log-console-format option is specified, this option has no effect. CLI: --log-console-include-mdc Env: KC_LOG_CONSOLE_INCLUDE_MDC Available only when Console log handler and MDC logging are activated
log-console-include-mdc
Include mdc information in the console log.
If the log-console-format option is specified, this option has no effect.
CLI: --log-console-include-mdc Env: KC_LOG_CONSOLE_INCLUDE_MDC
Available only when Console log handler and MDC logging are activated
true (default), false
true (default), false
log-console-include-trace Include tracing information in the console log. If the log-console-format option is specified, this option has no effect. CLI: --log-console-include-trace Env: KC_LOG_CONSOLE_INCLUDE_TRACE Available only when Console log handler and Tracing is activated
log-console-include-trace
Include tracing information in the console log.
If the log-console-format option is specified, this option has no effect.
CLI: --log-console-include-trace Env: KC_LOG_CONSOLE_INCLUDE_TRACE
Available only when Console log handler and Tracing is activated
true (default), false
true (default), false
log-console-json-format Set the format of the produced JSON. CLI: --log-console-json-format Env: KC_LOG_CONSOLE_JSON_FORMAT Available only when Console log handler is activated and output is set to 'json'
log-console-json-format
Set the format of the produced JSON.
CLI: --log-console-json-format Env: KC_LOG_CONSOLE_JSON_FORMAT
Available only when Console log handler is activated and output is set to 'json'
default (default), ecs
default (default), ecs
log-console-level Set the log level for the console handler. It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide. CLI: --log-console-level Env: KC_LOG_CONSOLE_LEVEL Available only when Console log handler is activated
log-console-level
Set the log level for the console handler.
It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide.
CLI: --log-console-level Env: KC_LOG_CONSOLE_LEVEL
Available only when Console log handler is activated
off , fatal , error , warn , info , debug , trace , all (default)
off , fatal , error , warn , info , debug , trace , all (default)
log-console-output Set the log output to JSON or default (plain) unstructured logging. CLI: --log-console-output Env: KC_LOG_CONSOLE_OUTPUT Available only when Console log handler is activated
log-console-output
Set the log output to JSON or default (plain) unstructured logging.
CLI: --log-console-output Env: KC_LOG_CONSOLE_OUTPUT
Available only when Console log handler is activated
default (default), json
default (default), json
log-file Set the log file path and filename. CLI: --log-file Env: KC_LOG_FILE Available only when File log handler is activated
Set the log file path and filename.
CLI: --log-file Env: KC_LOG_FILE
Available only when File log handler is activated
data/log/keycloak.log (default)
data/log/keycloak.log (default)
log-file-async Indicates whether to log asynchronously to file log. If not set, value from the parent property log-async is used. CLI: --log-file-async Env: KC_LOG_FILE_ASYNC Available only when File log handler is activated
log-file-async
Indicates whether to log asynchronously to file log.
If not set, value from the parent property log-async is used.
CLI: --log-file-async Env: KC_LOG_FILE_ASYNC
Available only when File log handler is activated
true , false (default)
true , false (default)
log-file-async-queue-length The queue length to use before flushing writing when logging to file log. CLI: --log-file-async-queue-length Env: KC_LOG_FILE_ASYNC_QUEUE_LENGTH Available only when File log handler is activated and asynchronous logging is enabled
log-file-async-queue-length
The queue length to use before flushing writing when logging to file log.
CLI: --log-file-async-queue-length Env: KC_LOG_FILE_ASYNC_QUEUE_LENGTH
Available only when File log handler is activated and asynchronous logging is enabled
512 (default)
512 (default)
log-file-format Set a format specific to file log entries. CLI: --log-file-format Env: KC_LOG_FILE_FORMAT Available only when File log handler is activated
log-file-format
Set a format specific to file log entries.
CLI: --log-file-format Env: KC_LOG_FILE_FORMAT
Available only when File log handler is activated
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
log-file-include-mdc Include MDC information in the file log. If the log-file-format option is specified, this option has no effect. CLI: --log-file-include-mdc Env: KC_LOG_FILE_INCLUDE_MDC Available only when File log handler and MDC logging are activated
log-file-include-mdc
Include MDC information in the file log.
If the log-file-format option is specified, this option has no effect.
CLI: --log-file-include-mdc Env: KC_LOG_FILE_INCLUDE_MDC
Available only when File log handler and MDC logging are activated
true (default), false
true (default), false
log-file-include-trace Include tracing information in the file log. If the log-file-format option is specified, this option has no effect. CLI: --log-file-include-trace Env: KC_LOG_FILE_INCLUDE_TRACE Available only when File log handler and Tracing is activated
log-file-include-trace
Include tracing information in the file log.
If the log-file-format option is specified, this option has no effect.
CLI: --log-file-include-trace Env: KC_LOG_FILE_INCLUDE_TRACE
Available only when File log handler and Tracing is activated
true (default), false
true (default), false
log-file-json-format Set the format of the produced JSON. CLI: --log-file-json-format Env: KC_LOG_FILE_JSON_FORMAT Available only when File log handler is activated and output is set to 'json'
log-file-json-format
Set the format of the produced JSON.
CLI: --log-file-json-format Env: KC_LOG_FILE_JSON_FORMAT
Available only when File log handler is activated and output is set to 'json'
default (default), ecs
default (default), ecs
log-file-level Set the log level for the file handler. It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide. CLI: --log-file-level Env: KC_LOG_FILE_LEVEL Available only when File log handler is activated
log-file-level
Set the log level for the file handler.
It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide.
CLI: --log-file-level Env: KC_LOG_FILE_LEVEL
Available only when File log handler is activated
off , fatal , error , warn , info , debug , trace , all (default)
off , fatal , error , warn , info , debug , trace , all (default)
log-file-output Set the log output to JSON or default (plain) unstructured logging. CLI: --log-file-output Env: KC_LOG_FILE_OUTPUT Available only when File log handler is activated
log-file-output
Set the log output to JSON or default (plain) unstructured logging.
CLI: --log-file-output Env: KC_LOG_FILE_OUTPUT
Available only when File log handler is activated
default (default), json
default (default), json
log-level The log level of the root category or a comma-separated list of individual categories and their levels. For the root category, you don’t need to specify a category. CLI: --log-level Env: KC_LOG_LEVEL
The log level of the root category or a comma-separated list of individual categories and their levels.
For the root category, you don’t need to specify a category.
CLI: --log-level Env: KC_LOG_LEVEL
[info] (default)
[info] (default)
log-level-<category> The log level of a category. Takes precedence over the log-level option. CLI: --log-level-<category> Env: KC_LOG_LEVEL_<CATEGORY>
log-level-<category>
The log level of a category.
Takes precedence over the log-level option.
CLI: --log-level-<category> Env: KC_LOG_LEVEL_<CATEGORY>
off , fatal , error , warn , info , debug , trace , all
off , fatal , error , warn , info , debug , trace , all
log-mdc-enabled Indicates whether to add information about the realm and other information to the mapped diagnostic context. All elements will be prefixed with kc. CLI: --log-mdc-enabled Env: KC_LOG_MDC_ENABLED Available only when log-mdc preview feature is enabled
log-mdc-enabled
Indicates whether to add information about the realm and other information to the mapped diagnostic context.
All elements will be prefixed with kc.
CLI: --log-mdc-enabled Env: KC_LOG_MDC_ENABLED
Available only when log-mdc preview feature is enabled
true , false (default)
true , false (default)
log-mdc-keys Defines which information should be added to the mapped diagnostic context as a comma-separated list. CLI: --log-mdc-keys Env: KC_LOG_MDC_KEYS Available only when MDC logging is enabled
log-mdc-keys
Defines which information should be added to the mapped diagnostic context as a comma-separated list.
CLI: --log-mdc-keys Env: KC_LOG_MDC_KEYS
Available only when MDC logging is enabled
realmName , clientId , userId , ipAddress , org , sessionId , authenticationSessionId , authenticationTabId
realmName , clientId , userId , ipAddress , org , sessionId , authenticationSessionId , authenticationTabId
log-syslog-app-name Set the app name used when formatting the message in RFC5424 format. CLI: --log-syslog-app-name Env: KC_LOG_SYSLOG_APP_NAME Available only when Syslog is activated
log-syslog-app-name
Set the app name used when formatting the message in RFC5424 format.
CLI: --log-syslog-app-name Env: KC_LOG_SYSLOG_APP_NAME
Available only when Syslog is activated
keycloak (default)
keycloak (default)
log-syslog-async Indicates whether to log asynchronously to Syslog. If not set, value from the parent property log-async is used. CLI: --log-syslog-async Env: KC_LOG_SYSLOG_ASYNC Available only when Syslog is activated
log-syslog-async
Indicates whether to log asynchronously to Syslog.
If not set, value from the parent property log-async is used.
CLI: --log-syslog-async Env: KC_LOG_SYSLOG_ASYNC
Available only when Syslog is activated
true , false (default)
true , false (default)
log-syslog-async-queue-length The queue length to use before flushing writing when logging to Syslog. CLI: --log-syslog-async-queue-length Env: KC_LOG_SYSLOG_ASYNC_QUEUE_LENGTH Available only when Syslog is activated and asynchronous logging is enabled
log-syslog-async-queue-length
The queue length to use before flushing writing when logging to Syslog.
CLI: --log-syslog-async-queue-length Env: KC_LOG_SYSLOG_ASYNC_QUEUE_LENGTH
Available only when Syslog is activated and asynchronous logging is enabled
512 (default)
512 (default)
log-syslog-counting-framing If true , the message being sent is prefixed with the size of the message. If protocol-dependent , the default value is true when log-syslog-protocol is tcp or ssl-tcp , otherwise false . CLI: --log-syslog-counting-framing Env: KC_LOG_SYSLOG_COUNTING_FRAMING Available only when Syslog is activated
log-syslog-counting-framing
If true , the message being sent is prefixed with the size of the message.
If protocol-dependent , the default value is true when log-syslog-protocol is tcp or ssl-tcp , otherwise false .
CLI: --log-syslog-counting-framing Env: KC_LOG_SYSLOG_COUNTING_FRAMING
Available only when Syslog is activated
true , false , protocol-dependent (default)
true , false , protocol-dependent (default)
log-syslog-endpoint Set the IP address and port of the Syslog server. CLI: --log-syslog-endpoint Env: KC_LOG_SYSLOG_ENDPOINT Available only when Syslog is activated
log-syslog-endpoint
Set the IP address and port of the Syslog server.
CLI: --log-syslog-endpoint Env: KC_LOG_SYSLOG_ENDPOINT
Available only when Syslog is activated
localhost:514 (default)
localhost:514 (default)
log-syslog-format Set a format specific to Syslog entries. CLI: --log-syslog-format Env: KC_LOG_SYSLOG_FORMAT Available only when Syslog is activated
log-syslog-format
Set a format specific to Syslog entries.
CLI: --log-syslog-format Env: KC_LOG_SYSLOG_FORMAT
Available only when Syslog is activated
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
log-syslog-include-mdc Include MDC information in the Syslog. If the log-syslog-format option is specified, this option has no effect. CLI: --log-syslog-include-mdc Env: KC_LOG_SYSLOG_INCLUDE_MDC Available only when Syslog handler and MDC logging are activated
log-syslog-include-mdc
Include MDC information in the Syslog.
If the log-syslog-format option is specified, this option has no effect.
CLI: --log-syslog-include-mdc Env: KC_LOG_SYSLOG_INCLUDE_MDC
Available only when Syslog handler and MDC logging are activated
true (default), false
true (default), false
log-syslog-include-trace Include tracing information in the Syslog. If the log-syslog-format option is specified, this option has no effect. CLI: --log-syslog-include-trace Env: KC_LOG_SYSLOG_INCLUDE_TRACE Available only when Syslog handler and Tracing is activated
log-syslog-include-trace
Include tracing information in the Syslog.
If the log-syslog-format option is specified, this option has no effect.
CLI: --log-syslog-include-trace Env: KC_LOG_SYSLOG_INCLUDE_TRACE
Available only when Syslog handler and Tracing is activated
true (default), false
true (default), false
log-syslog-json-format Set the format of the produced JSON. CLI: --log-syslog-json-format Env: KC_LOG_SYSLOG_JSON_FORMAT Available only when Syslog is activated and output is set to 'json'
log-syslog-json-format
Set the format of the produced JSON.
CLI: --log-syslog-json-format Env: KC_LOG_SYSLOG_JSON_FORMAT
Available only when Syslog is activated and output is set to 'json'
default (default), ecs
default (default), ecs
log-syslog-level Set the log level for the Syslog handler. It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide. CLI: --log-syslog-level Env: KC_LOG_SYSLOG_LEVEL Available only when Syslog is activated
log-syslog-level
Set the log level for the Syslog handler.
It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide.
CLI: --log-syslog-level Env: KC_LOG_SYSLOG_LEVEL
Available only when Syslog is activated
off , fatal , error , warn , info , debug , trace , all (default)
off , fatal , error , warn , info , debug , trace , all (default)
log-syslog-max-length Set the maximum length, in bytes, of the message allowed to be sent. The length includes the header and the message. If not set, the default value is 2048 when log-syslog-type is rfc5424 (default) and 1024 when log-syslog-type is rfc3164. CLI: --log-syslog-max-length Env: KC_LOG_SYSLOG_MAX_LENGTH Available only when Syslog is activated
log-syslog-max-length
Set the maximum length, in bytes, of the message allowed to be sent.
The length includes the header and the message. If not set, the default value is 2048 when log-syslog-type is rfc5424 (default) and 1024 when log-syslog-type is rfc3164.
CLI: --log-syslog-max-length Env: KC_LOG_SYSLOG_MAX_LENGTH
Available only when Syslog is activated
log-syslog-output Set the Syslog output to JSON or default (plain) unstructured logging. CLI: --log-syslog-output Env: KC_LOG_SYSLOG_OUTPUT Available only when Syslog is activated
log-syslog-output
Set the Syslog output to JSON or default (plain) unstructured logging.
CLI: --log-syslog-output Env: KC_LOG_SYSLOG_OUTPUT
Available only when Syslog is activated
default (default), json
default (default), json
log-syslog-protocol Set the protocol used to connect to the Syslog server. CLI: --log-syslog-protocol Env: KC_LOG_SYSLOG_PROTOCOL Available only when Syslog is activated
log-syslog-protocol
Set the protocol used to connect to the Syslog server.
CLI: --log-syslog-protocol Env: KC_LOG_SYSLOG_PROTOCOL
Available only when Syslog is activated
tcp (default), udp , ssl-tcp
tcp (default), udp , ssl-tcp
log-syslog-type Set the Syslog type used to format the sent message. CLI: --log-syslog-type Env: KC_LOG_SYSLOG_TYPE Available only when Syslog is activated
log-syslog-type
Set the Syslog type used to format the sent message.
CLI: --log-syslog-type Env: KC_LOG_SYSLOG_TYPE
Available only when Syslog is activated
rfc5424 (default), rfc3164
rfc5424 (default), rfc3164
tracing-compression OpenTelemetry compression method used to compress payloads. If unset, compression is disabled. CLI: --tracing-compression Env: KC_TRACING_COMPRESSION Available only when Tracing is enabled
tracing-compression
OpenTelemetry compression method used to compress payloads.
If unset, compression is disabled.
CLI: --tracing-compression Env: KC_TRACING_COMPRESSION
Available only when Tracing is enabled
gzip , none (default)
gzip , none (default)
tracing-enabled Enables the OpenTelemetry tracing. CLI: --tracing-enabled Env: KC_TRACING_ENABLED Available only when 'opentelemetry' feature is enabled
tracing-enabled
Enables the OpenTelemetry tracing.
CLI: --tracing-enabled Env: KC_TRACING_ENABLED
Available only when 'opentelemetry' feature is enabled
true , false (default)
true , false (default)
tracing-endpoint OpenTelemetry endpoint to connect to. CLI: --tracing-endpoint Env: KC_TRACING_ENDPOINT Available only when Tracing is enabled
tracing-endpoint
OpenTelemetry endpoint to connect to.
CLI: --tracing-endpoint Env: KC_TRACING_ENDPOINT
Available only when Tracing is enabled
http://localhost:4317 (default)
http://localhost:4317 (default)
tracing-infinispan-enabled Enables the OpenTelemetry tracing for embedded Infinispan. CLI: --tracing-infinispan-enabled Env: KC_TRACING_INFINISPAN_ENABLED Available only when tracing and embedded Infinispan is enabled
tracing-infinispan-enabled
Enables the OpenTelemetry tracing for embedded Infinispan.
CLI: --tracing-infinispan-enabled Env: KC_TRACING_INFINISPAN_ENABLED
Available only when tracing and embedded Infinispan is enabled
true (default), false
true (default), false
tracing-jdbc-enabled Enables the OpenTelemetry JDBC tracing. CLI: --tracing-jdbc-enabled Env: KC_TRACING_JDBC_ENABLED Available only when Tracing is enabled
tracing-jdbc-enabled
Enables the OpenTelemetry JDBC tracing.
CLI: --tracing-jdbc-enabled Env: KC_TRACING_JDBC_ENABLED
Available only when Tracing is enabled
true (default), false
true (default), false
tracing-protocol OpenTelemetry protocol used for the telemetry data. CLI: --tracing-protocol Env: KC_TRACING_PROTOCOL Available only when Tracing is enabled
tracing-protocol
OpenTelemetry protocol used for the telemetry data.
CLI: --tracing-protocol Env: KC_TRACING_PROTOCOL
Available only when Tracing is enabled
grpc (default), http/protobuf
grpc (default), http/protobuf
tracing-resource-attributes OpenTelemetry resource attributes present in the exported trace to characterize the telemetry producer. Values in format key1=val1,key2=val2 . For more information, check the Tracing guide. CLI: --tracing-resource-attributes Env: KC_TRACING_RESOURCE_ATTRIBUTES Available only when Tracing is enabled
tracing-resource-attributes
OpenTelemetry resource attributes present in the exported trace to characterize the telemetry producer.
Values in format key1=val1,key2=val2 . For more information, check the Tracing guide.
CLI: --tracing-resource-attributes Env: KC_TRACING_RESOURCE_ATTRIBUTES
Available only when Tracing is enabled
tracing-sampler-ratio OpenTelemetry sampler ratio. Probability that a span will be sampled. Expected double value in interval [0,1]. CLI: --tracing-sampler-ratio Env: KC_TRACING_SAMPLER_RATIO Available only when Tracing is enabled
tracing-sampler-ratio
OpenTelemetry sampler ratio.
Probability that a span will be sampled. Expected double value in interval [0,1].
CLI: --tracing-sampler-ratio Env: KC_TRACING_SAMPLER_RATIO
Available only when Tracing is enabled
1.0 (default)
1.0 (default)
tracing-sampler-type OpenTelemetry sampler to use for tracing. CLI: --tracing-sampler-type Env: KC_TRACING_SAMPLER_TYPE Available only when Tracing is enabled
tracing-sampler-type
OpenTelemetry sampler to use for tracing.
CLI: --tracing-sampler-type Env: KC_TRACING_SAMPLER_TYPE
Available only when Tracing is enabled
always_on , always_off , traceidratio (default), parentbased_always_on , parentbased_always_off , parentbased_traceidratio
always_on , always_off , traceidratio (default), parentbased_always_on , parentbased_always_off , parentbased_traceidratio
tracing-service-name OpenTelemetry service name. Takes precedence over service.name defined in the tracing-resource-attributes property. CLI: --tracing-service-name Env: KC_TRACING_SERVICE_NAME Available only when Tracing is enabled
tracing-service-name
OpenTelemetry service name.
Takes precedence over service.name defined in the tracing-resource-attributes property.
CLI: --tracing-service-name Env: KC_TRACING_SERVICE_NAME
Available only when Tracing is enabled
keycloak (default)
keycloak (default)
event-metrics-user-enabled Create metrics based on user events. CLI: --event-metrics-user-enabled Env: KC_EVENT_METRICS_USER_ENABLED Available only when metrics are enabled and feature user-event-metrics is enabled
event-metrics-user-enabled
Create metrics based on user events.
CLI: --event-metrics-user-enabled Env: KC_EVENT_METRICS_USER_ENABLED
Available only when metrics are enabled and feature user-event-metrics is enabled
true , false (default)
true , false (default)
event-metrics-user-events Comma-separated list of events to be collected for user event metrics. This option can be used to reduce the number of metrics created as by default all user events create a metric. CLI: --event-metrics-user-events Env: KC_EVENT_METRICS_USER_EVENTS Available only when user event metrics are enabled Use remove_credential instead of remove_totp , and update_credential instead of update_totp and update_password . Deprecated values: remove_totp , update_totp , update_password
event-metrics-user-events
Comma-separated list of events to be collected for user event metrics.
This option can be used to reduce the number of metrics created as by default all user events create a metric.
CLI: --event-metrics-user-events Env: KC_EVENT_METRICS_USER_EVENTS
Available only when user event metrics are enabled
Use remove_credential instead of remove_totp , and update_credential instead of update_totp and update_password . Deprecated values: remove_totp , update_totp , update_password
authreqid_to_token , client_delete , client_info , client_initiated_account_linking , client_login , client_register , client_update , code_to_token , custom_required_action , delete_account , execute_action_token , execute_actions , federated_identity_link , federated_identity_override_link , grant_consent , identity_provider_first_login , identity_provider_link_account , identity_provider_login , identity_provider_post_login , identity_provider_response , identity_provider_retrieve_token , impersonate , introspect_token , invalid_signature , invite_org , login , logout , oauth2_device_auth , oauth2_device_code_to_token , oauth2_device_verify_user_code , oauth2_extension_grant , permission_token , pushed_authorization_request , refresh_token , register , register_node , remove_credential , remove_federated_identity , remove_totp (deprecated), reset_password , restart_authentication , revoke_grant , send_identity_provider_link , send_reset_password , send_verify_email , token_exchange , unregister_node , update_consent , update_credential , update_email , update_password (deprecated), update_profile , update_totp (deprecated), user_disabled_by_permanent_lockout , user_disabled_by_temporary_lockout , user_info_request , verify_email , verify_profile
authreqid_to_token , client_delete , client_info , client_initiated_account_linking , client_login , client_register , client_update , code_to_token , custom_required_action , delete_account , execute_action_token , execute_actions , federated_identity_link , federated_identity_override_link , grant_consent , identity_provider_first_login , identity_provider_link_account , identity_provider_login , identity_provider_post_login , identity_provider_response , identity_provider_retrieve_token , impersonate , introspect_token , invalid_signature , invite_org , login , logout , oauth2_device_auth , oauth2_device_code_to_token , oauth2_device_verify_user_code , oauth2_extension_grant , permission_token , pushed_authorization_request , refresh_token , register , register_node , remove_credential , remove_federated_identity , remove_totp (deprecated), reset_password , restart_authentication , revoke_grant , send_identity_provider_link , send_reset_password , send_verify_email , token_exchange , unregister_node , update_consent , update_credential , update_email , update_password (deprecated), update_profile , update_totp (deprecated), user_disabled_by_permanent_lockout , user_disabled_by_temporary_lockout , user_info_request , verify_email , verify_profile
event-metrics-user-tags Comma-separated list of tags to be collected for user event metrics. By default only realm is enabled to avoid a high metrics cardinality. CLI: --event-metrics-user-tags Env: KC_EVENT_METRICS_USER_TAGS Available only when user event metrics are enabled
event-metrics-user-tags
Comma-separated list of tags to be collected for user event metrics.
By default only realm is enabled to avoid a high metrics cardinality.
CLI: --event-metrics-user-tags Env: KC_EVENT_METRICS_USER_TAGS
Available only when user event metrics are enabled
realm , idp , clientId
realm , idp , clientId
tls-hostname-verifier The TLS hostname verification policy for out-going HTTPS and SMTP requests. ANY should not be used in production. CLI: --tls-hostname-verifier Env: KC_TLS_HOSTNAME_VERIFIER STRICT and WILDCARD have been deprecated, use DEFAULT instead. Deprecated values: STRICT , WILDCARD
tls-hostname-verifier
The TLS hostname verification policy for out-going HTTPS and SMTP requests.
ANY should not be used in production.
CLI: --tls-hostname-verifier Env: KC_TLS_HOSTNAME_VERIFIER
STRICT and WILDCARD have been deprecated, use DEFAULT instead. Deprecated values: STRICT , WILDCARD
ANY , WILDCARD (deprecated), STRICT (deprecated), DEFAULT (default)
ANY , WILDCARD (deprecated), STRICT (deprecated), DEFAULT (default)
truststore-paths List of pkcs12 (p12, pfx, or pkcs12 file extensions), PEM files, or directories containing those files that will be used as a system truststore. CLI: --truststore-paths Env: KC_TRUSTSTORE_PATHS
truststore-paths
List of pkcs12 (p12, pfx, or pkcs12 file extensions), PEM files, or directories containing those files that will be used as a system truststore.
CLI: --truststore-paths Env: KC_TRUSTSTORE_PATHS
fips-mode Sets the FIPS mode. If non-strict is set, FIPS is enabled but on non-approved mode. For full FIPS compliance, set strict to run on approved mode. This option defaults to disabled when fips feature is disabled, which is by default. This option defaults to non-strict when fips feature is enabled. CLI: --fips-mode Env: KC_FIPS_MODE
Sets the FIPS mode.
If non-strict is set, FIPS is enabled but on non-approved mode. For full FIPS compliance, set strict to run on approved mode. This option defaults to disabled when fips feature is disabled, which is by default. This option defaults to non-strict when fips feature is enabled.
CLI: --fips-mode Env: KC_FIPS_MODE
non-strict , strict
non-strict , strict
dir Set the path to a directory where files will be created with the exported data. CLI: --dir Env: KC_DIR
Set the path to a directory where files will be created with the exported data.
CLI: --dir Env: KC_DIR
file Set the path to a file that will be created with the exported data. To export more than 50000 users, export to a directory with different files instead. CLI: --file Env: KC_FILE
Set the path to a file that will be created with the exported data.
To export more than 50000 users, export to a directory with different files instead.
CLI: --file Env: KC_FILE
realm Set the name of the realm to export. If not set, all realms are going to be exported. CLI: --realm Env: KC_REALM
Set the name of the realm to export.
If not set, all realms are going to be exported.
CLI: --realm Env: KC_REALM
users Set how users should be exported. CLI: --users Env: KC_USERS
Set how users should be exported.
CLI: --users Env: KC_USERS
skip , realm_file , same_file , different_files (default)
skip , realm_file , same_file , different_files (default)
users-per-file Set the number of users per file. It is used only if users is set to different_files . CLI: --users-per-file Env: KC_USERS_PER_FILE
users-per-file
Set the number of users per file.
It is used only if users is set to different_files .
CLI: --users-per-file Env: KC_USERS_PER_FILE
50 (default)
50 (default)
dir Set the path to a directory where files will be read from. CLI: --dir Env: KC_DIR
Set the path to a directory where files will be read from.
CLI: --dir Env: KC_DIR
file Set the path to a file that will be read. CLI: --file Env: KC_FILE
Set the path to a file that will be read.
CLI: --file Env: KC_FILE
override Set if existing data should be overwritten. If set to false, data will be ignored. CLI: --override Env: KC_OVERRIDE
Set if existing data should be overwritten.
If set to false, data will be ignored.
CLI: --override Env: KC_OVERRIDE
true (default), false
true (default), false

## Bootstrap Admin

bootstrap-admin-client-id Client id for the temporary bootstrap admin service account. Used only when the master realm is created. Available only when bootstrap admin client secret is set. CLI: --bootstrap-admin-client-id Env: KC_BOOTSTRAP_ADMIN_CLIENT_ID
bootstrap-admin-client-id
Client id for the temporary bootstrap admin service account.
Used only when the master realm is created. Available only when bootstrap admin client secret is set.
CLI: --bootstrap-admin-client-id Env: KC_BOOTSTRAP_ADMIN_CLIENT_ID
temp-admin (default)
temp-admin (default)
bootstrap-admin-client-secret Client secret for the temporary bootstrap admin service account. Used only when the master realm is created. Use a non-CLI configuration option for this option if possible. CLI: --bootstrap-admin-client-secret Env: KC_BOOTSTRAP_ADMIN_CLIENT_SECRET
bootstrap-admin-client-secret
Client secret for the temporary bootstrap admin service account.
Used only when the master realm is created. Use a non-CLI configuration option for this option if possible.
CLI: --bootstrap-admin-client-secret Env: KC_BOOTSTRAP_ADMIN_CLIENT_SECRET
bootstrap-admin-password Temporary bootstrap admin password. Used only when the master realm is created. Use a non-CLI configuration option for this option if possible. CLI: --bootstrap-admin-password Env: KC_BOOTSTRAP_ADMIN_PASSWORD
bootstrap-admin-password
Temporary bootstrap admin password.
Used only when the master realm is created. Use a non-CLI configuration option for this option if possible.
CLI: --bootstrap-admin-password Env: KC_BOOTSTRAP_ADMIN_PASSWORD
bootstrap-admin-username Temporary bootstrap admin username. Used only when the master realm is created. Available only when bootstrap admin password is set. CLI: --bootstrap-admin-username Env: KC_BOOTSTRAP_ADMIN_USERNAME
bootstrap-admin-username
Temporary bootstrap admin username.
Used only when the master realm is created. Available only when bootstrap admin password is set.
CLI: --bootstrap-admin-username Env: KC_BOOTSTRAP_ADMIN_USERNAME
temp-admin (default)
temp-admin (default)

---
Quelle: https://www.keycloak.org/server/all-config
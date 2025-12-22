# Configuring providers - Keycloak

# Configuring providers

The server is built with extensibility in mind and for that it provides a number of Service Provider Interfaces or SPIs, each one
responsible for providing a specific capability to the server. In this guide, you are going to understand the core concepts around
the configuration of SPIs and their respective providers.
After reading this guide, you should be able to use the concepts and the steps herein explained to install, uninstall, enable, disable, and configure
any provider, including those you have implemented to extend the server capabilities in order to better fulfill your requirements.

## Configuration option format

Providers can be configured by using a specific configuration format. The format consists of:
Or if there is no possibility of ambiguity between multiple providers:
The <spi-id> is the name of the SPI you want to configure.
The <provider-id> is the id of the provider you want to configure. This is the id set to the corresponding provider factory implementation.
The <property> is the actual name of the property you want to set for a given provider
the property name enabled is effectively reserved for enabling / disabling a provider
All those names (for spi, provider, and property) should be in lower case and if the name is in camel-case such as myKeycloakProvider , it should include dashes ( - ) before upper-case letters as follows: my-keycloak-provider .
Taking the HttpClientSpi SPI as an example, the name of the SPI is connectionsHttpClient and one of the provider implementations available is named default . In order to set the connectionPoolSize property you would use a configuration option as follows:

### Setting a provider configuration option

Provider configuration options are provided when starting the server. See all support configuration sources and formats for options in Configuring Keycloak . For example via a command line option:

## Build time options

### Configuring a single provider for an SPI

Depending on the SPI, multiple provider implementations can co-exist but only one of them is going to be used at runtime.
For these SPIs, a specific provider is the primary implementation that is going to be active and used at runtime. The format consists of:
spi-<spi-id>-provider=<provider-id> may still be used, but the server will not properly detect when reaugmentation is needed.
To configure a provider as the single provider you should run the build command as follows:

### Configuring a default provider for an SPI

Depending on the SPI, multiple provider implementations can co-exist and one is used by default.
For these SPIs, a specific provider is the default implementation that is going to selected unless a specific provider
is requested. The format consists of:
spi-<spi-id>-provider-default=<provider-id> may still be used, but the server will not properly detect when reaugmentation is needed.
The following logic is used to determine the default provider:
- The explicitly configured default provider
The explicitly configured default provider
- The provider with the highest order (providers with order ⇐ 0 are ignored)
The provider with the highest order (providers with order ⇐ 0 are ignored)
- The provider with the id set to default
The provider with the id set to default
To configure a provider as the default provider you should run the build command as follows:

### Enabling and disabling a provider

The format consists of:
spi-<spi-id>-<provider-id>-enabled=<boolean> may still be used, but the server will not properly detect when reaugmentation is needed.
To enable or disable a provider you should run the build command as follows:
To disable a provider, use the same command and set the enabled property to false .

## Installing and uninstalling a provider

Custom providers should be packaged in a Java Archive (JAR) file and copied to the providers directory of the distribution. After that if you are using --optimized,
you must run the build command in order to update the server’s provider registry with the implementations from the JAR file.
This step is needed in order to optimize the server runtime so that all providers are known ahead-of-time rather than discovered only when starting the server or at runtime.
Do not install untrusted provider JARs! There is a single class loader for the entire application, and JARs in the providers directory are given precedent over built-in libraries.
There is also no built-in sandboxing of what state or methods are available to provider logic. Providers can do whatever the server process can which includes direct access to the DB, reading all server configuration (incl. credentials), etc.
To uninstall a provider, you should remove the JAR file from the providers directory and run the build command again.

## Using third-party dependencies

When implementing a provider you might need to use some third-party dependency that is not available from the server distribution.
In this case, you should copy any additional dependency to the providers directory and run the build command.
Once you do that, the server is going to make these additional dependencies available at runtime for any provider that depends on them.
- Configuring Keycloak
Configuring Keycloak
- Server Developer Documentation
Server Developer Documentation

---
Quelle: https://www.keycloak.org/server/configuration-provider
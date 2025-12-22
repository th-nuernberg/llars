# Configuring Keycloak for production - Keycloak

# Configuring Keycloak for production

A Keycloak production environment provides secure authentication and authorization for deployments that range from on-premise deployments that support a few thousand users to deployments that serve millions of users.
This guide describes the general areas of configuration required for a production ready Keycloak environment. This information focuses on the general concepts instead of the actual implementation, which depends on your environment. The key aspects covered in this guide apply to all environments, whether it is containerized, on-premise, GitOps, or Ansible.

## TLS for secure communication

Keycloak continually exchanges sensitive data, which means that all communication to and from Keycloak requires a secure communication channel. To prevent several attack vectors, you enable HTTP over TLS, or HTTPS, for that channel.
To configure secure communication channels for Keycloak, see Configuring TLS and Configuring outgoing HTTP requests .
To secure the cache communication for Keycloak, see Configuring distributed caches .

## The hostname for Keycloak

In a production environment, Keycloak instances usually run in a private network, but Keycloak needs to expose certain public facing endpoints to communicate with the applications to be secured.
For details on the endpoint categories and instructions on how to configure the public hostname for them, see Configuring the hostname (v2) .

### Exposing the Keycloak Administration APIs and UI on a different hostname

It is considered a best practice to expose the Keycloak Administration REST API and Console on a different hostname or context-path than the one used for the public frontend URLs that are used e.g. by login flows. This separation ensures that the Administration interfaces are not exposed to the public internet, which reduces the attack surface.
Access to REST APIs needs to be blocked on the reverse proxy level, if they are not intended to be publicly exposed.
For details, see Configuring the hostname (v2) .

## Reverse proxy in a distributed environment

Apart from Configuring the hostname (v2) , production environments usually include a reverse proxy / load balancer component. It separates and unifies access to the network used by your company or organization. For a Keycloak production environment, this component is recommended.
For details on configuring proxy communication modes in Keycloak, see Configuring a reverse proxy . That guide also recommends which paths should be hidden from public access and which paths should be exposed so that Keycloak can secure your applications.

## Limit the number of queued requests

A production environment should protect itself from an overload situation, so that it responds to as many valid requests as possible, and to continue regular operations once the situation returns to normal again.
One way of doing this is rejecting additional requests once a certain threshold is reached.
Load shedding should be implemented on all levels, including the load balancers in your environment.
In addition to that, there is a feature in Keycloak to limit the number of requests that can’t be processed right away and need to be queued.
By default, there is no limit set.
Set the option http-max-queued-requests to limit the number of queued requests to a given threshold matching your environment.
Any request that exceeds this limit would return with an immediate 503 Server not Available response.

## Production grade database

The database used by Keycloak is crucial for the overall performance, availability, reliability and integrity of Keycloak. For details on how to configure a supported database, see Configuring the database .

## Running Keycloak in a cluster

To ensure that users can continue to log in when a Keycloak instance goes down, a typical production environment contains two or more Keycloak instances.
Keycloak runs on top of JGroups and Infinispan, which provide a reliable, high-availability stack for a clustered scenario. In the default setup, communication between the nodes is encrypted using TLS.
To find out more about using multiple nodes, the different caches and an appropriate stack for your environment, see Configuring distributed caches .

### Configure Firewall ports

A set of network ports must be open to allow a healthy network communication between Keycloak servers.
See Configuring distributed caches .
It describes what ports need to be open and their usage.

## Configure Keycloak Server with IPv4 or IPv6

The system properties java.net.preferIPv4Stack and java.net.preferIPv6Addresses are used to configure the JVM for use with IPv4 or IPv6 addresses.
By default, Keycloak is accessible via IPv4 and IPv6 addresses at the same time.
In order to run only with IPv4 addresses, you need to specify the property java.net.preferIPv4Stack=true .
The latter ensures that any hostname to IP address conversions always return IPv4 address variants.
These system properties are conveniently set by the JAVA_OPTS_APPEND environment variable.
For example, to change the IP stack preference to IPv4, set an environment variable as follows:
To set up the server for IPv6 only, set an environment variable as follows for the distributed caches to form a cluster:
See Configuring distributed caches for more details.

---
Quelle: https://www.keycloak.org/server/configuration-production
# Planning for securing applications and services - Keycloak

# Planning for securing applications and services

As an OAuth2, OpenID Connect and SAML compliant server, Keycloak can secure any application and service as long
as the technology stack they are using supports any of these protocols. For more details about the security protocols
supported by Keycloak, consider looking at Server Administration Guide .
Most of the support for some of these protocols is already available from the programming language, framework,
or reverse proxy they are using. Leveraging the support already available from the application ecosystem is a key aspect to make your
application fully compliant with security standards and best practices, so that you avoid vendor lock-in.
For some programming languages, Keycloak provides libraries that try to fill the gap for the lack of support of
a particular security protocol or to provide a more rich and tightly coupled integration with the server. These libraries
are known by Keycloak Client Adapters , and they should be used as a last resort if you cannot rely on what is available
from the application ecosystem.

## Basic steps to secure applications and services

These are the basic steps for securing an application or a service in Keycloak.
- Register a client to a realm using one of these options: The Keycloak Admin Console The client registration service The CLI
Register a client to a realm using one of these options:
- The Keycloak Admin Console
The Keycloak Admin Console
- The client registration service
The client registration service
- Enable OpenID Connect or SAML protocols in your application using one these options: Leveraging existing OpenID Connect and SAML support from the application ecosystem Using a Keycloak Adapter
Enable OpenID Connect or SAML protocols in your application using one these options:
- Leveraging existing OpenID Connect and SAML support from the application ecosystem
Leveraging existing OpenID Connect and SAML support from the application ecosystem
- Using a Keycloak Adapter
Using a Keycloak Adapter
This guide provides the detailed instructions for these steps. You can find more details
in the Server Administration Guide about how to register a client to Keycloak through the
administration console.

## Getting Started

The Keycloak Quickstarts Repository provides examples about how to secure applications and services
using different programming languages and frameworks. By going through their documentation and codebase, you will
understand the bare minimum changes required in your application and service in order to secure it with Keycloak.
Also, see the following sections for recommendations for trusted and well-known client-side implementations for both OpenID
Connect and SAML protocols.

### OpenID Connect

- Wildfly Elytron OIDC
Wildfly Elytron OIDC
- Spring Boot
Spring Boot

#### JavaScript (client-side)

- Keycloak JS adapter
Keycloak JS adapter

#### Node.js (server-side)

- Keycloak Node.js adapter
Keycloak Node.js adapter

#### Apache HTTP Server

- mod_auth_openidc
mod_auth_openidc
- Keycloak SAML Galleon feature pack for WildFly and EAP
Keycloak SAML Galleon feature pack for WildFly and EAP

#### Apache HTTP Server

- Configuring the mod_auth_mellon Apache Module
Configuring the mod_auth_mellon Apache Module

## Terminology

These terms are used in this guide:
- Clients are entities that interact with Keycloak to authenticate users and obtain tokens. Most often, clients are applications and services acting on behalf of users that provide a single sign-on experience to their users and access other services using the tokens issued by the server. Clients can also be entities only interested in obtaining tokens and acting on their own behalf for accessing other services.
Clients are entities that interact with Keycloak to authenticate users and obtain tokens. Most often, clients are applications and services acting on behalf of users that provide a single sign-on experience to their users and access other services using the tokens issued by the server. Clients can also be entities only interested in obtaining tokens and acting on their own behalf for accessing other services.
- Applications include a wide range of applications that work for specific platforms for each protocol
Applications include a wide range of applications that work for specific platforms for each protocol
- Client adapters are libraries that make it easy to secure applications and services with Keycloak. They provide a tight integration to the underlying platform and framework.
Client adapters are libraries that make it easy to secure applications and services with Keycloak. They provide a tight integration to the underlying platform and framework.
- Creating a client and registering a client are the same action. Creating a Client is the term used to create a client by using the Admin Console. Registering a client is the term used to register a client by using the Keycloak Client Registration Service.
Creating a client and registering a client are the same action. Creating a Client is the term used to create a client by using the Admin Console. Registering a client is the term used to register a client by using the Keycloak Client Registration Service.
- A service account is a type of client that is able to obtain tokens on its own behalf.
A service account is a type of client that is able to obtain tokens on its own behalf.

---
Quelle: https://www.keycloak.org/securing-apps/overview
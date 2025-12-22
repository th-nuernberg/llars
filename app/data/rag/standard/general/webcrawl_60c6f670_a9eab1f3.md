# Basic Keycloak deployment - Keycloak

# Basic Keycloak deployment

## Performing a basic Keycloak deployment

This guide describes how to perform a basic Keycloak Deployment on
Kubernetes or
OpenShift using the Operator.

### Preparing for deployment

Once the Keycloak Operator is installed and running in the cluster namespace, you can set up the other deployment prerequisites.
- TLS Certificate and associated keys
TLS Certificate and associated keys
A database should be available and accessible from the cluster namespace where Keycloak is installed.
For a list of supported databases, see Configuring the database .
The Keycloak Operator does not manage the database and you need to provision it yourself. Consider verifying your cloud provider offering or using a database operator.
For development purposes, you can use an ephemeral PostgreSQL pod installation. To provision it, follow the approach below:
Create YAML file example-postgres.yaml :
Apply the changes:
For a production ready installation, you need a hostname that can be used to contact Keycloak.
See Configuring the hostname (v2) for the available configurations.
For development purposes, this guide will use test.keycloak.org .
When running on OpenShift, with ingress enabled, and with the spec.ingress.classname set to openshift-default, you may leave the spec.hostname.hostname unpopulated in the Keycloak CR.
The operator will assign a default hostname to the stored version of the CR similar to what would be created by an OpenShift Route without an explicit host - that is ingress-namespace.appsDomain
If the appsDomain changes, or should you need a different hostname for any reason, then update the Keycloak CR.
If you set the hostname-admin , or the deprecated hostname-admin-url , even if you enable ingress, no ingress will be created specifically for admin access.
Admin access via a separate hostname is generally expected to have access restrictions, which are not currently expressible via the Keycloak CR.
Also the default ingress does not prevent accessing admin endpoints, so you may not want to enable ingress handling via the Keycloak CR at all when you have a separate hostname for admin endpoints.

#### TLS Certificate and key

See your Certification Authority to obtain the certificate and the key.
For development purposes, you can enter this command to obtain a self-signed certificate:
You should install it in the cluster namespace as a Secret by entering this command:

### Deploying Keycloak

To deploy Keycloak, you create a Custom Resource (CR) based on the Keycloak Custom Resource Definition (CRD).
Consider storing the Database credentials in a separate Secret. Enter the following commands:
You can customize several fields using the Keycloak CRD. For a basic deployment, you can stick to the following approach:
Create YAML file example-kc.yaml :
Apply the changes:
To check that the Keycloak instance has been provisioned in the cluster, check the status of the created CR by entering the following command:
When the deployment is ready, look for output similar to the following:

### Accessing the Keycloak deployment

The Keycloak deployment can be exposed through a basic Ingress accessible through the provided hostname.
On installations with multiple default IngressClass instances
or when running on OpenShift 4.12+ you should provide an ingressClassName by setting ingress spec with className property to the desired class name:
Edit YAML file example-kc.yaml :
The operator annotates the Ingress to match expectations for TLS passthrough or TLS termination on OpenShift with the default IngressClass.
See below for more on TLS termination.

#### Proxy modes with the basic Ingress

The operator annotates the Ingress to match expectations for TLS termination or passthrough on OpenShift with the default IngressClass.
For this reason TLS reencryption is not yet considered supported by basic Ingress, but you may be able to specify the tlsSecret on both the http and ingress specs as a starting point.
You should double check the requirements of your IngressClass and platform to see if additional Ingress or Service annotations are needed in your desired scenario.
TLS passthrough is shown in the preceding example-kc example. It is enabled when you associate a tlsSecret with the http configuration and leave Ingress enabled without specifying a tlsSecret on it.
TLS termination, or edge mode, is enabled by associating a tlsSecret with the ingress spec and by enabling HTTP access.
Example TLS Termination YAML:

#### Custom Access

If the default ingress does not fit your use case, disable it by setting ingress spec with enabled property to false value:
Edit YAML file example-kc.yaml :
Apply the changes:
You can then provide an alternative ingress resource pointing to the service <keycloak-cr-name>-service . For example, on OpenShift you are not allowed to use wildcard certificates on passthrough Routes with HTTP/2 enabled. A Keycloak CR on OpenShift with TLS enabled using a wildcard certificate with the default IngressClass creates such a Route. In this case, you must disable the built-in ingress with .spec.ingress.enabled: false . Access may then be provided by creating a reencrypt Route instead:
For debugging and development purposes, consider directly connecting to the Keycloak service using a port forward. For example, enter this command:

#### Configuring the reverse proxy settings matching your Ingress Controller

The Operator supports configuring which of the reverse proxy headers should be accepted by server, which includes Forwarded and X-Forwarded-* headers.
If you Ingress implementation sets and overwrites either Forwarded or X-Forwarded-* headers, you can reflect that
in the Keycloak CR as follows:
If the proxy.headers field is not specified, the Operator falls back to legacy behaviour by implicitly setting proxy=passthrough by default. This results in deprecation warnings in the server log. This fallback will be removed
in a future release.
When using the proxy.headers field, make sure your Ingress properly sets and overwrites the Forwarded or X-Forwarded-* headers respectively. To set these headers, consult the documentation for your Ingress Controller. Consider configuring it for
either reencrypt or edge TLS termination as passthrough TLS doesn’t allow the Ingress to modify the requests headers.
Misconfiguration will leave Keycloak exposed to security vulnerabilities.
For more details refer to the Configuring a reverse proxy guide.

### Accessing the Admin Console

When deploying Keycloak, the operator generates an arbitrary initial admin username and password and stores those credentials as a basic-auth Secret object in the same namespace as the CR.
Change the default admin credentials and enable MFA in Keycloak before going to production.
Change the default admin credentials and enable MFA in Keycloak before going to production.
To fetch the initial admin credentials, you have to read and decode the Secret.
The Secret name is derived from the Keycloak CR name plus the fixed suffix -initial-admin .
To get the username and password for the example-kc CR, enter the following commands:
You can use those credentials to access the Admin Console or the Admin REST API.

### Security Considerations

Anyone with the ability to create or edit Keycloak or KeycloakRealmImport CRs should be a namespace level admin.
Anyone with the ability to create or edit Keycloak or KeycloakRealmImport CRs should be a namespace level admin.
Setting the Keycloak CR image requires a high degree of trust as whatever image is running will at least have access to any Secrets used for environment variables.
Similarly the unsupported podTemplate gives the ability to deploy alternative workloads which may be granted the same permissions as the operator itself - which includes the ability to access Secrets in the namespace.

---
Quelle: https://www.keycloak.org/operator/basic-deployment
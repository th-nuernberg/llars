# Bootstrapping and recovering an admin account - Keycloak

# Bootstrapping and recovering an admin account

## A temporary admin account

A user or service admin account created using one of the methods described below is temporary . This means the account should exist only for the duration necessary to perform operations needed to gain permanent and more secure admin access. After that, the account needs to be removed manually. Various UI/UX elements, such as the Administration Console warning banner, labels, and log messages, will indicate to a Keycloak administrator that the account is temporary.

## Bootstrapping a temporary admin account at Keycloak startup

Keycloak start and start-dev commands support options for bootstrapping both temporary admin users and admin service accounts. These options are standard configuration options, so they can be specified in any of the configuration sources such as environment variables or CLI parameters. For instance, the following examples demonstrate how to use the start and start-dev commands with CLI parameters to bootstrap a temporary admin user and an admin service account, respectively:
The username or client ID values can be omitted; see the Default values section below for more information.
The purpose of these options is solely for bootstrapping temporary admin accounts. These accounts will be created only during the initial start of the Keycloak server when the master realm doesn’t exist yet. The accounts are always created in the master realm. For recovering lost admin access, use the dedicated command described in the sections below.

## Bootstrapping an admin user or service account using the dedicated command

The bootstrap-admin command can be executed even before the first-ever start of Keycloak. Bear in mind that all the Keycloak nodes need to be stopped prior to using this command. Its execution will trigger the creation of the initial master realm, and as a result, the startup options to bootstrap the admin user and service account will be ignored later when the server is started for the first time.
Additionally, it is strongly recommended to use the dedicated command with the same options that the Keycloak server is started with (e.g., db options).
If you have built an optimized version of Keycloak with the build command as outlined in Configuring Keycloak , use the command line option --optimized to have Keycloak skip the build check for a faster startup time.
When doing this, remove the build time options from the command line and keep only the runtime options.
if you do not use --optimized keep in mind that an bootstrap-admin command may implicitly create or update an optimized build for you - if you are running the command from the same machine as a server instance, this may impact the next start of your server.

### Create an admin user

To create a temporary admin user, execute the following command:
If no other parameters are specified and/or no corresponding environment variables are set, the user is prompted to enter the required information. The username value can be omitted to use the default values. For more information, see the Default values and Environment variables sections below.
Alternatively, the parameters can be directly specified in the command:
This command creates a temporary admin user with the username tmpadm and the password retrieved from the environment variable.

### Create a service account

In automated scenarios, a temporary admin service account can be a more suitable alternative to a temporary admin user.
To create a temporary admin service account, execute the following command:
Similarly, if no corresponding environment variables or additional parameters are set, the user will be prompted to enter the required information. The client ID value can be omitted to use the default values. For more information, see the Default values and Environment variables sections below.
Alternatively, the parameters can be directly specified in the command:
This command creates a temporary admin service account with the client ID tmpclient and the secret retrieved from the environment variable.

## Regaining access to the realm with an increased security

Passwordless, OTP, or other advanced authentication methods can be enforced for a realm with lost admin access. In such a case, the admin service account needs to be created to recover lost admin access to the realm. After the service account is created, authentication against the Keycloak instance is required to perform all necessary operations:
Next, retrieve the credentialId . For this example, the OTP credential is the relevant one. Use the following command to get an array of CredentialRepresentation objects and find the one with type set to otp :
Finally, the retrieved ID can be used to remove the advanced authentication method (in our case, OTP):

## Default values

For both the startup and dedicated command scenarios, the username and client ID are optional and default to temp-admin for both the user and service account, respectively.

## Disable the parameters prompt

To disable the prompt for the parameters, the --no-prompt parameter can be used. For example:
If no corresponding environment variable is set, the command will fail with an error message indicating that the required password parameter is missing.
The --no-prompt parameter can be useful if the username or client ID should be omitted. For example:
This creates a temporary admin user with the default username without prompting for confirmation. For more information, see the Default values section above.

## Environment variables

For the bootstrap-admin user command, both username and password can be optionally set as environment variables:
For the bootstrap-admin service command, the client ID is optional and defaults to temp-admin , while the client secret is required to be set as an environment variable:

---
Quelle: https://www.keycloak.org/server/bootstrap-admin-recovery
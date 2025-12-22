# OpenShift - Keycloak

## Before you start

Make sure your machine or container platform can provide sufficient memory and CPU for your desired usage of Keycloak.
See Concepts for sizing CPU and memory resources for more on how to get started with production sizing.
- Install Red Hat Code Ready Containers and follow the steps in the documentation to install a
local OpenShift cluster.
Install Red Hat Code Ready Containers and follow the steps in the documentation to install a
local OpenShift cluster.
- Make sure the cluster is functional by entering the following command: crc status
Make sure the cluster is functional by entering the following command:
- Look for output similar to the following to confirm the cluster is working. CRC VM: Running
OpenShift: Running
...
Look for output similar to the following to confirm the cluster is working.
- Log in as the user developer : oc login -u developer -p developer
Log in as the user developer :
- Create a project called keycloak by entering the following command: oc new-project keycloak
Create a project called keycloak by entering the following command:

## Start Keycloak

- To start a Keycloak server in your project, enter the following command: oc process -f https://raw.githubusercontent.com/keycloak/keycloak-quickstarts/refs/heads/main/openshift/keycloak.yaml \
 -p KC_BOOTSTRAP_ADMIN_USERNAME=admin \
 -p KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
 -p NAMESPACE=keycloak \
| oc create -f - In this example, the user name and password are admin .
To start a Keycloak server in your project, enter the following command:
In this example, the user name and password are admin .
- Once the command above completes, look for a message similar to this: service/keycloak created
route.route.openshift.io/keycloak created
deploymentconfig.apps.openshift.io/keycloak created. At this point, OpenShift will provision a Keycloak pod and related resources. As part of the process, OpenShift will
try to pull the Keycloak server image. This operation might take some time depending on your network connection.
Once the command above completes, look for a message similar to this:
At this point, OpenShift will provision a Keycloak pod and related resources. As part of the process, OpenShift will
try to pull the Keycloak server image. This operation might take some time depending on your network connection.
- To make sure Keycloak is provisioned, execute the following command: oc get pods
To make sure Keycloak is provisioned, execute the following command:
- After a while, look for a message similar to the following; it indicates the pod is ready: NAME READY STATUS RESTARTS AGE
keycloak-1-deploy 0/1 Completed 0 1h
keycloak-1-l9kdx 1/1 Running 0 1h
After a while, look for a message similar to the following; it indicates the pod is ready:
- Once the server is provisioned, enter the following command to find out the Keycloak URLs: KEYCLOAK_URL=https://$(oc get route keycloak --template='{{ .spec.host }}') &&
echo "" &&
echo "Keycloak: $KEYCLOAK_URL" &&
echo "Keycloak Admin Console: $KEYCLOAK_URL/admin" &&
echo "Keycloak Account Console: $KEYCLOAK_URL/realms/myrealm/account" &&
echo ""
Once the server is provisioned, enter the following command to find out the Keycloak URLs:
If you will eventually want more than one server replica, please see the Scaling guide.
Remember these URLs as you will need them throughout this guide. The URL for the account console won’t work
right now as you will need to create the realm first.

## Log in to the Admin Console

- Go to the Keycloak Admin Console.
Go to the Keycloak Admin Console.
- Log in with the username and password you created earlier.
Log in with the username and password you created earlier.

## Create a realm

A realm in Keycloak is equivalent to a tenant. Each realm allows an administrator to create isolated groups of applications and users. Initially, Keycloak
includes a single realm, called master . Use this realm only for managing Keycloak and not for managing any applications.
Use these steps to create the first realm.
- Open the Keycloak Admin Console.
Open the Keycloak Admin Console.
- Click Create Realm next to Current realm .
Click Create Realm next to Current realm .
- Enter myrealm in the Realm name field.
Enter myrealm in the Realm name field.
- Click Create .
Click Create .

## Create a user

Initially, the realm has no users. Use these steps to create a user:
- Verify that you are still in the myrealm realm, which is next to Current realm .
Verify that you are still in the myrealm realm, which is next to Current realm .
- Click Users in the left-hand menu.
Click Users in the left-hand menu.
- Click Create new user .
Click Create new user .
- Fill in the form with the following values: Username : myuser First name : any first name Last name : any last name
Fill in the form with the following values:
- Username : myuser
Username : myuser
- First name : any first name
First name : any first name
- Last name : any last name
Last name : any last name
- Click Create .
Click Create .
This user needs a password to log in. To set the initial password:
- Click Credentials at the top of the page.
Click Credentials at the top of the page.
- Fill in the Set password form with a password.
Fill in the Set password form with a password.
- Toggle Temporary to Off so that the user does not need to update this password at the first login.
Toggle Temporary to Off so that the user does not need to update this password at the first login.

## Log in to the Account Console

You can now log in to the Account Console to verify this user is configured correctly.
- Open the Keycloak Account Console.
Open the Keycloak Account Console.
- Log in with myuser and the password you created earlier.
Log in with myuser and the password you created earlier.
As a user in the Account Console, you can manage your account including modifying your profile, adding two-factor authentication, and including identity provider accounts.

## Secure the first application

To secure the first application, you start by registering the application with your Keycloak instance:
- Open the Keycloak Admin Console.
Open the Keycloak Admin Console.
- Click myrealm next to Current realm .
Click myrealm next to Current realm .
- Click Clients .
Click Clients .
- Click Create client
Click Create client
- Fill in the form with the following values: Client type : OpenID Connect Client ID : myclient Figure 4. Add client
Fill in the form with the following values:
- Client type : OpenID Connect
Client type : OpenID Connect
- Client ID : myclient Figure 4. Add client
Client ID : myclient
- Confirm that Standard flow is enabled.
Confirm that Standard flow is enabled.
- Click Next .
Click Next .
- Make these changes under Login settings . Set Valid redirect URIs to https://www.keycloak.org/app/* Set Web origins to https://www.keycloak.org
Make these changes under Login settings .
- Set Valid redirect URIs to https://www.keycloak.org/app/*
Set Valid redirect URIs to https://www.keycloak.org/app/*
- Set Web origins to https://www.keycloak.org
Set Web origins to https://www.keycloak.org
- Click Save .
Click Save .
To confirm the client was created successfully, you can use the SPA testing application on the Keycloak website .
- Open https://www.keycloak.org/app/ .
Open https://www.keycloak.org/app/ .
- Change Keycloak URL to the URL of your Keycloak instance.
Change Keycloak URL to the URL of your Keycloak instance.
- Click Save .
Click Save .
- Click Sign in to authenticate to this application using the Keycloak server you started earlier.
Click Sign in to authenticate to this application using the Keycloak server you started earlier.

## Taking the next step

Before you run Keycloak in production, consider the following actions:
- Switch to a production ready database such as PostgreSQL.
Switch to a production ready database such as PostgreSQL.
- Configure SSL with your own certificates.
Configure SSL with your own certificates.
- Switch the admin password to a more secure password.
Switch the admin password to a more secure password.
For more information, see the server guides .

---
Quelle: https://www.keycloak.org/getting-started/getting-started-openshift
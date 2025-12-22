# Directory Structure - Keycloak

# Directory Structure

## Installation Locations

If you are installing from a zip file then by default there will be an install root directory of keycloak-26.4.6 , which can be created anywhere you choose on your filesystem.
/opt/keycloak is the root install location for the server in all containerized usage shown for Keycloak including Running Keycloak in a container , Docker , Podman , Kubernetes , and OpenShift .
In the rest of the documentation, relative paths are understood to be relative to the install root - for example, conf/file.xml means <install root>/conf/file.xml

## Directory Structure

Under the Keycloak install root there exists a number of folders:
- bin/ - contains all the shell scripts for the server, including kc.sh|bat , kcadm.sh|bat , and kcreg.sh|bat client/ - used internally
bin/ - contains all the shell scripts for the server, including kc.sh|bat , kcadm.sh|bat , and kcreg.sh|bat
- client/ - used internally
client/ - used internally
- conf/ - directory used for configuration files, including keycloak.conf - see Configuring Keycloak . Many options for specifying a configuration file expect paths relative to this directory. truststores/ - default path used by the truststore-paths option - see Configuring trusted certificates
conf/ - directory used for configuration files, including keycloak.conf - see Configuring Keycloak . Many options for specifying a configuration file expect paths relative to this directory.
- truststores/ - default path used by the truststore-paths option - see Configuring trusted certificates
truststores/ - default path used by the truststore-paths option - see Configuring trusted certificates
- data/ - directory for the server to store runtime information, such as transaction logs logs/ - default directory for file logging - see Configuring logging
data/ - directory for the server to store runtime information, such as transaction logs
- logs/ - default directory for file logging - see Configuring logging
logs/ - default directory for file logging - see Configuring logging
- lib/ - used internally
lib/ - used internally
- providers/ - directory for user provided dependencies - see Configuring providers for extending the server and Configuring the database for an example of adding a JDBC driver.
providers/ - directory for user provided dependencies - see Configuring providers for extending the server and Configuring the database for an example of adding a JDBC driver.
- themes/ - directory for customizations to the Admin Console - see Developing Themes
themes/ - directory for customizations to the Admin Console - see Developing Themes

---
Quelle: https://www.keycloak.org/server/directory-structure
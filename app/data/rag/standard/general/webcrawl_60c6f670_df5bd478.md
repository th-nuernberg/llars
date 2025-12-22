# Automating a realm import - Keycloak

# Automating a realm import

## Importing a Keycloak Realm

Using the Keycloak Operator, you can perform a realm import for the Keycloak Deployment.
If a Realm with the same name already exists in Keycloak, it will not be overwritten. The Realm Import CR only supports creation of new realms and does not update or delete those. Changes to the realm performed directly on Keycloak are not synced back in the CR. Once the realm is imported you should delete the Realm Import CR as that will cleanup the associated Kubernetes Job and Pod resources.
- If a Realm with the same name already exists in Keycloak, it will not be overwritten.
If a Realm with the same name already exists in Keycloak, it will not be overwritten.
- The Realm Import CR only supports creation of new realms and does not update or delete those. Changes to the realm performed directly on Keycloak are not synced back in the CR.
The Realm Import CR only supports creation of new realms and does not update or delete those. Changes to the realm performed directly on Keycloak are not synced back in the CR.
- Once the realm is imported you should delete the Realm Import CR as that will cleanup the associated Kubernetes Job and Pod resources.
Once the realm is imported you should delete the Realm Import CR as that will cleanup the associated Kubernetes Job and Pod resources.

### Creating a Realm Import Custom Resource

The following is an example of a Realm Import Custom Resource (CR):
This CR should be created in the same namespace as the Keycloak Deployment CR, defined in the field keycloakCRName .
The realm field accepts a full RealmRepresentation .
The recommended way to obtain a RealmRepresentation is by leveraging the export functionality Importing and exporting realms .
- Export the Realm to a single file.
Export the Realm to a single file.
- Convert the JSON file to YAML.
Convert the JSON file to YAML.
- Copy and paste the obtained YAML file as body for the realm key, making sure the indentation is correct.
Copy and paste the obtained YAML file as body for the realm key, making sure the indentation is correct.

### Applying the Realm Import CR

Use kubectl to create the CR in the correct cluster namespace:
Create YAML file example-realm-import.yaml :
Apply the changes:
To check the status of the running import, enter the following command:
When the import has successfully completed, the output will look like the following example:

### Placeholders

Imports support placeholders referencing environment variables, see Importing and exporting realms for more.
The KeycloakRealmImport CR allows you to leverage this functionality via the spec.placeholders stanza, for example:
In the above example placeholder replacement will be enabled and an environment variable with key ENV_KEY will be created from the Secret SECRET_NAME 's value for key SECRET_KEY .
Currently only Secrets are supported and they must be in the same namespace as the Keycloak CR.

### Security Considerations

Anyone with the ability to create or edit KeycloakRealmImport CRs should be a namespace level admin.
Anyone with the ability to create or edit KeycloakRealmImport CRs should be a namespace level admin.
Placeholder replacement gives access to all environment variables even sensitive ones.

---
Quelle: https://www.keycloak.org/operator/realm-import
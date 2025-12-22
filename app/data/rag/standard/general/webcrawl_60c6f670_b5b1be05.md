# Using a vault - Keycloak

# Using a vault

Keycloak provides two out-of-the-box implementations of the Vault SPI: a plain-text file-based vault and Java KeyStore-based vault.
The file-based vault implementation is especially useful for Kubernetes/OpenShift secrets. You can mount Kubernetes secrets into the Keycloak Container, and the data fields will be available in the mounted folder with a flat-file structure.
The Java KeyStore-based vault implementation is useful for storing secrets in bare metal installations. You can use the KeyStore vault, which is encrypted using a password.

## Available integrations

Secrets stored in the vaults can be used at the following places of the Administration Console:
- Obtain the SMTP Mail server Password
Obtain the SMTP Mail server Password
- Obtain the LDAP Bind Credential when using LDAP-based User Federation
Obtain the LDAP Bind Credential when using LDAP-based User Federation
- Obtain the OIDC identity providers Client Secret when integrating external identity providers
Obtain the OIDC identity providers Client Secret when integrating external identity providers

## Enabling a vault

For enabling the file-based vault you need to build Keycloak first using the following build option:
Analogically, for the Java KeyStore-based you need to specify the following build option:

## Configuring the file-based vault

### Setting the base directory to lookup secrets

Kubernetes/OpenShift secrets are basically mounted files. To configure a directory where these files should be mounted, enter this command:

### Realm-specific secret files

Kubernetes/OpenShift Secrets are used on a per-realm basis in Keycloak, which requires a naming convention for the file in place:

## Configuring the Java KeyStore-based vault

In order to use the Java KeyStore-based vault, you need to create a KeyStore file first. You can use the following command for doing so:
and then enter a value you want to store in the vault. Note that the format of the -alias parameter depends on the key resolver used. The default key resolver is REALM_UNDERSCORE_KEY .
This by default results to storing the value in a form of generic PBEKey (password based encryption) within SecretKeyEntry.
You can then start Keycloak using the following runtime options:
Note that the --vault-type parameter is optional and defaults to PKCS12 .
Secrets stored in the vault can then be accessed in a realm via the following placeholder (assuming using the REALM_UNDERSCORE_KEY key resolver): ${vault.realm-name_alias} .

## Using underscores in the secret names

To process the secret correctly, you double all underscores in the <secretname>. When REALM_UNDERSCORE_KEY key resolver is used, underscores in <realmname> are also doubled and <secretname> and <realmname> is separated by a single underscore.
- Realm Name: sso_realm
Realm Name: sso_realm
- Desired Name: ldap_credential
Desired Name: ldap_credential
- Resulting file name:
Resulting file name:
Note the doubled underscores between sso and realm and also between ldap and credential .
To learn more about key resolvers, see Key resolvers section in the Server Administration guide .

## Example: Use an LDAP bind credential secret in the Admin Console

- A realm named secrettest
A realm named secrettest
- A desired Name ldapBc for the bind Credential
A desired Name ldapBc for the bind Credential
- Resulting file name: secrettest_ldapBc
Resulting file name: secrettest_ldapBc
You can then use this secret from the Admin Console by using ${vault.ldapBc} as the value for the Bind Credential when configuring your LDAP User federation.

## Relevant options

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

---
Quelle: https://www.keycloak.org/server/vault
# Avoiding downtime with rolling updates - Keycloak

# Avoiding downtime with rolling updates

By default, the Keycloak Operator will perform rolling updates on configuration changes without downtime, and recreate updates with downtime when the image name or tag changes.
This guide describes how to minimize downtimes by configuring the Keycloak Operator to perform rolling updates of Keycloak automatically where possible, and how to override automatic detection for rolling updates.
Use it, for example, to avoid downtimes when rolling out an update to a theme, provider or build time configuration in a custom or optimized image.

## Supported Update Strategies

The Operator supports the following update strategies:
Update the StatefulSet in a rolling fashion, avoiding a downtime when at least two replicas are running.
Scale down the StatefulSet before applying updates, causing temporary downtime.

## Configuring the Update Strategy

Specify the update strategy within the spec section of the Keycloak CR YAML definition:
Set the desired update strategy here.
Revision value for Explicit strategy.
Ignored by the other strategies.
Description
RecreateOnImageChange (default)
RecreateOnImageChange (default)
On image name or tag change
On image name or tag change
Mimics Keycloak 26.1 or older behavior.
When the image field changes, the Operator scales down the StatefulSet before applying the new image.
Mimics Keycloak 26.1 or older behavior.
When the image field changes, the Operator scales down the StatefulSet before applying the new image.
On incompatible changes
On incompatible changes
The Keycloak Operator detects if a rolling or recreate update is possible. In the current version, Keycloak performs a rolling update if the Keycloak version is the same for the old and the new image.
Future versions of Keycloak will change that behavior and use additional information from the configuration, the image and the version to determine if a rolling update is possible to reduce downtimes.
The Keycloak Operator detects if a rolling or recreate update is possible.
In the current version, Keycloak performs a rolling update if the Keycloak version is the same for the old and the new image.
Future versions of Keycloak will change that behavior and use additional information from the configuration, the image and the version to determine if a rolling update is possible to reduce downtimes.
Only the revision field changes
Only the revision field changes
The Keycloak Operator checks the spec.update.revision value.
If it matches the previous deployment, it performs a rolling update.
The Keycloak Operator checks the spec.update.revision value.
If it matches the previous deployment, it performs a rolling update.

### Understanding Auto and Explicit Update Strategies

When using the Auto update strategy, the Keycloak Operator automatically starts a Job to assess the feasibility of a rolling update.
Read more about the process in the Checking if rolling updates are possible guide.
This process consumes cluster resources for the time of the check and introduces a slight delay before the StatefulSet update begins.
If the Keycloak CR configured a podTemplate as part of the unsupported configuration parameters, the Keycloak Operator will do its best to use those settings for the started Job. Still it might miss some settings due to the flexibility of the podTemplate feature and its unsupported nature. As a consequence, the Operator might draw the wrong conclusions if a rolling update is possible from changes to the podTemplate or information pulled in from Secrets, ConfigMaps or Volumes in the podTemplate . Therefore, if you are using the unsupported podTemplate , you may need to use one of the other update strategies.
If the Keycloak CR configured a podTemplate as part of the unsupported configuration parameters, the Keycloak Operator will do its best to use those settings for the started Job. Still it might miss some settings due to the flexibility of the podTemplate feature and its unsupported nature.
As a consequence, the Operator might draw the wrong conclusions if a rolling update is possible from changes to the podTemplate or information pulled in from Secrets, ConfigMaps or Volumes in the podTemplate .
Therefore, if you are using the unsupported podTemplate , you may need to use one of the other update strategies.
The Explicit update strategy delegates the update decision to the user.
The revision field acts as a user-controlled trigger.
While the Keycloak Operator does not interpret the revision value itself, any change to the Custom Resource (CR) while the revision remains unchanged will prompt a rolling update.
Exercise caution when using this with automatic Operator upgrades.
The Operator Lifecycle Manager (OLM) may upgrade the Keycloak Operator, and if the Explicit update strategy is in use, this could lead to unexpected behavior or deployment failures as the Operator would attempt a rolling update when this is actually not supported. If you are using the Explicit update strategy, thorough testing in a non-production environment is highly recommended before upgrading.

### CR Statuses

The Keycloak CR status of RecreateUpdateUsed indicates the update strategy employed during the last update operation.
The lastTransitionTime field indicates when the last update occurred.
Use this information to observe actions and decisions taken by the Operator.
Description
The initial state.
It means no update has taken place.
The initial state.
It means no update has taken place.
The Operator applied the rolling update strategy in the last update.
The Operator applied the rolling update strategy in the last update.
The Operator applied the recreate update strategy in the last update.
The message field explains why this strategy was chosen.
The Operator applied the recreate update strategy in the last update.
The message field explains why this strategy was chosen.

## Rolling updates for patch releases

This behavior is currently in an experimental mode, and it is not recommended for use in production.
It is possible to enable automatic rolling updates when upgrading to a newer patch version in the same major.minor release stream.
To enable this behavior, enable feature rolling-updates:v2 as shown in the following example:
Read more about rolling updates for patch releases in the Checking if rolling updates are possible guide.

---
Quelle: https://www.keycloak.org/operator/rolling-updates
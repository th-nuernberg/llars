# Troubleshooting using metrics - Keycloak

# Troubleshooting using metrics

For a running Keycloak deployment it is important to understand how the system performs and whether it meets your service level objectives (SLOs).
For more details on SLOs, proceed to the Monitoring performance with Service Level Indicators guide.
This guide will provide directions to answer the question: “What can I do when my SLOs are not met?”
Keycloak consists of several components where an issue or misconfiguration of one of them can move your service level indicators to undesirable numbers.
A guidance provided by this guide is illustrated in the following example:
Observation: Latency service level objective is not met.
Metrics that indicate a problem :
- Keycloak’s database connection pool is often exhausted, and there are threads queuing for a connection to be retrieved from the pool.
Keycloak’s database connection pool is often exhausted, and there are threads queuing for a connection to be retrieved from the pool.
- Keycloak’s users cache hit ratio is at a low percentage, around 5%. This means only 1 out of 20 user searches is able to obtain user data from the cache and the rest needs to load it from the database.
Keycloak’s users cache hit ratio is at a low percentage, around 5%. This means only 1 out of 20 user searches is able to obtain user data from the cache and the rest needs to load it from the database.
Possible mitigations suggested:
- Increasing the users cache size to a higher number which would decrease the number of reads from the database.
Increasing the users cache size to a higher number which would decrease the number of reads from the database.
- Increasing the number of connections in the connection pool. This would need to be checked with metrics for your database and tuning it for a higher load, for example, by increasing the number of available processors.
Increasing the number of connections in the connection pool. This would need to be checked with metrics for your database and tuning it for a higher load, for example, by increasing the number of available processors.
This guide focuses on Keycloak metrics.
Troubleshooting the database itself is out of scope. This guide provides general guidance.
You should always confirm the configuration change by conducting a performance test comparing the metrics in question for the old and the new configuration.
- This guide focuses on Keycloak metrics.
Troubleshooting the database itself is out of scope.
This guide focuses on Keycloak metrics.
Troubleshooting the database itself is out of scope.
- This guide provides general guidance.
You should always confirm the configuration change by conducting a performance test comparing the metrics in question for the old and the new configuration.
This guide provides general guidance.
You should always confirm the configuration change by conducting a performance test comparing the metrics in question for the old and the new configuration.
Grafana dashboards for the metrics below can be found in Visualizing activities in dashboards guide.
Grafana dashboards for the metrics below can be found in Visualizing activities in dashboards guide.

## List of Keycloak key metrics

- Self-provided metrics
Self-provided metrics
- JVM metrics
JVM metrics
- Database Metrics
Database Metrics
- HTTP metrics
HTTP metrics
- Local caching metrics
Local caching metrics
- Single-cluster deployments metrics Clustering metrics Embedded Infinispan metrics for single-cluster deployments
Single-cluster deployments metrics
- Clustering metrics
Clustering metrics
- Embedded Infinispan metrics for single-cluster deployments
Embedded Infinispan metrics for single-cluster deployments
- Multi-cluster deployments metrics Embedded Infinispan metrics for multi-cluster deployments External Infinispan metrics
Multi-cluster deployments metrics
- Embedded Infinispan metrics for multi-cluster deployments
Embedded Infinispan metrics for multi-cluster deployments
- External Infinispan metrics
External Infinispan metrics

---
Quelle: https://www.keycloak.org/observability/metrics-for-troubleshooting
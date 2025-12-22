# Gaining insights with metrics - Keycloak

# Gaining insights with metrics

Keycloak has built in support for metrics. This guide describes how to enable and configure server metrics.

## Enabling Metrics

It is possible to enable metrics using the build time option metrics-enabled :

## Querying Metrics

Keycloak exposes metrics at the following endpoint on the management interface at:
For more information about the management interface, see Configuring the Management Interface .
The response from the endpoint uses a application/openmetrics-text content type and it is based on the Prometheus (OpenMetrics) text format. The snippet below
is an example of a response:
Read the guides Monitoring performance with Service Level Indicators and Troubleshooting using metrics to see how to use the metrics.

## Relevant options

cache-metrics-histograms-enabled Enable histograms for metrics for the embedded caches. CLI: --cache-metrics-histograms-enabled Env: KC_CACHE_METRICS_HISTOGRAMS_ENABLED Available only when metrics are enabled
cache-metrics-histograms-enabled
Enable histograms for metrics for the embedded caches.
CLI: --cache-metrics-histograms-enabled Env: KC_CACHE_METRICS_HISTOGRAMS_ENABLED
Available only when metrics are enabled
true , false (default)
true , false (default)
http-metrics-histograms-enabled Enables a histogram with default buckets for the duration of HTTP server requests. CLI: --http-metrics-histograms-enabled Env: KC_HTTP_METRICS_HISTOGRAMS_ENABLED Available only when metrics are enabled
http-metrics-histograms-enabled
Enables a histogram with default buckets for the duration of HTTP server requests.
CLI: --http-metrics-histograms-enabled Env: KC_HTTP_METRICS_HISTOGRAMS_ENABLED
Available only when metrics are enabled
true , false (default)
true , false (default)
http-metrics-slos Service level objectives for HTTP server requests. Use this instead of the default histogram, or use it in combination to add additional buckets. Specify a list of comma-separated values defined in milliseconds. Example with buckets from 5ms to 10s: 5,10,25,50,250,500,1000,2500,5000,10000 CLI: --http-metrics-slos Env: KC_HTTP_METRICS_SLOS Available only when metrics are enabled
http-metrics-slos
Service level objectives for HTTP server requests.
Use this instead of the default histogram, or use it in combination to add additional buckets. Specify a list of comma-separated values defined in milliseconds. Example with buckets from 5ms to 10s: 5,10,25,50,250,500,1000,2500,5000,10000
CLI: --http-metrics-slos Env: KC_HTTP_METRICS_SLOS
Available only when metrics are enabled
metrics-enabled If the server should expose metrics. If enabled, metrics are available at the /metrics endpoint. CLI: --metrics-enabled Env: KC_METRICS_ENABLED
metrics-enabled
If the server should expose metrics.
If enabled, metrics are available at the /metrics endpoint.
CLI: --metrics-enabled Env: KC_METRICS_ENABLED
true , false (default)
true , false (default)

---
Quelle: https://www.keycloak.org/observability/configuration-metrics
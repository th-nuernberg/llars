# Configuring logging - Keycloak

# Configuring logging

Keycloak uses the JBoss Logging framework.
The following is a high-level overview for the available log handlers with the common parent log handler root :

## Logging configuration

Logging is done on a per-category basis in Keycloak.
You can configure logging for the root log level or for more specific categories such as org.hibernate or org.keycloak .
It is also possible to tailor log levels for each particular log handler.
This guide describes how to configure logging.
The following table defines the available log levels.
Description
Critical failures with complete inability to serve any kind of request.
Critical failures with complete inability to serve any kind of request.
A significant error or problem leading to the inability to process requests.
A significant error or problem leading to the inability to process requests.
A non-critical error or problem that might not require immediate correction.
A non-critical error or problem that might not require immediate correction.
Keycloak lifecycle events or important information. Low frequency.
Keycloak lifecycle events or important information. Low frequency.
More detailed information for debugging purposes, such as database logs. Higher frequency.
More detailed information for debugging purposes, such as database logs. Higher frequency.
Most detailed debugging information. Very high frequency.
Most detailed debugging information. Very high frequency.
Special level for all log messages.
Special level for all log messages.
Special level to turn logging off entirely (not recommended).
Special level to turn logging off entirely (not recommended).

### Configuring the root log level

When no log level configuration exists for a more specific category logger, the enclosing category is used instead. When there is no enclosing category, the root logger level is used.
To set the root log level, enter the following command:
Use these guidelines for this command:
- For <root-level> , supply a level defined in the preceding table.
For <root-level> , supply a level defined in the preceding table.
- The log level is case-insensitive. For example, you could either use DEBUG or debug .
The log level is case-insensitive. For example, you could either use DEBUG or debug .
- If you were to accidentally set the log level twice, the last occurrence in the list becomes the log level. For example, if you included the syntax --log-level="info,…​,DEBUG,…​" , the root logger would be DEBUG .
If you were to accidentally set the log level twice, the last occurrence in the list becomes the log level. For example, if you included the syntax --log-level="info,…​,DEBUG,…​" , the root logger would be DEBUG .

### Configuring category-specific log levels

You can set different log levels for specific areas in Keycloak. Use this command to provide a comma-separated list of categories for which you want a different log level:
A configuration that applies to a category also applies to its sub-categories unless you include a more specific matching sub-category.
This example sets the following log levels:
- Root log level for all loggers is set to INFO.
Root log level for all loggers is set to INFO.
- The hibernate log level in general is set to debug.
The hibernate log level in general is set to debug.
- To keep SQL abstract syntax trees from creating verbose log output, the specific subcategory org.hibernate.hql.internal.ast is set to info. As a result, the SQL abstract syntax trees are omitted instead of appearing at the debug level.
To keep SQL abstract syntax trees from creating verbose log output, the specific subcategory org.hibernate.hql.internal.ast is set to info. As a result, the SQL abstract syntax trees are omitted instead of appearing at the debug level.

### Adding context for log messages

Log messages with Mapped Diagnostic Context (MDC) is Preview and is not fully supported. This feature is disabled by default.
Log messages with Mapped Diagnostic Context (MDC) is Preview and is not fully supported. This feature is disabled by default.
You can enable additional context information for each log line like the current realm and client that is executing the request.
Use the option log-mdc-enabled to enable it.
Specify which keys to be added by setting the configuration option log-mdc-keys .

### Configuring levels as individual options

When configuring category-specific log levels, you can also set the log levels as individual log-level-<category> options instead of using the log-level option for that.
This is useful when you want to set the log levels for selected categories without overwriting the previously set log-level option.
If you start the server as:
you can then set an environmental variable KC_LOG_LEVEL_ORG_KEYCLOAK=trace to change the log level for the org.keycloak category.
The log-level-<category> options take precedence over log-level . This allows you to override what was set in the log-level option.
For instance if you set KC_LOG_LEVEL_ORG_HIBERNATE=trace for the CLI example above, the org.hibernate category will use the trace level instead of debug .
Bear in mind that when using the environmental variables, the category name must be in uppercase and the dots must be replaced with underscores.
When using other config sources, the category name must be specified "as is", for example:

## Enabling log handlers

To enable log handlers, enter the following command:
The available handlers are:
The more specific handler configuration mentioned below will only take effect when the handler is added to this comma-separated list.

### Specify log level for each handler

The log-level property specifies the global root log level and levels for selected categories.
However, a more fine-grained approach for log levels is necessary to comply with the modern application requirements.
To set log levels for particular handlers, properties in format log-<handler>-level (where <handler> is available log handler) were introduced.
It means properties for log level settings look like this:
- log-console-level - Console log handler
log-console-level - Console log handler
- log-file-level - File log handler
log-file-level - File log handler
- log-syslog-level - Syslog log handler
log-syslog-level - Syslog log handler
The log-<handler>-level properties are available only when the particular log handlers are enabled.
More information in log handlers settings below.
Only log levels specified in Log levels section are accepted, and must be in lowercase .
There is no support for specifying particular categories for log handlers yet.

#### General principle

It is necessary to understand that setting the log levels for each particular handler does not override the root level specified in the log-level property.
Log handlers respect the root log level, which represents the maximal verbosity for the whole logging system.
It means individual log handlers can be configured to be less verbose than the root logger, but not more.
Specifically, when an arbitrary log level is defined for the handler, it does not mean the log records with the log level will be present in the output.
In that case, the root log-level must also be assessed.
Log handler levels provide the restriction for the root log level , and the default log level for log handlers is all - without any restriction.
The root log level is set to debug , so every log handler inherits the value - so does the file log handler.
To hide debug records in the console, we need to set the minimal (least severe) level to info for the console handler.
The root level must be set to the most verbose required level ( debug in this case), and other log handlers must be amended accordingly.
In order to see the org.keycloak.events:trace , the trace level must be set for the Syslog handler.

### Use different JSON format for log handlers

Every log handler provides the ability to have structured log output in JSON format.
It can be enabled by properties in the format log-<handler>-output=json (where <handler> is a log handler).
If you need a different format of the produced JSON, you can leverage the following JSON output formats:
- default (default)
default (default)
The ecs value refers to the ECS (Elastic Common Schema).
ECS is an open-source, community-driven specification that defines a common set of fields to be used with Elastic solutions.
The ECS specification is being converged with OpenTelemetry Semantic Conventions with the goal of creating a single standard maintained by OpenTelemetry.
In order to change the JSON output format, properties in the format log-<handler>-json-format (where <handler> is a log handler) were introduced:
- log-console-json-format - Console log handler
log-console-json-format - Console log handler
- log-file-json-format - File log handler
log-file-json-format - File log handler
- log-syslog-json-format - Syslog log handler
log-syslog-json-format - Syslog log handler
If you want to have JSON logs in ECS (Elastic Common Schema) format for the console log handler, you can enter the following command:

### Asynchronous logging

Keycloak supports asynchronous logging, which might be useful for deployments requiring high throughput and low latency .
Asynchronous logging uses a separate thread to take care of processing all log records.
The logging handlers are invoked in exactly the same way as with synchronous logging, only done in separate threads.
You can enable asynchronous logging for all Keycloak log handlers.
A dedicated thread will be created for every log handler with enabled asynchronous logging.
The underlying mechanism for asynchronous logging uses a queue for processing log records.
Every new log record is added to the queue and then published to the particular log handler with enabled asynchronous logging.
Every log handler has a different queue.
If the queue is already full, it blocks the main thread and waits for free space in the queue.

#### When to use asynchronous logging

- You need lower latencies for incoming requests
You need lower latencies for incoming requests
- You need higher throughput
You need higher throughput
- You have small worker thread pool and want to offload logging to separate threads
You have small worker thread pool and want to offload logging to separate threads
- You want to reduce the impact of I/O-heavy log handlers
You want to reduce the impact of I/O-heavy log handlers
- You are logging to remote destinations (e.g., network syslog servers) and want to avoid blocking worker threads
You are logging to remote destinations (e.g., network syslog servers) and want to avoid blocking worker threads
Be aware that enabling asynchronous logging might bring some additional memory overhead due to the additional separate thread and the inner queue.
In that case, it is not recommended to use it for resource-constrained environments.
Additionally, unexpected server shutdowns create a risk of losing log records .

#### Enable asynchronous logging

You can enable asynchronous logging globally for all log handlers by using log-async property as follows:
Or you can enable the asynchronous logging for every specific handler by using properties in the format log-<handler>-async (where <handler> is a log handler).
If the property for a specific handler is not set, the value from the parent log-async property is used.
You can use these properties as follows:
- log-console-async - Console log handler
log-console-async - Console log handler
- log-file-async - File log handler
log-file-async - File log handler
- log-syslog-async - Syslog log handler
log-syslog-async - Syslog log handler

#### Change queue length

You can change the size of the queue used for the asynchronous logging.
The default size is 512 log records in the queue.
You can change the queue length as follows:
These properties are available only when asynchronous logging is enabled for these specific log handlers.

### HTTP Access Logging

Keycloak supports HTTP access logging to record details of incoming HTTP requests.
While access logs are often used for debugging and traffic analysis, they are also important for security auditing and compliance monitoring, helping administrators track access patterns, identify suspicious activity, and maintain audit trails.
These logs are written at the INFO level, so make sure your logging configuration includes this level — either globally (e.g. log-level=info ) or specifically for the access log category (e.g. log-level=org.keycloak.http.access-log:info ).
When HTTP access logs are enabled, they are shown by default, as INFO level is the default log level for Keycloak.

#### How to enable

You can enable HTTP access logging by using http-access-log-enabled property as follows:

#### Change log format/pattern

You can change format/pattern of the access log records by using http-access-log-pattern property as follows:
Predefined named patterns:
- common (default) - prints basic information about the request
common (default) - prints basic information about the request
- combined - prints basic information about the request + information about referer and user agent
combined - prints basic information about the request + information about referer and user agent
- long - prints comprehensive information about the request with all its headers
long - prints comprehensive information about the request with all its headers
You can even specify your own pattern with your required data to be logged, such as:
Consult the Quarkus documentation for the full list of variables that can be used.

#### Exclude specific URL paths

It is possible to exclude specific URL paths from the HTTP access logging, so they will not be recorded.
You can use regular expressions to exclude them, such as:
In this case, all calls to the /realms/my-internal-realm/ and subsequent paths will be excluded from the HTTP Access log.

## Console log handler

The console log handler is enabled by default, providing unstructured log messages for the console.

### Configuring the console log format

Keycloak uses a pattern-based logging formatter that generates human-readable text logs by default.
The logging format template for these lines can be applied at the root level. The default format template is:
- %d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n
The format string supports the symbols in the following table:
Description
Renders a simple % character.
Renders a simple % character.
Renders the log category name.
Renders the log category name.
Renders a date with the given date format string.String syntax defined by java.text.SimpleDateFormat
Renders a date with the given date format string.String syntax defined by java.text.SimpleDateFormat
Renders a thrown exception.
Renders a thrown exception.
Renders the simple host name.
Renders the simple host name.
Qualified host name
Qualified host name
Renders the fully qualified hostname, which may be the same as the simple host name, depending on the OS configuration.
Renders the fully qualified hostname, which may be the same as the simple host name, depending on the OS configuration.
Renders the current process PID.
Renders the current process PID.
Full Message
Full Message
Renders the log message and an exception, if thrown.
Renders the log message and an exception, if thrown.
Renders the platform-specific line separator string.
Renders the platform-specific line separator string.
Process name
Process name
Renders the name of the current process.
Renders the name of the current process.
Renders the log level of the message.
Renders the log level of the message.
Relative time
Relative time
Render the time in milliseconds since the start of the application log.
Render the time in milliseconds since the start of the application log.
Simple message
Simple message
Renders only the log message without exception trace.
Renders only the log message without exception trace.
Thread name
Thread name
Renders the thread name.
Renders the thread name.
Render the thread ID.
Render the thread ID.
%z{<zone name>}
%z{<zone name>}
Set the time zone of log output to <zone name>.
Set the time zone of log output to <zone name>.
Line number
Line number
Render the line number of the log message.
Render the line number of the log message.

### Setting the logging format

To set the logging format for a logged line, perform these steps:
- Build your desired format template using the preceding table.
Build your desired format template using the preceding table.
- Enter the following command: bin/kc.[sh|bat] start --log-console-format="'<format>'"
Enter the following command:
Note that you need to escape characters when invoking commands containing special shell characters such as ; using the CLI. Therefore, consider setting it in the configuration file instead.
This example abbreviates the category name to three characters by setting [%c{3.}] in the template instead of the default [%c] .

### Configuring JSON or plain console logging

By default, the console log handler logs plain unstructured data to the console. To use structured JSON log output instead, enter the following command:
When using JSON output, colors are disabled and the format settings set by --log-console-format will not apply.
To use unstructured logging, enter the following command:
Colored console log output for unstructured logs is disabled by default. Colors may improve readability, but they can cause problems when shipping logs to external log aggregation systems. To enable or disable color-coded console log output, enter following command:

### Configuring the console log level

Log level for console log handler can be specified by --log-console-level property as follows:
For more information, see the section Specify log level for each handler above.

## File logging

As an alternative to logging to the console, you can use unstructured logging to a file.

### Enable file logging

Logging to a file is disabled by default. To enable it, enter the following command:
A log file named keycloak.log is created inside the data/log directory of your Keycloak installation.

### Configuring the location and name of the log file

To change where the log file is created and the file name, perform these steps:
- Create a writable directory to store the log file. If the directory is not writable, Keycloak will start correctly, but it will issue an error and no log file will be created.
Create a writable directory to store the log file.
If the directory is not writable, Keycloak will start correctly, but it will issue an error and no log file will be created.
- Enter this command: bin/kc.[sh|bat] start --log="console,file" --log-file=<path-to>/<your-file.log>
Enter this command:

### Configuring the file handler format

To configure a different logging format for the file log handler, enter the following command:
See Configuring the console log format for more information and a table of the available pattern configuration.

### Configuring the file log level

Log level for file log handler can be specified by --log-file-level property as follows:
For more information, see the section Specify log level for each handler above.

## Centralized logging using Syslog

Keycloak provides the ability to send logs to a remote Syslog server.
It utilizes the protocol defined in RFC 5424 .

### Enable the Syslog handler

To enable logging using Syslog, add it to the list of activated log handlers as follows:

### Configuring the Syslog Application Name

To set a different application name, add the --log-syslog-app-name option as follows:
If not set, the application name defaults to keycloak .

### Configuring the Syslog endpoint

To configure the endpoint( host:port ) of your centralized logging system, enter the following command and substitute the values with your specific values:
When the Syslog handler is enabled, the host is using localhost as host value.
The Default port is 514 .

### Configuring the Syslog log level

Log level for Syslog log handler can be specified by --log-syslog-level property as follows:
For more information, see the section Specify log level for each handler above.

### Configuring the Syslog protocol

Syslog uses TCP as the default protocol for communication.
To use UDP instead of TCP, add the --log-syslog-protocol option as follows:
The available protocols are: tpc , udp , and ssl-tcp .

### Configuring the Syslog counting framing

By default, Syslog messages sent over TCP or SSL-TCP are prefixed with the message size, as required by certain Syslog receivers.
This behavior is controlled by the --log-syslog-counting-framing option.
To explicitly enable or disable this feature, use the following command:
You can set the value to one of the following:
- protocol-dependent (default) – Enable counting framing only when the log-syslog-protocol is tcp or ssl-tcp .
protocol-dependent (default) – Enable counting framing only when the log-syslog-protocol is tcp or ssl-tcp .
- true – Always enable counting framing by prefixing messages with their size.
true – Always enable counting framing by prefixing messages with their size.
- false – Never use counting framing.
false – Never use counting framing.
Note that using protocol-dependent ensures compatibility with most Syslog servers by enabling the prefix only when required by the protocol.

### Configuring the Syslog log format

To set the logging format for a logged line, perform these steps:
- Build your desired format template using the preceding table.
Build your desired format template using the preceding table.
- Enter the following command: bin/kc.[sh|bat] start --log-syslog-format="'<format>'"
Enter the following command:
Note that you need to escape characters when invoking commands containing special shell characters such as ; using the CLI. Therefore, consider setting it in the configuration file instead.
This example abbreviates the category name to three characters by setting [%c{3.}] in the template instead of the default [%c] .

### Configuring the Syslog type

Syslog uses different message formats based on particular RFC specifications.
To change the Syslog type with a different message format, use the --log-syslog-type option as follows:
Possible values for the --log-syslog-type option are:
- rfc5424 (default)
rfc5424 (default)
The preferred Syslog type is RFC 5424 , which obsoletes RFC 3164 , known as BSD Syslog protocol.

### Configuring the Syslog maximum message length

To set the maximum length of the message allowed to be sent (in bytes), use the --log-syslog-max-length option as follows:
The length can be specified in memory size format with the appropriate suffix, like 1k or 1K .
The length includes the header and the message.
If the length is not explicitly set, the default values are set based on the --log-syslog-type option as follows:
- 2048B - for RFC 5424
2048B - for RFC 5424
- 1024B - for RFC 3164
1024B - for RFC 3164

### Configuring the Syslog structured output

By default, the Syslog log handler sends plain unstructured data to the Syslog server.
To use structured JSON log output instead, enter the following command:
When using JSON output, colors are disabled and the format settings set by --log-syslog-format will not apply.
To use unstructured logging, enter the following command:
As you can see, the timestamp is present twice, so you can amend it correspondingly via the --log-syslog-format property.

## Relevant options

log Enable one or more log handlers in a comma-separated list. CLI: --log Env: KC_LOG
Enable one or more log handlers in a comma-separated list.
CLI: --log Env: KC_LOG
console , file , syslog
console , file , syslog
log-async Indicates whether to log asynchronously to all handlers. CLI: --log-async Env: KC_LOG_ASYNC
Indicates whether to log asynchronously to all handlers.
CLI: --log-async Env: KC_LOG_ASYNC
true , false (default)
true , false (default)
log-level The log level of the root category or a comma-separated list of individual categories and their levels. For the root category, you don’t need to specify a category. CLI: --log-level Env: KC_LOG_LEVEL
The log level of the root category or a comma-separated list of individual categories and their levels.
For the root category, you don’t need to specify a category.
CLI: --log-level Env: KC_LOG_LEVEL
[info] (default)
[info] (default)
log-level-<category> The log level of a category. Takes precedence over the log-level option. CLI: --log-level-<category> Env: KC_LOG_LEVEL_<CATEGORY>
log-level-<category>
The log level of a category.
Takes precedence over the log-level option.
CLI: --log-level-<category> Env: KC_LOG_LEVEL_<CATEGORY>
off , fatal , error , warn , info , debug , trace , all
off , fatal , error , warn , info , debug , trace , all
log-mdc-enabled Indicates whether to add information about the realm and other information to the mapped diagnostic context. All elements will be prefixed with kc. CLI: --log-mdc-enabled Env: KC_LOG_MDC_ENABLED Available only when log-mdc preview feature is enabled
log-mdc-enabled
Indicates whether to add information about the realm and other information to the mapped diagnostic context.
All elements will be prefixed with kc.
CLI: --log-mdc-enabled Env: KC_LOG_MDC_ENABLED
Available only when log-mdc preview feature is enabled
true , false (default)
true , false (default)
log-mdc-keys Defines which information should be added to the mapped diagnostic context as a comma-separated list. CLI: --log-mdc-keys Env: KC_LOG_MDC_KEYS Available only when MDC logging is enabled
log-mdc-keys
Defines which information should be added to the mapped diagnostic context as a comma-separated list.
CLI: --log-mdc-keys Env: KC_LOG_MDC_KEYS
Available only when MDC logging is enabled
realmName , clientId , userId , ipAddress , org , sessionId , authenticationSessionId , authenticationTabId
realmName , clientId , userId , ipAddress , org , sessionId , authenticationSessionId , authenticationTabId
log-console-async Indicates whether to log asynchronously to console. If not set, value from the parent property log-async is used. CLI: --log-console-async Env: KC_LOG_CONSOLE_ASYNC Available only when Console log handler is activated
log-console-async
Indicates whether to log asynchronously to console.
If not set, value from the parent property log-async is used.
CLI: --log-console-async Env: KC_LOG_CONSOLE_ASYNC
Available only when Console log handler is activated
true , false (default)
true , false (default)
log-console-async-queue-length The queue length to use before flushing writing when logging to console. CLI: --log-console-async-queue-length Env: KC_LOG_CONSOLE_ASYNC_QUEUE_LENGTH Available only when Console log handler is activated and asynchronous logging is enabled
log-console-async-queue-length
The queue length to use before flushing writing when logging to console.
CLI: --log-console-async-queue-length Env: KC_LOG_CONSOLE_ASYNC_QUEUE_LENGTH
Available only when Console log handler is activated and asynchronous logging is enabled
512 (default)
512 (default)
log-console-color Enable or disable colors when logging to console. CLI: --log-console-color Env: KC_LOG_CONSOLE_COLOR Available only when Console log handler is activated
log-console-color
Enable or disable colors when logging to console.
CLI: --log-console-color Env: KC_LOG_CONSOLE_COLOR
Available only when Console log handler is activated
true , false (default)
true , false (default)
log-console-format The format of unstructured console log entries. If the format has spaces in it, escape the value using "<format>". CLI: --log-console-format Env: KC_LOG_CONSOLE_FORMAT Available only when Console log handler is activated
log-console-format
The format of unstructured console log entries.
If the format has spaces in it, escape the value using "<format>".
CLI: --log-console-format Env: KC_LOG_CONSOLE_FORMAT
Available only when Console log handler is activated
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
log-console-include-mdc Include mdc information in the console log. If the log-console-format option is specified, this option has no effect. CLI: --log-console-include-mdc Env: KC_LOG_CONSOLE_INCLUDE_MDC Available only when Console log handler and MDC logging are activated
log-console-include-mdc
Include mdc information in the console log.
If the log-console-format option is specified, this option has no effect.
CLI: --log-console-include-mdc Env: KC_LOG_CONSOLE_INCLUDE_MDC
Available only when Console log handler and MDC logging are activated
true (default), false
true (default), false
log-console-include-trace Include tracing information in the console log. If the log-console-format option is specified, this option has no effect. CLI: --log-console-include-trace Env: KC_LOG_CONSOLE_INCLUDE_TRACE Available only when Console log handler and Tracing is activated
log-console-include-trace
Include tracing information in the console log.
If the log-console-format option is specified, this option has no effect.
CLI: --log-console-include-trace Env: KC_LOG_CONSOLE_INCLUDE_TRACE
Available only when Console log handler and Tracing is activated
true (default), false
true (default), false
log-console-json-format Set the format of the produced JSON. CLI: --log-console-json-format Env: KC_LOG_CONSOLE_JSON_FORMAT Available only when Console log handler is activated and output is set to 'json'
log-console-json-format
Set the format of the produced JSON.
CLI: --log-console-json-format Env: KC_LOG_CONSOLE_JSON_FORMAT
Available only when Console log handler is activated and output is set to 'json'
default (default), ecs
default (default), ecs
log-console-level Set the log level for the console handler. It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide. CLI: --log-console-level Env: KC_LOG_CONSOLE_LEVEL Available only when Console log handler is activated
log-console-level
Set the log level for the console handler.
It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide.
CLI: --log-console-level Env: KC_LOG_CONSOLE_LEVEL
Available only when Console log handler is activated
off , fatal , error , warn , info , debug , trace , all (default)
off , fatal , error , warn , info , debug , trace , all (default)
log-console-output Set the log output to JSON or default (plain) unstructured logging. CLI: --log-console-output Env: KC_LOG_CONSOLE_OUTPUT Available only when Console log handler is activated
log-console-output
Set the log output to JSON or default (plain) unstructured logging.
CLI: --log-console-output Env: KC_LOG_CONSOLE_OUTPUT
Available only when Console log handler is activated
default (default), json
default (default), json
log-file Set the log file path and filename. CLI: --log-file Env: KC_LOG_FILE Available only when File log handler is activated
Set the log file path and filename.
CLI: --log-file Env: KC_LOG_FILE
Available only when File log handler is activated
data/log/keycloak.log (default)
data/log/keycloak.log (default)
log-file-async Indicates whether to log asynchronously to file log. If not set, value from the parent property log-async is used. CLI: --log-file-async Env: KC_LOG_FILE_ASYNC Available only when File log handler is activated
log-file-async
Indicates whether to log asynchronously to file log.
If not set, value from the parent property log-async is used.
CLI: --log-file-async Env: KC_LOG_FILE_ASYNC
Available only when File log handler is activated
true , false (default)
true , false (default)
log-file-async-queue-length The queue length to use before flushing writing when logging to file log. CLI: --log-file-async-queue-length Env: KC_LOG_FILE_ASYNC_QUEUE_LENGTH Available only when File log handler is activated and asynchronous logging is enabled
log-file-async-queue-length
The queue length to use before flushing writing when logging to file log.
CLI: --log-file-async-queue-length Env: KC_LOG_FILE_ASYNC_QUEUE_LENGTH
Available only when File log handler is activated and asynchronous logging is enabled
512 (default)
512 (default)
log-file-format Set a format specific to file log entries. CLI: --log-file-format Env: KC_LOG_FILE_FORMAT Available only when File log handler is activated
log-file-format
Set a format specific to file log entries.
CLI: --log-file-format Env: KC_LOG_FILE_FORMAT
Available only when File log handler is activated
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
log-file-include-mdc Include MDC information in the file log. If the log-file-format option is specified, this option has no effect. CLI: --log-file-include-mdc Env: KC_LOG_FILE_INCLUDE_MDC Available only when File log handler and MDC logging are activated
log-file-include-mdc
Include MDC information in the file log.
If the log-file-format option is specified, this option has no effect.
CLI: --log-file-include-mdc Env: KC_LOG_FILE_INCLUDE_MDC
Available only when File log handler and MDC logging are activated
true (default), false
true (default), false
log-file-include-trace Include tracing information in the file log. If the log-file-format option is specified, this option has no effect. CLI: --log-file-include-trace Env: KC_LOG_FILE_INCLUDE_TRACE Available only when File log handler and Tracing is activated
log-file-include-trace
Include tracing information in the file log.
If the log-file-format option is specified, this option has no effect.
CLI: --log-file-include-trace Env: KC_LOG_FILE_INCLUDE_TRACE
Available only when File log handler and Tracing is activated
true (default), false
true (default), false
log-file-json-format Set the format of the produced JSON. CLI: --log-file-json-format Env: KC_LOG_FILE_JSON_FORMAT Available only when File log handler is activated and output is set to 'json'
log-file-json-format
Set the format of the produced JSON.
CLI: --log-file-json-format Env: KC_LOG_FILE_JSON_FORMAT
Available only when File log handler is activated and output is set to 'json'
default (default), ecs
default (default), ecs
log-file-level Set the log level for the file handler. It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide. CLI: --log-file-level Env: KC_LOG_FILE_LEVEL Available only when File log handler is activated
log-file-level
Set the log level for the file handler.
It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide.
CLI: --log-file-level Env: KC_LOG_FILE_LEVEL
Available only when File log handler is activated
off , fatal , error , warn , info , debug , trace , all (default)
off , fatal , error , warn , info , debug , trace , all (default)
log-file-output Set the log output to JSON or default (plain) unstructured logging. CLI: --log-file-output Env: KC_LOG_FILE_OUTPUT Available only when File log handler is activated
log-file-output
Set the log output to JSON or default (plain) unstructured logging.
CLI: --log-file-output Env: KC_LOG_FILE_OUTPUT
Available only when File log handler is activated
default (default), json
default (default), json
log-syslog-app-name Set the app name used when formatting the message in RFC5424 format. CLI: --log-syslog-app-name Env: KC_LOG_SYSLOG_APP_NAME Available only when Syslog is activated
log-syslog-app-name
Set the app name used when formatting the message in RFC5424 format.
CLI: --log-syslog-app-name Env: KC_LOG_SYSLOG_APP_NAME
Available only when Syslog is activated
keycloak (default)
keycloak (default)
log-syslog-async Indicates whether to log asynchronously to Syslog. If not set, value from the parent property log-async is used. CLI: --log-syslog-async Env: KC_LOG_SYSLOG_ASYNC Available only when Syslog is activated
log-syslog-async
Indicates whether to log asynchronously to Syslog.
If not set, value from the parent property log-async is used.
CLI: --log-syslog-async Env: KC_LOG_SYSLOG_ASYNC
Available only when Syslog is activated
true , false (default)
true , false (default)
log-syslog-async-queue-length The queue length to use before flushing writing when logging to Syslog. CLI: --log-syslog-async-queue-length Env: KC_LOG_SYSLOG_ASYNC_QUEUE_LENGTH Available only when Syslog is activated and asynchronous logging is enabled
log-syslog-async-queue-length
The queue length to use before flushing writing when logging to Syslog.
CLI: --log-syslog-async-queue-length Env: KC_LOG_SYSLOG_ASYNC_QUEUE_LENGTH
Available only when Syslog is activated and asynchronous logging is enabled
512 (default)
512 (default)
log-syslog-counting-framing If true , the message being sent is prefixed with the size of the message. If protocol-dependent , the default value is true when log-syslog-protocol is tcp or ssl-tcp , otherwise false . CLI: --log-syslog-counting-framing Env: KC_LOG_SYSLOG_COUNTING_FRAMING Available only when Syslog is activated
log-syslog-counting-framing
If true , the message being sent is prefixed with the size of the message.
If protocol-dependent , the default value is true when log-syslog-protocol is tcp or ssl-tcp , otherwise false .
CLI: --log-syslog-counting-framing Env: KC_LOG_SYSLOG_COUNTING_FRAMING
Available only when Syslog is activated
true , false , protocol-dependent (default)
true , false , protocol-dependent (default)
log-syslog-endpoint Set the IP address and port of the Syslog server. CLI: --log-syslog-endpoint Env: KC_LOG_SYSLOG_ENDPOINT Available only when Syslog is activated
log-syslog-endpoint
Set the IP address and port of the Syslog server.
CLI: --log-syslog-endpoint Env: KC_LOG_SYSLOG_ENDPOINT
Available only when Syslog is activated
localhost:514 (default)
localhost:514 (default)
log-syslog-format Set a format specific to Syslog entries. CLI: --log-syslog-format Env: KC_LOG_SYSLOG_FORMAT Available only when Syslog is activated
log-syslog-format
Set a format specific to Syslog entries.
CLI: --log-syslog-format Env: KC_LOG_SYSLOG_FORMAT
Available only when Syslog is activated
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n (default)
log-syslog-include-mdc Include MDC information in the Syslog. If the log-syslog-format option is specified, this option has no effect. CLI: --log-syslog-include-mdc Env: KC_LOG_SYSLOG_INCLUDE_MDC Available only when Syslog handler and MDC logging are activated
log-syslog-include-mdc
Include MDC information in the Syslog.
If the log-syslog-format option is specified, this option has no effect.
CLI: --log-syslog-include-mdc Env: KC_LOG_SYSLOG_INCLUDE_MDC
Available only when Syslog handler and MDC logging are activated
true (default), false
true (default), false
log-syslog-include-trace Include tracing information in the Syslog. If the log-syslog-format option is specified, this option has no effect. CLI: --log-syslog-include-trace Env: KC_LOG_SYSLOG_INCLUDE_TRACE Available only when Syslog handler and Tracing is activated
log-syslog-include-trace
Include tracing information in the Syslog.
If the log-syslog-format option is specified, this option has no effect.
CLI: --log-syslog-include-trace Env: KC_LOG_SYSLOG_INCLUDE_TRACE
Available only when Syslog handler and Tracing is activated
true (default), false
true (default), false
log-syslog-json-format Set the format of the produced JSON. CLI: --log-syslog-json-format Env: KC_LOG_SYSLOG_JSON_FORMAT Available only when Syslog is activated and output is set to 'json'
log-syslog-json-format
Set the format of the produced JSON.
CLI: --log-syslog-json-format Env: KC_LOG_SYSLOG_JSON_FORMAT
Available only when Syslog is activated and output is set to 'json'
default (default), ecs
default (default), ecs
log-syslog-level Set the log level for the Syslog handler. It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide. CLI: --log-syslog-level Env: KC_LOG_SYSLOG_LEVEL Available only when Syslog is activated
log-syslog-level
Set the log level for the Syslog handler.
It specifies the most verbose log level for logs shown in the output. It respects levels specified in the log-level option, which represents the maximal verbosity for the whole logging system. For more information, check the Logging guide.
CLI: --log-syslog-level Env: KC_LOG_SYSLOG_LEVEL
Available only when Syslog is activated
off , fatal , error , warn , info , debug , trace , all (default)
off , fatal , error , warn , info , debug , trace , all (default)
log-syslog-max-length Set the maximum length, in bytes, of the message allowed to be sent. The length includes the header and the message. If not set, the default value is 2048 when log-syslog-type is rfc5424 (default) and 1024 when log-syslog-type is rfc3164. CLI: --log-syslog-max-length Env: KC_LOG_SYSLOG_MAX_LENGTH Available only when Syslog is activated
log-syslog-max-length
Set the maximum length, in bytes, of the message allowed to be sent.
The length includes the header and the message. If not set, the default value is 2048 when log-syslog-type is rfc5424 (default) and 1024 when log-syslog-type is rfc3164.
CLI: --log-syslog-max-length Env: KC_LOG_SYSLOG_MAX_LENGTH
Available only when Syslog is activated
log-syslog-output Set the Syslog output to JSON or default (plain) unstructured logging. CLI: --log-syslog-output Env: KC_LOG_SYSLOG_OUTPUT Available only when Syslog is activated
log-syslog-output
Set the Syslog output to JSON or default (plain) unstructured logging.
CLI: --log-syslog-output Env: KC_LOG_SYSLOG_OUTPUT
Available only when Syslog is activated
default (default), json
default (default), json
log-syslog-protocol Set the protocol used to connect to the Syslog server. CLI: --log-syslog-protocol Env: KC_LOG_SYSLOG_PROTOCOL Available only when Syslog is activated
log-syslog-protocol
Set the protocol used to connect to the Syslog server.
CLI: --log-syslog-protocol Env: KC_LOG_SYSLOG_PROTOCOL
Available only when Syslog is activated
tcp (default), udp , ssl-tcp
tcp (default), udp , ssl-tcp
log-syslog-type Set the Syslog type used to format the sent message. CLI: --log-syslog-type Env: KC_LOG_SYSLOG_TYPE Available only when Syslog is activated
log-syslog-type
Set the Syslog type used to format the sent message.
CLI: --log-syslog-type Env: KC_LOG_SYSLOG_TYPE
Available only when Syslog is activated
rfc5424 (default), rfc3164
rfc5424 (default), rfc3164

### HTTP Access log

http-access-log-enabled If HTTP access logging is enabled. By default this will log records in console. CLI: --http-access-log-enabled Env: KC_HTTP_ACCESS_LOG_ENABLED
http-access-log-enabled
If HTTP access logging is enabled.
By default this will log records in console.
CLI: --http-access-log-enabled Env: KC_HTTP_ACCESS_LOG_ENABLED
true , false (default)
true , false (default)
http-access-log-exclude A regular expression that can be used to exclude some paths from logging. For instance, /realms/my-realm/.* will exclude all subsequent endpoints for realm my-realm from the log. CLI: --http-access-log-exclude Env: KC_HTTP_ACCESS_LOG_EXCLUDE Available only when HTTP Access log is enabled
http-access-log-exclude
A regular expression that can be used to exclude some paths from logging.
For instance, /realms/my-realm/.* will exclude all subsequent endpoints for realm my-realm from the log.
CLI: --http-access-log-exclude Env: KC_HTTP_ACCESS_LOG_EXCLUDE
Available only when HTTP Access log is enabled
http-access-log-pattern The HTTP access log pattern. You can use the available named formats, or use custom format described in Quarkus documentation. CLI: --http-access-log-pattern Env: KC_HTTP_ACCESS_LOG_PATTERN Available only when HTTP Access log is enabled
http-access-log-pattern
The HTTP access log pattern.
You can use the available named formats, or use custom format described in Quarkus documentation.
CLI: --http-access-log-pattern Env: KC_HTTP_ACCESS_LOG_PATTERN
Available only when HTTP Access log is enabled
common (default), combined , long , or any
common (default), combined , long , or any

---
Quelle: https://www.keycloak.org/server/logging
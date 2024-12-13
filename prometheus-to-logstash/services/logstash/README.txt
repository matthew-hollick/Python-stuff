Usage:
    bin/logstash [OPTIONS]

Options:
    -n, --node.name NAME          Specify the name of this logstash instance, if no value is given
                                  it will default to the current hostname.
                                   (default: "nixos")
    --enable-local-plugin-development Allow Gemfile to be manipulated directly
                                  to facilitate simpler local plugin
                                  development.
                                  This is an advanced setting, intended
                                  only for use by Logstash developers,
                                  and should not be used in production.
                                   (default: false)
    -f, --path.config CONFIG_PATH Load the logstash config from a specific file
                                  or directory.  If a directory is given, all
                                  files in that directory will be concatenated
                                  in lexicographical order and then parsed as a
                                  single config file. You can also specify
                                  wildcards (globs) and any matched files will
                                  be loaded in the order described above.
    -e, --config.string CONFIG_STRING Use the given string as the configuration
                                  data. Same syntax as the config file. If no
                                  input is specified, then the following is
                                  used as the default input:
                                  "input { stdin { type => stdin } }"
                                  and if no output is specified, then the
                                  following is used as the default output:
                                  "output { stdout { codec => rubydebug } }"
                                  If you wish to use both defaults, please use
                                  the empty string for the '-e' flag.
                                   (default: nil)
    --field-reference-parser MODE (DEPRECATED) This option is no longer
                                  configurable.

                                  Use the given MODE when parsing field
                                  references.

                                  The field reference parser is used to expand
                                  field references in your pipeline configs,
                                  and has become more strict to better handle
                                  ambiguous- and illegal-syntax inputs.

                                  The only available MODE is:
                                   - `STRICT`: parse in a strict manner; when
                                     given ambiguous- or illegal-syntax input,
                                     raises a runtime exception that should
                                     be handled by the calling plugin.

                                   (default: "STRICT")
    --modules MODULES             Load Logstash modules.
                                  Modules can be defined using multiple instances
                                  '--modules module1 --modules module2',
                                     or comma-separated syntax
                                  '--modules=module1,module2'
                                  Cannot be used in conjunction with '-e' or '-f'
                                  Use of '--modules' will override modules declared
                                  in the 'logstash.yml' file.
    -M, --modules.variable MODULES_VARIABLE Load variables for module template.
                                  Multiple instances of '-M' or
                                  '--modules.variable' are supported.
                                  Ignored if '--modules' flag is not used.
                                  Should be in the format of
                                  '-M "MODULE_NAME.var.PLUGIN_TYPE.PLUGIN_NAME.VARIABLE_NAME=VALUE"'
                                  as in
                                  '-M "example.var.filter.mutate.fieldname=fieldvalue"'
    --setup                       Load index template into Elasticsearch, and saved searches,
                                  index-pattern, visualizations, and dashboards into Kibana when
                                  running modules.
                                   (default: false)
    --cloud.id CLOUD_ID           Sets the elasticsearch and kibana host settings for
                                  module connections in Elastic Cloud.
                                  Your Elastic Cloud User interface or the Cloud support
                                  team should provide this.
                                  Add an optional label prefix '<label>:' to help you
                                  identify multiple cloud.ids.
                                  e.g. 'staging:dXMtZWFzdC0xLmF3cy5mb3VuZC5pbyRub3RhcmVhbCRpZGVudGlmaWVy'
    --cloud.auth CLOUD_AUTH       Sets the elasticsearch and kibana username and password
                                  for module connections in Elastic Cloud
                                  e.g. 'username:<password>'
    --pipeline.id ID              Sets the ID of the pipeline.
                                   (default: "main")
    -w, --pipeline.workers COUNT  Sets the number of pipeline workers to run.
                                   (default: 4)
    --pipeline.ordered ORDERED    Preserve events order. Possible values are `auto` (default), `true` and `false`.
                                  This setting
                                  will only work when also using a single worker for the pipeline.
                                  Note that when enabled, it may impact the performance of the filters
                                  and ouput processing.
                                  The `auto` option will automatically enable ordering if the
                                  `pipeline.workers` setting is set to `1`.
                                  Use `true` to enable ordering on the pipeline and prevent logstash
                                  from starting if there are multiple workers.
                                  Use `false` to disable any extra processing necessary for preserving
                                  ordering.
                                   (default: "auto")
    --java-execution              Use Java execution engine.
                                   (default: true)
    --plugin-classloaders         (Beta) Load Java plugins in independent classloaders to isolate their dependencies.
                                   (default: false)
    -b, --pipeline.batch.size SIZE Size of batches the pipeline is to work in.
                                   (default: 125)
    -u, --pipeline.batch.delay DELAY_IN_MS When creating pipeline batches, how long to wait while polling
                                  for the next event.
                                   (default: 50)
    --pipeline.unsafe_shutdown    Force logstash to exit during shutdown even
                                  if there are still inflight events in memory.
                                  By default, logstash will refuse to quit until all
                                  received events have been pushed to the outputs.
                                   (default: false)
    --pipeline.ecs_compatibility STRING Sets the pipeline's default value for `ecs_compatibility`,
                                  a setting that is available to plugins that implement
                                  an ECS Compatibility mode for use with the Elastic Common
                                  Schema.
                                  Possible values are:
                                   - disabled (default)
                                   - v1
                                   - v2
                                  This option allows the early opt-in (or preemptive opt-out)
                                  of ECS Compatibility modes in plugins, which is scheduled to
                                  be on-by-default in a future major release of Logstash.

                                  Values other than `disabled` are currently considered BETA,
                                  and may produce unintended consequences when upgrading Logstash.
                                   (default: "disabled")
    --path.data PATH              This should point to a writable directory. Logstash
                                  will use this directory whenever it needs to store
                                  data. Plugins will also have access to this path.
                                   (default: "/nix/store/kwm289q6zn0zhqxfl55j0qza3dni3aqx-logstash-7.17.16/data")
    -p, --path.plugins PATH       A path of where to find plugins. This flag
                                  can be given multiple times to include
                                  multiple paths. Plugins are expected to be
                                  in a specific directory hierarchy:
                                  'PATH/logstash/TYPE/NAME.rb' where TYPE is
                                  'inputs' 'filters', 'outputs' or 'codecs'
                                  and NAME is the name of the plugin.
                                   (default: [])
    -l, --path.logs PATH          Write logstash internal logs to the given
                                  file. Without this flag, logstash will emit
                                  logs to standard output.
                                   (default: "/nix/store/kwm289q6zn0zhqxfl55j0qza3dni3aqx-logstash-7.17.16/logs")
    --log.level LEVEL             Set the log level for logstash. Possible values are:
                                    - fatal
                                    - error
                                    - warn
                                    - info
                                    - debug
                                    - trace
                                   (default: "info")
    --config.debug                Print the compiled config ruby code out as a debug log (you must also have --log.level=debug enabled).
                                  WARNING: This will include any 'password' options passed to plugin configs as plaintext, and may result
                                  in plaintext passwords appearing in your logs!
                                   (default: false)
    -i, --interactive SHELL       Drop to shell instead of running as normal.
                                  Valid shells are "irb" and "pry"
    -V, --version                 Emit the version of logstash and its friends,
                                  then exit.
    -t, --config.test_and_exit    Check configuration for valid syntax and then exit.
                                   (default: false)
    -r, --config.reload.automatic Monitor configuration changes and reload
                                  whenever it is changed.
                                  NOTE: use SIGHUP to manually reload the config
                                   (default: false)
    --config.reload.interval RELOAD_INTERVAL How frequently to poll the configuration location
                                  for changes, in seconds.
                                   (default: #<Java::OrgLogstashUtil::TimeValue:0xf75843e>)
    --api.enabled ENABLED         Can be used to disable the Web API, which is
                                  enabled by default.
                                   (default: true)
    --api.http.host HTTP_HOST     Web API binding host (default: "127.0.0.1")
    --api.http.port HTTP_PORT     Web API http port (default: 9600..9700)
    --log.format FORMAT           Specify if Logstash should write its own logs in JSON form (one
                                  event per line) or in plain text (using Ruby's Object#inspect)
                                   (default: "plain")
    --path.settings SETTINGS_DIR  Directory containing logstash.yml file. This can also be
                                  set through the LS_SETTINGS_DIR environment variable.
                                   (default: "/nix/store/kwm289q6zn0zhqxfl55j0qza3dni3aqx-logstash-7.17.16/config")
    --verbose                     Set the log level to info.
                                  DEPRECATED: use --log.level=info instead.
    --debug                       Set the log level to debug.
                                  DEPRECATED: use --log.level=debug instead.
    --quiet                       Set the log level to info.
                                  DEPRECATED: use --log.level=info instead.
    --http.enabled                Can be used to disable the Web API, which is
                                  enabled by default.
                                  DEPRECATED: use `--api.enabled=false`
    --http.host HTTP_HOST         Web API binding host
                                  DEPRECATED: use `--api.http.host=IP`
    --http.port HTTP_PORT         Web API http port
                                  DEPRECATED: use `--api.http.port=PORT`
    -h, --help                    print help

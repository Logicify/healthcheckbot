# Healthcheck Bot

[![Build Status](https://travis-ci.org/Logicify/healthcheckbot.svg?branch=master)](https://travis-ci.org/Logicify/healthcheckbot)
![License](https://img.shields.io/github/license/logicify/healthcheckbot.svg)
![PyPi](https://img.shields.io/pypi/v/healthcheckbot.svg)
![Last Commit](https://img.shields.io/github/last-commit/logicify/healthcheckbot.svg)
[![Requirements Status](https://requires.io/github/Logicify/healthcheckbot/requirements.svg?branch=master)](https://requires.io/github/Logicify/healthcheckbot/requirements/?branch=master)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FLogicify%2Fhealthcheckbot.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2FLogicify%2Fhealthcheckbot?ref=badge_shield)



Healthcheck Bot is a standalone, highly configurable and extendable, application for verifying the status of your software products.
The user is free to configure which targets to test, which metrics to monitor, and where to store check outcomes. Healthcheck Bot also supports custom assertions written in Python for more sophisticated check scenarios.

## When Should I Use Healthcheck Bot?

Consider using Healthcheck Bot if:

* you need proactive monitoring of your software. This means you have an existing application in place, and you need to query it, regularly capture its state and compare it to the expected one;
* you want to load the outcomes of proactive healthchecks into existing infrastructure (Graylog, Nagios, whatever)
* the validation of your system state requires more complex comparations than the ones defined in DSL\Yaml\JSON, which are easier to express with code.
* you are familiar with Python.
 
## Alternative Solutions

If none of the above describes your case, you might want to consider one of the following alternatives:

* [Nagios](https://www.nagios.org/) and its application checks
* [Gloss](https://goss.rocks) if you need just servers pings, ports checks, server configuration etc.

## Healthcheck Bot Usage

The package provides executable `healthcheckbot` as the main entry point. You must pass a configuration file containing definitions of
your watchers and other options. In order to start the application, run:

```
healthcheckbot -c examples/config.yaml run
```

If you prefer Docker, there is a pre-built image available. You need to create a config file somewhere on host machine and run Docker as follows:

```bash
docker run --rm -it -v $PWD/myconfigs:/srv/config logicify/healthcheckbot
```

In this case, your config must be named `config.yaml`; it must be located in `./myconfigs` directory on your host machine.

If you want to use a different file, you could set it in env variable `CONFIG_FILE`:

```bash
docker run --rm -it -v $PWD/myconfigs:/srv/config -e CONFIG_FILE=/srv/config/advanced.yaml logicify/healthcheckbot
```

For the cases when you also need to pass your custom modules, e.g. custom assertions, you need to mount data directory as well. Check the following example:

docker-compose.yaml
```yaml
healthcheckbot:
  image: logicify/healthcheckbot
  volumes:
    - ./myconfig:/srv/config
    - ./mydata:/srv/data
  environment:
    CONFIG_FILE: /srv/config/my_config_name.yaml
```

my_config_name.yaml
```yaml
app:
  classpath:
    - /srv/data

outputs:
  console:
    provider: healthcheckbot.outputs.ConsoleOutput

triggers:
  each_1_minute:
    provider: healthcheckbot.triggers.SimpleTimer
    interval: 60

watchers:
  google_home:
    provider: healthcheckbot.watchers.HttpRequest
    url: http://google.com
    assert_response_time: 2
    assert_status: 200
    triggers:
      - each_1_minute
    custom_assertions:
      check_something_interesting:
        provider: mypackage.assertions.CustomAssert
        my_param: 'val1'
```

In this sample, we mount directory `/srv/data` from the host and declare it as a part of classpath, so all Python modules from this dir are accessible from the application in runtime. Thus, we can implement `CustomAssert` module and use it in our configuration. See [Customization](#customization) section for details.

## Concepts

Consider the following configuration example:

```yaml
outputs:
  console:
    provider: healthcheckbot.outputs.ConsoleOutput

triggers:
  each_1_minute:
    provider: healthcheckbot.triggers.SimpleTimer
    interval: 60

watchers:
  google_home:
    provider: healthcheckbot.watchers.HttpRequest
    url: http://google.com
    assert_status: 200
    triggers:
      - each_1_minute
```

In this example, we define a single watcher that will send HTTP request to `http://google.com` each minute.
Healthcheck will be treated as failed when the response status is not `200`.
The result of the watcher evaluation will be printed to STDOUT.

Generally, there are 4 types of entities (module types) Healthcheck Bot works with: Outputs, Triggers, Watchers, WatcherAsserts.
Sections below describe each of them. Please also note that user is able to implement their own module to extend or override default behaviour and connect it without modifying the core code. See [Customization](#customization) section below.
Regardless of the module type you define, there is a mandatory component called `provider`. It defines fully qualified name
of the class implementing corresponding module. The rest of options are parameters for module instance.

### Outputs

Output defines the way watcher's evaluation result will be delivered to the end user. It might be as simple as just console output
or a more real-life and common record in a database, or a centralized metric collection for a system like CloudWatch or Graylog2.

There is a couple of implementations of outputs built in the package.

#### Console Output

Just prints serialized JSON output to the STDOUT. There are no configuration parameters.

Usage Example:

```yaml
outputs:
  console:
    provider: healthcheckbot.outputs.ConsoleOutput
```

#### Logger Output

This one is very similar to console output, but the serialized result will be passed to the logger.

Parameters

| Parameter  | Description                                 | Default Value | Required |
| ---------- | ------------------------------------------- | ------------- | -------- |
| log_level  | Log level to be used when outputting result | INFO          | No       |
| loger_name | Name of the logger to use                   | OUT           | No       |


### Triggers

Triggers are responsible for initiation of worker execution. The most common use case is periodic run, but other scenarios are possible as well, e.g. execution after HTTP call.

#### Simple Timer

This implementation of the trigger is pretty self-explanatory - all it does is periodic watchers execution with constant interval specified as a parameter.

| Parameter         | Description                              | Default Value | Required |
| ----------------- | ---------------------------------------- | ------------- | -------- |
| interval          | Time interval in seconds between iterations | 300           | No       |
| start_immediately | If set to True, the first iteration will be triggered immediately after application starts; otherwise, in `interval` seconds | True          | No       |

Example

```yaml
triggers:
  each_1_minute:
    provider: healthcheckbot.triggers.SimpleTimer
    interval: 60
  each_5_minutes:
    provider: healthcheckbot.triggers.SimpleTimer
    interval: 300
```

### Watchers

Watchers are modules that actually read the system state and could optionally run some assertions over a certain state. Their parameters mostly depend on implementation, but there is a couple of options common for all watchers.

* `triggers` - the list of trigger names that will invoke the given watcher. It is important to list at least one trigger, otherwise, the watcher will never be invoked.
* `custom_assertions` - the dictionary containing assertions to be applied as a part of state verification after regular module assertions. See section [Watcher Asserts](#watcher-asserts) for details.

### Watcher Asserts

TBD

## Customization

User's ability to extend the behavior of any module is a key feature of Healthcheck Bot. In order to make it easier to load modules from the outside, user could extend classpath (folders to be scanned for classes) with a simple configuration option. Consider the following example:

```yaml
app:  
  classpath:
    - /tmp
outputs:
  console:
    provider: healthcheckbot.outputs.ConsoleOutput
triggers:
  each_1_minute:
    provider: healthcheckbot.triggers.SimpleTimer
    interval: 60
watchers:
  system_time:
    provider: logicify.watchers.SystemTimeWatcher
    triggers:
      - each_1_minute
```

Our `/tmp/logicify` folder looks as follows:

```
/tmp/logicify/
├── watchers.py
└── __init__.py
```

File `watchers.py` contains class `SystemTimeWatcher` that implements `WatcherModule`:

```python
class SystemTimeWatcher(WatcherModule):

    def __init__(self, application):
        super().__init__(application)
        self.error_when_midnight = False

    def obtain_state(self, trigger) -> object:
        current_time = datetime.now()
        return current_time

    def serialize_state(self, state: datetime) -> [dict, None]:
        return {
            "time": state.isoformat()
        }

    def do_assertions(self, state: datetime, reporter: ValidationReporter):
        if self.error_when_midnight:
            if state.time() == time(0, 0):
                reporter.error('its_midnight', 'Must be any time except of 00:00')

    PARAMS = (
        ParameterDef('error_when_midnight', validators=(validators.boolean,)),
    )
```

This implementation illustrates how you could create your own watchers. While this example shows only a watcher module, many concepts apply to the Triggers, Outputs and Asserts too.

`PARAMS` tuple gives you a way to configure arguments for your module. During application, bootstrap parameters from `yaml` will be sanitized, validated and assigned to the module instance according to definition configured with `ParameterDef`. 

Method `obtain_state` will be invoked by the trigger. You should implement your state gathering logic here. The result could be any object.

`do_assertions` will be invoked on state verification stage. `state` parameter here is what was returned from `obtain_state`, and `reporter` instance must be used to report assertion errors (if any).

And finally, `serialize_state` will be called before passing the result to output. It should convert state object to simple types (dictionaries, lists, primitives).

##  Contribution

The initial configuration of dev environment:

1. `virtualenv -p python3 venv`
1. `source ./venv/bin/activate`
1. `pip install -r ./requirements.txt`

## Credits

Dmitry Berezovsky, Logicify (http://logicify.com/)

## License

This plug-in is licensed under GPLv3. This means you are free to use it even in commercial projects.
Also note there is no warranty for this free software. Please see the included [LICENSE](LICENSE]) file for details.


[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FLogicify%2Fhealthcheckbot.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FLogicify%2Fhealthcheckbot?ref=badge_large)

# Healthcheck Bot

Healthcheck Bot is a standalone highly configurable and extendable application for verifying application status.
User is free to configure targets to be tested as well as the way output needs to be delivered. Application also supports custom
assertions written in Python for the cases when healthcheck is more complicated.

## Usage

Package provides executable `healthcheckbot` which is the main entry point. You must pass a configuration file containing definitions of
your watchers and other options. In order to start application run:

```
./healthcheckbot -c ../../examples/config.yaml server run
```


## Concepts

Consider the following configuration example:

```
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

In this example we define one single watcher which will send HTTP request to `http://google.com` each minute.
Healthcheck will be treated as failed when response status will be not `200`.
Result of the watcher evaluation will be printed to STDOUT.

Generally there are 4 types of entities healthcheckbot works with: Outputs, Triggers, Watchers, WatcherAsserts.
Sections below describe each one. Please also note that user has an ability to implement own module
to extend or override default behaviour and connect it without modifying core code. See [Customization] section below.

### Outputs

TBD

### Triggers

TBD

### Watchers

TBD

### WatcherAsserts

TBD

## Customization

TBD

## Contribution

TBD

## Credits

Dmitry Berezovsky, Logicify (http://logicify.com/)

## License

This plug-in is licensed under GPLv3. This allows you free non-commercial use.
Also note there is no warranty for this free software. Please see the included [LICENSE] file for details.
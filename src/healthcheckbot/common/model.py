#    Healthcheck Bot
#    Copyright (C) 2018 Dmitry Berezovsky
#    
#    HealthcheckBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    HealthcheckBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging

import typing
from argparse import ArgumentParser
from typing import List


class CliExtension(object):
    """
    Allows Module to extend CLI interface
    """
    COMMAND_NAME = None
    COMMAND_DESCRIPTION = None

    def __init__(self, parser: ArgumentParser, application):
        """
        :type application: healthcheckbot.common.core.ApplicationManager
        """
        super().__init__()
        self.parser = parser
        self.__application_manager = application

    def get_application_manager(self):
        """

        :rtype: healthcheckbot.common.core.ApplicationManager
        """
        return self.__application_manager

    @classmethod
    def setup_parser(cls, parser: ArgumentParser):
        pass

    def handle(self, args):
        raise NotImplementedError()


class Serializer(object):
    def serialize(self, obj):
        raise NotImplementedError("This method needs to be implemented in child class")

    def deserialize(self, data):
        raise NotImplementedError("This method needs to be implemented in child class")


class JsonSerializer(Serializer):
    def serialize(self, obj: object):
        json.dumps(obj)

    def deserialize(self, data: str):
        return json.loads(data)


class ConfigParser(object):
    def parse(self, config_section: dict, application, absolute_path: str = ''):
        """
        :param config_section:
        :param absolute_path: String containing absolute path from the config root to the given section.
        E.g. watchers/my_watcher/option1
        :type application: healthcheckbot.common.core.ApplicationManager
        """
        raise NotImplementedError()


class ParameterDef:
    def __init__(self, name: str, is_required=False, validators=None, parser: ConfigParser = None,
                 sanitize_fn: typing.Callable[[object], object] = None):
        super().__init__()
        self.name = name
        self.is_required = is_required
        self.validators = validators
        self.parser = parser
        self.sanitize_fn = sanitize_fn
        if self.validators is None:
            self.validators = []

    def sanitize(self, value):
        if self.sanitize_fn is not None:
            return self.sanitize_fn(value)
        return value

    def validate(self, value):
        for x in self.validators:
            if not x(value):
                raise ValueError('Parameter {} is invalid'.format(self.name))


class Module:
    PARAMS = []  # type: List[ParameterDef]
    MODULE_LEVEL_PARAMS = []  # type: List[ParameterDef]

    def __init__(self, application):
        """
        :type application: healthcheckbot.common.core.ApplicationManager
        """
        self.name = None
        self.__application = application
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_application_manager(self):
        """
        :rtype application: healthcheckbot.common.core.ApplicationManager
        """
        return self.__application

    def on_initialized(self):
        pass

    def on_configured(self):
        pass

    def on_before_destroyed(self):
        pass

    def validate(self):
        pass


class LoopModuleMixin:
    """
    Modules inheriting this mixin will be registered in application loop. Thus step method will be invoked
    regularly as a part of main application routine.
    """

    def step(self):
        pass


class ValidationError(typing.NamedTuple):
    name: str
    description: str
    critical: bool


class WatcherResult:

    def __init__(self, state: dict = None, assertions_failed: List[ValidationError] = None,
                 extra: typing.Dict[str, str] = None) -> None:
        self.assertions_failed = assertions_failed
        self.state = state or {}
        self.extra = extra or {}

    def to_dict(self) -> typing.Dict:
        return {
            'failed_assertions': [x._asdict() for x in self.assertions_failed],
            'checks_passed': int(self.checks_passed),
            'state': self.state,
            'extra': self.extra
        }

    @property
    def checks_passed(self):
        return self.assertions_failed is None or len(self.assertions_failed) == 0


class ValidationReporter:

    def __init__(self, watcher, trigger) -> None:
        """
        :type watcher: healthcheckbot.common.core.WatcherModule
        :type trigger: healthcheckbot.common.core.TriggerModule
        """
        super().__init__()
        self.watcher = watcher
        self.trigger = trigger
        self.errors = []  # type: List[ValidationError]
        self.extra_data = {}

    def error(self, name: str, description: str = None, critical=True):
        self.errors.append(ValidationError(name=name, description=description, critical=critical))

    def extra(self, field: str, value: str):
        self.extra_data[field] = value


class WatcherModule(Module):

    def __init__(self, application):
        super().__init__(application)
        self.enable_assertions = True
        self.custom_assertions = []  # type: List[WatcherAssert]

    def obtain_state(self, trigger) -> object:
        """
        :type trigger: healthcheckbot.common.core.TriggerModule
        :return state object
        """
        pass

    def serialize_state(self, state: object) -> [dict, None]:
        if state is not None:
            return vars(state)
        else:
            return None

    def do_assertions(self, state: object, reporter: ValidationReporter):
        """
        :param reporter:
        :param state:
        :param trigger:
        """
        pass


class OutputModule(Module):

    def output(self, watcher_instance: WatcherModule, watcher_result: WatcherResult):
        pass


class TriggerModule(Module):

    def register_watcher(self, watcher: WatcherModule):
        pass


class WatcherAssert(Module):

    def do_assert(self, state: object, reporter: ValidationReporter, assertion_name: str):
        """
        :param assertion_name:
        :param reporter:
        :param state:
        :param trigger:
        """
        pass

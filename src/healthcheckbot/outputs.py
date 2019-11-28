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

import logging

import collections
from graypy import GELFHandler, GELFTcpHandler

from healthcheckbot.common import validators
from healthcheckbot.common.error import ConfigValidationError
from healthcheckbot.common.model import OutputModule, WatcherModule, WatcherResult, ParameterDef


class ConsoleOutput(OutputModule):
    def output(self, watcher_instance: WatcherModule, watcher_result: WatcherResult):
        print(watcher_result.to_dict())


class LoggerOutput(OutputModule):
    def __init__(self, application):
        super().__init__(application)
        self.logger_name = None  # type: str
        self.log_level = logging.INFO  # type: int
        self.include_state = True
        self.include_validations = True
        self.target_logger = None  # type: logging.Logger

    def output(self, watcher_instance: WatcherModule, watcher_result: WatcherResult):
        self.target_logger.log(self.log_level, str(watcher_result.to_dict()))

    def on_configured(self):
        self.target_logger = logging.getLogger(self.logger_name)
        self.target_logger.setLevel(self.log_level)

    PARAMS = (
        ParameterDef('logger_name', is_required=True),
        ParameterDef('log_level', sanitize_fn=lambda level_name: logging._nameToLevel.get(level_name.upper()),
                     validators=(validators.integer,)),
        ParameterDef('facility', validators=(validators.string,)),
        ParameterDef('include_instance_name', validators=(validators.boolean,)),
        ParameterDef('include_state', validators=(validators.boolean,)),
        ParameterDef('include_validations', validators=(validators.boolean,)),
    )


class GelfOutput(OutputModule):
    def __init__(self, application):
        super().__init__(application)
        self.gelf_logger = None  # type: logging.Logger
        self.gelf_port = 9402  # type: int
        self.gelf_host = None  # type: str
        self.gelf_protocol = 'udp'
        self.facility = 'healthcheck'
        self.include_state = True
        self.include_validations = True
        self.include_instance_name = True
        self.extra_fields = {}

    def __flatten(self, dictionary, parent_key='', sep='__'):
        items = []
        for k, v in dictionary.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.__flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def on_configured(self):
        self.gelf_logger = logging.getLogger('GELF')
        self.gelf_logger.setLevel(logging.DEBUG)
        self.gelf_logger.propagate = False
        if self.gelf_protocol == 'udp':
            self.gelf_logger.addHandler(
                GELFHandler(host=self.gelf_host, port=self.gelf_port, facility=self.facility, debugging_fields=False, extra_fields=True))
        elif self.gelf_protocol == 'tcp':
            handler = GELFTcpHandler(host=self.gelf_host, facility=self.facility, port=self.gelf_port,
                                     debugging_fields=False, extra_fields=True)
            handler.level = logging.DEBUG
            self.gelf_logger.addHandler(handler)

        else:
            raise ConfigValidationError('/'.join(('watchers', self.name)),
                                        "Parameter gelf_protocol must be one of: udp, tcp but {} given".format(
                                            self.gelf_protocol))

    def output(self, watcher_instance: WatcherModule, watcher_result: WatcherResult):
        data = watcher_result.to_dict()
        if not self.include_state:
            del data['state']
        if not self.include_validations:
            del data['failed_assertions']
        data = self.__flatten(watcher_result.to_dict())
        data.update(dict(tags='healthcheck', watcher_name=watcher_instance.name))
        if self.include_instance_name:
            data['instance'] = self.get_application_manager().get_instance_settings().id
        if len(watcher_result.extra.keys()) > 0 and 'extra' in data:
            data.update(self.__flatten(watcher_result.extra))
            del data['extra']
        data.update(self.extra_fields)
        self.gelf_logger.info('HealthcheckBot {}: Watcher {} - checks {}'.format(
            self.get_application_manager().get_instance_settings().id,
            watcher_instance.name,
            'passed' if watcher_result.checks_passed else 'failed'
        ),
            extra=data)

    PARAMS = (
        ParameterDef('gelf_host', is_required=True),
        ParameterDef('gelf_port', validators=(validators.integer,)),
        ParameterDef('gelf_protocol', validators=(validators.string,)),
        ParameterDef('facility', validators=(validators.string,)),
        ParameterDef('include_state', validators=(validators.boolean,)),
        ParameterDef('include_validations', validators=(validators.boolean,)),
        ParameterDef('extra_fields', validators=(validators.dict_of_strings,)),
    )

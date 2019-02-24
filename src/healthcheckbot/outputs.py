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

from healthcheckbot.common import validators
from healthcheckbot.common.model import OutputModule, WatcherModule, WatcherResult, ParameterDef, ConfigParser


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
        self.target_logger = logging.Logger(self.logger_name)

    PARAMS = (
        ParameterDef('logger_name', is_required=True),
        ParameterDef('log_level', sanitize_fn=lambda level_name: logging._nameToLevel.get(level_name.upper()),
                     validators=(validators.integer,)),
        ParameterDef('include_instance_name', validators=(validators.boolean,)),
        ParameterDef('include_state', validators=(validators.boolean,)),
        ParameterDef('include_validations', validators=(validators.boolean,)),
    )

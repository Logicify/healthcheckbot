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

from typing import NamedTuple, Callable, List

import datetime

from healthcheckbot.common import validators
from healthcheckbot.common.model import TriggerModule, WatcherModule, LoopModuleMixin, ParameterDef


class SimpleTimerJob:

    def __init__(self, next_run: datetime.datetime = None, watcher: WatcherModule = None) -> None:
        self.next_run = next_run
        self.watcher = watcher


class SimpleTimer(TriggerModule, LoopModuleMixin):

    def __init__(self, application):
        super().__init__(application)
        self.interval = 300
        self.start_immediately = True
        self.__jobs = []  # type: List[SimpleTimerJob]

    def on_configured(self):
        pass

    def register_watcher(self, watcher: WatcherModule):
        self.__jobs.append(SimpleTimerJob(
            next_run=datetime.datetime.now() + datetime.timedelta(
                seconds=0 if self.start_immediately else self.interval),
            watcher=watcher
        ))

    def step(self):
        current_time = datetime.datetime.now()
        for job in self.__jobs:
            if job.next_run <= current_time:
                self.logger.info("Running watcher {}".format(job.watcher.name))
                self.get_application_manager().run_watcher(job.watcher, self)
                job.next_run = datetime.datetime.now() + datetime.timedelta(seconds=self.interval)

    PARAMS = (
        ParameterDef('interval', validators=(validators.integer,)),
        ParameterDef('start_immediately', validators=(validators.boolean,)),
    )

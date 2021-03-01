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

from typing import List

import datetime

from healthcheckbot.common import validators
from healthcheckbot.common.model import (
    TriggerModule,
    WatcherModule,
    LoopModuleMixin,
    ParameterDef,
    WatcherResult,
    ValidationError,
)
from healthcheckbot.common.utils import time_limit


class SimpleTimerJob:
    def __init__(self, next_run: datetime.datetime = None, watcher: WatcherModule = None) -> None:
        self.next_run = next_run
        self.postpone_interval = None  # type: datetime.timedelta
        self.watcher = watcher
        self.fail_counter = 0


class SimpleTimer(TriggerModule, LoopModuleMixin):
    def __init__(self, application):
        super().__init__(application)
        self.interval = 300
        self.start_immediately = True
        self.__jobs = []  # type: List[SimpleTimerJob]
        self.__max_postpone_duration = datetime.timedelta(minutes=20)
        self.__postpone_interval = None

    def on_configured(self):
        pass

    def register_watcher(self, watcher: WatcherModule):
        self.__jobs.append(
            SimpleTimerJob(
                next_run=datetime.datetime.now()
                + datetime.timedelta(seconds=0 if self.start_immediately else self.interval),
                watcher=watcher,
            )
        )

    def step(self):
        current_time = datetime.datetime.now()
        for job in self.__jobs:
            if job.next_run <= current_time:
                self.logger.info("Running watcher {}".format(job.watcher.name))
                try:
                    with time_limit(job.watcher.execution_timeout, msg="Execution watcher timeout"):
                        self.get_application_manager().run_watcher(job.watcher, self)
                    job.next_run = datetime.datetime.now() + datetime.timedelta(seconds=self.interval)
                    job.postpone_interval = None
                    job.fail_counter = 0
                except Exception as e:
                    self.logger.error("Worker execution failed: " + str(e))
                    if job.postpone_interval is None:
                        job.postpone_interval = datetime.timedelta(seconds=self.interval)
                    job.postpone_interval *= 2
                    job.fail_counter += 1
                    if job.postpone_interval > self.__max_postpone_duration:
                        job.postpone_interval = self.__max_postpone_duration
                    job.next_run = datetime.datetime.now() + job.postpone_interval
                    self.logger.error(
                        "The next cycle will be postponed for {} seconds".format(job.postpone_interval.total_seconds())
                    )
                    watcher_result = WatcherResult({}, [ValidationError("execution_cycle", str(e), True)])
                    self.get_application_manager().deliver_watcher_result(job.watcher, watcher_result)

    PARAMS = (
        ParameterDef("interval", validators=(validators.integer,)),
        ParameterDef("start_immediately", validators=(validators.boolean,)),
    )

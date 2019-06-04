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

from healthcheckbot.common import validators
from healthcheckbot.common.model import WatcherModule, ParameterDef, ValidationReporter
import redis


class RedisQueueSizeWatcher(WatcherModule):
    def __init__(self, application):
        super().__init__(application)
        self.url = None
        self.host = 'localhost'
        self.port = 6379
        self.db = 0
        self.queue_name = 'celery'
        self.assert_min_qty = None
        self.assert_max_qty = None
        self.__redis = None  # type: redis.Redis
        self.socket_timeout = 7000

    def obtain_state(self, trigger) -> object:
        if self.__redis is None:
            if self.url:
                self.__redis = redis.Redis.from_url(url=self.url, db=self.db, socket_timeout=self.socket_timeout,
                                                    socket_connect_timeout=self.socket_timeout, max_connections=1)
            else:
                self.__redis = redis.Redis(host=self.host, port=self.port, db=self.db,
                                           socket_timeout=self.socket_timeout, max_connections=1,
                                           socket_connect_timeout=self.socket_timeout)
        messages_count = self.__redis.llen(self.queue_name)
        self.__redis.connection_pool.disconnect()
        return messages_count

    def serialize_state(self, state: int) -> [dict, None]:
        return {
            "queue": self.queue_name,
            "msg_qty": state
        }

    def do_assertions(self, state: int, reporter: ValidationReporter):
        if self.assert_min_qty is not None:
            if state < self.assert_min_qty:
                reporter.error('min_qty_assert', "Expected minimum number of messages in queue is {} but actual qty "
                                                 "is {}".format(self.assert_min_qty, state))
        if self.assert_max_qty is not None:
            if state > self.assert_max_qty:
                reporter.error('max_qty_assert', "Expected maximum number of messages in queue is {} but actual qty "
                                                 "is {}".format(self.assert_max_qty, state))

    PARAMS = (
        ParameterDef('url', validators=(validators.string,)),
        ParameterDef('host', validators=(validators.string,)),
        ParameterDef('queue_name', validators=(validators.string,)),
        ParameterDef('port', validators=(validators.integer,)),
        ParameterDef('db', validators=(validators.integer,)),
        ParameterDef('assert_min_qty', validators=(validators.integer,)),
        ParameterDef('assert_max_qty', validators=(validators.integer,)),
    )

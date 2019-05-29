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

from datetime import datetime, time

import requests

from healthcheckbot.common import validators
from healthcheckbot.common.model import WatcherModule, ParameterDef, ValidationReporter


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
                reporter.error('its_midnight')

    PARAMS = (
        ParameterDef('error_when_midnight', validators=(validators.boolean,)),
    )


class HttpRequest(WatcherModule):

    def __init__(self, application):
        super().__init__(application)
        self.url = None
        self.headers = None
        self.auth_user = None
        self.auth_password = None
        self.payload = None
        self.method = 'GET'
        self.timeout = 4
        self.assert_status = None
        self.assert_response_time = None

    def obtain_state(self, trigger):
        return requests.request(self.method, self.url, data=self.payload, headers=self.headers,
                                auth=self.basic_auth,
                                timeout=self.timeout)

    @property
    def basic_auth(self):
        return None if self.auth_user is None and self.auth_password is None else (self.auth_user, self.auth_password)

    def serialize_state(self, state: requests.Response):
        return dict(
            status_code=state.status_code,
            response_time=state.elapsed.total_seconds(),
            url=state.url,
            redirect_history=[dict(status_code=x.status_code, url=x.url) for x in state.history]
        )

    def do_assertions(self, state: requests.Response, reporter: ValidationReporter):
        if self.assert_status is not None and state.status_code != self.assert_status:
            reporter.error('status_code',
                           'Expected HTTP status {} but got {}'.format(self.assert_status, state.status_code))
        if self.assert_response_time is not None and state.elapsed.total_seconds() > self.assert_response_time:
            reporter.error('response_time',
                           'Expected HTTP response time must be '
                           '< {} but actual is {}'.format(self.assert_response_time, state.elapsed.total_seconds()))

    PARAMS = (
        ParameterDef('url', is_required=True, validators=(validators.string,)),
        ParameterDef('method', validators=(validators.string,)),
        ParameterDef('auth_user', validators=(validators.string,)),
        ParameterDef('auth_password', validators=(validators.string,)),
        ParameterDef('headers', validators=(validators.dict_of_strings,)),
        ParameterDef('timeout', validators=(validators.integer,)),
        ParameterDef('payload'),
        ParameterDef('assert_status'),
        ParameterDef('assert_response_time', validators=(validators.number,)),
    )

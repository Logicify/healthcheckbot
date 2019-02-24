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

import requests
from bs4 import BeautifulSoup

from healthcheckbot.common import validators
from healthcheckbot.common.model import WatcherAssert, ValidationReporter, ParameterDef


class TitleAssert(WatcherAssert):

    def __init__(self, application):
        super().__init__(application)
        self.expected_title = None

    def do_assert(self, state: requests.Response, reporter: ValidationReporter, assertion_name: str):
        soup = BeautifulSoup(state.content, 'html.parser')
        actual_title = soup.title.string if soup.title else None
        if actual_title != self.expected_title:
            reporter.error(assertion_name,
                           'Expected title is "{}" but actual is "{}"'.format(self.expected_title, actual_title))

    PARAMS = (
        ParameterDef('expected_title', is_required=True, validators=(validators.string,)),
    )

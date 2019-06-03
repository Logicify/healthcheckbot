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

class SimpleException(Exception):
    def __init__(self, message, ex=None):
        self.message = message
        self.ex = ex


class ExpressionEvaluationError(SimpleException):
    pass


class InvalidModuleError(SimpleException):
    pass


class WatcherRuntimeError(SimpleException):
    pass


class OutputRuntimeError(SimpleException):
    pass


class ConfigValidationError(SimpleException):

    def __init__(self, section_name, message, ex=None):
        super().__init__(message, ex)
        self.section = section_name

    def __repr__(self, *args, **kwargs):
        return "Invalid configuration: [" + self.section + ']: ' + self.message

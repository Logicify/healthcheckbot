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

def boolean(value):
    return isinstance(value, bool)


def integer(value):
    return isinstance(value, int)


def float_number(value):
    return isinstance(value, float)


def number(value):
    return isinstance(value, (int, float))


def string(value):
    return isinstance(value, str)


def dictionary(value):
    return isinstance(value, dict)


def dict_of_strings(value):
    if not dictionary(value):
        return False
    for v in value.values():
        if not isinstance(v, str):
            return False
    return True

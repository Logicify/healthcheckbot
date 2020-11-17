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

import traceback
from typing import Callable, Optional, Any

import collections
import sys


class EvaluatingConfigWrapper(dict, collections.UserDict):

    def __init__(self, source: dict, evaluator: Callable[[str], str] = None):
        super().__init__(source)
        self.evaluator = evaluator

    def get(self, k, default=None) -> Optional[Any]:
        try:
            return self[k]
        except KeyError:
            return default

    def __getitem__(self, key):
        original = dict.__getitem__(self, key)
        if self.evaluator is not None:
            if isinstance(original, str):
                return self.evaluator(original)
            elif isinstance(original, dict) and not isinstance(original, EvaluatingConfigWrapper):
                return self.__class__(original, self.evaluator)
        return original


class CLI:
    verbose_mode = False

    @classmethod
    def print_data(cls, msg: str):
        print(msg)

    @classmethod
    def print_info(cls, msg: str):
        print(msg, file=sys.stderr)

    @classmethod
    def print_error(cls, exception):
        print(" -> ERROR: " + str(exception), file=sys.stderr)
        if cls.verbose_mode:
            print('--------------')
            traceback.print_exc(file=sys.stderr)

    @classmethod
    def print_debug(cls, string_to_print):
        if cls.verbose_mode:
            print('[DEBUG] ' + string_to_print, file=sys.stderr)

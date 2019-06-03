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

import re
from os import environ

from typing import NamedTuple

from healthcheckbot.common.error import ExpressionEvaluationError

__ALL__ = ('simple_env_evaluator',)

sel_expression_parser = re.compile(r'\$(?P<name>\w[\d\w]*)(?P<is_func>\((?P<arg>.*?)?\))?',
                                   re.IGNORECASE | re.MULTILINE)


class SelExpression(NamedTuple):
    name: str
    is_function: bool
    arguments: str


def simple_sel_parser(expression: str):
    def match_cb(m):
        return evaluate_expression(SelExpression(m.group('name'), m.group('is_func') is not None, m.group('arg')))

    return sel_expression_parser.sub(match_cb, expression)


def evaluate_expression(sel_expr: SelExpression) -> str:
    if sel_expr.name == 'env':
        return environ.get(sel_expr.arguments, '')
    else:
        raise ExpressionEvaluationError('Expression ${} is not supported'.format(sel_expr.name))


def simple_env_evaluator(original):
    if isinstance(original, str):
        return simple_sel_parser(original)
    return original


if __name__ == '__main__':
    simple_sel_parser('hello $env(MY_VAR1) and also $env(ANOTHER_VAR2)')

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

import unittest
from os import environ

from healthcheckbot.common.evaluator import simple_env_evaluator


class SimpleEnvSubstitutionTest(unittest.TestCase):

    def setUp(self) -> None:
        self.evaluator = simple_env_evaluator

    def test_no_expression_returns_original_str(self):
        input_str = 'parameter without expression'
        res = self.evaluator(input_str)
        self.assertEqual(input_str, res)

    def test_single_correct_substitution_in_the_middle(self):
        environ["MY_VAR"] = "value"
        input_str = 'my string=$env(MY_VAR) some other text'
        res = self.evaluator(input_str)
        self.assertEqual(res, 'my string=value some other text')

    def test_single_correct_substitution_at_the_end(self):
        environ["MY_VAR"] = "value"
        input_str = 'my string=$env(MY_VAR)'
        res = self.evaluator(input_str)
        self.assertEqual(res, 'my string=value')

    def test_single_correct_substitution_without_surrounding_text(self):
        environ["MY_VAR"] = "value"
        input_str = '$env(MY_VAR)'
        res = self.evaluator(input_str)
        self.assertEqual(res, 'value')

    def test_multiple_correct_substitutions(self):
        environ["MY_VAR"] = "value"
        environ["ANOTHER_VAR"] = "value2"
        input_str = 'key1=$env(MY_VAR), key2=$env(ANOTHER_VAR)'
        res = self.evaluator(input_str)
        self.assertEqual(res, 'key1=value, key2=value2')

    def test_non_existing_substitutions(self):
        input_str = 'key1=$env(NON_EXISTING)'
        res = self.evaluator(input_str)
        self.assertEqual(res, 'key1=')

    def test_none_input(self):
        res = self.evaluator(None)
        self.assertEqual(res, None)

    def test_integer_input(self):
        res = self.evaluator(1)
        self.assertEqual(res, 1)

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

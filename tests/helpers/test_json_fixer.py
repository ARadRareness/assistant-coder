from language_models.helpers.json_fixer import (
    fix_json_errors_manually,
)
import unittest


class TestJsonFixer(unittest.TestCase):
    def test_valid_json(self):
        valid_json = '{"name": "John", "age": 30}'
        result = fix_json_errors_manually(valid_json)
        self.assertEqual(result, valid_json)

    def test_invalid_json_single_quotes(self):
        invalid_json = "{'name': 'John', 'age': 30}"
        expected_fixed_json = '{"name": "John", "age": 30}'
        result = fix_json_errors_manually(invalid_json)
        self.assertEqual(result, expected_fixed_json)

    def test_invalid_json_unfinished_json(self):
        invalid_json = "{'name': 'John', 'age': '"
        expected_fixed_json = '{"name": "John"}'
        result = fix_json_errors_manually(invalid_json)
        self.assertEqual(result, expected_fixed_json)

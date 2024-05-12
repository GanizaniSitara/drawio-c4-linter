import unittest
from drawio_c4_lint.c4_lint import C4Lint
import os

class TestC4Lint(unittest.TestCase):

    def test_missing_name(self):
        lint = C4Lint(os.path.join('test_files', 'missing_name.drawio'))
        errors = lint.lint()
        self.assertIn("mxCell (id: esDkObLFpEDxHqnVwX9G-1) missing 'C4 name' property.", errors)

    def test_missing_description(self):
        lint = C4Lint(os.path.join('test_files', 'missing_description.drawio'))
        errors = lint.lint()
        self.assertIn("mxCell (id: esDkObLFpEDxHqnVwX9G-1) missing 'C4 description' property.", errors)

    def test_missing_type(self):
        lint = C4Lint(os.path.join('test_files', 'missing_type.drawio'))
        errors = lint.lint()
        self.assertIn("mxCell (id: esDkObLFpEDxHqnVwX9G-1) missing 'C4 type' property.", errors)

    def test_missing_technology_on_relationship(self):
        lint = C4Lint(os.path.join('test_files', 'missing_technology_on_relationship.drawio'))
        errors = lint.lint()
        self.assertIn("mxCell (id: lmOmmAKjzgPhh1E44Ozs-1) missing 'C4 relationship technology' property.", errors)

    def test_missing_description_on_relationship(self):
        lint = C4Lint(os.path.join('test_files', 'missing_description_on_relationship.drawio'))
        errors = lint.lint()
        self.assertIn("mxCell (id: lmOmmAKjzgPhh1E44Ozs-1) missing 'C4 relationship description' property.", errors)

    def test_non_c4_object(self):
        lint = C4Lint(os.path.join('test_files', 'non_c4_object.drawio'))
        errors = lint.lint()
        expected_error = "Non C4 element (id: lvlDorcLZH3-U9y09GGk-1) found."
        self.assertIn(expected_error, errors)

    def test_non_c4_no_objects(self):
        lint = C4Lint(os.path.join('test_files', 'non_c4_no_objects.drawio'))
        errors = lint.lint()
        expected_error = "No elements of type Object found."
        self.assertIn(expected_error, errors)

    def test_is_c4_true(self):
        lint = C4Lint(os.path.join('test_files', 'c4.drawio'))
        self.assertTrue(lint.is_c4())

    def test_is_c4_false(self):
        lint = C4Lint(os.path.join('test_files', 'non_c4_no_objects.drawio'))
        self.assertFalse(lint.is_c4())

    def test_missing_connection(self):
        lint = C4Lint(os.path.join('test_files', 'missing_connection.drawio'))
        errors = lint.lint()
        self.assertEqual(len(errors), 2)

if __name__ == "__main__":
    unittest.main()

import unittest
from drawio_c4_lint.c4_lint import C4Lint
import os

class TestC4Lint(unittest.TestCase):

    def test_missing_name(self):
        lint = C4Lint(os.path.join('test_files', 'missing_name.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Name' property missing ---  c4Type: Software System, c4Description: Description of software system."
        self.assertIn(expected_error, errors['Systems'])

    def test_missing_description(self):
        lint = C4Lint(os.path.join('test_files', 'missing_description.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Description' property missing ---  c4Name: System Name, c4Type: Software System"
        self.assertIn(expected_error, errors['Systems'])

    def test_missing_type(self):
        lint = C4Lint(os.path.join('test_files', 'missing_type.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Type' property missing ---  c4Name: System Name, c4Description: Description"
        self.assertIn(expected_error, errors['Actors'])

    def test_missing_technology_on_relationship(self):
        lint = C4Lint(os.path.join('test_files', 'missing_technology_on_relationship.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Technology' property missing ---  c4Type: Relationship, c4Description: Description"
        self.assertIn(expected_error, errors['Relationships'])

    def test_missing_description_on_relationship(self):
        lint = C4Lint(os.path.join('test_files', 'missing_description_on_relationship.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Description' property missing ---  c4Type: Relationship, c4Technology: e.g. JSON/HTTP"
        self.assertIn(expected_error, errors['Relationships'])

    def test_non_c4_object(self):
        lint = C4Lint(os.path.join('test_files', 'non_c4_object.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: Non-C4 element found. Label: With Properties"
        self.assertIn(expected_error, errors['Other'])

    def test_non_c4_no_objects(self):
        lint = C4Lint(os.path.join('test_files', 'non_c4_no_objects.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: No elements of type Object found."
        self.assertIn(expected_error, errors['Other'])

    def test_is_c4_true(self):
        lint = C4Lint(os.path.join('test_files', 'c4.drawio'))
        self.assertTrue(lint.is_c4())

    def test_is_c4_false(self):
        lint = C4Lint(os.path.join('test_files', 'non_c4_no_objects.drawio'))
        self.assertFalse(lint.is_c4())

    def test_missing_connection(self):
        lint = C4Lint(os.path.join('test_files', 'missing_connection.drawio'))
        errors = lint.lint()
        expected_error_1 = "ERROR: Software System (c4Type: Software System, id: esDkObLFpEDxHqnVwX9G-3) is not connected by any relationship."
        expected_error_2 = "ERROR: Software System (c4Type: Software System, id: esDkObLFpEDxHqnVwX9G-4) is not connected by any relationship."
        self.assertIn(expected_error_1, errors['Systems'])
        self.assertIn(expected_error_2, errors['Systems'])
        self.assertEqual(len(errors['Systems']), 2)


    def test_filename_format_invalid(self):
        lint = C4Lint(os.path.join('test_files', 'c4.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: Filename 'test_files\\c4.drawio' does not match expected format 'C4 L<x> <system name>.drawio'"
        self.assertIn(expected_error, errors['Other'])

    def test_filename_format_unicode(self):
        lint = C4Lint(os.path.join('test_files', 'C4 L2 システム.drawio'))
        errors = lint.lint()
        self.assertNotIn(
            "Filename 'C4 L2 システム.drawio' does not match expected format 'C4 L<x> <system name>.drawio'",
            errors['Other'])

if __name__ == "__main__":
    unittest.main()

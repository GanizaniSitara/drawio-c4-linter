import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from drawio_c4_lint.c4_lint import C4Lint
from drawio_c4_lint.cli import collect_files, main

# Fixtures are addressed relative to this file, not to the working directory.
# Using bare relative paths meant the suite only passed when pytest happened to be
# run from inside this package - from the repository root every test that opened a
# fixture failed with "failed to load external entity".
HERE = Path(__file__).resolve().parent
TEST_FILES = HERE / "test_files"
APPLICATIONS_CSV = HERE / "applications.csv"


def fixture(name):
    """Absolute path to a fixture diagram."""
    return str(TEST_FILES / name)

class TestC4Lint(unittest.TestCase):

    def test_missing_name(self):
        lint = C4Lint(fixture('missing_name.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Name' property missing ---  c4Type: Software System, c4Description: Description of software system."
        self.assertIn(expected_error, errors['Systems'])

    def test_missing_description(self):
        lint = C4Lint(fixture('missing_description.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Description' property missing ---  c4Name: System Name, c4Type: Software System"
        self.assertIn(expected_error, errors['Systems'])

    def test_missing_type(self):
        lint = C4Lint(fixture('missing_type.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Type' property missing ---  c4Name: System Name, c4Description: Description"
        self.assertIn(expected_error, errors['Other'])

    def test_missing_technology_on_relationship(self):
        lint = C4Lint(fixture('missing_technology_on_relationship.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Technology' property missing ---  c4Type: Relationship, c4Description: Description"
        self.assertIn(expected_error, errors['Relationships'])

    def test_missing_description_on_relationship(self):
        lint = C4Lint(fixture('missing_description_on_relationship.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: 'c4Description' property missing ---  c4Type: Relationship, c4Technology: e.g. JSON/HTTP"
        self.assertIn(expected_error, errors['Relationships'])

    def test_non_c4_object(self):
        lint = C4Lint(fixture('non_c4_object.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: Non-C4 element found. Label: With Properties"
        self.assertIn(expected_error, errors['Other'])

    def test_non_c4_no_objects(self):
        lint = C4Lint(fixture('non_c4_no_objects.drawio'))
        errors = lint.lint()
        expected_error = "ERROR: No elements of type Object found."
        self.assertIn(expected_error, errors['Other'])

    def test_is_c4_true(self):
        lint = C4Lint(fixture('c4.drawio'))
        self.assertTrue(lint.is_c4())

    def test_is_c4_false(self):
        lint = C4Lint(fixture('non_c4_no_objects.drawio'))
        self.assertFalse(lint.is_c4())

    def test_missing_connection(self):
        lint = C4Lint(fixture('missing_connection.drawio'),known_applications=str(APPLICATIONS_CSV))
        errors = lint.lint()
        expected_error_1 = "ERROR: Software System (c4Name: System name C, c4Type: Software System, id esDkObLFpEDxHqnVwX9G-3) is not connected by any relationship."
        expected_error_2 = "ERROR: Software System (c4Name: External system name D, c4Type: Software System, id esDkObLFpEDxHqnVwX9G-4) is not connected by any relationship."
        self.assertIn(expected_error_1, errors['Systems'])
        self.assertIn(expected_error_2, errors['Systems'])
        self.assertEqual(len(errors['Systems']), 2)


    def test_filename_format_invalid(self):
        lint = C4Lint(fixture('c4.drawio'), check_filename=True)
        errors = lint.lint()
        # The message embeds the path as given, so assert on the parts that do not
        # vary with the platform's separator or with where the repo is checked out.
        self.assertEqual(len(errors['Other']), 1)
        message = errors['Other'][0]
        self.assertTrue(message.startswith("ERROR: Filename '"))
        self.assertIn('c4.drawio', message)
        self.assertTrue(
            message.endswith("does not match expected format 'C4 L<x> <system name>.drawio'")
        )

    def test_filename_format_not_checked_by_default(self):
        lint = C4Lint(fixture('c4.drawio'))
        self.assertEqual(lint.lint()['Other'], [])

    def test_filename_format_unicode(self):
        lint = C4Lint(fixture('C4 L2 システム.drawio'), check_filename=True)
        errors = lint.lint()
        self.assertNotIn(
            "Filename 'C4 L2 システム.drawio' does not match expected format 'C4 L<x> <system name>.drawio'",
            errors['Other'])


def output_full_linter_results():
    test_files_dir = str(TEST_FILES)
    test_results_dir = str(HERE / 'test_results')
    if not os.path.exists(test_results_dir):
        os.makedirs(test_results_dir)
    for filename in os.listdir(test_files_dir):
        if filename.endswith('.drawio'):
            file_path = os.path.join(test_files_dir, filename)
            lint = C4Lint(file_path,structurizr=True)
            result = str(lint)
            output_file = os.path.join(test_results_dir, f"{os.path.splitext(filename)[0]}_results.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)


class TestKnownApplications(unittest.TestCase):
    """The known-application check only applies when a list is supplied."""

    def test_no_warnings_without_a_list(self):
        lint = C4Lint(fixture('c4.drawio'))
        self.assertEqual(lint.warnings['Systems'], [])

    def test_exact_match_is_case_insensitive_and_keeps_the_known_spelling(self):
        lint = C4Lint(fixture('c4.drawio'))
        self.assertEqual(lint.match_strings('aphrodite', ['Aphrodite', 'Boreas']),
                         ['Aphrodite'])

    def test_near_miss_is_suggested(self):
        lint = C4Lint(fixture('c4.drawio'))
        self.assertEqual(lint.match_strings('Aphrodit', ['Aphrodite', 'Boreas']),
                         ['Aphrodite'])

    def test_unrelated_name_suggests_nothing(self):
        lint = C4Lint(fixture('c4.drawio'))
        self.assertEqual(lint.match_strings('Zzzz', ['Aphrodite', 'Boreas']), [])

    def test_unknown_name_warns_but_is_not_an_error(self):
        lint = C4Lint(fixture('c4.drawio'),
                      known_applications=str(APPLICATIONS_CSV))
        self.assertTrue(lint.warnings['Systems'])
        self.assertFalse(lint.has_errors())


class TestStructurizrExport(unittest.TestCase):

    def setUp(self):
        self.lint = C4Lint(fixture('c4.drawio'))

    def test_elements_and_relationship_are_present(self):
        model = self.lint.to_model()
        self.assertEqual(len(model['elements']), 2)
        self.assertEqual(len(model['relationships']), 1)

    def test_relationship_endpoints_resolve_to_elements(self):
        model = self.lint.to_model()
        relationship = model['relationships'][0]
        self.assertIn(relationship['source'], model['elements'])
        self.assertIn(relationship['target'], model['elements'])

    def test_dsl_declares_the_systems_and_the_relationship(self):
        dsl = self.lint.to_structurizr()
        self.assertIn('workspace {', dsl)
        self.assertIn('softwareSystem "System name"', dsl)
        self.assertIn('->', dsl)


class TestCli(unittest.TestCase):

    def test_clean_diagram_exits_zero(self):
        self.assertEqual(main([fixture('c4.drawio')]), 0)

    def test_diagram_with_errors_exits_one(self):
        self.assertEqual(main([fixture('missing_name.drawio')]), 1)

    def test_directory_is_walked(self):
        self.assertEqual(len(collect_files([str(TEST_FILES)])), 10)

    def test_json_output_is_parseable(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main([fixture('missing_name.drawio'), '--format', 'json'])
        report = json.loads(buffer.getvalue())
        self.assertEqual(report['total_errors'], report['files'][0]['summary']['errors'])

    def test_warnings_alone_do_not_fail_the_run(self):
        self.assertEqual(
            main([fixture('c4.drawio'),
                  '--known-applications', str(APPLICATIONS_CSV)]), 0)


if __name__ == "__main__":
    unittest.main()

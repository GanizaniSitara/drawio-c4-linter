"""Command line interface for the C4 draw.io linter."""
import argparse
import json
import logging
import os
import sys

from drawio_c4_lint.c4_lint import C4Lint, XMLParseException


def collect_files(paths):
    """Expand the given files and directories into a sorted list of .drawio files."""
    files = []
    for path in paths:
        if os.path.isdir(path):
            for root, _, names in os.walk(path):
                files.extend(os.path.join(root, name)
                             for name in names if name.endswith('.drawio'))
        else:
            files.append(path)
    return sorted(files)


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        prog='c4lint',
        description='Lint C4 diagrams drawn in draw.io.')
    parser.add_argument(
        'paths', nargs='+',
        help='.drawio files, or directories to search for them')
    parser.add_argument(
        '--known-applications', metavar='CSV',
        help="CSV with a 'Business Application Name' column; system names not on the "
             "list are reported as warnings with the closest matches")
    parser.add_argument(
        '--check-filenames', action='store_true',
        help="require filenames of the form 'C4 L<level> <system name>.drawio'")
    parser.add_argument(
        '--include-ids', action='store_true',
        help='include the draw.io element id in each finding')
    parser.add_argument(
        '--format', choices=['text', 'json', 'structurizr'], default='text',
        help='text report (default), machine-readable JSON, or Structurizr DSL')
    parser.add_argument(
        '--quiet', action='store_true',
        help='only report files that have findings')
    parser.add_argument(
        '--skip-non-c4', action='store_true',
        help='ignore files that contain no C4 objects')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='verbose logging')
    return parser.parse_args(argv)


def lint_file(path, args):
    return C4Lint(
        path,
        include_ids=args.include_ids,
        structurizr=(args.format == 'structurizr'),
        known_applications=args.known_applications,
        check_filename=args.check_filenames,
    )


def main(argv=None):
    args = parse_arguments(argv)
    logging.getLogger('drawio_c4_lint.c4_lint').setLevel(
        logging.DEBUG if args.verbose else logging.WARNING)

    # diagram names are often non-ASCII; do not die on a legacy console codepage
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    files = collect_files(args.paths)
    if not files:
        sys.exit('no .drawio files found')

    reports = []
    total_errors = 0
    failed = []

    for path in files:
        try:
            lint = lint_file(path, args)
        except XMLParseException as exc:
            failed.append({'file': path, 'error': str(exc)})
            continue

        if args.skip_non_c4 and not lint.is_c4():
            continue

        counts = lint.summary()
        total_errors += counts['errors']
        reports.append((path, lint, counts))

    if args.format == 'json':
        print(json.dumps({
            'files': [{
                'file': path,
                'summary': counts,
                'errors': lint.errors,
                'warnings': lint.warnings,
            } for path, lint, counts in reports],
            'unreadable': failed,
            'total_errors': total_errors,
        }, indent=2))
    elif args.format == 'structurizr':
        for path, lint, _ in reports:
            print(f'# {path}')
            print(lint.to_structurizr())
    else:
        for path, lint, counts in reports:
            if args.quiet and not counts['errors'] and not counts['warnings']:
                continue
            print(lint)
        for failure in failed:
            print(f"Could not read {failure['file']}: {failure['error']}")
        print(f"{len(reports)} file(s) linted, {total_errors} error(s), "
              f"{len(failed)} unreadable.")

    return 1 if total_errors or failed else 0


if __name__ == '__main__':
    sys.exit(main())

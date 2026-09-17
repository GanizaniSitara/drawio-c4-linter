# drawio_c4_lint

A linter for C4 diagrams drawn in draw.io.

C4 diagrams carry their meaning in element properties — `c4Name`, `c4Type`,
`c4Description`, `c4Technology` — and draw.io will happily let you leave any of them
blank. In a large estate that is how diagram sets rot: they look right and describe
nothing. This reads the `.drawio` XML and reports what is missing, with an exit code, so
diagram standards can be enforced by a build rather than by review.

## Installation

```
pip install -e .
```

That puts a `c4lint` command on the path. `pip install -e .[analysis]` adds the
dependencies for the network analysis script.

## Usage

```
c4lint diagram.drawio
c4lint diagrams/ another/directory
```

Directories are searched recursively for `.drawio` files. The command exits `1` if any
diagram has errors and `0` otherwise, so it drops into CI or a pre-commit hook:

```
c4lint --quiet diagrams/ || exit 1
```

```
############################################################
C4 Linter Input: diagrams/payments.drawio

  === Systems ===
  ERROR: 'c4Description' property missing ---  c4Name: Payments, c4Type: Software System
  ERROR: Software System (c4Name: Ledger) is not connected by any relationship.

  === Summary ===
  2 error(s), 0 warning(s).
  6 C4 object(s), 1 non-C4 object(s).
```

### Options

| Option | Effect |
|---|---|
| `--known-applications CSV` | Warn when a system name is not on a list of known applications, suggesting near misses |
| `--check-filenames` | Require filenames of the form `C4 L<level> <system name>.drawio` |
| `--include-ids` | Include the draw.io element id in each finding, so you can find it on the canvas |
| `--format text\|json\|structurizr` | Human report, machine-readable JSON, or a Structurizr DSL workspace |
| `--quiet` | Only print files that have findings |
| `--skip-non-c4` | Ignore files containing no C4 objects |

## What it checks

- Missing `c4Name`, `c4Type` or `c4Description` on systems and actors.
- Missing `c4Description` or `c4Technology` on relationships.
- Elements that no relationship connects to.
- Objects that are not C4 objects at all, counted so you can see how much of a diagram
  is decoration.
- Optionally, whether each system name is one of your known applications.
- Optionally, the filename convention.

Errors fail the run. Unknown application names are warnings and do not.

## Known applications

```
c4lint diagrams/ --known-applications applications.csv
```

The CSV needs a `Business Application Name` column. Matching ignores case, and a name
that is close but not exact is reported with the spelling it should have had:

```
  WARN: 'Payment Gatway' is not a known application. Did you mean Payment Gateway?
```

This is the check that catches the same system appearing under four spellings across a
diagram set. The included `applications.csv` is dummy data.

## Structurizr output

```
c4lint diagram.drawio --format structurizr
```

```
workspace {

    model {
        systemName = softwareSystem "System name" "Description of software system."
        externalSystemName = softwareSystem "External system name" "Description of external software system."
        systemName -> externalSystemName "Makes API calls" "JSON/HTTP"
    }
}
```

A diagram someone drew by hand becomes a text model you can diff, review and keep in
version control.

## Using it as a library

```python
from drawio_c4_lint.c4_lint import C4Lint

lint = C4Lint("diagram.drawio")
if lint.has_errors():
    print(lint)                 # the report above
print(lint.summary())           # {'errors': 2, 'warnings': 0, ...}
print(lint.lint())              # findings keyed by Systems / Actors / Relationships / Other
print(lint.to_model())          # elements and relationships as plain data
```

## Network analysis

`python -m drawio_c4_lint.analyze_network path/to/diagrams` builds a graph across a
directory of diagrams and reports how many systems and connections exist, whether the
estate is connected, and what the disconnected components are. Needs the `analysis`
extra.

## Tests

```
cd drawio_c4_lint
python -m pytest test_lint.py
```

The fixtures in `test_files/` are one diagram per defect, which also makes them the
readable specification of what each rule catches.

## Licence

BSD 3-Clause. See [LICENSE](LICENSE).

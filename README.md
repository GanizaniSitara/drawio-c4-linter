# drawio_c4_lint

A linter for C4 diagrams drawn in draw.io.

C4 diagrams carry their meaning in element properties — `c4Name`, `c4Type`,
`c4Description`, `c4Technology` — and draw.io will happily let you leave any of them
blank. In a large estate that is how diagram sets rot: they look right and describe
nothing. This reads the `.drawio` XML and reports what is missing, so diagram standards
can be enforced mechanically rather than by review.

## What it checks

- Missing `c4Name`, `c4Type` or `c4Description` on systems and actors.
- Missing `c4Description` or `c4Technology` on relationships.
- Elements that no relationship connects to.
- Objects in the file that are not C4 objects at all, reported as a count so you can see
  how much of a diagram is decoration.
- Optionally, whether each system name appears in a supplied list of known applications,
  with a fuzzy match so near-misses are reported rather than passing silently.
- Optionally, a filename convention (`C4 L<level> <system name>.drawio`).

## Usage

Lint every diagram under a directory, from the repository root:

```
python -m drawio_c4_lint.c4_lint_on_directory path/to/diagrams
```

Or use it directly:

```python
from drawio_c4_lint.c4_lint import C4Lint

lint = C4Lint("diagram.drawio")
print(lint)              # human-readable report
errors = lint.lint()     # dict keyed by Systems / Actors / Relationships / Other
```

Findings are grouped by Systems, Actors, Relationships and Other:

```
  === Systems ===
  ERROR: 'c4Description' property missing ---  c4Name: System Name, c4Type: Software System
  ERROR: Software System (c4Name: System Name) is not connected by any relationship.

  === Summary ===
  1 C4 objects, 0 non-C4 objects found.
```

### Known applications

`C4Lint(..., known_applications='applications.csv')` matches every system name against a
CSV column named `Business Application Name`, exactly first, then by close match. The
included `applications.csv` is dummy data.

### Structurizr output

`C4Lint(..., structurizr=True)` emits the parsed model as Structurizr DSL, which is a
way to get from a hand-drawn diagram to a text model you can diff.

### Network analysis

`python -m drawio_c4_lint.analyze_network path/to/diagrams` builds a graph across a
directory of diagrams and reports how many systems and connections exist, whether the
estate is connected, and what the disconnected components are.

## Requirements

Python 3.10+ and the packages in `requirements.txt`. `networkx` and `matplotlib` are
only needed for `analyze_network.py`.

## Tests

```
cd drawio_c4_lint
python -m pytest test_lint.py
```

The fixtures in `test_files/` are one diagram per defect, which also makes them the
readable specification of what each rule catches.

## Licence

BSD 3-Clause. See [LICENSE](LICENSE).

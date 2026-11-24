# brash

[![CI][ci-badge]][ci]
[![Documentation][docs-badge]][docs]
[![PyPI][pypi-badge]][pypi]
[![Python versions][python-badge]][pypi]
[![License][license-badge]][license]

[ci-badge]: https://github.com/eddieland/brash/actions/workflows/ci.yml/badge.svg?branch=main
[ci]: https://github.com/eddieland/brash/actions/workflows/ci.yml?query=branch%3Amain
[docs-badge]: https://readthedocs.org/projects/brash/badge/?version=latest
[docs]: https://brash.readthedocs.io
[pypi-badge]: https://img.shields.io/pypi/v/brash
[pypi]: https://pypi.org/project/brash/
[python-badge]: https://img.shields.io/pypi/pyversions/brash
[license-badge]: https://img.shields.io/pypi/l/brash
[license]: https://github.com/eddieland/brash/blob/main/LICENSE

![brash](https://github.com/user-attachments/assets/bf0d5df8-235d-4962-8e27-c2b6a32ae684)

Codemods that hold a Python codebase to its conventions. A linter can only report that a module constant is not
`Final` or that a parameter is typed `list` where `Iterable` would do; brash rewrites the file. It is built on
[LibCST](https://libcst.readthedocs.io), which keeps every comment and blank line a rewrite does not touch.

brash is meant to run twice in a project, as a formatter does: once to apply (`brash .`, in the step that formats)
and once to check (`brash --check .`, in the lint), so the repository stays as the codemods leave it and a change that
drifts fails CI with the diff that fixes it. It came out of [canopy](https://github.com/eddieland/canopy), whose own
code is held to it.

## Install

brash needs Python 3.12 or later. Add it to a project as a dev dependency, or run it without installing:

```sh
uv add --dev brash        # or: pip install brash
uvx brash --check .       # run it once, installing nothing
```

## Usage

```sh
brash .                                   # rewrite every Python file under the directory
brash --check .                           # change nothing: print the diff, exit 1 if there is one
brash --only final-constants src/app.py   # one codemod, one file; give --only again for each
brash --list                              # the codemods, brash's own and the project's
```

A directory gives its `.py` files and its scripts that open with a Python shebang, but nothing under a hidden
directory, `node_modules`, `site-packages`, a `venv`, or a build's output. A file named outright is taken as it is,
whatever its name, which is how a git hook runs brash on a commit's files. Neither gives a file the project
[excludes](#configuration).

The exit code is 0 when there is nothing to report, 1 when `--check` found a file a codemod would rewrite or a file
could not be rewritten (a syntax error, say, reported by name), and 2 for a usage error.

Run brash before the formatter: a codemod adds an import where LibCST puts it and writes code unformatted, and
`ruff check --select I --fix` and `ruff format` (or isort and black) then put both right. In a Makefile:

```make
fmt:
	uv run brash .
	uv run ruff check --select I --fix .
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run brash --check .
```

Every codemod runs by default but one that says it is off by default, which of brash's own is `explicit-override`,
for a convention few projects hold. A project turns one off, or names the few it wants, with `ignore`, `select` and
`extend-select` in its [configuration](#configuration); `--only` names the ones for a single run, and is taken in
place of them. Its `per-file-ignores` there turns one off for some files alone.

A project whose code runs on a Python older than 3.12 sets its `target-version`, and a codemod that writes syntax
that Python does not have, which is `type-aliases` or `explicit-override`, does not run; `--target-version py310`
says it for a single run.

## Configuration

A project configures brash in its `pyproject.toml`, under `[tool.brash]`. Every setting is optional:

```toml
[tool.brash]
target-version = "py310"
ignore = ["general-params"]
exclude = ["src/app/_generated", "*_pb2.py"]

[tool.brash.per-file-ignores]
"tests/*" = ["general-params"]

[tool.brash.codemods]
no-print = "codemods.no_print:NoPrint"
```

- **`select`** is an allowlist: the codemods that run, by name, and no other. Left out, every codemod runs but one
  off by default, so a release of brash that adds one runs it; with `select`, a new one waits to be named.
- **`extend-select`** names codemods that run as well: added to those of `select`, or, where there is no `select`,
  to those that run by default. It is how a project turns on a codemod that is off by default, and still runs each
  one a release of brash adds.
- **`ignore`** is a blocklist: the codemods that do not run. With the others, a run has the codemods of `select`
  and `extend-select` that `ignore` does not name. Each takes your project's own codemods as it takes brash's, and
  a name no codemod has fails the run. The order codemods run in is brash's, whatever the list's. `--only` on the
  command line is taken in place of all three, so it runs an ignored codemod, and `--list` lists every codemod, on
  or off, and says which are off by default.
- **`per-file-ignores`** turns codemods off for some files alone: each key is a glob pattern, as `exclude`'s are and
  matching what one would, and its value the codemods that do not run on the files it matches. A file that several
  patterns match is rewritten by none of the codemods any of them names. It holds for a file named outright, and for
  a codemod `--only` names: `--only` runs it on the project's other files. A name no codemod has fails the run.
- **`target-version`** is the oldest Python the project's code runs on, as ruff spells it: `py310` for 3.10. A
  codemod whose output needs a later Python does not run, named by `--only` or not. Left out, every codemod runs,
  whatever the project's `requires-python`: brash does not read it. `--target-version` on the command line is taken
  in place of it.
- **`exclude`** lists the files and directories no codemod rewrites, such as generated code, as glob patterns of
  paths relative to the directory that holds the `pyproject.toml`. A pattern excludes the file or directory it
  matches, and everything under that directory. Its `*` matches any run of characters, slashes among them, so
  `*_pb2.py` excludes such a file at any depth and `top.py` only the one beside the `pyproject.toml`. An excluded
  file is left alone when it is named outright too, as a git hook names it.
- **`codemods`** registers [your project's own codemods](#your-projects-own-codemods).

A project that keeps each tool's settings in a file of its own has a `brash.toml` instead, with the same settings at
its top level, and no `[tool.brash]` above them:

```toml
target-version = "py310"
ignore = ["general-params"]
exclude = ["src/app/_generated", "*_pb2.py"]

[per-file-ignores]
"tests/*" = ["general-params"]

[codemods]
no-print = "codemods.no_print:NoPrint"
```

brash reads the nearest `brash.toml` or `pyproject.toml`, in the directory it runs from or one above it, and the
`brash.toml` where a directory holds both: the `[tool.brash]` beside it is not read. What is said here of the
`pyproject.toml`, such as what `exclude`'s patterns are relative to, is as true of a `brash.toml`. A setting it does
not have, or a value of the wrong type, fails the run with exit code 1 and a line for each, naming the file and the
key:

```text
Error: /repo/pyproject.toml: tool.brash.excludes: no such setting; there are `codemods`, `select`, `extend-select`, `ignore`, `per-file-ignores`, `target-version`, `exclude`
```

## As a git hook

brash is a hook for [pre-commit](https://pre-commit.com) and [prek](https://prek.j178.dev), which read the same
`.pre-commit-config.yaml`. List it before the formatter's hooks, for the reason it runs before the formatter:

```yaml
repos:
  - repo: https://github.com/eddieland/brash
    rev: v0.2.0 # the latest release
    hooks:
      - id: brash
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.5
    hooks:
      - id: ruff-check
        args: [--select, I, --fix]
      - id: ruff-format
```

`brash` rewrites the commit's Python files, and the runner stops the commit where one changed, for you to stage.
`brash-check` changes nothing and fails with the diff, for a run in CI. Either takes `args: [--only, final-constants]`.
In prek, a hook given a `priority` runs alongside the others that share it: give brash a lower one than the formatter.

The hook runs in an environment of its own, which holds brash and nothing of your project:

- **Your project's codemods run too**, read from the working tree as the command line reads them. One that imports a
  package other than `libcst` and `brash` names it in the hook's `additional_dependencies`. One that imports your
  project as installed needs your environment, which is a local hook:

  ```yaml
  repos:
    - repo: local
      hooks:
        - id: brash
          name: brash
          entry: uv run brash
          language: system
          types: [python]
          require_serial: true
  ```

- **The `pyproject.toml` is the one at the repository's root**, where a hook runs, so codemods registered in one
  below it, in `backend/pyproject.toml`, are not run. prek runs a hook from the directory of the configuration that
  names it: give `backend/` a `.pre-commit-config.yaml` of its own. For pre-commit, make the local hook's entry
  `bash -c 'cd backend && uv run brash "${@#backend/}"' --`, with `files: ^backend/`.

- **It needs Python 3.12 or later**: where the runner's default is older, set the hook's `language_version`.

## The codemods

- **`final-constants`** annotates every module constant `Final`, so the type checker refuses a second assignment:
  `LIMIT = 3` becomes `LIMIT: Final = 3`, and `NAMES: Sequence[str] = ()` becomes `NAMES: Final[Sequence[str]] = ()`.
  A constant is an `UPPER_CASE` name bound once, by an assignment among the module's own statements. It leaves alone
  a lowercase name, which is how a module spells an object with state of its own (`_log`, `router`); a name bound
  again anywhere in the module (a second assignment, `+=`, `del`, a function's `global`); an object made to hold
  state whatever its name, such as a logger or a lock; and a `TypeVar` or an explicit `TypeAlias`.
- **`type-aliases`** spells an implicit type alias as a `type` statement, which ruff does only for one annotated
  `TypeAlias`: `Outcome = Literal["packed", "failed"]` becomes `type Outcome = Literal["packed", "failed"]`. An alias
  is a `CamelCase` name bound once, among the module's own statements, to a `Literal`, a `tuple`, a `Callable`, or a
  union of types. A `type` statement makes a `TypeAliasType`, not the type it names, so it leaves alone a name the
  module reads outside an annotation (passed to `get_args` or `isinstance`, called, subclassed, held in another
  assignment); an `Annotated[...]` alias, whose metadata frameworks read as the program runs; and a union that may be
  of values, with no `None`, subscript, or builtin type in it. It leaves alone an alias with a quoted name as a member
  of a `Union[...]` or `Optional[...]`, since ruff then writes `str | "Text"`, which raises when the alias is read. It
  sees one module at a time: where another module reads a rewritten alias at run time, that reader takes its
  `__value__`. The `type` statement is Python 3.12's, so
  it does not run in a project whose [`target-version`](#configuration) is older.
- **`doc-comments`** writes the comment directly above a name as a Sphinx doc comment, which editors and doc tools
  attach to the name: `# How often a run is resumed.` above `MAX_RESUMES: Final = 3` becomes
  `#: How often a run is resumed.`. The names are a module's constants and type aliases, among its own statements, and
  the fields of a `@dataclass`, a `NamedTuple`, or an enum. It leaves alone a field of any other class, since a
  pydantic model's description is the docstring below its field and a `#` above one is a note kept out of the schema;
  a comment above a function, an import, or a lowercase module object; a block that holds a `#:` line already, a
  directive to a tool (`# noqa`, `# type:`, `# fmt:`), or a section's banner; and a comment a blank line separates
  from the name. It cannot tell what a name is from why the code is so, so a note of the second kind is written with
  a blank line below it, or beside the value. The colon can push a line past the line length, which the lint then
  reports.
- **`general-params`** widens a parameter annotated `list`, `dict`, `set`, or `frozenset` that its function only
  reads to the most general type its reads need: `def total(costs: list[float])` whose body only sums `costs` becomes
  `def total(costs: Iterable[float])`. One pass is `Iterable`; `len`, `in`, a truth test, or more than one pass is
  `Collection`; indexing, slicing, or `reversed` of a list is `Sequence`; a dict only read is `Mapping`; and a set
  tested with `in` is `AbstractSet`, never `Collection`. It is deliberately narrow, since a wrong widening fails the
  type checker at a call site: it leaves alone a parameter used in any way it does not know to be a read (mutated,
  stored, returned, yielded, compared, or passed to any call but a few builtins whose names the module does not bind),
  one bound again or named by a nested function, one never read, one whose function returns the type it takes, every
  parameter of a function with a decorator but a few plain ones (a click command, an override), and a method of a
  class with a base, or of one the module derives another class from, which may override or be overridden. The import
  goes under `if TYPE_CHECKING:` where the module has that block and postpones its annotations.
- **`empty-collections`** annotates an empty `[]`, `{}`, or `set()` that a function fills, which a strict pyright
  reports as partly unknown and no tool annotates: `found = []` that a function annotated `-> list[Path]` returns
  becomes `found: list[Path] = []`. The type comes from the return annotation, where the name is returned under its
  own type, an abstract one such as `Sequence[Path]`, or either `| None`, or returned through `sorted`, `list`,
  `tuple`, `set`, or `frozenset`; or from a string's `join`, which makes the items `str`. The rules that apply must
  agree. It leaves alone a name its function binds more than once, or uses in any way but a known few (filled by
  `.append` and its kin as a statement, stored to by `[k] =` or `del`, measured, tested, searched with `in`, joined,
  or returned), a return annotation that is quoted, an alias, a wider union, or names `Any`, an element type the
  function or its class binds, a generator, and a function with a checker's or a lint's directive on its header, on
  the assignment, or on the `return`. Python never evaluates a local's annotation, so nothing outside the function
  sees it.
- **`explicit-override`**, off by default, puts `@override` on a method that overrides one of a base class the module
  defines, so the type checker reports it once the base's is renamed; mypy, pyrefly, and basedpyright each report an
  override without it, and none writes it. It imports `override` from `typing` where the module has no import of it.
  A base is a class among the module's own statements, bound once, above the class that derives from it, with no
  decorator but one that hands the class back (`dataclass`, `final`, `total_ordering`, `runtime_checkable`); a method
  overrides when such a base, directly or through its own, defines it once. So most overrides, of a base imported
  from elsewhere, are not marked. It leaves alone a method with a decorator, one its class binds again, `__init__` and
  `__new__`, one with an unannotated parameter, whose type pyrefly would then take from the base's, and one with a
  checker's or a lint's directive on or above its header, and a module with a star import or another binding of
  `override`. `typing.override` is Python 3.12's, so it does not run where the
  [`target-version`](#configuration) is older.

Each is opinionated, and each is conservative: where it cannot be sure a rewrite is right, it leaves the code alone
and reports nothing. The cases each one is held to are Python snippets, before and after, in
[`tests/cases/`](https://github.com/eddieland/brash/tree/main/tests/cases).

## Your project's own codemods

A convention that only your project has, such as naming an enum's member where its code compares a bare string, is a
codemod of your own that brash runs with its own. Register it in the project's `pyproject.toml`, or in the
`[codemods]` of its `brash.toml`, under the name the command line takes, as the module that holds it and the
class's name there:

```toml
[tool.brash.codemods]
no-print = "codemods.no_print:NoPrint"
```

The module is imported as any other is: from the environment brash runs in, or from the directory that holds the
`pyproject.toml`, which brash puts last on the import path, so `codemods/no_print.py` beside it is found without
being installed. A project's
codemods run after brash's own, in the table's order, and `--only` and `--list` take them as they take brash's.

The class is a `brash.command.Command`, which is a
[`libcst.codemod.VisitorBasedCodemodCommand`](https://libcst.readthedocs.io/en/latest/codemods.html): its `visit_`
and `leave_` methods rewrite the tree, and `AddImportsVisitor.add_needed_import` adds an import it needs.

```python
import libcst as cst
from brash.command import Command


class NoPrint(Command):
    """Remove every `print(...)` statement."""

    DESCRIPTION = "Remove `print` statements."

    @classmethod
    def wants(cls, source: str) -> bool:
        return "print(" in source

    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr) -> cst.Expr | cst.RemovalSentinel:
        match updated_node.value:
            case cst.Call(func=cst.Name(value="print")):
                return cst.RemoveFromParent()
            case _:
                return updated_node
```

Two rules keep the check honest and quick, for your codemods as for brash's:

- **A codemod leaves alone what it wrote.** `--check` fails on any diff, so a second run over its own output must
  change nothing, also once the formatter has sorted the imports and formatted the result.
- **Say cheaply when a file is not yours.** Parsing a module with LibCST and visiting it takes a few hundred times as
  long as reading it, and the lint runs every codemod over every file. `Command.wants(source)` answers from the text
  alone, before anything is parsed: `final-constants` decides from the stdlib's `ast`, so a file with no constant
  left to annotate is never parsed by LibCST. A codemod without a `wants` parses every file on every lint. A codemod
  held to some files alone says which in `Command.covers(filename)`, asked before the text is read.

A codemod that writes syntax an older Python does not have names the first that has it, as `MINIMUM_PYTHON = (3, 12)`
on the class, and does not run in a project whose `target-version` is older. One for a convention a project
chooses to hold, which most do not, says so as `OPT_IN = True`: it is off by default, and runs only where `select`
or `extend-select` names it, or `--only` does.

To test one, run a module's text through it: `brash.run.rewrite(source, ["no-print"], codemods={"no-print": NoPrint})`
gives the text back rewritten.

A rewrite to run once, such as a migration off an API, needs no entry: LibCST's own
[`python -m libcst.tool codemod`](https://libcst.readthedocs.io/en/latest/codemods_tutorial.html) runs it, and you
commit the result.

### An example: canopy's `vocab-members`

[canopy](https://github.com/eddieland/canopy) keeps its statuses, kinds, and phases as `StrEnum`s in one module,
`core/vocab.py`. A member of a `StrEnum` is the string it holds, so `run.status == "running"` type-checks and works,
and no linter catches the bare string where the code is meant to name the member. canopy's own codemod rewrites it:

```python
if run.status == "running":           # before
if run.status == RunStatus.RUNNING:   # after, with RunStatus imported
```

It is one module, [`codemods/vocab_members.py`](https://github.com/eddieland/canopy/blob/main/codemods/vocab_members.py),
at the root of canopy's repository, and one entry in its `pyproject.toml`:

```toml
[tool.brash.codemods]
vocab-members = "codemods.vocab_members:VocabMembers"
```

Three things in it are worth copying:

- **It reads the project, without importing it.** The vocabularies are whatever `core/vocab.py` holds today, read
  with the stdlib's `ast` from a path relative to the codemod's own file. A new member needs no change to the codemod,
  and nothing of canopy is imported or run to lint it.
- **It says which files are its own.** `covers(filename)` is true under `src/canopy` alone: the tests assert on the
  string on purpose, and the vocabulary's own module defines it.
- **It rewrites only what it can tie down.** A string becomes a member where the other side of the comparison is
  annotated with one vocabulary, or is a field of a typed row. A string several vocabularies hold, with nothing to
  say which is meant, is left alone, as is any string outside a comparison.

Its tests are before-and-after snippets in Markdown, the same shape as brash's own in `tests/cases/`.

### Other things a project's codemod can do

A codemod of your own fits wherever a review comment keeps being written and the fix is always the same edit. It
sees one module at a time, as text and syntax, and may read other files of the project to learn its names.

- **Keep a migration finished.** Once every caller has moved from `old_client.get(...)` to `client.fetch(...)`, a
  codemod that rewrites the old call keeps a new one from landing: the lint fails with the fix as its diff.
- **Send calls through the project's own seam.** `subprocess.run(...)` becomes `procs.run(...)`, `datetime.now()`
  becomes `clock.now()`, `print(...)` becomes `log.info(...)`: wherever the project has one module that is allowed
  to touch something and wants every other module to go through it.
- **Name a constant where a string is repeated.** Feature flags, config keys, route names, metric names: read the
  names from the module or file that declares them, as `vocab-members` does, and rewrite the bare string that
  equals one, in the calls that take them.
- **Import from the public module.** Rewrite `from app.billing._internal import Invoice` to
  `from app.billing import Invoice` where the package re-exports the name, so a private module can move.
- **Hold tests to one way of doing a thing.** `from unittest.mock import patch` becomes `from unittest import mock`
  with `mock.patch` at each use; a `time.sleep` in a test becomes the project's `wait_until`. `covers` holds it to
  `tests/`.
- **Spell a framework's idiom one way.** A logging call with an f-string becomes one with `%s` arguments; a
  `@pytest.fixture()` loses its empty parentheses; a `Depends(get_db)` parameter gets the project's `Annotated`
  alias.
- **Add what every module must have.** A `from __future__ import annotations`, a license header, a module logger
  named for `__name__`.

What does not fit: a rewrite that needs to know a value's type across modules, which is a type checker's question,
and one that changes what the code does in a way a person should decide each time.

## Adding a codemod to brash

A codemod belongs in brash when it holds code to a convention any Python project could adopt, and reads nothing but
the module it rewrites.

1. Write a module in `src/brash/` holding a subclass of `command.Command`, with a `DESCRIPTION`.
2. Add it to `registry.CODEMODS` under the name the command line takes.
3. Test it in `tests/`, with its cases as Python snippets in `tests/cases/<name>.md`: under a `###` heading, two
   `python` blocks are a module's text before and after, and one is text it must leave alone. `helpers.cases(name)`
   reads them for the test module, which runs each through `run.rewrite(source, [name])`. ruff does not format that
   file, so a snippet stays as the codemod writes it.
4. Describe it in this README, under The codemods.
5. Run `make fmt` and commit what it rewrote, since brash runs on its own code and the lint fails from then on
   wherever it would still change a file.

## Development

```sh
uv sync      # install brash and its dev tools
make fmt     # brash on its own code, then ruff and rumdl
make lint    # every formatter's check, ruff, brash --check, pyrefly, rumdl, actionlint, zizmor
make test    # pytest
make docs    # the documentation, into docs/_build/html
```

[AGENTS.md](https://github.com/eddieland/brash/blob/main/AGENTS.md) holds the conventions.
[Read the Docs](https://brash.readthedocs.io) builds `docs/` on every push: this README, and the API a project's
codemod is written against. A release is a `v*` tag:
the Publish workflow builds it, with the tag as its version, and publishes it to PyPI. The Tag workflow, run by hand,
creates the tag on the head of `main` or a branch it is given: the next major, minor or patch version, or an exact
tag.

## License

MIT.

# AGENTS.md

Instructions for any agent working in this repository. Humans should read it too.

brash is a command line that rewrites Python with codemods, and checks that none has anything left to rewrite. Read
`README.md` first: what each codemod does, how a project registers its own, and how to add one here.

## How to work

- Small PRs. One concern per PR. Conventional commit messages.
- A codemod's behaviour is its cases: a change to what one rewrites or leaves alone changes `tests/cases/<name>.md`
  and its paragraph in `README.md` in the same PR.
- brash is a published library. A change to what other projects rely on (the command's flags and exit codes,
  `[tool.brash]`, `brash.command.Command`, `brash.run.rewrite`) says so in its PR.
- A codemod here reads nothing but the module it rewrites, so it works in any project. One that reads a project's
  own files is that project's, registered in its `pyproject.toml`.
- When unsure, prefer the smaller change and leave a note in the PR. Do not invent requirements.

## Toolchain

- Python 3.12+. Package layout `src/brash/`. CLI entry point `brash`.
- `uv` for everything: `uv sync`, `uv run`. `hatchling` builds it, and the version comes from the latest `v*` tag.
- Runtime dependencies are `click`, for the command line (never argparse), `libcst`, and `pydantic`, for
  `[tool.brash]`: a setting is a field of `brash.config.Config`. Adding a fourth makes every project that installs
  brash install it too: do it only when the stdlib makes the code materially worse, and say why in the PR. A
  dev-only tool gets a comment where it is configured saying what it is for.
- `make fmt`, then `make lint` and `make test`, before pushing: all three take seconds. `make check` is lint and test,
  and never rewrites files. CI runs the lint, and the tests under each supported Python.
- `make fmt` runs brash on its own code first, then ruff (imports, trailing commas, format) and rumdl. `make lint`
  fails with the diff where a codemod would still change a file.
- ruff selects every stable rule, and preview rules named one by one. Opt out with a commented `ignore` entry or a
  `noqa` with a code; never narrow `select`. `pyrefly` type-checks in strict mode. `pytest` runs in strict mode,
  where a warning fails the test that raised it. `rumdl` lints and formats Markdown; `actionlint` and `zizmor` lint
  the workflows, where every action is pinned to a commit.

## Formatting

Maximum line length is 120 characters, for every file type: Python (ruff), Markdown (rumdl), and the rest
(`.editorconfig`). Do not reflow existing text to fill 120 columns; wrap new or edited prose at 120. The exceptions
are lines that cannot be broken: long URLs, Markdown tables and code blocks.

## Code conventions

These are the conventions brash's codemods apply, and a few they cannot.

- Fully typed, `pyrefly` strict clean, the tests included.
- A public module, class, or function has a Google docstring, with Returns, Yields, and Raises sections that match
  its body. Every docstring opens with a one-line summary ending in a period.
- A parameter takes the most general type its body needs (`Iterable`, `Collection`, `Sequence`, `Mapping`,
  `AbstractSet`); a return keeps the concrete type it builds. `general-params` widens what it can prove.
- A module constant is `UPPER_CASE` and `Final` (`final-constants`); a type alias is a `type` statement
  (`type-aliases`).
- A comment that says what a constant, a type alias, a dataclass or `NamedTuple` field, or an enum member is, is a
  `#:` doc comment directly above it (`doc-comments`). A note on why the code is so stays a plain `#`, with a blank
  line below it or beside the value.
- A frozen dataclass holds no mutable collection type.
- Modules are in newspaper order: the docstring, what Python needs at import time, the public names, most important
  first, then the private helpers, each below the first function that calls it.
- No global mutable state.
- A codemod decides from the module's text and syntax alone: it never imports or runs the code it rewrites.

## Testing

- A codemod's cases are Python snippets in `tests/cases/<name>.md`, read by `tests/helpers.py`: two `python` blocks
  under a `###` heading are before and after, one is text it must leave alone. A new case goes there, not in an
  escaped string in a test module.
- Every codemod leaves alone what it wrote: its test runs each case's output through it again, and `wants` says no
  to it.
- Patch with `unittest.mock`, as context managers, never pytest's `monkeypatch`; a mock is specced. Import the
  namespace: `from unittest import mock`.
- Every test directory has an `__init__.py`, so the tests import `tests.helpers`. A test module imports from no
  other test module.
- A test waits on a condition, never on time.

## Definition of done for a PR

- `make lint` and `make test` pass, and CI passes.
- New behavior has a test.
- `README.md` describes what changed, where it describes that part.

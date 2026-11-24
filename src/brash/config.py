"""What a project sets for brash, in the `[tool.brash]` table of its `pyproject.toml` or in a `brash.toml`.

    [tool.brash]
    target-version = "py310"
    ignore = ["general-params"]
    exclude = ["src/app/_generated", "*_pb2.py"]

    [tool.brash.per-file-ignores]
    "tests/*" = ["general-params"]

    [tool.brash.codemods]
    vocab-members = "codemods.vocab_members:VocabMembers"

A `brash.toml` holds the same settings at its top level, with no `[tool.brash]` above them:

    target-version = "py310"
    ignore = ["general-params"]
    exclude = ["src/app/_generated", "*_pb2.py"]

    [per-file-ignores]
    "tests/*" = ["general-params"]

    [codemods]
    vocab-members = "codemods.vocab_members:VocabMembers"

The project is the nearest directory, the one brash runs from or one above it, that holds either file, and the
`brash.toml` is the one read where it holds both. The settings are a `Config`: one it does not have, or a value of
the wrong type, fails the run with the key it is at.
"""

import re
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Annotated, Final

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError
from pydantic_core import ErrorDetails, PydanticCustomError

#: The file a project configures brash in by itself, with the settings at its top level.
DEDICATED: Final = "brash.toml"
#: The file a project configures brash in beside its other tools, under `[tool.brash]`.
SHARED: Final = "pyproject.toml"
#: Both, in the order brash looks for them in a directory.
CONFIGS: Final = (DEDICATED, SHARED)
_ENTRY: Final = re.compile(r"[^\W\d]\w*(\.[^\W\d]\w*)*:[^\W\d]\w*")
_TARGET: Final = re.compile(r"py3(\d{1,2})")


def _module_and_class(entry: str) -> str:
    if not _ENTRY.fullmatch(entry):
        raise PydanticCustomError("codemod_entry", "`{entry}` is not a `module:Class`", {"entry": entry})
    return entry


def _target(target: str) -> str:
    try:
        python(target)
    except ValueError as e:
        raise PydanticCustomError("target_version", "{problem}", {"problem": str(e)}) from e
    return target


class Config(BaseModel):
    """The `[tool.brash]` table, or a `brash.toml`: every setting a project has, each optional."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_attribute_docstrings=True)

    codemods: Mapping[str, Annotated[str, AfterValidator(_module_and_class)]] = Field(default_factory=dict)
    """The project's own codemods, by the name the command line takes, each as its `module:Class`.

    They run after brash's own, in the table's order.
    """
    select: tuple[str, ...] | None = None
    """The codemods that run, by name, brash's own or the project's: an allowlist.

    When it is not set, every codemod runs but those off by default (`OPT_IN`). They run in brash's order whatever the
    list's, and `--only` on the command line is taken in place of it.
    """
    extend_select: tuple[str, ...] = Field(default=(), alias="extend-select")
    """The codemods that run as well, by name: added to those of `select`, or to those that run by default."""
    ignore: tuple[str, ...] = ()
    """The codemods that do not run, by name: a blocklist, taken from those `select` and `extend-select` leave on."""
    per_file_ignores: Mapping[str, tuple[str, ...]] = Field(default_factory=dict, alias="per-file-ignores")
    """The codemods that do not run on some files, by name, under a glob pattern of the files' paths.

    A pattern is one of `exclude`'s, and matches what it would. A file that several match is rewritten by none of
    the codemods any of them names, and `--only` on the command line does not run one on such a file.
    """
    target_version: Annotated[str, AfterValidator(_target)] | None = Field(default=None, alias="target-version")
    """The oldest Python the project's code runs on, as `py310` for 3.10. Every codemod runs, when it is not set.

    A codemod whose `MINIMUM_PYTHON` is later does not run, and `--target-version` on the command line is taken in
    place of it.
    """
    exclude: tuple[str, ...] = ()
    """Files and directories no codemod rewrites, as glob patterns of paths relative to the project's directory.

    A pattern excludes the file or directory it matches, and everything under that directory. Its `*` matches any run
    of characters, slashes among them, so `*_pb2.py` excludes such a file at any depth.
    """


@dataclass(frozen=True)
class Project:
    """A project's configuration, and where it was read."""

    #: The directory that holds the file it was read from, resolved, or None when the run is in no project.
    root: Path | None
    config: Config
    #: The name of that file: one of `CONFIGS`.
    file: str = SHARED

    def setting(self, *keys: object) -> str:
        """Where a setting is, for a message about it.

        Returns:
            The file's path, then the key the setting is at in it: under `tool.brash` in a `pyproject.toml`.
        """
        return f"{self.root / self.file if self.root else self.file}: {_key(self.file, keys)}"

    def excludes(self, path: Path) -> bool:
        """Whether the project's `exclude` keeps the codemods off the file at `path`.

        Returns:
            True for a file under the project's directory that a pattern matches, itself or a directory above it.
        """
        candidates = self._candidates(path) if self.config.exclude else ()
        return any(_matches(candidates, pattern) for pattern in self.config.exclude)

    def ignored(self, path: Path) -> frozenset[str]:
        """The codemods the project's `per-file-ignores` keeps off the file at `path`.

        Returns:
            Their names: those under each pattern that matches the file, itself or a directory above it, and none
            for a file outside the project's directory.
        """
        table = self.config.per_file_ignores
        candidates = self._candidates(path) if table else ()
        return frozenset(name for pattern, names in table.items() if _matches(candidates, pattern) for name in names)

    def _candidates(self, path: Path) -> list[str]:
        """What a pattern is matched against for the file at `path`.

        Returns:
            The file's path relative to the project's directory, then each directory above it there, or nothing for
            a file that is not under it.
        """
        if self.root is None:
            return []
        try:
            relative = path.resolve().relative_to(self.root)
        except ValueError:
            return []
        return [relative.as_posix(), *(parent.as_posix() for parent in relative.parents[:-1])]


class ConfigError(Exception):
    """A project's `brash.toml` or `pyproject.toml` does not parse, or its settings are not a `Config`."""


def load(start: Path) -> Project:
    """Read the configuration of the project a run from the directory `start` is in.

    Returns:
        The project, with every setting at its default when neither file is found, or the one found is a
        `pyproject.toml` with no `[tool.brash]`.

    Raises:
        ConfigError: When the file does not parse, or holds a setting or a value brash does not take. The message
            has a line for each, with the file and the key.
    """
    start = start.resolve()
    candidates = (d / name for d in (start, *start.parents) for name in CONFIGS)
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        return Project(None, Config())
    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise ConfigError(f"{path}: {e}") from e
    try:
        return Project(path.parent, Config.model_validate(_table(document, path.name)), path.name)
    except ValidationError as e:
        raise ConfigError("\n".join(f"{path}: {_problem(error, path.name)}" for error in e.errors())) from e


def python(target: str) -> tuple[int, int]:
    """The Python version a target names: `py310` is 3.10.

    Returns:
        The major and minor version.

    Raises:
        ValueError: When the text names no version of Python 3.
    """
    match = _TARGET.fullmatch(target)
    if match is None:
        raise ValueError(f"`{target}` is not a Python version such as `py310`")
    return 3, int(match[1])


def _matches(candidates: Iterable[str], pattern: str) -> bool:
    return any(fnmatchcase(candidate, pattern.rstrip("/")) for candidate in candidates)


def _table(document: Mapping[str, object], file: str) -> object:
    """What the file of that name sets for brash: all a `brash.toml` holds, or a `pyproject.toml`'s `[tool.brash]`.

    Returns:
        The settings, not yet validated: none when a `pyproject.toml` has no such table.
    """
    if file == DEDICATED:
        return document
    tool = document.get("tool")
    empty: dict[str, object] = {}
    return tool.get("brash", empty) if isinstance(tool, dict) else empty


def _problem(error: ErrorDetails, file: str) -> str:
    """One thing wrong with the settings, as the key it is at in the file of that name and what is wrong there.

    Returns:
        The line, without the file's name.
    """
    key = _key(file, error["loc"])
    if error["type"] == "extra_forbidden":
        return f"{key}: no such setting; there are {', '.join(f'`{name}`' for name in _settings())}"
    return f"{key}: {error['msg']}"


def _key(file: str, keys: Iterable[object]) -> str:
    return ".".join((*(() if file == DEDICATED else ("tool", "brash")), *map(str, keys)))


def _settings() -> list[str]:
    return [field.alias or name for name, field in Config.model_fields.items()]

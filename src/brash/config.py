"""What a project sets for brash, in the `[tool.brash]` table of its `pyproject.toml`.

    [tool.brash]
    exclude = ["src/app/_generated", "*_pb2.py"]

    [tool.brash.codemods]
    vocab-members = "codemods.vocab_members:VocabMembers"

The project is the nearest directory, the one brash runs from or one above it, that holds a `pyproject.toml`. The
table is a `Config`: a setting it does not have, or a value of the wrong type, fails the run with the key it is at.
"""

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Annotated, Final

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError
from pydantic_core import ErrorDetails, PydanticCustomError

#: The file a project configures brash in.
CONFIG: Final = "pyproject.toml"
_ENTRY: Final = re.compile(r"[^\W\d]\w*(\.[^\W\d]\w*)*:[^\W\d]\w*")


def _module_and_class(entry: str) -> str:
    if not _ENTRY.fullmatch(entry):
        raise PydanticCustomError("codemod_entry", "`{entry}` is not a `module:Class`", {"entry": entry})
    return entry


class Config(BaseModel):
    """The `[tool.brash]` table: every setting a project has, each optional."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_attribute_docstrings=True)

    codemods: Mapping[str, Annotated[str, AfterValidator(_module_and_class)]] = Field(default_factory=dict)
    """The project's own codemods, by the name the command line takes, each as its `module:Class`.

    They run after brash's own, in the table's order.
    """
    exclude: tuple[str, ...] = ()
    """Files and directories no codemod rewrites, as glob patterns of paths relative to the project's directory.

    A pattern excludes the file or directory it matches, and everything under that directory. Its `*` matches any run
    of characters, slashes among them, so `*_pb2.py` excludes such a file at any depth.
    """


@dataclass(frozen=True)
class Project:
    """A project's configuration, and where it was read."""

    #: The directory that holds the `pyproject.toml`, resolved, or None when the run is in no project.
    root: Path | None
    config: Config

    def excludes(self, path: Path) -> bool:
        """Whether the project's `exclude` keeps the codemods off the file at `path`.

        Returns:
            True for a file under the project's directory that a pattern matches, itself or a directory above it.
        """
        if self.root is None or not self.config.exclude:
            return False
        try:
            relative = path.resolve().relative_to(self.root)
        except ValueError:
            return False
        candidates = [relative.as_posix(), *(parent.as_posix() for parent in relative.parents[:-1])]
        patterns = [pattern.rstrip("/") for pattern in self.config.exclude]
        return any(fnmatchcase(candidate, pattern) for candidate in candidates for pattern in patterns)


class ConfigError(Exception):
    """A project's `pyproject.toml` does not parse, or its `[tool.brash]` is not a `Config`."""


def load(start: Path) -> Project:
    """Read the configuration of the project a run from the directory `start` is in.

    Returns:
        The project, with every setting at its default when no `pyproject.toml` is found or it has no `[tool.brash]`.

    Raises:
        ConfigError: When the file does not parse, or the table holds a setting or a value brash does not take. The
            message has a line for each, with the file and the key.
    """
    start = start.resolve()
    path = next((d / CONFIG for d in (start, *start.parents) if (d / CONFIG).is_file()), None)
    if path is None:
        return Project(None, Config())
    try:
        with path.open("rb") as stream:
            tool: object = tomllib.load(stream).get("tool")
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise ConfigError(f"{path}: {e}") from e
    try:
        return Project(path.parent, Config.model_validate(tool.get("brash", {}) if isinstance(tool, dict) else {}))
    except ValidationError as e:
        raise ConfigError("\n".join(f"{path}: {_problem(error)}" for error in e.errors())) from e


def _problem(error: ErrorDetails) -> str:
    """One thing wrong with the table, as the key it is at and what is wrong there.

    Returns:
        The line, without the file's name.
    """
    key = ".".join(("tool", "brash", *map(str, error["loc"])))
    if error["type"] == "extra_forbidden":
        return f"{key}: no such setting; there are {', '.join(f'`{name}`' for name in Config.model_fields)}"
    return f"{key}: {error['msg']}"

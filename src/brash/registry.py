"""The codemods, by the name the command line takes: brash's own, and those a project registers for itself.

A project registers a codemod of its own in its `pyproject.toml`, under the name its command line takes, as the
module that holds it and the class's name there:

    [tool.brash.codemods]
    vocab-members = "codemods.vocab_members:VocabMembers"

The module is imported as any other is, from the environment brash runs in or from the directory that holds the
`pyproject.toml`, so a project's codemod need not be installed. The class is a `command.Command`. A project's
codemods run after brash's own, in the order the table gives them.
"""

from __future__ import annotations

import importlib
import sys
import tomllib
from typing import TYPE_CHECKING, Final

from brash.command import Command
from brash.doc_comments import DocComments
from brash.final_constants import FinalConstants
from brash.general_params import GeneralParams
from brash.type_aliases import TypeAliases

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: brash's own codemods by name, in the order they run on a file.
CODEMODS: Final[Mapping[str, type[Command]]] = {
    "final-constants": FinalConstants,
    "type-aliases": TypeAliases,
    "doc-comments": DocComments,
    "general-params": GeneralParams,
}
#: The file a project registers its codemods in, and the table there that names them.
CONFIG: Final = "pyproject.toml"
TABLE: Final = "tool.brash.codemods"


class RegistryError(Exception):
    """A project's `pyproject.toml` registers a codemod that cannot be loaded."""


def registered(start: Path) -> dict[str, type[Command]]:
    """Every codemod a run from the directory `start` has: brash's own, then the project's.

    The project is the nearest directory, `start` or one above it, that holds a `pyproject.toml`. It is put on the
    import path, last, so a codemod's module there is found without being installed.

    Returns:
        Each codemod by name, in the order they run on a file.

    Raises:
        RegistryError: When the file does not parse, or an entry in its table names no codemod.
    """
    codemods = dict(CODEMODS)
    config = next((d / CONFIG for d in (start, *start.parents) if (d / CONFIG).is_file()), None)
    if config is None:
        return codemods
    try:
        with config.open("rb") as stream:
            brash: object = tomllib.load(stream).get("tool", {}).get("brash", {})
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise RegistryError(f"{config}: {e}") from e
    if not isinstance(brash, dict) or brash.keys() - {"codemods"}:
        raise RegistryError(f"{config}: [tool.brash] holds one key, `codemods`")
    table: object = brash.get("codemods", {})
    if not isinstance(table, dict):
        raise RegistryError(f"{config}: [{TABLE}] is a table of names, each with its `module:Class`")
    if table and str(config.parent) not in sys.path:
        sys.path.append(str(config.parent))
    for name, where in table.items():
        if name in CODEMODS:
            raise RegistryError(f"{config}: [{TABLE}] names `{name}`, which is one of brash's own")
        codemods[str(name)] = _load(where, f"{config}: [{TABLE}] {name}")
    return codemods


def _load(where: object, entry: str) -> type[Command]:
    """Import the codemod an entry names as `module:Class`.

    Returns:
        The class.

    Raises:
        RegistryError: When the entry is not of that form, the module does not import, or the name is no codemod.
    """
    module, _, name = where.partition(":") if isinstance(where, str) else ("", "", "")
    if not module or not name:
        raise RegistryError(f"{entry}: `{where}` is not a `module:Class`")
    try:
        found: object = getattr(importlib.import_module(module), name, None)
    except Exception as e:
        raise RegistryError(f"{entry}: importing `{module}` failed: {type(e).__name__}: {e}") from e
    if not isinstance(found, type) or not issubclass(found, Command):
        raise RegistryError(f"{entry}: `{where}` is not a subclass of `brash.command.Command`")
    return found

"""The codemods, by the name the command line takes: brash's own, and those a project registers for itself.

A project registers a codemod of its own in its `pyproject.toml`, or in the `[codemods]` of its `brash.toml`, under
the name its command line takes, as the module that holds it and the class's name there:

    [tool.brash.codemods]
    vocab-members = "codemods.vocab_members:VocabMembers"

The module is imported as any other is, from the environment brash runs in or from the directory that holds that
file, so a project's codemod need not be installed. The class is a `command.Command`. A project's codemods
run after brash's own, in the order the table gives them. `config` reads the table, and its `select`, `extend-select`
and `ignore` there say which of them all a run leaves out, as its `per-file-ignores` says for some files alone. A
codemod that is `OPT_IN`, brash's own or the project's, runs only where `select` or `extend-select` names it.
"""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING, Final

from brash.command import Command
from brash.doc_comments import DocComments
from brash.final_constants import FinalConstants
from brash.general_params import GeneralParams
from brash.type_aliases import TypeAliases

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from brash.config import Project

#: brash's own codemods by name, in the order they run on a file.
CODEMODS: Final[Mapping[str, type[Command]]] = {
    "final-constants": FinalConstants,
    "type-aliases": TypeAliases,
    "doc-comments": DocComments,
    "general-params": GeneralParams,
}


class RegistryError(Exception):
    """A project registers a codemod that cannot be loaded, or chooses one there is not."""


def registered(project: Project) -> dict[str, type[Command]]:
    """Every codemod a run in a project has: brash's own, then those its `codemods` registers.

    The project's directory is put on the import path, last, so a codemod's module there is found without being
    installed.

    Returns:
        Each codemod by name, in the order they run on a file.

    Raises:
        RegistryError: When an entry takes the name of one of brash's own, or names no codemod.
    """
    codemods = dict(CODEMODS)
    if project.root is None:
        return codemods
    table = project.config.codemods
    if table and str(project.root) not in sys.path:
        sys.path.append(str(project.root))
    for name, where in table.items():
        entry = project.setting("codemods", name)
        if name in CODEMODS:
            raise RegistryError(f"{entry}: the name is one of brash's own")
        codemods[name] = _load(where, entry)
    return codemods


def selected(project: Project, codemods: Mapping[str, type[Command]]) -> list[str]:
    """The codemods a run in a project runs by default.

    They are those its `select` names, or all but those that are `OPT_IN`, and those its `extend-select` names, but
    for its `ignore`.

    Those its `per-file-ignores` names are checked here too, though they are left out file by file, by the run.

    Args:
        project: The project, whose configuration may hold any of the three lists.
        codemods: Every codemod the run has by name, in the order they run on a file.

    Returns:
        The names, in that order.

    Raises:
        RegistryError: When a list, or one of `per-file-ignores`, names no codemod.
    """
    select, extend, ignore = project.config.select, project.config.extend_select, project.config.ignore
    settings: list[tuple[tuple[str, ...], Iterable[str]]] = [
        (("select",), select or ()),
        (("extend-select",), extend),
        (("ignore",), ignore),
    ]
    settings += [(("per-file-ignores", pattern), names) for pattern, names in project.config.per_file_ignores.items()]
    for keys, names in settings:
        for name in names:
            if name not in codemods:
                there = ", ".join(f"`{known}`" for known in codemods)
                where = project.setting(*keys)
                raise RegistryError(f"{where}: `{name}` is not a codemod; there are {there}")
    default = [name for name, codemod in codemods.items() if not codemod.OPT_IN]
    chosen = {*(default if select is None else select), *extend}
    return [name for name in codemods if name in chosen and name not in ignore]


def _load(where: str, entry: str) -> type[Command]:
    """Import the codemod an entry names as `module:Class`.

    Returns:
        The class.

    Raises:
        RegistryError: When the module does not import, or the name is no codemod.
    """
    module, _, name = where.partition(":")
    try:
        found: object = getattr(importlib.import_module(module), name, None)
    except Exception as e:
        raise RegistryError(f"{entry}: importing `{module}` failed: {type(e).__name__}: {e}") from e
    if not isinstance(found, type) or not issubclass(found, Command):
        raise RegistryError(f"{entry}: `{where}` is not a subclass of `brash.command.Command`")
    return found

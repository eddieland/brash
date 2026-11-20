"""The codemods a project registers in its `pyproject.toml`: found, listed, run after brash's own, and refused."""

import contextlib
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Final
from unittest import mock

import pytest
from click.testing import CliRunner

from brash import main, registry
from brash.registry import CODEMODS, RegistryError

#: A project's codemod, which renames the constant `OLD`, and so runs on what `final-constants` wrote.
LOCAL: Final = '''\
import libcst as cst
from brash.command import Command


class Rename(Command):
    """Rename `OLD`."""

    DESCRIPTION = "Rename `OLD` to `NEW`."

    @classmethod
    def wants(cls, source: str) -> bool:
        return "OLD" in source

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        return updated_node.with_changes(value="NEW") if original_node.value == "OLD" else updated_node


class NotOne:
    """No codemod."""
'''
BEFORE: Final = "OLD = 3\n"
AFTER: Final = "from typing import Final\n\nNEW: Final = 3\n"


@pytest.fixture
def project(tmp_path: Path) -> Iterator[Path]:
    """A project that registers `rename`, run from its own directory, with the import state restored after."""
    (tmp_path / "pyproject.toml").write_text('[tool.brash.codemods]\nrename = "local_codemods.rename:Rename"\n')
    (tmp_path / "local_codemods").mkdir()
    (tmp_path / "local_codemods" / "rename.py").write_text(LOCAL)
    with mock.patch.object(sys, "path", list(sys.path)), mock.patch.dict(sys.modules), contextlib.chdir(tmp_path):
        yield tmp_path


def invoke(*args: object) -> tuple[int, str]:
    result = CliRunner().invoke(main, [str(arg) for arg in args])
    return result.exit_code, result.output


def configure(project: Path, text: str) -> None:
    (project / "pyproject.toml").write_text(text)


def test_a_directory_with_no_project_above_it_has_brashs_own_codemods(tmp_path: Path) -> None:
    with mock.patch.object(registry, "CONFIG", "no-such-file.toml"):
        assert registry.registered(tmp_path) == dict(CODEMODS)


def test_a_project_that_registers_none_has_brashs_own_and_its_directory_is_not_imported_from(project: Path) -> None:
    configure(project, '[project]\nname = "plain"\n')

    assert registry.registered(project) == dict(CODEMODS)
    assert str(project) not in sys.path


def test_a_projects_codemods_come_after_brashs_own_from_any_directory_below_it(project: Path) -> None:
    below = project / "src" / "pkg"
    below.mkdir(parents=True)

    found = registry.registered(below)

    assert list(found) == [*CODEMODS, "rename"]
    assert found["rename"].__module__ == "local_codemods.rename"
    assert sys.path[-1] == str(project)


def test_list_names_a_projects_codemods_too(project: Path) -> None:
    code, output = invoke("--list")

    assert code == 0
    assert output.splitlines()[len(CODEMODS) :] == ["rename  Rename `OLD` to `NEW`."]


def test_a_projects_codemod_runs_on_what_brashs_own_wrote(project: Path) -> None:
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    assert invoke(stale) == (0, f"Rewrote {stale}\n")
    assert stale.read_text() == AFTER
    assert invoke("--check", stale) == (0, "")


def test_only_takes_a_projects_codemod_by_name(project: Path) -> None:
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    assert invoke("--only", "rename", stale)[0] == 0
    assert stale.read_text() == "NEW = 3\n"


def test_only_refuses_a_name_no_codemod_has_and_names_those_there_are(project: Path) -> None:
    code, output = invoke("--only", "nope", ".")

    assert code == 2
    assert "'nope' is not one of 'final-constants', " in output
    assert "'rename'." in output


def test_a_projects_codemod_runs_over_many_files_as_over_few(project: Path) -> None:
    for i in range(20):
        (project / f"m{i:02}.py").write_text(BEFORE)

    code, _ = invoke(".")

    assert code == 0
    assert {(project / f"m{i:02}.py").read_text() for i in range(20)} == {AFTER}


@pytest.mark.parametrize(
    ("config", "message"),
    [
        pytest.param("[tool.brash", "pyproject.toml: ", id="not TOML"),
        pytest.param("[tool.brash]\ncodemod = {}\n", "[tool.brash] holds one key, `codemods`", id="another key"),
        pytest.param("[tool.brash]\ncodemods = ['m:C']\n", "is a table of names", id="a list"),
        pytest.param(
            "[tool.brash.codemods]\ndoc-comments = 'local_codemods.rename:Rename'\n",
            "names `doc-comments`, which is one of brash's own",
            id="one of brash's names",
        ),
        pytest.param(
            "[tool.brash.codemods]\nrename = 'local_codemods.rename'\n",
            "rename: `local_codemods.rename` is not a `module:Class`",
            id="no class",
        ),
        pytest.param("[tool.brash.codemods]\nrename = 3\n", "rename: `3` is not a `module:Class`", id="not a string"),
        pytest.param(
            "[tool.brash.codemods]\nrename = 'local_codemods.missing:Rename'\n",
            "importing `local_codemods.missing` failed: ModuleNotFoundError",
            id="no such module",
        ),
        pytest.param(
            "[tool.brash.codemods]\nrename = 'local_codemods.rename:Missing'\n",
            "is not a subclass of `brash.command.Command`",
            id="no such name",
        ),
        pytest.param(
            "[tool.brash.codemods]\nrename = 'local_codemods.rename:NotOne'\n",
            "is not a subclass of `brash.command.Command`",
            id="another class",
        ),
    ],
)
def test_an_entry_that_names_no_codemod_fails_the_run_and_says_which(project: Path, config: str, message: str) -> None:
    configure(project, config)
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    with pytest.raises(RegistryError) as raised:
        registry.registered(project)
    code, output = invoke(".")

    assert message in str(raised.value)
    assert code == 1
    assert message in output
    assert stale.read_text() == BEFORE

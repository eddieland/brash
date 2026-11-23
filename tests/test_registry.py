"""What a project sets in its `pyproject.toml` or `brash.toml`.

Its codemods found, listed, run and refused, and its files excluded.
"""

import contextlib
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Final
from unittest import mock

import pytest
from click.testing import CliRunner

from brash import config, main, registry
from brash.config import ConfigError
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
#: The start of a `pyproject.toml` that registers it, for a test to add `[tool.brash]`'s other settings to.
CONFIGURED: Final = '[tool.brash]\ncodemods = { rename = "local_codemods.rename:Rename" }\n'
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
    with mock.patch.object(config, "CONFIGS", ("no-such-file.toml",)):
        assert registry.registered(config.load(tmp_path)) == dict(CODEMODS)


def test_a_project_that_registers_none_has_brashs_own_and_its_directory_is_not_imported_from(project: Path) -> None:
    configure(project, '[project]\nname = "plain"\n')

    assert registry.registered(config.load(project)) == dict(CODEMODS)
    assert str(project) not in sys.path


def test_a_projects_codemods_come_after_brashs_own_from_any_directory_below_it(project: Path) -> None:
    below = project / "src" / "pkg"
    below.mkdir(parents=True)

    found = registry.registered(config.load(below))

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
    ("text", "message"),
    [
        pytest.param(
            "[tool.brash.codemods]\ndoc-comments = 'local_codemods.rename:Rename'\n",
            "tool.brash.codemods.doc-comments: the name is one of brash's own",
            id="one of brash's names",
        ),
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
def test_an_entry_that_names_no_codemod_fails_the_run_and_says_which(project: Path, text: str, message: str) -> None:
    configure(project, text)
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    with pytest.raises(RegistryError) as raised:
        registry.registered(config.load(project))
    code, output = invoke(".")

    assert message in str(raised.value)
    assert code == 1
    assert message in output
    assert stale.read_text() == BEFORE


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param("[tool.brash", "pyproject.toml: ", id="not TOML"),
        pytest.param("[tool]\nbrash = 3\n", "tool.brash: Input should be a valid dictionary", id="no table"),
        pytest.param(
            "[tool.brash]\ncodemod = {}\n",
            "tool.brash.codemod: no such setting; there are `codemods`, `select`, `ignore`, `exclude`",
            id="another key",
        ),
        pytest.param(
            "[tool.brash]\ncodemods = ['m:C']\n",
            "tool.brash.codemods: Input should be a valid dictionary",
            id="a list of codemods",
        ),
        pytest.param(
            "[tool.brash.codemods]\nrename = 'local_codemods.rename'\n",
            "tool.brash.codemods.rename: `local_codemods.rename` is not a `module:Class`",
            id="no class",
        ),
        pytest.param(
            "[tool.brash.codemods]\nrename = 3\n",
            "tool.brash.codemods.rename: Input should be a valid string",
            id="not a string",
        ),
        pytest.param(
            "[tool.brash]\nexclude = 'build'\n",
            "tool.brash.exclude: Input should be a valid tuple",
            id="one pattern, not a list",
        ),
        pytest.param(
            "[tool.brash]\nexclude = ['build', 3]\n",
            "tool.brash.exclude.1: Input should be a valid string",
            id="a pattern that is no string",
        ),
    ],
)
def test_a_table_brash_does_not_take_fails_the_run_and_says_where(project: Path, text: str, message: str) -> None:
    configure(project, text)
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    with pytest.raises(ConfigError) as raised:
        config.load(project)
    code, output = invoke(".")

    assert message in str(raised.value)
    assert code == 1
    assert message in output
    assert stale.read_text() == BEFORE


def test_everything_wrong_with_a_table_is_reported_at_once_each_with_the_file(project: Path) -> None:
    configure(project, "[tool.brash]\nexclude = 3\nexcludes = []\ncodemods = { rename = 'nope' }\n")

    with pytest.raises(ConfigError) as raised:
        config.load(project)

    assert sorted(line.removeprefix(f"{project / 'pyproject.toml'}: ") for line in str(raised.value).splitlines()) == [
        "tool.brash.codemods.rename: `nope` is not a `module:Class`",
        "tool.brash.exclude: Input should be a valid tuple",
        "tool.brash.excludes: no such setting; there are `codemods`, `select`, `ignore`, `exclude`",
    ]


def test_a_brash_toml_holds_the_settings_at_its_top_level(project: Path) -> None:
    (project / "pyproject.toml").unlink()
    (project / "brash.toml").write_text(
        "exclude = ['skipped.py']\n[codemods]\nrename = 'local_codemods.rename:Rename'\n",
    )
    stale, skipped = project / "stale.py", project / "skipped.py"
    stale.write_text(BEFORE)
    skipped.write_text(BEFORE)

    code, _ = invoke(".")

    assert code == 0
    assert stale.read_text() == AFTER
    assert skipped.read_text() == BEFORE


def test_a_brash_toml_is_read_in_place_of_the_pyproject_beside_it_and_of_any_above(project: Path) -> None:
    configure(project, CONFIGURED + "ignore = ['final-constants']\n")
    (project / "brash.toml").write_text("ignore = ['doc-comments']\n")
    below = project / "below"
    below.mkdir()
    (below / "brash.toml").write_text("")

    assert config.load(project).config.ignore == ("doc-comments",)
    assert list(registry.registered(config.load(project))) == list(CODEMODS)
    assert config.load(below).config == config.Config()
    assert config.load(below).root == below


def test_a_pyproject_below_a_brash_toml_is_the_one_read(project: Path) -> None:
    (project / "brash.toml").write_text("ignore = ['doc-comments']\n")
    below = project / "below"
    below.mkdir()
    (below / "pyproject.toml").write_text("[tool.brash]\nignore = ['type-aliases']\n")

    assert config.load(below).config.ignore == ("type-aliases",)


def test_what_is_wrong_in_a_brash_toml_is_at_its_key_there_with_no_table_above_it(project: Path) -> None:
    (project / "brash.toml").write_text("excludes = []\n[codemods]\nrename = 'nope'\n")

    with pytest.raises(ConfigError) as raised:
        config.load(project)

    assert sorted(line.removeprefix(f"{project / 'brash.toml'}: ") for line in str(raised.value).splitlines()) == [
        "codemods.rename: `nope` is not a `module:Class`",
        "excludes: no such setting; there are `codemods`, `select`, `ignore`, `exclude`",
    ]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param("select = ['final-constant']\n", "select: `final-constant` is not a codemod", id="a choice"),
        pytest.param(
            "[codemods]\ndoc-comments = 'local_codemods.rename:Rename'\n",
            "codemods.doc-comments: the name is one of brash's own",
            id="a codemod",
        ),
    ],
)
def test_a_codemod_a_brash_toml_cannot_have_fails_the_run_at_its_key_there(
    project: Path,
    text: str,
    message: str,
) -> None:
    (project / "brash.toml").write_text(text)

    code, output = invoke(".")

    assert code == 1
    assert f"Error: {project / 'brash.toml'}: {message}" in output


def test_excluded_files_are_left_alone_found_or_named_outright_and_others_are_rewritten(project: Path) -> None:
    configure(project, "[tool.brash]\nexclude = ['pkg/_generated/', '*_pb2.py', 'top.py']\n")
    names = ("pkg/_generated/deep/a.py", "pkg/wire/b_pb2.py", "top.py", "pkg/top.py", "pkg/c.py")
    for name in names:
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_text(BEFORE)

    code, output = invoke(".", "top.py", "pkg/wire/b_pb2.py")

    assert code == 0
    assert output == "Rewrote pkg/c.py\nRewrote pkg/top.py\n"
    assert {name: (project / name).read_text() == BEFORE for name in names} == {
        "pkg/_generated/deep/a.py": True,
        "pkg/wire/b_pb2.py": True,
        "top.py": True,
        "pkg/top.py": False,
        "pkg/c.py": False,
    }


def test_exclude_holds_from_a_directory_below_the_project_and_not_for_a_file_outside_it(
    project: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    configure(project, "[tool.brash]\nexclude = ['pkg/skipped.py']\n")
    (project / "pkg").mkdir()
    (project / "pkg" / "skipped.py").write_text(BEFORE)
    outside = tmp_path_factory.mktemp("outside") / "skipped.py"
    outside.write_text(BEFORE)

    with contextlib.chdir(project / "pkg"):
        code, output = invoke("skipped.py", outside)

    assert (code, output) == (0, f"Rewrote {outside}\n")
    assert (project / "pkg" / "skipped.py").read_text() == BEFORE


def test_ignore_turns_a_codemod_off_brashs_own_or_the_projects_and_the_others_run(project: Path) -> None:
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    configure(project, CONFIGURED + "ignore = ['rename']\n")
    assert invoke("--check", stale)[1].count("+NEW") == 0
    configure(project, CONFIGURED + "ignore = ['final-constants']\n")
    assert invoke(stale)[0] == 0

    assert stale.read_text() == "NEW = 3\n"


def test_select_runs_the_codemods_it_names_alone_but_for_those_ignore_names(project: Path) -> None:
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    configure(project, CONFIGURED + "select = ['rename', 'final-constants', 'doc-comments']\nignore = ['rename']\n")
    chosen = registry.selected(config.load(project), registry.registered(config.load(project)))
    code, _ = invoke(stale)

    assert chosen == ["final-constants", "doc-comments"]
    assert code == 0
    assert stale.read_text() == "from typing import Final\n\nOLD: Final = 3\n"


def test_selecting_none_runs_none(project: Path) -> None:
    stale = project / "stale.py"
    stale.write_text(BEFORE)
    configure(project, CONFIGURED + "select = []\n")

    assert invoke("--check", stale) == (0, "")


def test_only_is_taken_in_place_of_the_projects_choice_and_list_names_every_codemod(project: Path) -> None:
    stale = project / "stale.py"
    stale.write_text(BEFORE)
    configure(project, CONFIGURED + "select = ['doc-comments']\nignore = ['rename']\n")

    code, _ = invoke("--only", "rename", stale)
    _, listed = invoke("--list")

    assert code == 0
    assert stale.read_text() == "NEW = 3\n"
    assert [line.split()[0] for line in listed.splitlines()] == [*CODEMODS, "rename"]


@pytest.mark.parametrize("setting", ["select", "ignore"])
def test_a_choice_of_a_codemod_there_is_not_fails_the_run_and_names_those_there_are(
    project: Path,
    setting: str,
) -> None:
    configure(project, CONFIGURED + f"{setting} = ['final-constant']\n")
    stale = project / "stale.py"
    stale.write_text(BEFORE)

    code, output = invoke(".")

    assert code == 1
    assert f"pyproject.toml: tool.brash.{setting}: `final-constant` is not a codemod; there are " in output
    assert "`general-params`, `rename`" in output
    assert stale.read_text() == BEFORE

"""The `type-aliases` codemod: what it rewrites, what it leaves alone, and that it has nothing to do twice."""

from typing import Final

import pytest

from brash import run
from brash.config import Config
from brash.type_aliases import TypeAliases, aliases
from tests.helpers import cases

NAME: Final = "type-aliases"
CASES: Final = cases(NAME)
#: A project that names two generic types of its own, and the cases that hold in it.
EXTENDED: Final = Config.model_validate({"extend-generics": ["numpy.typing.NDArray", "app.tables.Table"]})
EXTENDED_CASES: Final = cases(f"{NAME}-extend-generics")


def rewrite(source: str) -> str:
    return run.rewrite(source, [NAME])


@pytest.mark.parametrize(("before", "after"), CASES.rewritten)
def test_an_implicit_type_alias_becomes_a_type_statement(before: str, after: str) -> None:
    assert rewrite(before) == after
    assert rewrite(after) == after
    assert not TypeAliases.wants(after)


@pytest.mark.parametrize("source", CASES.left_alone)
def test_what_is_not_an_alias_safe_to_rewrite_is_left_alone(source: str) -> None:
    assert not aliases(source)
    assert not TypeAliases.wants(source)
    assert rewrite(source) == source


@pytest.mark.parametrize(("before", "after"), EXTENDED_CASES.rewritten)
def test_an_alias_of_a_generic_the_project_names_becomes_a_type_statement(before: str, after: str) -> None:
    assert run.rewrite(before, [NAME], config=EXTENDED) == after
    assert run.rewrite(after, [NAME], config=EXTENDED) == after
    assert not TypeAliases.wants_in(after, EXTENDED)


@pytest.mark.parametrize("source", EXTENDED_CASES.left_alone)
def test_what_is_not_an_alias_in_a_project_that_names_generics_is_left_alone(source: str) -> None:
    assert not aliases(source, EXTENDED.extend_generics)
    assert not TypeAliases.wants_in(source, EXTENDED)
    assert run.rewrite(source, [NAME], config=EXTENDED) == source


def test_a_generic_the_project_names_is_left_alone_where_no_project_names_it() -> None:
    source = "from app.tables import Table\n\nRows = Table[Row]\n"

    assert TypeAliases.wants_in(source, EXTENDED)
    assert not TypeAliases.wants(source)
    assert rewrite(source) == source


def test_a_module_with_no_capitalised_name_assigned_is_never_parsed() -> None:
    assert not TypeAliases.wants("x = (\n")


def test_a_module_that_does_not_parse_is_wanted_so_that_it_is_reported() -> None:
    assert TypeAliases.wants("Unit = tuple[\n")
    with pytest.raises(run.CodemodError, match="type-aliases"):
        rewrite("Unit = tuple[\n")

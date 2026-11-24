"""The `empty-collections` codemod: what it annotates, what it leaves alone, and that it has nothing to do twice."""

import ast
from typing import Final
from unittest import mock

import pytest

from brash import run
from brash.empty_collections import EmptyCollections, annotated
from tests.helpers import cases

NAME: Final = "empty-collections"
CASES: Final = cases(NAME)


def rewrite(source: str) -> str:
    return run.rewrite(source, [NAME])


@pytest.mark.parametrize(("before", "after"), CASES.rewritten)
def test_an_empty_collection_takes_the_type_its_return_or_join_gives(before: str, after: str) -> None:
    assert rewrite(before) == after
    assert rewrite(after) == after
    assert not EmptyCollections.wants(after)


@pytest.mark.parametrize("source", CASES.left_alone)
def test_an_empty_collection_not_known_to_be_typed_so_is_left_alone(source: str) -> None:
    assert not annotated(source)
    assert not EmptyCollections.wants(source)
    assert rewrite(source) == source


def test_a_collection_is_found_by_the_line_of_its_name() -> None:
    source = "def f() -> list[int]:\n    x = 1\n    found = []\n    return found\n"

    assert annotated(source) == {(3, "found"): "list[int]"}


def test_a_module_that_assigns_no_empty_collection_is_never_parsed() -> None:
    with mock.patch.object(ast, "parse", autospec=True, side_effect=ast.parse) as parse:
        assert not EmptyCollections.wants("def f() -> list[int]:\n    return [1]\n")
        assert EmptyCollections.wants("def f() -> list[int]:\n    found = []\n    return found\n")

    assert parse.call_count == 1


def test_a_module_that_does_not_parse_is_wanted_so_that_it_is_reported() -> None:
    assert EmptyCollections.wants("def f() -> list[int]:\n    found = []\n    return (\n")
    with pytest.raises(run.CodemodError, match="empty-collections"):
        rewrite("def f() -> list[int]:\n    found = []\n    return (\n")

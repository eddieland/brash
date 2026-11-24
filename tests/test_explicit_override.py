"""The `explicit-override` codemod: what it marks, what it leaves alone, and that it has nothing to do twice."""

import ast
from typing import Final
from unittest import mock

import pytest

from brash import run
from brash.explicit_override import ExplicitOverride, overrides
from tests.helpers import cases

NAME: Final = "explicit-override"
CASES: Final = cases(NAME)


def rewrite(source: str) -> str:
    return run.rewrite(source, [NAME])


@pytest.mark.parametrize(("before", "after"), CASES.rewritten)
def test_a_method_that_overrides_a_base_of_the_module_is_marked(before: str, after: str) -> None:
    assert rewrite(before) == after
    assert rewrite(after) == after
    assert not ExplicitOverride.wants(after)


@pytest.mark.parametrize("source", CASES.left_alone)
def test_a_method_not_known_to_override_safely_is_left_alone(source: str) -> None:
    assert not overrides(source)
    assert not ExplicitOverride.wants(source)
    assert rewrite(source) == source


def test_a_method_is_found_by_the_line_of_its_name() -> None:
    source = "class A:\n    def f(self) -> None: ...\n\n\nclass B(A):\n    def f(self) -> None: ...\n"

    assert overrides(source) == {(6, "f")}


def test_it_is_off_by_default_and_needs_python_3_12() -> None:
    assert ExplicitOverride.OPT_IN
    assert ExplicitOverride.MINIMUM_PYTHON == (3, 12)


def test_a_module_that_derives_no_class_is_never_parsed() -> None:
    base = "class A:\n    def f(self) -> None: ...\n"
    with mock.patch.object(ast, "parse", autospec=True, side_effect=ast.parse) as parse:
        assert not ExplicitOverride.wants(base)
        assert ExplicitOverride.wants(base + "class B(A):\n    def f(self) -> None: ...\n")

    assert parse.call_count == 1


def test_a_module_that_does_not_parse_is_wanted_so_that_it_is_reported() -> None:
    assert ExplicitOverride.wants("class A(B):\n    def f(self) -> (\n")
    with pytest.raises(run.CodemodError, match="explicit-override"):
        rewrite("class A(B):\n    def f(self) -> (\n")

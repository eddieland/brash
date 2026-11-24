"""Mark a method that overrides one of a base class in the same module with `@override`.

`@override` makes a type checker report a method that no longer overrides anything once the base's is renamed. mypy
(`explicit-override`), pyrefly (`missing-override-decorator`) and basedpyright (`reportImplicitOverride`) each report
an override without it, and none writes it. Here

    class Base:
        def run(self, argv: list[str]) -> int: ...


    class Child(Base):
        def run(self, argv: list[str]) -> int:
            return 0

gets `@override` above `Child.run`, and the module `from typing import override` when it has no import of it. A
method overrides when a class it derives from, directly or through others, defines a method of its name. Only a base
the module defines can say so, so most overrides, of a base imported from elsewhere, are not marked. It is off by
default (`OPT_IN`): few projects mark their overrides, and one that does selects it. It leaves alone:

- a base that is not a class among the module's own statements, bound once, above the class that derives from it; one
  with a decorator other than one that hands back the class itself (`dataclass`, `final`, `total_ordering`,
  `runtime_checkable`); and a base's method that its class binds again or deletes;
- a method with a decorator, `@override` among them, one its class binds again, and `__init__` and `__new__`, which
  construct rather than override;
- a method with a parameter but `self` or `cls` that is unannotated, whose type pyrefly then takes from the base's;
- a method with a type checker's or a lint's directive on its header or on the line above it;
- a module with a star import, and one that binds `override` other than by importing it from `typing` or
  `typing_extensions` among its own statements, since the decorator would then be something else.

`typing.override` is Python 3.12's, so it does not run in a project whose `target-version` is older.

What to mark is decided from the stdlib's syntax tree, and only for a module whose text derives a class from another,
so a module with none is never parsed by libcst (`Command.wants`).
"""

from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING, Final, override

import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import CodeRange, PositionProvider

from brash.command import Command
from brash.final_constants import last_name

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

    from libcst.codemod import CodemodContext

#: What the text of a module with an override to mark must hold: a class with a base.
DERIVED: Final = re.compile(r"^[ \t]*class[ \t]+\w+[ \t]*(?:\[[^\]]*\])?[ \t]*\(", re.MULTILINE)
#: The class decorators that hand back the class they are given, so that its methods are still the base's.
KEEPING: Final = frozenset({"dataclass", "final", "runtime_checkable", "total_ordering"})
#: The methods that construct an object, which a class defines for itself rather than overrides.
CONSTRUCTORS: Final = frozenset({"__init__", "__new__"})
#: The modules `override` is imported from.
SOURCES: Final = frozenset({"typing", "typing_extensions"})
#: A comment that steers a type checker or a lint, which a new decorator may contradict.
DIRECTIVE: Final = re.compile(r"#\s*(?:type:|noqa\b|pyright:|pyrefly:|mypy:)")


class ExplicitOverride(Command):
    """Mark each method that overrides one of a base class in the same module with `@override`."""

    DESCRIPTION = "Mark a method that overrides one of a base class in the same module with `@override`."
    MINIMUM_PYTHON = (3, 12)
    OPT_IN = True
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context: CodemodContext) -> None:
        """Start with no method to mark."""
        super().__init__(context)
        #: The methods to mark in the module being rewritten, as `overrides` finds them.
        self._found: frozenset[tuple[int, str]] = frozenset()

    @classmethod
    @override
    def wants(cls, source: str) -> bool:
        """Whether a module with this text has an override to mark.

        Returns:
            True when it has one, or may have one and does not parse, which is then libcst's to report.
        """
        if not DERIVED.search(source):
            return False
        try:
            return bool(overrides(source))
        except SyntaxError:
            return True

    @override
    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        """Mark the module's overrides, and import `override` when it has no import of it.

        Returns:
            The module rewritten, or as it was when it has no override to mark.
        """
        found = overrides(tree.code)
        if not found:
            return tree
        self._found = found
        rewritten = tree.visit(self)
        if _imports(ast.parse(tree.code)):
            return rewritten
        AddImportsVisitor.add_needed_import(self.context, "typing", "override")
        return AddImportsVisitor(self.context).transform_module(rewritten)

    @override
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Put `@override` on a method, when it is one to mark.

        Returns:
            The method marked, or as it was.
        """
        position = self.get_metadata(PositionProvider, original_node.name, None)
        line = position.start.line if isinstance(position, CodeRange) else None
        if (line, original_node.name.value) not in self._found:
            return updated_node
        return updated_node.with_changes(decorators=[cst.Decorator(cst.Name("override")), *updated_node.decorators])


def overrides(source: str) -> frozenset[tuple[int, str]]:
    """The methods of a module to mark as overrides, from its text.

    Returns:
        Each method, by the line its name is on and that name.

    Raises:
        SyntaxError: When the text is not Python.
    """
    module = ast.parse(source)
    if not _marks(module):
        return frozenset()
    lines = source.splitlines()
    bound = _bindings([module], nested=True)
    classes = {
        statement.name: statement
        for statement in module.body
        if isinstance(statement, ast.ClassDef) and bound.get(statement.name) == 1
    }
    return frozenset(
        (method.lineno, method.name) for derived in classes.values() for method in _overriding(derived, classes, lines)
    )


def _marks(module: ast.Module) -> bool:
    """Whether `override` in a module can only be `typing.override`: it has no star import, and no other binding.

    Returns:
        True when every binding of the name is its import from `typing` or `typing_extensions`, among the module's
        own statements.
    """
    starred = any(
        isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names) for node in ast.walk(module)
    )
    return not starred and _bindings([module], nested=True).get("override", 0) == len(_imports(module))


def _imports(module: ast.Module) -> list[ast.alias]:
    """The module's own imports of `override` from `typing` or `typing_extensions`, under its own name.

    Returns:
        The imports.
    """
    return [
        alias
        for statement in module.body
        if isinstance(statement, ast.ImportFrom) and statement.module in SOURCES and not statement.level
        for alias in statement.names
        if alias.name == "override" and alias.asname is None
    ]


def _overriding(
    derived: ast.ClassDef,
    classes: Mapping[str, ast.ClassDef],
    lines: list[str],
) -> Iterator[ast.FunctionDef | ast.AsyncFunctionDef]:
    """The methods of a class that override one of a class it derives from, among the module's, to mark.

    Yields:
        Each method.
    """
    inherited = _inherited(derived, classes)
    own = _bindings(derived.body, nested=False)
    for method in derived.body:
        match method:
            case ast.FunctionDef(name=name) | ast.AsyncFunctionDef(name=name) if name in inherited:
                if _markable(method, own, lines):
                    yield method
            case _:
                pass


def _inherited(derived: ast.ClassDef, classes: Mapping[str, ast.ClassDef]) -> frozenset[str]:
    """The methods a class's bases among the module's own define, directly or through their own bases.

    Returns:
        The names of the methods, each defined once by a class that binds the name no other way. A base is one of
        `classes` above the class, whose decorators are of `KEEPING`.
    """
    found: set[str] = set()
    seen: set[str] = set()
    stack = [derived]
    while stack:
        current = stack.pop()
        for base in current.bases:
            # A generic base, `Base[int]`, names the class as its subscript's value.
            named = base.value if isinstance(base, ast.Subscript) else base
            parent = classes.get(named.id) if isinstance(named, ast.Name) else None
            if parent is None or parent.name in seen or parent.lineno >= current.lineno or not _keeps(parent):
                continue
            seen.add(parent.name)
            bound = _bindings(parent.body, nested=False)
            found |= {
                statement.name
                for statement in parent.body
                if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef) and bound[statement.name] == 1
            }
            stack.append(parent)
    return frozenset(found)


def _markable(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    own: Mapping[str, int],
    lines: list[str],
) -> bool:
    """Whether an override is one to mark: no constructor, bound once, undecorated, annotated, and with no directive.

    Args:
        method: The method.
        own: How many times its class binds each name.
        lines: The module's lines.

    Returns:
        True when it is.
    """
    if method.name in CONSTRUCTORS or own[method.name] != 1 or method.decorator_list:
        return False
    return _annotated(method) and not _directed(lines, method)


def _keeps(base: ast.ClassDef) -> bool:
    """Whether a class's decorators each hand back the class they are given.

    Returns:
        True when each is one of `KEEPING`, called or not.
    """
    return all(
        last_name(decorator.func if isinstance(decorator, ast.Call) else decorator) in KEEPING
        for decorator in base.decorator_list
    )


def _annotated(method: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether every parameter of a method but its first, `self` or `cls`, is annotated.

    Returns:
        True when each is.
    """
    arguments = method.args
    positional = [*arguments.posonlyargs, *arguments.args][1:]
    starred = [argument for argument in (arguments.vararg, arguments.kwarg) if argument is not None]
    return all(argument.annotation is not None for argument in [*positional, *arguments.kwonlyargs, *starred])


def _directed(lines: Sequence[str], method: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether a method has a type checker's or a lint's directive on its header or on the line above it.

    Returns:
        True when it has.
    """
    end = max(method.lineno, method.body[0].lineno - 1)
    return any(DIRECTIVE.search(lines[number - 1]) for number in range(method.lineno - 1, end + 1) if number > 0)


def _bindings(nodes: Iterable[ast.AST], *, nested: bool) -> dict[str, int]:
    """How many times some nodes bind each name, other than by a type parameter.

    Args:
        nodes: The nodes, each searched whole.
        nested: Whether to search the functions, lambdas, and classes inside them too, or only name them.

    Returns:
        Each name by the times it is bound.
    """
    found: dict[str, int] = {}
    stack = list(nodes)
    while stack:
        node = stack.pop()
        names: list[str] = []
        match node:
            case ast.Name(id=name, ctx=ast.Store() | ast.Del()) | ast.arg(arg=name):
                names = [name]
            case ast.FunctionDef(name=name) | ast.AsyncFunctionDef(name=name) | ast.ClassDef(name=name):
                names = [name]
            case ast.ExceptHandler(name=str(name)) | ast.MatchAs(name=str(name)) | ast.MatchStar(name=str(name)):
                names = [name]
            case ast.alias(name=name, asname=asname):
                names = [asname or name.partition(".")[0]]
            case ast.Global(names=declared) | ast.Nonlocal(names=declared):
                names = [*declared, *declared]
            case _:
                pass
        for name in names:
            found[name] = found.get(name, 0) + 1
        if nested or not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda):
            stack.extend(ast.iter_child_nodes(node))
    return found

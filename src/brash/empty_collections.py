"""Annotate an empty list, dict, or set that a function fills, with the type its return annotation or a `join` gives.

An empty `[]`, `{}`, or `set()` has no element type, so a strict pyright reports it, and every `append` to it, as
partly unknown; mypy and pyrefly infer the type from the first `append` and say nothing. No tool writes the
annotation. Here the function

    def sources(paths: Iterable[Path]) -> list[Path]:
        found = []
        for path in paths:
            found.append(path)
        return found

gets `found: list[Path] = []`. The type comes from one of three places:

- the name is returned under a return annotation of the collection's type (`list[X]`, `set[X]`, `dict[K, V]`), an
  abstract type it is one of (`Sequence[X]`, `Iterable[X]`, `AbstractSet[X]`, `Mapping[K, V]`), or one of those
  `| None`;
- a list or set is returned whole through `sorted`, `list`, `tuple`, `set`, or `frozenset`, and the return annotation
  gives the element type of what that makes;
- a string's `join` reads a list or set, whose items are then `str`.

The annotation is the builtin, `list[X]`, whatever the return annotation spells, and every rule that applies to a name
must give the same one. It leaves alone:

- a name its function binds more than once, a parameter, a tuple or chained assignment, and anything at module or
  class level or on `self`;
- a name used in any way but a known few: `.append`, `.extend`, `.insert`, `.add`, `.update`, `.remove`, `.discard`,
  `.clear`, or `.reverse` called as a statement, `name[k] = v`, `del name[k]`, `len`, a test of its truth, `in`, a
  `join`, and the return. An item read back, `.sort()`, `.pop()`, a pass over it, the name given to any other call,
  and any use in a nested function, lambda, class, or comprehension each leave it alone;
- a return annotation that is quoted, names `Any`, is a bare `list` or an alias, or is a union other than with
  `None`, and an element type that names something the function, or the class it is a method of, binds, since the
  name would mean another thing in the body;
- a function with no return annotation, a generator, and a function with a type checker's or a lint's directive
  (`# type:`, `# noqa`, `# pyright:`, `# pyrefly:`, `# mypy:`) on its header, on the assignment, or on a `return` a
  rule reads;
- a name whose rules rely on a builtin the module binds: the collection's own, `str` for a `join`, `len`, or the one a
  return goes through.

Nothing outside the function sees the annotation, since Python never evaluates a local's.

What to annotate is decided from the stdlib's syntax tree, and only for a module whose text assigns an empty
collection, so a module with none is never parsed by libcst (`Command.wants`).
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, override

import libcst as cst
from libcst.metadata import CodeRange, PositionProvider

from brash.command import Command
from brash.final_constants import last_name

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping
    from collections.abc import Set as AbstractSet

    from libcst.codemod import CodemodContext

#: What the text of a module with a collection to annotate must hold: an empty one assigned.
ASSIGNED: Final = re.compile(r"=[ \t]*(?:\[[ \t]*\]|\{[ \t]*\}|set\(\))")
#: The heads of a return annotation each collection may be returned under, by their last names.
RETURNED: Final[Mapping[str, frozenset[str]]] = {
    "dict": frozenset({"Dict", "Mapping", "MutableMapping", "dict"}),
    "list": frozenset({"Collection", "Iterable", "List", "MutableSequence", "Sequence", "list"}),
    "set": frozenset({"AbstractSet", "Collection", "Iterable", "MutableSet", "Set", "set"}),
}
#: The builtins a list or set may be returned through, each with the heads of a return annotation its result takes.
THROUGH: Final[Mapping[str, frozenset[str]]] = {
    "frozenset": frozenset({"AbstractSet", "Collection", "FrozenSet", "Iterable", "Set", "frozenset"}),
    "list": RETURNED["list"],
    "set": RETURNED["set"],
    "sorted": RETURNED["list"],
    "tuple": frozenset({"Collection", "Iterable", "Sequence", "Tuple", "tuple"}),
}
#: The methods of each collection that, called as a statement, only put items in or take them out.
METHODS: Final[Mapping[str, frozenset[str]]] = {
    "dict": frozenset({"clear", "update"}),
    "list": frozenset({"append", "clear", "extend", "insert", "remove", "reverse"}),
    "set": frozenset({"add", "clear", "discard", "remove", "update"}),
}
#: A comment that steers a type checker or a lint, which a new annotation may contradict.
DIRECTIVE: Final = re.compile(r"#\s*(?:type:|noqa\b|pyright:|pyrefly:|mypy:)")


class EmptyCollections(Command):
    """Annotate each empty collection a function fills whose type its return annotation or a `join` gives."""

    DESCRIPTION = "Annotate an empty list, dict, or set from the return annotation, or a `join`, that types it."
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context: CodemodContext) -> None:
        """Start with no collection to annotate."""
        super().__init__(context)
        #: The collections to annotate in the module being rewritten, as `annotated` finds them.
        self._found: Mapping[tuple[int, str], str] = {}

    @classmethod
    @override
    def wants(cls, source: str) -> bool:
        """Whether a module with this text has a collection to annotate.

        Returns:
            True when it has one, or may have one and does not parse, which is then libcst's to report.
        """
        if not ASSIGNED.search(source):
            return False
        try:
            return bool(annotated(source))
        except SyntaxError:
            return True

    @override
    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        """Annotate the module's empty collections.

        Returns:
            The module rewritten, or as it was when it has no collection to annotate.
        """
        found = annotated(tree.code)
        if not found:
            return tree
        self._found = found
        return tree.visit(self)

    @override
    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.BaseSmallStatement:
        """Write an assignment as an annotated one, when it is of a collection to annotate.

        Returns:
            The assignment rewritten, or as it was.
        """
        match updated_node.targets:
            case [cst.AssignTarget(target=cst.Name(value=name) as target) as assigned]:
                pass
            case _:
                return updated_node
        position = self.get_metadata(PositionProvider, original_node.targets[0].target, None)
        text = self._found.get((position.start.line, name)) if isinstance(position, CodeRange) else None
        if text is None:
            return updated_node
        return cst.AnnAssign(
            target=target,
            annotation=cst.Annotation(cst.parse_expression(text)),
            value=updated_node.value,
            equal=cst.AssignEqual(
                whitespace_before=assigned.whitespace_before_equal,
                whitespace_after=assigned.whitespace_after_equal,
            ),
            semicolon=updated_node.semicolon,
        )


def annotated(source: str) -> dict[tuple[int, str], str]:
    """The empty collections of a module to annotate, and the type each takes, from its text.

    Returns:
        Each collection's type, as the text to write, by the line its name is assigned on and that name.

    Raises:
        SyntaxError: When the text is not Python.
    """
    module = ast.parse(source)
    tree = _Tree(
        source=source,
        lines=tuple(source.splitlines()),
        parents={child: node for node in ast.walk(module) for child in ast.iter_child_nodes(node)},
        bound=frozenset(_bindings([module], nested=True)),
    )
    # A name is assigned once in its function, and two functions are never on one line, so no two keys are alike.
    return {
        key: text
        for function in ast.walk(module)
        if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef)
        for key, text in _in_function(function, tree)
    }


@dataclass(frozen=True)
class _Tree:
    """What every function of a module is read against."""

    #: The module's text, from which a type is copied.
    source: str
    #: Its lines, where a directive is looked for.
    lines: tuple[str, ...]
    #: Each node of its tree by the node it is in.
    parents: Mapping[ast.AST, ast.AST]
    #: Every name the module binds in any scope, so that a builtin of the same name is not taken as one.
    bound: AbstractSet[str]


def _in_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    tree: _Tree,
) -> Iterator[tuple[tuple[int, str], str]]:
    """The empty collections a function assigns to annotate, and the type of each.

    Yields:
        Each collection, by the line its name is assigned on and that name, with its type as the text to write.
    """
    header = range(function.lineno, max(function.lineno, function.body[0].lineno - 1) + 1)
    if function.returns is None or _generator(function, tree.parents) or _directed(tree.lines, header):
        return
    returns = _returned(function.returns)
    bindings = _bindings([function.args, *function.body], nested=True)
    shadowing = set(bindings)
    if isinstance(scope := _scope(function, tree.parents), ast.ClassDef):
        shadowing |= set(_bindings(scope.body, nested=False))
    for statement in ast.walk(function):
        match statement:
            case ast.Assign(targets=[ast.Name(id=name) as target], value=value) if (
                _scope(statement, tree.parents) is function
                and (kind := _empty(value)) is not None
                and bindings[name] == 1
                and not _directed(tree.lines, range(statement.lineno, (statement.end_lineno or 0) + 1))
            ):
                typed = _typed(target, kind, function, returns=returns, shadowing=shadowing, tree=tree)
                if typed is not None:
                    yield (target.lineno, name), typed
            case _:
                pass


def _returned(annotation: ast.expr | None) -> ast.Subscript | None:
    """What a function's return annotation says it returns, when that is one subscripted type, alone or with `None`.

    Returns:
        The subscript, from inside `X | None`, `Optional[X]`, or `Union[X, None]`; None for any other annotation,
        quoted, bare, an alias, a wider union, or naming `Any` anywhere.
    """
    match annotation:
        case (
            ast.BinOp(left=inner, op=ast.BitOr(), right=ast.Constant(value=None))
            | ast.BinOp(
                left=ast.Constant(value=None),
                op=ast.BitOr(),
                right=inner,
            )
        ):
            return _returned(inner)
        case ast.Subscript(value=head, slice=inner) if last_name(head) == "Optional":
            return _returned(inner)
        case ast.Subscript(value=head, slice=ast.Tuple(elts=[first, second])) if last_name(head) == "Union":
            match first, second:
                case (inner, ast.Constant(value=None)) | (ast.Constant(value=None), inner):
                    return _returned(inner)
                case _:
                    return None
        case ast.Subscript(value=ast.Name() | ast.Attribute()) if not any(
            last_name(node) == "Any" for node in ast.walk(annotation) if isinstance(node, ast.Name | ast.Attribute)
        ):
            return annotation
        case _:
            return None


def _generator(function: ast.FunctionDef | ast.AsyncFunctionDef, parents: Mapping[ast.AST, ast.AST]) -> bool:
    """Whether a function is a generator, whose `return` gives no item of what it is annotated to return.

    Returns:
        True when it yields in its own scope.
    """
    return any(
        isinstance(node, ast.Yield | ast.YieldFrom) and _scope(node, parents) is function for node in ast.walk(function)
    )


def _directed(lines: tuple[str, ...], numbers: Iterable[int]) -> bool:
    """Whether any of some lines has a type checker's or a lint's directive.

    Returns:
        True when one has.
    """
    return any(DIRECTIVE.search(lines[number - 1]) for number in numbers if 0 < number <= len(lines))


def _bindings(nodes: Iterable[ast.AST], *, nested: bool) -> Counter[str]:
    """How many times some nodes bind each name, other than by a type parameter.

    Args:
        nodes: The nodes, each searched whole.
        nested: Whether to search the functions, lambdas, and classes inside them too, or only name them.

    Returns:
        Each name by the times it is bound; a `global` or `nonlocal` name twice over, so that it is never taken as
        bound once.
    """
    found: Counter[str] = Counter()
    stack = list(nodes)
    while stack:
        node = stack.pop()
        match node:
            case ast.Name(id=name, ctx=ast.Store() | ast.Del()) | ast.arg(arg=name):
                found[name] += 1
            case ast.FunctionDef(name=name) | ast.AsyncFunctionDef(name=name) | ast.ClassDef(name=name):
                found[name] += 1
                if not nested:
                    continue
            case ast.Lambda() if not nested:
                continue
            case ast.ExceptHandler(name=str(name)) | ast.MatchAs(name=str(name)) | ast.MatchStar(name=str(name)):
                found[name] += 1
            case ast.MatchMapping(rest=str(name)):
                found[name] += 1
            case ast.Import(names=aliases) | ast.ImportFrom(names=aliases):
                found.update(alias.asname or alias.name.partition(".")[0] for alias in aliases)
            case ast.Global(names=names) | ast.Nonlocal(names=names):
                found.update(dict.fromkeys(names, 2))
            case _:
                pass
        stack.extend(ast.iter_child_nodes(node))
    return found


def _scope(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> ast.AST | None:
    """The scope a node is in: the module, or the function, lambda, class, or comprehension nearest around it.

    Returns:
        The scope.
    """
    scopes = (
        ast.Module
        | ast.ClassDef
        | ast.FunctionDef
        | ast.AsyncFunctionDef
        | ast.Lambda
        | ast.ListComp
        | ast.SetComp
        | ast.DictComp
        | ast.GeneratorExp
    )
    parent = parents.get(node)
    while parent is not None and not isinstance(parent, scopes):
        parent = parents.get(parent)
    return parent


def _empty(value: ast.expr) -> str | None:
    """Which collection an expression makes empty: `[]`, `{}`, or `set()`.

    Returns:
        The collection's builtin, or None for any other expression.
    """
    match value:
        case ast.List(elts=[]):
            return "list"
        case ast.Dict(keys=[]):
            return "dict"
        case ast.Call(func=ast.Name(id="set"), args=[], keywords=[]):
            return "set"
        case _:
            return None


def _typed(
    target: ast.Name,
    kind: str,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    returns: ast.Subscript | None,
    shadowing: AbstractSet[str],
    tree: _Tree,
) -> str | None:
    """The type of an empty collection, when its every use is known and the rules that type it agree.

    Args:
        target: The name it is assigned to.
        kind: The collection's builtin: `list`, `dict`, or `set`.
        function: The function it is assigned in.
        returns: What the function's return annotation says it returns, or None when it is not one a return rule reads.
        shadowing: The names the function, or the class it is a method of, binds, which an element type may not name.
        tree: The module.

    Returns:
        The type, as the text to write, or None for a collection to leave alone.
    """
    types: set[str] = set()
    relied = {kind}
    for node in ast.walk(function):
        if not isinstance(node, ast.Name) or node.id != target.id or node is target:
            continue
        use = _use(node, kind, tree.parents) if _scope(node, tree.parents) is function else None
        if use is None:
            return None
        relied |= {use.builtin} if use.builtin is not None else set()
        if use.joined:
            if kind == "dict":
                return None
            types.add(f"{kind}[str]")
            relied.add("str")
        if use.returned is not None:
            lines = range(use.returned.lineno, (use.returned.end_lineno or 0) + 1)
            typed = None if returns is None else _from_return(returns, kind, use.builtin, shadowing, tree.source)
            if typed is None or _directed(tree.lines, lines):
                return None
            types.add(typed)
    if len(types) != 1 or relied & tree.bound:
        return None
    return types.pop()


@dataclass(frozen=True)
class _Use:
    """What one use of a collection says of its type."""

    #: The builtin the use relies on: `len`, or the one a return goes through.
    builtin: str | None = None
    #: The `return` that gives the type, of the name or of what `builtin` makes of it.
    returned: ast.Return | None = None
    #: Whether a string's `join` reads it, which makes its items `str`.
    joined: bool = False


def _use(node: ast.Name, kind: str, parents: Mapping[ast.AST, ast.AST]) -> _Use | None:
    """What one use of a collection is, when it is one of the few that leave its type to its rules.

    Returns:
        The use, or None for any other.
    """
    parent = parents[node]
    match parent:
        case ast.Return(value=value) if value is node:
            return _Use(returned=parent)
        case ast.Call(func=ast.Name(id=builtin), args=[argument], keywords=[]) if argument is node:
            return _given(parent, builtin, kind, parents)
        case ast.Call(func=ast.Attribute(value=ast.Constant(value=str()), attr="join"), args=[argument], keywords=[]):
            return _Use(joined=True) if argument is node else None
        case _:
            filled = _filled(node, kind, parents)
            return _Use() if filled or _searched(node, parents) or _tested(node, parents) else None


def _given(call: ast.Call, builtin: str, kind: str, parents: Mapping[ast.AST, ast.AST]) -> _Use | None:
    """What giving a collection to a builtin is, when it is `len`, or a return through one of `THROUGH`.

    Returns:
        The use, or None for any other call.
    """
    match parents.get(call):
        case _ if builtin == "len":
            return _Use(builtin=builtin)
        # A dict is iterated by its keys, which say nothing of its values.
        case ast.Return(value=value) as statement if value is call and builtin in THROUGH and kind != "dict":
            return _Use(builtin=builtin, returned=statement)
        case _:
            return None


def _filled(node: ast.Name, kind: str, parents: Mapping[ast.AST, ast.AST]) -> bool:
    """Whether a use only puts items in a collection or takes them out: a method of `METHODS`, or a store to an item.

    Returns:
        True when it does, as a statement whose value is not used, or as the target of `=` or `del`.
    """
    parent = parents[node]
    match parent:
        case ast.Attribute(value=value, attr=method) if value is node and method in METHODS[kind]:
            call = parents.get(parent)
            return isinstance(call, ast.Call) and call.func is parent and isinstance(parents.get(call), ast.Expr)
        case ast.Subscript(value=value, ctx=ast.Store() | ast.Del()) if value is node and kind != "set":
            holder = parents.get(parent)
            stored = isinstance(holder, ast.Assign) and any(target is parent for target in holder.targets)
            return stored or isinstance(holder, ast.Delete)
        case _:
            return False


def _searched(node: ast.Name, parents: Mapping[ast.AST, ast.AST]) -> bool:
    """Whether a use is the right of one `in` or `not in`.

    Returns:
        True when it is.
    """
    match parents[node]:
        case ast.Compare(ops=[ast.In() | ast.NotIn()], comparators=[right]):
            return right is node
        case _:
            return False


def _tested(node: ast.expr, parents: Mapping[ast.AST, ast.AST]) -> bool:
    """Whether an expression's value is only tested for its truth: by `if`, `while`, `assert`, or `not`.

    A boolean operator counts only where its own value is tested, since `found or None` is `found` itself.

    Returns:
        True when it is.
    """
    parent = parents.get(node)
    match parent:
        case ast.If(test=test) | ast.While(test=test) | ast.IfExp(test=test) | ast.Assert(test=test):
            return test is node
        case ast.UnaryOp(op=ast.Not()):
            return True
        case ast.BoolOp():
            return _tested(parent, parents)
        case _:
            return False


def _from_return(
    returns: ast.Subscript,
    kind: str,
    through: str | None,
    shadowing: AbstractSet[str],
    source: str,
) -> str | None:
    """The type a return annotation gives a collection returned as it is, or through a builtin.

    Args:
        returns: What the function's return annotation says it returns.
        kind: The collection's builtin: `list`, `dict`, or `set`.
        through: The builtin it is returned through, or None when it is returned as it is.
        shadowing: The names an element type may not name.
        source: The module's text, from which the element types are copied.

    Returns:
        The type, as the text to write, or None when the annotation is not one the collection, or what the builtin
        makes of it, can be returned under.
    """
    head = last_name(returns.value)
    if head not in (RETURNED[kind] if through is None else THROUGH[through]):
        return None
    arguments = returns.slice.elts if isinstance(returns.slice, ast.Tuple) else [returns.slice]
    match arguments:
        case [element, ast.Constant(value=value)] if head in {"Tuple", "tuple"} and value is ...:
            elements = [element]
        case [_] if head in {"Tuple", "tuple"}:
            return None
        case [_, _] if kind == "dict":
            elements = arguments
        case [_] if kind != "dict":
            elements = arguments
        case _:
            return None
    named = {node.id for element in elements for node in ast.walk(element) if isinstance(node, ast.Name)}
    texts = [ast.get_source_segment(source, element) for element in elements]
    if named & shadowing or any(text is None for text in texts):
        return None
    return f"{kind}[{', '.join(text for text in texts if text is not None)}]"

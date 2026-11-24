# `general-params`

Each case is a module's text. Under Rewritten, a case is the text before and the text after; under Left alone, text
the codemod does not change. `test_general_params.py` runs them. The codemod adds an import where libcst puts it, and
ruff then sorts and spaces it, which a case does not show.

## Rewritten

### One for

```python
def total(costs: list[float]) -> float:
    result = 0.0
    for cost in costs:
        result += cost
    return result
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float]) -> float:
    result = 0.0
    for cost in costs:
        result += cost
    return result
```

### One comprehension

```python
def total(costs: list[float]) -> float:
    return sum(c for c in costs)
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float]) -> float:
    return sum(c for c in costs)
```

### A builtin that iterates

```python
def total(costs: list[float]) -> float:
    return sum(costs)
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float]) -> float:
    return sum(costs)
```

### Joined

```python
def line(words: list[str]) -> str:
    return ", ".join(words)
```

```python
from collections.abc import Iterable

def line(words: Iterable[str]) -> str:
    return ", ".join(words)
```

### Measured

```python
def count(items: list[str]) -> int:
    return len(items)
```

```python
from collections.abc import Collection

def count(items: Collection[str]) -> int:
    return len(items)
```

### Searched

```python
def has(items: list[str], item: str) -> bool:
    return item in items
```

```python
from collections.abc import Collection

def has(items: Collection[str], item: str) -> bool:
    return item in items
```

### Two passes

```python
def spread(costs: list[float]) -> float:
    return max(costs) - min(costs)
```

```python
from collections.abc import Collection

def spread(costs: Collection[float]) -> float:
    return max(costs) - min(costs)
```

### A loop inside a loop

```python
def pairs(left: list[int], right: list[int]) -> int:
    found = 0
    for a in left:
        for b in right:
            found += a * b
    return found
```

```python
from collections.abc import Collection, Iterable

def pairs(left: Iterable[int], right: Collection[int]) -> int:
    found = 0
    for a in left:
        for b in right:
            found += a * b
    return found
```

### Tested

```python
def first(items: list[str]) -> str:
    if not items:
        return ""
    return "x"
```

```python
from collections.abc import Collection

def first(items: Collection[str]) -> str:
    if not items:
        return ""
    return "x"
```

### Indexed

```python
def first(items: list[str]) -> str:
    return items[0]
```

```python
from collections.abc import Sequence

def first(items: Sequence[str]) -> str:
    return items[0]
```

### Reversed

```python
def last(items: list[str]) -> str:
    for item in reversed(items):
        return item
    return ""
```

```python
from collections.abc import Sequence

def last(items: Sequence[str]) -> str:
    for item in reversed(items):
        return item
    return ""
```

### Sliced and only read

```python
def rest(items: list[str]) -> int:
    return len(items[1:])
```

```python
from collections.abc import Sequence

def rest(items: Sequence[str]) -> int:
    return len(items[1:])
```

### A dict only read

```python
def name(row: dict[str, str]) -> str:
    return row.get("name") or row["id"]
```

```python
from collections.abc import Mapping

def name(row: Mapping[str, str]) -> str:
    return row.get("name") or row["id"]
```

### A set tested with in

```python
def kept(name: str, names: set[str]) -> bool:
    return name in names
```

```python
from collections.abc import Set as AbstractSet

def kept(name: str, names: AbstractSet[str]) -> bool:
    return name in names
```

### A frozenset tested with in

```python
def kept(name: str, names: frozenset[str]) -> bool:
    return name not in names
```

```python
from collections.abc import Set as AbstractSet

def kept(name: str, names: AbstractSet[str]) -> bool:
    return name not in names
```

### Under TYPE_CHECKING

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def total(costs: list[float], path: Path) -> float:
    return sum(costs)
```

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def total(costs: Iterable[float], path: Path) -> float:
    return sum(costs)
```

### Joins an import

```python
from collections.abc import Callable


def total(costs: list[float], round: Callable[[float], float]) -> float:
    return round(sum(costs))
```

```python
from collections.abc import Iterable, Callable


def total(costs: Iterable[float], round: Callable[[float], float]) -> float:
    return round(sum(costs))
```

### A method of a class with no base

```python
class Totals:
    def total(self, costs: list[float]) -> float:
        return sum(costs)
```

```python
from collections.abc import Iterable

class Totals:
    def total(self, costs: Iterable[float]) -> float:
        return sum(costs)
```

### Plain decorators

```python
import pytest


@pytest.mark.parametrize("costs", [[1.0]])
def test_total(costs: list[float]) -> None:
    assert sum(costs)
```

```python
import pytest
from collections.abc import Iterable


@pytest.mark.parametrize("costs", [[1.0]])
def test_total(costs: Iterable[float]) -> None:
    assert sum(costs)
```

### A nested function's own parameter

```python
def outer() -> float:
    def total(costs: list[float]) -> float:
        return sum(costs)

    return total([1.0])
```

```python
from collections.abc import Iterable

def outer() -> float:
    def total(costs: Iterable[float]) -> float:
        return sum(costs)

    return total([1.0])
```

### Each parameter by itself

```python
def merge(left: list[int], right: list[int]) -> int:
    right.append(1)
    return sum(left)
```

```python
from collections.abc import Iterable

def merge(left: Iterable[int], right: list[int]) -> int:
    right.append(1)
    return sum(left)
```

### Keeps an already-imported name

```python
from collections.abc import Set as AbstractSet


def kept(name: str, names: set[str], others: AbstractSet[str]) -> bool:
    return name in names and name in others
```

```python
from collections.abc import Set as AbstractSet


def kept(name: str, names: AbstractSet[str], others: AbstractSet[str]) -> bool:
    return name in names and name in others
```

### A name bound again

```python
def pick(items: list[str], rows: list[list[str]]) -> int:
    for items in rows:
        pass
    return 0
```

```python
from collections.abc import Iterable

def pick(items: list[str], rows: Iterable[list[str]]) -> int:
    for items in rows:
        pass
    return 0
```

### The left of in

```python
def known(item: list[str], seen: list[list[str]]) -> bool:
    return item in seen
```

```python
from collections.abc import Collection

def known(item: list[str], seen: Collection[list[str]]) -> bool:
    return item in seen
```

### A dict copied

```python
def copy(row: dict[str, str]) -> int:
    return len(dict(row))
```

```python
from collections.abc import Mapping

def copy(row: Mapping[str, str]) -> int:
    return len(dict(row))
```

### Imported again where a function's import cannot serve

```python
def helper() -> None:
    from collections.abc import Iterable


def total(costs: list[float]) -> float:
    return sum(costs)
```

```python
from collections.abc import Iterable

def helper() -> None:
    from collections.abc import Iterable


def total(costs: Iterable[float]) -> float:
    return sum(costs)
```

### Imported again where the checker's import cannot serve

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def total(costs: list[float]) -> float:
    return sum(costs)
```

```python
from typing import TYPE_CHECKING
from collections.abc import Iterable

if TYPE_CHECKING:
    from collections.abc import Iterable


def total(costs: Iterable[float]) -> float:
    return sum(costs)
```

### Beside a one-line TYPE_CHECKING suite

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING: from pathlib import Path


def total(costs: list[float], path: Path) -> float:
    return sum(costs)
```

```python
from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Iterable

if TYPE_CHECKING: from pathlib import Path


def total(costs: Iterable[float], path: Path) -> float:
    return sum(costs)
```

### Called by name, and by nothing else

```python
def total(costs: list[float]) -> float:
    return sum(costs)


class Report:
    def lines(self, rows: list[str]) -> int:
        return len(rows)

    def size(self) -> float:
        return total([1.0]) + self.lines(["a"])
```

```python
from collections.abc import Collection, Iterable

def total(costs: Iterable[float]) -> float:
    return sum(costs)


class Report:
    def lines(self, rows: Collection[str]) -> int:
        return len(rows)

    def size(self) -> float:
        return total([1.0]) + self.lines(["a"])
```

### Starred into a call

```python
def show(names: list[str]) -> None:
    print(*names, sep=", ")
```

```python
from collections.abc import Iterable

def show(names: Iterable[str]) -> None:
    print(*names, sep=", ")
```

### Starred into a display

```python
def command(args: list[str], flags: set[str], extra: list[str]) -> tuple[list[str], set[str], tuple[str, ...]]:
    return ["tox", *args], {"-q", *flags}, (*extra, "--")
```

```python
from collections.abc import Iterable

def command(args: Iterable[str], flags: Iterable[str], extra: Iterable[str]) -> tuple[list[str], set[str], tuple[str, ...]]:
    return ["tox", *args], {"-q", *flags}, (*extra, "--")
```

### Starred in a loop

```python
def show(names: list[str], times: int) -> None:
    for _ in range(times):
        print(*names)
```

```python
from collections.abc import Collection

def show(names: Collection[str], times: int) -> None:
    for _ in range(times):
        print(*names)
```

### A dict spread into a call

```python
def make(options: dict[str, int]) -> object:
    return build(**options)
```

```python
from collections.abc import Mapping

def make(options: Mapping[str, int]) -> object:
    return build(**options)
```

### A dict spread into a display

```python
def merged(base: dict[str, str], more: dict[str, str]) -> dict[str, object]:
    return {**base, "mode": "strict", **more}
```

```python
from collections.abc import Mapping

def merged(base: Mapping[str, str], more: Mapping[str, str]) -> dict[str, object]:
    return {**base, "mode": "strict", **more}
```

### A dict's keys starred

```python
def keys(row: dict[str, int]) -> list[str]:
    return [*row]
```

```python
from collections.abc import Mapping

def keys(row: Mapping[str, int]) -> list[str]:
    return [*row]
```

### A tuple of any length

```python
def total(costs: tuple[float, ...]) -> float:
    return sum(costs)
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float]) -> float:
    return sum(costs)
```

### A tuple starred, and a dict spread

```python
import os
import subprocess


def run(args: tuple[str, ...], env: dict[str, str]) -> None:
    subprocess.run(["tox", *args], env={**os.environ, **env}, check=True)
```

```python
import os
import subprocess
from collections.abc import Iterable, Mapping


def run(args: Iterable[str], env: Mapping[str, str]) -> None:
    subprocess.run(["tox", *args], env={**os.environ, **env}, check=True)
```

### A tuple measured, and one searched

```python
def known(name: str, names: tuple[str, ...], seen: tuple[str, ...]) -> bool:
    return len(names) > 1 and name in seen
```

```python
from collections.abc import Collection

def known(name: str, names: Collection[str], seen: Collection[str]) -> bool:
    return len(names) > 1 and name in seen
```

### A tuple indexed, sliced, and counted

```python
def first(items: tuple[str, ...], rest: tuple[str, ...], votes: tuple[str, ...]) -> tuple[str, int, int]:
    return items[0], len(rest[1:]), votes.count("yes")
```

```python
from collections.abc import Sequence

def first(items: Sequence[str], rest: Sequence[str], votes: Sequence[str]) -> tuple[str, int, int]:
    return items[0], len(rest[1:]), votes.count("yes")
```

### A tuple of tuples, spaced in its brackets

```python
def total(pairs: tuple[ tuple[int, str] , ... ]) -> int:
    return sum(number for number, _ in pairs)
```

```python
from collections.abc import Iterable

def total(pairs: Iterable[ tuple[int, str] ]) -> int:
    return sum(number for number, _ in pairs)
```

### A tuple over lines

```python
def total(
    costs: tuple[
        float,
        ...,
    ],
) -> float:
    return sum(costs)
```

```python
from collections.abc import Iterable

def total(
    costs: Iterable[
        float
    ],
) -> float:
    return sum(costs)
```

### Optional

```python
def total(costs: list[float] | None) -> float:
    return sum(costs or [])
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float] | None) -> float:
    return sum(costs or [])
```

### Optional, compared with None

```python
def total(costs: list[float] | None = None) -> float:
    if costs is None:
        return 0.0
    return sum(costs)
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float] | None = None) -> float:
    if costs is None:
        return 0.0
    return sum(costs)
```

### Optional, tested for its truth

```python
def total(costs: list[float] | None) -> float:
    if not costs:
        return 0.0
    return sum(costs)
```

```python
from collections.abc import Collection

def total(costs: Collection[float] | None) -> float:
    if not costs:
        return 0.0
    return sum(costs)
```

### Optional, its default looped over

```python
def total(costs: list[float] | None) -> float:
    result = 0.0
    for cost in costs or ():
        result += cost
    return result
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float] | None) -> float:
    result = 0.0
    for cost in costs or ():
        result += cost
    return result
```

### Optional, its default passed over twice

```python
def spread(costs: list[float] | None) -> float:
    return max(costs or [0.0]) - min(costs or [0.0])
```

```python
from collections.abc import Collection

def spread(costs: Collection[float] | None) -> float:
    return max(costs or [0.0]) - min(costs or [0.0])
```

### Optional, its default indexed

```python
def first(names: list[str] | None) -> str:
    return (names or [""])[0]
```

```python
from collections.abc import Sequence

def first(names: Sequence[str] | None) -> str:
    return (names or [""])[0]
```

### An optional dict

```python
def colour(row: dict[str, str] | None) -> str | None:
    return (row or {}).get("colour")
```

```python
from collections.abc import Mapping

def colour(row: Mapping[str, str] | None) -> str | None:
    return (row or {}).get("colour")
```

### An optional dict spread

```python
def show(row: dict[str, str] | None) -> None:
    print({"x": "y", **(row or {})})
```

```python
from collections.abc import Mapping

def show(row: Mapping[str, str] | None) -> None:
    print({"x": "y", **(row or {})})
```

### An optional set searched

```python
def known(name: str, names: set[str] | None = None) -> bool:
    return names is not None and name in names
```

```python
from collections.abc import Set as AbstractSet

def known(name: str, names: AbstractSet[str] | None = None) -> bool:
    return names is not None and name in names
```

### An optional tuple starred

```python
def run(args: tuple[str, ...] | None) -> None:
    call("tox", *(args or ()))
```

```python
from collections.abc import Iterable

def run(args: Iterable[str] | None) -> None:
    call("tox", *(args or ()))
```

### Optional with a default after another

```python
def total(costs: list[float] | None, more: list[float] | None) -> float:
    return sum(costs or more or [])
```

```python
from collections.abc import Iterable

def total(costs: Iterable[float] | None, more: Iterable[float] | None) -> float:
    return sum(costs or more or [])
```

### Optional, with a comment and over lines

```python
def total(
    costs: (
        list[float]  # in pounds
        | None
    ),
) -> float:
    return sum(costs or [])
```

```python
from collections.abc import Iterable

def total(
    costs: (
        Iterable[float]  # in pounds
        | None
    ),
) -> float:
    return sum(costs or [])
```

## Left alone

### Mutated

```python
def add(items: list[str]) -> None:
    items.append("x")
```

### Subscript stored

```python
def put(row: dict[str, str]) -> None:
    row["x"] = "y"
```

### Stored on an object

```python
class Box:
    def __init__(self, items: list[str]) -> None:
        self.items = items
```

### Returned

```python
def same(items: list[str]) -> object:
    return items
```

### Returned when true

```python
def same(items: list[str]) -> object:
    return items or None
```

### Yielded

```python
def each(items: list[str]):
    yield from items
```

### Passed to another call

```python
import json


def dump(items: list[str]) -> str:
    return json.dumps(items)
```

### Given to isinstance

```python
def check(items: dict[str, str]) -> bool:
    return isinstance(items, dict)
```

### Given as a keyword argument

```python
def ordered(items: list[str], keys: dict[str, int]) -> list[str]:
    return sorted(items, key=keys.get)
```

### Compared

```python
def empty(items: list[str]) -> bool:
    return items == []
```

### Formatted

```python
def show(items: list[str]) -> str:
    return f"{items}"
```

### Sliced and returned

```python
def rest(items: list[str]) -> list[str]:
    return items[1:]
```

### Unused

```python
def ignore(items: list[str]) -> None:
    pass
```

### Reassigned

```python
def pick(items: list[str]) -> int:
    items = sorted(items)
    return len(items)
```

### A closure

```python
def later(items: list[str]):
    def count() -> int:
        return len(items)

    return count
```

### A lambda

```python
def later(items: list[str]):
    return lambda: len(items)
```

### A click command

```python
import click


@click.command()
@click.argument("names", nargs=-1)
def main(names: list[str]) -> None:
    for name in names:
        click.echo(name)
```

### An override

```python
from typing import override


class Base:
    def total(self, costs: list[float]) -> float:
        return 0.0


class Totals(Base):
    @override
    def total(self, costs: list[float]) -> float:
        return sum(costs)
```

### A method of a class with a base

```python
class Totals(Base):
    def total(self, costs: list[float]) -> float:
        return sum(costs)
```

### A protocol

```python
from typing import Protocol


class Totals(Protocol):
    def total(self, costs: list[float]) -> float:
        return sum(costs)
```

### Returns the type it takes

```python
def unique(items: list[str]) -> list[str]:
    return sorted(set(items))
```

### A set's own method

```python
def overlap(names: set[str], other: set[str]) -> bool:
    return names.isdisjoint(other)
```

### A dict merged

```python
def merged(row: dict[str, str]) -> int:
    return len(row | {"x": "y"})
```

### A dict reversed

```python
def last(row: dict[str, str]) -> list[str]:
    return [k for k in reversed(row)]
```

### A set indexed

```python
def first(names: set[str]) -> str:
    return names[0]
```

### Quoted

```python
def total(costs: "list[float]") -> float:
    return sum(costs)
```

### Optional the other way round

```python
def total(costs: None | list[float]) -> float:
    return sum(costs or [])
```

### Optional as the typing module spells it

```python
from typing import Optional


def total(costs: Optional[list[float]]) -> float:
    return sum(costs or [])
```

### A union of two collections

```python
def total(costs: list[float] | set[float]) -> float:
    return sum(costs)
```

### A union of three

```python
def total(costs: list[float] | int | None) -> float:
    return sum(costs or [])
```

### Optional and quoted

```python
def total(costs: "list[float] | None") -> float:
    return sum(costs or [])
```

### Optional and bound again

```python
def total(costs: list[float] | None = None) -> float:
    if costs is None:
        costs = []
    return sum(costs)
```

### Optional and only compared with None

```python
def given(costs: list[float] | None) -> bool:
    return costs is not None
```

### Optional through a conditional expression

```python
def total(costs: list[float] | None) -> float:
    return sum(costs if costs is not None else [])
```

### Optional and its default stored

```python
def total(costs: list[float] | None) -> float:
    kept = costs or []
    return sum(kept)
```

### Optional and its default returned

```python
def given(costs: list[float] | None) -> list[float]:
    return costs or []
```

### Optional as the default of another

```python
def total(costs: list[float] | None, more: list[float]) -> float:
    return sum(more or costs)
```

### Optional through an and

```python
def total(costs: list[float] | None) -> float:
    return sum(costs and [1.0])
```

### Optional compared with None by ==

```python
def total(costs: list[float] | None) -> float:
    if costs == None:
        return 0.0
    return sum(costs)
```

### Optional and returning the type it takes

```python
def unique(items: list[str] | None) -> list[str] | None:
    return sorted(set(items or []))
```

### Optional and returning that type without its None

```python
def unique(items: list[str] | None) -> list[str]:
    return sorted(set(items or []))
```

### Optional and its default given to a shadowed builtin

```python
from mylib import sorted


def count(items: list[str] | None) -> int:
    return len(sorted(items or []))
```

### Compared with None, and not optional

```python
def total(costs: list[float]) -> float:
    if costs is None:
        return 0.0
    return sum(costs)
```

### A default by or, and not optional

```python
def total(costs: list[float]) -> float:
    return sum(costs or [])
```

### Bare

```python
def total(costs: list) -> float:
    return sum(costs)
```

### Already abstract

```python
from collections.abc import Iterable


def total(costs: Iterable[float]) -> float:
    return sum(costs)
```

### A clashing name

```python
from typing import Iterable


def total(costs: list[float], more: Iterable[float]) -> float:
    return sum(costs) + sum(more)
```

### Variadic

```python
def total(*costs: list[float]) -> float:
    return sum(costs[0])
```

### Max of two

```python
def larger(a: list[int], b: list[int]) -> list[int] | int:
    return max(a, b)
```

### A class binds the abstract name

```python
class Box:
    Mapping = 3

    def get(self, row: dict[str, str]) -> str:
        return row["x"]
```

### A builtin's name bound

```python
from mylib import sorted


def ordered(items: list[str]) -> int:
    return len(sorted(items))
```

### A builtin's name bound around a slice

```python
from mylib import sorted


def ordered(items: list[str]) -> int:
    return len(sorted(items[1:]))
```

### A function named as a value

```python
import typer


def main(files: list[str]) -> None:
    for file in files:
        print(file)


if __name__ == "__main__":
    typer.run(main)
```

### A method named as a value

```python
from threading import Thread


class Worker:
    def run(self, jobs: list[str]) -> None:
        for job in jobs:
            print(job)

    def start(self) -> None:
        Thread(target=self.run, args=([],)).start()
```

### A function wrapped, returned, or registered

```python
from functools import lru_cache


def _size(names: frozenset[str]) -> int:
    return len(names)


size = lru_cache(maxsize=1024)(_size)


def counter() -> object:
    def count(rows: list[str]) -> int:
        return len(rows)

    return count


def first(rows: list[str]) -> bool:
    return bool(rows)


HANDLERS = {"first": first}
```

### A method another class of the module overrides

```python
class Base:
    def total(self, costs: list[float]) -> float:
        return sum(costs)


class Totals(Base):
    def total(self, costs: list[float]) -> float:
        costs.append(1.0)
        return 0.0
```

### A method a class of the module overrides through a generic base

```python
class Base[T]:
    def total(self, costs: list[float]) -> float:
        return sum(costs)


class Totals(Base[int]):
    def total(self, costs: list[float]) -> float:
        costs.append(1.0)
        return 0.0
```

### A method under an if in a class with a base

```python
import sys


class Totals(Base):
    if sys.version_info >= (3, 12):
        def total(self, costs: list[float]) -> float:
            return sum(costs)
```

### A tuple of a fixed length

```python
def total(pair: tuple[float, float], one: tuple[float], none: tuple[()]) -> float:
    return sum(pair) + sum(one) + len(none)
```

### A tuple of a type variable tuple

```python
def count[*Ts](items: tuple[*Ts]) -> int:
    return len(items)
```

### A tuple unpacked by an assignment

```python
def first(items: tuple[str, ...], pair: list[str]) -> str:
    head, *_ = items
    left, _right = pair
    return head + left
```

### A tuple matched

```python
def kind(items: tuple[str, ...]) -> str:
    match items:
        case ():
            return "none"
        case _:
            return "some"
```

### A tuple hashed, and one used as a key

```python
def cached(key: tuple[str, ...], other: tuple[str, ...], cache: Cache) -> int:
    return hash(key) + cache[other]
```

### A tuple concatenated

```python
def longer(items: tuple[str, ...]) -> int:
    return len(items + ("last",))
```

### A tuple formatted with %

```python
def show(items: tuple[str, ...]) -> str:
    return "%s and %s" % items
```

### A tuple compared

```python
def empty(items: tuple[str, ...]) -> bool:
    return items == ()
```

### A tuple given to isinstance, and one to startswith

```python
def check(value: object, kinds: tuple[type, ...], name: str, prefixes: tuple[str, ...]) -> bool:
    return isinstance(value, kinds) and name.startswith(prefixes)
```

### A tuple that catches

```python
def attempt(errors: tuple[type[Exception], ...]) -> bool:
    try:
        work()
    except errors:
        return False
    return True
```

### A tuple with a comment inside its brackets

```python
def total(
    costs: tuple[
        float,  # in pounds
        ...,
    ],
) -> float:
    return sum(costs)
```

### A tuple with parentheses inside its brackets

```python
def total(costs: tuple[(float, ...)]) -> float:
    return sum(costs)
```

### A tuple quoted

```python
def total(costs: "tuple[float, ...]") -> float:
    return sum(costs)
```

### A tuple of a function named as a value

```python
from functools import lru_cache


def _total(costs: tuple[float, ...]) -> float:
    return sum(costs)


total = lru_cache(maxsize=1024)(_total)
```

### Starred among a class's bases

```python
def make(bases: list[type]) -> type:
    class Made(*bases):
        pass

    return Made
```

### Starred in a subscript

```python
def cell(grid: Grid, at: list[int]) -> int:
    return grid[*at]
```

### Starred into a call, and stored

```python
def show(names: list[str], log: Log) -> None:
    print(*names)
    log.names = names
```

### Yielded from

```python
from collections.abc import Iterator


def each(names: list[str]) -> Iterator[str]:
    yield from names
```

### A list spread by two stars

```python
def make(options: list[str]) -> object:
    return build(**options)
```

### A dict as a display's value

```python
def wrap(row: dict[str, int]) -> dict[str, dict[str, int]]:
    return {"row": row}
```

# `explicit-override`

Each case is a module's text. Under Rewritten, a case is the text before and the text after; under Left alone, text
the codemod does not change. `test_explicit_override.py` runs them. The codemod adds an import where libcst puts it,
and ruff then sorts and spaces it, which a case does not show.

## Rewritten

### Overrides a base's method

```python
class Base:
    def run(self, argv: list[str]) -> int: ...


class Child(Base):
    def run(self, argv: list[str]) -> int:
        return 0
```

```python
from typing import override

class Base:
    def run(self, argv: list[str]) -> int: ...


class Child(Base):
    @override
    def run(self, argv: list[str]) -> int:
        return 0
```

### Through a generic base, a dataclass, and another class

```python
"""Rows."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Row(Generic[T]):
    def key(self) -> T: ...

    def size(self, *, deep: bool = False) -> int:
        return 0


class Named(Row[str]):
    def key(self) -> str:
        return ""


class Tagged(Named, Mapping[str, int]):
    # Every tag counts.
    def size(self, *, deep: bool = False) -> int:
        return 1
```

```python
"""Rows."""

from dataclasses import dataclass
from typing import override, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Row(Generic[T]):
    def key(self) -> T: ...

    def size(self, *, deep: bool = False) -> int:
        return 0


class Named(Row[str]):
    @override
    def key(self) -> str:
        return ""


class Tagged(Named, Mapping[str, int]):
    # Every tag counts.
    @override
    def size(self, *, deep: bool = False) -> int:
        return 1
```

### Async, with override imported already

```python
from typing_extensions import override


class Base:
    async def fetch(self, *urls: str, **options: object) -> None: ...


class Child(Base):
    async def fetch(self, *urls: str, **options: object) -> None: ...
```

```python
from typing_extensions import override


class Base:
    async def fetch(self, *urls: str, **options: object) -> None: ...


class Child(Base):
    @override
    async def fetch(self, *urls: str, **options: object) -> None: ...
```

### Beside methods it leaves alone

```python
from typing import override


class Base:
    def run(self) -> None: ...

    def stop(self) -> None: ...

    def wait(self) -> None: ...


class Child(Base):
    def __init__(self) -> None: ...

    def run(self) -> None: ...

    @override
    def stop(self) -> None: ...

    def wait(self, timeout=None) -> None: ...

    def other(self) -> None: ...
```

```python
from typing import override


class Base:
    def run(self) -> None: ...

    def stop(self) -> None: ...

    def wait(self) -> None: ...


class Child(Base):
    def __init__(self) -> None: ...

    @override
    def run(self) -> None: ...

    @override
    def stop(self) -> None: ...

    def wait(self, timeout=None) -> None: ...

    def other(self) -> None: ...
```

## Left alone

### A base from elsewhere

```python
import ast

from lib import Base


class Child(Base):
    def run(self) -> None: ...


class Visitor(ast.NodeVisitor):
    def visit_Name(self, node: ast.Name) -> None: ...
```

### A base below

```python
class Child(Base):
    def run(self) -> None: ...


class Base:
    def run(self) -> None: ...
```

### A base bound again, or not among the module's own statements

```python
import sys


class Base:
    def run(self) -> None: ...


Base = make(Base)


class Child(Base):
    def run(self) -> None: ...


if sys.platform == "win32":

    class Other:
        def run(self) -> None: ...

    class Mine(Other):
        def run(self) -> None: ...
```

### A base under a decorator that may replace it

```python
@register
class Base:
    def run(self) -> None: ...


class Child(Base):
    def run(self) -> None: ...
```

### A base's method bound again or deleted

```python
class Base:
    def run(self) -> None: ...

    run = staticmethod(run)

    def stop(self) -> None: ...

    del stop


class Child(Base):
    def run(self) -> None: ...

    def stop(self) -> None: ...
```

### A method with a decorator

```python
class Base:
    def size(self) -> int: ...

    def make(self) -> object: ...


class Child(Base):
    @property
    def size(self) -> int: ...

    @classmethod
    def make(cls) -> object: ...
```

### A method its class binds again

```python
class Base:
    def run(self) -> None: ...


class Child(Base):
    def run(self) -> None: ...

    run = wrap(run)
```

### A constructor

```python
class Base:
    def __init__(self) -> None: ...

    def __new__(cls) -> Base: ...


class Child(Base):
    def __init__(self) -> None: ...

    def __new__(cls) -> Child: ...
```

### An unannotated parameter

```python
class Base:
    def run(self, argv: list[str], *rest: str) -> None: ...


class Child(Base):
    def run(self, argv, *rest: str) -> None: ...


class Other(Base):
    def run(self, argv: list[str], *rest) -> None: ...
```

### A directive

```python
class Base:
    def run(self) -> None: ...

    def stop(self) -> None: ...


class Child(Base):
    def run(self) -> None:  # type: ignore[override]
        pass

    # pyright: ignore[reportIncompatibleMethodOverride]
    def stop(self) -> None: ...
```

### A star import

```python
from typing import *


class Base:
    def run(self) -> None: ...


class Child(Base):
    def run(self) -> None: ...
```

### Override bound otherwise

```python
from mylib import override


class Base:
    def run(self) -> None: ...


class Child(Base):
    def run(self) -> None: ...
```

### Override bound in a class

```python
class Base:
    def run(self) -> None: ...


class Child(Base):
    override = True

    def run(self) -> None: ...
```

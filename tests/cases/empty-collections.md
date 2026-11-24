# `empty-collections`

Each case is a module's text. Under Rewritten, a case is the text before and the text after; under Left alone, text
the codemod does not change. `test_empty_collections.py` runs them.

## Rewritten

### Returned

```python
def sources(paths: Iterable[Path]) -> list[Path]:
    found = []
    for path in paths:
        found.append(path)
    return found
```

```python
def sources(paths: Iterable[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        found.append(path)
    return found
```

### Joined

```python
def describe(name: str, tags: Iterable[str]) -> str:
    parts = []
    parts.append(name)
    parts.extend(tags)
    return " ".join(parts)
```

```python
def describe(name: str, tags: Iterable[str]) -> str:
    parts: list[str] = []
    parts.append(name)
    parts.extend(tags)
    return " ".join(parts)
```

### A set joined

```python
def describe(tags: Iterable[str]) -> str:
    seen = set()
    seen.update(tags)
    text = ", ".join(seen)
    return text
```

```python
def describe(tags: Iterable[str]) -> str:
    seen: set[str] = set()
    seen.update(tags)
    text = ", ".join(seen)
    return text
```

### Returned under an abstract type

```python
def names(rows: Iterable[Row]) -> Sequence[str]:
    found = []
    for row in rows:
        found.insert(0, row.name)
    return found
```

```python
def names(rows: Iterable[Row]) -> Sequence[str]:
    found: list[str] = []
    for row in rows:
        found.insert(0, row.name)
    return found
```

### A set returned

```python
def tags(rows: Iterable[Row]) -> AbstractSet[str]:
    found = set()
    for row in rows:
        found.add(row.tag)
    found.discard("")
    return found
```

```python
def tags(rows: Iterable[Row]) -> AbstractSet[str]:
    found: set[str] = set()
    for row in rows:
        found.add(row.tag)
    found.discard("")
    return found
```

### A dict returned or none

```python
def counts(words: Iterable[str]) -> Mapping[str, int] | None:
    seen = {}
    for word in words:
        seen[word] = 1
    if not seen:
        return None
    return seen
```

```python
def counts(words: Iterable[str]) -> Mapping[str, int] | None:
    seen: dict[str, int] = {}
    for word in words:
        seen[word] = 1
    if not seen:
        return None
    return seen
```

### Spelled from typing

```python
def names(rows: Iterable[Row]) -> Optional[List[str]]:
    found = []
    found.extend(row.name for row in rows)
    return found
```

```python
def names(rows: Iterable[Row]) -> Optional[List[str]]:
    found: list[str] = []
    found.extend(row.name for row in rows)
    return found
```

### Returned through sorted

```python
def tags(rows: Iterable[Row]) -> list[str]:
    found = set()
    for row in rows:
        found.add(row.tag)
    return sorted(found)
```

```python
def tags(rows: Iterable[Row]) -> list[str]:
    found: set[str] = set()
    for row in rows:
        found.add(row.tag)
    return sorted(found)
```

### Returned through tuple

```python
def sizes(rows: Iterable[Row]) -> tuple[int, ...]:
    found = []
    for row in rows:
        found.append(row.size)
    return tuple(found)
```

```python
def sizes(rows: Iterable[Row]) -> tuple[int, ...]:
    found: list[int] = []
    for row in rows:
        found.append(row.size)
    return tuple(found)
```

### Every known use

```python
def pending(rows: Iterable[Row], done: Row) -> list[Row]:
    found = []
    found.extend(rows)
    found.remove(done)
    found.reverse()
    found[0] = done
    del found[-1]
    assert found, "empty"
    while len(found) > 3 and done in found:
        found.clear()
    return found
```

```python
def pending(rows: Iterable[Row], done: Row) -> list[Row]:
    found: list[Row] = []
    found.extend(rows)
    found.remove(done)
    found.reverse()
    found[0] = done
    del found[-1]
    assert found, "empty"
    while len(found) > 3 and done in found:
        found.clear()
    return found
```

### Rules that agree

```python
def describe(tags: Iterable[str], *, joined: bool) -> Sequence[str]:
    parts = []
    parts.extend(tags)
    if joined:
        return " ".join(parts)
    return parts
```

```python
def describe(tags: Iterable[str], *, joined: bool) -> Sequence[str]:
    parts: list[str] = []
    parts.extend(tags)
    if joined:
        return " ".join(parts)
    return parts
```

### Async, in a method, nested in a block

```python
class Store:
    async def keys(self, prefix: str) -> list["Key"]:
        async with self.lock:
            found = []
            async for key in self.scan(prefix):
                found.append(key)
        return found
```

```python
class Store:
    async def keys(self, prefix: str) -> list["Key"]:
        async with self.lock:
            found: list["Key"] = []
            async for key in self.scan(prefix):
                found.append(key)
        return found
```

### Element type over lines

```python
def index(rows: Iterable[Row]) -> dict[
    str,
    tuple[int, int],
]:
    found = {}
    for row in rows:
        found[row.name] = row.span
    return found
```

```python
def index(rows: Iterable[Row]) -> dict[
    str,
    tuple[int, int],
]:
    found: dict[str, tuple[int, int]] = {}
    for row in rows:
        found[row.name] = row.span
    return found
```

### Keeps comments and layout

```python
def names(rows: Iterable[Row]) -> list[str]:
    found=[]  # every name
    parts = [ ] ; parts.append("x")
    found.extend(parts)
    return found
```

```python
def names(rows: Iterable[Row]) -> list[str]:
    found: list[str]=[]  # every name
    parts = [ ] ; parts.append("x")
    found.extend(parts)
    return found
```

### On the line of its function

```python
def names() -> list[str]: found = []; return found
```

```python
def names() -> list[str]: found: list[str] = []; return found
```

## Left alone

### No rule types it

```python
def collect(rows: Iterable[Row]) -> None:
    found = []
    found.append(rows)
    del found[0]
```

### No return annotation

```python
def names(rows):
    found = []
    found.append("x")
    return found
```

### A generator

```python
def names(rows: Iterable[Row]) -> Iterator[list[str]]:
    found = []
    found.append("x")
    yield found
    return found
```

### Bound again

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []
    found += ["x"]
    return found


def tags(found: list[str]) -> list[str]:
    found = []
    return found
```

### Tuple or chained

```python
def names(rows: Iterable[Row]) -> list[str]:
    found, other = [], []
    first = second = []
    first.append("x")
    return first
```

### Not a function's own

```python
NAMES = []


class Rows:
    found = []

    def __init__(self) -> None:
        self.found = []
```

### An item read back

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []
    found.append("x")
    print(found[0])
    return found
```

### Sorted or popped

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []
    found.sort()
    return found


def tags(rows: Iterable[Row]) -> list[str]:
    found = []
    found.pop()
    return found
```

### A method's value used

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []
    done = found.append("x")
    return found
```

### Passed to another call

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []
    fill(found)
    return found
```

### Iterated

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []
    for name in found:
        print(name)
    return found
```

### Read in a nested scope

```python
def names(rows: Iterable[Row]) -> list[str]:
    found = []

    def add(name: str) -> None:
        found.append(name)

    return found


def tags(rows: Iterable[Row]) -> list[str]:
    found = []
    return [tag for tag in rows if tag in found] and found
```

### Returned with something else

```python
def names(rows: Iterable[Row]) -> list[str] | None:
    found = []
    return found or None


def tags(rows: Iterable[Row]) -> tuple[list[str], int]:
    found = []
    return found, 0
```

### Quoted, bare, an alias, any, or a wider union

```python
def a(rows: Iterable[Row]) -> "list[str]":
    found = []
    return found


def b(rows: Iterable[Row]) -> list:
    found = []
    return found


def c(rows: Iterable[Row]) -> Names:
    found = []
    return found


def d(rows: Iterable[Row]) -> list[Any]:
    found = []
    return found


def e(rows: Iterable[Row]) -> list[str] | int:
    found = []
    return found


def f(rows: Iterable[Row]) -> Union[list[str], int]:
    found = []
    return found
```

### Not what the annotation takes

```python
def a(rows: Iterable[Row]) -> set[str]:
    found = []
    return found


def b(rows: Iterable[Row]) -> Iterable[str]:
    found = {}
    return found


def c(rows: Iterable[Row]) -> tuple[str]:
    found = []
    return tuple(found)


def d(rows: Iterable[Row]) -> list[str]:
    found = {}
    return sorted(found)


def e(rows: Iterable[Row]) -> str:
    found = {}
    return ", ".join(found)
```

### Rules that disagree

```python
def describe(tags: Iterable[int], *, joined: bool) -> Sequence[int]:
    parts = []
    if joined:
        return " ".join(parts)
    return parts
```

### An element type the function binds

```python
def names(rows: Iterable[Row]) -> list[Name]:
    found = []
    Name = str
    return found
```

### An element type the class binds

```python
class Rows:
    Name = str

    def names(self) -> list[Name]:
        found = []
        return found
```

### A directive

```python
def a(rows: Iterable[Row]) -> list[str]:  # type: ignore[override]
    found = []
    return found


def b(rows: Iterable[Row]) -> list[str]:
    found = []  # type: list[str]
    return found


def c(rows: Iterable[Row]) -> list[str]:
    found = []
    return found  # pyright: ignore[reportReturnType]


def d(
    rows: Iterable[Row],  # noqa: ARG001
) -> list[str]:
    found = []
    return found
```

### A builtin the module binds

```python
from mylib import list, sorted, str


def a(rows: Iterable[Row]) -> Sequence[int]:
    found = []
    return found


def b(rows: Iterable[Row]) -> Sequence[int]:
    found = set()
    return sorted(found)


def c(rows: Iterable[Row]) -> None:
    found = set()
    print(" ".join(found))
```

### A set given an item

```python
def tags(rows: Iterable[Row]) -> set[str]:
    found = set()
    found[0] = "x"
    return found
```

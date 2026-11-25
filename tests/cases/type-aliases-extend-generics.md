# `type-aliases`, with `extend-generics`

Each case is a module's text in a project whose `extend-generics` is `["NDArray", "Table"]`. Under Rewritten, a case
is the text before and the text after; under Left alone, text the codemod does not change. `test_type_aliases.py`
runs them.

## Rewritten

### Named generic

```python
Rows = Table[Row]
```

```python
type Rows = Table[Row]
```

### Named generic reached through a module

```python
Grid = npt.NDArray[np.float64]
```

```python
type Grid = npt.NDArray[np.float64]
```

### Beside the standard library's

```python
Index = dict[str, Table["Row"]]
Rows = Table[Row] | None
Grids = list[npt.NDArray[np.float64]]
```

```python
type Index = dict[str, Table["Row"]]
type Rows = Table[Row] | None
type Grids = list[npt.NDArray[np.float64]]
```

## Left alone

### Generic not named

```python
Grid = np.ndarray[int]
Rows = Frame[Row]
```

### Named generic that holds no type

```python
First = Table[0]
```

### Named generic read at run time

```python
Rows = Table[Row]
EMPTY = Rows()
```

### Generic over a type variable

```python
from typing import TypeVar

T = TypeVar("T")
Rows = Table[T]
```

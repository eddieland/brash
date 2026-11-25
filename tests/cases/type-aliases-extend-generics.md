# `type-aliases`, with `extend-generics`

Each case is a module's text in a project whose `extend-generics` is `["numpy.typing.NDArray", "app.tables.Table"]`.
Under Rewritten, a case is the text before and the text after; under Left alone, text the codemod does not change.
`test_type_aliases.py` runs them.

## Rewritten

### Imported by name

```python
from app.tables import Table

Rows = Table[Row]
```

```python
from app.tables import Table

type Rows = Table[Row]
```

### Imported under another name

```python
from numpy.typing import NDArray as Array

Grid = Array[np.float64]
```

```python
from numpy.typing import NDArray as Array

type Grid = Array[np.float64]
```

### Through its module under another name

```python
import numpy.typing as npt

Grid = npt.NDArray[np.float64]
```

```python
import numpy.typing as npt

type Grid = npt.NDArray[np.float64]
```

### Through its module imported from its package

```python
from numpy import typing as npt

Grid = npt.NDArray[np.float64]
```

```python
from numpy import typing as npt

type Grid = npt.NDArray[np.float64]
```

### Through its package

```python
import numpy as np

Grid = np.typing.NDArray[np.float64]
```

```python
import numpy as np

type Grid = np.typing.NDArray[np.float64]
```

### Through its module in full

```python
import numpy.typing

Grid = numpy.typing.NDArray[numpy.float64]
```

```python
import numpy.typing

type Grid = numpy.typing.NDArray[numpy.float64]
```

### Relative import

```python
from .tables import Table

Rows = Table[Row]
```

```python
from .tables import Table

type Rows = Table[Row]
```

### Relative import from further up

```python
from ..app.tables import Table

Rows = Table[Row]
```

```python
from ..app.tables import Table

type Rows = Table[Row]
```

### Relative import of its module

```python
from . import tables

Rows = tables.Table[Row]
```

```python
from . import tables

type Rows = tables.Table[Row]
```

### Imported for type checking

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.tables import Table

Rows = Table[Row]
```

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.tables import Table

type Rows = Table[Row]
```

### Imported twice from the same place

```python
import numpy
import numpy.typing

Grid = numpy.typing.NDArray[numpy.float64]
```

```python
import numpy
import numpy.typing

type Grid = numpy.typing.NDArray[numpy.float64]
```

## Left alone

### Not imported

```python
Rows = Table[Row]
Grid = npt.NDArray[np.float64]
```

### Same name from another module

```python
from rich.table import Table
from .frames import Table as Frame

Rows = Table[Row]
Frames = Frame[Row]
```

### Another name of its module

```python
import numpy.typing as npt

Like = npt.ArrayLike[np.float64]
```

### Brought by a star

```python
from numpy.typing import *

Grid = NDArray[np.float64]
```

### Imported from two places

```python
from app.tables import Table

if legacy:
    from old.tables import Table

Rows = Table[Row]
```

### Named generic that holds no type

```python
from app.tables import Table

First = Table[0]
```

### Named generic read at run time

```python
from app.tables import Table

Rows = Table[Row]
EMPTY = Rows()
```

### Generic over a type variable

```python
from typing import TypeVar

from app.tables import Table

T = TypeVar("T")
Rows = Table[T]
```

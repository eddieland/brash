# brash codemod ideas

As of 2026-11-24.

Three ideas are worth building, each in a narrowed form: `empty-collections`, `explicit-override`, and star-unpacking
plus `tuple[X, ...]` in `general-params`. Two more are sound as opt-in codemods, for a project that holds the
convention. Twelve ideas are shelved, 24 are untested, and three defects turned up in
the codemods brash already has.

## Next steps, in order

The order for whoever picks this up next. Each step is one PR unless it says otherwise. It puts what is wrong in
shipped code first, then what unblocks the most, then the ideas by strength of evidence. Tick a step here in the PR
that does it.

The prototypes and the corpus were not kept, so every step that builds a codemod starts by writing it again from its
entry, and its PR says how the numbers it relies on were checked again, or that they were not.

1. **Fix the defects in the codemods brash ships.** They write wrong code in projects today, the fixes are known and
   each is a few lines with a case. See "Defects found in the existing codemods".
   - [x] `type-aliases`: leave alone an alias with a quoted name directly inside a `Union` or `Optional`. First,
     because the result raises at run time, and two corpus aliases hit it.
   - [x] `general-params`: check the slice's parent for a shadowed builtin, not only the parameter's own.
   - [ ] `general-params`: leave alone a function the module names as a value. This one waits on decision A below,
     because it changes what the codemod rewrites today.
   - [x] brash's own two parameters, `_choose` and `_with_imports`. Trivial, and by hand.
2. **Let a codemod be off by default.** `extend-select` exists since #12, so a project can already name a codemod to
   run as well. What is missing is the other half: a codemod that says it does not run unless `select` or
   `extend-select` names it, as `MINIMUM_PYTHON` says what it needs. It is small, it unblocks steps 5 and 7, and it
   settles how every later idea of "taste" is judged. It changes `brash.command.Command`, so its PR says so.
   - [x] Done: a codemod that sets `OPT_IN = True` runs only where `select`, `extend-select` or `--only` names it.
3. **Build `empty-collections`.** The strongest evidence of any idea, and nothing outside the function can see the
   rewrite. Keep the join rule, which supplies half the sites and was right in the sample. Leave out the
   cross-function rule, which is the larger change.
   - [x] Done, with the join rule and without the cross-function one. See "Built" in its entry.
4. **Extend `general-params` with star-unpacking and `tuple[X, ...]`.** After the third defect of step 1, since both
   rest on the named-as-a-value rule. Then look again at the optional-collections rider, which is 40 lines on top
   and waits on decision C.
5. **Build `explicit-override`, off by default.** After step 2. It is sound, with no wrong site and no new
   diagnostic, but only 3 of 30 projects use `@override`, it cannot fire on brash's own code, and its tester gave it
   0.6.
   - [x] Done, off by default. See "Built" in its entry.
6. **Take the `Union[...]` and `Optional[...]` rider into `type-aliases`.** About 12 lines once the first defect of
   step 1 has added the quoted-member guard it shares. Rare, so only if a maintainer says the rate bar does not apply
   to one more row of a table.
7. **The two opt-in ideas**, after step 2, each behind a decision. Narrower `Sequence` and `Collection` first: it is
   the AGENTS.md rule and the only idea that fires on brash, but it needs brash to remove an import it orphans
   (decision D). `docstring-types` second: it needs a Google docstring parser and decision E.
8. **Test before building anything else.** Of the untested ideas, `todo-colons` is the one to try first: smallest,
   safest, and ruff reports it with no fix. `section-order` is next if step 7 brings a docstring parser. Give the
   others no time until someone asks for one: fifteen of eighteen tested ideas failed.

Not to do: anything under Shelved without the fact its "Reopen if" names, and anything under "Rejected without
testing".

Decisions a maintainer has to make, with what this document's evidence suggests. An agent does not settle these by
building; it asks, or builds the smaller form and says so in the PR.

| | Decision | Blocks | The evidence suggests |
| --- | --- | --- | --- |
| A | Does the named-as-a-value rule apply to all of `general-params`, removing 49 of its 417 corpus sites? | Steps 1 and 4 | Yes: the typer case is a real break, and one rule for the whole codemod is consistent |
| B | Was "unpacked" left alone in `general-params` on purpose? | Step 4 | Unknown; 78 of 82 sampled rewrites were right |
| C | Is the pinned "Optional" case in `tests/cases/general-params.md` spelling or intent? | The rider in step 4 | Unknown |
| D | May a codemod remove an import it orphans? | Step 7 | Needed: without it 31 of 66 files end with an unused import |
| E | May brash edit `__doc__`? | Step 7, and the docstring family | Only as opt-in; no corpus break was found, three were constructed |
| F | Do `mock-namespace` and `lazy-logging` ship in brash, off by default, or stay a project's own? | Nothing yet | Not before step 2 |

## How to use this document

Every idea has one entry, written to the same template, and one row in the index. To add an idea, copy the template,
fill what is known, and give it the status Untested.

| Status | Meaning |
| --- | --- |
| Build | Tested on real code and worth implementing in the form the entry describes |
| Opt-in | Sound for a project that holds the convention, which most do not; build it to run only where selected |
| Rider | Sound and small, but too rare to justify on its own; build with its parent or not at all |
| Shelved | Tested and not worth building; the entry says what would reopen it |
| Untested | A written idea with no evidence yet |
| Rejected | Ruled out without testing because it fails the bar by its nature |

The entry template:

- **Motivation**: the convention it holds, and who already asks for it (a lint rule, a type checker, AGENTS.md).
- **Rewrite**: a before and after, as small as will show it.
- **Leaves alone**: what it must not touch, and why.
- **Evidence**: sites and files in the corpus, how many sampled rewrites were right, what the type checkers said before
  and after.
- **Limitations**: what it cannot do, and breaks no one-module rule can exclude.
- **Size**: estimated lines, and where a prototype is.
- **Open decisions**: questions only a maintainer can settle.
- **Reopen if**: for a shelved idea, the fact that would change the verdict.

Numbers in this document come from one day of testing on 2026-11-24. "Sites" means places the codemod would rewrite.
"Right" means a person reading the rewrite judged it what the maintainer would have written; "debatable" and "wrong" are
the other two grades.

## The bar

An idea belongs in brash only if it meets all seven of these. They come from the README and AGENTS.md, and every idea
here was judged against them.

1. Any Python 3.12+ project could adopt the convention.
2. It decides from one module's text and syntax, and never imports or runs code.
3. It is conservative: it leaves alone anything it cannot prove.
4. A second run changes nothing, also after `ruff check --select I --fix` and `ruff format`.
5. It is a standing convention with a cheap `wants(source)`, not a one-off migration.
6. ruff does not already fix it.
7. It is deterministic and writes no prose.

The README adds two exclusions: a rewrite that needs a value's type across modules, and one that changes what the code
does in a way a person should decide each time.

### What survived testing

Testing showed the seven rules are necessary but not enough. Fifteen of the eighteen ideas tested in depth failed on
something the rules do not name. The ones that survived share four traits:

- **Something already asks for it.** A strict type checker or a lint reports the site and offers no fix.
- **Its effect stays inside what it touches.** Annotating a local or widening a parameter is invisible to callers. A
  return type, a constant's type or a docstring is not.
- **A table of known reads decides it.** As `general-params` does: list the uses that are provably safe and leave alone
  any other.
- **It fires often enough where it is wanted.** Below about 1.5 sites per 100 files, in the projects that hold the
  convention, maintainers rarely see it run and the cases cost more than they return.

### Default-on and opt-in

How many projects hold a convention is not part of the bar. A project turns a codemod off with `ignore` and names the
ones it wants with `select`, so a codemod that suits one project in ten is still worth having. The question for such an
idea is which way it defaults, not whether it exists.

An earlier version of this document shelved ideas because they "fire where they are not wanted". That was a mistake, and
two ideas moved to Opt-in when it was corrected. Two things still disqualify an idea, and neither is fixed by a
switch:

- It is wrong at some sites in a project that does want the convention, with no rule to tell which.
- It breaks something in a module it cannot see.

**Done.** `extend-select` shipped in #12, so a project can name a codemod to run on top of the defaults, and a
codemod says it is off by default with `OPT_IN = True` on its `brash.command.Command`, step 2 of the next steps. Such
a codemod runs only where `select` or `extend-select` names it, or `--only` does.

### How ideas failed

| Failure                                          | Example                                                                                                                 |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| The rewrite overrides a choice made at that site | `sorted-sets` reordered sets whose order meant something in 12 of 64 samples                                            |
| Another module can see it                        | `object-params` drew 13 new errors at callers                                                                           |
| A type checker reacts to the edit itself         | pyrefly retypes unannotated parameters once `@override` is present; mypy starts checking a body at its first annotation |
| The provable form is too rare                    | `frozen-constants` rewrote 9 sites in 7,436 files                                                                       |
| ruff is already most of the way there            | ruff's own fix does 81% of `single-with` at 120 columns                                                                 |
| It is a migration                                | `type-params` fires zero times on a codebase that has converted                                                         |
| A person must choose                             | `raise-from`: `from e` or `from None`                                                                                   |

One more pattern holds for every survivor: it writes the provable fraction of a convention, not the whole of it. A
passing `brash --check` then says less than it seems to.

## Index

One row per idea. "Kind" is New for a new codemod, or the name of the existing codemod it extends. Rejected classes of
ideas are listed in their own section. A deciding fact of "taste" or "contested" on an untested idea argues against
running it by default, not against building it as opt-in.

| Idea | Kind | Status | What it does | Deciding fact |
| --- | --- | --- | --- | --- |
| `empty-collections` | New | Build | Annotates an empty list, dict or set from the return annotation or a `join` | 214 sites, 53 of 54 right, invisible outside the function |
| `explicit-override` | New | Build | `@override` where the base class is in the same module | 775 sites, 0 wrong, no new diagnostics |
| Star-unpacking and `tuple[X, ...]` | `general-params` | Build | Counts `*p` and `**p` as reads; widens `tuple[X, ...]` | 157 sites, 78 of 82 right |
| `Union[...]` and `Optional[...]` aliases | `type-aliases` | Rider | Takes an alias ruff reports and cannot fix | 59 of 59 right, about 12 lines, but 59 sites |
| Optional collections | `general-params` | Rider | Widens `list[X] \| None` | 27 of 31 right, but 31 sites and undoes a pinned case |
| `sorted-sets` | New | Shelved | Sorts a set display's elements | 12 of 64 destroyed a meaningful order |
| `single-with` | New | Shelved | Merges nested `with` statements | ruff's fix already does 81% at 120 columns |
| `self-returns` | New | Shelved | `-> Self` on a method that returns `self` | 8 wrong sites; 3 new mypy errors in jinja2 |
| `frozen-constants` | New | Shelved | List or set constant to tuple or frozenset | 9 sites in 7,436 files |
| `raise-from` | New | Shelved | Adds `from e` to a `raise` in a handler | 29 of 59 right; a person must choose |
| `newspaper-order` | New | Shelved | Moves a private helper below its first caller | Best rule puts a drifted helper back exactly 17 of 45 times in brash, 147 of 201 in tox |
| `method-order` | New | Shelved | The same, for methods in a class | Not run on its own; falls with `newspaper-order` |
| `typed-fixtures` | New | Shelved | Annotates test parameters from fixtures | New type errors at 23 of 150 sites |
| `type-params` | New | Shelved | `TypeVar` to PEP 695 syntax | A one-off migration; a type error in cattrs |
| `object-params` | New | Shelved | `Any` to `object` on a parameter only inspected | 13 new errors at callers |
| `docstring-types` | New | Opt-in | Drops a docstring type that repeats the annotation | 0 wrong of 49; 16 of 16 right in projects that hold the convention |
| `dunder-signatures` | New | Shelved | Annotates `__exit__`, `__hash__` and the like | 9 of 59 wrong, 39 debatable |
| Narrower `Sequence` and `Collection` | `general-params` | Opt-in | `Sequence[X]` to `Iterable[X]` where reads allow | The AGENTS.md rule; finds 2 parameters in brash; orphans an import in 31 of 66 files |
| `#:` above `self.x` in `__init__` | `doc-comments` | Shelved | Doc comment for an instance attribute | 23 of 45 comments say what the attribute is |
| `section-order` | New | Untested | Google docstring sections in the guide's order | Rate measured only: 1.29 docstrings per 100 files |
| `returns-none` | New | Untested | Removes a Returns section that says `None` | Rate only: all 104 hits in litestar |
| `args-order` | New | Untested | Args entries in signature order | Rate only: 0.50 per 100 files |
| `section-names` | New | Untested | `Parameters:` to `Args:` and the like | Rate only: 0.22 per 100 files |
| `todo-colons` | New | Untested | `# TODO x` to `# TODO: x` | Safest and smallest; ruff reports, no fix |
| `narrow-try` | New | Untested | Moves a trailing `return` out of a `try` body | TRY300 is often switched off |
| `final-attributes` | New | Untested | `Final` on a private attribute assigned once | Nothing asks for it; likely noise |
| `match-chains` | New | Untested | Equality `if`/`elif` chain to `match` | Taste; wide diffs |
| `digit-groups` | New | Untested | `1500000` to `1_500_000` | Cannot tell a quantity from an identifier |
| `strenum-values` | New | Untested | `auto()` to the written value in a `StrEnum` | Contested preference |
| `mock-namespace` | New | Untested | `from unittest.mock import patch` to `mock.patch` | README names it a project's own codemod |
| `pytest-namespace` | New | Untested | `from pytest import raises` to `pytest.raises` | Same machinery, very little work to do |
| `raises-match` | New | Untested | Folds an assert on the message into `match=` | Slightly weakens the assertion |
| `param-ids` | New | Untested | `ids=[...]` to `pytest.param(..., id=...)` | Taste; nothing reports it |
| `patch-blocks` | New | Untested | `@mock.patch` decorators to one `with` block | Largest diff brash would write |
| `concrete-returns` | New | Untested | Narrows an abstract return to what is built | Narrowing a return can break unseen callers |
| `never-returns` | New | Untested | `-> None` to `-> Never` when the body always raises | Rare; reaches callers |
| `lazy-logging` | New | Untested | f-string in a logging call to `%s` arguments | README names it a project's own; ruff fixes the simple case in preview |
| `keyword-flags` | New | Untested | Trailing booleans of a private function keyword-only | Changes a signature on the strength of an underscore |
| `enumerate-loops` | New | Untested | Hand-kept counter to `enumerate` | Almost never fires once safe |
| `final-classes` | New | Untested | `@final` on a private class nothing derives from | Little gain where it is decidable |
| `attribute-docstrings` | New | Untested | String below a name to `#:` above it | Sides against the more widely read spelling |
| `positive-conditions` | New | Untested | Swaps branches of `if not ...: else:` | A person should decide; churns blame |
| `named-expressions` | New | Untested | Folds an assignment into the `if` below it | Contested taste |

## Build

Three ideas passed testing. None fires on brash's own code today, because brash already holds each convention by hand.
Suggested order: `empty-collections` first, since nothing outside the function can observe it.

### empty-collections

**Motivation.** An empty `[]`, `{}` or `set()` has no element type, so strict pyright and basedpyright report it and
every `append` after it. 47% of the corpus's empty locals are already annotated by hand, and brash annotates all 10 of
its own. No tool writes the annotation: `pyrefly infer` leaves the example unchanged and ruff has no rule.

**Rewrite.**

```python
def sources(paths: Iterable[Path]) -> list[Path]:
    found = []  # becomes: found: list[Path] = []
    for path in paths:
        found.append(path)
    return found


def describe(name: str, tags: Iterable[str]) -> str:
    parts = []  # becomes: parts: list[str] = []
    parts.append(name)
    parts.extend(tags)
    return " ".join(parts)
```

The type comes from one of three places: the name is returned under `list[X]`, `dict[K, V]`, `set[X]` or an abstract
type of them; it is returned whole through `sorted`, `list`, `tuple`, `set` or `frozenset`; or a string literal joins
it.

**Leaves alone.**

- A name bound more than once, a parameter, a tuple or chained assignment, and anything at module or class level or on
  `self`.
- A name used outside a table of known uses. The table is `.append`, `.extend`, `.insert`, `.add`, `.update`, `.remove`,
  `.discard`, `.clear`, `.reverse` as statements, `name[k] = v`, `del name[k]`, `return`, `len`, a truth test, `in`, and
  the join. An item read back, `.sort()`, `.pop()`, or passing the name to any other call all exclude it.
- A return annotation that is quoted, names `Any`, is a bare `list`, is an alias, or is a union other than with `None`.
- An annotation naming something the function or its class rebinds.
- A function with no return annotation, a generator, and any function with a checker or lint directive on its header or
  `return`.
- Two rules that disagree, and a module that rebinds `list`, `dict`, `set`, `str`, `len` or the builtin used.

**Evidence.**

- 214 sites in 147 of 7,436 files, across 26 of 30 projects. 134 of them are `list[str]`, and the join rule supplies
  104.
- 53 of 54 sampled rewrites were right. The one miss is tox, which spells such locals `Final[list[str]]`.
- Strip test: with the annotation removed from all 1,473 hand-annotated empty locals, the prototype restored 170, none
  as a different type and 154 character for character.
- Across 18 projects, basedpyright lost 497 unknown-type reports and gained 30. Of the 30, 24 are rewordings, 3 repeat
  what the return annotation already draws, and 3 are real. mypy and pyrefly changed by 5 diagnostics in total.
- A second run changes nothing, also after ruff's import fix and format at 88 and 120 columns.
- Independent check: on a 32-function adversarial module written separately, all 14 rewrites had the right type, and two
  mypy errors that asked for exactly this annotation went away.

**Limitations.**

- It types 12.7% of unannotated empty locals. It would restore 6 of brash's own 10.
- Only pyright-family checkers ask for these sites. mypy and pyrefly infer the type from the first `append`.
- 3 of 171 checked sites drew a new basedpyright error at an `append` (cattrs twice, aiohttp once), where pyright
  disagrees with a return annotation it had never checked. No rule excludes these.
- It copies the return annotation's spelling, so `Dict[str, Optional[str]]` is copied too. ruff then fixes the copy.
- 18 of the 214 sites are loops ruff's PERF401 would turn into a comprehension, where the annotation is then unneeded.

**Size.** About 350 lines.

**Open decisions.** Whether the join rule belongs, since without it the rate falls by half. Whether to take an empty
collection passed to a typed function of the same module, which covers 3 of brash's 4 misses but needs resolution across
functions.

**Built** in `src/brash/empty_collections.py`, about 550 lines with its docstrings, from this entry and not from the
prototype, which was not kept. It has the three rules and every exclusion above, and runs by default. The corpus was not
kept either, so the numbers above were not reproduced. Instead it was run on the sdists of 14 of the 30 projects
(httpx, rich, click, attrs, pytest, black, starlette, werkzeug, flask, jinja2, typer, pip-tools, hatch, structlog):
108 sites in 74 of 2,385 files, 88 of them `list[str]`. Every output parses, and a second run changes nothing. All 10
rewrites read in context were right. No type checker was run on the result, and brash's own code has no site.

### explicit-override

**Motivation.** `@override` makes a type checker report a method that no longer overrides anything after a rename. mypy
(`explicit-override`), pyrefly (`missing-override-decorator`) and basedpyright (`reportImplicitOverride`) each report a
missing one, and none writes it. brash uses `@override` throughout.

**Rewrite.**

```python
class Base:
    def run(self, argv: list[str]) -> int: ...


class Child(Base):
    def run(self, argv: list[str]) -> int:  # gains @override above it
        return 0
```

It adds `from typing import override` when the module does not have it.

**Leaves alone.**

- A method whose base class is not defined in the same module. This is most overrides.
- A method with an unannotated parameter. pyrefly retypes such parameters from the base once `@override` is present,
  which drew 7 new errors in black and pytest.
- A module that binds the name `override` in any scope. A class attribute of that name makes the decorator resolve to
  it.
- A method with a checker or lint directive on or above its header.
- A base defined below the subclass, a base under a class decorator that replaces it, a module with a star import, and a
  base method that is deleted or rebound.

**Evidence.**

- 775 sites in 120 files with the seven exclusions above.
- 48 of 51 sampled rewrites were right, 3 debatable, none wrong.
- No new diagnostic from pyrefly, mypy `--strict` (17 packages) or basedpyright (all 30 projects).
- A second run changes nothing, also after ruff's import fix and format.
- Tested by a skeptic independent of the proposer. Confidence 0.6 that it is worth building.

**Limitations.**

- It clears 13.5% of basedpyright's missing-override reports, 14.6% of pyrefly's and 23.2% of mypy's. It clears none of
  brash's own 29, whose bases are in LibCST.
- 76 of the 120 files it rewrites still hold an unmarked override afterwards.
- Only 3 of the 30 projects use `@override` at all. That argues for opt-in, not against building it.
- A module that star-imports a rewritten one gains the name `override`. Every codemod that adds an import shares this.
- The corpus test suites were not run, so run-time safety rests on the decorator's source and three checkers agreeing.

**Size.** About 320 lines.

**Open decisions.** Whether a codemod that cannot fire on brash's own code is worth carrying. Whether it runs by default
or is opt-in.

**Built** in `src/brash/explicit_override.py`, off by default (`OPT_IN = True`) as step 5 says, from this entry and not
from the prototype, which was not kept. It has every exclusion above, and two more: a method with any decorator, since
where `@override` goes among others is a choice, and `__init__` and `__new__`, which brash itself leaves unmarked. The
corpus was not kept, so the numbers above were not reproduced. Instead it was run on the sdists of 14 of the 30
projects (those listed for `empty-collections`): 361 sites in 57 of 2,385 files, in 13 of the 14 projects. Every
output parses, and a second run changes nothing. All 12 sampled sites override a method an ancestor in the module
defines. No type checker was run on the result, and brash's own code has no site.

### general-params: star-unpacking and tuple\[X, ...\]

**Motivation.** AGENTS.md asks a parameter to take the most general type its body needs. `general-params` leaves alone a
parameter that is star-unpacked, the sole blocker for 69 parameters, and any parameter annotated `tuple[X, ...]`, of
which there are 270.

**Rewrite.**

```python
# before
def run(args: tuple[str, ...], env: dict[str, str]) -> None:
    subprocess.run(["tox", *args], env={**os.environ, **env}, check=True)


# after
def run(args: Iterable[str], env: Mapping[str, str]) -> None:
    subprocess.run(["tox", *args], env={**os.environ, **env}, check=True)
```

`*p` in a call's arguments or in a list, tuple or set display counts as one pass. `**p` counts as a mapping read. A
`tuple[X, ...]` parameter is treated as a `list[X]` one is.

**Leaves alone.**

- Everything `general-params` leaves alone today.
- A tuple of fixed length, `tuple[()]`, and `tuple[*Ts]`.
- A tuple used as a tuple: unpacked by assignment, matched, hashed, used as a key, `%`-formatted, concatenated,
  compared, or passed to `isinstance`, `except` or `str.startswith`.
- `*p` in class bases or assignment targets, and `yield from p`.
- New rule: a function whose name the module reads other than to call it. aiohttp wraps one with
  `lru_cache(maxsize=1024)(f)`, which needs the tuple for hashing.
- A `tuple[...]` annotation with a comment inside its brackets.

**Evidence.**

- 157 sites in 100 files with the new rule, 167 in 105 without.
- 78 of 82 sampled rewrites were right. All 44 non-test sites were read: 40 right, 4 debatable.
- No new diagnostic from pyrefly, mypy or basedpyright strict across all 23 projects with a site.
- Independent check: on a 20-function adversarial module, all 4 rewrites were right, every tuple-as-tuple case was left
  alone, and the three checkers reported no change.

**Limitations.**

- 113 of the 157 sites are in test files, and 70 are tox's. In other code it fires about once per 100 files.
- No lint or checker asks for it. It rests on the AGENTS.md convention alone.
- A tuple is chosen on purpose more often than a list. The 4 debatable sites include pydantic parameters that mirror a
  class's `__bases__`.
- A base-less class meant for subclassing elsewhere, such as structlog's `BoundLoggerBase`, is the parent's existing
  blind spot and remains one.

**Size.** An extension of `general_params.py`.

**Open decisions.**

- The parent's docstring lists "unpacked" among the uses it leaves alone. Was that deliberate?
- The new named-as-a-value rule would also remove 49 of the parent's own 417 corpus sites. Adopt it for the extension
  alone, which is inconsistent, or for the whole codemod, which changes existing behaviour?

## Riders

Two extensions are sound and small but rare. Each is worth building only alongside its parent.

### type-aliases: Union\[...\] and Optional\[...\] aliases

**Motivation.** ruff's UP007 and UP045 report `StrPath = Union[str, os.PathLike[str]]` and offer no fix on a
module-level assignment, even with unsafe fixes. Once the alias is a `type` statement, ruff's safe fix writes the `|`.
This is the only extension a lint already asks for.

**Rewrite.** `NoneStr = Optional[str]` becomes `type NoneStr = Optional[str]`, which ruff then turns into `type NoneStr
= str | None`.

**Leaves alone.** Everything `type-aliases` leaves alone today. Also a `Union` or `Optional` with a quoted name as a
direct member, since ruff would write `"Node" | int`, which raises when evaluated; 24 corpus aliases stay for this. Also
`Union[X]` with one member, which basedpyright rejects in a `type` statement.

**Evidence.** 59 sites in 30 files, all 59 read and all right. pyrefly and mypy report nothing new on five projects.
basedpyright reports 2 new errors in aiohttp, both traced to a dependency that was not installed for the check.

**Limitations.** 0.79 sites per 100 files and none in brash. It is a backlog more than a standing convention: a 3.12+
project that selects ruff's UP rules has already cleared these by hand. 19 of the 59 are public pydantic v1 names that
users' models read at run time, the parent's stated one-module limit. httpx's `_types.py` ends half converted, 7
rewritten and 8 kept.

**Size.** About 12 lines in `_is_alias`.

**Reopen if** the rate bar is judged not to apply to one more entry in a table. The quoted-member guard it needs is in the
parent already, as the fix of the first defect.

### general-params: optional collections

**Motivation.** 515 parameters in the corpus are spelled `list[X] | None`, and `general-params` reads none of them.

**Rewrite.** `def total(costs: list[float] | None) -> float: return sum(costs or [])` becomes `costs: Iterable[float] |
None`. It knows `p is None`, `p is not None`, and a value that flows through `p or other` into a known read.

**Leaves alone.** A parameter rebound (`if p is None: p = []`), stored, returned or assigned, which are the commonest
things done with an optional collection. Also a value that flows through a conditional expression, which drew 2 new
basedpyright errors in pip-tools.

**Evidence.** 31 sites in 24 files, all read: 27 right, 4 debatable. The 4 are litestar constructors where `set[str] |
None` becomes `Collection[str] | None` and so admits a bare `str`. One new basedpyright diagnostic across seven
projects, beside an unresolved import.

**Limitations.** 0.42 sites per 100 files. The case "Optional" in `tests/cases/general-params.md` pins exactly this
rewrite as left alone.

**Size.** About 40 lines on top of the star-unpacking extension.

**Reopen if** the star-unpacking extension is built and the pinned case is judged a matter of spelling, not intent.

## Opt-in

Two ideas are sound for a project that holds the convention and would be noise in one that does not. Each should be
built to run only where a project selects it, as `OPT_IN = True`, which step 2 of the next steps added.

### general-params: narrower Sequence and Collection

**Motivation.** The AGENTS.md rule applied to a parameter that is already abstract: `Sequence[X]` that is only iterated
needs only `Iterable[X]`. It is the only idea here that fires on brash's own code.

**Rewrite.** `def _with_imports(block, names: Sequence[str])`, whose body is one comprehension over `names`, becomes
`names: Iterable[str]`.

**Leaves alone.** Everything `general-params` leaves alone today. A parameter whose reads need what it already says:
indexing, slicing, `reversed`, `.index` or `.count` of a Sequence; `len`, `in`, a truth test or two passes of a
Collection. A dotted head such as `t.Sequence`. `AbstractSet`, `Mapping` and the mutable types.

**Evidence.**

- 99 sites in 66 files: 52 in public functions, 29 in private ones, 18 in tests.
- 28 of 34 sampled rewrites were right. The 6 misses replace `Sequence` where order, an index or a public contract was
  the point, such as a command line that would then accept a set.
- No new type errors from pyrefly or mypy on six projects.
- Both of brash's own hits are right by its rule; see the defects section.

**Limitations.**

- Authors use `Sequence` to mean "a read-only list": of 128 plain `Sequence` parameters with only known reads, 20 need
  one. A project that opts in is choosing to give that meaning up.
- It leaves an unused import in 31 of the 66 files, which ruff's F401 and basedpyright then report and `make fmt` does
  not remove. It needs to remove the import it orphans, and no brash codemod removes one today.
- `Sequence` to `Collection` drops "ordered", and nothing in the syntax says when order mattered.

**Size.** An extension of `general_params.py`, behind its own name so it can be selected apart from the parent.

**Open decisions.** Whether it is a separate codemod or a setting of `general-params`. Whether brash removes an import
it orphans.

### docstring-types

**Motivation.** A Google docstring that writes `name (str): ...` beside an annotated parameter repeats the annotation,
and the two drift apart. Projects divide cleanly: textual, litestar and pydantic type 0.2% to 2% of entries, while rich
types 95%, nox 80% and trio 71% on purpose.

**Rewrite.** `name (str): The name.` becomes `name: The name.` where the parenthesised type matches the parameter's
annotation exactly.

**Leaves alone.** A type that differs from the annotation in any way, an unannotated parameter, and class docstrings.

**Evidence.**

- 661 lines in 78 files. Every output parses, nothing but docstrings differs, and a second run changes nothing.
- The three type checkers give identical diagnostics before and after.
- 32 of 49 sampled rewrites were right, 17 debatable, none wrong. All 16 from the three projects that hold the
  convention were right.
- In those three projects it gives 51 sites in 1,665 files.

**Limitations.**

- A docstring is a run-time value. A click help text, a schema built from docstring types and a strict Sphinx build
  each broke in a second module in constructed cases. None was found in the corpus.
- The exact-match rule leaves a docstring half typed where some entries differ from their annotations. Converting only
  whole docstrings fixes that and lowers the count.
- pydoclint's default demands the opposite convention, so a project cannot run both.
- It needs a Google docstring parser, which brash does not have.

**Size.** About 300 lines with the parser.

**Open decisions.** Whether brash may edit `__doc__` at all; see the docstring family under Untested, which would share
the parser.

## Shelved

Twelve ideas were tested or ruled out by a test and are not worth building as they stand. Each entry records why, so
the same ground is not covered twice. The "reopen if" lines are suggestions drawn from the evidence, not tested claims.

### sorted-sets

**Motivation.** A set has no order, so its display could always be written sorted, as ruff's RUF022 does for `__all__`.

**Evidence.** 419 unsorted displays in 238 files. Of 64 sampled, 26 were plainly right and 12 destroyed an order that
carried meaning, such as grouping by topic. No unsorted display held a duplicate, and ruff's B033 already handles
duplicates.

**Why shelved.** The written order is often deliberate, and no syntax separates the two cases. Iteration order also
changes when `PYTHONHASHSEED` is pinned. Confidence 0.85.

**Reopen if** a decidable signal for "this order is incidental" is found.

### single-with

**Motivation.** Nested `with` statements can be one statement with several items. ruff's SIM117 reports it.

**Evidence.** The rewrite is sound: 0 wrong of 50 sampled. But ruff's own fix already does 81% of sites at line length
120 and 40% at 88, leaving 90 pairs in 42 files. A trailing `# type: ignore` on the inner header moves after formatting.

**Why shelved.** ruff has an open issue (#23040) to lift the guard that stops its fix. Confidence 0.7.

**Reopen if** ruff closes that issue without lifting the guard.

### self-returns

**Motivation.** A method that returns `self` should be annotated `-> Self` so subclasses keep their type through a
chain.

**Evidence.** 198 sites in 107 files. 8 were wrong in their own project, including 3 new mypy errors in jinja2, because
mypy retypes `self` once the return is `Self`. Restricted to classes with no base it is safe but falls to 84 sites in 41
files, for about 480 lines.

**Why shelved.** A return type is visible to subclasses in other modules, and the safe form is rare for its cost.
Confidence 0.7.

**Reopen if** the base-less form can be written in far fewer lines.

### frozen-constants

**Motivation.** AGENTS.md says a module constant should not be a mutable collection: a list should be a tuple and a set
a frozenset.

**Evidence.** The provable form rewrites 9 sites in 7 of 7,436 files. The list-to-tuple half draws type-checker breaks,
and 47% of public set constants are named by another file.

**Why shelved.** A constant's type is visible to every module that imports it. Confidence 0.78.

**Reopen if** it is wanted as brash's own project codemod, where every reader is in sight.

### raise-from

**Motivation.** ruff's B904 reports a `raise` inside an `except` with no `from`, and offers no fix.

**Evidence.** All 59 sites were read: 29 right, 3 wrong, 27 debatable. Where maintainers wrote the clause by hand in a
named handler, they chose `from None` in 84 of 491 cases. `__cause__` is observable by `contextlib` and by tests.

**Why shelved.** Choosing between `from e` and `from None` is a decision about what the user should see. Confidence
0.86.

**Reopen if** never. This is the README's "a person should decide each time".

### newspaper-order and method-order

**Motivation.** AGENTS.md puts each private helper below the first function that calls it. Few projects hold this: 43%
of corpus helpers already sit below a caller. That alone would make it an opt-in codemod, not a shelved one.

**First round.** As first specified it broke the import of `pygments.lexers.configs`, where a helper is used at import
time. The form that survived moves a helper only below an undecorated top-level caller, with nothing but defs, classes
and literal assignments in between. That gives 345 sites in 178 files and is about 420 lines. Of the 20 sampled sites
that pass the safety rules, 9 were not plainly right. 49 of the 178 changed files end in mixed order, a moved helper
beside ones that must stay.

**Second round.** Three families of variants were measured: where a moved helper lands, which helpers move, and which
settings a project could turn. They were judged on the four corpus projects that hold the convention, by the share of
helpers already below a caller: brash and tox (100%), pip-tools (80%) and attrs (71%). No other project is above 56%.
The test lifts one helper to just above its first caller and asks whether the rule puts it back exactly where its
authors had it. The best rule was then attacked.

| Rule                                    | brash, of 45 | tox, of 201 | pip-tools, of 28 | attrs, of 5 |
| --------------------------------------- | ------------ | ----------- | ---------------- | ----------- |
| The first round's rule                  | 10           | 74          | 10               | 2           |
| With the sibling join                   | 15           | 128         | 11               | 3           |
| And quiet classes                       | 15           | 136         | 11               | 3           |
| And `safe-decorators`, the candidate    | 17           | 147         | 10               | 3           |

- **The sibling join is the gain.** Where the first caller already has helpers below it, the moved helper joins them
  in the order the caller first uses them. Where it has none, the helper lands directly below the caller, as before.
- **Quiet classes.** A class counts as a caller when making it provably runs none of its methods: no base, keyword or
  decorator, and a body of docstrings, literal assignments and plain methods.
- **One setting earned its place.** `safe-decorators` lists decorators the project vouches do not call what they
  decorate, so a def under them counts as a caller. tox would set `pytest.*` and brash `click.*`. It is an assertion,
  and a wrong entry cannot be detected.
- **Settings measured and dropped.** Landing below the public names suits brash by two helpers (19 against 17) and
  costs tox 21 (126 against 147). Moving only single-caller helpers costs tox 41 (147 to 106), because tox stands
  shared helpers below the first caller. Keeping a run of adjacent helpers together cuts the repair of a fully drifted
  brash from 36 of 45 helpers to 9, since one helper that cannot move freezes its run. A minimum distance, a
  whole-module switch, a tests switch and vouched base classes each moved three helpers or fewer.
- **The ceiling is the authors.** With every safety rule off, the best placement rule still restores only 26 of 45
  in brash. Sibling order in brash is not call order in `general_params`, `type_aliases` and `config`, and pip-tools
  orders breadth-first. No rule read from the module reproduces a layout its authors did not follow.
- **A helper drifted to the top of the module mostly stays there.** The candidate restores 2 of 45 in brash and 85 of
  201 in tox, because a `re.compile` or `frozenset` constant stands between and cannot be crossed safely.
- **The first round's safety rules had four holes.** A lambda in a default that is called at once, a helper named in a
  string annotation that a decorator reads, an attribute lookup on the module object, and a string equal to the
  helper's name. A wider fuzz found 98 run-time differences in 3,217 modules under the old rules, and none in 6,511
  under the candidate. Three risks have no decidable exclusion: line numbers read back, another module reading the
  helper mid-import, and a computed name.
- **On code as written** the candidate moves nothing in brash or tox, 4 helpers in pip-tools and 1 in attrs, all of
  which do stand above their callers. On the corpus it moves 386 helpers in 203 files and leaves 45 of them in mixed
  order. A second run changes nothing, also after ruff. It is about 950 lines.
- **Sample.** Of 44 graded moves, 28 were right, 11 debatable and 5 worse. In projects that do not hold the convention
  it was 13, 6 and 5 of 24. Nine of the 11 not right there are a shared helper wedged below the first of many callers,
  which is tox's own style, so no rule excludes it without losing tox. Of 14 single-caller moves, 12 were right and
  none worse.
- **A check that moves nothing sees the drift.** Reporting a helper that stands above every caller catches 276 of 278
  simulated drifts and reports nothing on brash or tox as written. brash cannot fail a check without a diff.

**Why shelved.** A drifted helper in brash comes back exactly 17 times in 45. It is put where the authors did not have
it 11 times, and left where it drifted 17 times, while `brash --check` passes. That is wrong at some sites in a project
that wants the convention, with no rule to tell which. tox reaches 73%. `method-order`, the same rule inside a class,
was not run on its own. Confidence 0.72.

**Open decisions.**

- Whether the bar is the authors' exact layout, or any layout with the helper below a caller. On the second reading
  the candidate is buildable as an opt-in: after one helper drifts it leaves 28 of 45 below a caller in brash and 170
  of 201 in tox.
- Whether brash should report without rewriting. It is the only form that catches nearly all drift, and it changes
  `brash.command.Command` and the command's output.
- Whether one codemod may have settings. `[tool.brash.settings.<name>]` was prototyped and no valid configuration
  changed meaning, but it is new surface for one unprovable setting.
- Whether AGENTS.md should say what order sibling helpers stand in. brash's own files disagree with any single rule.

**Reopen if** either of the first two decisions goes its way.

### typed-fixtures

**Motivation.** A test parameter that names a fixture has a known type, and ruff's ANN001 reports it unannotated.

**Evidence.** 295 sites in 56 test files. Copying a same-module fixture's return annotation drew new type errors at 23
of 150 sites, because fixture annotations nobody had used are often untrue. A table of 13 built-in pytest fixtures is
accurate: it matches 4,049 of 4,111 hand annotations and gives 142 sites in 45 files for about 330 lines.

**Why shelved.** The half that reads only the module is unsound. The half that works is another package's contract kept
inside brash, which the README assigns to a project's own codemods. It also leaves 88% of ANN001 reports in partly
annotated tests. Confidence 0.72.

**Reopen if** brash decides tables of third-party types are in scope. The pytest table would then be a sound start.

### type-params

**Motivation.** Python 3.12 writes type parameters in the signature (`def first[T](xs: list[T]) -> T`) where older code
declares a `TypeVar`.

**Evidence.** 341 sites in 109 files. As specified it wrote a real type error in cattrs, on `AnyStr`, and moved a pragma
in pytest. Whether a Protocol's variance survives is undecidable, and checkers disagree. Narrowed it is sound at 263
sites in 91 files, but leaves at least 70 of 123 converted `TypeVar` statements behind unread. It fires zero times on
Home Assistant's 10,935 converted files.

**Why shelved.** It is a one-off migration, and ruff tracks the remaining cases in its issue #15642. Confidence 0.8.

**Reopen if** never as a standing codemod. It could be a one-time script.

### object-params

**Motivation.** ruff's ANN401 reports a parameter typed `Any`. Where the function only tests, compares or prints it,
`object` says the same and is checked.

**Evidence.** 98 parameters in 63 files as specified; 78 right, 16 debatable, 4 wrong. basedpyright strict reports an
unknown-typed argument passed to an `object` parameter and stays silent for `Any`, which drew 13 new errors at callers
in fastapi, litestar, werkzeug and pytest. `functools.singledispatch` reads the annotation at run time, so the rewrite
changed which function was called. With every decidable exclusion it is 66 sites in 41 files and still draws 6 caller
errors.

**Why shelved.** Unlike widening a collection, moving a parameter off `Any` is visible to callers, and nothing in the
module predicts it. It clears 1.3% of ANN401 reports. Confidence 0.85.

**Reopen if** pyright stops exempting `Any` parameters from that check.

### dunder-signatures

**Motivation.** The data model fixes some signatures: `__exit__` takes three known types, `__hash__` returns `int`,
`__post_init__` returns `None`.

**Evidence.** 59 sites in 25 files; 11 right, 9 wrong, 39 debatable. The 9 wrong ones draw new mypy errors: 4 `# type:
ignore` comments made unused in werkzeug, and 5 errors inside bodies mypy starts checking once the def has its first
annotation. Held to code that is already annotated it is right 9 times of 9, in 7,436 files. `pyrefly infer` writes the
same return at 56 of the 59.

**Why shelved.** Typed code already has these annotations (262 of 272), and untyped tests do not want one lone
annotation. Confidence 0.86.

**Reopen if** brash gains a way to run on new code only, or a corpus of half-typed applications shows the annotated form
firing often.

### doc-comments: `#:` above `self.x` in `__init__`

**Motivation.** brash writes `#:` above an annotated `self.x: T = ...` by hand in 5 of 5 cases, and `doc-comments` does
not.

**Evidence.** 159 blocks in 73 files. Of 45 sampled, 23 say what the attribute is, 14 are a group's label or a why-note
such as `# Timeouts`, and 8 are debatable. A narrowing leaves 101 blocks at about 64% right. Related shapes are too
rare: TypedDict and Protocol members give 22 comments in the whole corpus.

**Why shelved.** Half the comments above an instance attribute are not descriptions of it, a worse rate than the codemod
accepts for constants.

**Reopen if** a decidable rule separates a label from a description.

## Untested

Twenty-four ideas have a written spec and no evidence. Expect few to survive: of the eighteen tested, fifteen did not.
The index gives each one's rewrite and the strongest objection raised when it was proposed.

### The docstring family

`section-order`, `returns-none`, `args-order` and `section-names` all need a Google docstring parser, which brash does
not have. They were measured for rate only, on one shared prototype parser, alongside `docstring-types`.

- Only 6 of the 30 projects write Google docstrings in volume: textual, litestar, rich, pydantic, trio and nox.
- Together the five ideas change 179 of 7,423 parsed files, and 168 of those are in those six projects.
- None fires on brash's own 17 files.
- They do fire on the two projects that lint docstrings with ruff's D rules and the google convention: litestar and
  pydantic.

If brash ever takes on a docstring parser, it should be one shared module with separate codemods, since projects would
need to switch them off one by one. `section-order` has the best claim to go first: it is the only one a ruff rule
reports (D420, a preview rule with no fix), and it moves text without removing any.

**Open decision.** May brash edit `__doc__` at all? A docstring is a run-time value that help text, schemas and
documentation builds read.

### Lower-tier ideas

The other twenty were ranked lowest at ideation and have not been prototyped. Many were ranked low as "taste" or
"contested", which is an argument about defaults: `strenum-values`, `match-chains`, `param-ids`, `patch-blocks`,
`positive-conditions`, `named-expressions` and `attribute-docstrings` could each be an opt-in codemod if the rewrite
proves sound. Three notes for whoever picks one up:

- `todo-colons` was called the safest and smallest of all the ideas: it respells a comment tag, and ruff's TD004 and
  TD007 report it with no fix.
- `mock-namespace` and `lazy-logging` are named in the README as examples of a project's own codemod. With opt-in
  codemods they could ship in brash instead; that is the maintainers' call.
- `concrete-returns`, `never-returns`, `keyword-flags` and `final-classes` each change something another module can see.
  That is the trait that sank `self-returns` and `object-params`.

The index is the whole record of these twenty: their fuller specs were not kept.

## Rejected without testing

These classes of idea fail the bar by their nature. They are listed so that a new proposal can be checked against them
first.

| Class | Examples | Why |
| --- | --- | --- |
| ruff already fixes it | `None` last in a union (RUF036), TYPE\_CHECKING imports (TC001-003), PEP 695 at module level (UP040, UP046, UP047), `contextlib.suppress` (SIM105), else-after-return (RET505-508), PERF401, most pytest shapes | Bar 6. Checked against ruff 0.17.6, which has 977 rules: 250 always fix, 232 sometimes, 495 never |
| Readers are in another module | Frozen dataclass field `list[T]` to `tuple[T, ...]`; `frozen=True`, `slots=True`, `kw_only=True`; boolean traps on public functions; `@staticmethod` for no-self-use; `Final` or `ClassVar` on class attributes | Every constructor call, caller and subclass is out of sight |
| It would write prose or invent a name | Missing Args, Returns or Raises entries; magic values to constants; renames; a TODO's author; skip reasons; `namedtuple` to `NamedTuple` | Bar 7 |
| Removing text that may be right | Stale docstring sections and entries | 36 of 41 stale Args entries sat beside a renamed parameter, where the code may be what is wrong |
| Annotation inference | Return types, parameter types from defaults, `__eq__(self, other: object)` | ruff's ANN fixes and `pyrefly infer` already do it with real inference; a guess can break a caller |
| Needs a tool's output or a value's type | A code for a bare `# type: ignore`; `setdefault` and `defaultdict` idioms; `if` chain to dict lookup; `isinstance` chains to `match` | Bar 2 |
| A person should decide | Bare `except:`; imports moved to the top; `autospec=True`; `tz=` on datetimes; `subprocess.run(check=)`; `pytest.approx` | Each changes behaviour |
| One-off migrations | Sphinx or NumPy docstrings to Google; type comments to annotations; `tmpdir` to `tmp_path`; unittest assertions to pytest | Bar 5 |
| Sorts where order is meaning | Dict keys, `Literal` members, union members, enum members | `get_args` and iteration observe the order |
| `@override` from a table of stdlib bases | `ast.NodeVisitor.visit_*` | Knowledge of other modules, with no end to the table |
| Dict constants | `Final[Mapping[K, V]]`, `MappingProxyType({...})` | Needs K and V inferred; the proxy breaks `json.dumps`, `pickle` and `deepcopy` |
| Too rare | Needless `global` (44 hits in 2,787 files), `logger.exception` (0), useless try/except (3), merging identical handlers (3 in 886) | Not worth the cases |
| `monkeypatch` to `mock.patch` blocks | `monkeypatch.setattr`, `setenv`, `chdir` | The patch then ends with the test body, not at teardown; "never monkeypatch" is brash's house rule, not a general one |

### Extension leads measured and dropped

The scout that found the two extensions above also measured these and dropped them.

| Codemod | Lead | Result |
| --- | --- | --- |
| `general-params` | Methods of a class with a base | 381 parameters, 99 would widen; pinned by two cases, and an overrider elsewhere is what sank `self-returns` |
| `general-params` | A parameter compared with `==` | Sole blocker for 114 parameters, mostly test expectations; pinned by "Compared" |
| `general-params` | Passed only to a same-module function with an abstract parameter | At most 57 sites; needs a fixed point across functions |
| `general-params` | Decorated functions | 189 parameters, 160 under `click.option`; right as it is |
| `general-params` | Bare `list` or `dict`, quoted annotations, `@final` classes | At most 22, 4 and 8 sites |
| `type-aliases` | A generic alias over a module `TypeVar` | 22 sites, and it leaves the `TypeVar` behind |
| `type-aliases` | Other subscripts read only in annotations | 48 sites; pinned by "Another subscript" |
| `final-constants` | Names under `if`, `try` or `TYPE_CHECKING` | 139 names, 9 eligible; the rest are bound in two arms |
| `final-constants` | Class-level constants | 110 in plain classes, but `Final` forbids an override in another module; 2 sites in `@final` classes |
| `doc-comments` | A trailing comment moved above as `#:` | 94 sites, but the README makes that the place for a why-note |
| `doc-comments` | Unannotated `self.x`, TypedDict and Protocol members, plain-class attributes | Nothing marks them as declarations, or too rare |

## Defects found in the existing codemods

Three defects in codemods brash already ships turned up during testing. All three were reproduced against the current
code. The first two are fixed; the third is not, nor filed.

- [x] **`type-aliases` and ruff together write an alias that raises.** `HighlighterType = Callable[[Union[str, "Text"]],
  "Text"]` becomes a `type` statement, and ruff's safe UP007 fix then writes `Callable[[str | "Text"], "Text"]`. Reading
  `__value__` raises `TypeError`. Two corpus aliases hit it: `rich/console.py:68` and `aiohttp/web_urldispatcher.py:86`.
  Fixed by leaving alone an alias with a quoted name directly inside a `Union` or `Optional`, at any depth.
- [x] **`general-params` misses a shadowed builtin around a slice.** With `from mylib import sorted`, it correctly
  leaves `len(sorted(items))` alone but widens `items: list[str]` to `Sequence[str]` in `len(sorted(items[1:]))`.
  `_shadowed` checked the parameter's own parent, not the slice's; it now follows a slice to the call around it.
- [ ] **`general-params` widens a function the module hands to a framework.** `def main(files: list[str])` passed to
  `typer.run(main)` becomes `Iterable[str]`, and typer reads the annotation at run time. The rewrite was confirmed;
  typer itself was not run. 49 of the codemod's 417 corpus sites are in functions the module names as a value. The
  named-as-a-value rule from the star-unpacking extension would close this.

One more finding is about brash's own code, not a codemod. Two parameters in `src/brash/general_params.py` take more
than they read, by the AGENTS.md rule. Both are widened now:

- [x] `_choose(head, reads: Sequence[_Read])` needs only `Collection`.
- [x] `_with_imports(block, names: Sequence[str])` needs only `Iterable`.

For scale, the existing codemods fire on the corpus as follows: `final-constants` 2,260 sites in 836 files,
`doc-comments` 898 comment lines in 290, `general-params` 417 in 220, `type-aliases` 189 in 116.

## Method and evidence

The ideas came from three rounds of work on 2026-11-24, and the numbers are only as good as the method below.

**Ideation.** Eight lenses each proposed ideas: brash's house conventions, typing, ruff rules with no fix, prior art in
other tools, data modelling, docs and comments, structure and flow, and tests. Their 59 ideas merged into 37 candidates,
each checked against ruff 0.17.6.

**Corpus.** Source and tests of 30 projects from their published sdists: 7,436 Python files, 2,487 of them tests. The
projects are httpx, starlette, fastapi, attrs, structlog, trio, anyio, typer, rich, textual, pytest, hatch, poetry,
black, urllib3, werkzeug, flask, jinja2, click, pydantic, litestar, cattrs, aiohttp, nox, tox, pip-tools, polyfactory,
sqlmodel, uvicorn and httpcore. The code was parsed only, never imported or run. 13 files do not parse and were skipped.

**Testing.** Each tested idea was prototyped as a `brash.command.Command` and run over the whole corpus. Each was then
checked five ways:

1. Every output parses, and a second run changes nothing, also after ruff's import fix and format at 88 and 120 columns.
2. pyrefly 1.5.0 strict, mypy 2.4.1 `--strict` and basedpyright ran on whole projects before and after, and the
   diagnostics were compared.
3. A sample of rewrites was read and graded right, debatable or wrong.
4. Adversarial modules were written to break the spec.
5. The codemod was run on brash's own code.

**Who tested what.** Twelve candidates were tested by a skeptic independent of whoever proposed them.
`empty-collections` and the four extensions were proposed and tested by the same agent, with no independent skeptic.
Only the two marked Build were then spot-checked separately, each on one adversarial module, and both held.

**Limits.**

- The corpus is 30 libraries, most of them strictly typed. Application code may behave differently, and half-typed code
  more so.
- The projects' third-party dependencies were not installed for type checking, so unknown-type counts are inflated and a
  few reported differences are artefacts of that.
- Corpus test suites were never run. Run-time safety rests on reading, small executed cases, and three checkers
  agreeing.
- "Right" and "debatable" are one reader's judgement per sample. Site counts and checker diagnostics are measured.
- Everything is pinned to ruff 0.17.6. A fix ruff declines today is a moving target: ruff may add it in any release.

**Where the evidence is.** The prototypes, the corpus and the full per-idea verdicts were scratch files of the working
session and are not in the repository. This document is the record: a prototype named here has to be written again from
its entry.

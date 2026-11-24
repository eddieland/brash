"""brash: codemods that hold a Python codebase to its conventions, applied to files or checked against them.

`brash PATHS` rewrites the Python under the paths with every codemod there is, brash's own in `registry.CODEMODS` and
those the project registers in its `pyproject.toml` or `brash.toml`, but for any it turns off there, for every file or
in its `per-file-ignores` for some, leaving alone the files its `exclude` there names, and `--check` changes nothing:
it prints the diff each would make and fails when there is one, which is how a lint holds a repository to them. A
codemod is a `libcst.codemod` command, so it keeps every comment and blank line it does not touch. A project that
runs on a Python older than a codemod's output needs says so with `target-version` there, or `--target-version` here,
and that codemod does not run. The README says how to add one.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from brash import config, registry, run

if TYPE_CHECKING:
    from collections.abc import Collection

    from brash.command import Command
    from brash.config import Project


def _target(_context: click.Context, _parameter: click.Parameter, target: str | None) -> str | None:
    """Check what `--target-version` was given.

    Returns:
        The target as it was given, or None when it was not.

    Raises:
        click.BadParameter: When it names no Python version.
    """
    if target is not None:
        try:
            config.python(target)
        except ValueError as e:
            raise click.BadParameter(f"{e}.") from e
    return target


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--check", is_flag=True, help="Change nothing: print the diff, and fail when there is one.")
@click.option(
    "--only",
    "names",
    multiple=True,
    metavar="NAME",
    help="Run this codemod alone; give it again for each. By default, all the project has not turned off.",
)
@click.option(
    "--target-version",
    "target",
    metavar="PY",
    callback=_target,
    help="The oldest Python the code runs on, as py310: a codemod whose output needs a later one does not run. "
    "By default, the project's `target-version`.",
)
@click.option("--list", "listing", is_flag=True, help="List the codemods and exit.")
def main(
    *,
    paths: tuple[Path, ...],
    check: bool,
    names: tuple[str, ...],
    target: str | None,
    listing: bool,
) -> None:
    """Rewrite the Python under PATHS, files or directories, with every codemod."""
    project, codemods, chosen = _registered(names, target)
    if listing:
        for name, codemod in codemods.items():
            click.echo(f"{name}  {codemod.DESCRIPTION}")
        return
    if not paths:
        raise click.UsageError("Give the files or directories to rewrite.")
    found = [path for path in run.files(paths) if not project.excludes(path)]
    ignored = {path: names for path in found if (names := project.ignored(path))}
    rewrites = run.rewrite_all(found, chosen, codemods, ignored)
    failed = [rewrite for rewrite in rewrites if rewrite.error is not None]
    changed = [rewrite for rewrite in rewrites if rewrite.changed]
    for rewrite in failed:
        click.echo(f"{rewrite.path}: {rewrite.error}", err=True)
    for rewrite in changed:
        if check:
            click.echo(rewrite.diff(), nl=False)
        else:
            rewrite.path.write_text(rewrite.after, encoding="utf-8")
            click.echo(f"Rewrote {rewrite.path}")
    if failed:
        raise click.ClickException(f"{_files(len(failed))} could not be rewritten")
    if check and changed:
        raise click.ClickException(f"{_files(len(changed))} would be rewritten; run `brash` without `--check`")


def _registered(names: Collection[str], target: str | None) -> tuple[Project, dict[str, type[Command]], list[str]]:
    """The project this run is in, every codemod it has, and those it runs: `--only`'s, or the project's choice.

    Either way, a codemod whose output needs a later Python than the target does not run: `--target-version`'s, or
    the project's `target-version`.

    Returns:
        The project; each codemod by name, brash's own and then the project's, in the order they run on a file; and
        the names of those to run, in that order.

    Raises:
        click.ClickException: When the project's configuration is not one brash takes, registers a codemod that
            cannot be loaded, or selects or ignores one there is not, for every file or for some.
        click.BadParameter: When `--only` names no codemod.
    """
    try:
        project = config.load(Path.cwd())
        codemods = registry.registered(project)
        chosen = registry.selected(project, codemods)
    except (config.ConfigError, registry.RegistryError) as e:
        raise click.ClickException(str(e)) from e
    for name in names:
        if name not in codemods:
            raise click.BadParameter(f"{name!r} is not one of {', '.join(map(repr, codemods))}.", param_hint="'--only'")
    if names:
        chosen = [name for name in codemods if name in names]
    target = target or project.config.target_version
    if target is not None:
        oldest = config.python(target)
        chosen = [name for name in chosen if oldest >= codemods[name].MINIMUM_PYTHON]
    return project, codemods, chosen


def _files(count: int) -> str:
    return "1 file" if count == 1 else f"{count} files"

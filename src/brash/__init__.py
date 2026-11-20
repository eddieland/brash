"""brash: codemods that hold a Python codebase to its conventions, applied to files or checked against them.

`brash PATHS` rewrites the Python under the paths with every codemod there is, brash's own in `registry.CODEMODS`
and those the project registers in its `pyproject.toml`, leaving alone the files its `exclude` there names, and
`--check` changes nothing: it prints the diff each would make and fails when there is one, which is how a lint holds
a repository to them. A codemod is a `libcst.codemod` command, so it keeps every comment and blank line it does not
touch. The README says how to add one.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from brash import config, registry, run

if TYPE_CHECKING:
    from collections.abc import Iterable

    from brash.command import Command
    from brash.config import Project


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--check", is_flag=True, help="Change nothing: print the diff, and fail when there is one.")
@click.option(
    "--only",
    "names",
    multiple=True,
    metavar="NAME",
    help="Run this codemod alone; give it again for each. By default, all of them.",
)
@click.option("--list", "listing", is_flag=True, help="List the codemods and exit.")
def main(*, paths: tuple[Path, ...], check: bool, names: tuple[str, ...], listing: bool) -> None:
    """Rewrite the Python under PATHS, files or directories, with every codemod."""
    project, codemods = _registered(names)
    if listing:
        for name, codemod in codemods.items():
            click.echo(f"{name}  {codemod.DESCRIPTION}")
        return
    if not paths:
        raise click.UsageError("Give the files or directories to rewrite.")
    found = [path for path in run.files(paths) if not project.excludes(path)]
    rewrites = run.rewrite_all(found, [name for name in codemods if not names or name in names], codemods)
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


def _registered(names: Iterable[str]) -> tuple[Project, dict[str, type[Command]]]:
    """The project this run is in and every codemod it has, once `--only` is known to name some of them.

    Returns:
        The project, and each codemod by name, brash's own and then the project's, in the order they run on a file.

    Raises:
        click.ClickException: When the project's `[tool.brash]` is not one brash takes, or registers a codemod that
            cannot be loaded.
        click.BadParameter: When `--only` names no codemod.
    """
    try:
        project = config.load(Path.cwd())
        codemods = registry.registered(project)
    except (config.ConfigError, registry.RegistryError) as e:
        raise click.ClickException(str(e)) from e
    for name in names:
        if name not in codemods:
            raise click.BadParameter(f"{name!r} is not one of {', '.join(map(repr, codemods))}.", param_hint="'--only'")
    return project, codemods


def _files(count: int) -> str:
    return "1 file" if count == 1 else f"{count} files"

"""What every codemod is: a `libcst.codemod` command that can say cheaply when a file is not its concern."""

from __future__ import annotations

from typing import ClassVar

from libcst.codemod import VisitorBasedCodemodCommand


class Command(VisitorBasedCodemodCommand):
    """A codemod: its `visit_` and `leave_` methods rewrite a module, or `transform_module_impl` does it whole.

    Parsing a module with libcst and visiting it takes a few hundred times as long as reading it, and the lint runs
    every codemod over every file. So a codemod that can tell from a module's text that it has nothing to do there
    says so in `wants`, and the file is never parsed.
    """

    #: The oldest Python that runs what the codemod writes, as its major and minor version. A project whose
    #: `target-version` is older does not run the codemod.
    MINIMUM_PYTHON: ClassVar[tuple[int, int]] = (3, 0)

    @classmethod
    def covers(cls, filename: str | None) -> bool:  # noqa: ARG003
        """Whether the codemod holds a file at this path to it at all, before its text is read for `wants`.

        Args:
            filename: The file's path, or None for text with no file, which every codemod covers.

        Returns:
            True unless the file is outside what the codemod is for. Always True here.
        """
        return True

    @classmethod
    def wants(cls, source: str) -> bool:  # noqa: ARG003
        """Whether the codemod might change a module with this text.

        Returns:
            True unless it is sure to leave the module as it is. Always True here.
        """
        return True

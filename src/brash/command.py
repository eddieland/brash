"""What every codemod is: a `libcst.codemod` command that can say cheaply when a file is not its concern."""

from __future__ import annotations

from typing import ClassVar, Final

from libcst.codemod import VisitorBasedCodemodCommand

from brash.config import Config

#: The key a run keeps the project's settings under in a codemod's `context.scratch`.
SETTINGS: Final = "brash.config"


class Command(VisitorBasedCodemodCommand):
    """A codemod: its `visit_` and `leave_` methods rewrite a module, or `transform_module_impl` does it whole.

    Parsing a module with libcst and visiting it takes a few hundred times as long as reading it, and the lint runs
    every codemod over every file. So a codemod that can tell from a module's text that it has nothing to do there
    says so in `wants`, and the file is never parsed.
    """

    #: The oldest Python that runs what the codemod writes, as its major and minor version. A project whose
    #: `target-version` is older does not run the codemod.
    MINIMUM_PYTHON: ClassVar[tuple[int, int]] = (3, 0)
    #: Whether the codemod is off by default: it runs only where a project's `select` or `extend-select` names it, or
    #: `--only` does. For a convention a project chooses to hold, which most do not.
    OPT_IN: ClassVar[bool] = False

    @property
    def config(self) -> Config:
        """The settings of the project the codemod runs in: every one at its default where the run gave none."""
        found: object = self.context.scratch.get(SETTINGS)
        return found if isinstance(found, Config) else Config()

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

    @classmethod
    def wants_in(cls, source: str, config: Config) -> bool:  # noqa: ARG003
        """Whether the codemod might change a module with this text, in a project with these settings.

        It is what a run asks. A codemod that reads no setting leaves it as it is, and answers in `wants`.

        Args:
            source: The module's text.
            config: The project's settings, which the codemod has as `self.config` when it rewrites.

        Returns:
            What `wants` says of the text.
        """
        return cls.wants(source)

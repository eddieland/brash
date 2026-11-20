"""Sphinx configuration for the documentation Read the Docs builds: the README, and the API a project's codemod uses."""

project = "brash"
author = "eddieland"
project_copyright = "%Y, eddieland"

extensions = [
    # The first page is the README itself, which is Markdown.
    "myst_parser",
    "sphinx.ext.autodoc",
    # Google docstrings.
    "sphinx.ext.napoleon",
]

html_theme = "furo"
html_title = "brash"

# The docstrings are written for a reader of the source, where `name` is code.
default_role = "code"
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# An anchor for each README heading, so a link to a section of it resolves.
myst_heading_anchors = 3
# A `:::` directive, which rumdl leaves as it is where it would give a bare code fence a language.
myst_enable_extensions = ["colon_fence"]

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import re

sys.path.insert(0, os.path.abspath(".."))

# -- Version setup -----------------------------------------------------------

_changelog_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "CHANGELOG.md")
)
with open(_changelog_path, "r") as changelog:
    try:
        _version_info = re.match(
            r"# v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)", changelog.readline(),
        ).groupdict()
    except (OSError, IndexError):
        raise RuntimeError("Unable to determine version.")


# -- Project information -----------------------------------------------------

project = "aiocouch"
copyright = "2020, ZIH, Technische Universität Dresden"
author = "Mario Bielert"

# The short X.Y version
version = "{major}.{minor}".format(**_version_info)
# The full version
release = "{major}.{minor}.{patch}".format(**_version_info)

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "couchdb": ("https://docs.couchdb.org/en/stable/", None),
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_theme_options = {
    "description": "An asynchronous CouchDB client library for asyncio and Python.",
    "canonical_url": "TODO",
    "github_user": "metricq",
    "github_repo": "aiocouch",
    "github_button": True,
    "github_type": "star",
    "github_banner": True,
    "fixed_sidebar": True,
}

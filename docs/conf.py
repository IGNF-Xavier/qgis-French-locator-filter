#!python3

"""
    Configuration for project documentation using Sphinx.
"""

# standard
import sys
from datetime import datetime
from os import environ, path

sys.path.insert(0, path.abspath(".."))  # move into project package

# Package
from french_locator_filter import __about__

# -- Build environment -----------------------------------------------------
on_rtd = environ.get("READTHEDOCS", None) == "True"

# -- Project information -----------------------------------------------------
author = __about__.__author__
copyright = __about__.__copyright__
description = (
    "Ajoute un filtre de géocodage basé sur l'API de la BAN dans le  "
    "Localisateur (barre de recherche universelle) de QGIS."
)
project = __about__.__title__
version = release = __about__.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # Sphinx included
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.githubpages",
    "sphinx.ext.imgmath",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    # 3rd party
    "myst_parser",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]


# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
autosectionlabel_prefix_document = True
# The master toctree document.
master_doc = "index"


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = [
    "_build",
    ".venv",
    "Thumbs.db",
    ".DS_Store",
    "_output",
    "ext_libs",
    "tests",
    "demo",
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output -------------------------------------------------

# -- Theme

html_favicon = str(__about__.__icon_path__)
html_logo = str(__about__.__icon_path__)
# html_static_path = ["_static"]
html_theme = "furo"

# -- EXTENSIONS --------------------------------------------------------

# Configuration for intersphinx (refer to others docs).
intersphinx_mapping = {
    "PyQt5": ("https://www.riverbankcomputing.com/static/Docs/PyQt5", None),
    "python": ("https://docs.python.org/3/", None),
    "qgis": ("https://qgis.org/pyqgis/master/", None),
}

# MyST Parser
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
]

myst_substitutions = {
    "author": author,
    "date_update": datetime.now().strftime("%d %B %Y"),
    "description": __about__.__summary__,
    "qgis_version_max": __about__.__plugin_md__.get("general").get(
        "qgismaximumversion"
    ),
    "qgis_version_min": __about__.__plugin_md__.get("general").get(
        "qgisminimumversion"
    ),
    "repo_url": __about__.__uri__,
    "title": project,
    "version": version,
}

myst_url_schemes = ("http", "https", "mailto")

# OpenGraph
ogp_image = (
    f"{__about__.__uri_homepage__}_images/french_locator_sample_basque_qgis_details.png"
)
ogp_site_name = "French Locator Filter : géocodeur BAN pour QGIS"
ogp_site_url = __about__.__uri_homepage__
ogp_custom_meta_tags = [
    "<meta name='twitter:card' content='summary_large_image'>",
    f'<meta property="twitter:description" content="{description}" />',
    f'<meta property="twitter:image" content="{ogp_image}" />',
    '<meta property="twitter:site" content="@oslandia" />',
    f'<meta property="twitter:title" content="{project}" />',
]

# -- Options for Sphinx API doc ----------------------------------------------

autodoc_mock_imports = [
    "qgis.core",
    "qgis.gui",
    "qgis.PyQt",
    "qgis.PyQt.QtCore",
    "qgis.PyQt.QtGui",
    "qgis.PyQt.QtNetwork",
    "qgis.PyQt.QtWidgets",
    "qgis.utils",
    "qgis",
]

# run api doc
def run_apidoc(_):
    from sphinx.ext.apidoc import main

    cur_dir = path.normpath(path.dirname(__file__))
    output_path = path.join(cur_dir, "_apidoc")
    modules = path.normpath(path.join(cur_dir, "../french_locator_filter"))
    exclusions = ["../.venv", "../tests"]
    main(["-e", "-f", "-M", "-o", output_path, modules] + exclusions)


# launch setup
def setup(app):
    app.connect("builder-inited", run_apidoc)

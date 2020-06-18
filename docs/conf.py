import os
import sys

from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

sys.path.insert(0, os.path.abspath(".."))

# -- Project -------------------------------------------------------------------

project = "WTForms-SQLAlchemy"

# -- General -------------------------------------------------------------------

master_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "pallets_sphinx_themes",
    "sphinx_issues",
    "sphinxcontrib.log_cabinet",
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "WTForms": ("https://wtforms.readthedocs.io/en/stable/", None),
}
copyright = "2020, WTForms Team"
release, version = get_version("WTForms")
exclude_patterns = ["_build"]
pygments_style = "sphinx"

# -- HTML ----------------------------------------------------------------------

html_theme = "werkzeug"
html_context = {
    "project_links": [
        ProjectLink(
            "WTForms documentation", "https://wtforms.readthedocs.io/en/stable/"
        ),
        ProjectLink("PyPI Releases", "https://pypi.org/project/WTForms-SQLAlchemy/"),
        ProjectLink("Source Code", "https://github.com/wtforms/wtforms-sqlalchemy/"),
        ProjectLink("Discord Chat", "https://discord.gg/F65P7Z9",),
        ProjectLink(
            "Issue Tracker", "https://github.com/wtforms/wtforms-sqlalchemy/issues/"
        ),
    ]
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
html_title = f"WTForms SQLAlchemy Documentation ({version})"
html_show_sourcelink = False

# -- LATEX ---------------------------------------------------------------------

latex_documents = [
    (
        "index",
        "WTForms-SQLAlchemy.tex",
        "WTForms-SQLAlchemy Documentation",
        "WTForms Team",
        "manual",
    ),
]

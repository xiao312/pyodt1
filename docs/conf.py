from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

project = "pyodt1"
author = "xiao312"
copyright = "2026, xiao312"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]

autosummary_generate = True
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "furo"
html_title = "pyodt1"
html_static_path = []
html_theme_options = {
    "source_repository": "https://github.com/xiao312/pyodt1/",
    "source_branch": "main",
    "source_directory": "docs/",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "substitution",
]

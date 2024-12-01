# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath(".."))  # Add the parent directory
sys.path.insert(0, os.path.abspath("../shared"))  # Add the shared module directory

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ecommerce_platform_zebibsabbagh'
copyright = '2024, joudy sabbagh and zein zebib'
author = 'joudy sabbagh and zein zebib'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Automatically document modules, classes, functions, etc.
    'sphinx.ext.napoleon',     # Support for Google and NumPy-style docstrings
    'sphinx.ext.viewcode',     # Add links to source code
    'sphinx.ext.todo',         # Enable TODO notes in the documentation
    'sphinx.ext.coverage',     # Track documentation coverage
    'sphinx.ext.intersphinx',  # Link to external documentation 
]

napoleon_google_docstring = True
napoleon_numpy_docstring = True
todo_include_todos = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'  # Better theme for navigation
html_static_path = ['_static']

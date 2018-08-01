# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

from datetime import datetime

extensions = []
templates_path = ['/tmp/sphinx-template-dir', 'templates', '_templates', '.templates']
source_suffix = ['.rst']
master_doc = 'index'
project = u'Pip'
copyright = str(datetime.now().year)
version = '0.8.1'
release = '0.8.1'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
htmlhelp_basename = 'pip'
html_theme = 'docs-italia-theme'
file_insertion_enabled = False

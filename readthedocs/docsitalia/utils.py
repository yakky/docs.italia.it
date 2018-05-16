# -*- coding: utf-8 -*-
"""Utils for the docsitalia app."""

from __future__ import absolute_import
from __future__ import unicode_literals

import yaml

from readthedocs.restapi.client import api as apiv2


def load_yaml(txt):
    """Helper for yaml parsing"""
    try:
        return yaml.safe_load(txt)
    except yaml.YAMLError as exc:
        note = ''
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            note = ' (line %d, column %d)' % (mark.line + 1, mark.column + 1)
        raise ValueError(
            "The file could not be loaded, "
            "possibly due to a syntax error%s" % (
                note,))


def get_subprojects(project_pk):
    """
    Returns the list of subprojects from a project primary key by using the API

    This makes it suitable for using in signals and wherever you don't have access to the
    project context

    :param project_pk:
    :return:
    """
    return (
        apiv2.project(project_pk)
        .subprojects()
        .get()['subprojects']
    )

# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from django.test import TestCase
from elasticmock import FakeElasticsearch
from mock import patch

from readthedocs.projects.models import Project
from readthedocs.search.indexes import ProjectIndex
from readthedocs.rtd_tests.mocks.mock_indexes import MockIndex


class TestSearch(TestCase):
    """
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
    """

    def test_project_index(self):
        index = ProjectIndex(elasticsearch_class=FakeElasticsearch)
        self.assertTrue(index)

    @patch('readthedocs.search.indexes.ProjectIndex', new_callable=MockIndex)
    def test_search_project(self, mock_index):
        from readthedocs.search.lib import search_project
        foo = search_project({}, "ciao")
        self.assertTrue(foo)

# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from django.test import TestCase, RequestFactory
from mock import patch
from django.core.urlresolvers import reverse

from readthedocs.projects.models import Project
from readthedocs.search.indexes import ProjectIndex, PageIndex, SectionIndex
from readthedocs.rtd_tests.mocks.mock_indexes import MockIndex
from readthedocs.rtd_tests.mocks.test_search_mock_responses import (
    search_project_response, search_file_response
)

from urllib3._collections import HTTPHeaderDict


class TestSearch(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.factory = RequestFactory()

    def perform_request_mock(self, method, url, params=None, body=None, timeout=None, ignore=()):
        """
        Elastic Search Urllib3HttpConnection mock
        the response is taken by a real search on a db after loading
        the test fixtures (eric and test_data) for the project search
        and by a local custom project for file search
        """
        headers = HTTPHeaderDict(
            {
                'content-length': '893',
                'content-type': 'application/json; charset=UTF-8'
            }
        )
        if 'project.keyword' in params or '"project": "pip"' in params:
            raw_data = search_file_response
        else:
            raw_data = search_project_response
        return 200, headers, raw_data

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_mock
    )
    def test_search_project(self, perform_request_mock):
        """
        Tests the search view (by project) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            reverse('search'),
            {'q': 'pip', 'type': 'project', 'project': None}
        )
        self.assertEqual(r.status_code, 200)
        query_dict = perform_request_mock.call_args_list[0][0][3]
        self.assertTrue('"query": "pip"' in query_dict)
        main_hit = r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['fields']['name'], 'Pip')
        self.assertEqual(main_hit['fields']['slug'], 'pip')

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_mock
    )
    def test_search_file(self, perform_request_mock):
        """
        Tests the search view (by file) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            reverse('search'),
            {'q': 'capitolo', 'type': 'file'}
        )
        query_dict = perform_request_mock.call_args_list[0][0][3]
        self.assertTrue('"query": "capitolo"' in query_dict)
        self.assertTrue('"title": {"query"' in query_dict)
        self.assertTrue('"headers": {"query"' in query_dict)
        self.assertTrue('"content": {"query"' in query_dict)
        main_hit = r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'page')
        self.assertEqual(main_hit['fields']['project'], 'prova')
        self.assertEqual(main_hit['fields']['path'], '_docs/cap2')

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_mock
    )
    def test_search_in_project(self, perform_request_mock):
        """
        Tests the search view (by file) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            '/projects/pip/search/',
            {'q': 'capitolo'}
        )
        query_dict = perform_request_mock.call_args_list[0][0][3]
        self.assertTrue('"query": "capitolo"' in query_dict)
        self.assertTrue('"title": {"query"' in query_dict)
        self.assertTrue('"headers": {"query"' in query_dict)
        self.assertTrue('"content": {"query"' in query_dict)
        main_hit = r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'page')
        self.assertEqual(main_hit['fields']['project'], 'prova')
        self.assertEqual(main_hit['fields']['path'], '_docs/cap2')

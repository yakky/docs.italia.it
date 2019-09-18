# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from django.test import TestCase
from mock import patch
from urllib3._collections import HTTPHeaderDict

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.restapi.utils import index_search_request
from readthedocs.rtd_tests.mocks.search_mock_responses import (
    search_project_response
)
from readthedocs.search.indexes import PageIndex
from readthedocs.docsitalia.models import Publisher, PublisherProject


class TestSearch(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.version = Version.objects.create(
            project=self.pip, identifier='test_id', verbose_name='verbose name')

    def perform_request_project_mock(self, method, url, params=None, body=None, timeout=None, ignore=()):
        """
        Elastic Search Urllib3HttpConnection mock for project search
        """
        headers = HTTPHeaderDict({
            'content-length': '893',
            'content-type': 'application/json; charset=UTF-8'
        })
        raw_data = search_project_response
        return 200, headers, raw_data

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_project_mock
    )
    def test_index_search_request_indexes_the_project(self, perform_request_mock):
        page_list = []
        index_search_request(
            version=self.version, page_list=page_list, commit=None,
            project_scale=1, page_scale=None, section=False, delete=False)
        response = perform_request_mock.call_args_list[0][0][3]
        self.assertJSONEqual(response, {
            'slug': 'pip',
            'lang': 'en',
            'tags': None,
            'name': u'Pip',
            'id': 6,
            'weight': 1,
            'publisher': None,
            'url': u'/projects/pip/',
            'author': ['eric'],
            'progetto': None,
            'description': '',
            'private': False
        })

    @patch(
        'elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request',
        side_effect=perform_request_project_mock
    )
    def test_index_search_request_indexes_publisher_and_publisher_project(self, perform_request_mock):
        publisher = Publisher.objects.create(
            name='Test Org',
            slug='publisher',
            metadata={},
            projects_metadata={},
            active=True
        )
        pub_project = PublisherProject.objects.create(
            name='Test Project',
            slug='testproject',
            metadata={
                'documents': [
                    'https://github.com/testorg/myrepourl',
                    'https://github.com/testorg/anotherrepourl',
                ]
            },
            publisher=publisher,
            active=True
        )
        pub_project.projects.add(self.pip)

        page_list = [{'path': 'path', 'title': 'title', 'content': 'content', 'headers': 'headers'}]
        with patch.object(PageIndex, 'bulk_index') as bulk_mock:
            index_search_request(
                version=self.version, page_list=page_list, commit=None,
                project_scale=1, page_scale=1, section=False, delete=False)
        response = perform_request_mock.call_args_list[0][0][3]
        self.assertJSONEqual(response, {
            'slug': 'pip',
            'lang': 'en',
            'tags': None,
            'name': u'Pip',
            'id': 6,
            'weight': 1,
            'publisher': 'Test Org',
            'url': u'/projects/pip/',
            'author': ['eric'],
            'progetto': 'testproject',
            'description': '',
            'private': False
        })
        bulk_mock.assert_called_with(
            [{'publisher': 'Test Org', 'taxonomy': None, 'project': 'pip',
              'commit': None, 'progetto': 'testproject', 'path': 'path',
              'weight': 2, 'version': 'verbose-name', 'headers': 'headers',
              'id': 'b3129830187e487e332bb2eab1b7a9c3', 'title': 'title',
              'content': 'content', 'project_id': self.pip.pk, 'private': False}],
            routing='pip'
        )

# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from django.test import TestCase, RequestFactory
from elasticmock import FakeElasticsearch
from mock import patch
from django.core.urlresolvers import reverse

from readthedocs.projects.models import Project
from readthedocs.search.indexes import ProjectIndex, PageIndex, SectionIndex
from readthedocs.rtd_tests.mocks.mock_indexes import MockIndex

from urllib3._collections import HTTPHeaderDict


class TestSearch(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.factory = RequestFactory()

    def test_project_index(self):
        index = ProjectIndex(elasticsearch_class=FakeElasticsearch)
        self.assertTrue(index)

    def test_page_index(self):
        index = PageIndex(elasticsearch_class=FakeElasticsearch)
        self.assertTrue(index)

    def test_section_index(self):
        index = SectionIndex(elasticsearch_class=FakeElasticsearch)
        self.assertTrue(index)

    @patch('readthedocs.search.indexes.ProjectIndex', new_callable=MockIndex)
    @patch('readthedocs.search.indexes.PageIndex', new_callable=MockIndex)
    def test_search_project(self, mock_index, mock2):
        from readthedocs.search.lib import search_project
        foo = search_project({}, "ciao")
        self.assertTrue(foo)

    @patch('readthedocs.search.indexes.PageIndex', new_callable=MockIndex)
    @patch('readthedocs.search.indexes.ProjectIndex', new_callable=MockIndex)
    def test_search_file(self, mock_index, mock2):
        from readthedocs.search.lib import search_file
        self.client.login(username='eric', password='test')
        r = self.client.get(reverse('search'), {'type': 'file'})
        foo = search_file(r.wsgi_request, 'lorem', project_slug='pip')
        self.assertTrue(foo)

    def perform_request_mock(self, method, url, params=None, body=None, timeout=None, ignore=()):
        """
        Elastic Search Urllib3HttpConnection mock
        the response is taken by a real search on a db after loading
        the test fixtures (eric and test_data)
        """
        headers = HTTPHeaderDict(
            {'content-length': '893', 'content-type': 'application/json; charset=UTF-8'}
        )
        raw_data = """{
            "took": 51,
            "timed_out": false,
            "_shards": {
                "total": 5,
                "successful": 5,
                "skipped": 0,
                "failed": 0
            },
            "hits": {
                "total": 2,
                "max_score": 2.8768208,
                "hits": [
                    {
                        "_index": "readthedocs",
                        "_type": "project",
                        "_id": "3",
                        "_score": 2.8768208,
                        "_source": {
                            "name": "pip",
                            "description": "Praesent turpis. Nulla porta dolor.",
                            "lang": "en",
                            "url": "/projects/pip/",
                            "slug": "pip"
                        },
                        "highlight": {
                            "name": [
                                "<em>pip</em>"
                            ]
                        }
                    },
                    {
                        "_index": "readthedocs",
                        "_type": "project",
                        "_id": "6",
                        "_score": 1.8232156,
                        "_source": {
                            "name": "Pip",
                            "description": "",
                            "lang": "en",
                            "url": "/projects/pip/",
                            "slug": "pip"
                        },
                        "highlight": {
                            "name": [
                                "<em>Pip</em>"
                            ]
                        }
                    }
                ]
            },
            "aggregations": {
                "language": {
                    "doc_count_error_upper_bound": 0,
                    "sum_other_doc_count": 0,
                    "buckets": [
                        {
                            "key": "en",
                            "doc_count": 2
                        }
                    ]
                }
            }
        }"""
        return 200, headers, raw_data

    @patch('elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request', side_effect=perform_request_mock)
    def test_search_project(self, perform_request_mock):
        """
        Tests the search view (by project) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        In this case it should be something like this:
        {
            "size": 50,
            "query": {
                "bool": {"should": [
                    {"match": {"name": {"query": "pip", "boost": 10}}},
                    {"match": {"description": {"query": "pip"}}}
                ]}
            },
            "_source": ["name", "slug", "description", "lang", "url"],
            "aggs": {
                "language": {"terms": {"field": "lang.keyword"}}
            }, "highlight": {"fields": {"name": {}, "description": {}}}
        }
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            reverse('search'),
            {'q': 'pip', 'type': 'project', 'project': None}
        )
        self.assertEqual(r.status_code, 200)
        query_dict = perform_request_mock.call_args_list[0][0][3]
        self.assertTrue('"query": "pip"' in query_dict)
        main_hit =r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['fields']['name'], 'pip')
        self.assertEqual(main_hit['fields']['slug'], 'pip')

    @patch('elasticsearch.connection.http_urllib3.Urllib3HttpConnection.perform_request', side_effect=perform_request_mock)
    def test_search_file(self, perform_request_mock):
        """
        Tests the search view (by file) by mocking the perform request method
        of the elastic search module. Checks the query string provided
        to elastic search.
        In this case it should be something like this:
        {
            "size": 50,
            "query": {
                "bool": {
                    "filter": [{"term": {"version": "latest"}}],
                    "should": [
                        {"match_phrase": {"title": {"query": "pip", "boost": 10, "slop": 2}}},
                        {"match_phrase": {"headers": {"query": "pip", "boost": 5, "slop": 3}}},
                        {"match_phrase": {"content": {"query": "pip", "slop": 5}}}]
                        }
                    },
                "_source": ["title", "project", "version", "path"],
                "aggs": {"project": {"terms": {"field": "project.keyword"}},
                "taxonomy": {"terms": {"field": "taxonomy.keyword"}},
                "version": {"terms": {"field": "version.keyword"}}},
                "highlight": {"fields": {"content": {}, "headers": {}, "title": {}}}
            }
        }
        """
        self.client.login(username='eric', password='test')
        r = self.client.get(
            reverse('search'),
            {'q': 'pip', 'type': 'file'}
        )
        self.assertEqual(r.status_code, 200)
        query_dict = perform_request_mock.call_args_list[0][0][3]
        self.assertTrue('"query": "pip"' in query_dict)
        self.assertTrue('"title": {"query"' in query_dict)
        self.assertTrue('"headers": {"query"' in query_dict)
        self.assertTrue('"content": {"query"' in query_dict)
        main_hit =r.context['results']['hits']['hits'][0]
        self.assertEqual(r.status_code, 200)
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['_type'], 'project')
        self.assertEqual(main_hit['fields']['name'], 'pip')
        self.assertEqual(main_hit['fields']['slug'], 'pip')

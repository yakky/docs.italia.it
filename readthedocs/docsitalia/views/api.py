# -*- coding: utf-8 -*-
"""Docs italia api"""
from __future__ import absolute_import

from dal import autocomplete
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.constants import PUBLIC
from readthedocs.restapi.views.model_views import ProjectViewSet
from readthedocs.restapi.serializers import VersionSerializer
from readthedocs.search.indexes import PageIndex

from ..models import AllowedTag
from ..serializers import (
    DocsItaliaProjectSerializer, DocsItaliaProjectAdminSerializer)


class DocsItaliaProjectViewSet(ProjectViewSet):  # pylint: disable=too-many-ancestors

    """Like :py:class:`ProjectViewSet` but using slug as lookup key."""

    lookup_field = 'slug'
    serializer_class = DocsItaliaProjectSerializer
    admin_serializer_class = DocsItaliaProjectAdminSerializer

    def get_queryset(self):
        """
        Filter projects by tags, publisher and project passed as query parameters

        e.g. ?tags=tag1,tag2, ?publisher=publisher-slug, ?project=project-slug

        """
        qs = super(DocsItaliaProjectViewSet, self).get_queryset()
        tags = self.request.query_params.get('tags', None)
        if tags:
            tags = tags.split(',')
            qs = qs.filter(tags__slug__in=tags).distinct()
        publisher = self.request.query_params.get('publisher', None)
        if publisher:
            qs = qs.filter(publisherproject__publisher__slug=publisher)
        project = self.request.query_params.get('project', None)
        if project:
            qs = qs.filter(publisherproject__slug=project)
        return qs

    @detail_route()
    def active_versions(self, request, **kwargs):
        """Returns active versions, non private, of a project"""
        project = self.get_project_for_user_or_404(
            kwargs[self.lookup_field])
        versions = project.versions.filter(active=True, privacy_level=PUBLIC)
        return Response({
            'versions': VersionSerializer(versions, many=True).data,
        })


class DocSearch(APIView):

    """Search api for documentation builds."""

    def _build_es_query(self, query, project_slug, version_slug):  # noqa
        # c&p straight from search.lib.search_file AMA
        body = {
            # avoid elastic search returning hits with very low score
            "min_score": getattr(settings, 'ES_SEARCH_FILE_MIN_SCORE', 1),
            "query": {
                "bool": {
                    "should": [
                        {"match_phrase": {
                            "title": {
                                "query": query,
                                "boost": 10,
                                "slop": 2,
                            },
                        }},
                        {"match_phrase": {
                            "headers": {
                                "query": query,
                                "boost": 5,
                                "slop": 3,
                            },
                        }},
                        {"match_phrase": {
                            "content": {
                                "query": query,
                                "slop": 5,
                            },
                        }},
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "headers": {},
                    "content": {},
                }
            },
            "_source": ["title", "project", "version", "path"],
            "size": 50  # TODO: Support pagination.
        }
        body['query']['bool']['filter'] = [
            {"terms": {"project": [project_slug]}},
            {'term': {'version': version_slug}},
        ]
        return body

    def get(self, request):
        """Search API: takes project, version and q as mandatory query strings"""
        project_slug = self.request.query_params.get('project')
        version_slug = self.request.query_params.get('version')
        query = self.request.query_params.get('q')

        if not all([project_slug, version_slug, query]):
            raise ParseError()

        try:
            project = Project.objects.get(slug=project_slug)
            Version.objects.public(
                user=request.user,
                project=project,
            ).get(slug=version_slug)
        except (Project.DoesNotExist, Version.DoesNotExist):
            raise ParseError()

        body = self._build_es_query(query, project_slug, version_slug)
        results = PageIndex().search(body, routing=project_slug)
        if results is None:
            return Response({'error': 'No results found'},
                            status=status.HTTP_404_NOT_FOUND)

        # taken from restapi/views/search_views.py
        # Supplement result paths with domain information on project
        hits = results.get('hits', {}).get('hits', [])
        for (i, hit) in enumerate(hits):
            fields = hit.get('_source', {})
            canonical_url = project.get_docs_url(version_slug=version_slug)
            results['hits']['hits'][i]['_source']['link'] = (
                canonical_url + fields.get('path')
            )
            # we cannot render attributes starting with an underscore
            results['hits']['hits'][i]['fields'] = results['hits']['hits'][i]['_source']
            del results['hits']['hits'][i]['_source']

        return Response({'results': results})


# pylint: disable=too-many-ancestors
class AllowedTagAutocomplete(autocomplete.Select2QuerySetView):

    """Allowed tag listing for autocomplete purpose."""

    def get_queryset(self):
        """Filter and order allowed tags."""
        qs = AllowedTag.objects.filter(enabled=True)
        if self.q:
            return qs.filter(name__istartswith=self.q)
        return qs.order_by('name')

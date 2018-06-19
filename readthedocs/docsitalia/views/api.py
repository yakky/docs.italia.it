# -*- coding: utf-8 -*-
"""Docs italia api"""
from __future__ import absolute_import

from readthedocs.restapi.views.model_views import ProjectViewSet

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

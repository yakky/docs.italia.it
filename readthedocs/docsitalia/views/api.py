# -*- coding: utf-8 -*-
"""Docs italia api"""
from __future__ import absolute_import

from readthedocs.restapi.views.model_views import ProjectViewSet

from ..serializers import DocsItaliaProjectSerializer


class DocsItaliaProjectViewSet(ProjectViewSet):  # pylint: disable=too-many-ancestors

    """Like :py:class:`ProjectViewSet` but using slug as lookup key."""

    lookup_field = 'slug'
    serializer_class = DocsItaliaProjectSerializer

    def get_queryset(self):
        """
        Filter projects by tags

        Takes a GET with tags separated by a comma:
        tags=tag1,tag2
        """
        qs = super(DocsItaliaProjectViewSet, self).get_queryset()
        tags = self.request.query_params.get('tags', None)
        if tags:
            tags = tags.split(',')
            qs = qs.filter(tags__slug__in=tags).distinct()
        return qs

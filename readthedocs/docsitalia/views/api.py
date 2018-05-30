# -*- coding: utf-8 -*-
"""Docs italia api"""
from __future__ import absolute_import

from rest_framework import viewsets
from rest_framework import mixins

from readthedocs.projects.models import Project

from ..serializers import DocsItaliaProjectSerializer


class ProjectsByTagViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):  # pylint: disable=too-many-ancestors

    """
    Projects by Tag DRF list model mixin

    Takes a GET with tags separated by a comma:
    tags=tag1,tag2
    """

    serializer_class = DocsItaliaProjectSerializer
    allowed_methods = ('GET',)

    def get_queryset(self):
        """filter projects by tags"""
        tags = self.request.query_params.get('tags', None)
        if tags:
            tags = tags.split(',')
            queryset = Project.objects.filter(tags__slug__in=tags).distinct()
        else:
            queryset = Project.objects.none()
        return queryset

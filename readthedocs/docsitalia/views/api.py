# -*- coding: utf-8 -*-
"""Docs italia api"""
from __future__ import absolute_import

from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.response import Response

from readthedocs.projects.models import Project

from ..serializers import ProjectsByTagSerializer, ProjectTagsSerializer


class ProjectsByTagViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):  # pylint: disable=too-many-ancestors

    """
    Projects by Tag DRF list model mixin

    Takes a GET with tags separated by a comma:
    tags=tag1,tag2
    """

    serializer_class = ProjectsByTagSerializer
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


class ProjectTagsViewSet(viewsets.ViewSet):

    """Return project tags"""

    serializer_class = ProjectTagsSerializer
    allowed_methods = ('GET',)
    lookup_field = 'slug'

    @classmethod
    def retrieve(cls, _, slug=None):
        """Get the project by slug"""
        queryset = Project.objects.all()
        user = get_object_or_404(queryset, slug=slug)
        serializer = ProjectTagsSerializer(user)
        return Response(serializer.data)

# -*- coding: utf-8 -*-
"""Docs italia serializers"""
from __future__ import absolute_import

from rest_framework import serializers
from readthedocs.restapi.serializers import ProjectSerializer
from readthedocs.projects.models import Project


class ProjectsByTagSerializer(ProjectSerializer):

    """Projects by Tag DRF Serializer"""

    publisher = serializers.SerializerMethodField()
    publisher_project = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = (
            'id', 'name', 'slug', 'description',
            'canonical_url', 'publisher', 'publisher_project',
        )

    @classmethod
    def get_publisher(cls, obj):
        """gets the publisher"""
        p_p = obj.publisherproject_set.first()
        if p_p.publisher:
            return {
                'name': p_p.publisher.name,
                'canonical_url': p_p.publisher.get_canonical_url()
            }

    @classmethod
    def get_publisher_project(cls, obj):
        """gets the publisher project"""
        p_p = obj.publisherproject_set.first()
        return {
            'name': p_p.name,
            'canonical_url': p_p.get_canonical_url()
        }


class TagsListField(serializers.ListField):

    """Django taggit list field"""

    def to_representation(self, data):
        """returns the project tags as a list"""
        return [tag for tag in data.values_list('name', flat=True)]


class ProjectTagsSerializer(ProjectSerializer):

    """Project Tags DRF Serializer"""

    tags = TagsListField()
    lookup_field = 'slug'

    class Meta:
        model = Project
        fields = ('tags',)

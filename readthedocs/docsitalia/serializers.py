# -*- coding: utf-8 -*-
"""Docs italia serializers"""
from __future__ import absolute_import

from rest_framework import serializers
from readthedocs.restapi.serializers import ProjectSerializer


class DocsItaliaProjectSerializer(ProjectSerializer):

    """Projects by Tag DRF Serializer"""

    publisher = serializers.SerializerMethodField()
    publisher_project = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = (
            'id',
            'name', 'slug', 'description', 'language',
            'programming_language', 'repo', 'repo_type',
            'default_version', 'default_branch',
            'documentation_type',
            'users',
            'canonical_url',
            'tags', 'publisher', 'publisher_project',
        )

    @staticmethod
    def get_publisher(obj):
        """gets the publisher"""
        p_p = obj.publisherproject_set.first()
        if p_p:
            return {
                'name': p_p.publisher.metadata.get('name', ''),
                'canonical_url': p_p.publisher.get_canonical_url()
            }

    @staticmethod
    def get_publisher_project(obj):
        """gets the publisher project"""
        p_p = obj.publisherproject_set.first()
        if p_p:
            return {
                'name': p_p.metadata.get('name', ''),
                'canonical_url': p_p.get_canonical_url()
            }

    @staticmethod
    def get_tags(obj):
        """gets the project tags"""
        return obj.tags.slugs()

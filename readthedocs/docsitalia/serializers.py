# -*- coding: utf-8 -*-
"""Docs italia serializers"""
from __future__ import absolute_import

from rest_framework import serializers
from readthedocs.restapi.serializers import ProjectSerializer


class DocsItaliaProjectSerializer(ProjectSerializer):

    """DocsItalia custom serializer for Projects"""

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


class DocsItaliaProjectAdminSerializer(DocsItaliaProjectSerializer):

    """
    Project serializer for admin only access.

    Includes special internal fields that don't need to be exposed through the
    general API, mostly for fields used in the build process
    """

    features = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='feature_id',
    )

    class Meta(DocsItaliaProjectSerializer.Meta):
        fields = DocsItaliaProjectSerializer.Meta.fields + (
            'enable_epub_build',
            'enable_pdf_build',
            'conf_py_file',
            'analytics_code',
            'cdn_enabled',
            'container_image',
            'container_mem_limit',
            'container_time_limit',
            'install_project',
            'use_system_packages',
            'suffix',
            'skip',
            'requirements_file',
            'python_interpreter',
            'features',
        )

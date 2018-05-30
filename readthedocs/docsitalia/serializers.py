# -*- coding: utf-8 -*-
"""Docs italia serializers"""
from __future__ import absolute_import

from rest_framework import serializers

from readthedocs.projects.models import Project


class ProjectsByTagSerializer(serializers.HyperlinkedModelSerializer):

    """Projects by Tag DRF Serializer"""

    class Meta:
        model = Project
        fields = ('name', 'description', 'url')

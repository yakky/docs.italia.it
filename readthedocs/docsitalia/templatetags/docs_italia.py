"""Template tags for docs italia app."""
from __future__ import absolute_import

from django import template

from ..models import PublisherProject

register = template.Library()


@register.filter
def get_publisher_project(slug):
    """get a publisher project from the slug"""
    try:
        return PublisherProject.objects.get(slug=slug)
    except PublisherProject.DoesNotExist:
        return None

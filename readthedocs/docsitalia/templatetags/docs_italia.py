"""Template tags for docs italia app."""
from __future__ import absolute_import

from django import template
from readthedocs.core.resolver import resolve

from ..models import PublisherProject

register = template.Library()


@register.filter
def get_publisher_project(slug):
    """get a publisher project from the slug"""
    try:
        return PublisherProject.objects.get(slug=slug)
    except PublisherProject.DoesNotExist:
        return None


@register.simple_tag(name="doc_url_patched")
def make_document_url(project, version=None, page=''):
    """create the full document URL and appends index.html if root"""
    if not project:
        return ""
    url = resolve(project=project, version_slug=version, filename=page)
    if url.endswith('/'):
        url = '%sindex.html' % url
    return url

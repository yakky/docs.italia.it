# -*- coding: utf-8 -*-
"""Public project views."""

from __future__ import absolute_import
from __future__ import unicode_literals

from django.shortcuts import render
from readthedocs.docsitalia.models import PublisherProject, Publisher
from django.views.generic import DetailView, ListView


class PublisherList(ListView):

    """List view of :py:class:`Publisher` instances."""

    model = Publisher

    def get_context_data(self, **kwargs):
        context = super(PublisherList, self).get_context_data(**kwargs)
        return context


class PublisherIndex(DetailView):

    """Detail view of :py:class:`Publisher` instances."""

    model = Publisher

    def get_context_data(self, **kwargs):
        context = super(PublisherIndex, self).get_context_data(**kwargs)
        return context


class PublisherProjectIndex(DetailView):

    """Detail view of :py:class:`PublisherProject` instances."""

    model = PublisherProject

    def get_context_data(self, **kwargs):
        context = super(PublisherProjectIndex, self).get_context_data(**kwargs)
        return context

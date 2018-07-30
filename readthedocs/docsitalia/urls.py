from __future__ import absolute_import

from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url
from django.views.generic.base import RedirectView, TemplateView

from readthedocs.constants import pattern_opts
from rest_framework import routers

from .views.core_views import (
    DocsItaliaHomePage, PublisherIndex, PublisherProjectIndex, DocsItaliaImport)
from .views import integrations, api

router = routers.DefaultRouter()
router.register(r'document', api.DocsItaliaProjectViewSet, base_name='docsitalia-document')

docsitalia_urls = [
    url(r'^api/', include(router.urls)),
    url(r'webhook/github/(?P<publisher_slug>{project_slug})/$'.format(**pattern_opts),
        integrations.MetadataGitHubWebhookView.as_view(),
        name='metadata_webhook_github'),
    url((r'webhook/(?P<publisher_slug>{project_slug})/'
         r'(?P<integration_pk>{integer_pk})/$'.format(**pattern_opts)),
        integrations.MetadataWebhookView.as_view(),
        name='metadata_webhook'),
    url(r'^dashboard/import/$',
        DocsItaliaImport.as_view(),
        name='projects_import'),
    url(r'^dashboard/import/manual/$',
        RedirectView.as_view(pattern_name='projects_import'),
        name='projects_import_manual'),
    url(r'^dashboard/import/manual/demo/$',
        RedirectView.as_view(pattern_name='projects_import'),
        name='projects_import_demo'),
]

urlpatterns = [
    url(r'^docsitalia/', include(docsitalia_urls)),
    url(
        r'^$',
        DocsItaliaHomePage.as_view(),
        name='homepage'
    ),
    url(
        r'^che-cos-e-docs-italia/$',
        TemplateView.as_view(template_name='docsitalia/about.html'),
        name='about_docs_italia'
    ),
    url(
        r'^privacy-policy/$',
        TemplateView.as_view(template_name='docsitalia/privacy-policy.html'),
        name='privacy_policy'
    ),
    url(
        r'^cookies-policy/$',
        TemplateView.as_view(template_name='docsitalia/cookies-policy.html'),
        name='cookies_policy'
    ),
    url(
        r'^note-legali/$',
        TemplateView.as_view(template_name='docsitalia/note-legali.html'),
        name='note_legali'
    ),
    url(
        r'^(?P<slug>[-\w]+)/$',
        PublisherIndex.as_view(),
        name='publisher_detail'
    ),
    url(
        r'^(?P<publisherslug>[-\w]+)/(?P<slug>[-\w]+)/$',
        PublisherProjectIndex.as_view(),
        name='publisher_project_detail'
    ),
]

if apps.is_installed('docs_italia_convertitore_web'):
    urlpatterns.insert(
        0,
        url(r'converti/',
            include('docs_italia_convertitore_web.urls', namespace='docs_italia_convertitore'))
    )

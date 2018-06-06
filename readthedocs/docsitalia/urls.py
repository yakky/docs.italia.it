from __future__ import absolute_import

from django.conf.urls import include, url

from readthedocs.constants import pattern_opts
from rest_framework import routers

from .views.core_views import DocsItaliaHomePage, PublisherIndex, PublisherProjectIndex
from .views import integrations, api

router = routers.DefaultRouter()
router.register(r'project', api.DocsItaliaProjectViewSet, base_name='project')
router.register(r'projects-by-tag', api.ProjectsByTagViewSet, base_name='projects-by-tag')

docsitalia_urls = [
    url(r'^api/', include(router.urls)),
    url(r'webhook/github/(?P<publisher_slug>{project_slug})/$'.format(**pattern_opts),
        integrations.MetadataGitHubWebhookView.as_view(),
        name='metadata_webhook_github'),
    url((r'webhook/(?P<publisher_slug>{project_slug})/'
         r'(?P<integration_pk>{integer_pk})/$'.format(**pattern_opts)),
        integrations.MetadataWebhookView.as_view(),
        name='metadata_webhook'),
]


urlpatterns = [
    url(r'^docsitalia/', include(docsitalia_urls)),
    url(
        r'^$',
        DocsItaliaHomePage.as_view(),
        name='homepage'
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

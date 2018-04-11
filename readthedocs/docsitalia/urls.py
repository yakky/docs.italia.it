from __future__ import absolute_import
from django.conf.urls import url

from .views.core_views import PublisherIndex, PublisherList, PublisherProjectIndex


urlpatterns = [
    url(
        r'^$',
        PublisherList.as_view(),
        name='publisher_list'
    ),
    url(
        r'^(?P<slug>[-\w]+)$',
        PublisherIndex.as_view(),
        name='publisher_detail'
    ),
    url(
        r'^(?P<publisherslug>[-\w]+)/(?P<slug>[-\w]+)$',
        PublisherProjectIndex.as_view(),
        name='publisher_project_detail'
    ),
]
# -*- coding: utf-8 -*-
"""Admin for the docsitalia app."""

from django.contrib import admin

from .models import Publisher, PublisherProject


class PublisherProjectAdmin(admin.ModelAdmin):

    """Admin view for :py:class:`PublisherProject`"""

    list_filter = ('featured',)


admin.site.register(Publisher)
admin.site.register(PublisherProject, PublisherProjectAdmin)

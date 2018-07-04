# -*- coding: utf-8 -*-
"""Admin for the docsitalia app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .forms import PublisherAdminForm
from .models import Publisher, PublisherProject


class PublisherAdmin(admin.ModelAdmin):

    """Admin view for :py:class:`Publisher`"""

    form = PublisherAdminForm
    readonly_fields = ('metadata', 'projects_metadata',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'active'),
        }),
        (_('Advanced Settings'), {
            'classes': ('collapse',),
            'fields': (
                'metadata',
                'projects_metadata',
                'config_repo_name',
                'remote_organization',
            )
        }),
    )


class PublisherProjectAdmin(admin.ModelAdmin):

    """Admin view for :py:class:`PublisherProject`"""

    list_filter = ('featured',)


admin.site.register(Publisher, PublisherAdmin)
admin.site.register(PublisherProject, PublisherProjectAdmin)

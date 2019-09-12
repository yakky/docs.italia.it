# -*- coding: utf-8 -*-
"""Forms for the docsitalia app."""

import logging
from builtins import str # noqa

from django import forms
from django.utils.translation import ugettext_lazy as _

from .github import get_metadata_for_publisher
from .metadata import PUBLISHER_SETTINGS, PROJECTS_SETTINGS, InvalidMetadata
from .models import Publisher


log = logging.getLogger(__name__) # noqa


class PublisherAdminForm(forms.ModelForm):

    """Form for Publisher Admin"""

    def clean(self):
        """Check if the metadata is valid at clean time"""
        super(PublisherAdminForm, self).clean()

        # create the minimal object required for validation. We mock the
        # required RemoteOrganization attributes to reuse the same object.
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        publisher = Publisher(slug=slug, name=name)
        publisher.url = ''

        msg = _('Error retrieving {filename}')
        try:
            get_metadata_for_publisher(
                publisher, publisher, PUBLISHER_SETTINGS)
        except InvalidMetadata as exception:
            log.debug(
                'Cannot save publisher: %s', exception)
            raise forms.ValidationError(str(exception))
        except Exception:
            msg = msg.format(filename=PUBLISHER_SETTINGS)
            log.debug(
                'Cannot save publisher: %s', msg)
            raise forms.ValidationError(msg)

        try:
            get_metadata_for_publisher(
                publisher, publisher, PROJECTS_SETTINGS)
        except InvalidMetadata as exception:
            log.debug(
                'Cannot save publisher: %s', exception)
            raise forms.ValidationError(str(exception))
        except Exception:
            msg = msg.format(filename=PROJECTS_SETTINGS)
            log.debug(
                'Cannot save publisher: %s', msg)
            raise forms.ValidationError(msg)

    class Meta:
        model = Publisher
        fields = '__all__'

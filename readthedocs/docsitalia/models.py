# -*- coding: utf-8 -*-
"""Signals for the docsitalia app."""

from __future__ import absolute_import
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.core.urlresolvers import reverse

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.oauth.models import RemoteOrganization

from readthedocs.core.resolver import resolver
from .utils import load_yaml


PUBLISHER_SETTINGS = 'publisher_settings.yml'
PROJECTS_SETTINGS = 'projects_settings.yml'
DOCUMENT_SETTINGS = 'document_settings.yml'

PUBLISHER_REQUIRED_FIELDS = 'name', 'description'
PROJECT_REQUIRED_FIELDS = 'name', 'description', 'documents'
DOCUMENT_REQUIRED_FIELDS = 'name', 'description', 'tags'


def validate_publisher_metadata(org, settings): # noqa
    """Validate the publisher metadata"""
    data = load_yaml(settings)
    try:
        publisher = data['publisher']
        for field in PUBLISHER_REQUIRED_FIELDS:
            if not publisher[field]:
                raise ValueError('Missing required field "%s" in %s' % (field, publisher))
    except (KeyError, TypeError):
        raise ValueError('General error in parsing publisher metadata %s' % data)
    return data


def validate_projects_metadata(org, settings):
    """Validate the projects metadata"""
    data = load_yaml(settings)
    try:
        projects = data['projects']
        for project in projects:
            # required values for a well formed configuration
            for field in PROJECT_REQUIRED_FIELDS:
                if not project[field]:
                    raise ValueError('Missing required field "%s" in %s' % (field, project))
            if not project['documents'][0]:
                raise ValueError('Missing required field "%s" in %s' % ('documents', project))
            for index, document in enumerate(project['documents']):
                # expand the document repository to an url so it's easier to query at
                # Project import time
                project['documents'][index] = {
                    'repository':  document,
                    'repo_url': '{}/{}'.format(org.url, document)
                }
            project['slug'] = slugify(project['name'])
    except (KeyError, TypeError):
        raise ValueError('General error in parsing projects metadata %s' % data)
    return data


def validate_document_metadata(org, settings): # noqa
    """Validate the document metadata"""
    data = load_yaml(settings)
    try:
        document = data['document']
        for field in DOCUMENT_REQUIRED_FIELDS:
            if not document[field]:
                raise ValueError('Missing required field "%s" in %s' % (field, document))
    except (KeyError, TypeError):
        raise ValueError('General error in parsing document metadata %s' % data)
    return data


SETTINGS_VALIDATORS = {
    PUBLISHER_SETTINGS: validate_publisher_metadata,
    PROJECTS_SETTINGS: validate_projects_metadata,
    DOCUMENT_SETTINGS: validate_document_metadata,
}


def update_project_from_metadata(project, metadata):
    """Update a project instance with the validated  project metadata"""
    document = metadata['document']
    project.name = document['name']
    project.description = document['description']
    project.tags.set(*document['tags'], clear=True)
    try:
        project.language = document['language']
    except KeyError:
        project.language = 'it'
    project.save()


@python_2_unicode_compatible
class Publisher(models.Model):

    """
    The Publisher is the organization that hosts projects (PublisherProject)

    The idea is to tie a Publisher to a RemoteOrganization, if we have a
    Publisher instance for a RemoteOrganization we can sync its data as
    available in the well-known repo and config files.

    Given the requirement of handling content in different languages we don't
    want to duplicate the publisher data here so the config file is the source
    of truth. A parsed version of the configuration is saved in the metadata
    field.

    The publisher homepage is handled by a django view with data from the
    metadata field.
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # we need something unique
    name = models.CharField(_('Name'), max_length=255, unique=True, help_text=_(
        'Publisher\'s name in full. You can refer to the "name" field from '
        '"publisher_settings.yml", e.g. Ministero della Documentazione.'
    ))
    slug = models.SlugField(_('Slug'), max_length=255, unique=True, help_text=_(
        'Pick the URL fragment following "https://github.com" in the organization '
        'URL, e.g ministero-della-documentazione.'
    ))

    # TODO: is this enough to hold the publisher metadata?
    # https://github.com/italia/docs-italia-starter-kit/tree/master/repo-configurazione
    metadata = JSONField(_('Publisher Metadata'), blank=True, default={})
    projects_metadata = JSONField(_('Projects Metadata'), blank=True, default={})

    # the name of the repository that will hold the metadata
    config_repo_name = models.CharField(_('Docs italia config repo'),
                                        max_length=255,
                                        default=u'docs-italia-conf')

    # the remote organization where we can find the configuration repository
    remote_organization = models.ForeignKey(RemoteOrganization,
                                            verbose_name=_('Remote organization'),
                                            null=True,
                                            blank=True)

    active = models.BooleanField(_('Active'), default=True, help_text=_(
        'Enables the import of documents.'
    ))

    def __str__(self):
        return self.name

    def create_projects_from_metadata(self, settings):
        """Create PublisherProjects from metadata"""
        slugs = []
        for project in settings['projects']:
            proj, _ = PublisherProject.objects.get_or_create(
                publisher=self,
                name=project['name'],
                slug=project['slug'],
            )
            proj.metadata = project
            proj.active = True
            proj.save()

            slugs.append(project['slug'])

        # TODO: double check this is something we want
        PublisherProject.objects.filter(
            publisher=self
        ).exclude(
            slug__in=slugs
        ).update(
            active=False
        )

    def active_publisher_projects(self):
        """Active publisher projects"""
        return self.publisherproject_set.filter(active=True)

    def get_absolute_url(self):
        """Get absolute url for publisher"""
        return reverse('publisher_detail', args=[self.slug])

    def get_canonical_url(self):
        """Get canonical url for publisher"""
        return resolver.resolve_docsitalia(self.slug)


@python_2_unicode_compatible
class PublisherProject(models.Model):

    """
    The PublisherProject is the project that contains documents

    These are created from the organization metadata and created at import time

    The publisher project homepage is handled by a django view with data
    from the metadata field.
    """

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # we need something unique
    name = models.CharField(_('Name'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)

    # this holds the metadata for the single project
    metadata = JSONField(_('Metadata'), blank=True, default={})

    # the organization that holds the project
    publisher = models.ForeignKey(Publisher, verbose_name=_('Publisher'))
    # projects are the documents :)
    projects = models.ManyToManyField(Project, verbose_name=_('Projects'))

    featured = models.BooleanField(_('Featured'), default=False)
    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return self.name

    def active_documents(self):
        """Active documents"""
        with_public_version = Version.objects.filter(
            privacy_level='public',
            active=True,
        ).values_list(
            'project',
            flat=True
        )
        return self.projects.filter(
            pk__in=with_public_version
        ).order_by(
            '-modified_date', '-pub_date'
        )

    def get_absolute_url(self):
        """get absolute url for publisher project"""
        return reverse('publisher_project_detail', args=[self.publisher.slug, self.slug])

    def get_canonical_url(self):
        """get canonical url for publisher project"""
        return resolver.resolve_docsitalia(self.publisher.slug, self.slug)


@python_2_unicode_compatible
class PublisherIntegration(models.Model):

    """Inbound webhook integration for publisher."""

    GITHUB_WEBHOOK = 'github_webhook'

    WEBHOOK_INTEGRATIONS = (
        (GITHUB_WEBHOOK, _('GitHub incoming webhook')),
    )

    INTEGRATIONS = WEBHOOK_INTEGRATIONS

    publisher = models.ForeignKey(Publisher, related_name='integrations')
    integration_type = models.CharField(
        _('Integration type'),
        max_length=32,
        choices=INTEGRATIONS
    )
    provider_data = JSONField(_('Provider data'), blank=True, default={})

    # Integration attributes
    has_sync = True

    def __str__(self):
        return (
            _('{0} for {1}')
            .format(self.get_integration_type_display(), self.publisher.name))

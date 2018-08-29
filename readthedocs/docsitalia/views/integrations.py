"""
Endpoints integrating with Github webhooks for our metadata.

See restapi.views.integrations.
"""

from __future__ import absolute_import

import json
import logging

from builtins import object  # pylint: disable=redefined-builtin
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.docsitalia.metadata import (
    PUBLISHER_SETTINGS, PROJECTS_SETTINGS, InvalidMetadata)
from readthedocs.docsitalia.models import (
    Publisher, PublisherIntegration)

from readthedocs.docsitalia.github import get_metadata_for_publisher
from readthedocs.integrations.models import HttpExchange
from readthedocs.integrations.utils import normalize_request_payload


log = logging.getLogger(__name__) # noqa


class MetadataWebhookMixin(object): # noqa

    """Base class for Metadata Webhook mixins."""

    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer,)
    integration = None
    integration_type = None

    def post(self, request, publisher_slug):
        """Set up webhook post view with request and publisher objects."""
        self.request = request
        self.publisher = None
        try:
            self.publisher = Publisher.objects.get(slug=publisher_slug)
        except Publisher.DoesNotExist:
            raise NotFound('Publisher not found')
        self.data = self.get_data()
        resp = self.handle_webhook()
        if resp is None:
            log.info('Unhandled webhook event')
            resp = {'detail': 'Unhandled webhook event'}
        return Response(resp)

    def finalize_response(self, req, *args, **kwargs):
        """If the publisher was set on POST, store an HTTP exchange."""
        resp = super(MetadataWebhookMixin, self).finalize_response(req, *args, **kwargs)
        if hasattr(self, 'publisher') and self.publisher:
            HttpExchange.objects.from_exchange(
                req,
                resp,
                related_object=self.get_integration(),
                payload=self.data,
            )
        return resp

    def get_data(self):
        """Normalize posted data."""
        return normalize_request_payload(self.request)

    def handle_webhook(self):
        """Handle webhook payload."""
        raise NotImplementedError

    def get_integration(self):
        """
        Get or create an inbound webhook to track webhook requests.

        We shouldn't need this, but to support legacy webhooks, we can't assume
        that a webhook has ever been created on our side. Most providers don't
        pass the webhook ID in either, so we default to just finding *any*
        integration from the provider. This is not ideal, but the
        :py:class:`WebhookView` view solves this by performing a lookup on the
        integration instead of guessing.
        """
        # `integration` can be passed in as an argument to `as_view`, as it is
        # in `WebhookView`
        if self.integration is not None:
            return self.integration
        integration, _ = PublisherIntegration.objects.get_or_create(
            publisher=self.publisher,
            integration_type=self.integration_type,
        )
        return integration

    def get_response_push(self, publisher, branches): # noqa
        """
        Update metadata on push events and return API response.

        Return a JSON response with the following::

            {
                "build_triggered": true,
                "project": "project_name",
                "versions": [...]
            }

        :param publisher: Publisher instance
        :type publisher: Publisher
        :param branches: List of branch names to build
        :type branches: list(str)
        """
        # we get metadata only from the master branch
        to_update = [branch for branch in branches if branch == 'master']
        if to_update:
            # TODO: we should probably do this inside a task as core.utils.trigger_build
            org_obj = publisher.remote_organization
            try:
                publisher_metadata = get_metadata_for_publisher(
                    org_obj, publisher, PUBLISHER_SETTINGS)
                projects_metadata = get_metadata_for_publisher(
                    org_obj, publisher, PROJECTS_SETTINGS)
            except InvalidMetadata as exception:
                log.debug(
                    'Syncing GitHub organizations metadata from webhook failed: %s', exception)
                # push the failure to the caller
                to_update = False
            else:
                publisher.metadata = publisher_metadata
                publisher.projects_metadata = projects_metadata
                publisher.save()
                publisher.create_projects_from_metadata(projects_metadata)

        if not to_update:
            log.info('Skipping metadata update for publisher: publisher=%s branches=%s',
                     publisher, branches)
        triggered = True if to_update else False
        return {'build_triggered': triggered,
                'publisher': publisher.slug,
                'versions': to_update}


class MetadataGitHubWebhookView(MetadataWebhookMixin, APIView):

    """
    Metadata webhook consumer for GitHub.

    Accepts webhook events from GitHub, 'push' events trigger builds. Expects the
    webhook event type will be included in HTTP header ``X-GitHub-Event``, and
    we will have a JSON payload.

    Expects the following JSON::

        {
            "ref": "branch-name",
            ...
        }
    """

    integration_type = PublisherIntegration.GITHUB_WEBHOOK

    def get_data(self):
        """Normalize posted data."""
        if self.request.content_type == 'application/x-www-form-urlencoded':
            try:
                return json.loads(self.request.data['payload'])
            except (ValueError, KeyError):
                pass
        return super(MetadataGitHubWebhookView, self).get_data()

    def handle_webhook(self):
        """Handle webhook payload."""
        # Get event and trigger other webhook events
        event = self.request.META.get('HTTP_X_GITHUB_EVENT', 'push')

        # TODO: the upstream code sends a signal but we don't have any use for it

        # Handle push events
        if event == 'push':
            try:
                branches = [self.data['ref'].replace('refs/heads/', '')]
                return self.get_response_push(self.publisher, branches)
            except KeyError:
                raise ParseError('Parameter "ref" is required')


class MetadataWebhookView(APIView):

    """Dispatcher for platform specific Metadata webhooks, only Github supported."""

    VIEW_MAP = {
        PublisherIntegration.GITHUB_WEBHOOK: MetadataGitHubWebhookView,
    }

    def post(self, request, publisher_slug, integration_pk):
        """Set up webhook post view with request and Publisher objects."""
        integration = get_object_or_404(
            PublisherIntegration,
            publisher__slug=publisher_slug,
            pk=integration_pk,
        )
        view_cls = self.VIEW_MAP[integration.integration_type]
        view = view_cls.as_view()
        return view(request, publisher_slug)

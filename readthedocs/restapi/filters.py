from django.utils.translation import ugettext_lazy as _

import django_filters

from readthedocs.projects import constants
from readthedocs.projects.models import Project, Domain
from readthedocs.projects.filters import sort_slug

ANY_REPO = (
    ('', _('Any')),
)

REPO_CHOICES = ANY_REPO + constants.REPO_CHOICES


class ProjectFilter(django_filters.FilterSet):
    slug = django_filters.CharFilter(label=_("Slug"), name='slug',
                                     action=sort_slug)
    repo = django_filters.CharFilter(label=_("Repository URL"), name='repo',
                                     lookup_type='icontains')
    repo_type = django_filters.ChoiceFilter(
        label=_("Repository Type"),
        name='repo',
        lookup_type='icontains',
        choices=REPO_CHOICES,
    )

    class Meta:
        model = Project
        fields = ('slug', 'repo', 'repo_type')


class DomainFilter(django_filters.FilterSet):
    project = django_filters.CharFilter(label=_("Project"), name='project__slug',
                                        lookup_type='exact')

    class Meta:
        model = Domain
        fields = ('project',)

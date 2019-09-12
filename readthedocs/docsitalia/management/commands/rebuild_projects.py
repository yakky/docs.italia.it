"""Rebuild documentation for all projects"""

from __future__ import absolute_import
from django.core.management.base import BaseCommand, CommandError

from readthedocs.builds.models import Build, Version
from readthedocs.projects.tasks import UpdateDocsTaskStep
from readthedocs.projects.models import Project
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.doc_builder.python_environments import Virtualenv


from readthedocs.docsitalia.models import Publisher, PublisherProject


class Command(BaseCommand):

    """Rebuild all projects command"""

    help = 'Rebuild projects'

    def add_arguments(self, parser):
        """adds arguments"""
        parser.add_argument(
            '--publisher', nargs='?', type=str,
            help='A publisher project slug'
        )
        parser.add_argument(
            '--document', nargs='?', type=str,
            help='A Read the docs document slug'
        )

    def handle(self, *args, **options):
        """handle command"""
        versions = Version.objects.all()
        publisher = options['publisher']
        document = options['document']
        if publisher:
            try:
                projects = PublisherProject.objects.filter(
                    publisher=Publisher.objects.get(slug=publisher)
                ).values_list('projects', flat=True)
                versions = versions.filter(project__in=projects)
            except Publisher.DoesNotExist:
                raise CommandError("Publisher {} doesn't exist".format(publisher))
        if document:
            try:
                project = Project.objects.get(slug=document)
                versions = versions.filter(project=project)
            except Project.DoesNotExist:
                raise CommandError("Project {} doesn't exist".format(document))
        for version in versions:
            build_env = LocalBuildEnvironment(project=version.project, version=version, build={})
            python_env = Virtualenv(version=version, build_env=build_env)
            config = load_yaml_config(version)
            task = UpdateDocsTaskStep(
                build_env=build_env, project=version.project, python_env=python_env,
                version=version, search=True, localmedia=False, config=config
            )
            build = Build.objects.create(
                project=version.project,
                version=version,
                type='html',
                state='triggered',
            )
            task.run(version.project.pk, version_pk=version.pk, build_pk=build.pk)

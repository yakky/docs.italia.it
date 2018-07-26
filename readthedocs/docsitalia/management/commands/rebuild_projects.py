"""Rebuild documentation for all projects"""

from __future__ import absolute_import
from django.core.management.base import BaseCommand

from readthedocs.builds.models import Build, Version
from readthedocs.projects.tasks import UpdateDocsTaskStep
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.doc_builder.python_environments import Virtualenv


class Command(BaseCommand):

    """Rebuild all projects command"""

    def handle(self, *args, **options):
        """handle command"""
        for version in Version.objects.all():
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

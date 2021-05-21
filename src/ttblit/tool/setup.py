import os
import logging
import pathlib
import re
import shutil
import subprocess

import click

@click.command('setup', help='Setup a project')
@click.option('--project-name', prompt=True)
@click.option('--author-name', prompt=True)
@click.option('--sdk-path', type=pathlib.Path, default=lambda: os.path.expanduser('~/32blit-sdk'), prompt='32Blit SDK path')
@click.option('--git/--no-git', prompt='Initialise a Git repository?', default=True)
def setup_cli(project_name, author_name, sdk_path, git):
    if not (sdk_path / '32blit.toolchain').exists():
        if click.confirm(f'32Blit SDK not found at "{sdk_path}", would you like to install it?', abort=True):
            click.echo('Installing SDK...')

    project_name_clean = re.sub(r'[^a-z0-9]+', '-', project_name.lower()).strip('-')
    project_path = pathlib.Path.cwd() / project_name_clean

    if project_path.exists():
        logging.critical(f'A project already exists at {project_path}!')
        raise click.Abort()

    # get the boilerplate
    click.echo('Downloading boilerplate...')
    subprocess.run(['git', 'clone', '--depth', '1', 'https://github.com/32blit/32blit-boilerplate', project_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # de-git it (using the template on GitHub also removes the history)
    shutil.rmtree(pathlib.Path(project_name_clean) / '.git')

    # do some editing
    cmakelists = open(project_path / 'CMakeLists.txt').read()
    cmakelists = cmakelists.replace('project(game)', f'project({project_name_clean})')
    open(project_path / 'CMakeLists.txt', 'w').write(cmakelists)

    metadata = open(project_path / 'metadata.yml').read()
    metadata = metadata.replace('game title', project_name).replace('you', author_name)
    open(project_path / 'metadata.yml', 'w').write(metadata)

    licence = open(project_path / 'LICENSE').read()
    licence = licence.replace('<insert your name>', author_name)
    open(project_path / 'LICENSE', 'w').write(licence)

    # re-git it if we want a git repo
    if git:
        subprocess.run(['git', 'init'], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'add', '.'], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

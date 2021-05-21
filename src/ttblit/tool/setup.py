import os
import logging
import pathlib
import re
import shutil
import subprocess
import textwrap

import click

# check environment before prompting
class SetupCommand(click.Command):
    def parse_args(self, ctx, args):
        logging.info("Checking for prerequisites...")

        # command/name/required version
        prereqs = [
            (['git', '--version'], 'Git', None),
            (['cmake', '--version'], 'CMake', [3, 9]),
            (['arm-none-eabi-gcc', '--version'], 'GCC Arm Toolchain', [7, 3])
        ]

        failed = False

        for command, name, version in prereqs:
            try:
                result = subprocess.run(command, stdout=subprocess.PIPE, text=True)

                version_str = ".".join([str(x) for x in version]) if version else 'any'
                found_version_str = re.search(r'[0-9]+\.[0-9\.]+', result.stdout).group(0)

                if version:
                    found_version_list = [int(x) for x in found_version_str.split('.')[:len(version)]]
                    if found_version_list < version:
                        logging.critical(f'Found {name} version {found_version_str}, {version_str} is required!')
                        failed = True

                logging.info(f'Found {name} version {found_version_str} (required {version_str})')
            except:
                logging.critical(f'Could not find {name}!')
                failed = True

        if failed:
            click.echo('\nCheck the documentation for info on installing.\nhttps://github.com/32blit/32blit-sdk#you-will-need')
            raise click.Abort()

        super().parse_args(ctx, args)

def install_sdk(sdk_path):
    click.echo('Installing SDK...')
    subprocess.run(['git', 'clone', 'https://github.com/32blit/32blit-sdk', sdk_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # checkout the latest release
    # TODO: could do something with the GitHub API and download the release?
    result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], cwd=sdk_path, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    latest_tag = result.stdout.strip()
    result = subprocess.run(['git', 'checkout', latest_tag], cwd=sdk_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def vscode_config(project_path, sdk_path):
    (project_path / '.vscode').mkdir()

    open(project_path / '.vscode' / 'settings.json','w').write(textwrap.dedent(
        '''
        {
            "cmake.configureSettings": {
                "32BLIT_DIR": "{sdk_path}"
            },
            "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools"
        } 
        '''.replace('{sdk_path}', str(sdk_path))))

    open(project_path / '.vscode' / 'cmake-kits.json','w').write(textwrap.dedent(
        '''
        [
            {
                "name": "32blit",
                "toolchainFile": "{sdk_path}/32blit.toolchain"
            }
        ]
        '''.replace('{sdk_path}', str(sdk_path))))

@click.command('setup', help='Setup a project', cls=SetupCommand)
@click.option('--project-name', prompt=True)
@click.option('--author-name', prompt=True)
@click.option('--sdk-path', type=pathlib.Path, default=lambda: os.path.expanduser('~/32blit-sdk'), prompt='32Blit SDK path')
@click.option('--git/--no-git', prompt='Initialise a Git repository?', default=True)
@click.option('--vscode/--no-vscode', prompt='Create VS Code configuration?', default=True)
def setup_cli(project_name, author_name, sdk_path, git, vscode):
    if not (sdk_path / '32blit.toolchain').exists():
        click.confirm(f'32Blit SDK not found at "{sdk_path}", would you like to install it?', abort=True)
        install_sdk(sdk_path)

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

    if vscode:
        vscode_config(project_path, sdk_path)

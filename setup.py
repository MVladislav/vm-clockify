'''
    will setup the project, by install it local
    with needed dependencies
'''
import os
from subprocess import check_call

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

try:
    from dotenv import load_dotenv
    load_dotenv('.env_project')
except ImportError:
    import logging
    import sys

    source_to_install = 'python-dotenv'
    logging.log(logging.CRITICAL, f'Failed to Import {source_to_install}')
    logging.log(logging.INFO, f'Attempting to Install {source_to_install}')
    try:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', '-q', source_to_install])
        from dotenv import load_dotenv
        load_dotenv('.env_project')
        logging.log(logging.INFO, '[DONE]')
    except Exception:
        logging.log(logging.CRITICAL, '[FAIL]')

PROJECT_NAME: str = os.getenv('PROJECT_NAME', 'vm_clockify')
VERSION: str = os.getenv('VERSION', '0.0.2')
SCRIPT_INSTALL: str = os.getenv('VM_SCRIPT_INSTALL', 'no')


def main():
    PROJECT_NAME_SLUG = slugify(PROJECT_NAME)
    setup(
        cmdclass={
            'develop': PostDevelopCommand,
            'install': PostInstallCommand,
        },
        install_requires=read_requirements(),
        entry_points=f'''
            [console_scripts]
            {PROJECT_NAME_SLUG}=app.main:cli
        ''',
    )

# ------------------------------------------------------------------------------
#
# POST installer
#
# ------------------------------------------------------------------------------


class PostDevelopCommand(develop):
    '''
        Post-installation for development mode.
    '''

    def run(self):
        if isinstance(SCRIPT_INSTALL, str) and SCRIPT_INSTALL == 'yes':
            check_call(['/bin/bash', './scripts/setup-dev.sh'])
        develop.run(self)


class PostInstallCommand(install):
    '''
        Post-installation for installation mode.
    '''

    def run(self):
        if isinstance(SCRIPT_INSTALL, str) and SCRIPT_INSTALL == 'yes':
            check_call(['/bin/bash', './scripts/setup.sh'])
        install.run(self)

# ------------------------------------------------------------------------------
#
# TEXTs and requirements
#
# ------------------------------------------------------------------------------


def read_long_description():
    '''
        load the readme to add as long description
    '''
    with open('README.md', 'r', encoding='utf-8') as fh:
        long_description = fh.read()
    return long_description


def read_requirements():
    '''
        load and read the dependencies
        from the requirements.txt file
        and return them as a list
    '''
    with open('requirements.txt', 'r', encoding='utf-8') as req:
        requirements = req.read().split('\n')
    return requirements

# ------------------------------------------------------------------------------
#
# HELPER
#
# ------------------------------------------------------------------------------


def slugify(value, allow_unicode=False):
    import re
    import unicodedata

    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', value.lower())).strip('-_')

# ------------------------------------------------------------------------------
#
# SETUP
#
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    main()

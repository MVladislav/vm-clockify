'''
    will setup the project, by install it local
    with needed dependencies
'''
import os
from subprocess import check_call

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install

PROJECT_NAME: str = os.getenv('PROJECT_NAME', 'vm_clockify')
VERSION: str = os.getenv('VERSION', '0.0.2')

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
        check_call(['/bin/bash', './scripts/setup-dev.sh'])
        develop.run(self)


class PostInstallCommand(install):
    '''
        Post-installation for installation mode.
    '''

    def run(self):
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


PROJECT_NAME_SLUG = slugify(PROJECT_NAME)

setup(
    name=PROJECT_NAME,
    version=VERSION,
    license='GNU AGPLv3',
    description=PROJECT_NAME,
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    author='MVladislav',
    author_email='info@mvladislav.online',
    packages=find_packages(),
    data_files=[('', ['requirements.txt', 'scripts/setup.sh', 'scripts/setup-dev.sh'])],
    include_package_data=True,
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    install_requires=read_requirements(),
    python_requires='>=3.8',
    zip_safe=True,
    entry_points=f'''
        [console_scripts]
        {PROJECT_NAME_SLUG}=app.main:cli
    ''',
)

'''
    will setup the project, by install it local
    with needed dependencies
'''
from setuptools import setup


def main():
    setup(
        install_requires=read_requirements(),
        entry_points='''
            [console_scripts]
            vm-clockify=vm_clockify.main:cli
        ''',
    )

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
# SETUP
#
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    main()

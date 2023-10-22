"""Will setup the project, by install it local with needed dependencies."""
from setuptools import setup


def main() -> None:
    """Start install."""
    setup(
        install_requires=read_requirements(),
        entry_points="""
            [console_scripts]
            vm-clockify=vm_clockify.main:cli
        """,
    )


# ------------------------------------------------------------------------------
#
# TEXTs and requirements
#
# ------------------------------------------------------------------------------


def read_long_description() -> str:
    """Load the readme to add as long description."""
    with open("README.md", encoding="utf-8") as fh:
        long_description = fh.read()
    return long_description


def read_requirements() -> list[str]:
    """Read the requirements.txt file."""
    with open("requirements.txt", encoding="utf-8") as req:
        requirements = req.read().split("\n")
    return requirements


# ------------------------------------------------------------------------------
#
# SETUP
#
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    main()

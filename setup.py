from pathlib import Path
from setuptools import setup, find_packages

here = Path(__file__).absolute().parent
readme = here / 'README.md'
version = here / 'VERSION'

SETUP = {
    'name': "jujuna",
    'description': 'Continuous deployment, upgrade and testing for Juju.',
    'packages': find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    'version': version.read_text().strip(),
    'author': "Matus Kosut",
    'author_email': "matuskosut@gmail.com",
    'maintainer': 'HUNT Data Center',
    'maintainer_email': 'cloud@hunt.ntnu.no',
    'url': "https://github.com/huntdatacenter/jujuna",
    'long_description': readme.read_text().strip(),
    'long_description_content_type': 'text/markdown',
    'entry_points': {
        'console_scripts': [
            # Script invokation:
            'jujuna = jujuna.__main__:main',
        ]
    },
    'license': 'Apache 2',
    'classifiers': [
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console"
    ],
    'install_requires': [
        'pyyaml',
        'async-timeout==2.0.1',
        'juju>=0.10.2',
        'argcomplete',
        'theblues>=0.5.1'
    ],
}


if __name__ == '__main__':
    setup(**SETUP)

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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console"
    ],
    'install_requires': [
        'async-timeout>=2.0.1,<4.0.0',
        'argcomplete>=1.10.0,<2.0.0',
        'theblues>=0.5.2,<1.0'
    ],
    'extras_require': {
        ":python_version>'3.5.2'": [
            'juju==2.9.7',
            'pyyaml>=5.1.2,<=6.0.0',
        ],
        ":python_version<='3.5.2'": [
            'juju<1.0.0,>=0.11.7',
            'pyyaml<=4.2,>=3.0',
        ]
    }
}


if __name__ == '__main__':
    setup(**SETUP)

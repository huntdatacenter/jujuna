from pathlib import Path
from setuptools import setup, find_packages

here = Path(__file__).absolute().parent
readme = here / 'README.md'
changelog = here / 'CHANGELOG'
reqs_file = here / 'requirements.txt'

with open(reqs_file) as f:
    reqs = [line for line in f.read().splitlines()
            if not line.startswith('--')]
version = here / 'VERSION'

SETUP = {
    'name': "jujuna",
    'packages': find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    'version': version.read_text().strip(),
    'author': "Matus Kosut",
    'author_email': "matuskosut@gmail.com",
    'maintainer': 'HUNT Data Center',
    'maintainer_email': 'cloud@hunt.ntnu.no',
    'url': "https://github.com/huntdatacenter/jujuna",
    'long_description': open('README.md').read(),
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
    'install_requires': reqs,
}


if __name__ == '__main__':
    setup(**SETUP)

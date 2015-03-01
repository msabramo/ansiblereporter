
import os
import glob

from setuptools import setup, find_packages

VERSION='1.4'

setup(
    name = 'ansiblereporter',
    keywords = 'system management ansible automation reporting',
    description = 'Scripts for ansible to report host output data',
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    version = VERSION,
    url = 'http://tuohela.net/packages/ansiblereporter',
    license = 'PSF',
    packages = find_packages(),
    scripts = glob.glob('bin/*'),
    install_requires = (
        'ansible>=1.8.2',
        'boto',
        'seine>=2.5.0',
        'systematic>=4.2.3',
        'termcolor',
    ),
)


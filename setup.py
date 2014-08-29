
import os
import glob

from setuptools import setup, find_packages

VERSION='1.0'
README = open(os.path.join(os.path.dirname(__file__),'README.md'),'r').read()

setup(
    name = 'ansiblereporter',
    keywords = 'system management ansible automation reporting',
    description = 'Scripts for ansible to report host output data',
    author = 'Ilkka Tuohela',
    author_email = 'hile@iki.fi',
    long_description = README,
    version = VERSION,
    url = 'http://tuohela.net/packages/ansiblereporter',
    license = 'PSF',
    zip_safe = False,
    packages = find_packages(),
    scripts = glob.glob('bin/*'),
    install_requires = (
        'systematic>=4.0.7',
    ),
)


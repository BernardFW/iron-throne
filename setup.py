# coding: utf-8
from __future__ import unicode_literals

import os
import codecs
from setuptools import setup, find_packages

try:
    from pip.req import parse_requirements
    from pip.download import PipSession
except ImportError:
    from pip._internal.req import parse_requirements
    from pip._internal.download import PipSession

rf = codecs.open(os.path.join(os.path.dirname(__file__), 'README.txt'), 'r')
with rf as readme:
    README = readme.read()

requirements = parse_requirements(
    os.path.join(os.path.dirname(__file__), 'requirements_as_lib.txt'),
    session=PipSession()
)

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='iron_throne',
    version='0.0.1',
    packages=find_packages('src'),
    package_dir={
        '': 'src',
    },
    scripts=[],
    include_package_data=True,
    license='Apache License 2.0',
    description='A claim-based NLU engine',
    long_description=README,
    url='https://github.com/BernardFW/iron-throne',
    author='Rémy Sanchez',
    author_email='remy.sanchez@hyperthese.net',
    install_requires=[str(x.req) for x in requirements],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 3 - Alpha',
    ]
)

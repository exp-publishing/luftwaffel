#!/usr/bin/env python

from setuptools import setup
import sys

if sys.version_info < (3, 4):
    raise ImportError('Requires Python 3.4 or later.')

with open('requirements.txt', 'r') as f:
    requires = []
    depends = []
    for line in f.readlines():
        if 'git+' in line:
            depends.append(line)
        else:
            requires.append(line)

setup(
    name='expp-irc',
    version='0.0.1',

    description='ExP Publishing IRC Plugins',
    long_description=(
        'ExP Publishing plugins for the CloudBot IRC Bot.'
    ),

    url='https://github.com/exp-publishing/cloudbot-plugins',
    license='GPLv3',

    include_package_data=True,
    install_requires=requires,
    dependency_links=depends,

    packages=[
        'expp.cloudbot.plugins',
        'expp.cloudbot.test',
    ],
    package_dir={
        'expp.cloudbot.plugins': 'plugins',
        'expp.cloudbot.test': 'test',
    },
)

#!/usr/bin/env python

from setuptools import setup
import sys

if sys.version_info < (3, 4):
    raise ImportError('Requires Python 3.4 or later.')

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
    dependency_links=[
        'git+https://github.com/jaelsasser/CloudBot.git@setuptools',
    ],

    packages=[
        'expp.cloudbot.plugins',
        'expp.cloudbot.test',
    ],
    package_dir={
        'expp.cloudbot.plugins': 'plugins',
        'expp.cloudbot.test': 'test',
    },
)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           mercurial-hg
# Program Description:    A wrapper for select Mercurial functionality.
#
# Filename:               setup.py
# Purpose:                Configuration for installation with setuptools.
#
# Copyright (C) 2016, 2017 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
'''
Configuration for installation with setuptools.
'''

from setuptools import find_packages, setup
from metadata import HUG_METADATA
import versioneer


with open('README.rst', 'r') as file_pointer:
    _LONG_DESCRIPTION = file_pointer.read()

setup(
    name=HUG_METADATA['name'],
    version=versioneer.get_version(),
    packages=find_packages(),
    include_package_data=True,

    install_requires=['mercurial>3,<4'],
    tests_require=['pytest>2.7,<3'],
    cmdclass=versioneer.get_cmdclass(),

    # metadata for upload to PyPI
    author=HUG_METADATA['author'],
    author_email=HUG_METADATA['author_email'],
    description=HUG_METADATA['description'],
    long_description=_LONG_DESCRIPTION,
    license=HUG_METADATA['license'],
    keywords='mercurial, vcs, version control, wrapper',
    url=HUG_METADATA['url'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Operating System :: OS Independent',
    ],
)

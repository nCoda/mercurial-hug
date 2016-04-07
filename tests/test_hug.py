#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           mercurial-hg
# Program Description:    A wrapper for select Mercurial functionality.
#
# Filename:               tests/test_hug.py
# Purpose:                Tests for "hug.py."
#
# Copyright (C) 2016 Christopher Antila
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
Tests for "hug.py."
'''

import os.path
import shutil
import subprocess
import tempfile

from mercurial import error
import pytest

from hug import hug


@pytest.fixture()
def temp_dir(request):
    "This PyTest fixture provides and cleans up a temporary directory."
    temp_dir = tempfile.mkdtemp()
    def clean_up_temp_dir():
        "Delete the temporary directory."
        shutil.rmtree(temp_dir)
    request.addfinalizer(clean_up_temp_dir)
    return temp_dir


@pytest.fixture()
def repo(temp_dir):
    "This PyTest fixture creates a Hug instance in a temporary directory."
    return hug.Hug(temp_dir)


class TestInit(object):
    '''
    Tests for Hug.__init__().
    '''

    def test_repo_dir_not_exist(self):
        '''
        The provided repo_dir doesn't exist.
        '''
        with pytest.raises(error.RepoError) as exc:
            hug.Hug('eeeeeeeeeeeeeeeeeee')
        assert exc.value.args[0] == hug._REPO_DIR_NOT_EXIST

    def test_repo_dir_is_file(self):
        '''
        The provided repo_dir is a file (not a directory).
        '''
        with pytest.raises(error.RepoError) as exc:
            hug.Hug('/usr/bin/env')
        assert exc.value.args[0] == hug._REPO_DIR_NOT_EXIST

    def test_repo_exists_and_works(self, temp_dir):
        '''
        When ``hg init`` was run previously and the repository initialized successfully.
        '''
        with open(os.path.join(temp_dir, 'fuzz'), 'w') as temp_file:
            temp_file.write('some file contents')
        subprocess.check_call(['hg', 'init'], cwd=temp_dir)
        subprocess.check_call(['hg', 'add', 'fuzz'], cwd=temp_dir)
        subprocess.check_call(['hg', 'commit', '-m', '"whatever"'], cwd=temp_dir)

        repo = hug.Hug(temp_dir)

        assert repo._repo is not None

    def test_repo_dir_empty(self, temp_dir):
        '''
        When the repository directory is totally empty, ``hg init`` will be run.
        '''
        repo = hug.Hug(temp_dir)
        assert os.path.exists(os.path.join(temp_dir, '.hg'))

    def test_repo_dir_not_empty_safe(self, temp_dir):
        '''
        When the directory has files in it, but isn't a Hg repo, and safe=True
        '''
        with open(os.path.join(temp_dir, 'fuzz'), 'w') as temp_file:
            temp_file.write('some file contents')

        with pytest.raises(error.RepoError) as exc:
            repo = hug.Hug(temp_dir, safe=True)

        assert exc.value.args[0] == hug._CANNOT_UNSAFE_INIT

    def test_repo_dir_not_empty_unsafe(self, temp_dir):
        '''
        When the directory has files in it, but isn't a Hg repo, and safe=False
        '''
        with open(os.path.join(temp_dir, 'fuzz'), 'w') as temp_file:
            temp_file.write('some file contents')

        repo = hug.Hug(temp_dir, safe=False)

        assert os.path.exists(os.path.join(temp_dir, '.hg'))


class TestRepoDirProperty(object):
    '''
    Tests for Hug.repo_dir
    '''

    def test_read_works(self, repo):
        '''
        The ``repo_dir`` property can be read.
        '''
        assert repo.repo_dir is repo._repo_dir

    def test_write_doesnt_work(self, repo):
        '''
        The ``repo_dir`` property cannot be changed.
        '''
        with pytest.raises(AttributeError):
            repo.repo_dir = 'bork'

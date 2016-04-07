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

import os
import os.path
import shutil
import subprocess
import tempfile

try:
    from unittest import mock
except ImportError:
    import mock

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
    repo = hug.Hug(temp_dir)
    repo.username = 'this is set to prevent a crash'
    return repo


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


class TestStringRepr(object):
    def test_string(self, repo):
        assert repo.__str__() == hug._STR.format(repo.repo_dir)

    def test_repr(self, repo):
        assert repo.__repr__() == hug._REPR.format(repo.repo_dir)


class TestAdd(object):
    '''
    Tests for Hug.add().
    '''

    def test_add_no_files(self, repo):
        '''
        Call add() with an empty list; it shouldn't do anything.
        '''
        with open(os.path.join(repo.repo_dir, 'boring'), 'w') as temp_file:
            temp_file.write('some file contents')

        repo.add([])

        status = repo._repo.status()
        assert status.added == []
        # NB: I don't know why this commented assertion fails... ?
        # assert status.unknown == ['boring']
        status = subprocess.check_output(['hg', 'status'], cwd=repo.repo_dir)
        assert '? boring' in status

    def test_add_one_file_1(self, repo):
        '''
        Call add() with a single file (relative pathname) that isn't already added; the file should
        be added.
        '''
        with open(os.path.join(repo.repo_dir, 'boring'), 'w') as temp_file:
            temp_file.write('some file contents')

        repo.add(['boring'])

        status = repo._repo.status()
        assert status.added == ['boring']

    def test_add_one_file_2(self, repo):
        '''
        Call add() with a single file (absolute pathname) that isn't already added; the file should
        be added.
        '''
        abs_path = os.path.abspath(os.path.join(repo.repo_dir, 'boring'))
        with open(abs_path, 'w') as temp_file:
            temp_file.write('some file contents')

        repo.add([abs_path])

        status = repo._repo.status()
        assert status.added == ['boring']

    def test_add_one_file_3(self, repo):
        '''
        Call add() with a single file (relative pathname, in a subdirectory) that isn't already
        added; the file should be added.
        '''
        os.mkdir(os.path.join(repo.repo_dir, 'lol'))
        rel_path = os.path.join('lol', 'boring')
        abs_path = os.path.abspath(os.path.join(repo.repo_dir, rel_path))
        with open(abs_path, 'w') as temp_file:
            temp_file.write('some file contents')

        repo.add([rel_path])

        status = repo._repo.status()
        assert status.added == ['lol/boring']

    def test_add_three_files(self, repo):
        '''
        Call add() with three files that aren't already added; the files should be added.
        '''
        filenames = ['aoring', 'boring', 'coring']
        for filename in filenames:
            with open(os.path.join(repo.repo_dir, filename), 'w') as temp_file:
                temp_file.write('some file contents')

        repo.add(filenames)

        status = repo._repo.status()
        assert len(status.added) == len(filenames)
        for filename in filenames:
            assert filename in status.added

    def test_add_already_added(self, repo):
        '''
        Call add() with files that were already added; it shouldn't do anything.
        '''
        with open(os.path.join(repo.repo_dir, 'boring'), 'w') as temp_file:
            temp_file.write('some file contents')
        subprocess.check_call(['hg', 'add', 'boring'], cwd=repo.repo_dir)
        # pre-check: the file is already added
        status = repo._repo.status()
        assert status.added == ['boring']

        # function under test
        repo.add(['boring'])

        # post-check: the file is still added
        status = repo._repo.status()
        assert status.added == ['boring']

    def test_not_in_repo_dir(self, repo):
        '''
        Call add() with a file that's not in the repo_dir; it should raise RuntimeError.
        '''
        with pytest.raises(RuntimeError) as exc:
            repo.add(['/bin/bash'])
        assert exc.value.args[0] == hug._FILE_NOT_IN_REPO_DIR.format('/bin/bash')


class TestCommit(object):
    '''
    Tests for Hug.commit()
    '''

    def test_no_changes(self, repo):
        '''
        When there are no changes to commit, raise RuntimeError.
        '''
        with pytest.raises(RuntimeError) as exc:
            repo.commit('a message')
        assert exc.value.args[0] == hug._NOTHING_TO_COMMIT

    def test_give_message(self, repo):
        '''
        When there are changes to commit, and a message is given.
        Also check that the username is used.
        '''
        with open(os.path.join(repo.repo_dir, 'boring'), 'w') as temp_file:
            temp_file.write('some file contents')
        subprocess.check_call(['hg', 'add', 'boring'], cwd=repo.repo_dir)
        repo.username = 'HUSH'

        repo.commit('a message')

        assert repo._repo[0].description() == 'a message'
        assert repo._repo[0].user() == 'HUSH'

    def test_no_message(self, repo):
        '''
        When there are changes to commit, but no message is given.
        '''
        with open(os.path.join(repo.repo_dir, 'boring'), 'w') as temp_file:
            temp_file.write('some file contents')
        subprocess.check_call(['hg', 'add', 'boring'], cwd=repo.repo_dir)

        repo.commit()

        assert repo._repo[0].description() == hug._DEFAULT_COMMIT_MESSAGE


def test_username_property(repo):
    '''
    Test the username property.
    '''
    ui_mock = mock.Mock()
    ui_mock.username = mock.Mock(side_effect=error.Abort)
    repo._ui = ui_mock

    # test the mercurial-hug fallback username
    ui_mock.username = mock.Mock(side_effect=error.Abort)
    repo._username = None
    assert repo.username == hug._DEFAULT_USERNAME

    # test the Mercurial fallback
    ui_mock.username = mock.Mock(return_value='A-Lin')
    assert repo.username == 'A-Lin'

    # test setting a mercurial-hug override username
    repo.username = '张靓颖'
    assert repo.username == '张靓颖'

    # test deleting the override
    del repo.username
    assert repo.username == 'A-Lin'

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           mercurial-hg
# Program Description:    A wrapper for select Mercurial functionality.
#
# Filename:               hug.py
# Purpose:                Wrapper library for Mercurial.
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
Wrapper library for Mercurial.
'''

import os
import os.path
from mercurial import error, ui, hg, commands


_REPO_DIR_NOT_EXIST = 'Repository path does not exist or is a file'
_CANNOT_UNSAFE_INIT = 'Cannot safely initialize repository directory'
_FILE_NOT_IN_REPO_DIR = 'Cannot add file outside repository: {0}'
_NOTHING_TO_COMMIT = 'There are no changes to commit'
_DEFAULT_COMMIT_MESSAGE = '(empty commit message)'

_STR = '<Hug repository for "{0}">'
_REPR = 'Hug("{0}")'

class Hug(object):
    '''
    :class:`Hug` represents a Mercurial repository.
    '''

    def __init__(self, repo_dir, safe=False):
        '''
        Create a :class:`Hug` instance, initializing the ``repo_dir`` repository if necessary.

        :param str repo_dir: Pathname to the repository directory.
        :para bool safe: Whether to insist on safe repository creation (see below). Default ``False``.
        :raises: :exc:`mercurial.error.RepoError` if ``safe`` is ``True`` but we cannot be safe.
        :raises: :exc:`~mercurial.error.RepoError` if ``repo_dir`` is not a directory or does not
            exist.

        If the ``safe`` argument is ``True``, we will raise a :exc:`RepoError` unless either the
        repository directory is already initialized as a Mercurial repository, or the directory is
        completely empty.
        '''
        super(Hug, self).__init__()
        self._ui = ui.ui()
        self._repo = None

        repo_dir = os.path.abspath(repo_dir)
        self._repo_dir = repo_dir

        if not (os.path.exists(repo_dir) and os.path.isdir(repo_dir)):
            raise error.RepoError(_REPO_DIR_NOT_EXIST)

        try:
            self._repo = hg.repository(self._ui, repo_dir)
        except error.RepoError:
            if safe and len(os.listdir(repo_dir)) > 0:
                raise error.RepoError(_CANNOT_UNSAFE_INIT)
            commands.init(self._ui, repo_dir)
            self._repo = hg.repository(self._ui, repo_dir)

    def __str__(self):
        "Does the string thing."
        return _STR.format(self.repo_dir)

    def __repr__(self):
        "Does the repr thing."
        return _REPR.format(self.repo_dir)

    @property
    def repo_dir(self):
        '''
        Return the absolute pathname to this repository's directory.
        '''
        return self._repo_dir

    def add(self, pathnames):
        '''
        Given a list of pathnames, ensure they are all tracked in the repository.

        :param pathnames: Pathnames that may or may not be tracked in the repository.
        :type pathnames: list of string
        :raises: :exc:`RuntimeError` if any of the files in ``pathnames`` are not in the repository
            directory.

        If any of the files in ``pathnames`` are not in the repository's directory, no files are
        added and a :exc:`RuntimeError` is raised.

        Files that are already tracked are silently ignored.
        '''
        repo_dir = self.repo_dir

        # these paths are assumed to be in the repository directory, but "pathnames" may not be
        unknowns = self._repo.status(unknown=True).unknown

        # make sure the pathnames-to-add are absolute
        abs_pathnames = []
        for each_path in pathnames:
            if os.path.isabs(each_path):
                abs_pathnames.append(each_path)
            else:
                abs_pathnames.append(os.path.abspath(os.path.join(repo_dir, each_path)))

        for each_path in abs_pathnames:
            if not each_path.startswith(repo_dir):
                raise RuntimeError(_FILE_NOT_IN_REPO_DIR.format(each_path))

        for each_path in abs_pathnames:
            relative_to_repo = each_path.replace(repo_dir, '')[1:]  # replace() leaves a leading /
            if relative_to_repo in unknowns:
                # only call add() for untracked files
                commands.add(self._ui, self._repo, each_path)

    def commit(self, message=None):
        '''
        Make a new commit, optionally with the supplied commit message.

        :param message: A commit message to use.
        :type message: str
        :raises: :exc:`RuntimeError` if there are no added, deleted, modified, or removed files to
            commit. We could silently ignore this, but "hg commit" returns a 1 status code if there
            is nothing to commit, so this is more consistent.

        If no commit message is supplied, a default is used
        '''
        # don't try to commit if nothing has changed
        stat = self._repo.status()
        if 0 == (len(stat.added) + len(stat.deleted) + len(stat.modified) + len(stat.removed)):
            raise RuntimeError(_NOTHING_TO_COMMIT)

        if message is None:
            message = _DEFAULT_COMMIT_MESSAGE

        commands.commit(self._ui, self._repo, message=message)

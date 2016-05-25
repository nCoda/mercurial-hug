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


# translatable strings
# error messages
_REPO_DIR_NOT_EXIST = 'Repository path does not exist or is a file'
_CANNOT_UNSAFE_INIT = 'Cannot safely initialize repository directory'
_FILE_NOT_IN_REPO_DIR = 'Cannot add file outside repository: {0}'
_NOTHING_TO_COMMIT = 'There are no changes to commit'
_MISSING_SUMMARY_FIELDS = 'Expected at least "parent" and "message"; repository may be corrupted.'
_UNKNOWN_REVISION = 'Unknown revision; could not run "update."'
# defaults
_DEFAULT_COMMIT_MESSAGE = '(empty commit message)'
_DEFAULT_USERNAME = '(unknown user)'
# templates for magic methods
_STR = '<Hug repository for "{0}">'
_REPR = "Hug('{0}')"


class Hug(object):
    '''
    :class:`Hug` represents a Mercurial repository.

    Because :meth:`commit` requires a username, ``mercurial-hug`` provides a default if nothing is
    available. The username may come from one of three places:

    #. The value provided to the :attr:`username` property at runtime. If this is not available,
    #. The value Mercurial would use if called on the commandline. If this is not available,
    #. A default provided by ``mercurial-hug``. At the moment, the default in English is
       "(unknown user)".

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
        self._username = None

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

    def commit(self, message=None, date=None):
        '''
        Make a new commit, optionally with the supplied commit message and date.

        :param str message: A commit message to use.
        :param str date: A date to use. This should be the same format as used in ``hg log``, like
            ``'Tue Apr 19 15:00:00 2016 -0500'``.
        :raises: :exc:`RuntimeError` if there are no added, deleted, modified, or removed files to
            commit. We could silently ignore this, but "hg commit" returns a 1 status code if there
            is nothing to commit, so this is more consistent.

        If no commit message is supplied, a default is used.

        Use the :attr:`username` property to set a username for the commit, or a default is used.
        '''
        # don't try to commit if nothing has changed
        stat = self._repo.status()
        if 0 == (len(stat.added) + len(stat.deleted) + len(stat.modified) + len(stat.removed)):
            raise RuntimeError(_NOTHING_TO_COMMIT)

        if message is None:
            message = _DEFAULT_COMMIT_MESSAGE

        commands.commit(self._ui, self._repo, message=message, user=self.username, date=date)

    def _get_username(self):
        "Return the username in order of preference."
        if self._username:
            return self._username
        else:
            try:
                return self._ui.username()
            except error.Abort:
                return _DEFAULT_USERNAME

    def _set_username(self, username):
        "Set a Hug-specific username."
        self._username = username

    def _del_username(self):
        "Unset a Hug-specific username."
        self._username = None

    username = property(_get_username, _set_username, _del_username,
        '''
        Username for commits.

        If you set the username, it will be used for every commit until you ``del`` to unset the
        custom username. If you delete or do not set a username, ``mercurial-hug`` uses the same
        username that Mercurial would use on the commandline. If no username is set and Mercurial
        does not have a username set either, a default stand-in is used.
        ''')

    def summary(self):
        '''
        Get a summary of the repository state.

        :returns: A dictionary summarizing the repository state; see below.
        :rtype: dict
        :raises: :exc:`RuntimeError` if at least the "parent" and "message" field are not available,
            which indicates a serious problem with the repository.

        If running ``hg summary`` on the commandline returns this:

        ..
            parent: 41:d16397e87778
             Change @xml:id of <section> to valid Lychee-MEI
            branch: default
            commit: (clean)
            update: 29 new changesets (update)

        Then :meth:`summary` will return this dictionary:

        ..
            {
                'parent': '41:d16397e87778',
                'message': 'Change @xml:id of <section> to valid Lychee-MEI',
                'branch': 'default',
                'commit': '(clean)',
                'update': '29 new changesets (update)',
            }

        '''
        self._ui.pushbuffer()
        commands.summary(self._ui, self._repo)
        summary = self._ui.popbuffer()

        post = {}
        summary = summary.split('\n')
        if len(summary) < 2:
            raise RuntimeError(_MISSING_SUMMARY_FIELDS)

        post['parent'] = summary[0][8:].strip()
        post['message'] = summary[1].strip()

        for field in summary[2:]:
            if field:
                split = field.split(': ')
                post[split[0]] = ''.join(split[1:])

        return post

    def update(self, rev=None, clean=False, check=False):
        '''
        Update working directory (or switch revisions).

        :param str rev: The changeset to update to (either by revision number or hash).
        :param bool clean: If ``True``, any changes in the working directory are lost.
        :param bool check: If ``True``, any changes in the working directory cause the update to fail.
        :raises: :exc:`RuntimeError` when ``rev`` doesn't refer to a valid revision.

        (From the Mercurial documentation):

        Update the repository's working directory to the specified changeset. If no changeset is
        specified, update to the tip of the current named branch and move the current bookmark.

        Update sets the working directory's parent revision to the specified changeset.

        If the changeset is not a descendant or ancestor of the working directory's parent, the
        update is aborted. With the ``check`` option, the working directory is checked for
        uncommitted changes; if none are found, the working directory is updated to the specified
        changeset.
        '''
        try:
            commands.update(self._ui, self._repo, rev=rev, clean=clean, check=check)
        except error.RepoLookupError:
            raise RuntimeError(_UNKNOWN_REVISION)

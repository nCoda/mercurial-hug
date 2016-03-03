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

from os import path
from mercurial import error, ui, hg, commands


class Hug(object):
    '''
    :class:`Hug` represents a Mercurial repository.
    '''

    def __init__(self, repodir, *args, **kwargs):
        '''
        Create a :class:`Hug` instance, initializing the ``repodir`` repository if necessary.
        '''
        super(Hug, self).__init__(*args, **kwargs)
        self._ui = ui.ui()
        self._repo = None

        repodir = path.abspath(repodir)

        try:
            self._repo = hg.repository(self._ui, repodir)
        except error.RepoError:
            commands.init(self._ui, repodir)
            self._repo = hg.repository(self._ui, repodir)

    def add(self, pathnames):
        '''
        Given a list of pathnames, ensure they are all tracked in the repository.

        :param pathnames: Pathnames that may or may not be tracked in the repository.
        :type pathnames: list of string
        '''
        # these paths are assumed to be in the repository directory, but "pathnames" may not be
        unknowns = self._repo.status(unknown=True).unknown
        for each_path in pathnames:
            if path.split(each_path)[1] in unknowns:
                commands.add(self._ui, self._repo, path.abspath(each_path))

    def commit(self, message=None):
        '''
        Make a new commit, optionally with the supplied commit message.

        :param message: A commit message to use.
        :type message: str

        If no commit message is supplied, an empty string is used.
        '''
        # don't try to commit if nothing has changed
        stat = self._repo.status()
        if 0 == (len(stat.added) + len(stat.deleted) + len(stat.modified) + len(stat.removed)):
            return

        if message is None:
            message = ''

        commands.commit(self._ui, self._repo, message=message)

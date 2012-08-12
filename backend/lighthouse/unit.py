# -*- coding: utf-8 -*-
#
# Lighthouse - object modelling a translation unit.
# Copyright (C) 2009  Joseph Birr-Pixton
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import lighthouse.types as types

class Unit(object):
    """
    A single translation unit, comprising the original unpreprocessed source,
    the set of aggregate types used and the functions defined.
    """
    def __init__(self):
        self._raw_source = None
        self._filename = None
        self._language = None
        self._types = {}
        self._functions = []

    def __repr__(self):
        return '<%s translation-unit file %r>' % \
                (self.lang, self.filename)
    
    def finalise(self):
        for tid, t in self._types.iteritems():
            self._types[tid] = types.resolve_aggregates(t, self._types)

        for f in self._functions:
            f.resolve_aggregates(self._types)
            f.resolve_temporary_names()

    def get_source(self):
        assert self._raw_source is not None
        return self._raw_source
    def set_source(self, src):
        self._raw_source = src
    source = property(get_source, set_source)
    
    def get_lang(self):
        assert self._language is not None
        return self._language
    def set_lang(self, lang):
        assert lang in ('C', 'C++')
        self._language = lang
    lang = property(get_lang, set_lang)

    def get_filename(self):
        assert self._filename is not None
        return self._filename
    def set_filename(self, fn):
        self._filename = fn
    filename = property(get_filename, set_filename)

    def get_types(self):
        return self._types
    def set_types(self, t):
        self._types = t
    types = property(get_types, set_types)
    
    def get_functions(self):
        return self._functions
    def set_functions(self, f):
        self._functions = f
    functions = property(get_functions, set_functions)

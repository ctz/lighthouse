# -*- coding: utf-8 -*-
#
# Lighthouse - analysis core.
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

import os.path
import sys

import lighthouse.statements as statements

g_analysers = []

class AnalysisBase(object):
    """
    Analysis base class.  Subclasses are registered with the analysis machinery.
    """
    
    def __init__(self):
        """
        Registers with analysis machinery.
        """
        g_analysers.append(self)
        self.unit = None # current unit
    
    def check_unit(self, unit):
        """
        Entrypoint from analysis machinery.  'unit' is a Unit instance to be analysed.
        """
        self.unit = unit
    
    def warn(self, message, location = dict(), cls = 'Warning'):
        f = sys.stderr
        print >>f, 'lighthouse:', cls + ':', message
        
        for label, stmt in location.iteritems():
            if stmt and stmt.location:
                print >>f, '  ', label, 'at:', stmt.location
                print >>f, stmt.location.highlight(self.unit.source, label)
            print >>f
        
    def error(self, message, location = dict()):
        self.warn(message, location = location, cls = 'Error')
        raise StopAnalysis

class StopAnalysis(Exception):
    pass

class FunctionCallAnalyser(AnalysisBase):
    @staticmethod
    def Handler(name = None):
        def apply(fn):
            fn.handler = True
            if name:
                fn.handler_for = name
            else:
                fn.handler_for = fn.__name__
            return fn
        return apply

    def __init__(self):
        AnalysisBase.__init__(self)
        self.handlers = {}
        
    def handle(self, unit, stmt):
        called = stmt.fnexpr.to_c()
        
        if called in self.handlers:
            try:
                self.handlers[called](stmt, stmt.lhs, stmt.args)
            except StopAnalysis:
                pass
            except Exception:
                self.warn("Python exception raised.", location = {'when processing statement': stmt})
                raise

    def _enum_handlers(self):
        """
        Fill the mapping of handlers.
        """
        for x in dir(self):
            y = getattr(self, x)
            if getattr(y, 'handler', False) == True and hasattr(y, 'handler_for'):
                self.handlers[y.handler_for] = y

    def check_unit(self, unit):
        AnalysisBase.check_unit(self, unit)
        
        self._enum_handlers()
    
        for fn in unit.functions:
            for block in fn.blocks_in_natural_order():
                for stmt in block.statements:
                    if isinstance(stmt, statements.Call):
                        self.handle(unit, stmt)

def _load_from(where):
    g = dict()
    
    if os.path.isfile(where):
        # add the target to path so localised includes work
        oldpath = list(sys.path)
        basedir = os.path.dirname(where)
        sys.path = [basedir] + sys.path
        
        try:
            execfile(where, g)
        finally:
            sys.path = oldpath
        
    return g.values()

def _load_site_analysers():
    here = os.path.realpath(os.path.dirname(os.path.realpath(sys.argv[0])))
    _load_from(os.path.join(here, 'analysers/checkers.py'))

def _load_user_analysers():
    _load_from(os.path.expanduser('~/.lh/checkers.py'))

def _enumerate_analysers():
    global g_analysers
    g_analysers = []
    
    _load_user_analysers()
    _load_site_analysers()
    
    return g_analysers

def analyse(unit):
    for a in _enumerate_analysers():
        if isinstance(a, AnalysisBase):
            try:
                a.check_unit(unit)
            except StopAnalysis:
                pass
        else:
            pass # ignore unsuitable things
    return 0

# -*- coding: utf-8 -*-
#
# Lighthouse - object modelling a single basic block including the cfg.
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

import lighthouse.statements as statements

class Block(object):
    def __init__(self):
        self.id = 0
        self.statements = []
        self.next = []

    def to_c(self):
        out = ['bb%d:' % self.id]
      
        for s in self.statements:
            out += [ '  ' + s.to_c() ]

        for n in self.next:
            out += [ '  goto bb%d' % n ]

        return '\n'.join(out)
    
    def get_edges(self):
        r = self.next[:]
        for s in self.statements:
            r.extend(s.get_edges())
        return r
        
    def statements_by_line(self):
        """
        Generates location, [ stmt, stmt, ...] pairs where
        statements are consecutive and associated with the same
        line.
        """
        ourloc = None
        out = []
        for stmt in self.statements:
            if ourloc is None:
                ourloc = stmt.location
            if stmt.location is None or ourloc is None or stmt.location.line == ourloc.line:
                out.append(stmt)
            else:
                hereloc, hereout = ourloc, out
                ourloc, out = stmt.location, [stmt]
                yield hereloc, hereout
        if len(out):
            yield ourloc, out
    
    @staticmethod
    def from_xml(e):
        b = Block()
        assert e.tag == 'block'
        b.id = int(e.get('id'))
        for s in e.getchildren():
            if s.tag == 'next':
                b.next += [ int(s.get('id')) ]
            else:
                ss = statements.statement_from_xml(s)
                if ss:
                    b.statements.append(ss)
        return b

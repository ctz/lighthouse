# -*- coding: utf-8 -*-
#
# Lighthouse - object modelling a single defined function.
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
import lighthouse.decl as decl
from lighthouse.misc import descend_one, to_c, Location
from lighthouse.bb import Block

class Bounds:
    def __init__(self, decl, lo, hi):
        self.decl, self.lo, self.hi = decl, lo, hi
    def min(self):
        return min(self.decl, self.lo)
    def diff(self):
        return self.hi - self.min() + 1

class Function(object):
    def __init__(self):
        self.name = None
        self.location = None
        self.body_bounds = Bounds(None, 0, 0)
        self.return_type = None
        self.argument_decls = []
        self.entrypoint = None
        self.local_decls = {}
        self.blocks = {}
        self.externals = {}

    def fndecl_to_c(self):
        return '%s %s(%s)' % \
            ( self.return_type.to_c(), 
              self.name,
              ', '.join([x.to_c() for x in self.argument_decls]) )

    def locals_to_c(self):
        return '\n'.join([x.to_c() + ';' for x in self.local_decls.values()])

    def blocks_to_c(self):
        return '\n\n'.join([x.to_c() for x in self.blocks.values()])

    def to_c(self):
        return '%s\n{\n%s\ngoto bb%d;\n%s' % \
            ( self.fndecl_to_c(),
              self.locals_to_c(),
              self.entrypoint,
              self.blocks_to_c() )

    def for_every_statement(self, call):
        for block in self.blocks.values():
            for stmt in block.statements[:]:
                if call(stmt):
                    block.statements.remove(stmt)
    
    def collect_aggregate_decls(self, types):
        o = []
        for t in types.values():
            o += t.collect_interior_decls()
        return dict((d.binding.id, d) for d in o)

    def resolve_aggregates(self, types):
        for l in self.local_decls.values():
            l.resolve_aggregates(types)
        for l in self.argument_decls:
            l.resolve_aggregates(types)
        for l in self.externals.values():
            l.resolve_aggregates(types)
        aggregate_decls = self.collect_aggregate_decls(types)
        self.for_every_statement(lambda x: x.attach_decls(aggregate_decls))
        self.for_every_statement(lambda x: x.resolve_aggregates(aggregate_decls))

    def resolve_temporary_names(self):
        args = dict((x.binding.id, x) for x in self.argument_decls)
        self.for_every_statement(lambda x: x.attach_decls(args))
        self.for_every_statement(lambda x: x.attach_decls(self.local_decls))
        self.for_every_statement(lambda x: x.attach_decls(self.externals))
        self.for_every_statement(lambda x: x.resolve_temporary_names())
    
    def cyclomatic_complexity(self):
        e = self.count_edges()
        n = len(self.blocks)
        return e - n + 2
    
    def count_edges(self):
        r = 0
        for block in self.blocks.values():
            r += len(block.get_edges())
        return r
    
    def count_blocks(self):
        return len(self.blocks)
    
    def count_expressions(self):
        return sum([len(bb.statements) for bb in self.blocks.values()])
    
    def blocks_in_natural_order(self):
        """
        Returns a list of blocks in 'natural' order, ie
        the order they are likely to be visited during execution.
        """
        out = []
        worklist = []
        visited = []
        
        def add(edge):
            bb = self.blocks[edge]
            if bb not in visited:
                visited.append(bb)
            else:
                return
            if bb not in out:
                out.append(bb)
            if bb not in worklist:
                worklist.append(bb)
        
        # start at the start.
        add(self.entrypoint)
        
        while len(worklist):
            bb = worklist.pop(0)
            for edge in bb.get_edges():
                add(edge)
        
        # last block (containing fake return) is last.
        last = self.blocks[max(self.blocks.keys())]
        out.remove(last)
        out.append(last)
        
        return out
    
    def complexity_raw_lines(self):
        lines = self.body_bounds.diff()
        return self.cyclomatic_complexity() / float(lines)
    
    def complexity_source_lines(self):
        # define sloc as lines who generated an instruction.
        linemap = set()
        for bb in self.blocks.values():
            for loc, stmts in bb.statements_by_line():
                linemap.add(loc.line)
            
        return self.cyclomatic_complexity() / float(len(linemap))

    def __repr__(self):
        return '<Function %r(%r) at %r returning %r, %d blocks>' % \
             (self.name, self.argument_decls, self.location,
              self.return_type, len(self.blocks))

    @staticmethod
    def from_xml(e):
        f = Function()
        assert e.tag == 'function'
        f.return_type = types.type_from_xml(descend_one(e.find('returns')))
        f.name = e.get('name')
        f.location = Location(e.get('location'))
        f.body_bounds = Bounds(f.location.line, int(e.get('body-begin')), int(e.get('body-end')))
        for a in e.find('args').getchildren():
            f.argument_decls += [ decl.Decl.from_xml(a) ]
        b = e.find('body')
        f.entrypoint = int(b.get('entrypoint'))
        
        for l in b.find('locals').getchildren():
            d = decl.Decl.from_xml(l)
            assert d.binding.id not in f.local_decls
            f.local_decls[d.binding.id] = d
        
        for l in b.findall('block'):
            bb = Block.from_xml(l)
            assert bb.id not in f.blocks
            f.blocks[bb.id] = bb

        for b in e.find('externals'):
            d = decl.Decl.from_xml(b)
            assert d.binding.id not in f.externals
            f.externals[d.binding.id] = d
        
        return f
        

# -*- coding: utf-8 -*-
#
# Lighthouse - objects representing possible statements.
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
import lighthouse.expression as expression
import lighthouse.constant as constant
from lighthouse.misc import descend_one, to_c, Location

class Statement(object):
    def __init__(self):
        self.location = None

    def resolve_temporary_names(self):
        """
        Returns True if the statement is now pointless as a result
        of it being an constant assignment to a temporary.
        """
        return False

    def attach_decls(self, decls):
        pass

    def resolve_aggregates(self, aggrs):
        pass
    
    def get_edges(self):
        return []

class Assignment(Statement):
    def __init__(self):
        Statement.__init__(self)
        self.lhs = None
        self.rhs = []

    def to_c(self):
      rhs = ' '.join([to_c(x) for x in self.rhs])
      return '%s = %s' % \
        (to_c(self.lhs), rhs)

    def attach_decls(self, decls):
        expression.attach_decls_to_bindings(decls, self.lhs, *self.rhs)
    
    def resolve_temporary_names(self):
        return self.convolve_simple_assignments()
    
    def convolve_simple_assignments(self):
        # assignments without an operator (either binary or unary)
        # and an unnamed bound variable (ie, a temporary)
        if len(self.rhs) == 1 and isinstance(self.lhs, expression.Bound) and \
               self.lhs.decl and self.lhs.decl.binding.name is None:
            self.lhs.decl.binding.constant_temporary_value = to_c(self.rhs[0])
            return True
        else:
            return False
    
    @staticmethod
    def from_xml(t):
        a = Assignment()
        if t.get('location'):
            a.location = Location(t.get('location'))
        a.lhs = expression.result_from_xml(descend_one(t.find('lhs')))
        for x in t.find('rhs').getchildren():
          a.rhs += [expression.expression_from_xml(x)]
        return a

class Cond(Statement):
    def __init__(self):
        Statement.__init__(self)
        self.cond = []
        self.then = None
        self.else_ = None

    def cond_to_c(self):
        return ' '.join([to_c(x) for x in self.cond])

    def to_c(self):
      return 'if (%s)\n  goto bb%d;\nelse\n  goto bb%d' % \
          (self.cond_to_c(), self.then, self.else_)
    
    def attach_decls(self, decls):
        expression.attach_decls_to_bindings(decls, *self.cond)
    
    def get_edges(self):
        return [self.then, self.else_]
    
    @staticmethod
    def from_xml(t):
        c = Cond()
        if t.get('location'):
            c.location = Location(t.get('location'))
        for x in t.getchildren():
            if x.tag == 'then':
                c.then = int(x.get('id'))
            elif x.tag == 'else':
                c.else_ = int(x.get('id'))
            else:
                c.cond += [ expression.expression_from_xml(x) ]
        return c

class Call(Statement):
    def __init__(self):
        Statement.__init__(self)
        self.fnexpr = None
        self.lhs = None
        self.args = []

    def to_c(self):
      fn = to_c(self.fnexpr)
      lhs = to_c(self.lhs)
      args = ', '.join([to_c(x) for x in self.args])
      return '%s = %s(%s)' % (lhs, fn, args)
    
    def attach_decls(self, decls):
        expression.attach_decls_to_bindings(decls, self.fnexpr, self.lhs, *self.args)
    
    def resolve_aggregates(self, aggrs):
        self.args = [types.resolve_aggregates(arg, aggrs) for arg in self.args]

    @staticmethod
    def from_xml(t):
        c = Call()
        if t.get('location'):
            c.location = Location(t.get('location'))
        
        if t.find('function') == None:
          c.fnexpr = expression.expression_from_xml(t.getchildren()[0])
        else:
          c.fnexpr = expression.Bound(t.find('function'))
        
        c.lhs = expression.expression_from_xml(descend_one(t.find('lhs')))
        for a in t.find('args').getchildren():
            c.args += [ expression.expression_from_xml(a) ]
        return c

class Ret(Statement):
    def __init__(self):
        Statement.__init__(self)
        self.expr = None

    def to_c(self):
      if self.expr:
          return 'return %s' % ( to_c(self.expr) )
      else:
          return 'return'
    
    def attach_decls(self, decls):
        if self.expr:
            expression.attach_decls_to_bindings(decls, self.expr)
    
    @staticmethod
    def from_xml(t):
        r = Ret()
        if t.get('location'):
            r.location = Location(t.get('location'))
        if t.getchildren():
            r.expr = expression.expression_from_xml(descend_one(t))
        return r

class Switch(Statement):
    def __init__(self):
        Statement.__init__(self)
        self.expr = None
        self.default = None
        self.mapping = {}
    
    def to_c(self):
      expr = 'switch (%s)' % (self.expr.to_c())

      cases = []
      for v, b in self.mapping.iteritems():
          cases.append('  case %s: goto bb%d;' % (str(v), b))
      if self.default:
          cases.append('  default: goto bb%d;' % (self.default))
      cases = '\n'.join(cases)

      return '%s\n{\n%s}\n' % (expr, cases)

    def attach_decls(self, decls):
        expression.attach_decls_to_bindings(decls, self.expr)
    
    def get_edges(self):
        out = list(self.mapping.values())
        if self.default: out.append(self.default)
        return out

    @staticmethod
    def from_xml(t):
        s = Switch()
        if t.get('location'):
            s.location = Location(t.get('location'))
        s.expr = expression.expression_from_xml(descend_one(t.find('index')))
        if t.find('default') is not None:
          s.default = int(t.find('default').get('id'))
        for c in t.findall('case'):
          if len(c.getchildren()) == 1:
            k = descend_one(c)
            assert k.tag == 'exact', 'strange case label'
            s.mapping[constant.convert(descend_one(k))] = int(c.get('id'))
          else:
            assert len(c.getchildren()) == 2, 'strange case label'
            low, high = c.getchildren()
            assert low.tag == 'low-bound'
            assert high.tag == 'high-bound'
            low_const, high_const = constant.convert(descend_one(low)).get_value(), constant.convert(descend_one(high)).get_value()
            for x in range(low_const, high_const + 1):
                s.mapping[x] = int(c.get('id'))
        return s

def statement_from_xml(t):
    kinds = {
      'assign': Assignment,
      'if': Cond,
      'call': Call,
      'switch': Switch,
      'return': Ret,
    }
    
    ignore = set(['exception-dispatch'])
    if t.tag in ignore:
        return None
    
    assert t.tag in kinds, 'unknown type ' + t.tag
    return kinds[t.tag].from_xml(t)
    

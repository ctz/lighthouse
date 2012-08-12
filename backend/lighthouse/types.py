# -*- coding: utf-8 -*-
#
# Lighthouse - objects modelling types in C.
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

from lighthouse.decl import Decl
from lighthouse.misc import descend_one

class TypeCompare:
    """
    Contains all valid result types from TypeBase.compare().
    """
    
    class Base(object):
        """
        Base class for all comparison results.
        """
        def __init__(self, t1, t2):
            self.t1, self.t2 = t1, t2
        def has_same_memory_layout(self): return False
            
    class Equal(Base):
        """
        Types are equal modulo constness.
        """
        def has_same_memory_layout(self): return True
    
    class ZeroExtend(Base):
        """
        Types are 'compatible' unsigned integer types, through zero extension.
        """
        pass
    
    class SignExtend(Base):
        """
        Types are 'compatible' integer types, through sign extension.
        """
        pass
    
    class Truncate(Base):
        """
        Types are 'compatible' integer types, through truncation.
        """
        pass
        
    class FloatResize(Base):
        """
        Types are 'compatible' floating point types, through conversion.
        """
        pass
      
    class Incompatible(Base):
        """
        Types are incompatible.
        """
        pass

class TypeBase(object):
    """
    Base class for all C types.
    """
    def __init__(self, id, name = None):
        self.id = int(id)
        self.name = name
        self.constant = False

    def __eq__(self, other):
        return self.id != 0 and \
               self.id == other.id and \
               self.constant == other.constant
    
    def collect_interior_decls(self):
        return []
        
    def compare(self, other):
        """
        Default type comparison is by id.
        """
        if self.id == other.id:
            return TypeCompare.Equal(self, other)
        else:
            return TypeCompare.Incompatible(self, other)

    def to_c(self):
      # raise ValueError, '%r has no to_c'%type(self)
      return '{type %d}' % (self.id)

def resolve_aggregates(type, aggregates):
    if isinstance(type, AggregateRef):
        assert type.id in aggregates
        return aggregates[type.id]
    elif hasattr(type, 'resolve_interior_aggregates'):
        type.resolve_interior_aggregates(aggregates)
    return type

class Integer(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)
        self.precision = 0
        self.min = None
        self.max = None
        self.unsigned = False
        self.constant = False

    def to_c(self):
        cc = ['', 'const '][self.constant]
        if self.name:
            return cc + self.name
        else:
            return cc + '%sint%d' % \
              (('', 'u')[self.unsigned], self.precision)
    
    def compare(self, other):
        # Bools are effectively zero extended.
        if isinstance(other, Boolean):
            return TypeCompare.ZeroExtend(self, other)
            
        # Floats are value-cast.
        if isinstance(other, Float):
            return TypeCompare.FloatResize(self, other)
        
        # Only deal with integers from here-on in.
        if not isinstance(other, Integer):
            return TypeCompare.Incompatible(self, other)
    
        # If we're the same precision and same signedness, we're equal.
        if self.precision == other.precision and self.unsigned == other.unsigned:
            return TypeCompare.Equal(self, other)
    
        # If we're unsigned, we can either truncate or zero extend.
        if self.unsigned:
            if self.precision > other.precision:
                return TypeCompare.Truncate(self, other)
            else:
                return TypeCompare.ZeroExtend(self, other)
                
        # If we're signed, we either truncate or sign extend.
        if not self.unsigned:
            if self.precision > other.precision:
                return TypeCompare.Truncate(self, other)
            else:
                return TypeCompare.SignExtend(self, other)
        
        assert False, 'not reachable'

    @staticmethod
    def construct(precision, unsigned = False):
        i = Integer(0)
        i.precision = int(precision)
        i.unsigned = bool(unsigned)
        return i

    @staticmethod
    def from_xml(t):
        i = Integer(0, t.get('name'))
        i.constant = bool(t.get('constant') and int(t.get('constant')))
        i.precision = int(t.get('precision'))
        i.unsigned = bool(t.get('unsigned'))
        if t.get('min'): i.min = int(t.get('min'))
        if t.get('max'): i.max = int(t.get('max'))
        return i

class Enum(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)

    def to_c(self):
        if self.name:
            return 'enum ' + self.name
        else:
            return '<anonymous enum>'

    @staticmethod
    def from_xml(t):
        i = Enum(0, t.get('name'))
        return i

class Float(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)
        self.precision = 0

    def to_c(self):
        return self.name
        
    def compare(self, other):
        """
        Type comparison is by precision only.
        """
        if isinstance(other, Integer):
            return TypeCompare.FloatResize(self, other)
        if not isinstance(other, Float):
            return TypeCompare.Incompatible(self, other)
        
        if self.precision == other.precision:
            return TypeCompare.Equal(self, other)
        else:
            return TypeCompare.FloatResize(self, other)

    @staticmethod
    def construct(precision):
        f = Float(0)
        f.precision = int(precision)
        return f

    @staticmethod
    def from_xml(t):
        f = Float(0, t.get('name'))
        f.precision = int(t.get('precision'))
        return f

class Boolean(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)

    def compare(self, other):
        """
        Always equal.
        """
        if isinstance(other, Boolean):
            return TypeCompare.Equal(self, other)
        else:
            # Can extend into integer and float types
            if isinstance(other, (Integer, Float)):
                return Integer.construct(precision = 8, unsigned = True).compare(other)
            return TypeCompare.Incompatible(self, other)

    def to_c(self):
        return 'bool'

    @staticmethod
    def construct():
        return Boolean(0)

    @staticmethod
    def from_xml(t):
        f = Boolean(0)
        return f

class Function(TypeBase):
    def __init__(self, id, name):
        TypeBase.__init__(self, id, name)
        self.returns = None
        self.arguments = []

    def resolve_interior_aggregates(self, types):
        if self.returns:
            self.returns = resolve_aggregates(self.returns, types)
        self.arguments = [resolve_aggregates(a, types) for a in self.arguments]

    def to_c(self):
      return '%s %s(%s)' % \
          ( self.returns.to_c(), 
            self.name,
            ', '.join([x.to_c() for x in self.arguments]) )

    def compare(self, other):
        """
        By identity.
        (TODO: compare returns and args in detail?)
        """
        TypeBase.compare(self, other)
    
    @staticmethod
    def from_xml(t):
        f = Function(t.get('id') or 0, t.get('name'))
        f.returns = type_from_xml(descend_one(t.find('return')))
        for a in t.find('arguments').getchildren():
            f.arguments += [ type_from_xml(a) ]
        return f

class Void(TypeBase):
    def __init__(self):
        TypeBase.__init__(self, 0, 'void')

    def to_c(self):
        return 'void'
        
    def compare(self, other):
        """
        Always equal.
        """
        if isinstance(other, Void):
            return TypeCompare.Equal(self, other)
        else:
            return TypeCompare.Incompatible(self, other)
    
    @staticmethod
    def from_xml(t):
        return Void()

class AddrOf(TypeBase):
    def __init__(self, id = 0, name = None):
        TypeBase.__init__(self, id, name)
        self.of = None

    def to_c(self):
        return self.of.to_c() + '*'
        
    def compare(self, other):
        """
        Compares targets.
        """
        if isinstance(other, AddrOf):
            return self.of.compare(other.of)
        else:
            return TypeCompare.Incompatible(self, other)

    def resolve_interior_aggregates(self, types):
        self.of = resolve_aggregates(self.of, types)

    @staticmethod
    def from_xml(t):
        a = AddrOf(0, t.get('name'))
        a.of = type_from_xml(descend_one(t))
        return a

class AggregateRef(TypeBase):
    """
    Reference to an aggregate, before resolution.
    """
    def __init__(self, id):
        TypeBase.__init__(self, id)

    @staticmethod
    def from_xml(t):
        return AggregateRef(int(t.get('id')))

class Structure(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)
        self.members = [] # decls

    def resolve_interior_aggregates(self, types):
        for m in self.members:
            m.resolve_aggregates(types)

    def collect_interior_decls(self):
        return self.members

    def to_c(self):
        if self.name:
            return 'struct %s' % self.name
        else:
            o = []
            for m in self.members:
                o.append(m.to_c() + ';')
            n = ''
            if self.name:
                n = self.name
            return 'struct %s { %s }' % (n, ' '.join(o))
    
    def resolve_member(self, i):
        for mm in self.members:
            if mm.binding.name == i:
                return mm

    @staticmethod
    def from_xml(t):
        assert t.tag == 'structure'
        s = Structure(t.get('id'), t.get('name'))
        for m in t.getchildren():
            assert m.tag == 'member'
            s.members += [ Decl.from_xml(m) ]
        return s

class Union(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)
        self.members = [] # decls

    def resolve_interior_aggregates(self, types):
        for m in self.members:
            m.resolve_aggregates(types)

    def collect_interior_decls(self):
        return self.members
    
    def resolve_member(self, i):
        for mm in self.members:
            if mm.binding.name == i:
                return mm

    def to_c(self):
        if self.name:
            return 'union %s' % self.name
        else:
            o = []
            for m in self.members:
                o.append(m.to_c() + ';')
            n = ''
            if self.name:
                n = self.name
            return 'union %s { %s }' % (n, ' '.join(o))

    @staticmethod
    def from_xml(t):
        assert t.tag == 'union'
        s = Structure(t.get('id'), t.get('name'))
        for m in t.getchildren():
            assert m.tag == 'member'
            s.members += [ Decl.from_xml(m) ]
        return s

class Array(TypeBase):
    def __init__(self, id, name = None):
        TypeBase.__init__(self, id, name)
        self.type = None
        self.domain = None

    def resolve_interior_aggregates(self, types):
        self.type = resolve_aggregates(self.type, types)

    def decompose_to_pointer(self):
        a = AddrOf()
        a.of = self.type
        return a
   
    def to_c(self):
        domain = ''
        if self.domain.min is not None and self.domain.max is not None:
            domain = str(self.domain.max)
        return '%s[%s]' % ( self.type.to_c(), domain )

    @staticmethod
    def from_xml(t):
        assert t.tag == 'array'
        a = Array(t.get('id'), t.get('name'))
        a.type = type_from_xml(descend_one(t.find('type')))
        if t.find('domain'):
            a.domain = type_from_xml(descend_one(t.find('domain')))
        return a

def type_from_xml(t):
    kinds = {
      'addr-of': AddrOf,
      'float': Float,
      'integer': Integer,
      'void': Void,
      'function': Function,
      'structure': AggregateRef,
      'array': AggregateRef,
      'enum': Enum,
      'boolean': Boolean,
      'union': AggregateRef,
    }

    assert t.tag in kinds, 'unknown type ' + t.tag
    return kinds[t.tag].from_xml(t)

def aggregate_from_xml(t):
    kinds = dict(array = Array, structure = Structure, union = Union)
    assert t.tag in kinds
    return kinds[t.tag].from_xml(t)

def _test():
    uint = Integer.construct(precision = 32, unsigned = True)
    int = Integer.construct(precision = 32)
    bool = Boolean.construct()

    print 'uint'
    print uint.compare(uint)
    print uint.compare(int)
    print uint.compare(bool)

    print 'bool'
    print bool.compare(bool)
    print bool.compare(int)
    print bool.compare(uint)

if __name__ == '__main__':
    _test()


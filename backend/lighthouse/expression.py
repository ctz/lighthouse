# -*- coding: utf-8 -*-
#
# Lighthouse - objects representing possible expressions.
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

from etree import etree
import operator
import decimal

import lighthouse.types as types
import lighthouse.constant as constant
from lighthouse.misc import descend_one, to_c, dump

valid_lvalues = ('bound', 'bound-parameter', 'member-ref', 'item-ref',
                 'indirection', 'result')

def attach_decls_to_bindings(decls, *exprs):
    for e in exprs:
        if hasattr(e, 'attach_decl'):
            e.attach_decl(decls)

class Bound(object):
    def __init__(self, t = None):
        if t is not None:
            self.id = int(t.get('id'))
        else:
            self.id = 0
        self.decl = None
    
    def get_type(self):
        return self.decl.type

    def to_c(self):
        if self.decl:
            return self.decl.binding.to_c()
        else:
            return 'U.%d' % (self.id)

    def attach_decl(self, decls):
        if self.id in decls:
            self.decl = decls[self.id]

class MemberRef(object):
    def __init__(self, t):
        self.struct = expression_from_xml(descend_one(t.find('structure')))
        self.member = expression_from_xml(descend_one(t.find('member')))
    
    def get_type(self):
        return self.member.decl.type

    def attach_decl(self, decls):
        attach_decls_to_bindings(decls, self.struct, self.member)

    def to_c(self):
        return '%s.%s' % (to_c(self.struct), to_c(self.member))

class ItemRef(object):
    def __init__(self, t):
        self.array = expression_from_xml(descend_one(t.find('array')))
        self.index = expression_from_xml(descend_one(t.find('index')))
        
    def get_type(self):
        # Resolves to the arrayed type.
        array_t = self.array.get_type()
        return array_t.type
    
    def attach_decl(self, decls):
        attach_decls_to_bindings(decls, self.array, self.index)

    def to_c(self):
        return '%s[%s]' % (to_c(self.array), to_c(self.index))

class Indirect(object):
    def __init__(self, t):
        self.thing = result_from_xml(descend_one(t))
        
    def get_type(self):
        return self.thing.get_type()
    
    def attach_decl(self, decls):
        attach_decls_to_bindings(decls, self.thing)

    def to_c(self):
        return '*%s' % (to_c(self.thing))

class BinaryOp(object):
    def __init__(self, tt):
        assert len(tt) == 2
        self.op, self.c = tt

    def to_c(self):
        return self.c

class UnaryOp(BinaryOp):
    pass
 
class Void(object):
    def __init__(self):
        pass
    def to_c(self):
        return '(void)'
    def get_type(self):
        return types.Void()
 
class Result(object):
    def __init__(self):
        pass
    def to_c(self):
        return '__result'

class AddrOf(object):
    def __init__(self, t):
        self.of = expression_from_xml(descend_one(t))
    
    def attach_decl(self, decls):
        attach_decls_to_bindings(decls, self.of)

    def get_type(self):
        if self.string_literal():
            return self.of.array.get_type()
        else:
            t = types.AddrOf()
            t.of = self.of.get_type()
            return t

    def to_c(self):
        return '&' + to_c(self.of)
    
    def string_literal(self):
        if isinstance(self.of, ItemRef) and isinstance(self.of.array, constant.ConstantString) and isinstance(self.of.index, constant.ConstantInteger):
            return self.of.array.get_value()[self.of.index.get_value():].rstrip('\0')
        else:
            return None

def result_from_xml(t):
    assert t.tag in valid_lvalues

    if t.tag in ('bound', 'bound-parameter'):
        return Bound(t)
    elif t.tag == 'member-ref':
        return MemberRef(t)
    elif t.tag == 'item-ref':
        return ItemRef(t)
    elif t.tag == 'indirection':
        return Indirect(t)
    elif t.tag == 'result':
        return Result()

# XXX marks incorrect operator members which need wrapping.
binary_operators = {
    'plus':             (operator.add, '+'),
    'minus':            (operator.sub, '-'),
    'multiply':         (operator.mul, '*'),
    'pointer-offset':   (operator.add, '+'), #      XXX
    'division-truncate':(operator.div, '/'),
    'division-ceil':    (operator.div, '/'), #      XXX
    'division-floor':   (operator.floordiv, '//'),
    'division-round':   (operator.truediv, '/'), #  XXX
    'division-exact':   (operator.div, '/'),
    'modulo-truncate':  (operator.mod, '%'),
    'modulo-ceil':      (operator.mod, '%'), #      XXX
    'modulo-floor':     (operator.mod, '%'), #      XXX
    'modulo-round':     (operator.mod, '%'), #      XXX
    'shift-left':       (operator.lshift, '<<'),
    'shift-right':      (operator.rshift, '>>'),
    'rotate-left':      (operator.lshift, '<<'), #  XXX
    'rotate-right':     (operator.rshift, '>>'),
    'bitwise-or':       (operator.or_, '|'),
    'bitwise-xor':      (operator.xor, '^'),
    'bitwise-and':      (operator.and_, '&'),
    'logical-short-and':(operator.and_, '&&'), #    XXX
    'logical-short-or': (operator.or_, '||'), #     XXX
    'logical-and':      (operator.and_, '&&'),
    'logical-or':       (operator.or_, '||'),
    'logical-xor':      (operator.xor, '^^'),
    'less-than':        (operator.lt, '<'),
    'less-than-or-equal':(operator.le, '<='),
    'greater-than':     (operator.gt, '>'),
    'greater-than-or-equal':
                        (operator.ge, '>='),
    'equal':            (operator.eq, '=='),
    'not-equal':        (operator.ne, '!='),
    'min':              (min, 'min'),
    'max':              (max, 'max'),
}

unary_operators = {
    'float':            (decimal.Decimal, '(float)'),
    'fixed-point-truncate':
                        (long, '(int)'),
    'negate':           (operator.neg, '-'),
    'absolute':         (operator.abs, 'abs'),
    'bitwise-not':      (operator.not_, 'not'),
    'logical-not':      (operator.not_, 'not'),
    'nop-convert':      (None, '(reinterpret)'),
    'exception-pointer':(None, '???'),
    'convert':          (None, '(convert)'),
    'address-of':       (None, '&'),
}

def expression_from_xml(t):
    if t.tag in valid_lvalues:
        return result_from_xml(t)
    if t.tag in ('constant',):
        return constant.convert(t)
    if t.tag in binary_operators.keys():
        return BinaryOp(binary_operators[t.tag])
    if t.tag in unary_operators.keys():
        return UnaryOp(unary_operators[t.tag])
    if t.tag == 'addr-of':
        return AddrOf(t)
    if t.tag == 'void':
        return Void()
    if t.tag == 'function':
        return expression_from_xml(descend_one(t))

    print 'warn: tag %s unhandled, returning dummy bound' % (t.tag)
    dump(t)
    return Bound()


# -*- coding: utf-8 -*-
#
# Lighthouse - conversion of constants to python types.
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

import decimal
import lighthouse.types as types

class ConstantBase(object):
    def get_type(self):
        return self.type
    def get_value(self):
        return self.value
    def to_c(self):
        return self.value

class ConstantString(ConstantBase):
    def __init__(self, type, value):
        self.type = types.aggregate_from_xml(type)
        self.value = value.text.decode('string-escape')

    def get_type(self):
        return self.type.decompose_to_pointer()

    def to_c(self):
        return repr(self.value)

# these two never have interior aggregates
class ConstantInteger(ConstantBase):
    def __init__(self, type, value):
        self.type = types.type_from_xml(type)
        self.value = long(value.get('value'))

class ConstantFloat(ConstantBase):
    def __init__(self, type, value):
      self.type = types.type_from_xml(type)
      if value.get('special'):
          self.value = decimal.Decimal(value.get('special'))
      else:
          self.value = decimal.Decimal(value.get('value'))

def convert(t):
    kinds = {'string-literal': ConstantString,
             'integer-literal': ConstantInteger,
             'float-literal': ConstantFloat}

    assert t.tag == 'constant'
    type, value = t.getchildren()

    assert value.tag in kinds.keys()
    return kinds[value.tag](type, value)

# -*- coding: utf-8 -*-
#
# Lighthouse - object representing a single declaration.
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

from lighthouse.misc import Location

class Binding(object):
    def __init__(self):
        self.id = 0
        self.name = None
        self.constant_temporary_value = None

    def __repr__(self):
      return '<binding id %r name %r>' % (self.id, self.name)

    def to_c(self):
      if self.name:
        return self.name
      elif self.constant_temporary_value:
        return self.constant_temporary_value
      else:
        return '__tmp_%d' % (self.id)

    @staticmethod
    def from_xml(t):
        b = Binding()
        b.id = int(t.get('id'))
        b.name = t.get('name')
        return b

class Decl(object):
    def __init__(self):
        self.location = None
        self.binding = None
        self.decl = None
        self.type = None

    def resolve_aggregates(self, types):
        from lighthouse.types import resolve_aggregates
        self.type = resolve_aggregates(self.type, types)

    def attach_bound_names(self, decls):
        if self.binding.id in decls:
            self.decl = decls[self.binding.id]
    
    def is_temporary(self):
        return self.binding.name is None

    def __repr__(self):
      return '<declaration of %r type %r>' % (self.binding, self.type)

    def to_c(self):
      return self.type.to_c() + ' ' + self.binding.to_c()

    @staticmethod
    def from_xml(t):
        from lighthouse.types import type_from_xml
        d = Decl()
        if t.get('location'):
            d.location = Location(t.get('location'))
        d.binding = Binding.from_xml(t.find('binding'))
        d.type = type_from_xml(t.find('type').getchildren()[0])
        return d

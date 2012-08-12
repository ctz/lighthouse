# -*- coding: utf-8 -*-
#
# Lighthouse - misc objects.
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

class Location(object):
    def __init__(self, loc):
        self.set(loc)
    
    def __str__(self):
        if self.column:
            return '%s:%d:%d' % (self.file, self.line, self.column)
        else:
            return '%s:%d' % (self.file, self.line)

    def set(self, loc):
        bits = loc.split(':')
        if len(bits) in (2, 3):
            self.line = int(bits[1])
            self.file = bits[0]
        if len(bits) == 3:
            self.column = int(bits[2])
        else:
            self.column = 0
        if len(bits) not in (2, 3):
            raise ValueError, "%r is not a valid location" % loc

    def __repr__(self):
        return '<Location file %r line %d col %d>' % \
                (self.file, self.line, self.column)
    
    def highlight(self, src, label = ''):
        x = max(0, self.line - 1 - 2)
        y = self.line - 1 + 2
        actual_lines = src.splitlines()

        selected_lines = []
        context = 5

        for l in range(max(0, self.line - 1 - context), self.line + context):
            if l == self.line - 1:
                selected_lines.append('>>> %-4d ' % (l+1)  + actual_lines[l])
                if self.column:
                    selected_lines.append((' ' * 9) + (' ' * (self.column - 1)) + '^----- ' + label)
            else:
                selected_lines.append('*** %-4d ' % (l+1)  + actual_lines[l])
        
        return '\n'.join(selected_lines)

def descend_one(t):
    """
    descend into t's single child element.
    """
    if len(t.getchildren()) != 1:
        print 'descend_one', etree.tostring(t)
    assert len(t.getchildren()) == 1, 'descend_one given %d children' % len(t.getchildren())
    return t.getchildren()[0]

def to_c(s):
    if hasattr(s, 'to_c'):
        return s.to_c()
    elif isinstance(s, str) or isinstance(s, unicode):
        return repr(s)
    else:
        return str(s)

def dump(node):
    etree.dump(node)

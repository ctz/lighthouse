# -*- coding: utf-8 -*-
#
# Lighthouse - decoding from the xml to a unit.
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
from etree import etree
import lighthouse.unit as unit
import lighthouse.functions as functions
import lighthouse.types as types

def parse(fn, out = None):
    """
    Reads XML from the file name or object 'fn' and returns
    a 'Unit' instance.  Rewrites the XML to out, if not None.
    """
    e = etree.parse(fn).getroot()
    u = unit.Unit()
    u.lang = e.get('language')
    u.filename = e.get('filename')
    
    if out:
        open(out + os.path.basename(u.filename) + '.lh', 'w').write(etree.tostring(e))

    u.source = e.find('raw-source').text
    for t in e.find('referenced-types').getchildren():
        tt = types.aggregate_from_xml(t)
        assert tt.id not in u.types
        u.types[tt.id] = tt
    for f in e.find('function-bodies').getchildren():
        u.functions += [ functions.Function.from_xml(f) ]
    u.finalise()
    return u

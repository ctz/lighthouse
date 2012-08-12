import xml.sax.saxutils

def format(unit):
    return xml.sax.saxutils.escape(unit.source)
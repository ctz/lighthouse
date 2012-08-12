from xml.sax.saxutils import escape
from urllib import quote_plus

htmlextras = {'"': '&quot;'}

__all__ = ('htmlencode', 'urlencode')
    
def htmlencode(s):
    return escape(s, htmlextras)

def urlencode(s):
    return quote_plus(s)

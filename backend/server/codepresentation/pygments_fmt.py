
import pygments
import pygments.lexers
import pygments.formatters

def format(unit):
    fmt = pygments.formatters.HtmlFormatter(nowrap = True)
    return pygments.highlight(unit.source,
        pygments.lexers.get_lexer_for_filename(unit.filename),
        fmt)
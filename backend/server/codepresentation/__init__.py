import simple_fmt
import bbgraph

TRY_PYGMENTS = True

class line(object):
    def __init__(self, no, raw, fmt):
        self.number = no + 1
        self.raw = raw
        self.formatted = fmt
        self.function = None
        self.bbgraph = None
        self.decls = []
    
    def columns(self):
        out = []
        for col, char in enumerate(self.raw):
            found = False
            for d in self.decls:
                if d.location.column == col+1:
                    found = True
                    break
            if found:
                yield d
            else:
                yield None

def format_source(unit):
    raw_lines = unit.source.split('\n')
    lines = highlight_lines(unit).split('\n')
    out = []
    
    line_functions = {}
    line_decls = {}
    
    for f in unit.functions:
        line_functions[f.location.line] = line_functions.get(f.location.line, []) + [f]
    for d in decl_markers(unit):
        line_decls[d.location.line] = line_decls.get(d.location.line, []) + [d]
    
    for lineno, linefmt in enumerate(lines):
        l = line(lineno, raw_lines[lineno], linefmt)
        l.function = line_functions.get(l.number, [None])[0]
        if l.function:
            l.bbgraph = bbgraph.construct(l.function)
        l.decls = line_decls.get(l.number, [])
        out.append(l)
    
    return out

def highlight_lines(unit):
    if TRY_PYGMENTS:
        try:
            import pygments_fmt
        except ImportError:
            return simple_fmt.format(unit)
        else:
            return pygments_fmt.format(unit)
    else:
        return simple_fmt.format(unit)

def decl_markers(unit):
    decls = []
    for f in unit.functions:
        decls.extend(f.argument_decls)
        decls.extend([d for d in f.local_decls.values() if not d.is_temporary()])
        decls.extend(f.externals.values())
    return decls

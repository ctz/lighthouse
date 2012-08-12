import lighthouse.statements as ST
from utils import htmlencode

class edge(object):
    Basic = 1
    IfThen = 2
    IfElse = 3
    Exception = 4
    SwitchCase = 5
    SwitchDefault = 6
    
    Structured = (IfThen, IfElse, SwitchCase, SwitchDefault)
    
    def __init__(self, target, kind):
        self.kind, self.target = kind, target
        self.annot = None
        self.value = None

SpecialStatements = (ST.cond, ST.switch)

class block(object):
    def __init__(self):
        self.bb = None
        self.stmts = []
        self.out_edges = []
        self.fn_name = None
    
    def add_out_edge(self, targ, kind):
        e = edge(targ, kind)
        self.out_edges.append(e)
        return e
        
    LINEBLOCK = """<div id="lineblock_%(fn_name)s_%(id)d_%(line)d" class="lineblock lineblock_%(fn_name)s_%(line)d" title="Line %(line)d"><pre>"""
    MOUSEHANDLER = """<script type="text/javascript">
$('#lineblock_%(fn_name)s_%(id)d_%(line)d').bind("mouseenter mouseleave", function(e) {
    $('#lineno_%(line)d').toggleClass('lineno_hilight');
    $(this).toggleClass('lineblock_hilight');
  });
</script>"""
    POSTBLOCK = """<script type="text/javascript">
$('#block_%(fn_name)s_%(id)d').bind("mouseenter", function(e) {
    highlightArrows("%(fn_name)s", %(id)d);
  });
$('#block_%(fn_name)s_%(id)d').bind("mouseleave", function(e) {
    unhighlightArrows("%(fn_name)s", %(id)d);
  });
</script>"""
    
    @property
    def statements(self):
        out = []
        for loc, stmts in self.bb.statements_by_line():
            line = 0
            if loc:
                line = loc.line
            v = dict(line = line, fn_name = self.fn_name, id = self.bb.id)
            out.append(block.LINEBLOCK % v)
            out += [htmlencode(s.to_c()) + '<br/>' for s in stmts if not isinstance(s, SpecialStatements)]
            if len(stmts):
                ls = stmts[-1]
                if isinstance(ls, ST.cond):
                    out += [ 'if ' + htmlencode(ls.cond_to_c()) + '<br/>',
                             'if not ' + htmlencode(ls.cond_to_c()) ]
                if isinstance(ls, ST.switch):
                    out += [ 'switch ' + htmlencode(ls.expr.to_c()) + '<br/>' ]
                    out += [ '  case ' + htmlencode(str(x)) + '<br/>' for x in ls.mapping.keys() ]
                    out.append('  default')
            out.append('</pre></div>')
            out.append(block.MOUSEHANDLER % v)
        return ''.join(out)
    
    def format(self):
        fmt = '<div id="block_%(fn_name)s_%(id)d" class="basicblock">%(statements)s</div>' + block.POSTBLOCK
        return fmt % dict(fn_name = self.fn_name, id = self.bb.id, statements = self.statements)
        
class arrow(object):
    def __init__(self, edge):
        self.edge = edge
        self.start = 0
        self.end = 0
        self.rank = 0
        self.depth = 0
        self.offset = 0
    
    def format(self, fn):
        return 'cfgArrow(r, "%s", %d, %d, %d, %d);' % (fn, self.rank, self.start, self.end, self.offset)

class graph(object):
    def __init__(self):
        self.blocks = []
        self.arrows = []
        self.fn_name = None
    
    ARROWBLOCK = """<div id='blockgraph_%(fn_name)s' class="blockgraph"></div>
<script type="text/javascript">
var d = document.getElementById("blockgraph_%(fn_name)s");
var h = document.getElementById("blocks_%(fn_name)s");
var r = Raphael(d, cfgGraphWidth, h.getSize().y);
%(arrows)s
</script>"""
    
    def add(self, b):
        assert isinstance(b, block)
        self.blocks.append(b)
    
    def make_arrows(self):
        for b in self.blocks:
            for i, edge in enumerate(b.out_edges):
                a = arrow(edge)
                if edge.kind in edge.Structured:
                    a.offset = - (len(b.out_edges) - b.out_edges.index(edge))
                a.start = b.bb.id
                a.end = edge.target
                self.arrows.append(a)
        self.rank_arrows()
    
    def rank_arrows(self):
        def find(id):
            for x in self.blocks:
                if id == x.bb.id:
                    return x
        
        def indices(st, ed):
            return self.blocks.index(st), self.blocks.index(ed)
        
        def block_span(st, ed):
            sti, edi = indices(st, ed)
            return abs(edi - sti)
        
        def arrows_in_block(b):
            id = self.blocks.index(b)
            out = set()
            for a in self.arrows:
                sti, edi = indices(find(a.start), find(a.end))
                for x in range(sti, edi + 1):
                    if id == self.blocks[x].bb.id:
                        out.add(a)
            return out
        
        def max_rank_in_block(b):
            depths = [a.depth for a in arrows_in_block(b)]
            if depths:
                return max(depths)
            return 0
        
        def arrow_span(st, ed):
            ranks = []
            sti, edi = indices(st, ed)
            for i in range(sti, edi + 1):
                ranks.append(max_rank_in_block(self.blocks[i]))
            if ranks:
                return max(ranks) + 1
            else:
                return 1
            
        for a in self.arrows:
            s, e = find(a.start), find(a.end)
            a.depth = block_span(s, e)
        for a in self.arrows:
            s, e = find(a.start), find(a.end)
            a.rank = arrow_span(s, e) + a.depth
    
    def format_arrows(self):
        arrows = '\n'.join([a.format(self.fn_name) for a in self.arrows])
        return graph.ARROWBLOCK % dict(fn_name = self.fn_name, arrows = arrows)

    def format(self):
        return '<table class="blockgraph"><tr><td>' + ''.join([b.format() for b in self.blocks]) + \
                 '</td><td>' + self.format_arrows() + '</td></tr></table>'

def construct(fn):
    g = graph()
    g.fn_name = fn.name
    for bb in fn.blocks_in_natural_order():
        b = block()
        b.bb = bb
        b.fn_name = fn.name
        for s in bb.statements:
            # Look for statements containing edges (conditions, and switch statements)
            if isinstance(s, ST.cond):
                b.add_out_edge(s.then, edge.IfThen)
                b.add_out_edge(s.else_, edge.IfElse)
            elif isinstance(s, ST.switch):
                for vv, b_id in s.mapping.items():
                    b.add_out_edge(b_id, edge.SwitchCase)
                b.add_out_edge(s.default, edge.SwitchDefault)
        for e in bb.next:
            b.add_out_edge(e, edge.Basic)
        g.add(b)

    g.make_arrows()
    return g.format()
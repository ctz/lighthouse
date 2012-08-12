from lighthouse.analysis import FunctionCallAnalyser
from lighthouse.misc import to_c

unpack = [
  ('i(%d)' % x, 'int%d_t*' % x) for x in (8, 16, 32, 64)
] + [
  ('v(%d)' % x, 'uint%d_t*' % x) for x in (8, 16, 32, 64)
] + [
  ('i(s)',  'short int*'),
  ('i(l)',  'long int*'),
  ('i(max)','intmax_t*'),
  
  ('v(s)',  'short unsigned int*'),
  ('v(l)',  'long unsigned int*'),
  ('v(max)','uintmax_t*'),
  
  ('i',     'int*'),
  ('v',     'unsigned int*'),
  ('j',     'size_t*'),
  ('n',     'struct NFast_Bignum**'),
  ('s',     'char**'),
  ('h',     'struct DSSymbolNode**'),
  ('b',     'struct DSByteBlock*'),
  ('m',     'struct DSMessage**'),
  ('l',     'struct DSMessage**'),
  ('e',     'struct DSMessage**'),
  ('d',     'struct DSMessage**'),
]

pack = [
  ('i(%d)' % x, 'int%d_t' % x) for x in (8, 16, 32, 64)
] + [
  ('v(%d)' % x, 'uint%d_t' % x) for x in (8, 16, 32, 64)
] + [
  ('i(s)',  'short int'),
  ('i(l)',  'long int'),
  ('i(max)','intmax_t'),
  
  ('v(s)',  'short unsigned int'),
  ('v(l)',  'long unsigned int'),
  ('v(max)','uintmax_t'),
  
  ('i',     'int'),
  ('v',     'unsigned int'),
  ('j',     'size_t'),
  ('n',     'struct NFast_Bignum*'),
  ('s',     'const char*'),
  ('h',     'struct DSSymbolNode*'),
  ('b',     'struct DSByteBlock*'),
  ('m',     'struct DSMessage*'),
  ('r',     'struct DSMessage*'),
  ('e',     'struct DSMessage**'),
]

symbol_type = 'struct DSSymbolNode*'


class D3SAnalyser(FunctionCallAnalyser):
    def __init__(self):
        FunctionCallAnalyser.__init__(self)
    
    def decompose_format_string(self, stmt, format, specs, unpack = True):
        out = []
        
        lastlen = len(format)
        
        while True:
            handled = False
            
            if format == '':
                break
                
            if format.startswith('|'):
                format = format[1:]
                continue

            if format[0] == '-':
                format = format[1:]
                out.append(None)
                continue
             
            if unpack and format[0] == format[0].upper():
                format = format[1:]
                out.append(None)
                continue
            
            for fmtspec, fmttype in specs:
                if format.startswith(fmtspec):
                    out.append(fmttype)
                    format = format[len(fmtspec):]
                    lastlen = len(format)
                    handled = True
                    break
            if not handled:
                self.error('Unknown format string ' + repr(format), location = {'call-site': stmt})
        
        return out
    
    def pop_or_error(self, stmt, tt):
        if len(tt) == 0:
            self.error('Not enough arguments to varargs function.',
                       location = {'call-site': stmt})
        return tt.pop(0)

    def check_unpack(self, fn, stmt, lhs, args):
        assert len(args) >= 4, 'not enough args to ' + fn
        format = args[3]
        format = format.string_literal()
        if format is None:
            self.warn('Call to %s has variable format string. Verify it will always correspond with the passed in types.' % fn,
                      location = {'call-site': stmt})
            return
        
        specifiers = self.decompose_format_string(stmt, format, unpack)
        varargs = args[4:]
        
        for i, spec in enumerate(specifiers):
            if fn == 'dsUnpackMap':
                symbol = self.pop_or_error(stmt, varargs)
                if to_c(symbol.get_type()) != symbol_type:
                    self.error('Symbol argument (index %d) to %s is not a DSSymbol, but a "%s".' % (i, fn, to_c(symbol.get_type())),
                               location = {'call-site': stmt})
            
            if spec is None:
                continue
                
            item = self.pop_or_error(stmt, varargs)
            if to_c(item.get_type()) != spec:
                self.error('Value argument (index %d) to %s is not a "%s" as specified, but a "%s".' % (i, fn, spec, to_c(item.get_type())),
                           location = {'call-site': stmt})
    
    def check_pack(self, fn, stmt, lhs, args, fmtidx):
        assert len(args) >= fmtidx, 'not enough args to ' + fn
        format = args[fmtidx]
        format = format.string_literal()
        if format is None:
            self.warn('Call to %s has variable format string. Verify it will always correspond with the passed in types.' % fn,
                      location = {'call-site': stmt})
            return
        
        specifiers = self.decompose_format_string(stmt, format, pack, False)
        varargs = args[fmtidx+1:]
        
        for i, spec in enumerate(specifiers):
            if fn == 'dsPackMapB':
                symbol = self.pop_or_error(stmt, varargs)
                if to_c(symbol.get_type()) != symbol_type:
                    self.error('Symbol argument (index %d) to %s is not a DSSymbol, but a "%s".' % (i, fn, to_c(symbol.get_type())),
                               location = {'call-site': stmt})
            
            item = self.pop_or_error(stmt, varargs)
            if to_c(item.get_type()) != spec:
                self.error('Value argument (index %d) to %s is not a "%s" as specified, but a "%s".' % (i, fn, spec, to_c(item.get_type())),
                           location = {'call-site': stmt})
    
    @FunctionCallAnalyser.Handler()
    def dsUnpackMap(self, stmt, lhs, args):
        self.check_unpack('dsUnpackMap', stmt, lhs, args)

    @FunctionCallAnalyser.Handler()
    def dsUnpackList(self, stmt, lhs, args):
        self.check_unpack('dsUnpackList', stmt, lhs, args)

    @FunctionCallAnalyser.Handler()
    def dsPackListB(self, stmt, lhs, args):
        self.check_pack('dsPackListB', stmt, lhs, args, 2)

    @FunctionCallAnalyser.Handler()
    def dsPackMapB(self, stmt, lhs, args):
        self.check_pack('dsPackMapB', stmt, lhs, args, 2)

    @FunctionCallAnalyser.Handler()
    def dsMakeMapB(self, stmt, lhs, args):
        self.check_pack('dsMakeMapB', stmt, lhs, args, 1)
    
    @FunctionCallAnalyser.Handler()
    def dsMakeListB(self, stmt, lhs, args):
        self.check_pack('dsMakeListB', stmt, lhs, args, 1)

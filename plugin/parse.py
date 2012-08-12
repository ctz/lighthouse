
from lighthouse import input
import lighthouse.presentation

if __name__ == '__main__':
    v = input.parse('helloworld.c.lh')
    print v
    for f in v.functions:
      print f.to_c()
    print >>open('helloworld.c.html', 'w'), lighthouse.presentation.format_source(v)
    v = input.parse('hello.cc.lh')
    print v

GCCARCH=$(shell gcc -dumpmachine)
GCCVER=$(shell gcc -dumpversion)
GCCHOME=/usr/local/lib/gcc/$(GCCARCH)/$(GCCVER)/plugin

CFLAGS=	 -DIN_GCC	-g -shared -fPIC -Wall -I. -I$(GCCHOME)/include/

all:		printargs.so complexity.so lighthouse-client.so

complexity.so: complexity.c
		gcc $(CFLAGS) -o $@ $^

printargs.so:	printargs.c
		gcc $(CFLAGS) -o $@ $^

lighthouse-client.so:	lighthouse-client.c lighthouse-output.c lighthouse-internal.h lighthouse-gimple.c lighthouse-tree.c
		gcc $(CFLAGS) -DLH_CLIENT_VERSION='"0.1"' -o $@ $^

DEBUG=gdb --args 
DEBUG=

clean:
		rm *.so

test:		lighthouse-client.so
		$(DEBUG) gcc -fplugin=./lighthouse-client.so -fdump-tree-cfg -fdump-tree-gimple-raw -o helloworld helloworld.c
		$(DEBUG) g++ -fplugin=./lighthouse-client.so -fdump-tree-cfg -fdump-tree-gimple-raw -o hello hello.cc
		$(DEBUG) gcc -fplugin=./complexity.so -fplugin-arg-complexity-cyclomatic=warn:5 -o helloworld helloworld.c
		$(DEBUG) g++ -fplugin=./complexity.so -o hello hello.cc

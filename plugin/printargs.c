/* Introductory plugin which prints all plugin arguments. */

#include <stdio.h>

#include "gcc-plugin.h"

int plugin_init(const char *name, int argc, struct plugin_argument *argv)
{
  while (argc--)
  {
    printf("%s: %s -> %s\n", name, argv->key, argv->value);
    ++argv;
  }

  return 0;
}

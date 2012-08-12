/**
 * complexity.c
 * ------------
 * This is a GCC plugin which emits diagnostics (through the standard GCC
 * system) for code which exceeds a specified complexity level
 * according to a specific complexity metric. 
 *
 * Three metrics are provided:
 * - Simple cyclomatic complexity.
 * - 
 */

#include "config.h"
#include "system.h"
#include "coretypes.h"
#include "input.h"
#include "tm.h"
#include "intl.h"
#include "tree.h"
#include "tree-flow.h"
#include "gimple.h"
#include "output.h"
#include "c-common.h"

#include "tree-pass.h"
#include "gcc-plugin.h"

#include <assert.h>

/* --- Forward decls --- */

/* wc_process_function is our entrypoint.  It is called once
 * for each defined function, and analyses that function. */
static unsigned int wc_process_function(void);

/* --- GCC interfacing --- */

/* We have a pass which hooks us into GCC's complilation
 * sequence. */
static struct gimple_opt_pass wc_gimple_pass = {
  {
    GIMPLE_PASS,
    "complexity",
    NULL,
    wc_process_function,
    NULL,
    NULL,
    0,
    PROP_trees,
    PROP_cfg,
    0,
    0,
    0,
    TODO_dump_func
  } 
};

/* We have details of ourselves, provided to GCC at registration
 * time. */
static struct plugin_info wc_info = {
  "complexity $Revision$",
  "test"
};

/* We have our configurable options in a struct. */
#define N_METRICS 3
#define N_LIMITS (N_METRICS * 2)

static const char *metric_names[N_METRICS+1] = 
{
  NULL,
  "cyclomatic",
  "design",
  "jbp-cyclomatic",
};

static struct {
  struct limit {
    int metric;     /* What metric we're talking about. */
    int threshold;  /* The limit. */
    enum {
      action_warn,
      action_error
    } action;   /* What do do when limit exceeded. */
  } limits[N_LIMITS];
} conf;

void parse_arg(const char *metric_name, char *spec)
{
  size_t i;
  struct limit *limit = NULL;
  const char *r;

  for (i = 0; i < N_LIMITS; i++)
  {
    if (conf.limits[i].metric == 0)
    {
      limit = conf.limits + i;
      break;
    }
  }
    
  if (limit == NULL)
    return; /* Ignore excess limits. */

  for (i = 1; i < N_METRICS+1; i++)
  {
    if (strcasecmp(metric_names[i], metric_name) == 0)
      limit->metric = i;
  }

  if (limit->metric == 0)
  {
    fprintf(stderr, "warn-complexity: unknown metric '%s'\n",
            metric_name);
    exit(1); 
  }

  r = strtok(spec, ":");
  if (r == NULL)
  {
    fprintf(stderr, "warn-complexity: malformed action specifier '%s'\n",
            spec);
    exit(1); 
  }

  if (strcasecmp("warn", r) == 0)
    limit->action = action_warn;
  else if (strcasecmp("error", r) == 0)
    limit->action = action_error;
  else
  {
    fprintf(stderr, "warn-complexity: unknown action '%s'\n",
            r);
    exit(1);
  }

  r = strtok(NULL, ":");
  if (r == NULL)
  {
    fprintf(stderr, "warn-complexity: malformed action specifier '%s'\n",
            spec);
    exit(1);
  }

  limit->threshold = atoi(r);
}

/* Finally, we have the definition of the function which GCC calls for
 * all plugins. */
int plugin_init(const char *name, int argc, struct plugin_argument *argv)
{
  struct plugin_pass pass_info = { 0 };

  /* Parse arguments. */
  if (argc == 0)
  {
    char def[] = "warn:20";
    parse_arg("cyclomatic", def); /* Our default. */
  } else {
    while (argc--)
    {
      parse_arg(argv->key, argv->value);
      argv++;
    }
  }

  /* Insert ourselves after the control flow graph has been constructed.
   * This is the most convenient point at which to do our analysis. */
  pass_info.pass = &wc_gimple_pass.pass;
  pass_info.reference_pass_name = "cfg";
  pass_info.ref_pass_instance_number = 0;
  pass_info.pos_op = PASS_POS_INSERT_AFTER;
  register_callback(name, PLUGIN_PASS_MANAGER_SETUP, NULL, &pass_info);

  /* Register our data. */
  register_callback(name, PLUGIN_INFO, NULL, &wc_info);

  return 0;
}

/* --- Interesting stuff --- */

/* Group together what we learned about the code. */
struct complexity_input
{
  unsigned int blocks; /* How many blocks we've seen. */
  unsigned int edges;  /* How many edges we've seen. */
};

/* Process a basic block. */
void wc_process_basic_block(basic_block bb, struct complexity_input *inp)
{
  edge_iterator ei;
  edge e;

  /* Count our leaving edges. */
  FOR_EACH_EDGE(e, ei, bb->succs)
  {
    inp->edges++;
  }
}

/* Process all the information about a function. */
static void wc_check_complexity(struct complexity_input *inp)
{
  size_t i;
  unsigned int cyclomatic_complexity = inp->edges - inp->blocks + 2;

  for (i = 0; i < N_LIMITS; i++)
  {
    unsigned int applicable = 0;
    
    switch (conf.limits[i].metric)
    {
      case 0:
        continue;
      case 1:
        applicable = cyclomatic_complexity;
        break;
      case 2:
        abort();
      case 3:
        abort();
    }

    if (applicable >= conf.limits[i].threshold)
    {
      switch (conf.limits[i].action)
      {
        case action_warn:
          warning(0, "%q+D has %s complexity of %u; maximum is %u",
                  current_function_decl,
                  metric_names[conf.limits[i].metric],
                  applicable,
                  conf.limits[i].threshold);
          break;
        case action_error:
          error("%q+D has %s complexity of %u; maximum is %u",
                current_function_decl,
                metric_names[conf.limits[i].metric],
                applicable,
                conf.limits[i].threshold);
          break;
      }

    }
  }
}

/* Process a function. */
static unsigned int wc_process_function(void)
{
  basic_block bb;
  struct complexity_input inp = { 0 };

  /* Run through all the basic blocks in the function being processed,
   * counting and analysing edges from each. */
  FOR_EACH_BB (bb)
  {
    inp.blocks++;
    wc_process_basic_block(bb, &inp);
  }

  /* Having done so, calculate our complexity. */
  wc_check_complexity(&inp);

  return 0;
}


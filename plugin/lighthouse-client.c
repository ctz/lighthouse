
#include "lighthouse-internal.h"
#include "gcc-plugin.h"

#include <assert.h>

static lh_output out;

static struct gimple_opt_pass lh_gimple_pass;
static void lh_finish_unit(void *unused, void *unused_ud);

static struct plugin_info lh_info = {
  "lighthouse-client 0.1",
  "test"
};

int plugin_is_GPL_compatible = 1;

int plugin_init(struct plugin_name_args *args,
                struct plugin_gcc_version *version)
{
  struct register_pass_info pass_info;
  pass_info.pass = &lh_gimple_pass.pass;

  /* Insert ourselves after the control flow graph has been constructed. */
  pass_info.reference_pass_name = "cfg";
  pass_info.ref_pass_instance_number = 0;
  pass_info.pos_op = PASS_POS_INSERT_AFTER;
  register_callback(args->base_name, PLUGIN_PASS_MANAGER_SETUP, NULL, &pass_info);

  /* And then the final step, where we put the finishing touches to our
   * representation of the tu. */
  register_callback(args->base_name, PLUGIN_FINISH_UNIT, lh_finish_unit, NULL);

  /* Register our data. */
  register_callback(args->base_name, PLUGIN_INFO, NULL, &lh_info);

  lh_output_begin(&out);

  return 0;
}

/* --- UID memos. --- */
void uidm_init(uid_memo *m)
{
  memset(m, 0, sizeof(*m));
}

void uidm_empty(uid_memo *m)
{
  m->next = 0;
}

void uidm_destroy(uid_memo *m)
{
  free(m->v);
  m->v = NULL;
  m->next = 0;
  m->len = 0;
}

void uidm_add(uid_memo *m, unsigned int uid)
{
  if (uidm_has(m, uid))
    return;

  if (m->next == m->len)
  {
    if (m->len)
      m->len *= 2;
    else
      m->len = 16;

    m->v = xrealloc(m->v, sizeof(unsigned int) * m->len);
  }

  m->v[m->next++] = uid;
}

bool uidm_has(const uid_memo *m, unsigned int uid)
{
  size_t i;

  for (i = 0; i < m->next; i++)
  {
    if (uid == m->v[i])
      return true;
  }

  return false;
}

void lh_memo_type(tree type)
{
  static int reentered = 0, stackidx = 0, hi = 0;
  static tree stack[512];
  int i;

  if (uidm_has(&out.typememo, TYPE_UID(type)))
    return;

  /* If we've recursed into another type, add it to the stack. */
  if (reentered)
  {
    assert(stackidx != 512);
    stack[stackidx] = type;
    stackidx++;

    if (stackidx > hi)
      hi = stackidx;
    return;
  }

  /* Note *first* to avoid unhelpful recursion. */
  uidm_add(&out.typememo, TYPE_UID(type));

  stackidx = 0;
  hi = 0;
  reentered = 1;
  xml_type_aggregate(type, INDENT * 2, out.types);
  reentered = 0;

  for (i = 0; i < hi; i++)
  {
    if (uidm_has(&out.typememo, TYPE_UID(stack[i])))
      continue;
    
    uidm_add(&out.typememo, TYPE_UID(stack[i]));

    reentered = 1;
    xml_type_aggregate(stack[i], INDENT * 2, out.types);
    stack[i] = NULL;
    reentered = 0;
  }
}

void lh_memo_decl(tree decl)
{
  if (uidm_has(&out.declmemo, DECL_UID(decl)))
    return;

  uidm_add(&out.declmemo, DECL_UID(decl));
  
  if (out.xdecls == NULL)
  {
    out.xdecls = tmpfile();
    if (!out.xdecls)
    {
      perror("creating temporary file for external declarations");
      exit(EXIT_FAILURE);
    }
  }
  
  xml_generic_decl(decl, INDENT * 4, "external", out.xdecls);
}

static void lh_finish_unit(void *unused, void *unused_ud)
{
  lh_output_finish(&out);
}

static unsigned int lh_finish_fndecl(void)
{
  tree arg;
  basic_block bb;

  uidm_empty(&out.declmemo);

  fprintf(out.functions, "    <function name='%s' location='%s:%d' body-begin='%d' body-end='%d'>\n",
      IDENTIFIER_POINTER(DECL_NAME(current_function_decl)),
      DECL_SOURCE_FILE(current_function_decl),
      DECL_SOURCE_LINE(current_function_decl),
      LOCATION_LINE(DECL_STRUCT_FUNCTION(current_function_decl)->function_start_locus),
      LOCATION_LINE(DECL_STRUCT_FUNCTION(current_function_decl)->function_end_locus));
  
  fprintf(out.functions, "      <returns>\n");
  xml_type_ref(TREE_TYPE(TREE_TYPE(current_function_decl)), 8, out.functions);
  fprintf(out.functions, "      </returns>\n");
  fprintf(out.functions, "      <args%s>\n", (DECL_STRUCT_FUNCTION(current_function_decl)->stdarg) ? " varargs='1'" : "");

  for (arg = DECL_ARGUMENTS(current_function_decl);
       arg;
       arg = TREE_CHAIN(arg))
  {
    xml_generic_decl(arg, 8, "arg", out.functions);
  }
  
  fprintf(out.functions, "      </args>\n");
  fprintf(out.functions, "      <body entrypoint='%d'>\n",
      DECL_STRUCT_FUNCTION(current_function_decl)->cfg->x_entry_block_ptr->next_bb->index);

  /* Output local declarations. */
  xml_local_decls(8, out.functions);

  /* Now run through all the basic blocks, and output statements contained therein. */
  FOR_EACH_BB (bb)
  {
    // gimple_dump_bb(bb, stdout, 2, TDF_VOPS | TDF_MEMSYMS | TDF_TREE | TDF_RAW);
    xml_basic_block(bb, 8, out.functions);
  }

  fprintf(out.functions, "      </body>\n");
  fprintf(out.functions, "      <externals>\n");

  if (out.xdecls)
  {
    rewind(out.xdecls);

    while (1)
    {
      int c;

      if (feof(out.xdecls))
        break;

      c = fgetc(out.xdecls);
      if (c == EOF)
        break;
      fputc(c, out.functions);
    }

    fclose(out.xdecls);
    out.xdecls = NULL;
  }

  fprintf(out.functions, "      </externals>\n");
  fprintf(out.functions, "    </function>\n");
          
  return 0;
}

static struct gimple_opt_pass lh_gimple_pass = {
  {
    GIMPLE_PASS,
    "printer",
    NULL,
    lh_finish_fndecl,
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

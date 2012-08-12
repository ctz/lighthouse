#ifndef LIGHTHOUSE_INTERNAL_H
#define LIGHTHOUSE_INTERNAL_H

#include "config.h"
#include "system.h"
#include "coretypes.h"
#include "input.h"
#include "tm.h"
#include "intl.h"
#include "tree.h"
#include "tree-flow.h"
#include "real.h"

/*
#include "except.h"
#include "flags.h"
#include "output.h"
#include "expr.h"
#include "c-tree.h"
*/

#include "gimple.h"
#include "c-common.h"

#include "tree-pass.h"
#include "gcc-plugin.h"

#include <stdio.h>

/* --- Keeping track of what things we output. */
typedef struct 
{
  unsigned int *v;
  size_t len, next;
} uid_memo;

/* Initializes `m' to an empty set. */
void uidm_init(uid_memo *m);

/* Returns true if `m' contains `uid'. */
bool uidm_has(const uid_memo *m, unsigned int uid);

/* Adds `uid' to `m'. */
void uidm_add(uid_memo *m, unsigned int uid);

/* Obvious meanings... */
void uidm_empty(uid_memo *m);
void uidm_destroy(uid_memo *m);

/* --- Output management. --- */
typedef struct
{
  /* Temporary files used for collecting type definitions and function
   * bodies. */
  FILE *types;
  FILE *functions;
  FILE *xdecls;

  /* Track what type UIDs have been written. */
  uid_memo typememo;
  uid_memo declmemo; /* Only used when inside a fn body. */
} lh_output;

/* XML indentation. */
#define INDENT 2

/* Initializes `lho' by opening temporary files. */
void lh_output_begin(lh_output *lho);

/* Finalizes `lho' by re-reading the temporary contents,
 * integrating their contents into the tu description, and
 * finally killing off the temporaries. */
void lh_output_finish(lh_output *lho);

/* Make a note of the type in the `types' output
 * for later reference. */
void lh_memo_type(tree type);

/* Ditto, but for declarations external to the function. */
void lh_memo_decl(tree decl);

/* --- Writing of GIMPLE statements. --- */

/* Write a single statement. */
void xml_statement(gimple stmt, int indent, FILE *out);

/* Write a basic block, including any statements it contains. */
void xml_basic_block(basic_block bb, int indent, FILE *out);

/* --- Writing of GENERIC trees. --- */

/* Write a representation of a literal. */
void xml_short_constant(tree cst, FILE *out);

/* Write fragment note the source location of the declaration or expression `x'. */
void xml_location(tree x, FILE *out);

/* Write a representation of a reference to a declaration (either binding to a name or
 * for an unnamed temporary.) */
void xml_decl_binding(tree decl, int indent, const char *tag, FILE *out);

/* Write a full representation of a type.  For aggregate types this reduces
 * to a reference. */
void xml_type(tree t, tree decl_opt, int indent, FILE *out);

/* Write a reference representation of an aggregate type (in other words, only
 * point to the type in the table of types -- don't write it longhand.) */
void xml_type_ref(tree t, int indent, FILE *out);

/* Write a full representation of an aggregate type, also outputting 
 * the members (as references if they're further aggregates to
 * avoid cycles). */
void xml_type_aggregate(tree t, int indent, FILE *out);

/* Write an expression. */
void xml_expr(tree expr, int indent, FILE *out);

/* Write an expression represented only by its code. Obviously this
 * is less useful for expressions having arguments. */
void xml_expr_code(enum tree_code code, int indent, FILE *out);

/* Write declaration, including its type and binding. */
void xml_generic_decl(tree decl, int indent, const char *tag, FILE *out);

/* Write declaration of a local. */
void xml_local_decl(tree decl, int indent, FILE *out);

/* Write declaration of an aggregate member. */
void xml_member_decl(tree decl, int indent, FILE *out);

/* Write declarations of all function-local declarations
 * in the current function. */
void xml_local_decls(int indent, FILE *out);

#endif

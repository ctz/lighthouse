
#include "lighthouse-internal.h"
#include <assert.h>

static const char * spc(int i)
{
  static char spc[128];
  memset(spc, ' ', 128);
  assert(i < 128);
  spc[i] = '\0';
  return spc;
}

static const char * xml_node_name(gimple stmt)
{
  switch (gimple_code(stmt))
  {
    case GIMPLE_ASSIGN:
      return "assign";
    case GIMPLE_CALL:
      return "call";
    case GIMPLE_COND:
      return "if";
    case GIMPLE_RETURN:
      return "return";
    case GIMPLE_SWITCH:
      return "switch";
    case GIMPLE_GOTO:
      return "goto";
    case GIMPLE_LABEL:
      return "label";
    case GIMPLE_PREDICT:
      return "branch-prediction";
    case GIMPLE_ASM:
      return "inline-assembler";
    case GIMPLE_EH_DISPATCH:
      return "exception-dispatch";

    default:
      fprintf(stderr, "code is %s\n", gimple_code_name[gimple_code(stmt)]);
      assert(!"unhandled gimple code");
      abort();
      return NULL;
  }
}

static void xml_statement_ops(gimple stmt, int indent, FILE *out)
{
  tree rightmost;
  enum tree_code op;

  switch (gimple_code(stmt))
  {
    case GIMPLE_ASSIGN:
      fprintf(out, "%s<lhs>\n", spc(indent));
      xml_expr(gimple_assign_lhs(stmt), indent + INDENT, out);
      fprintf(out, "%s</lhs>\n", spc(indent));

      if (gimple_num_ops(stmt) == 2) /* unary */
        rightmost = NULL;
      else /* binary */
        rightmost = gimple_assign_rhs2(stmt);
      
      fprintf(out, "%s<rhs>\n", spc(indent));
      indent += INDENT;

      op = gimple_assign_rhs_code(stmt);

      if (TREE_CODE_CLASS(op) == tcc_declaration ||
          TREE_CODE_CLASS(op) == tcc_constant ||
          TREE_CODE_CLASS(op) == tcc_reference ||
          CONVERT_EXPR_CODE_P(op))
      {
        /* Straight assignment. */
        assert(rightmost == NULL);
        xml_expr(gimple_assign_rhs1(stmt), indent, out);
      } else {
        if (rightmost)
        {
          /* lhs = rhs1 op rightmost */
          xml_expr(gimple_assign_rhs1(stmt), indent, out);
          xml_expr_code(gimple_assign_rhs_code(stmt), indent, out);
          xml_expr(rightmost, indent, out);
        } else {
          /* lhs = op rhs1 */
          if (gimple_assign_rhs_code(stmt) != ADDR_EXPR) /* ADDR_EXPR has a subexpression also containing addr-of. */
            xml_expr_code(gimple_assign_rhs_code(stmt), indent, out);
          xml_expr(gimple_assign_rhs1(stmt), indent, out);
        }
      }

      indent -= INDENT;
      fprintf(out, "%s</rhs>\n", spc(indent));
      break;

    case GIMPLE_PREDICT:
      fprintf(out, "%s<%s />\n", spc(indent),
          (gimple_predict_outcome(stmt)) ? "likely" : "unlikely");
      fprintf(out, "%s<predictor>%s</predictor>\n", spc(indent),
          predictor_name(gimple_predict_predictor(stmt)));
      break;

    case GIMPLE_COND:
      xml_expr(gimple_cond_lhs(stmt), indent, out);
      xml_expr_code(gimple_cond_code(stmt), indent, out);
      xml_expr(gimple_cond_rhs(stmt), indent, out);

      /* after cfg pass, we refer back to our basic block to work out
       * the edges this condition creates. */
      {
        basic_block bb = gimple_bb(stmt);
        edge true_edge, false_edge;

        extract_true_false_edges_from_block(bb, &true_edge, &false_edge);
        
        fprintf(out, "%s<then id='%d' />\n", spc(indent), true_edge->dest->index);
        fprintf(out, "%s<else id='%d' />\n", spc(indent), false_edge->dest->index);
      }
      break;

    case GIMPLE_RETURN:
      if (gimple_return_retval(stmt))
        xml_expr(gimple_return_retval(stmt), indent, out);
      break;

    case GIMPLE_SWITCH:
      {
        unsigned int i;
        fprintf(out, "%s<index>\n", spc(indent));
        xml_expr(gimple_switch_index(stmt), indent + INDENT, out);
        fprintf(out, "%s</index>\n", spc(indent));

        for (i = 0; i < gimple_switch_num_labels(stmt); i++)
        {
          tree label = gimple_switch_label(stmt, i);

          if (label == NULL_TREE)
            continue;

          if (CASE_LOW(label) == NULL)
          {
            fprintf(out, "%s<default id='%d'", spc(indent),
                label_to_block(CASE_LABEL(label))->index);
            xml_location(CASE_LABEL(label), out);
            fprintf(out, " />\n");
          } else {
            fprintf(out, "%s<case id='%d'", spc(indent),
                label_to_block(CASE_LABEL(label))->index);
            xml_location(CASE_LABEL(label), out);
            fprintf(out, ">\n");

            if (CASE_HIGH(label))
            {
              fprintf(out, "%s<low-bound>\n", spc(indent + INDENT));
              xml_expr(CASE_LOW(label), indent + INDENT, out);
              fprintf(out, "%s</low-bound>\n", spc(indent + INDENT));
              fprintf(out, "%s<high-bound>\n", spc(indent + INDENT));
              xml_expr(CASE_HIGH(label), indent + INDENT, out);
              fprintf(out, "%s</high-bound>\n", spc(indent + INDENT));
            } else {
              fprintf(out, "%s<exact>\n", spc(indent + INDENT));
              xml_expr(CASE_LOW(label), indent + INDENT + INDENT, out);
              fprintf(out, "%s</exact>\n", spc(indent + INDENT));
            }
            fprintf(out, "%s</case>\n", spc(indent));
          }
        }
      }
      break;

    case GIMPLE_CALL:
      /* If it's a FUNCTION_DECL, write the bound name
       * shorthand.  Otherwise, we write the full tree. */
      if (gimple_call_fndecl(stmt))
      {
        /* Such functions must have a reasonable name. */
        assert(DECL_NAME(gimple_call_fndecl(stmt)));
        fprintf(out, "%s<function name='%s' id='%d' />\n", spc(indent),
            IDENTIFIER_POINTER(DECL_NAME(gimple_call_fndecl(stmt))),
            DECL_UID(gimple_call_fndecl(stmt)));
        lh_memo_decl(gimple_call_fndecl(stmt));

      } else {
        /* Probably called through a fn ptr. */
        xml_expr(gimple_call_fn(stmt), indent, out);
      }

      fprintf(out, "%s<lhs>\n", spc(indent));
      if (gimple_call_lhs(stmt))
        xml_expr(gimple_call_lhs(stmt), indent + INDENT, out);
      else
        fprintf(out, "%s<void />\n", spc(indent + INDENT));
      fprintf(out, "%s</lhs>\n", spc(indent));
      fprintf(out, "%s<args>\n", spc(indent));

      {
        size_t i;

        for (i = 0; i < gimple_call_num_args(stmt); i++)
          xml_expr(gimple_call_arg(stmt, i), indent + INDENT, out);
      }

      fprintf(out, "%s</args>\n", spc(indent));
      break;

    default:
      return;
      
  }

}

void xml_statement(gimple stmt, int indent, FILE *out)
{
  const char *tag = xml_node_name(stmt);

  /* Labels unconditionally start basic blocks.  We convolve
   * the two concepts, so no need to dump these.
   *
   * Also strip branch predictions annotations and
   * inline assembler (we don't care in either case,
   * though this does affect our understanding later!) */
  if (gimple_code(stmt) == GIMPLE_LABEL ||
      gimple_code(stmt) == GIMPLE_PREDICT ||
      gimple_code(stmt) == GIMPLE_ASM)
    return;

  fprintf(out, "%s<%s", spc(indent), tag);

  if (gimple_has_location(stmt))
  {
    expanded_location locus = expand_location(gimple_location(stmt));
    fprintf(out, " location='%s:%d:%d'", locus.file, locus.line, locus.column);
  }

  fprintf(out, ">\n");

  xml_statement_ops(stmt, indent + INDENT, out);

  fprintf(out, "%s</%s>\n", spc(indent), tag);
}

static bool edge_was_already_handled(gimple stmt, edge e)
{
  if (!stmt)
    return false;

  if (gimple_code(stmt) == GIMPLE_COND)
    if (e->flags & EDGE_TRUE_VALUE || e->flags & EDGE_FALSE_VALUE)
      return true;

  if (gimple_code(stmt) == GIMPLE_RETURN)
    return true;

  if (gimple_code(stmt) == GIMPLE_SWITCH)
    return true;

  return false;
}

void xml_basic_block(basic_block bb, int indent, FILE *out)
{
  gimple_stmt_iterator gsi;
  edge_iterator ei;
  edge e;

  fprintf(out, "%s<block id='%d'>\n", spc(indent), bb->index);

  for (gsi = gsi_start_bb(bb);
      !gsi_end_p(gsi);
       gsi_next(&gsi))
  {
    xml_statement(gsi_stmt(gsi), indent + INDENT, out);
  }

  /* Now consider where we go next.
   * -  We might have already output edges.  edge_was_already_handled 
   *    encodes the case where this is true.
   * - Otherwise, we have to output edges from this bb.
   */ 

  FOR_EACH_EDGE(e, ei, bb->succs)
  {
    if (edge_was_already_handled(last_stmt(bb), e))
      continue;

    fprintf(out, "%s<next id='%d'", spc(indent + INDENT), e->dest->index);
    if (e->flags & EDGE_ABNORMAL)
      fprintf(out, " abnormal='1'");
    if (e->flags & EDGE_ABNORMAL_CALL)
      fprintf(out, " abnormal-call='1'");
    if (e->flags & EDGE_LOOP_EXIT)
      fprintf(out, " loop-exit='1'");
    if (e->flags & EDGE_EH)
      fprintf(out, " exceptional='1'");
    fprintf(out, " />\n");
  }

  fprintf(out, "%s</block>\n", spc(indent));
}


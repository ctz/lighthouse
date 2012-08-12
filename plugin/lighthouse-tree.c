
#include "lighthouse-internal.h"

#include <assert.h>

static long long double_int_to_ll(double_int di)
{
  /* XXX: this is really no good. should just print the thing correctly. */
#if (HOST_BITS_PER_WIDE_INT == 64)
  return di.low;
#else
  return di.low + (di.high << HOST_BITS_PER_WIDE_INT);
#endif
}

/* Returns true if the bound (higher for nonzero hi, otherwise lower)
 * of `cst' is not the bound implied by the type's precision and signedness. */
static bool integer_cst_interesting(tree cst, int hi)
{
  return true;
#if 0
  long long implicit_bound, explicit_bound;
  
  if (TYPE_UNSIGNED(cst))
    implicit_bound = (1 << TYPE_PRECISION(cst)) - 1;
  else
    implicit_bound = (1 << (TYPE_PRECISION(cst) - 1)) - 1;

  if (TYPE_UNSIGNED(cst) && TYPE_PRECISION(cst) / 8 == sizeof(implicit_bound))
    implicit_bound = (long long) -1;

  if (!hi)
  {
    if (TYPE_UNSIGNED(cst))
      implicit_bound = 0;
    else
      implicit_bound = -implicit_bound-1;
  }

  explicit_bound = (hi) ? double_int_to_ll(TREE_INT_CST(TYPE_MAX_VALUE(cst))) :
                          double_int_to_ll(TREE_INT_CST(TYPE_MIN_VALUE(cst)));

  return explicit_bound != implicit_bound;
#endif
}

static const char * spc(int i)
{
  static char spc[128];
  memset(spc, ' ', 128);
  assert(i < 128);
  spc[i] = '\0';
  return spc;
}

static const char * filter_built_in(const char *in)
{
  if (in == NULL || 0 == strcmp(in, "<built-in>"))
    return "&lt;built-in&gt;";
  return in;
}

void xml_location(tree x, FILE *out)
{
  expanded_location l;
  if (!CAN_HAVE_LOCATION_P(x) && !DECL_P(x)) 
    return;

  if (EXPR_P(x))
  {
    l = expand_location(EXPR_LOCATION(x));
    goto write;
  } else if (DECL_P(x)) {
    l = expand_location(DECL_SOURCE_LOCATION(x));
    goto write;
  }

  return;

write:
  fprintf(out, " location='%s:%d:%d'",
     filter_built_in(l.file), l.line, l.column); 
}

void xml_expr(tree expr, int indent, FILE *out)
{
  size_t el;

  switch (TREE_CODE(expr))
  {
    case REAL_CST:
    case STRING_CST:
    case INTEGER_CST:
      fprintf(out, "%s<constant>\n", spc(indent));

      /* For strings, we output the full type here. The backend should be fixed to resolve this though. */
      if (TREE_CODE(expr) == STRING_CST)
        xml_type_aggregate(TREE_TYPE(expr), indent + INDENT, out);
      else
        xml_type(TREE_TYPE(expr), NULL, indent + INDENT, out);
      fprintf(out, "%s", spc(indent + INDENT));
      xml_short_constant(expr, out);
      fprintf(out, "\n%s</constant>\n", spc(indent));
      break;

    case COMPONENT_REF:
      fprintf(out, "%s<member-ref>\n", spc(indent));
      fprintf(out, "%s<structure>\n", spc(INDENT + indent));
      xml_expr(TREE_OPERAND(expr, 0), indent + INDENT + INDENT, out);
      fprintf(out, "%s</structure>\n", spc(indent + INDENT));
      fprintf(out, "%s<member>\n", spc(indent + INDENT));
      xml_decl_binding(TREE_OPERAND(expr, 1), indent + INDENT + INDENT, "bound", out);
      fprintf(out, "%s</member>\n", spc(indent + INDENT));
      fprintf(out, "%s</member-ref>\n", spc(indent));
      break;

    case BIT_FIELD_REF:
      fprintf(out, "%s<bitfield-ref>\n", spc(indent));
      fprintf(out, "%s<structure>\n", spc(INDENT + indent));
      xml_expr(TREE_OPERAND(expr, 0), indent + INDENT + INDENT, out);
      fprintf(out, "%s</structure>\n", spc(indent + INDENT));
      assert(TREE_OPERAND(expr, 1) != NULL);
      assert(TREE_OPERAND(expr, 2) != NULL);
      assert(INTEGER_CST == TREE_CODE(TREE_OPERAND(expr, 1)));
      assert(INTEGER_CST == TREE_CODE(TREE_OPERAND(expr, 2)));
      fprintf(out, "%s<bits start='%lld' size='%lld' />", spc(indent + INDENT),
          double_int_to_ll(TREE_INT_CST(TREE_OPERAND(expr, 1))),
          double_int_to_ll(TREE_INT_CST(TREE_OPERAND(expr, 2))));
      fprintf(out, "%s<as-type>\n", spc(INDENT + indent));
      assert(TREE_TYPE(expr) != NULL);
      xml_type(TREE_TYPE(expr), NULL, indent + INDENT + INDENT, out);
      fprintf(out, "%s</as-type>\n", spc(indent + INDENT));
      fprintf(out, "%s</bitfield-ref>\n", spc(indent));
      break;

    case INDIRECT_REF:
      fprintf(out, "%s<indirection>\n", spc(indent));
      xml_expr(TREE_OPERAND(expr, 0), indent + INDENT, out);
      fprintf(out, "%s</indirection>\n", spc(indent));
      break;

    case RESULT_DECL:
      xml_decl_binding(expr, indent, "result", out);
      break;

    case VAR_DECL:
      xml_decl_binding(expr, indent, "bound", out);
      break;

    case PARM_DECL:
      xml_decl_binding(expr, indent, "bound-parameter", out);
      break;

    case ADDR_EXPR:
      fprintf(out, "%s<addr-of>\n", spc(indent));
      xml_expr(TREE_OPERAND(expr, 0), indent + INDENT, out);
      fprintf(out, "%s</addr-of>\n", spc(indent));
      break;

    case FUNCTION_DECL:
      fprintf(out, "%s<function>\n", spc(indent));
      xml_decl_binding(expr, indent + INDENT, "bound", out);
      fprintf(out, "%s</function>\n", spc(indent));
      break;

#define SIMPLE_TAG(when, tt) \
    case when: \
      fprintf(out, "%s<" tt " />\n", spc(indent)); \
      break
   
#define SIMPLE_TAGS \
    SIMPLE_TAG(PLUS_EXPR, "plus");\
    SIMPLE_TAG(MINUS_EXPR, "minus");\
    SIMPLE_TAG(MULT_EXPR, "multiply");\
    SIMPLE_TAG(POINTER_PLUS_EXPR, "pointer-offset");\
    \
    SIMPLE_TAG(TRUNC_DIV_EXPR, "division-truncate");\
    SIMPLE_TAG(CEIL_DIV_EXPR, "division-ceil");\
    SIMPLE_TAG(FLOOR_DIV_EXPR, "division-floor");\
    SIMPLE_TAG(ROUND_DIV_EXPR, "division-round");\
    SIMPLE_TAG(EXACT_DIV_EXPR, "division-exact");\
    SIMPLE_TAG(RDIV_EXPR, "division-real");\
    \
    SIMPLE_TAG(TRUNC_MOD_EXPR, "modulo-truncate");\
    SIMPLE_TAG(CEIL_MOD_EXPR, "modulo-ceil");\
    SIMPLE_TAG(FLOOR_MOD_EXPR, "modulo-floor");\
    SIMPLE_TAG(ROUND_MOD_EXPR, "modulo-round");\
    \
    SIMPLE_TAG(FLOAT_EXPR, "float");\
    SIMPLE_TAG(FIX_TRUNC_EXPR, "fixed-point-truncate");\
    SIMPLE_TAG(NEGATE_EXPR, "negate");\
    SIMPLE_TAG(ABS_EXPR, "absolute");\
    \
    SIMPLE_TAG(LSHIFT_EXPR, "shift-left");\
    SIMPLE_TAG(RSHIFT_EXPR, "shift-right");\
    SIMPLE_TAG(LROTATE_EXPR, "rotate-left");\
    SIMPLE_TAG(RROTATE_EXPR, "rotate-right");\
    \
    SIMPLE_TAG(BIT_IOR_EXPR, "bitwise-or");\
    SIMPLE_TAG(BIT_XOR_EXPR, "bitwise-xor");\
    SIMPLE_TAG(BIT_AND_EXPR, "bitwise-and");\
    SIMPLE_TAG(BIT_NOT_EXPR, "bitwise-not");\
    \
    SIMPLE_TAG(MIN_EXPR, "min");\
    SIMPLE_TAG(MAX_EXPR, "max");\
    SIMPLE_TAG(UNORDERED_EXPR, "unordered");\
    SIMPLE_TAG(ORDERED_EXPR, "ordered");\
    \
    SIMPLE_TAG(TRUTH_ANDIF_EXPR, "logical-short-and");\
    SIMPLE_TAG(TRUTH_ORIF_EXPR, "logical-short-or");\
    SIMPLE_TAG(TRUTH_AND_EXPR, "logical-and");\
    SIMPLE_TAG(TRUTH_OR_EXPR, "logical-or");\
    SIMPLE_TAG(TRUTH_XOR_EXPR, "logical-xor");\
    SIMPLE_TAG(TRUTH_NOT_EXPR, "logical-not");\
    \
    SIMPLE_TAG(LT_EXPR, "less-than");\
    SIMPLE_TAG(LE_EXPR, "less-than-or-equal");\
    SIMPLE_TAG(GT_EXPR, "greater-than");\
    SIMPLE_TAG(GE_EXPR, "greater-than-or-equal");\
    SIMPLE_TAG(EQ_EXPR, "equal");\
    SIMPLE_TAG(NE_EXPR, "not-equal");\
    SIMPLE_TAG(NOP_EXPR, "nop-convert");\
    SIMPLE_TAG(CONVERT_EXPR, "convert");

    SIMPLE_TAGS

#undef SIMPLE_TAG

    case ARRAY_REF:
      fprintf(out, "%s<item-ref>\n", spc(indent));
      fprintf(out, "%s<array>\n", spc(INDENT + indent));
      xml_expr(TREE_OPERAND(expr, 0), indent + INDENT + INDENT, out);
      fprintf(out, "%s</array>\n", spc(INDENT + indent));
      fprintf(out, "%s<index>\n", spc(indent + INDENT));
      xml_expr(TREE_OPERAND(expr, 1), indent + INDENT + INDENT, out);
      fprintf(out, "%s</index>\n", spc(indent + INDENT));
      fprintf(out, "%s</item-ref>\n", spc(indent));
      break;

    case CONSTRUCTOR:
      fprintf(out, "%s<constructor>\n", spc(indent));
      
      for (el = 0; el < CONSTRUCTOR_NELTS(expr); el++)
      {
        xml_expr(CONSTRUCTOR_ELT(expr, el)->value, indent + INDENT, out);
      }

      fprintf(out, "%s</constructor>\n", spc(indent));
      break;

    case REFERENCE_TYPE:
      fprintf(stderr, "lighthouse warning: ignoring unhandled expression tree type %s\n",
          tree_code_name[TREE_CODE(expr)]);
      break;

    default:
      fprintf(stderr, "xml_expr: unhandled expression tree type %s\n",
          tree_code_name[TREE_CODE(expr)]);
      assert(0);
      abort();
  } 
}

void xml_expr_code(enum tree_code code, int indent, FILE *out)
{
  switch (code)
  {
#define SIMPLE_TAG(expr, tag) \
    case (expr): \
      fprintf(out, "%s<" tag " />\n", spc(indent)); \
      break

  SIMPLE_TAGS
    SIMPLE_TAG(CONSTRUCTOR, "constructed");

#undef SIMPLE_TAG
    default:
      fprintf(stderr, "xml_tree_expr_code: unhandled expression tree type %s\n",
          tree_code_name[code]);
      abort();
      break;
  }
}

static void xml_type_quals(unsigned int quals, FILE *out)
{
  if (quals & TYPE_QUAL_CONST)
    fprintf(out, " constant='1'");
  if (quals & TYPE_QUAL_VOLATILE)
    fprintf(out, " volatile='1'");
  if (quals & TYPE_QUAL_RESTRICT)
    fprintf(out, " restrict='1'");
}

static void xml_type_attribs(tree attribs, const char *extra, FILE *out)
{
  bool output = (attribs != NULL || extra);

  if (output)
    fprintf(out, " attributes='");

  if (extra)
  {
    fputs(extra, out);

    if (attribs)
      fputs(",", out);
  }

  for (; attribs; attribs = TREE_CHAIN(attribs))
  {
    tree attr = TREE_PURPOSE(attribs);

    if (TREE_CODE(attr) != IDENTIFIER_NODE)
      printf("unhandled attrib type: %s\n", tree_code_name[TREE_CODE(attr)]);
    else
      fprintf(out, "%s", IDENTIFIER_POINTER(attr));
    
    if (TREE_CHAIN(attribs))
      fprintf(out, ",");
  }

  if (output)
    fprintf(out, "'");
}

static void xml_type_name(tree tn, FILE *out)
{
  /* anon types. */
  if (!tn)
    return;

  /* named types. */
  if (TREE_CODE(tn) == IDENTIFIER_NODE)
    fprintf(out, " name='%s'", IDENTIFIER_POINTER(tn));

  /* typedefs. */
  if (TREE_CODE(tn) == TYPE_DECL && DECL_NAME(tn))
    fprintf(out, " name='%s'", IDENTIFIER_POINTER(DECL_NAME(tn)));
}

void xml_type_ref(tree t, int indent, FILE *out)
{
  const char *tag;
  
  /* For non-aggregates, just print the type.  It can't
   * be that bad. */
  if (!AGGREGATE_TYPE_P(t))
    return xml_type(t, NULL, indent, out);

  switch (TREE_CODE(t))
  {
    case UNION_TYPE:
      tag = "union";
      goto write;

    case RECORD_TYPE:
      tag = "structure";
      goto write;

    case ARRAY_TYPE:
      tag = "array";
      goto write;

    default:
      abort();
  }

write:
  lh_memo_type(t);
  fprintf(out, "%s<%s id='%u'", spc(indent), tag, TYPE_UID(t));
  xml_type_quals(TYPE_QUALS(t), out);
  xml_location(t, out);
  fprintf(out, "/>\n");
}

void xml_type_aggregate(tree t, int indent, FILE *out)
{
  tree member;
  const char *tag = NULL;

  switch (TREE_CODE(t))
  {
    case UNION_TYPE:
      tag = "union";
    case RECORD_TYPE:
      if (!tag) tag = "structure";
      fprintf(out, "%s<%s id='%d'", spc(indent), tag, TYPE_UID(t));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      fprintf(out, ">\n");

      for (member = TYPE_FIELDS(t);
           member;
           member = TREE_CHAIN(member))
      {
        xml_member_decl(member, indent + INDENT, out);
      }
      
      fprintf(out, "%s</%s>\n", spc(indent), tag);
      break;

    case ARRAY_TYPE:
      fprintf(out, "%s<array id='%d'", spc(indent), TYPE_UID(t));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      fprintf(out, ">\n");
      fprintf(out, "%s<type>\n", spc(indent + INDENT));
      xml_type(TREE_TYPE(t), NULL, indent + INDENT + INDENT, out);
      fprintf(out, "%s</type>\n", spc(indent + INDENT));
      if (TYPE_DOMAIN(t))
      {
        fprintf(out, "%s<domain>\n", spc(indent + INDENT));
        xml_type(TYPE_DOMAIN(t), NULL, indent + INDENT + INDENT, out);
        fprintf(out, "%s</domain>\n", spc(indent + INDENT));
      }
      fprintf(out, "%s</array>\n", spc(indent));
      break;

    default:
      abort();
  }
}

void xml_type(tree t, tree opt_decl, int indent, FILE *out)
{
  tree a = NULL;

  if (AGGREGATE_TYPE_P(t))
    return xml_type_ref(t, indent, out);

  switch (TREE_CODE(t))
  {
    case POINTER_TYPE:
      fprintf(out, "%s<addr-of", spc(indent));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      fprintf(out, ">\n");
      xml_type(TREE_TYPE(t), NULL, indent + INDENT, out);
      fprintf(out, "%s</addr-of>\n", spc(indent));
      break;

    case REAL_TYPE:
      fprintf(out, "%s<float", spc(indent));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      fprintf(out, " precision='%d'", TYPE_PRECISION(t));
      fprintf(out, " />\n");
      break;

    case INTEGER_TYPE:
      fprintf(out, "%s<integer", spc(indent));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      if (TYPE_UNSIGNED(t))
        fprintf(out, " unsigned='1'");
      fprintf(out, " precision='%d'", TYPE_PRECISION(t));
      
      /* TREE_TYPE here indicates that there is an interesting domain. */
      if (TREE_TYPE(t) && TYPE_MIN_VALUE(t))
        fprintf(out, (TYPE_UNSIGNED(t) ? " min='%llu'" : " min='%lld'"), double_int_to_ll(TREE_INT_CST(TYPE_MIN_VALUE(t))));
      if (TREE_TYPE(t) && TYPE_MAX_VALUE(t))
        fprintf(out, (TYPE_UNSIGNED(t) ? " max='%llu'" : " max='%lld'"), double_int_to_ll(TREE_INT_CST(TYPE_MAX_VALUE(t))));
      fprintf(out, " />\n");
      break;

    case VOID_TYPE:
      fprintf(out, "%s<void />\n", spc(indent));
      break;

    case BOOLEAN_TYPE:
      fprintf(out, "%s<boolean />\n", spc(indent));
      break;
    
    case RESULT_DECL:
      fprintf(out, "%s<result />\n", spc(indent));
      break;

    case ENUMERAL_TYPE:
      /* TODO: finish this (output tags). */
      fprintf(out, "%s<enum", spc(indent));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      fprintf(out, " />\n");
      break;

    case METHOD_TYPE:
    case FUNCTION_TYPE:
      fprintf(out, "%s<function", spc(indent));
      xml_type_quals(TYPE_QUALS(t), out);
      xml_type_name(TYPE_NAME(t), out);
      xml_type_attribs(TYPE_ATTRIBUTES(t),
          (opt_decl && TREE_THIS_VOLATILE(opt_decl)) ? "noreturn" : NULL,
          out);
      indent += INDENT;
      fprintf(out, ">\n%s<return>\n", spc(indent));
      xml_type(TREE_TYPE(t), NULL, indent + INDENT, out);
      fprintf(out, "%s</return>\n", spc(indent));

      /* varargs if last is not void. */
      for (a = TYPE_ARG_TYPES(t); a && TREE_CHAIN(a); a = TREE_CHAIN(a))
        ;
      
      fprintf(out, "%s<arguments %s>\n", spc(indent), 
          (!a || TREE_CODE(TREE_VALUE(a)) == VOID_TYPE) ? "" : "varargs='1' ");
      
      for (a = TYPE_ARG_TYPES(t); a; a = TREE_CHAIN(a))
      {
        xml_type(TREE_VALUE(a), NULL, indent + INDENT, out);
      }
        
      fprintf(out, "%s</arguments>\n", spc(indent));
      indent -= INDENT;
      fprintf(out, "%s</function>\n", spc(indent));
      break;

    case REFERENCE_TYPE:
      fprintf(stderr, "lighthouse warning: ignoring unhandled tree type '%s'.\n",
              tree_code_name[TREE_CODE(t)]);
      break;

    default:
      fprintf(stderr, "failing: unhandled tree type %s\n",
          tree_code_name[TREE_CODE(t)]);
      assert(0);
      abort();
  }
}

void xml_short_constant(tree cst, FILE *out)
{
  size_t i;
  const char *p;
  char buf[100];
  REAL_VALUE_TYPE rt;

  switch (TREE_CODE(cst))
  {
    case REAL_CST:
      rt = TREE_REAL_CST(cst);

      if (REAL_VALUE_ISINF(rt))
        fprintf(out, "<float-literal special='%sInfinity' />",
            REAL_VALUE_NEGATIVE(rt) ? "-" : "+");
      else if (REAL_VALUE_ISNAN(rt))
        fprintf(out, "<float-literal special='NaN' />");
      else
      {
        real_to_decimal(buf, &rt, sizeof(buf), 0, 1);
        fprintf(out, "<float-literal value='%s' />", buf);
      }
      break;

    case INTEGER_CST:
      fprintf(out, "<integer-literal value='%lld' />", double_int_to_ll(TREE_INT_CST(cst)));
      break;

    case STRING_CST:
      fprintf(out, "<string-literal>");
      p = TREE_STRING_POINTER(cst);

      for (i = 0; i < TREE_STRING_LENGTH(cst); i++)
      {
        if (p[i] == '\\')
          fputc('\\', out), fputc('\\', out);
        else if (p[i] == '&')
          fputs("&amp;", out);
        else if (p[i] == '<')
          fputs("&lt;", out);
        else if (p[i] == '>')
          fputs("&gt;", out);
        else if (ISPRINT(p[i]))
          fputc(p[i], out);
        else
          fprintf(out, "\\x%02x", p[i] & 0xFF);
      }

      fprintf(out, "</string-literal>");
      break;

    default:
      fprintf(stderr, "failing: unhandled cst tree type %s\n",
          tree_code_name[TREE_CODE(cst)]);
      abort();
  }
}

static bool decl_file_scope(tree decl)
{
  return (DECL_CONTEXT(decl) == NULL_TREE ||
          TREE_CODE(DECL_CONTEXT(decl)) == TRANSLATION_UNIT_DECL);
}

static const char * decl_special_scope(tree decl)
{
  if (decl_file_scope(decl))
  {
    if (TREE_STATIC(decl))
      return "scope='file' ";
    else
      return "scope='global' ";
  }

  if (TREE_STATIC(decl))
    return "scope='static' ";
  return "";
}

void xml_decl_binding(tree decl, int indent, const char *tag, FILE *out)
{
  if (decl_file_scope(decl))
    lh_memo_decl(decl);

#if 0
  if (DECL_NAME(decl) && (0 == strcmp(tag, "binding")|| decl_file_scope(decl)))
    fprintf(out, "%s<%s name='%s' id='%d' %s/>\n", spc(indent), tag,
        IDENTIFIER_POINTER(DECL_NAME(decl)), DECL_UID(decl),
        decl_special_scope(decl));
  else
#endif
  
  fprintf(out, "%s<%s id='%d'", spc(indent), tag, DECL_UID(decl));
  
  if (0 == strcmp(tag, "binding") && DECL_NAME(decl))
    fprintf(out, " name='%s'", IDENTIFIER_POINTER(DECL_NAME(decl)));
  fprintf(out, " />\n");
}

/* Output a declaration.  Used for function locals, and struct/union members. */
void xml_generic_decl(tree decl, int indent, const char *tag, FILE *out)
{
  fprintf(out, "%s<%s", spc(indent), tag);
  xml_location(decl, out);
  fprintf(out, ">\n");
  indent += INDENT;

  xml_decl_binding(decl, indent, "binding", out);

  fprintf(out, "%s<type", spc(indent));
  if (DECL_SIZE(decl))
    fprintf(out, " size='%lu'", TREE_INT_CST_LOW(DECL_SIZE(decl)));
  if (DECL_ALIGN(decl))
    fprintf(out, " alignment='%d'", DECL_ALIGN(decl));
  fprintf(out, ">\n");

  /* Output the type. */
  xml_type(TREE_TYPE(decl), decl, indent + INDENT, out);
  
  fprintf(out, "%s</type>\n", spc(indent));
  
  if (TREE_CODE(decl) == VAR_DECL && DECL_INITIAL(decl))
  {
    fprintf(out, "%s<initial>\n", spc(indent));
    xml_expr(DECL_INITIAL(decl), indent + INDENT, out);
    fprintf(out, "%s</initial>\n", spc(indent));
  }

  indent -= INDENT;
  fprintf(out, "%s</%s>\n", spc(indent), tag);
}

void xml_local_decl(tree decl, int indent, FILE *out)
{
  xml_generic_decl(decl, indent, "local", out);
}

void xml_member_decl(tree decl, int indent, FILE *out)
{
  xml_generic_decl(decl, indent, "member", out);
}

void xml_local_decls(int indent, FILE *out)
{
  tree var;
  fprintf(out, "%s<locals>\n", spc(indent));
  indent += INDENT;
  
  for (var = DECL_STRUCT_FUNCTION(current_function_decl)->local_decls;
       var;
       var = TREE_CHAIN(var))
    xml_local_decl(TREE_VALUE(var), indent, out);
  
  indent -= INDENT;
  fprintf(out, "%s</locals>\n", spc(indent));
}

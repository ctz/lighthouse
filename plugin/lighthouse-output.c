
#include "lighthouse-internal.h"
#include <assert.h>

static void start(FILE **f, const char *what_for)
{
  *f = tmpfile();
  if (!*f)
  {
    perror(what_for);
    exit(EXIT_FAILURE);
  }
}

void lh_output_begin(lh_output *lho)
{
  start(&lho->types, "creating temporary file for types");
  start(&lho->functions, "creating temporary file for function bodies");
#if 0
  start(&lho->xdecls, "creating temporary file for external declarations");
#endif 

  uidm_init(&lho->typememo);
  uidm_init(&lho->declmemo);
}

void dump(FILE *out, FILE *in)
{
  while (!feof(in))
  {
    int i = fgetc(in);
    if (i != EOF)
      fputc(i, out);
  }
}

void dump_raw(FILE *out, FILE *in)
{
  while (!feof(in))
  {
    int i = fgetc(in);
    if (i == EOF)
      break;
    else if (i == '>')
      fputs("&gt;", out);
    else if (i == '<')
      fputs("&lt;", out);
    else if (i == '&')
      fputs("&amp;", out);
    else if (isascii(i))
      fputc(i, out);
    else
      fprintf(out, "&#%d;", i);
  }
}

static void lh_child(int fd)
{
  /* Replace our stdin with the pipe. */
  close(STDIN_FILENO);
  dup2(fd, STDIN_FILENO);

  if (-1 == execlp("lh-pipe", "lh-pipe", main_input_filename, NULL))
  {
    perror("lighthouse child exec failed");
    exit(EXIT_FAILURE);
  }
}

static FILE * lh_spawn_output_prog(void)
{
  /* Make a pipe to talk to our child-to-be. */
  int pipefds[2];
  int e;
  FILE *rc;

  if (-1 == pipe(pipefds))
  {
    perror("lighthouse pipe open failed");
    exit(EXIT_FAILURE);
  }

  /* Fork. */
  e = fork();

  switch (e)
  {
    case 0:
      close(pipefds[1]);
      lh_child(pipefds[0]);
      abort();
      break;

    case -1:
      perror("lighthouse fork failed");
      exit(EXIT_FAILURE);
      break;

    default:
      break;
  }

  close(pipefds[0]);
  rc = fdopen(pipefds[1], "w");
  if (rc == NULL)
  {
    perror("lighthouse child pipe fdopen failed");
    exit(EXIT_FAILURE);
  }

  return rc; 
}

void lh_output_finish(lh_output *lho)
{
  char mif[FILENAME_MAX] = { 0 };
  int child_rc;
  FILE *f, *src;

  assert(lho);
  assert(lho->types);
  assert(lho->functions);

  rewind(lho->types);
  rewind(lho->functions);

  assert(strlen(main_input_filename) < FILENAME_MAX);
  memcpy(mif, main_input_filename, strlen(main_input_filename));

  f = lh_spawn_output_prog();
  if (!f)
  {
    perror("opening output file");
    exit(EXIT_FAILURE);
  }

  src = fopen(main_input_filename, "r");
  if (!src)
  {
    perror("reopening input file");
    exit(EXIT_FAILURE);
  }

  fprintf(f, "<?xml version='1.0' encoding='UTF-8'?>\n");
  fprintf(f, "\n");
  fprintf(f, "<lh-translation-unit filename='%s' language='%s' client-version='%s'>\n",
      main_input_filename,
      (c_language == clk_c) ? "C" : "C++",
      LH_CLIENT_VERSION);
  fprintf(f, "  <raw-source>");
  dump_raw(f, src);
  fprintf(f, "</raw-source>\n");
  fprintf(f, "  <referenced-types>\n");
  dump(f, lho->types);
  fprintf(f, "  </referenced-types>\n");
  fprintf(f, "  <function-bodies>\n");
  dump(f, lho->functions);
  fprintf(f, "  </function-bodies>\n");
  fprintf(f, "</lh-translation-unit>\n");

  fclose(lho->types);
  fclose(lho->functions);
  fclose(f);
  fclose(src);

  wait(&child_rc);

  if (WEXITSTATUS(child_rc))
  {
    printf("lighthouse-plugin: child exited non-zero (%d)\n", WEXITSTATUS(child_rc));
    exit(EXIT_FAILURE);
  }
}

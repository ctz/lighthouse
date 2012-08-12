#include <stdio.h>
#include <stdarg.h>
#include <assert.h>

static int xyz = 2;
static float fx = 1.03;
static struct { int x, y; } zyx = { 1, 2 };

static void ksa(unsigned char state[], unsigned char key[], int len)
{
   int i,j=0,t; 

   t = zyx.y;
   
   for (i=0; i < 256; ++i)
      state[i] = i; 
   for (i=0; i < 256; ++i) {
      j = (j + state[i] + key[i % len]) % 256; 
      t = state[i]; 
      state[i] = state[j]; 
      state[j] = t; 
   }   
}

static void prga(unsigned char state[], unsigned char out[], int len)
{  
   int i=0,j=0,x,t; 
   static unsigned char key; 
   
   for (x=0; x < len; ++x)  {
      i = (i + 1) % 256; 
      j = (j + state[i]) % 256; 
      t = state[i]; 
      state[i] = state[j]; 
      state[j] = t; 
      out[x] = state[(state[i] + state[j]) % 256];
   }   
}  

static const char *get_location(const char *loc)
{
  return loc;
}

static void do_stuff(const char **abc)
{
  FILE *f = fopen("/dev/null", "r");
  assert(f != NULL);
  assert(f);
  fclose(f);
  abc++;
}

static void expressions(void)
{
  int x;
  long y;
  int (*thing)(const char *t, ...) = printf;
  int z[3];
  int u[3] = { 1, 2, 3};

  y = x * xyz * fx;
  y = x / 2;
  y = (long) &x;
  y = x < 1;
  y = x <= 1;
  y = x > 0;
  y = x == 0;
  y = x != 0;
  y = !x;
  y = z[0];
  y = x >= 1;
  y += 1;
  y -= 1;
  y++;
  y += 1.2f;
  y--;
  *z += 1;
  *z += 1;
  thing("test");
  z[0] = x;
  *z = 2;
  *(z+1) = 2;
  *z = 1;
}

static void control_structures(void)
{
  volatile int y = 2;

  if (y == 2)
    printf("two");
  else
    if (y == 3)
      printf("impossible");

  switch (y)
  {
    case 1:
      printf("inconceivable");
    case 3:
      printf("impossible");
      break;
    case 2:
      printf("two");
      break;
    default:
      printf("also hard");
      break;
  }

  if (y == 2)
    printf("two");

  for (y = 0; y < 2; y++)
  {
    long long n = 4;

    if (y == n)
      continue;
    if (y == 2)
      break;
    printf("a");
  }

  if (y == 2 || main())
  {
    printf("ok");
  }

  do
  {
    int n = 6;
    printf("a");
  }
  while (0);

  while (1)
  {
    printf("a");
    if (1)
      break;
  }

  goto abc;

xyz:
  printf("abc");
  return;

abc:
  goto xyz;

}

extern int global;
int global = 5;
static int file_local;

static void scoping(void)
{
  int local;
  static int function_local;
  local = global;
  function_local = file_local;
}

static void varargs(const char *fmt, ...)
{
  va_list vl;

  va_start(vl, fmt);

  while (*fmt)
  {
    int y = va_arg(vl, int);
    printf("arg = %d\n", y);
    fmt++;
  }

  va_end(vl);
}

int main(void)
{
  struct {
    int x, y, z;
  } v = { 0, 1, 2 };
  printf("hello %s! %p\n", get_location("world"), &v);
  do_stuff((const char **) &"hello");
  expressions();
  control_structures();
  scoping();
  varargs("abc", 1, 2, 3);
  return 0;
}

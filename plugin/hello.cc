#include <stdio.h>

class base
{
public:
  virtual void hello() = 0;
};

class thing : public base
{
public:
  virtual void hello()
  {
    printf("hello ");
  }

  void world()
  {
    printf("world\n");
    throw 10;
  }
};


int main(void)
{
  thing c;
  c.hello();

  try
  {
    c.world();
  } catch (int e) {
  } catch (...) {
  }
  return 0;
}

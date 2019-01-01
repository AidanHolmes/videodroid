#ifndef __ARDUINO_SERIAL_COMMAND
#define __ARDUINO_SERIAL_COMMAND
#include <stddef.h>

#define FNCALL(fn) void (*fn)(int)

class Command{
public:
  Command(const char *szcmd, FNCALL(fn) = NULL,  bool auto_reset = false);
  bool found(char c);
  bool found();
  void cmd(int val);
  void reset();
  const char *name(){return m_sz;}
protected:
  bool m_bautoreset ;
  bool m_bmatchfailed ;
  const char *m_sz ;
  const char *m_p ;
  FNCALL(m_fn) ;
};
  
#endif

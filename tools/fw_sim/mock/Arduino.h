#pragma once
#include <cstdint>
#include <cstdio>
#include <cmath>
#include <cstring>
#include <string>
#define F(x) (x)
#define D1 5
#define D2 4
extern unsigned long g_ms;
inline void delay(unsigned long ms){ g_ms += ms; }
inline unsigned long millis(){ return g_ms; }
inline char* dtostrf(double v, signed char w, unsigned char p, char* out){ sprintf(out, "%*.*f", w, p, v); return out; }
struct SerialMock {
  std::string line; bool quiet=true;
  void begin(long){}
  void flushLine(){ if(!quiet) printf("%s\n", line.c_str()); line.clear(); }
  void print(const char* s){ line += s; }
  void print(char c){ line += c; }
  void print(int v){ line += std::to_string(v); }
  void print(unsigned v){ line += std::to_string(v); }
  void print(long v){ line += std::to_string(v); }
  void print(unsigned long v){ line += std::to_string(v); }
  void print(double v, int d=2){ char b[64]; snprintf(b,64,"%.*f",d,v); line += b; }
  template<class T> void println(T v){ print(v); flushLine(); }
  void println(double v, int d){ print(v,d); flushLine(); }
  void println(){ flushLine(); }
};
extern SerialMock Serial;

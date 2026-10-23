#pragma once
#include "Arduino.h"
struct LiquidCrystal_I2C {
  char rows[2][17]; int r=0,c=0;
  LiquidCrystal_I2C(uint8_t,int,int){ clear(); }
  void init(){} void backlight(){}
  void clear(){ memset(rows,' ',sizeof(rows)); rows[0][16]=rows[1][16]=0; }
  void setCursor(int cc,int rr){ c=cc; r=rr; }
  void print(const char* s){ while(*s && c<16){ rows[r][c++]=*s++; } }
};

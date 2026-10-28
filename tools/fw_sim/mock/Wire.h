#pragma once
#include "Arduino.h"
// ACKs only the devices on the real board: TSL2591 (0x29) and the LCD backpack at g_i2c_lcd
// (0x3F = PCF8574AT, 0x27 = PCF8574T, 0 = LCD not connected)
inline uint8_t g_i2c_lcd = 0x3F;
struct TwoWire { uint8_t a=0; void begin(int,int){} void begin(){} void beginTransmission(uint8_t x){ a=x; } uint8_t endTransmission(){ return (a==0x29 || (g_i2c_lcd && a==g_i2c_lcd)) ? 0 : 2; } };
extern TwoWire Wire;

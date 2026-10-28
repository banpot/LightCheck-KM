// Boot test: I2C scan + LCD auto-detect with the backpack at 0x3F, at 0x27, missing,
// and plugged in after boot (retry every 5 s).
#include "Arduino.h"
#include "Wire.h"
#include <random>
unsigned long g_ms=0; SerialMock Serial; TwoWire Wire;
double g_true_lux=400; double g_gain_actual[4]={1.0,24.5,400.0,9200.0}; double g_ratio_ir=0.132;
double g_jitter=0.0; std::mt19937 g_rng(2569);
#include SKETCH
int main(){
  Serial.quiet=false;
  for (uint8_t addr : {(uint8_t)0x3F, (uint8_t)0x27, (uint8_t)0x00}) {
    printf("---- LCD backpack at 0x%02X ----\n", addr);
    g_i2c_lcd = addr; delete lcd; lcd = nullptr; lcdAddr = 0; g_ms = 0;
    setup();
    Serial.quiet = true; for (int i = 0; i < 3; i++) loop(); Serial.quiet = false;
    printf("lcd=%s addr=0x%02X  row0=[%s]\n", lcd ? "yes" : "no", lcdAddr, lcd ? lcd->rows[0] : "-");
  }
  printf("---- plug the LCD (0x27) in after boot ----\n");
  g_i2c_lcd = 0x27; for (int i = 0; i < 12 && !lcd; i++) loop();
  printf("lcd=%s addr=0x%02X at t=%lu ms  row0=[%s]\n", lcd ? "yes" : "no", lcdAddr, (unsigned long)g_ms, lcd ? lcd->rows[0] : "-");
  return 0;
}

#pragma once
#include "Arduino.h"
// Same enum values as the real Adafruit_TSL2591 v1.4.5 header
typedef enum { TSL2591_INTEGRATIONTIME_100MS=0x00, TSL2591_INTEGRATIONTIME_200MS=0x01, TSL2591_INTEGRATIONTIME_300MS=0x02,
  TSL2591_INTEGRATIONTIME_400MS=0x03, TSL2591_INTEGRATIONTIME_500MS=0x04, TSL2591_INTEGRATIONTIME_600MS=0x05 } tsl2591IntegrationTime_t;
typedef enum { TSL2591_GAIN_LOW=0x00, TSL2591_GAIN_MED=0x10, TSL2591_GAIN_HIGH=0x20, TSL2591_GAIN_MAX=0x30 } tsl2591Gain_t;
#define TSL2591_LUX_DF (408.0F)
// Physical model (datasheet DS000338 v6): CH0 = 1315 counts @ HIGH(400x typ),100ms, 4.98 uW/cm2 4000K LED (~15.7 lx @ 315 lm/W)
extern double g_true_lux; extern double g_gain_actual[4]; extern double g_ratio_ir;
struct Adafruit_TSL2591 {
  tsl2591Gain_t _gain=TSL2591_GAIN_MED; tsl2591IntegrationTime_t _integration=TSL2591_INTEGRATIONTIME_100MS;
  Adafruit_TSL2591(int){}
  bool begin(){ return true; }
  void setGain(tsl2591Gain_t g){ _gain=g; } tsl2591Gain_t getGain(){ return _gain; }
  void setTiming(tsl2591IntegrationTime_t t){ _integration=t; } tsl2591IntegrationTime_t getTiming(){ return _integration; }
  uint32_t getFullLuminosity(){
    for (uint8_t d=0; d<=_integration; d++) delay(120);
    double k0 = 1315.0/(400.0*15.7);                // counts per lux per 1x per 100 ms
    double ga = g_gain_actual[_gain>>4]; double at = (_integration+1);
    double sat = (_integration==0)?36863.0:65535.0;
    double c0 = g_true_lux*k0*ga*at, c1 = c0*g_ratio_ir;
    uint16_t full=(uint16_t)std::fmin(std::round(c0),sat), ir=(uint16_t)std::fmin(std::round(c1),sat);
    return ((uint32_t)ir<<16)|full;
  }
  float calculateLux(uint16_t ch0, uint16_t ch1){   // copied from library v1.4.5
    if ((ch0 == 0xFFFF) | (ch1 == 0xFFFF)) return -1;
    float atime = 100.0F*(_integration+1); float again = 1.0F;
    switch(_gain){ case TSL2591_GAIN_LOW: again=1.0F; break; case TSL2591_GAIN_MED: again=25.0F; break; case TSL2591_GAIN_HIGH: again=428.0F; break; case TSL2591_GAIN_MAX: again=9876.0F; break; }
    float cpl = (atime*again)/TSL2591_LUX_DF;
    return (((float)ch0-(float)ch1))*(1.0F-((float)ch1/(float)ch0))/cpl;
  }
};

// Stabilisation test: per-reading jitter -> spread of the LCD value and how often '*' (stable) shows.
#include "Arduino.h"
#include "Wire.h"
#include <random>
#include <vector>
unsigned long g_ms=0; SerialMock Serial; TwoWire Wire;
double g_true_lux=400; double g_gain_actual[4]={1.0,24.5,400.0,9200.0}; double g_ratio_ir=0.132;
double g_jitter=0.0; std::mt19937 g_rng(2569);
#include SKETCH  // passed with -DSKETCH="\"file.ino\""
static double sd(const std::vector<double>& v){ double m=0; for(double x:v) m+=x; m/=v.size(); double s=0; for(double x:v) s+=(x-m)*(x-m); return std::sqrt(s/(v.size()-1)); }
int main(){
  setup();
  printf("jitter/reading  CV(single raw)  CV(LCD value)  readings with '*'\n");
  for (double j : {0.003, 0.007, 0.015, 0.03, 0.06}) {
    g_jitter=j; g_true_lux=400; std::vector<double> lcdv; int star=0, n=0;
    for(int i=0;i<10;i++) loop();                                  // warm-up
    for(int i=0;i<400;i++){ loop(); n++;
      double v=atof(lcd.rows[0]+5); lcdv.push_back(v);
      if(strchr(lcd.rows[0], '*')) star++; }
    // single-reading spread = jitter by construction (counts scale linearly with light)
    printf("   %5.1f %%         %5.2f %%         %5.2f %%          %5.1f %%\n", j*100, j*100,
           100*sd(lcdv)/ (lcdv[0]>0?lcdv[0]:1), 100.0*star/n);
  }
}

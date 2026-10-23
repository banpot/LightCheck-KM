#include "Arduino.h"
#include "Wire.h"
unsigned long g_ms=0; SerialMock Serial; TwoWire Wire;
double g_true_lux=400; double g_gain_actual[4]={1.0,24.5,400.0,9200.0}; double g_ratio_ir=0.132;
#include SKETCH  // passed with -DSKETCH="\"file.ino\""
#include <vector>
struct R { int levels=0, osc=0, sat=0, office=0, office_med=0; };
R settleAt(double e, R r){ g_true_lux=e; std::vector<int> gs; int sats=0;
  for(int i=0;i<14;i++){ loop(); if(i>=6){ gs.push_back(tsl.getGain()); if(lcd.rows[0][5]=='S') sats++; } }
  int ch=0; for(size_t i=1;i<gs.size();i++) if(gs[i]!=gs[i-1]) ch++;
  r.levels++; if(ch) r.osc++; if(sats) r.sat++;
  if(e>=100 && e<=2900){ r.office++; if(gs.back()==TSL2591_GAIN_MED) r.office_med++; }
  return r; }
void report(const char* name, R r){ printf("  %-22s levels=%4d hunting=%3d showsSAT=%3d  office(100-2900lx) on MED: %d/%d\n", name, r.levels, r.osc, r.sat, r.office_med, r.office); }
int main(int argc, char** argv){
  if (argc>2) { g_gain_actual[1]=atof(argv[1]); g_gain_actual[2]=atof(argv[2]); }
  setup(); R up, down, jump;
  for (double e=2; e<=60000; e*=1.02) up = settleAt(e, up);
  for (double e=60000; e>=2; e/=1.02) down = settleAt(e, down);
  for (double e=100; e<=2900; e*=1.05){ settleAt(1.0, R()); jump = settleAt(e, jump); } // dark -> office jump
  report("ascending sweep", up); report("descending sweep", down); report("dark->office jumps", jump);
}

#!/usr/bin/env bash
# Host-side simulation of the firmware auto-range logic (no hardware needed).
# Compiles the sketch against mock Arduino/TSL2591 headers whose sensor model
# uses TSL2591 datasheet DS000338 typical responsivity and real gain ratios.
set -e
cd "$(dirname "$0")"
FW=../../firmware/LightCheck_TSL2591_Calibrated/LightCheck_TSL2591_Calibrated.ino
cp "$FW" mock/current.ino
cp v1.0_reference.ino mock/v10.ino
for v in v10 current; do
  g++ -std=c++17 -w -Imock -DSKETCH="\"$v.ino\"" -x c++ autorange_test.cpp -o "/tmp/fwsim_$v"
  for gains in "24.5 400" "22 440" "27 360"; do
    echo "== $v | device MED/HIGH gain = $gains (library assumes 25 / 428)"
    "/tmp/fwsim_$v" $gains
  done
done
echo
echo "== stabilisation (rolling mean of 5, '*' when CV < 2 %) at 400 lx =="
cp "$FW" mock/current.ino
g++ -std=c++17 -w -Imock -DSKETCH="\"current.ino\"" -x c++ flicker_test.cpp -o /tmp/fwsim_flicker
/tmp/fwsim_flicker
rm -f mock/current.ino mock/v10.ino

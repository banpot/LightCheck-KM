# Changelog

## [1.1.1] – 2026-10-28
### Firmware
- **Fixed** blank LCD when the backpack is a PCF8574T (0x27): v1.1.0 used a fixed address (0x3F) and only warned on
  Serial. The LCD address is now auto-detected (0x27, 0x3F, then 0x20–0x27 / 0x38–0x3F); `LCD_ADDR_FIXED` forces one.
- **Added** I2C bus scan in the boot log (`I2C scan: 0x27 0x29`) and `LCD found at 0x..`.
- **Added** Serial-only mode when no LCD answers, with a retry every 5 s (a re-seated cable starts the display without a reset).
- Measurement logic unchanged: `tools/fw_sim` results identical to v1.1.0; new boot test covers 0x3F, 0x27, missing and hot-plug.

## [Enclosure 1.1] – 2026-10-27
### Hardware
- **Fixed** screw holes too tight to drive on FDM prints (holes print 0.2–0.4 mm undersize):
  M3 pilot 2.5 → 2.8 mm, M2.5 pilots 2.1 → 2.3 mm, M3 clearance 3.4 → 3.6 mm, counterbore 6.4 → 6.6 mm,
  1/4"-20 nut pocket +0.2 mm, tripod hole 6.8 → 7.0 mm; 45° lead-in on every screw pilot; corner bosses Ø7.0 → Ø7.6.
- **Added** fit profiles: `stl/` standard (holes +0.2, clearance 0.35 mm) and `stl/loose/` for coarse printers
  (holes +0.4, clearance 0.55 mm, 108 × 64 × 26 mm); `--fit custom --hole-comp X --clr Y` for any printer.
- **Added** `stl/fit_test/hole_fit_test.stl` (~10 g): labelled M3 / M2.5 pilots and 1/4" nut pockets for choosing a profile.
- Sensor plane, sensor position on the lid and the light aperture are unchanged; record the profile in calibration reports.

## [1.1.0] – 2026-10-23
### Firmware
- **Fixed** auto-range gain hunting: v1.0 stepped the gain up whenever Full < 4095 counts without
  predicting the counts at the next gain, so the meter oscillated between gains and showed
  `SATURATED` every other reading (host simulation: 40–50 of 521 light levels affected across
  2–60,000 lx; office levels near ~260 lx included). v1.1 predicts the next-gain counts
  (step up only if < 70 % FS and Full < 1000), steps down at 90 % FS, and leaves HIGH/MAX or LOW
  as soon as MED fits. Office light (~100–2,900 lx) is now always read on MED gain.
- **Added** reading stabilisation for LED flicker (100 Hz on the 50 Hz grid) and PWM dimming:
  rolling mean of the last 5 valid readings at one gain, `CV`/`Stable` in the log, `*` on the LCD
  when CV < 2 %. Compensation is applied to the averaged value. Host test: displayed jitter ÷≈2.3.
- **Added** `CAL_GAIN` / `CAL_TIMING` traceability; Serial `CalScope=OK|OUT`, LCD prefix `!` when a
  calibrated reading was taken at another gain.
- **Added** optional CSV serial output (`SERIAL_CSV`) for paired-measurement logging.
- **Added** firmware version on boot and in the calibration banner; LCD line 2 now fits 16 chars
  (`R G:9876x 300ms`); LCD address hint for 0x27 backpacks.
### Knowledge repository
- Public repository with user manual, SOP with guard-band rule, wiring diagram, troubleshooting,
  KM process mapping, Green Office 5.2.1 checklist.
- Parametric 3D-printable enclosure (STL + generator) with flush sensor pocket and 1/4" tripod nut.
- Calibration toolkit: `fit_calibration.py` (real data), `simulate_calibration.py` (Monte Carlo),
  `expected_bias_from_datasheet.py`.
- Survey tools: `grid_planner.py` (2 × 2 m grid + survey form), `office_lighting_sim.py` (digital twin).
- Firmware host test: `tools/fw_sim`.

## [1.0.0] – 2026-08
- Initial firmware submitted with the KM form: TSL2591 + LCD1602 on Wemos D1 mini, raw/corrected
  logging, linear compensation (disabled by default), saturation limits per datasheet.

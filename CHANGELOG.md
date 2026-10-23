# Changelog

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

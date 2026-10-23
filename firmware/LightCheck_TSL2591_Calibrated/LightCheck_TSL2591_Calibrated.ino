/*
  LightCheck KM - TSL2591 + LCD1602 on Wemos D1 mini (ESP8266)
  Firmware v1.1.0  (see CHANGELOG.md for the v1.0 -> v1.1 changes)

  Purpose
  -------
  Low-cost office illuminance PRE-SURVEY / KM instrument.
  The firmware keeps both raw calculated lux and compensated lux so the
  calibration model is auditable. For formal Green Office evidence, verify
  results with a standards-compliant, currently calibrated lux meter.

  Wiring (shared I2C bus)
  -----------------------
  D1 (GPIO5)  -> SCL
  D2 (GPIO4)  -> SDA
  3V3         -> TSL2591 VIN
  5V          -> LCD1602 VCC (typical I2C backpack; verify your module)
  GND         -> common GND

  I2C addresses
  -------------
  TSL2591 = 0x29
  LCD1602 = 0x3F   (PCF8574A backpack; PCF8574 backpacks are usually 0x27)

  Accuracy compensation
  ---------------------
  The TSL2591 datasheet does not specify one universal end-to-end lux
  accuracy percentage for every light source. Therefore this project uses a
  locally validated calibration model against a standards-compliant,
  calibrated reference lux meter under the office lighting conditions where
  the instrument will be used.

      Lux_corrected = CAL_SLOPE * Lux_raw + CAL_OFFSET

  IMPORTANT:
  - Leave CALIBRATION_ENABLED = false until coefficients have been derived
    from paired measurements AND validated on a separate data set/session.
  - Auto-ranging is based on RAW ADC counts, never on compensated lux.
  - The code logs RawLux and CalLux separately for traceability.
  - Keep calibration date/model/version in the KM repository.
  - The coefficients are valid for the gain/integration time they were
    derived at (CAL_GAIN / CAL_TIMING). Readings taken at another gain are
    flagged (Serial CalScope=OUT, LCD "!") because the real TSL2591 gain
    ratios differ from the library's nominal values (datasheet typ.
    MED 24.5x / HIGH 400x vs library 25x / 428x, about 4-5 % step).

  Saturation limits follow the TSL2591 datasheet:
  - 100 ms integration: 36863 counts
  - 200-600 ms:          65535 counts

  v1.1.0 auto-range fix
  ---------------------
  v1.0 stepped the gain UP whenever Full < 4095 counts (1/16 of full scale)
  without checking whether the next gain (x17-25) would saturate. A host
  simulation with datasheet-typical gains (tools/fw_sim) shows v1.0 hunting
  between gains and printing SATURATED every other reading at ~11-16 lux
  (HIGH<->MAX), ~260 lux (MED<->HIGH; the exact band moves with each unit's
  real gain ratio) and ~4,300-6,500 lux (LOW<->MED, near windows). It also
  kept everything below ~260 lux on HIGH gain, which adds the ~5 % library
  vs real gain-ratio step inside the office range.
  v1.1: (1) predicts the counts at the next gain and steps UP only if they
  stay below 70 % of full scale and Full < 1000 counts; (2) steps DOWN at
  90 % of full scale; (3) leaves HIGH/MAX as soon as the lower gain would
  still give >= 1500 counts, and leaves LOW as soon as MED fits.
  Result: no hunting, and the office range (~100 to ~2,900 lux) is always
  read on MED gain = one calibration model.

  v1.1.0 reading stabilisation (field lesson)
  -------------------------------------------
  LED office lighting is not like daylight: its spectrum is different and its
  output flickers at twice the mains frequency (Thailand 50 Hz -> 100 Hz,
  10 ms period), so single readings jump around. Every TSL2591 integration
  time (100-600 ms) is a whole number of 10 ms periods, so one reading always
  integrates complete flicker cycles; the remaining jitter (PWM dimming,
  driver ripple, hand movement) is removed by a rolling mean of the last
  AVG_WINDOW valid readings taken at the same gain. The LCD shows '*' when
  the window is full and the coefficient of variation is < STABLE_CV_PCT (2 %,
  i.e. the 5-reading mean is good to about 1 %):
  record values only when '*' is shown.
*/

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TSL2591.h>
#include <LiquidCrystal_I2C.h>
#include <math.h>

#define LCD_ADDR     0x3F
#define TSL2591_ADDR 0x29

const char FW_VERSION[] = "1.1.0";

Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);

// -------------------------------------------------------------------------
// CALIBRATION / COMPENSATION MODEL
// -------------------------------------------------------------------------
// Set to true ONLY after a and b are obtained from paired measurements
// against a standards-compliant, currently calibrated reference lux meter.
const bool  CALIBRATION_ENABLED = false;

// Linear regression model: reference_lux = a * sensor_raw_lux + b
// Identity values below intentionally make no correction until calibration.
// Use calibration/fit_calibration.py to derive and validate a and b.
const float CAL_SLOPE  = 1.000000f;  // a  [replace after calibration]
const float CAL_OFFSET = 0.000000f;  // b  [replace after calibration]

// Gain / integration time at which the paired data were collected.
const tsl2591Gain_t            CAL_GAIN   = TSL2591_GAIN_MED;
const tsl2591IntegrationTime_t CAL_TIMING = TSL2591_INTEGRATIONTIME_300MS;

// Traceability metadata: update whenever coefficients are changed.
const char CAL_MODEL_VERSION[] = "CAL-UNSET";
const char CAL_DATE[]          = "YYYY-MM-DD";
const char CAL_REFERENCE[]     = "REFERENCE-METER-ID";

// Optional sanity bound for office pre-survey. This is NOT a legal threshold;
// it only prevents a bad coefficient from producing an absurd negative value.
const float MIN_VALID_CORRECTED_LUX = 0.0f;

// -------------------------------------------------------------------------
// SERIAL OUTPUT FORMAT
// -------------------------------------------------------------------------
// false = human-readable key=value lines (default, same as v1.0)
// true  = CSV rows for paired-measurement logging; paste into
//         calibration/paired_measurements.csv next to the reference value.
const bool SERIAL_CSV = false;

// -------------------------------------------------------------------------
// STABILISATION (LED flicker / mains ripple)
// -------------------------------------------------------------------------
const uint8_t AVG_WINDOW    = 5;     // readings in the rolling mean (1 = off)
const float   STABLE_CV_PCT = 2.0f;  // stable when CV of the window < 2 % (mean within ~1 %)

// -------------------------------------------------------------------------
// AUTO-RANGE PARAMETERS (raw ADC counts)
// -------------------------------------------------------------------------
// Step gain DOWN when either channel reaches this fraction of full scale.
const float    RANGE_STEP_DOWN_FRACTION = 0.90f;
// Step gain UP only if the predicted counts at the next gain stay below this
// fraction of full scale (prevents MED<->HIGH oscillation).
const float    RANGE_STEP_UP_HEADROOM   = 0.70f;
// ...and only when the signal is really small (keeps office light on MED).
const uint16_t RANGE_STEP_UP_FLOOR      = 1000;
// From HIGH/MAX, go back to the lower gain as soon as it would still give at
// least this many counts (1.5x the floor = hysteresis band).
const uint16_t RANGE_PREFER_LOWER       = 1500;

// -------------------------------------------------------------------------
// HELPERS
// -------------------------------------------------------------------------

bool i2cDeviceFound(uint8_t addr) {
  Wire.beginTransmission(addr);
  return (Wire.endTransmission() == 0);
}

void lcdLine(uint8_t row, const char *text) {
  lcd.setCursor(0, row);
  lcd.print("                ");
  lcd.setCursor(0, row);
  lcd.print(text);
}

void haltWithMessage(const char *line1, const char *line2) {
  lcd.clear();
  lcdLine(0, line1);
  lcdLine(1, line2);
  Serial.print(F("HALT: "));
  Serial.print(line1);
  Serial.print(F(" / "));
  Serial.println(line2);
  while (1) { delay(1000); }
}

uint16_t integrationMs(tsl2591IntegrationTime_t t) {
  switch (t) {
    case TSL2591_INTEGRATIONTIME_100MS: return 100;
    case TSL2591_INTEGRATIONTIME_200MS: return 200;
    case TSL2591_INTEGRATIONTIME_300MS: return 300;
    case TSL2591_INTEGRATIONTIME_400MS: return 400;
    case TSL2591_INTEGRATIONTIME_500MS: return 500;
    case TSL2591_INTEGRATIONTIME_600MS: return 600;
  }
  return 100;
}

// TSL2591 datasheet: max ADC count = 36863 at 100ms, 65535 at 200-600ms.
uint16_t saturationLimit(tsl2591IntegrationTime_t t) {
  return (t == TSL2591_INTEGRATIONTIME_100MS) ? 36863 : 65535;
}

const char *gainName(tsl2591Gain_t g) {
  switch (g) {
    case TSL2591_GAIN_LOW:  return "1x";
    case TSL2591_GAIN_MED:  return "25x";
    case TSL2591_GAIN_HIGH: return "428x";
    case TSL2591_GAIN_MAX:  return "9876x";
  }
  return "?";
}

// Nominal gain multipliers used by Adafruit_TSL2591::calculateLux().
float gainFactor(tsl2591Gain_t g) {
  switch (g) {
    case TSL2591_GAIN_LOW:  return 1.0f;
    case TSL2591_GAIN_MED:  return 25.0f;
    case TSL2591_GAIN_HIGH: return 428.0f;
    case TSL2591_GAIN_MAX:  return 9876.0f;
  }
  return 1.0f;
}

// Rolling mean of valid raw-lux readings taken at one gain.
float         avgBuf[AVG_WINDOW];
uint8_t       avgCount = 0, avgHead = 0;
tsl2591Gain_t avgGain  = TSL2591_GAIN_MED;

void avgReset() { avgCount = 0; avgHead = 0; }

void avgPush(float v) {
  avgBuf[avgHead] = v;
  avgHead = (uint8_t)((avgHead + 1) % AVG_WINDOW);
  if (avgCount < AVG_WINDOW) avgCount++;
}

float avgMean() {
  if (avgCount == 0) return NAN;
  float s = 0.0f;
  for (uint8_t i = 0; i < avgCount; i++) s += avgBuf[i];
  return s / avgCount;
}

// Coefficient of variation (sample SD / mean) in percent.
float avgCvPct() {
  if (avgCount < 2) return NAN;
  float m = avgMean();
  if (!(m > 0.0f)) return NAN;
  float ss = 0.0f;
  for (uint8_t i = 0; i < avgCount; i++) ss += (avgBuf[i] - m) * (avgBuf[i] - m);
  return 100.0f * sqrtf(ss / (avgCount - 1)) / m;
}

bool calibrationInScope(tsl2591Gain_t g, tsl2591IntegrationTime_t t) {
  return (g == CAL_GAIN) && (t == CAL_TIMING);
}

// Apply the validated local calibration model.
// If calibration is disabled, return raw lux unchanged.
float compensateLux(float rawLux) {
  if (isnan(rawLux) || isinf(rawLux) || rawLux < 0.0f) {
    return rawLux;
  }

  if (!CALIBRATION_ENABLED) {
    return rawLux;
  }

  float corrected = (CAL_SLOPE * rawLux) + CAL_OFFSET;

  if (isnan(corrected) || isinf(corrected)) {
    return -1.0f;
  }

  if (corrected < MIN_VALID_CORRECTED_LUX) {
    corrected = MIN_VALID_CORRECTED_LUX;
  }
  return corrected;
}

// Auto-ranging with hysteresis on RAW ADC counts.
// Returns true if gain changed (the next reading uses the new gain).
bool autoRange(uint16_t full, uint16_t ir) {
  tsl2591Gain_t            g = tsl.getGain();
  tsl2591IntegrationTime_t t = tsl.getTiming();
  uint16_t sat     = saturationLimit(t);
  uint16_t hiLimit = (uint16_t)(RANGE_STEP_DOWN_FRACTION * sat);
  uint16_t maxCh   = (full > ir) ? full : ir;

  // Near/at saturation -> step gain DOWN.
  if (maxCh >= hiLimit) {
    if (g == TSL2591_GAIN_MAX)  { tsl.setGain(TSL2591_GAIN_HIGH); return true; }
    if (g == TSL2591_GAIN_HIGH) { tsl.setGain(TSL2591_GAIN_MED);  return true; }
    if (g == TSL2591_GAIN_MED)  { tsl.setGain(TSL2591_GAIN_LOW);  return true; }
    return false; // already at minimum gain
  }

  // On HIGH/MAX, return to the lower gain once it gives enough counts, so
  // office light is never left on a high gain after a dark moment.
  if (g == TSL2591_GAIN_MAX || g == TSL2591_GAIN_HIGH) {
    tsl2591Gain_t lower = (g == TSL2591_GAIN_MAX) ? TSL2591_GAIN_HIGH : TSL2591_GAIN_MED;
    float predictedLower = (float)full * gainFactor(lower) / gainFactor(g);
    if (predictedLower >= (float)RANGE_PREFER_LOWER) {
      tsl.setGain(lower);
      return true;
    }
  }

  // Low signal -> step gain UP, but only if the next gain will not
  // saturate (predicted counts < headroom). This is what stops oscillation.
  // LOW -> MED needs only the headroom test (MED is the preferred office
  // gain); MED -> HIGH and HIGH -> MAX also need Full < RANGE_STEP_UP_FLOOR.
  if (g == TSL2591_GAIN_LOW || full < RANGE_STEP_UP_FLOOR) {
    tsl2591Gain_t next;
    if      (g == TSL2591_GAIN_LOW)  next = TSL2591_GAIN_MED;
    else if (g == TSL2591_GAIN_MED)  next = TSL2591_GAIN_HIGH;
    else if (g == TSL2591_GAIN_HIGH) next = TSL2591_GAIN_MAX;
    else return false;              // already at maximum gain

    float ratio     = gainFactor(next) / gainFactor(g);
    float predicted = (float)maxCh * ratio;
    if (predicted < RANGE_STEP_UP_HEADROOM * (float)sat) {
      tsl.setGain(next);
      return true;
    }
  }
  return false;
}

void configureSensor() {
  // Good starting point for typical indoor office lighting.
  // Auto-ranging changes gain when necessary.
  tsl.setGain(TSL2591_GAIN_MED);
  tsl.setTiming(TSL2591_INTEGRATIONTIME_300MS);
}

void printCalibrationInfo() {
  Serial.println(F("--- Calibration / compensation ---"));
  Serial.print(F("Firmware=")); Serial.println(FW_VERSION);
  Serial.print(F("Enabled=")); Serial.println(CALIBRATION_ENABLED ? F("YES") : F("NO"));
  Serial.print(F("Model="));   Serial.println(CAL_MODEL_VERSION);
  Serial.print(F("Date="));    Serial.println(CAL_DATE);
  Serial.print(F("Reference=")); Serial.println(CAL_REFERENCE);
  Serial.print(F("Slope(a)="));  Serial.println(CAL_SLOPE, 6);
  Serial.print(F("Offset(b)=")); Serial.println(CAL_OFFSET, 6);
  Serial.print(F("ValidAt=Gain ")); Serial.print(gainName(CAL_GAIN));
  Serial.print(F(" / Tint ")); Serial.print(integrationMs(CAL_TIMING)); Serial.println(F("ms"));
  Serial.println(F("Formula: CalLux = a*RawLux + b"));
  Serial.println(F("----------------------------------"));
  if (SERIAL_CSV) {
    Serial.println(F("ms,fw,cal_model,cal_on,gain,tint_ms,full,ir,raw_lux,raw_avg_lux,cv_pct,n_avg,stable,cal_lux,cal_scope"));
  }
}

// -------------------------------------------------------------------------
// SETUP
// -------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(100);
  Wire.begin(D2, D1);   // SDA=D2 (GPIO4), SCL=D1 (GPIO5)

  lcd.init();
  lcd.backlight();
  lcdLine(0, "LightCheck v1.1");
  lcdLine(1, "Checking HW...");
  Serial.println(F("Checking hardware..."));
  delay(800);

  lcdLine(1, "LCD 0x3F ...");
  delay(400);
  if (!i2cDeviceFound(LCD_ADDR)) {
    // LCD is already being used to show startup status; warn on Serial only.
    Serial.println(F("WARN: LCD not ACKing at 0x3F (try 0x27)"));
  } else {
    lcdLine(1, "LCD: OK");
  }
  delay(500);

  lcdLine(1, "TSL2591 0x29...");
  delay(400);
  if (!i2cDeviceFound(TSL2591_ADDR)) {
    haltWithMessage("TSL2591 NOT", "FOUND @ 0x29");
  }
  lcdLine(1, "TSL2591: found");
  delay(500);

  lcdLine(1, "TSL2591 init...");
  if (!tsl.begin()) {
    haltWithMessage("TSL2591", "INIT FAILED");
  }
  configureSensor();
  lcdLine(1, "TSL2591: OK");
  delay(500);

  lcdLine(1, "Test read...");
  uint32_t lum = tsl.getFullLuminosity();
  uint16_t ir   = lum >> 16;
  uint16_t full = lum & 0xFFFF;
  Serial.print(F("Test full=")); Serial.print(full);
  Serial.print(F(" ir="));       Serial.println(ir);
  if (full == 0 && ir == 0) {
    haltWithMessage("Sensor read", "returned 0/0");
  }
  lcdLine(1, "Read: OK");
  delay(500);

  printCalibrationInfo();

  lcd.clear();
  lcdLine(0, "All systems GO");
  lcdLine(1, CALIBRATION_ENABLED ? "CAL: ON" : "CAL: RAW MODE");
  Serial.println(F("Hardware check passed."));
  delay(1200);
  lcd.clear();
}

// -------------------------------------------------------------------------
// MAIN LOOP
// -------------------------------------------------------------------------

void loop() {
  uint32_t lum  = tsl.getFullLuminosity();
  uint16_t ir   = lum >> 16;
  uint16_t full = lum & 0xFFFF;

  // Pull current gain/timing back from the driver every cycle.
  tsl2591Gain_t            g = tsl.getGain();
  tsl2591IntegrationTime_t t = tsl.getTiming();
  uint16_t sat = saturationLimit(t);
  bool saturated = (full >= sat) || (ir >= sat);
  bool inScope   = calibrationInScope(g, t);

  // Raw lux is the library result before local correction.
  float rawLux = saturated ? -1.0f : tsl.calculateLux(full, ir);
  bool rawOk = !(saturated || rawLux < 0.0f || isnan(rawLux) || isinf(rawLux));

  // Stabilisation: rolling mean at one gain; restart on gain change/invalid.
  if (g != avgGain || !rawOk) { avgReset(); avgGain = g; }
  if (rawOk) avgPush(rawLux);
  float rawAvg = rawOk ? avgMean() : rawLux;
  float cvPct  = avgCvPct();
  bool  stable = rawOk && (avgCount == AVG_WINDOW) && !isnan(cvPct) && (cvPct < STABLE_CV_PCT);

  // Compensation is applied to the stabilised (averaged) raw value.
  float calLux = compensateLux(rawAvg);
  bool calOk = !(saturated || calLux < 0.0f || isnan(calLux) || isinf(calLux));

  uint16_t visible = (full > ir) ? (full - ir) : 0;

  // ---- Serial audit/debug output ----
  if (SERIAL_CSV) {
    Serial.print(millis());          Serial.print(',');
    Serial.print(FW_VERSION);        Serial.print(',');
    Serial.print(CAL_MODEL_VERSION); Serial.print(',');
    Serial.print(CALIBRATION_ENABLED ? 1 : 0); Serial.print(',');
    Serial.print(gainName(g));       Serial.print(',');
    Serial.print(integrationMs(t));  Serial.print(',');
    Serial.print(full);              Serial.print(',');
    Serial.print(ir);                Serial.print(',');
    if (rawOk) Serial.print(rawLux, 3); else Serial.print(saturated ? F("SAT") : F("ERR"));
    Serial.print(',');
    if (rawOk) Serial.print(rawAvg, 3); else Serial.print(saturated ? F("SAT") : F("ERR"));
    Serial.print(',');
    if (!isnan(cvPct)) Serial.print(cvPct, 2);
    Serial.print(',');
    Serial.print(avgCount);          Serial.print(',');
    Serial.print(stable ? 1 : 0);    Serial.print(',');
    if (calOk) Serial.print(calLux, 3); else Serial.print(saturated ? F("SAT") : F("ERR"));
    Serial.print(',');
    Serial.println(inScope ? F("OK") : F("OUT"));
  } else {
    Serial.print(F("Gain="));  Serial.print(gainName(g));
    Serial.print(F(" Tint=")); Serial.print(integrationMs(t)); Serial.print(F("ms"));
    Serial.print(F(" Full=")); Serial.print(full);
    Serial.print(F(" IR="));   Serial.print(ir);
    Serial.print(F(" Vis="));  Serial.print(visible);
    Serial.print(F(" RawLux="));
    if (saturated)      Serial.print(F("SAT"));
    else if (!rawOk)    Serial.print(F("ERR"));
    else                Serial.print(rawLux, 3);
    if (rawOk) {
      Serial.print(F(" RawAvg=")); Serial.print(rawAvg, 3);
      Serial.print(F(" N="));      Serial.print(avgCount);
      Serial.print(F(" CV="));
      if (isnan(cvPct)) Serial.print(F("-")); else Serial.print(cvPct, 2);
      Serial.print(F("% Stable=")); Serial.print(stable ? F("Y") : F("N"));
    }

    Serial.print(F(" CalLux="));
    if (saturated)      Serial.print(F("SAT"));
    else if (!calOk)    Serial.print(F("ERR"));
    else                Serial.print(calLux, 3);
    Serial.print(F(" CalMode="));
    Serial.print(CALIBRATION_ENABLED ? F("ON") : F("OFF"));
    Serial.print(F(" CalScope="));
    Serial.println(inScope ? F("OK") : F("OUT"));
  }

  // ---- LCD ----
  // Line 1: stabilised value (compensated when enabled; otherwise raw).
  // Prefix: C = calibrated, R = raw, ! = calibrated but outside the
  // gain/timing the coefficients were validated at.
  char buf[17];
  char mode = CALIBRATION_ENABLED ? (inScope ? 'C' : '!') : 'R';
  if (saturated) {
    snprintf(buf, sizeof(buf), "Lux: SATURATED ");
  } else if (!calOk) {
    snprintf(buf, sizeof(buf), "Lux: ERROR     ");
  } else {
    char fbuf[12];
    dtostrf(calLux, 7, 2, fbuf);
    // "*" at the end of line 1 = stable (rolling window full, CV < 2 %)
    snprintf(buf, sizeof(buf), "%cLux:%s %c", mode, fbuf, stable ? '*' : ' ');
  }
  lcdLine(0, buf);

  // Line 2: mode, gain and integration time, e.g. "R G:25x   300ms".
  snprintf(buf, sizeof(buf), "%c G:%-5s %3ums",
           mode, gainName(g), (unsigned)integrationMs(t));
  lcdLine(1, buf);

  // ---- Auto-range AFTER reporting ----
  // Auto-range always uses raw ADC counts, not corrected lux.
  if (autoRange(full, ir)) {
    Serial.print(F(">> auto-range -> Gain="));
    Serial.println(gainName(tsl.getGain()));

    // Allow at least one integration period for new gain to take effect.
    delay(integrationMs(t) + 50);
  } else {
    delay(500);
  }
}

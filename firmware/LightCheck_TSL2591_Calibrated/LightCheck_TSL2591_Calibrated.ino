/*
  LightCheck KM - TSL2591 + LCD1602 on Wemos D1 mini (ESP8266)

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
  LCD1602 = 0x3F

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
  - Keep calibration date/model/version in the private KM repository.

  Saturation limits follow the TSL2591 datasheet:
  - 100 ms integration: 36863 counts
  - 200-600 ms:          65535 counts
*/

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TSL2591.h>
#include <LiquidCrystal_I2C.h>
#include <math.h>

#define LCD_ADDR     0x3F
#define TSL2591_ADDR 0x29

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
const float CAL_SLOPE  = 1.000000f;  // a  [replace after calibration]
const float CAL_OFFSET = 0.000000f;  // b  [replace after calibration]

// Traceability metadata: update whenever coefficients are changed.
const char CAL_MODEL_VERSION[] = "CAL-UNSET";
const char CAL_DATE[]          = "YYYY-MM-DD";
const char CAL_REFERENCE[]     = "REFERENCE-METER-ID";

// Optional sanity bound for office pre-survey. This is NOT a legal threshold;
// it only prevents a bad coefficient from producing an absurd negative value.
const float MIN_VALID_CORRECTED_LUX = 0.0f;

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

// Auto-ranging shifts gain so ADC values stay away from saturation and the
// extreme low end. Returns true if gain changed; caller discards this sample.
bool autoRange(uint16_t full, uint16_t ir) {
  tsl2591Gain_t            g = tsl.getGain();
  tsl2591IntegrationTime_t t = tsl.getTiming();
  uint16_t sat = saturationLimit(t);

  // Saturated -> step gain DOWN.
  if (full >= sat || ir >= sat) {
    if (g == TSL2591_GAIN_MAX)  { tsl.setGain(TSL2591_GAIN_HIGH); return true; }
    if (g == TSL2591_GAIN_HIGH) { tsl.setGain(TSL2591_GAIN_MED);  return true; }
    if (g == TSL2591_GAIN_MED)  { tsl.setGain(TSL2591_GAIN_LOW);  return true; }
    return false; // already at minimum gain
  }

  // Very low signal -> step gain UP. Use 1/16 full scale as a practical floor.
  uint16_t lowThresh = sat / 16;
  if (full < lowThresh) {
    if (g == TSL2591_GAIN_LOW)  { tsl.setGain(TSL2591_GAIN_MED);  return true; }
    if (g == TSL2591_GAIN_MED)  { tsl.setGain(TSL2591_GAIN_HIGH); return true; }
    if (g == TSL2591_GAIN_HIGH) { tsl.setGain(TSL2591_GAIN_MAX);  return true; }
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
  Serial.print(F("Enabled=")); Serial.println(CALIBRATION_ENABLED ? F("YES") : F("NO"));
  Serial.print(F("Model="));   Serial.println(CAL_MODEL_VERSION);
  Serial.print(F("Date="));    Serial.println(CAL_DATE);
  Serial.print(F("Reference=")); Serial.println(CAL_REFERENCE);
  Serial.print(F("Slope(a)="));  Serial.println(CAL_SLOPE, 6);
  Serial.print(F("Offset(b)=")); Serial.println(CAL_OFFSET, 6);
  Serial.println(F("Formula: CalLux = a*RawLux + b"));
  Serial.println(F("----------------------------------"));
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
  lcdLine(0, "Checking HW...");
  Serial.println(F("Checking hardware..."));
  delay(800);

  lcdLine(1, "LCD 0x3F ...");
  delay(400);
  if (!i2cDeviceFound(LCD_ADDR)) {
    // LCD is already being used to show startup status; warn on Serial only.
    Serial.println(F("WARN: LCD not ACKing at 0x3F"));
  }
  lcdLine(1, "LCD: OK");
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

  // Raw lux is the library result before local correction.
  float rawLux = saturated ? -1.0f : tsl.calculateLux(full, ir);
  float calLux = compensateLux(rawLux);

  uint16_t visible = (full > ir) ? (full - ir) : 0;

  // ---- Serial audit/debug output ----
  Serial.print(F("Gain="));  Serial.print(gainName(g));
  Serial.print(F(" Tint=")); Serial.print(integrationMs(t)); Serial.print(F("ms"));
  Serial.print(F(" Full=")); Serial.print(full);
  Serial.print(F(" IR="));   Serial.print(ir);
  Serial.print(F(" Vis="));  Serial.print(visible);
  Serial.print(F(" RawLux="));

  if (saturated) {
    Serial.print(F("SAT"));
  } else if (rawLux < 0.0f || isnan(rawLux) || isinf(rawLux)) {
    Serial.print(F("ERR"));
  } else {
    Serial.print(rawLux, 3);
  }

  Serial.print(F(" CalLux="));
  if (saturated) {
    Serial.print(F("SAT"));
  } else if (calLux < 0.0f || isnan(calLux) || isinf(calLux)) {
    Serial.print(F("ERR"));
  } else {
    Serial.print(calLux, 3);
  }
  Serial.print(F(" CalMode="));
  Serial.println(CALIBRATION_ENABLED ? F("ON") : F("OFF"));

  // ---- LCD ----
  // Line 1: show compensated value when enabled; otherwise raw value.
  char buf[17];
  if (saturated) {
    snprintf(buf, sizeof(buf), "Lux: SATURATED ");
  } else if (calLux < 0.0f || isnan(calLux) || isinf(calLux)) {
    snprintf(buf, sizeof(buf), "Lux: ERROR     ");
  } else {
    char fbuf[10];
    dtostrf(calLux, 7, 2, fbuf);
    snprintf(buf, sizeof(buf), "%cLux:%s", CALIBRATION_ENABLED ? 'C' : 'R', fbuf);
  }
  lcdLine(0, buf);

  // Line 2: C/R indicates Calibrated/Raw mode.
  snprintf(buf, sizeof(buf), "%c G:%s T:%ums",
           CALIBRATION_ENABLED ? 'C' : 'R',
           gainName(g), integrationMs(t));
  buf[16] = '\0';
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

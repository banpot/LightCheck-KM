# Calibration / Compensation

สถานะปัจจุบัน: **ยังไม่มีข้อมูลวัดจริง** firmware จึงตั้งไว้ที่ `CALIBRATION_ENABLED = false`
และ `CAL_MODEL_VERSION = "CAL-UNSET"` (แสดงค่า Raw) ตัวเลขในโฟลเดอร์ `sim/` ทั้งหมด
เป็น **ผลจำลอง (Monte Carlo)** จากสเปกที่ตีพิมพ์และสมมติฐานที่ระบุไว้ ไม่ใช่ผลการวัด

## สมการชดเชย (Compensation equation)

**1) ค่า Raw Lux จากเซนเซอร์** (ไลบรารี Adafruit_TSL2591 v1.4.5 `calculateLux`)

$$E_{raw}=\frac{(CH_0-CH_1)\left(1-\dfrac{CH_1}{CH_0}\right)}{CPL},\qquad CPL=\frac{t_{int}\,[\mathrm{ms}]\times G}{408}$$

- $CH_0$ = ช่อง Full spectrum (visible + IR), $CH_1$ = ช่อง IR (ADC counts)
- $t_{int}$ = integration time (v1.1 ใช้ 300 ms), $G$ = gain ที่ไลบรารีสมมติ (1, 25, 428, 9876)

**2) ค่าเฉลี่ยลดการกระพริบของ LED** (rolling mean 5 ค่าล่าสุดที่ gain เดียวกัน)

$$\bar{E}_{raw}=\frac{1}{5}\sum_{k=0}^{4}E_{raw,\,t-k}$$

**3) สมการชดเชยเชิงเส้น** (ใน firmware: `CalLux = CAL_SLOPE * RawLux + CAL_OFFSET`)

$$\boxed{E_{corrected}=a\,\bar{E}_{raw}+b}$$

**4) หา a และ b ด้วย least squares** จากข้อมูลคู่ชุด fit เท่านั้น ($x_i$ = Raw ของต้นแบบ, $y_i$ = ค่าจากเครื่องอ้างอิงที่มีใบสอบเทียบ)

$$a=\frac{\sum_i (x_i-\bar{x})(y_i-\bar{y})}{\sum_i (x_i-\bar{x})^2},\qquad b=\bar{y}-a\,\bar{x}$$

**5) วัดความแม่นยำบนชุด validation (คนละ session)**

$$\mathrm{MAPE}=\frac{100}{n}\sum_{i=1}^{n}\frac{|E_{corrected,i}-E_{ref,i}|}{E_{ref,i}},\qquad U_{95}=P_{95}\left(\frac{|E_{corrected}-E_{ref}|}{E_{ref}}\right)$$

**6) กติกาตัดสินผล (guard band)**: ถ้า $|E_{corrected}-E_{เกณฑ์}| \le U_{95}\cdot E_{เกณฑ์}$ ให้ยืนยันด้วยเครื่องมาตรฐาน

**ตัวอย่างจากผลจำลอง** (ไม่ใช่ค่าจริง): $a = 1.596$, $b = -4.2$ lx
ถ้าต้นแบบอ่าน Raw = 250 lx จะได้ $E_{corrected} = 1.596 \times 250 - 4.2 = 394.8$ lx
ซึ่งอยู่ในช่วงยืนยันของเกณฑ์ 400 lux (371–429 lx เมื่อ $U_{95}$ = 7.3 %) จึงต้องวัดซ้ำด้วยเครื่องมาตรฐาน

## ขั้นตอนกับข้อมูลจริง

1. เลือกเครื่องอ้างอิงที่ได้มาตรฐานและมีใบสอบเทียบที่ยังใช้ได้ บันทึกยี่ห้อ รุ่น S/N วันที่ และเลขที่ certificate
2. วางหัวรับแสงของเครื่องอ้างอิงกับ TSL2591 ในระนาบเดียวกัน ทิศเดียวกัน และชิดกัน ระวังเงาและการสะท้อน
3. ตั้ง `SERIAL_CSV = true` เก็บข้อมูลคู่ 100–1,000 lux เน้นใกล้ 150 / 300 / 400 / 500 lux บันทึกซ้ำหลายครั้ง
   ใช้ค่า `raw_avg_lux` เฉพาะแถวที่ `stable = 1` (ค่าเฉลี่ย 5 รอบนิ่งแล้ว ลดผลการกระพริบของ LED)
4. แบ่งเป็น `role=fit` (session 1) และ `role=val` (อีก session / อีกวัน) ใน `paired_measurements.csv`
5. รัน
   ```bash
   python fit_calibration.py paired_measurements.csv --model CAL-20261105 \
          --reference "Hioki FT3424 S/N xxxx cert yyyy 2026-mm-dd"
   ```
6. ใส่ค่าที่โปรแกรมพิมพ์ลง firmware เปิด `CALIBRATION_ENABLED` เมื่อผ่านเกณฑ์ยอมรับ (MAPE ≤ 5 %, Max APE ≤ 10 %)
7. Commit ข้อมูลคู่ + รายงาน + firmware ใน commit เดียว

## ผลจำลองที่ใช้ประเมินความแม่นยำที่คาดว่าได้รับ

รัน `python expected_bias_from_datasheet.py` แล้ว `python simulate_calibration.py` แล้ว `python make_figures.py`

| ตัวชี้วัด (ชุด validation เทียบเครื่องอ้างอิง) | ก่อนชดเชย | หลังชดเชย |
|---|---|---|
| MAPE มัธยฐาน (P95) | 37.1 % (48.8 %) | 2.5 % (4.0 %) |
| Max APE มัธยฐาน | – | 7.3 % |
| r² (ดูความเป็นเส้นตรงเท่านั้น ไม่ใช่ความแม่นยำ) | ≈ 0.996 | ≈ 0.996 |
| ความคลาดเคลื่อนเทียบค่าจริง ระดับ 95 % (U95) | – | ±7.3 % |

r² เท่ากันทั้งก่อนและหลัง เพราะการชดเชยเชิงเส้นไม่เปลี่ยนความเป็นเส้นตรง ตัวเลขนี้จึงยืนยันว่า
**r² ใช้วัดความแม่นยำไม่ได้** ต้องดู MAPE / Max APE ประกอบ (KM 9.1.5 ฉ)

### ที่มาของ bias ก่อนชดเชย (จาก datasheet)

`expected_bias_from_datasheet.py` คำนวณจากค่า typical ของ datasheet (CH0 = 1315 counts ที่ 4.98 µW/cm²,
LED 4000 K, CH1/CH0 = 0.132, gain MED 24.5x) กับสูตรของไลบรารี Adafruit (gain 25x, LUX_DF 408)
และสมมติให้ luminous efficacy ของ LED 4000 K = 300–330 lm/W ผลคือค่า Raw ≈ 0.63 เท่าของค่าจริง
(ต่ำกว่าราว 37 %) ช่วงที่เป็นไปได้ 0.50–0.76 ซึ่งสอดคล้องกับที่ [6] รายงานว่า bias ของเซนเซอร์ราคาต่ำ
ส่วนใหญ่ต่ำกว่า 40 %

### สมมติฐานของแบบจำลอง

ดู docstring ใน `simulate_calibration.py`: ความต่างสเปกตรัมของแหล่งแสง N(0, 3 %), แสงผสมธรรมชาติ N(0, 6 %),
cosine/การวาง 1.5 %, repeatability 0.4 % + 0.2 lx, drift ระหว่าง session 0.5 %,
เครื่องอ้างอิง linearity ±2 % rdg. (FT3424) และความต่างตำแหน่งระหว่างการวัดคู่ 1 %

ไฟล์ใน `sim/`: `montecarlo_summary.json`, `representative_campaign.csv` (ข้อมูลจำลองติดป้าย SIMULATED),
และรูป `fig_*.svg/png`

# คู่มือการสร้างและใช้งาน LightCheck KM

คู่มือนี้พาตั้งแต่สั่งซื้ออุปกรณ์ ประกอบ อัปโหลด firmware สอบเทียบ จนถึงใช้งานจริง
ผู้ที่ไม่เคยทำงานด้านอิเล็กทรอนิกส์มาก่อนทำตามได้ภายในครึ่งวัน

## 1. รายการอุปกรณ์

| รายการ | จำนวน | หมายเหตุ |
|---|---|---|
| Adafruit TSL2591 breakout (#1980) | 1 | หัวรับแสง I2C 0x29 |
| Wemos D1 mini (ESP8266) | 1 | ไมโครคอนโทรลเลอร์ + Wi-Fi |
| LCD1602 + I2C backpack (PCF8574) | 1 | ส่วนใหญ่ใช้ address 0x3F หรือ 0x27 |
| สาย jumper / สายไฟ 26 AWG | ~10 เส้น | |
| สาย USB-C + power bank (หรืออะแดปเตอร์มือถือ 5 V) | 1 | แหล่งจ่ายไฟภาคสนาม (บอร์ดรุ่น micro-USB ใช้สาย micro-USB) |
| กล่องพิมพ์ 3 มิติ (base + lid) | 1 ชุด | ไฟล์ STL ใน `hardware/enclosure/stl/` |
| สกรู M3, นอต 1/4"-20 (ถ้าจะใช้ขาตั้งกล้อง) | ตาม BOM | ดู `hardware/enclosure/README.md` |

ราคาและแหล่งอ้างอิงอยู่ใน [`hardware/bom.md`](../hardware/bom.md)

## 2. การต่อวงจร

ทุกอุปกรณ์ใช้บัส I2C เส้นเดียวกัน (SDA/SCL ร่วมกัน)

| Wemos D1 mini | TSL2591 | LCD1602 I2C |
|---|---|---|
| D1 (GPIO5) | SCL | SCL |
| D2 (GPIO4) | SDA | SDA |
| 3V3 | VIN | – |
| 5V | – | VCC |
| G | GND | GND |

รายละเอียด ภาพผังวงจร และข้อควรระวังเรื่อง pull-up 5 V ของ backpack อยู่ใน [wiring.md](wiring.md)

## 3. พิมพ์และประกอบกล่อง

1. พิมพ์ `lightcheck_base.stl` และ `lightcheck_lid.stl` ตามค่าที่แนะนำใน
   [`hardware/enclosure/README.md`](../hardware/enclosure/README.md) (PLA/PETG, 0.2 มม., ไม่ต้องใช้ support)
   ถ้าเครื่องพิมพ์หยาบหรือรูสกรูมักคับ ใช้ชุด `stl/loose/` แทน (ฐานและฝาต้องมาจากชุดเดียวกัน)
   ไม่แน่ใจให้พิมพ์ `stl/fit_test/hole_fit_test.stl` (~10 กรัม) เพื่อเลือกขนาดรูที่ขันสกรูได้พอดีก่อน
2. ติด LCD ใต้ฝา ยึด TSL2591 ในช่องบนฝาฝั่งที่อยู่ไกลผู้ใช้ ให้หัวรับแสงเสมอผิวฝา
3. วาง Wemos D1 mini ในช่องที่ฐาน ให้พอร์ต USB ตรงช่องผนัง
4. ปิดฝาด้วยสกรู M3 สี่ตัว
5. **ถ้าเปลี่ยนกล่อง ฝา ตำแหน่งหัวรับแสง หรือใส่ diffuser ต้องทวนสอบ calibration ใหม่** (KM 9.1.12)

## 4. อัปโหลด firmware

1. ติดตั้ง Arduino IDE 2.x
2. เพิ่มบอร์ด ESP8266: *File → Preferences → Additional boards manager URLs*
   `https://arduino.esp8266.com/stable/package_esp8266com_index.json` แล้วติดตั้ง **esp8266 by ESP8266 Community**
3. ติดตั้งไลบรารีผ่าน Library Manager
   - Adafruit TSL2591 Library (ทดสอบกับ 1.4.5) ซึ่งจะติดตั้ง Adafruit Unified Sensor และ Adafruit BusIO ให้
   - LiquidCrystal I2C (Frank de Brabander)
4. เปิด `firmware/LightCheck_TSL2591_Calibrated/LightCheck_TSL2591_Calibrated.ino`
5. เลือกบอร์ด **LOLIN(WEMOS) D1 R2 & mini** และพอร์ต แล้วกด Upload
6. เปิด Serial Monitor ที่ 115200 baud

## 5. ลำดับการเปิดเครื่อง

| LCD แสดง | ความหมาย |
|---|---|
| `LightCheck v1.1` / `Checking HW...` | เริ่มตรวจอุปกรณ์ |
| `LCD 0x27: OK` หรือ `LCD 0x3F: OK` | พบจอและแอดเดรสที่หาได้อัตโนมัติ (Serial แสดง `I2C scan:` รายการอุปกรณ์บนบัสด้วย) |
| `TSL2591: found` → `TSL2591: OK` | พบและเริ่มต้นเซนเซอร์สำเร็จ |
| `Read: OK` | อ่านค่าทดสอบได้ |
| `All systems GO` + `CAL: RAW MODE` หรือ `CAL: ON` | พร้อมใช้งาน |
| `TSL2591 NOT FOUND @ 0x29` | ตรวจสาย SDA/SCL/3V3/GND ของเซนเซอร์ |

## 6. อ่านค่าบนหน้าจอ

```
RLux: 452.31 *      <- R = Raw, C = Calibrated, ! = Calibrated นอกช่วง gain ที่สอบเทียบ
R G:25x   300ms     <- gain และ integration time ที่ใช้อ่านค่านี้
```

- ตัวเลขบนจอเป็น **ค่าเฉลี่ย 5 รอบล่าสุด** (rolling mean) เพื่อลดผลจากการกะพริบของไฟ LED 100 Hz
- `*` ท้ายบรรทัดแรก = ค่านิ่งแล้ว (ครบ 5 ค่า และ CV < 2 %) **ให้จดค่าเมื่อเห็น `*` เท่านั้น**

- `Lux: SATURATED` = แสงจ้าเกินช่วงของ gain ปัจจุบัน เครื่องจะลด gain เองในรอบถัดไป
- v1.1 ล็อกช่วงแสงสำนักงานราว 100–2,900 lux ไว้ที่ gain 25x เพื่อให้ใช้สมการชดเชยชุดเดียว

## 7. บันทึกข้อมูลผ่าน Serial

- โหมดปกติ: `Gain=25x Tint=300ms Full=... IR=... RawLux=... RawAvg=... N=5 CV=0.42% Stable=Y CalLux=... CalMode=OFF CalScope=OK`
- โหมด CSV (ตั้ง `SERIAL_CSV = true`): ใช้เก็บข้อมูลคู่สำหรับ calibration แล้วนำค่า `raw_avg_lux`
  ของแถวที่ `stable = 1` ไปวางในคอลัมน์ `raw_lux` ของ `calibration/paired_measurements.csv`

## 8. สอบเทียบและเปิดใช้การชดเชย

1. เก็บข้อมูลคู่กับ lux meter มาตรฐานที่มีใบสอบเทียบ (ดู [calibration/README.md](../calibration/README.md))
2. เก็บอย่างน้อย 2 session: `fit` ใช้สร้างสมการ และ `val` ใช้ทวนสอบเท่านั้น
3. รัน `python calibration/fit_calibration.py calibration/paired_measurements.csv --model CAL-YYYYMMDD --reference "..."`
4. ถ้ารายงานขึ้น ACCEPT ให้คัดลอกค่าที่โปรแกรมพิมพ์ไปใส่ใน firmware แล้วอัปโหลดใหม่
5. commit ไฟล์ข้อมูล รายงาน และ firmware พร้อมกันใน commit เดียว เพื่อให้ตรวจย้อนกลับได้

## 9. ใช้งานภาคสนาม

ทำตาม [measurement-SOP.md](measurement-SOP.md) และตัดสินผลด้วย guard band
จุดที่อยู่ใกล้เกณฑ์หรือจะใช้เป็นหลักฐาน Green Office ต้องยืนยันด้วยเครื่องมาตรฐานทุกครั้ง

## 10. ดูแลรักษา

- เช็ดหัวรับแสงด้วยผ้าไมโครไฟเบอร์แห้ง ห้ามใช้แอลกอฮอล์กับ LCD
- เทียบกับเครื่องอ้างอิงหลายระดับแสงก่อนเริ่มสำรวจรอบใหญ่ทุกครั้งเพื่อดู drift
- ถ้าเปลี่ยนเซนเซอร์ตัวใหม่ เปลี่ยนไลบรารี หรือแก้ logic การชดเชย ต้องเพิ่มเวอร์ชันและทวนสอบใหม่

ปัญหาที่พบบ่อยและวิธีแก้อยู่ใน [troubleshooting.md](troubleshooting.md)

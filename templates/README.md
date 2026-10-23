# แบบบันทึกผลการสำรวจแสง

- `light-survey-form.csv` แบบบันทึกเปล่า (เปิดด้วย Excel / Google Sheets ได้ทันที ภาษาไทยไม่เพี้ยน)
- `light-survey-form_example-8x6m.csv` ตัวอย่างที่ `tools/survey/grid_planner.py` สร้างให้ห้อง 8 × 6 ม. (12 จุดกริด + 6 จุดทำงาน)

| คอลัมน์ | ความหมาย |
|---|---|
| point_id | `A<แถว><คอลัมน์>` = จุดกริด 2×2 ม., `Wnn` = จุดทำงาน |
| height_cm | 75 สำหรับจุดพื้นที่, `desk` = ระดับผิวโต๊ะ |
| raw_lux / corrected_lux | ค่า R และ C จากเครื่อง (ดูโหมดบน LCD) |
| gain / tint_ms | จาก Serial หรือบรรทัดที่ 2 ของ LCD |
| decision | PASS / VERIFY / FAIL ตามกติกา guard band ใน SOP |
| verify_with_reference / reference_lux | ผลจากเครื่องมาตรฐานที่มีใบสอบเทียบ (ถ้าต้องยืนยัน) |
| lamps_on / curtain / daylight / time | สภาวะขณะวัด |

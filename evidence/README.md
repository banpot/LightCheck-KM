# Evidence

เก็บภาพหลักฐานการตรวจวัดและการปรับปรุงตาม Green Office 5.2.1 (5)

```
evidence/
  YYYY-MM-DD_<room>/
    before_<point>.jpg
    after_<point>.jpg
    reference-meter_<point>.jpg
```

ก่อน commit:
- ปิดบังใบหน้า ชื่อ เอกสาร และหน้าจอที่มีข้อมูลส่วนบุคคล
- อย่าเก็บผังอาคารที่มีข้อมูลความปลอดภัยใน repository สาธารณะ
- ใส่ชื่อไฟล์ให้ตรงกับ `point_id` ในแบบบันทึก

## ภาพต้นแบบ

- `2026-10_enclosure-print/` พิมพ์กล่องรุ่นแรก
- `2026-10_prototype/` พิมพ์ฝากล่องด้วย Creality Ender-6 และเครื่อง LightCheck KM ที่ประกอบเสร็จ (firmware v1.1.1)

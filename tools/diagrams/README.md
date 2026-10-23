# Diagram generators

สร้างภาพใน `docs/img/` แบบ SVG ที่ฝังฟอนต์ (Kanit, IBM Plex Sans Thai, IBM Plex Mono)

| สคริปต์ | ผลลัพธ์ |
|---|---|
| `build_wiring.py` | `wiring_diagram.svg` ผังวงจร D1 mini + TSL2591 + LCD1602 บนบัส I²C ร่วม และแหล่งจ่ายไฟ USB-C 5 V (power bank) |
| `build_components.py` | `component_*.svg` ภาพอุปกรณ์แต่ละชิ้น |
| `build_flow.py` | `firmware_flow.svg`, `pin_table.svg` |

```bash
cd tools/diagrams && npm i            # ฟอนต์จาก @fontsource + playwright
python3 build_wiring.py && python3 build_components.py && python3 build_flow.py
node render.js ../../docs/img/wiring_diagram.svg ../../docs/img/wiring_diagram.png 3600   # PNG
```

"""
LightCheck KM - measurement-point planner (algorithmic SOP helper)
==================================================================
Implements the area-measurement rule used in the SOP (DLPW 2561 criteria [3]):
  * horizontal plane 75 cm above the floor
  * one point at the centre of every 2 m x 2 m cell (partial cells at the
    room edge are merged into the neighbouring cell when < 1 m)
  * plus every workstation (measured at the task plane, e.g. desk top)
and writes a pre-filled survey form (CSV) so every surveyor records the
same fields in the same order.

Usage:
  python grid_planner.py --room R-201 --width 8 --length 6 \
         --desks "1.2,4.8;3.0,4.8;5.0,1.2" --out ../../templates/R-201_survey.csv
"""
from __future__ import annotations

import argparse
import csv
import math

FIELDS = ["room", "point_id", "type", "x_m", "y_m", "height_cm", "raw_lux", "corrected_lux",
          "gain", "tint_ms", "decision", "verify_with_reference", "reference_lux",
          "lamps_on", "curtain", "daylight", "time", "surveyor", "notes"]


def axis_centres(length_m: float, cell: float = 2.0) -> list[float]:
    """Cell centres along one axis; a remainder < cell/2 is merged."""
    n = max(1, int(length_m // cell))
    rem = length_m - n * cell
    if rem >= cell / 2:
        n += 1
    step = length_m / n
    return [round(step * (i + 0.5), 2) for i in range(n)]


def plan(width: float, length: float, desks: list[tuple[float, float]] | None = None, cell: float = 2.0):
    xs, ys = axis_centres(width, cell), axis_centres(length, cell)
    pts = [dict(point_id=f"A{j + 1}{chr(65 + i)}", type="area", x_m=x, y_m=y, height_cm=75)
           for j, y in enumerate(ys) for i, x in enumerate(xs)]
    for k, (x, y) in enumerate(desks or []):
        pts.append(dict(point_id=f"W{k + 1:02d}", type="workstation", x_m=x, y_m=y, height_cm="desk"))
    return pts, xs, ys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--room", required=True)
    ap.add_argument("--width", type=float, required=True, help="room width (m), x axis")
    ap.add_argument("--length", type=float, required=True, help="room length (m), y axis")
    ap.add_argument("--desks", default="", help='"x,y;x,y" workstation positions (m)')
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    desks = [tuple(map(float, d.split(","))) for d in a.desks.split(";") if d.strip()]
    pts, xs, ys = plan(a.width, a.length, desks)
    n_area = sum(p["type"] == "area" for p in pts)
    print(f"{a.room}: {a.width} x {a.length} m -> {len(xs)} x {len(ys)} = {n_area} area points "
          f"(+{len(desks)} workstations) ; ~{math.ceil(len(pts) * 1.5)} min at 1.5 min/point")
    out = a.out or f"{a.room}_survey.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for p in pts:
            w.writerow({"room": a.room, **p})
    print("survey form ->", out)


if __name__ == "__main__":
    main()

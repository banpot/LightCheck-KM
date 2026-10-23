"""
Estimate the printed weight and filament cost of the enclosure (algorithmic,
no slicer needed). Each STL is cut into 0.4 mm layers; in every layer the
outer 1.2 mm of each outline is solid perimeter (3 walls x 0.4 mm), horizontal
surfaces get 0.8 mm solid top/bottom skin, and the remaining core is 20 % infill.

Usage:  python estimate_filament.py [--price 480] [--density 1.24]
Requires: trimesh, shapely, rtree  (pip install trimesh shapely rtree)
"""
import argparse
import os

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "..", "stl")


def printed_volume(mesh, layer=0.4, perimeter=1.2, skin=0.8, infill=0.20):
    z0, z1 = mesh.bounds[0][2], mesh.bounds[1][2]
    secs = mesh.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1],
                                   heights=list(np.arange(z0 + layer / 2, z1, layer)))
    a_all = a_core = 0.0
    for s in secs:
        if s is None:
            continue
        for poly in s.polygons_full:
            a_all += poly.area
            a_core += poly.buffer(-perimeter).area
    v_all, v_core = a_all * layer, a_core * layer
    horiz = mesh.area_faces[np.abs(mesh.face_normals[:, 2]) > 0.95].sum()
    v_skin = min(horiz * skin, v_core)
    return v_all, (v_all - v_core) + v_skin + infill * (v_core - v_skin)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", type=float, default=480.0, help="filament price, THB per kg (PLA+)")
    ap.add_argument("--density", type=float, default=1.24, help="g/cm3 (PLA/PLA+ ~1.24)")
    ap.add_argument("--waste", type=float, default=2.0, help="skirt/purge grams")
    a = ap.parse_args()
    total = 0.0
    for part in ("lightcheck_base", "lightcheck_lid"):
        m = trimesh.load(os.path.join(STL, part + ".stl"))
        v_all, v_print = printed_volume(m)
        g = v_print / 1000 * a.density
        total += g
        print(f"{part:16s} solid {v_all / 1000:5.1f} cm3 -> printed {v_print / 1000:5.1f} cm3 = {g:5.1f} g "
              f"({v_print / v_all * 100:.0f} % of solid)")
    total += a.waste
    print(f"total incl. {a.waste:.0f} g skirt/purge: {total:.1f} g  ->  {total / 1000 * a.price:.1f} THB "
          f"at {a.price:.0f} THB/kg")


if __name__ == "__main__":
    main()

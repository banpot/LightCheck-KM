"""
LightCheck KM - office lighting "digital twin" (algorithmic demonstration)
=========================================================================
!!! SIMULATION - a representative office, NOT a measured room !!!

Shows the KM loop  measure -> analyse -> improve -> re-measure  end to end
with physics instead of field data:
  * direct light: Lambertian LED panels, E = I0 cos^4(theta) / h^2, I0 = Phi/pi
  * indirect light: uniform inter-reflection, E_ind = Phi*MF*rho / (A_surf*(1-rho))
  * grid: 2 m x 2 m cell centres at 75 cm (grid_planner.py) + workstations
  * the pre-survey reading of every point is passed through the calibrated
    LightCheck error model (U95 from calibration/sim) and the guard-band rule:
        corrected >= thr*(1+U95)  -> PASS
        corrected <  thr*(1-U95)  -> FAIL
        otherwise                 -> VERIFY with the calibrated reference meter
Criteria (DLPW 2561 [2]): office area average >= 300 lx and minimum >= 150 lx;
routine office work at the workstation 400-500 lx (>= 400 used as the target).

Usage: python office_lighting_sim.py   (writes ../../docs/img/office_twin_*.png/svg + json)
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np

from grid_planner import plan

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_IMG = os.path.join(ROOT, "docs", "img")
U95 = 7.3  # % - default; replaced by calibration/sim/montecarlo_summary.json if present

ROOM = dict(name="ห้องตัวอย่าง (จำลอง) 8 × 6 ม.", W=8.0, L=6.0, H=2.7, plane=0.75, rho=0.45)
PANEL_LM = 4500.0                 # LED panel/troffer, initial lumens (assumption)
LUMINAIRES = [(x, y) for y in (1.5, 4.5) for x in (1.33, 4.0, 6.67)]
DESKS = [(1.9, 1.25), (4.6, 1.25), (7.1, 1.5), (1.9, 4.75), (4.0, 3.0), (7.2, 5.3)]

SCENARIOS = {
    "before": dict(label="ก่อนปรับปรุง", mf=0.75, out={5: 0.0, 2: 0.60}, task={}),
    # luminaire #5 (row 2, right) dead, #2 aged to 60 %, dirty diffusers (MF 0.75)
    "after": dict(label="หลังปรับปรุง", mf=0.90, out={}, task={5: 200.0}),
    # replace/clean lamps (MF 0.90) + 1 task lamp at the far-corner desk W06
}


def illuminance(xx, yy, sc):
    h = ROOM["H"] - ROOM["plane"]
    E = np.zeros_like(xx)
    phi_tot = 0.0
    for k, (lx, ly) in enumerate(LUMINAIRES):
        phi = PANEL_LM * sc["mf"] * sc["out"].get(k, 1.0)
        phi_tot += phi
        I0 = phi / np.pi
        d2 = (xx - lx) ** 2 + (yy - ly) ** 2 + h ** 2
        cos = h / np.sqrt(d2)
        E += I0 * cos ** 4 / h ** 2
    A = 2 * ROOM["W"] * ROOM["L"] + 2 * (ROOM["W"] + ROOM["L"]) * ROOM["H"]
    E += phi_tot * ROOM["rho"] / (A * (1 - ROOM["rho"]))
    return E


def decide(value, thr, u95):
    if value >= thr * (1 + u95 / 100):
        return "PASS"
    if value < thr * (1 - u95 / 100):
        return "FAIL"
    return "VERIFY"


def run(u95=U95, seed=7):
    rng = np.random.default_rng(seed)
    pts, xs, ys = plan(ROOM["W"], ROOM["L"], DESKS)
    gx, gy = np.meshgrid(np.linspace(0, ROOM["W"], 161), np.linspace(0, ROOM["L"], 121))
    res = {"_note": "SIMULATION - representative office, not measured", "room": ROOM, "u95_pct": u95,
           "grid_x": xs, "grid_y": ys, "scenarios": {}}
    for key, sc in SCENARIOS.items():
        Emap = illuminance(gx, gy, sc)
        rows = []
        for p in pts:
            e = float(illuminance(np.array(p["x_m"]), np.array(p["y_m"]), sc))
            if p["type"] == "workstation":
                e += sc["task"].get(int(p["point_id"][1:]) - 1, 0.0)
            reading = e * (1 + rng.normal(0, u95 / 100 / 1.96))      # calibrated LightCheck
            thr = 150 if p["type"] == "area" else 400
            rows.append(dict(**p, true_lux=round(e, 1), reading_lux=round(reading, 1),
                             decision=decide(reading, thr, u95) if p["type"] == "workstation" else None))
        area = [r for r in rows if r["type"] == "area"]
        avg = float(np.mean([r["reading_lux"] for r in area]))
        mn = float(np.min([r["reading_lux"] for r in area]))
        res["scenarios"][key] = dict(
            label=sc["label"], points=rows, area_avg_lux=avg, area_min_lux=mn,
            area_avg_decision=decide(avg, 300, u95), area_min_decision=decide(mn, 150, u95),
            uniformity=mn / avg, map_min=float(Emap.min()), map_max=float(Emap.max()),
            ws_pass=sum(r["decision"] == "PASS" for r in rows if r["type"] == "workstation"),
            ws_verify=sum(r["decision"] == "VERIFY" for r in rows if r["type"] == "workstation"),
            ws_fail=sum(r["decision"] == "FAIL" for r in rows if r["type"] == "workstation"),
            n_ws=len(DESKS), n_area=len(area))
        res["scenarios"][key]["_map"] = Emap
    return res, gx, gy


def figure(res, gx, gy):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    from matplotlib.colors import LinearSegmentedColormap
    for f in glob.glob(os.path.join(ROOT, "tools", "fonts", "*.ttf")):
        fm.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "IBM Plex Sans Thai", "font.size": 15, "svg.fonttype": "path"})
    INK, INK2 = "#14202B", "#5B6B78"
    # sequential single-hue ramp (blue 100 -> 650 of the dataviz reference palette)
    cmap = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"])
    vmin, vmax = 100, 700
    STATUS = {"PASS": ("#0ca30c", "✓ ผ่าน"), "VERIFY": ("#fab219", "? ตรวจยืนยัน"), "FAIL": ("#d03b3b", "× ไม่ผ่าน")}
    fig, axes = plt.subplots(1, 2, figsize=(16.5, 6.6), gridspec_kw=dict(wspace=0.08))
    for ax, key in zip(axes, ["before", "after"]):
        s = res["scenarios"][key]
        im = ax.imshow(s["_map"], origin="lower", extent=[0, ROOM["W"], 0, ROOM["L"]], cmap=cmap,
                       vmin=vmin, vmax=vmax, interpolation="bilinear")
        for gxv in np.arange(0, ROOM["W"] + 0.01, 2):
            ax.axvline(gxv, color="white", lw=1, alpha=0.6)
        for gyv in np.arange(0, ROOM["L"] + 0.01, 2):
            ax.axhline(gyv, color="white", lw=1, alpha=0.6)
        for k, (lx, ly) in enumerate(LUMINAIRES):
            dead = SCENARIOS[key]["out"].get(k, 1.0) == 0.0
            ax.add_patch(plt.Rectangle((lx - 0.3, ly - 0.3), 0.6, 0.6, fill=not dead, facecolor="#FFF6D5", zorder=4,
                                       edgecolor=INK if not dead else "#d03b3b", lw=1.6, ls="-" if not dead else "--"))
            if dead:
                ax.text(lx, ly - 0.42, "โคมเสีย", ha="center", va="top", fontsize=12, color="#d03b3b", zorder=5)
        for p in s["points"]:
            if p["type"] == "area":
                ax.text(p["x_m"], p["y_m"], f"{p['reading_lux']:.0f}", ha="center", va="center", zorder=6,
                        fontsize=13.5, color=INK, bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                                                           alpha=0.92, edgecolor=INK2, lw=0.8))
            else:
                col, _ = STATUS[p["decision"]]
                ax.plot(p["x_m"], p["y_m"], "s", ms=14, color=col, mec="white", mew=2, zorder=7)
                ax.text(min(max(p["x_m"], 0.75), ROOM["W"] - 0.75), p["y_m"] + 0.27,
                        f"{p['point_id']} · {p['reading_lux']:.0f}", fontsize=12.5, ha="center", va="bottom",
                        zorder=7, color=INK, bbox=dict(facecolor="white", alpha=0.9, edgecolor="none", pad=1.0))
        ax.set_xlim(0, ROOM["W"]), ax.set_ylim(0, ROOM["L"]), ax.set_aspect("equal")
        ax.set_xticks(range(0, 9, 2)), ax.set_yticks(range(0, 7, 2))
        ax.tick_params(colors=INK2, labelsize=12)
        verdict = "ผ่าน" if s["area_avg_decision"] == "PASS" and s["area_min_decision"] == "PASS" else "ไม่ผ่าน/ต้องยืนยัน"
        ax.set_title(f"{s['label']}: เฉลี่ย {s['area_avg_lux']:.0f} lx · ต่ำสุด {s['area_min_lux']:.0f} lx · "
                     f"โต๊ะผ่าน {s['ws_pass']}/{s['n_ws']}", fontsize=15.5, color=INK, loc="left")
    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.015)
    cb.set_label("ความส่องสว่างที่ระนาบ 75 ซม. (lux)", color=INK, labelpad=12)
    cb.outline.set_visible(False)
    handles = [plt.Line2D([], [], marker="s", ls="", ms=12, color=c, mec="white", label=l) for c, l in STATUS.values()]
    handles.append(plt.Line2D([], [], marker="s", ls="", ms=12, color="white", mec=INK2, label="ค่าที่จุดกริด 2×2 ม. (lux)"))
    handles.append(plt.Rectangle((0, 0), 1, 1, facecolor="#FFF6D5", edgecolor=INK, label="โคมไฟ"))
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=13.5, bbox_to_anchor=(0.45, -0.04))
    fig.text(0.125, 0.965, "ผลจำลอง (Simulation) · ห้องตัวอย่าง ไม่ใช่ข้อมูลวัดจริง · ตัดสินด้วย guard band "
             f"±{res['u95_pct']:.1f}%", fontsize=12.5, color=INK2, style="italic")
    os.makedirs(OUT_IMG, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_IMG, f"office_twin_before_after.{ext}"), dpi=300, bbox_inches="tight",
                    transparent=(ext == "svg"))
    plt.close(fig)


def figure_poster(res):
    """Compact before/after version sized for one 22 cm poster column (large type)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    from matplotlib.colors import LinearSegmentedColormap
    for f in glob.glob(os.path.join(ROOT, "tools", "fonts", "*.ttf")):
        fm.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "IBM Plex Sans Thai", "font.size": 17, "svg.fonttype": "path"})
    INK, INK2 = "#14202B", "#5B6B78"
    cmap = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"])
    STATUS = {"PASS": ("#0ca30c", "✓ ผ่าน"), "VERIFY": ("#fab219", "? ยืนยัน"), "FAIL": ("#d03b3b", "× ไม่ผ่าน")}
    fig, axes = plt.subplots(1, 2, figsize=(8.75, 4.6), gridspec_kw=dict(wspace=0.06))
    for ax, key in zip(axes, ["before", "after"]):
        sc = res["scenarios"][key]
        im = ax.imshow(sc["_map"], origin="lower", extent=[0, ROOM["W"], 0, ROOM["L"]], cmap=cmap,
                       vmin=100, vmax=700, interpolation="bilinear")
        for k, (lx, ly) in enumerate(LUMINAIRES):
            dead = SCENARIOS[key]["out"].get(k, 1.0) == 0.0
            ax.add_patch(plt.Rectangle((lx - 0.3, ly - 0.3), 0.6, 0.6, fill=not dead, facecolor="#FFF6D5", zorder=4,
                                       edgecolor=INK if not dead else "#d03b3b", lw=1.4, ls="-" if not dead else "--"))
        for p in sc["points"]:
            if p["type"] == "workstation":
                col, _ = STATUS[p["decision"]]
                ax.plot(p["x_m"], p["y_m"], "s", ms=13, color=col, mec="white", mew=2, zorder=7)
            else:
                ax.plot(p["x_m"], p["y_m"], "o", ms=5, color="white", mec=INK, mew=1, zorder=6)
        ax.set_xticks([]), ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(f"{sc['label']}\nเฉลี่ย {sc['area_avg_lux']:.0f} · ต่ำสุด {sc['area_min_lux']:.0f} lx\nโต๊ะผ่าน {sc['ws_pass']}/{sc['n_ws']}",
                     fontsize=16, color=INK, linespacing=1.35)
    cb = fig.colorbar(im, ax=axes, orientation="horizontal", fraction=0.06, pad=0.04, aspect=40)
    cb.set_label("lux ที่ระนาบ 75 ซม.", color=INK, fontsize=15)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=13, colors=INK2)
    handles = [plt.Line2D([], [], marker="s", ls="", ms=12, color=c, mec="white", label=l) for c, l in STATUS.values()]
    handles.append(plt.Line2D([], [], marker="o", ls="", ms=6, color="white", mec=INK, label="จุดกริด 2×2 ม."))
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=14.5, bbox_to_anchor=(0.5, -0.2),
               handletextpad=0.3, columnspacing=1.0)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_IMG, f"office_twin_poster.{ext}"), dpi=300, bbox_inches="tight",
                    transparent=(ext == "svg"))
    plt.close(fig)


def main():
    u95 = U95
    summ = os.path.join(ROOT, "calibration", "sim", "montecarlo_summary.json")
    if os.path.exists(summ):
        u95 = json.load(open(summ, encoding="utf-8"))["guard_band_pct"]
    res, gx, gy = run(u95)
    figure(res, gx, gy)
    figure_poster(res)
    out = {k: v for k, v in res.items() if k != "scenarios"}
    out["scenarios"] = {k: {kk: vv for kk, vv in v.items() if kk != "_map"} for k, v in res["scenarios"].items()}
    with open(os.path.join(ROOT, "tools", "survey", "office_twin_result.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    for k, s in out["scenarios"].items():
        print(f"{s['label']}: avg {s['area_avg_lux']:.0f} ({s['area_avg_decision']}), min {s['area_min_lux']:.0f} "
              f"({s['area_min_decision']}), U={s['uniformity']:.2f}, workstations PASS {s['ws_pass']} / VERIFY "
              f"{s['ws_verify']} / FAIL {s['ws_fail']}; map {s['map_min']:.0f}-{s['map_max']:.0f}")
        for p in s["points"]:
            if p["type"] == "workstation":
                print(f"    {p['point_id']} true {p['true_lux']:.0f} read {p['reading_lux']:.0f} -> {p['decision']}")


if __name__ == "__main__":
    main()

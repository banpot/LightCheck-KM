"""
Figures for the calibration simulation (poster + docs).
Reads calibration/sim/_figdata.npz and montecarlo_summary.json produced by
simulate_calibration.py.  Every figure is stamped "ผลจำลอง (Simulation)".
Usage: python make_figures.py [--fonts ../tools/fonts]
"""
import argparse
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
import numpy as np                                  # noqa: E402
from matplotlib import font_manager as fm           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "sim")

# Chart palette (validated with the dataviz palette checker: lightness band,
# chroma, CVD separation, contrast all PASS on white)
C_REF = "#1F5F9E"    # reference meter / SU blue
C_RAW = "#DD5A14"    # raw TSL2591
C_COR = "#008A70"    # compensated
INK, INK2, GRID = "#14202B", "#5B6B78", "#E3E7EB"
FONT_K, FIG_K, SUFFIX = 1.0, 1.0, ""     # --poster: bigger type relative to the figure


def fs(x):
    return x * FONT_K
BAND_REF, BAND_U95 = "#D6E6F4", "#D3EEE7"


def setup_fonts(font_dir):
    for f in glob.glob(os.path.join(font_dir, "*.ttf")):
        fm.fontManager.addfont(f)
    plt.rcParams.update({
        "font.family": "IBM Plex Sans Thai", "font.size": 17 * FONT_K,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "axes.titlesize": 20 * FONT_K,
        "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 1.0, "grid.linestyle": "-",
        "legend.frameon": False, "svg.fonttype": "path", "savefig.dpi": 300,
    })


def stamp(ax, text="ผลจำลอง (Simulation) · ไม่ใช่ข้อมูลวัดจริง", x=1.0, y=1.02, ha="right"):
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va="bottom",
            fontsize=fs(13), color=INK2, style="italic")


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(SIM, f"{name}{SUFFIX}.{ext}"), bbox_inches="tight", transparent=(ext == "svg"))
    plt.close(fig)


def fig_scatter(d, s):
    fig, ax = plt.subplots(figsize=(9.0 * FIG_K, 6.2 * FIG_K))
    x = np.linspace(0, 1150, 50)
    ax.fill_between(x, x * 0.98, x * 1.02, color=BAND_REF, lw=0, zorder=1)
    ax.plot(x, x, color=INK2, lw=1.5, zorder=2)
    ax.scatter(d["val_ref"], d["val_raw"], s=70, color=C_RAW, edgecolor="white", linewidth=1.6, zorder=4,
               label="TSL2591 ก่อนชดเชย (Raw)")
    ax.scatter(d["val_ref"], d["val_cor"], s=70, color=C_COR, edgecolor="white", linewidth=1.6, zorder=5,
               label="หลังชดเชย")
    a, b = float(d["a"]), float(d["b"])
    ax.text(1120, 360, f"Raw อ่านต่ำกว่าจริง ≈{abs(s['representative']['raw_vs_ref']['bias_pct']):.0f}%",
            color=INK, fontsize=fs(16), ha="right")
    ax.text(1120, 40, f"ตัวอย่างสมการ: E = {a:.3f}·Raw {'+' if b >= 0 else '−'} {abs(b):.1f}",
            color=INK, fontsize=fs(15), ha="right", va="bottom")
    ax.set_xlim(0, 1150), ax.set_ylim(0, 1150)
    ax.set_xlabel("ค่าจากเครื่องอ้างอิงมาตรฐาน (lux)")
    ax.set_ylabel("ค่าที่เครื่องต้นแบบแสดง (lux)")
    h, l = ax.get_legend_handles_labels()
    import matplotlib.patches as mp
    h.append(mp.Patch(color=BAND_REF)); l.append("±2% ของเครื่องอ้างอิง")
    h.append(plt.Line2D([], [], color=INK2, lw=1.5)); l.append("y = x (ตรงกับเครื่องอ้างอิง)")
    ax.legend(h, l, loc="upper left", fontsize=fs(14.5), handletextpad=0.4)
    if not SUFFIX:
        ax.set_title("ชุดทวนสอบ (validation) 24 จุด แยกจากชุดสร้างสมการ", loc="left", fontsize=fs(17), color=INK, pad=34)
        stamp(ax, y=1.01, ha="left", x=0.0)
    else:
        stamp(ax, y=1.01, ha="right", x=1.0)
    save(fig, "fig_cal_scatter")


def fig_error(d, s):
    u95 = s["guard_band_pct"]
    fig, ax = plt.subplots(figsize=(9.0 * FIG_K, 5.4 * FIG_K))
    ref = d["val_ref"]
    e_raw = (d["val_raw"] - ref) / ref * 100
    e_cor = (d["val_cor"] - ref) / ref * 100
    ax.axhspan(-u95, u95, color=BAND_U95, lw=0, zorder=1)
    ax.axhspan(-2, 2, color=BAND_REF, lw=0, zorder=1.5)
    ax.axhline(0, color=INK2, lw=1.2, zorder=2)
    lo_y = float(np.min(e_raw)) - 7
    mid_y = (float(np.max(e_raw)) + (-u95)) / 2
    for thr in (150, 300, 400, 500):
        ax.axvline(thr, color=GRID, lw=1.4, zorder=1.8)
        ax.text(thr, mid_y, f"{thr} lx", ha="center", va="center", fontsize=fs(13), color=INK2,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    ax.scatter(ref, e_raw, s=70, color=C_RAW, edgecolor="white", linewidth=1.6, zorder=4, label="ก่อนชดเชย")
    ax.scatter(ref, e_cor, s=70, color=C_COR, edgecolor="white", linewidth=1.6, zorder=5, label="หลังชดเชย")
    ax.text(1040, u95 + 0.8, f"ความคลาดเคลื่อนที่คาดหวัง ±{u95:.1f}% (95%)", ha="right", fontsize=fs(14), color=INK)
    ax.text(1040, float(np.max(e_raw)) + 2.5, f"Raw: เฉลี่ย {np.mean(e_raw):.0f}%", ha="right", fontsize=fs(14), color=INK)
    ax.set_xlim(60, 1080), ax.set_ylim(lo_y, 14)
    ax.set_xlabel("ค่าจากเครื่องอ้างอิง (lux)  ·  เส้นแนวตั้ง = เกณฑ์ 150 / 300 / 400 / 500 lux")
    ax.set_ylabel("ความคลาดเคลื่อน (%)")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=fs(14.5), ncol=2)
    stamp(ax, y=1.03)
    save(fig, "fig_cal_error")


def fig_mc(d, s):
    fig, ax = plt.subplots(figsize=(9.0 * FIG_K, 4.6 * FIG_K))
    bins = np.arange(0, 60.5, 0.5)
    ax.hist(d["mc_mape_raw"], bins=bins, color=C_RAW, alpha=0.9, label="ก่อนชดเชย", zorder=3)
    ax.hist(d["mc_mape_cor"], bins=bins, color=C_COR, alpha=0.95, label="หลังชดเชย", zorder=4)
    p = s["m_cor_ref"]["mape"]; r = s["m_raw_ref"]["mape"]
    ymax = ax.get_ylim()[1]
    ax.text(p["p95"] + 1.2, ymax * 0.78,
            f"หลังชดเชย MAPE\nมัธยฐาน {p['p50']:.1f}%  ·  P95 {p['p95']:.1f}%", fontsize=fs(14.5), color=INK, va="top")
    ax.text(r["p50"], ymax * 0.32, f"ก่อนชดเชย\nมัธยฐาน {r['p50']:.0f}%", fontsize=fs(14.5), color=INK, ha="center")
    ax.set_xlim(0, 60)
    ax.set_xlabel("MAPE เทียบเครื่องอ้างอิง (%)  ·  ยิ่งต่ำยิ่งแม่น")
    ax.set_ylabel("จำนวนรอบจำลอง")
    ax.legend(loc="upper right", fontsize=fs(14.5))
    ax.set_title(f"Monte Carlo {s['n_campaigns']:,} รอบ (สุ่มตัวเครื่อง เครื่องอ้างอิง และแหล่งแสงใหม่ทุกรอบ)",
                 loc="left", fontsize=fs(16), color=INK, pad=34)
    stamp(ax, y=1.01, ha="left", x=0.0)
    save(fig, "fig_mc_mape")


def fig_decision(s):
    da = s["decision_analysis"]
    thr = ["150", "300", "400"]
    raw = [da[t]["wrong_raw_pct"] for t in thr]
    cor = [da[t]["wrong_corrected_pct"] for t in thr]
    rule = [da[t]["wrong_decisions_after_guard_band_pct"] for t in thr]
    fig, ax = plt.subplots(figsize=(9.0 * FIG_K, 4.8 * FIG_K))
    x = np.arange(len(thr)); w = 0.26
    for i, (vals, col, lab) in enumerate([(raw, C_RAW, "ใช้ Raw Lux ตรง ๆ"),
                                          (cor, C_COR, "หลังชดเชย"),
                                          (rule, C_REF, f"หลังชดเชย + Guard band ±{s['guard_band_pct']:.1f}% (จุดใกล้เกณฑ์ส่งยืนยัน)")]):
        bars = ax.bar(x + (i - 1) * (w + 0.02), vals, width=w, color=col, label=lab, zorder=3)
        for bx, v in zip(bars, vals):
            ax.text(bx.get_x() + bx.get_width() / 2, v + 0.8, f"{v:.1f}%" if v >= 0.95 else f"{v:.2f}%",
                    ha="center", va="bottom", fontsize=fs(13.5), color=INK)
    ax.set_xticks(x, [f"เกณฑ์ {t} lux" for t in thr])
    ax.set_ylabel("ตัดสินผ่าน/ไม่ผ่านผิด (% ของจุด)")
    ax.set_ylim(0, max(raw) * 1.15)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=fs(14), ncol=1)
    ax.text(0.99, 0.97, "ผลจำลอง (Simulation) · ไม่ใช่ข้อมูลวัดจริง", transform=ax.transAxes, ha="right",
            va="top", fontsize=fs(13), color=INK2, style="italic")
    save(fig, "fig_decision")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", default=os.path.join(HERE, "..", "tools", "fonts"))
    ap.add_argument("--poster", action="store_true", help="larger type for the 80x100 cm poster (*_poster.svg)")
    args = ap.parse_args()
    global FONT_K, FIG_K, SUFFIX
    if args.poster:
        FONT_K, FIG_K, SUFFIX = 1.0, 0.74, "_poster"
    setup_fonts(args.fonts)
    d = np.load(os.path.join(SIM, "_figdata.npz"))
    s = json.load(open(os.path.join(SIM, "montecarlo_summary.json"), encoding="utf-8"))
    fig_scatter(d, s); fig_error(d, s); fig_mc(d, s); fig_decision(s)
    print("figures written to", SIM)


if __name__ == "__main__":
    main()

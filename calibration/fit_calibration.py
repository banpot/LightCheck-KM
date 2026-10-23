"""
Fit and validate the LightCheck compensation model from REAL paired data.

Usage:
    python fit_calibration.py paired_measurements.csv [--model CAL-2026-01] \
        [--reference "Hioki FT3424 S/N xxxx, cert. no. yyyy, cal. 2026-mm-dd"]

The CSV must contain rows with role = fit (used to derive a, b) and role = val
(an independent session, used ONLY to report accuracy) - KM doc 9.1.5 (d).
Writes calibration_report_<model>.md next to the CSV and prints the firmware
constants to paste into LightCheck_TSL2591_Calibrated.ino.
"""
import argparse
import datetime as dt
import os
import sys

import numpy as np

import lightcheck_cal as lc

ACCEPT_MAPE = 5.0      # % - suggested acceptance limits for enabling CAL (edit
ACCEPT_MAX_APE = 10.0  # %   in calibration/README.md if the team agrees others)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--model", default=f"CAL-{dt.date.today():%Y%m%d}")
    ap.add_argument("--reference", default="REFERENCE-METER-ID")
    a = ap.parse_args()

    rows = lc.load_pairs(a.csv)
    fit = [r for r in rows if r.get("role", "").strip().lower() == "fit"]
    val = [r for r in rows if r.get("role", "").strip().lower() == "val"]
    if len(fit) < 8 or len(val) < 5:
        sys.exit(f"need >= 8 fit rows and >= 5 val rows (have {len(fit)} / {len(val)})")
    gains = sorted({r.get("gain", "") for r in rows})
    if len(gains) > 1:
        print(f"WARNING: rows were taken at several gains {gains}; fit one model per gain.")

    raw_f = [r["raw_lux"] for r in fit]; ref_f = [r["ref_lux"] for r in fit]
    raw_v = np.array([r["raw_lux"] for r in val]); ref_v = np.array([r["ref_lux"] for r in val])
    A, B = lc.fit_linear(raw_f, ref_f)
    cor_v = lc.apply(A, B, raw_v)
    before, after = lc.metrics(raw_v, ref_v), lc.metrics(cor_v, ref_v)
    ape = np.abs(cor_v - ref_v) / ref_v * 100
    u95 = float(np.percentile(ape, 95))
    ok = after.mape <= ACCEPT_MAPE and after.max_ape <= ACCEPT_MAX_APE

    out = os.path.join(os.path.dirname(os.path.abspath(a.csv)), f"calibration_report_{a.model}.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"# Calibration report {a.model}\n\n")
        fh.write(f"- Date generated: {dt.date.today():%Y-%m-%d}\n- Reference: {a.reference}\n")
        fh.write(f"- Source data: `{os.path.basename(a.csv)}` (fit n={len(fit)}, validation n={len(val)})\n")
        fh.write(f"- Gain/timing in data: {', '.join(gains)}\n\n")
        fh.write(f"## Model\n\nE_corrected = **{A:.6f}** × E_raw **{'+' if B >= 0 else '−'} {abs(B):.6f}**\n\n")
        fh.write("## Validation (independent session)\n\n| Metric | Before | After |\n|---|---|---|\n")
        for k, lab, nd in [("mae", "MAE (lx)", 1), ("rmse", "RMSE (lx)", 1), ("mape", "MAPE (%)", 2),
                           ("max_ape", "Max APE (%)", 2), ("bias_pct", "Mean bias (%)", 2), ("r2", "r² (linearity only)", 4)]:
            fh.write(f"| {lab} | {lc.fmt(getattr(before, k), nd)} | {lc.fmt(getattr(after, k), nd)} |\n")
        fh.write(f"\nGuard band for the SOP (95th percentile |error|): ±{u95:.1f} %\n\n")
        fh.write(f"Decision: **{'ACCEPT - enable CALIBRATION' if ok else 'REJECT - keep RAW mode, investigate'}** "
                 f"(limits MAPE ≤ {ACCEPT_MAPE} %, Max APE ≤ {ACCEPT_MAX_APE} %)\n")
    print(open(out, encoding="utf-8").read())
    print("---- paste into firmware ----")
    print(f"const bool  CALIBRATION_ENABLED = {'true' if ok else 'false'};")
    print(f"const float CAL_SLOPE  = {A:.6f}f;\nconst float CAL_OFFSET = {B:.6f}f;")
    print(f'const char CAL_MODEL_VERSION[] = "{a.model}";\nconst char CAL_DATE[]          = "{dt.date.today():%Y-%m-%d}";')
    print(f'const char CAL_REFERENCE[]     = "{a.reference[:40]}";')


if __name__ == "__main__":
    main()

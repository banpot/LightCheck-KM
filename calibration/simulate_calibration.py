"""
LightCheck KM - Monte Carlo simulation of calibration / compensation
=====================================================================

!!! SIMULATION - NOT MEASURED DATA !!!
There are no real paired measurements yet. This script estimates the accuracy
the prototype can be EXPECTED to reach after the linear compensation in the
firmware, using only published specifications and stated assumptions. When
real data exist, run fit_calibration.py on calibration/paired_measurements.csv
instead - it uses exactly the same fit and metrics code (lightcheck_cal.py).

Error model (per simulated device / calibration campaign)
---------------------------------------------------------
TSL2591 + Adafruit calculateLux at MED gain, 300 ms:
  s_dev   raw/true scale, U(0.50, 0.76)      <- expected_bias_from_datasheet.py
  delta_k light-source spectral offset per source type, N(0, 3 %)
          (LED 4000 K = 0 by definition; mixed daylight N(0, 6 %))   [assumption]
  geo     cosine / placement error per reading, N(0, 1.5 %)           [assumption]
  noise   repeatability, N(0, 0.4 % + 0.2 lx)                         [assumption]
  drift   fit-session -> validation-session drift, N(0, 0.5 %)        [assumption]
Reference meter (Hioki FT3424 class, JIS C 1609-1 AA / DIN 5032-7 B):
  lin     systematic linearity error, U(-2 %, +2 %) per meter ("+-2 % rdg")
  rnd     random 0.3 %, resolution 1 lx (0-2000 lx range)
Pairing  position mismatch reference head vs sensor, N(0, 1.0 %)      [assumption]

Protocol (KM document 9.1.5): fit set = 8 levels (100-1000 lx, dense at
150/300/400/500) x 4 readings in session 1; validation set = 8 levels x 3
readings in a separate session 2. OLS ref = a*raw + b on the fit set only.

Outputs (calibration/sim/):
  montecarlo_summary.json, representative_campaign.csv,
  decision_analysis.json, figures *.svg (text kept as text) + *.png
Usage:  python simulate_calibration.py [--n 5000] [--seed 2569]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

import lightcheck_cal as lc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sim")

LEVELS = np.array([100, 150, 200, 300, 400, 500, 750, 1000], float)
SOURCES = ["LED4000K", "LED6500K", "LED3000K", "T8", "mixed-daylight"]
SOURCE_P = [0.55, 0.15, 0.10, 0.10, 0.10]

P = dict(
    s_dev=(0.50, 0.76), sigma_src=0.03, sigma_daylight=0.06, sigma_geo=0.015,
    sigma_noise_rel=0.004, sigma_noise_abs=0.2, sigma_drift=0.005,
    ref_lin=0.02, ref_rnd=0.003, sigma_pair=0.010, n_fit_per_level=4, n_val_per_level=3,
)


class Device:
    """One simulated LightCheck unit + one reference meter + one office."""

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.s = rng.uniform(*P["s_dev"])
        self.src_off = {s: (0.0 if s == "LED4000K" else
                            rng.normal(0, P["sigma_daylight"] if s == "mixed-daylight" else P["sigma_src"]))
                        for s in SOURCES}
        self.ref_lin = rng.uniform(-P["ref_lin"], P["ref_lin"])

    def session(self, n_per_level: int, drift: float = 0.0):
        r = self.rng
        true = np.repeat(LEVELS, n_per_level) * r.uniform(0.92, 1.08, LEVELS.size * n_per_level)
        src = r.choice(SOURCES, size=true.size, p=SOURCE_P)
        f_src = 1 + np.array([self.src_off[s] for s in src])
        at_sensor = true * (1 + r.normal(0, P["sigma_pair"], true.size))   # pairing mismatch
        raw = (self.s * (1 + drift) * at_sensor * f_src * (1 + r.normal(0, P["sigma_geo"], true.size))
               + r.normal(0, 1, true.size) * (P["sigma_noise_rel"] * at_sensor * self.s + P["sigma_noise_abs"]))
        ref = np.round(true * (1 + self.ref_lin) * (1 + r.normal(0, P["ref_rnd"], true.size)))
        return true, raw, ref, src


def run_campaign(rng):
    d = Device(rng)
    t_fit, raw_fit, ref_fit, src_fit = d.session(P["n_fit_per_level"])
    a, b = lc.fit_linear(raw_fit, ref_fit)
    t_val, raw_val, ref_val, src_val = d.session(P["n_val_per_level"], drift=rng.normal(0, P["sigma_drift"]))
    cor_val = lc.apply(a, b, raw_val)
    return dict(device=d, a=a, b=b,
                fit=(t_fit, raw_fit, ref_fit, src_fit), val=(t_val, raw_val, ref_val, src_val, cor_val),
                m_raw_ref=lc.metrics(raw_val, ref_val), m_cor_ref=lc.metrics(cor_val, ref_val),
                m_cor_true=lc.metrics(cor_val, t_val), m_raw_true=lc.metrics(raw_val, t_val))


def pct(x, q):
    return float(np.percentile(np.asarray(x, float), q))


def decision_analysis(rng, u95, n_campaigns=400, n_points=200):
    """Pass/fail decisions at the legal thresholds on a synthetic office survey
    (true lux ~ lognormal, median 380 lx, the range typically met in offices)."""
    out = {}
    for thr in (150, 300, 400):
        ff_raw = fp_raw = ff_cor = fp_cor = verify = wrong_after_rule = 0
        total = 0
        for _ in range(n_campaigns):
            c = run_campaign(rng)
            d = c["device"]
            true = rng.lognormal(np.log(380), 0.38, n_points)
            src = rng.choice(SOURCES, size=n_points, p=SOURCE_P)
            f_src = 1 + np.array([d.src_off[s] for s in src])
            raw = d.s * true * f_src * (1 + rng.normal(0, P["sigma_geo"], n_points)) \
                + rng.normal(0, 1, n_points) * (P["sigma_noise_rel"] * true * d.s + P["sigma_noise_abs"])
            cor = lc.apply(c["a"], c["b"], raw)
            ok_true = true >= thr
            ff_raw += np.sum(ok_true & (raw < thr))
            fp_raw += np.sum(~ok_true & (raw >= thr))
            ff_cor += np.sum(ok_true & (cor < thr))
            fp_cor += np.sum(~ok_true & (cor >= thr))
            lo, hi = lc.guard_band(thr, u95)
            in_band = (cor >= lo) & (cor <= hi)
            verify += np.sum(in_band)
            wrong_after_rule += np.sum(~in_band & (ok_true != (cor >= thr)))
            total += n_points
        out[str(thr)] = dict(
            threshold_lux=thr,
            false_fail_raw_pct=100 * ff_raw / total,
            wrong_raw_pct=100 * (ff_raw + fp_raw) / total,
            wrong_corrected_pct=100 * (ff_cor + fp_cor) / total,
            false_fail_corrected_pct=100 * ff_cor / total,
            false_pass_corrected_pct=100 * fp_cor / total,
            guard_band_lux=list(lc.guard_band(thr, u95)),
            to_verify_with_reference_pct=100 * verify / total,
            wrong_decisions_after_guard_band_pct=100 * wrong_after_rule / total,
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=2569)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    camps = [run_campaign(rng) for _ in range(args.n)]
    keys = ["mae", "rmse", "mape", "max_ape", "bias_pct", "r2"]
    summ = {"_note": "SIMULATION (Monte Carlo) - not measured data", "n_campaigns": args.n,
            "seed": args.seed, "parameters": P}
    for name in ["m_raw_ref", "m_cor_ref", "m_cor_true", "m_raw_true"]:
        summ[name] = {k: {"p50": pct([getattr(c[name], k) for c in camps], 50),
                          "p05": pct([getattr(c[name], k) for c in camps], 5),
                          "p95": pct([getattr(c[name], k) for c in camps], 95)} for k in keys}
    # pooled per-point error of the compensated reading vs TRUE illuminance
    pe = np.concatenate([(c["val"][4] - c["val"][0]) / c["val"][0] * 100 for c in camps])
    summ["pooled_point_error_vs_true_pct"] = {
        "mean": float(pe.mean()), "sd": float(pe.std()),
        "p2.5": pct(pe, 2.5), "p97.5": pct(pe, 97.5), "U95_abs": pct(np.abs(pe), 95)}
    pr = np.concatenate([(c["val"][1] - c["val"][0]) / c["val"][0] * 100 for c in camps])
    summ["pooled_raw_error_vs_true_pct"] = {"mean": float(pr.mean()), "p2.5": pct(pr, 2.5), "p97.5": pct(pr, 97.5)}
    summ["slope_a"] = {"p05": pct([c["a"] for c in camps], 5), "p50": pct([c["a"] for c in camps], 50),
                       "p95": pct([c["a"] for c in camps], 95)}
    summ["offset_b"] = {"p05": pct([c["b"] for c in camps], 5), "p50": pct([c["b"] for c in camps], 50),
                        "p95": pct([c["b"] for c in camps], 95)}
    u95 = summ["pooled_point_error_vs_true_pct"]["U95_abs"]
    summ["guard_band_pct"] = u95

    # representative campaign: a device near the datasheet-typical raw scale
    # (0.631) whose compensated MAPE is the median of those devices
    mapes = np.array([c["m_cor_ref"].mape for c in camps])
    near = [i for i, c in enumerate(camps) if abs(c["device"].s - 0.631) < 0.02]
    near.sort(key=lambda i: mapes[i])
    rep = camps[near[len(near) // 2]]
    summ["representative"] = {"a": rep["a"], "b": rep["b"], "s_dev": rep["device"].s,
                              "raw_vs_ref": rep["m_raw_ref"].as_row(), "cor_vs_ref": rep["m_cor_ref"].as_row()}
    rows = []
    for role, block in (("fit", rep["fit"]), ("val", rep["val"])):
        for i, (t, rw, rf, s) in enumerate(zip(block[0], block[1], block[2], block[3])):
            rows.append(dict(session="SIM-S1" if role == "fit" else "SIM-S2", role=role,
                             point_id=f"SIM-{role}-{i + 1:02d}", raw_lux=f"{rw:.2f}", ref_lux=f"{rf:.0f}",
                             gain="25x", tint_ms=300, source=s, notes=f"SIMULATED true={t:.1f}"))
    lc.write_pairs(os.path.join(OUT, "representative_campaign.csv"), rows,
                   "SIMULATED DATA - generated by simulate_calibration.py - NOT real measurements")

    summ["decision_analysis"] = decision_analysis(np.random.default_rng(args.seed + 1), u95)
    with open(os.path.join(OUT, "montecarlo_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summ, fh, indent=2, ensure_ascii=False)

    # data for figures
    np.savez(os.path.join(OUT, "_figdata.npz"),
             fit_true=rep["fit"][0], fit_raw=rep["fit"][1], fit_ref=rep["fit"][2],
             val_true=rep["val"][0], val_raw=rep["val"][1], val_ref=rep["val"][2], val_cor=rep["val"][4],
             mc_mape_raw=np.array([c["m_raw_ref"].mape for c in camps]),
             mc_mape_cor=mapes, mc_max_cor=np.array([c["m_cor_ref"].max_ape for c in camps]),
             pooled_err=pe, a=rep["a"], b=rep["b"])
    s = summ
    print(f"[SIMULATION] campaigns={args.n}")
    print(f"raw vs ref   : MAPE p50 {s['m_raw_ref']['mape']['p50']:.1f} %  (p05-p95 {s['m_raw_ref']['mape']['p05']:.1f}-{s['m_raw_ref']['mape']['p95']:.1f})")
    print(f"comp vs ref  : MAPE p50 {s['m_cor_ref']['mape']['p50']:.2f} %  p95 {s['m_cor_ref']['mape']['p95']:.2f} %; MaxAPE p50 {s['m_cor_ref']['max_ape']['p50']:.1f} % p95 {s['m_cor_ref']['max_ape']['p95']:.1f} %")
    print(f"comp vs true : MAPE p50 {s['m_cor_true']['mape']['p50']:.2f} %  p95 {s['m_cor_true']['mape']['p95']:.2f} %")
    print(f"U95 (|error| vs true, pooled points): {u95:.2f} %")
    print(f"representative a={rep['a']:.4f} b={rep['b']:.2f}")
    for k, v in s["decision_analysis"].items():
        print(f"thr {k}: false-fail raw {v['false_fail_raw_pct']:.1f} % -> comp {v['false_fail_corrected_pct']:.2f} %; "
              f"wrong raw {v['wrong_raw_pct']:.1f} % -> comp {v['wrong_corrected_pct']:.2f} %; verify {v['to_verify_with_reference_pct']:.1f} %; wrong after rule {v['wrong_decisions_after_guard_band_pct']:.2f} %")


if __name__ == "__main__":
    main()

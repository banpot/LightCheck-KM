"""
LightCheck KM - calibration / compensation toolkit
==================================================

Core functions shared by:
  * fit_calibration.py      -> fit & validate a, b from REAL paired measurements
  * simulate_calibration.py -> Monte Carlo of the expected accuracy (no real data)

Model (same as the firmware):  E_corrected = a * E_raw + b

Metrics follow the KM document section 9.1.5 (f):
  MAE, RMSE, MAPE, r^2 (linear relationship only - NOT accuracy), Max APE.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


# --------------------------------------------------------------------------
# Fitting
# --------------------------------------------------------------------------
def fit_linear(raw: Sequence[float], ref: Sequence[float]) -> tuple[float, float]:
    """Ordinary least squares  ref = a*raw + b.  Returns (a, b)."""
    x = np.asarray(raw, float)
    y = np.asarray(ref, float)
    if x.size < 3:
        raise ValueError("need at least 3 paired points to fit a and b")
    a, b = np.polyfit(x, y, 1)
    return float(a), float(b)


def apply(a: float, b: float, raw: Sequence[float]) -> np.ndarray:
    """Apply the compensation exactly like the firmware (clamped at 0 lux)."""
    return np.maximum(a * np.asarray(raw, float) + b, 0.0)


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
@dataclass
class Metrics:
    n: int
    mae: float          # lux
    rmse: float         # lux
    mape: float         # %
    max_ape: float      # %
    bias_pct: float     # mean signed % error
    r2: float           # squared Pearson correlation (linear relationship only)

    def as_row(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def metrics(pred: Sequence[float], ref: Sequence[float]) -> Metrics:
    p = np.asarray(pred, float)
    r = np.asarray(ref, float)
    ok = r > 0                                    # MAPE only where reference > 0
    err = p - r
    ape = np.abs(err[ok]) / r[ok] * 100.0
    r2 = float(np.corrcoef(p, r)[0, 1] ** 2) if p.size > 2 else float("nan")
    return Metrics(
        n=int(p.size),
        mae=float(np.mean(np.abs(err))),
        rmse=float(np.sqrt(np.mean(err ** 2))),
        mape=float(np.mean(ape)),
        max_ape=float(np.max(ape)),
        bias_pct=float(np.mean(err[ok] / r[ok]) * 100.0),
        r2=r2,
    )


# --------------------------------------------------------------------------
# Paired-measurement CSV
# --------------------------------------------------------------------------
CSV_FIELDS = [
    "session",      # e.g. S1-2026-11-05 (fit) / S2-2026-11-12 (validation)
    "role",         # fit | val
    "point_id",     # room/point code
    "raw_lux",      # RawLux from the LightCheck serial log / LCD (R mode)
    "ref_lux",      # calibrated reference lux meter reading
    "gain",         # e.g. 25x  (from serial log)
    "tint_ms",      # e.g. 300
    "source",       # LED4000K / LED6500K / T8 / mixed-daylight ...
    "notes",
]


def load_pairs(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(r for r in fh if not r.lstrip().startswith("#")):
            if not row.get("raw_lux") or not row.get("ref_lux"):
                continue
            row["raw_lux"] = float(row["raw_lux"])
            row["ref_lux"] = float(row["ref_lux"])
            rows.append(row)
    return rows


def write_pairs(path: str, rows: Iterable[dict], header_comment: str = "") -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if header_comment:
            for line in header_comment.strip().splitlines():
                fh.write(f"# {line}\n")
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})


# --------------------------------------------------------------------------
# Guard band (pre-survey decision rule)
# --------------------------------------------------------------------------
def guard_band(threshold_lux: float, u95_pct: float) -> tuple[float, float]:
    """Readings inside [thr*(1-U95), thr*(1+U95)] cannot be judged pass/fail by
    the low-cost meter and must be confirmed with the calibrated reference."""
    return threshold_lux * (1 - u95_pct / 100.0), threshold_lux * (1 + u95_pct / 100.0)


def fmt(x: float, nd: int = 2) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"

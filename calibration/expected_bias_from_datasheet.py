"""
Expected RAW bias of Adafruit_TSL2591::calculateLux() - estimated from the
TSL2591 datasheet only (no measurements).  Run:  python expected_bias_from_datasheet.py

Datasheet DS000338 v6-00, "ALS Characteristics" (VDD=3 V, 25 C, AGAIN=High,
ATIME=100 ms, white LED 4000 K, Ee = 4.98 uW/cm^2):
    CH0 = 1120 / 1315 / 1510 counts  (min / typ / max)
    CH1/CH0 ratio = 0.092 / 0.132 / 0.172
    AGAIN Medium = 22 / 24.5 / 27 x,  High = 360 / 400 / 440 x
Adafruit library v1.4.5 assumes: gain MED = 25x, HIGH = 428x, LUX_DF = 408,
    lux = (ch0 - ch1) * (1 - ch1/ch0) / (atime * again / LUX_DF)

Assumption (not in the datasheet): luminous efficacy of radiation of a 4000 K
phosphor white LED = 300-330 lm/W (typ. 315)  ->  true lux = Ee[W/m^2] * LER.
"""
import itertools
import json
import sys

EE_W_M2 = 4.98e-6 * 1e4          # 4.98 uW/cm^2 -> W/m^2
CH0 = {"min": 1120, "typ": 1315, "max": 1510}
RATIO = {"min": 0.092, "typ": 0.132, "max": 0.172}
LER = {"min": 300.0, "typ": 315.0, "max": 330.0}
GAIN_MED = {"min": 22.0, "typ": 24.5, "max": 27.0}
GAIN_HIGH = {"min": 360.0, "typ": 400.0, "max": 440.0}
LIB_GAIN = {"MED": 25.0, "HIGH": 428.0}
LUX_DF = 408.0


def adafruit_lux(ch0, ch1, atime_ms, again):
    cpl = atime_ms * again / LUX_DF
    return (ch0 - ch1) * (1 - ch1 / ch0) / cpl


def scale_at_med(ch0, ratio, ler, g_med, g_high=400.0):
    """raw_lux / true_lux when the same light is read at MED gain, 300 ms."""
    true_lux = EE_W_M2 * ler
    # counts per lux per 1x per 100 ms from the HIGH-gain characterisation
    k = ch0 / (g_high * true_lux)
    c0 = true_lux * k * g_med * 3          # 300 ms = 3 x 100 ms
    c1 = c0 * ratio
    return adafruit_lux(c0, c1, 300.0, LIB_GAIN["MED"]) / true_lux


def main():
    typ = scale_at_med(CH0["typ"], RATIO["typ"], LER["typ"], GAIN_MED["typ"])
    corners = [scale_at_med(c, r, l, g)
               for c, r, l, g in itertools.product(CH0.values(), RATIO.values(),
                                                    LER.values(), GAIN_MED.values())]
    # The datasheet min/max are not simultaneous worst cases; use a
    # root-sum-square spread around typ as the "plausible" range.
    import math
    rel = []
    for name, d, f in [("CH0 responsivity", CH0, lambda v: scale_at_med(v, RATIO["typ"], LER["typ"], GAIN_MED["typ"])),
                       ("CH1/CH0 ratio", RATIO, lambda v: scale_at_med(CH0["typ"], v, LER["typ"], GAIN_MED["typ"])),
                       ("LED efficacy (assumed)", LER, lambda v: scale_at_med(CH0["typ"], RATIO["typ"], v, GAIN_MED["typ"])),
                       ("MED gain", GAIN_MED, lambda v: scale_at_med(CH0["typ"], RATIO["typ"], LER["typ"], v))]:
        lo, hi = sorted([f(d["min"]), f(d["max"])])
        rel.append((name, lo / typ - 1, hi / typ - 1))
    rss = math.sqrt(sum(((h - l) / 2) ** 2 for _, l, h in rel))
    out = {
        "scale_typ": typ,
        "bias_typ_pct": (typ - 1) * 100,
        "scale_rss_range": [typ * (1 - rss), typ * (1 + rss)],
        "scale_worst_corners": [min(corners), max(corners)],
        "contributions": [{"factor": n, "low_pct": l * 100, "high_pct": h * 100} for n, l, h in rel],
        "gain_step_MED_to_HIGH_pct": ((GAIN_HIGH["typ"] / LIB_GAIN["HIGH"]) /
                                      (GAIN_MED["typ"] / LIB_GAIN["MED"]) - 1) * 100,
    }
    if "--json" in sys.argv:
        print(json.dumps(out, indent=2))
        return out
    print(f"Typical raw/true at MED gain : {typ:.3f}  (raw reads {abs(out['bias_typ_pct']):.0f} % low)")
    print(f"Plausible range (RSS)        : {out['scale_rss_range'][0]:.3f} - {out['scale_rss_range'][1]:.3f}")
    print(f"All-corners worst case       : {out['scale_worst_corners'][0]:.3f} - {out['scale_worst_corners'][1]:.3f}")
    for c in out["contributions"]:
        print(f"   {c['factor']:<24} {c['low_pct']:+6.1f} % .. {c['high_pct']:+6.1f} %")
    print(f"Raw-lux step when switching MED->HIGH (typ.): {out['gain_step_MED_to_HIGH_pct']:+.1f} %")
    return out


if __name__ == "__main__":
    main()

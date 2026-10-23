"""
LightCheck KM - lamp upgrade calculator (PDCA "Act" step)
========================================================
Lumen method:  E = N * Phi * UF * MF / A
For the same room, fittings, UF and MF, illuminance is proportional to the total
lamp flux, so to move a room from the measured E_meas to the target E_target:

    k = E_target / E_meas                       (required light increase)
    Small deficit  ->  replace lamps:  P_new = P_old * k * (eta_old / eta_new)
    Large deficit  ->  add lamps:      N_new = ceil(N_old * k)

eta = LED efficacy in lm/W (same lamp family -> eta_old / eta_new = 1).
Default target = criterion * (1 + margin); margin defaults to the prototype's
U95 guard band (7.3 %) so the room still passes after measurement uncertainty.
Default rule: a deficit up to 20 % is handled by the next lamp size up
(e.g. LED T8 18 W -> 22 W is +22 % flux); larger deficits need more luminaires.

Usage:
  python lighting_upgrade.py --measured 255 --criterion 300 --lamps 6 --watt 18
  python lighting_upgrade.py --measured 220 --criterion 300 --lamps 6 --watt 18 --sizes 18,20,22,24
"""
import argparse
import math


def plan(measured, criterion, lamps, watt, margin=0.073, small_deficit=0.20,
         sizes=(9, 10, 14, 18, 20, 22, 24, 28, 36), eta_old=100.0, eta_new=100.0):
    target = criterion * (1 + margin)
    deficit = max(0.0, 1 - measured / criterion)
    k = target / measured
    p_needed = watt * k * eta_old / eta_new
    bigger = [s for s in sorted(sizes) if s >= p_needed - 1e-9]
    out = dict(target_lux=target, deficit_pct=deficit * 100, k=k, p_needed_w=p_needed)
    if measured >= target:
        out.update(action="no change", detail="already above the criterion plus margin")
    elif deficit <= small_deficit and bigger:
        out.update(action="replace lamps", new_watt=bigger[0],
                   detail=f"replace {lamps} x {watt} W with {lamps} x {bigger[0]} W "
                          f"(needed {p_needed:.1f} W, +{(bigger[0] / watt - 1) * 100:.0f} % power)")
    else:
        n_new = math.ceil(lamps * k)
        out.update(action="add lamps", new_count=n_new,
                   detail=f"increase {lamps} -> {n_new} luminaires of {watt} W (+{n_new - lamps}); "
                          f"place them on the dim side of the 2 x 2 m grid")
    out["energy_change_pct"] = ((out.get("new_watt", watt) * out.get("new_count", lamps)) / (watt * lamps) - 1) * 100
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measured", type=float, required=True, help="confirmed illuminance (lux)")
    ap.add_argument("--criterion", type=float, default=300, help="300 area average / 400 workstation")
    ap.add_argument("--lamps", type=int, required=True)
    ap.add_argument("--watt", type=float, required=True)
    ap.add_argument("--margin", type=float, default=0.073)
    ap.add_argument("--small-deficit", type=float, default=0.20)
    ap.add_argument("--sizes", default="9,10,14,18,20,22,24,28,36")
    ap.add_argument("--eta-old", type=float, default=100.0)
    ap.add_argument("--eta-new", type=float, default=100.0)
    a = ap.parse_args()
    r = plan(a.measured, a.criterion, a.lamps, a.watt, a.margin, a.small_deficit,
             tuple(float(x) for x in a.sizes.split(",")), a.eta_old, a.eta_new)
    print(f"measured {a.measured:.0f} lx vs criterion {a.criterion:.0f} lx -> deficit {r['deficit_pct']:.0f} %")
    print(f"target {r['target_lux']:.0f} lx (criterion + {a.margin * 100:.1f} % margin), k = {r['k']:.3f}")
    print(f"ACTION: {r['action']} - {r['detail']}; lighting power {r['energy_change_pct']:+.0f} %")


if __name__ == "__main__":
    main()

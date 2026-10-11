"""OpenFOAM v2506 laminer boru sonucunu okur, elle hesapla (Hagen–Poiseuille) karşılaştırır, çizer.
Kama 2,5° → tam boru = kama × 144. Kinematik basınç × rho = Pa."""
import json, pathlib, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
B = pathlib.Path(__file__).resolve().parent; V = B / "openfoam/boru_laminer/postProcessing"; (B / "cikti").mkdir(exist_ok=True)
RHO, MU, R, L, DP = 998.0, 1.002e-3, 0.005, 2.0, 100.0
e = np.loadtxt(V / "eksen/3000/eksen_p_U.xy"); k = np.loadtxt(V / "eksen/3000/kesit_p_U.xy")
phi = float(open(next((V / "debi").glob("*/surfaceFieldValue.dat"))).read().split()[-1])
x, p = e[:, 0], e[:, 1] * RHO; r, u = k[:, 0], k[:, 2]
Q = phi * 360 / 2.5
umaks_an = DP / (4 * MU * L) * R ** 2; Q_an = np.pi * R ** 4 * DP / (8 * MU * L)
m = x >= 1.0; egim = -np.polyfit(x[m], p[m], 1)[0]
O = {"Q_openfoam_ml_s": round(Q * 1e6, 3), "Q_analitik_ml_s": round(Q_an * 1e6, 3),
     "umaks_openfoam_ms": round(float(u[0]), 4), "umaks_analitik_ms": round(umaks_an, 4),
     "dpdx_gelismis_openfoam_pa_m": round(float(egim), 2), "dpdx_analitik_pa_m": DP / L,
     "dp_toplam_openfoam_pa": round(float(p[0]), 1), "dp_toplam_analitik_pa": DP,
     "giris_bolgesi_ek_kayip_yuzde": round(float((p[0] / DP - 1) * 100), 1),
     "re": round(RHO * (Q_an / (np.pi * R ** 2)) * 2 * R / MU),
     "gelisme_boyu_tahmin_m": round(0.05 * RHO * (Q_an / (np.pi * R ** 2)) * 2 * R / MU * 2 * R, 2),
     "ag": "kama 2,5°, 800 × 24 hücre", "cozucu": "OpenFOAM v2506 simpleFoam, laminer, yakınsama artığı < 1e-9"}
O["umaks_fark_yuzde"] = round((O["umaks_openfoam_ms"] / O["umaks_analitik_ms"] - 1) * 100, 2)
O["dpdx_fark_yuzde"] = round((O["dpdx_gelismis_openfoam_pa_m"] / O["dpdx_analitik_pa_m"] - 1) * 100, 2)
json.dump(O, open(B / "cikti" / "OPENFOAM_OLCUMLER.json", "w"), indent=1, ensure_ascii=False)
fig, a = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150)
rr = np.linspace(0, R, 100)
a[0].plot(DP / (4 * MU * L) * (R ** 2 - rr ** 2), rr * 1000, "k-", lw=2, label="Hagen–Poiseuille (formül)")
a[0].plot(u, r * 1000, "o", ms=4, color="#d1495b", label="OpenFOAM, x = 1,9 m")
a[0].set_xlabel("hız u (m/s)"); a[0].set_ylabel("yarıçap r (mm)"); a[0].legend(); a[0].set_title("Hız profili")
a[1].plot(x, p, color="#00798c", lw=2, label="OpenFOAM, eksen boyunca")
a[1].plot([0, L], [DP, 0], "k--", label="formül: düz çizgi, 50 Pa/m")
a[1].axvspan(0, O["gelisme_boyu_tahmin_m"], color="#edae49", alpha=.25, label="giriş bölgesi")
a[1].set_xlabel("x (m)"); a[1].set_ylabel("basınç (Pa)"); a[1].legend(); a[1].set_title("Basınç düşümü")
for s in a: s.grid(alpha=.3)
fig.tight_layout(); fig.savefig(B / "cikti" / "openfoam_boru.png")
for kk, v in O.items(): print(kk, v)

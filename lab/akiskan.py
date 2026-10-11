"""Akışkanlar Mekaniği 101 — lab çekirdeği. Yalnız numpy; her sayı analitik sonuçla karşılaştırılır, OLCUMLER.json'a yazılır.
   Su 20 °C: rho=998 kg/m³, mu=1,002e-3 Pa·s, g=9,81 m/s². Kararlı, sıkıştırılamaz, tek fazlı akış (kavitasyon ve NPSH kapsam dışı).
   ~/.venv-goruntu/bin/python akiskan.py"""
import json, pathlib, numpy as np
RHO, MU, G = 998.0, 1.002e-3, 9.81
O = {}

# 1) hidrostatik: p = rho g h — sayısal integralle doğrula
h = 10.0
z = np.linspace(0, h, 100001); p_say = float(np.trapezoid(RHO * G * np.ones_like(z), z))
O["p_10m_pa"] = round(RHO * G * h, 1); O["p_10m_say_pa"] = round(p_say, 1); O["p_10m_atm"] = round(RHO * G * h / 101325, 3)
# dikdörtgen kapak: genişlik 2 m, yükseklik 3 m, üstü yüzeyde → F = rho g hc A, basınç merkezi 2H/3
W, H = 2.0, 3.0
y = np.linspace(0, H, 200001); pr = RHO * G * y
F_say = float(np.trapezoid(pr * W, y)); yc_say = float(np.trapezoid(pr * W * y, y) / F_say)
O["kapak_F_n"] = round(RHO * G * (H / 2) * W * H, 1); O["kapak_F_say_n"] = round(F_say, 1)
O["kapak_merkez_m"] = round(2 * H / 3, 3); O["kapak_merkez_say_m"] = round(yc_say, 3)
# kaldırma: 0,5 m küp, yoğunluk 600 → batma derinliği ikiye bölme ile
a = 0.5; rho_c = 600.0
def net(d): return RHO * G * a * a * d - rho_c * G * a ** 3
lo, hi = 0.0, a
for _ in range(60):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if net(mid) < 0 else (lo, mid)
O["kup_batma_m"] = round(lo, 4); O["kup_batma_beklenen_m"] = round(a * rho_c / RHO, 4)
O["kup_batma_oran"] = round(lo / a, 3)

# 2) süreklilik ve Bernoulli: 100 mm → 50 mm, 10 L/s
Q = 0.010; D1, D2 = 0.100, 0.050
A1, A2 = np.pi * D1 ** 2 / 4, np.pi * D2 ** 2 / 4
v1, v2 = Q / A1, Q / A2
dp = 0.5 * RHO * (v2 ** 2 - v1 ** 2)
O["v1_ms"] = round(v1, 3); O["v2_ms"] = round(v2, 3); O["hiz_orani"] = round(v2 / v1, 3); O["dp_venturi_pa"] = round(dp, 1)
Q_ters = A2 * np.sqrt(2 * dp / (RHO * (1 - (A2 / A1) ** 2)))   # venturi: dp'den debi
O["venturi_ters_Q_ls"] = round(Q_ters * 1000, 3)
# gerçek venturi: boşaltma katsayısı ~0,98 (tablo değeri) → ideal formül debiyi yaklaşık %2 fazla bulur
O["venturi_cd_hata_yuzde"] = round((1 / 0.98 - 1) * 100, 2)
# Torricelli tank boşalması: tank 1 m çap, delik 20 mm, h0=2 m, Cd=0,62 — RK4 ile
Dt, d0, h0, Cd = 1.0, 0.020, 2.0, 0.62
At, a0 = np.pi * Dt ** 2 / 4, np.pi * d0 ** 2 / 4
def dh(hh): return -Cd * a0 * np.sqrt(2 * G * max(hh, 0)) / At
t = 0.0; hh = h0; dt = 0.5; ts, hs = [0.0], [h0]; t_yarim = None
while hh > 0.01:
    k1 = dh(hh); k2 = dh(hh + dt * k1 / 2); k3 = dh(hh + dt * k2 / 2); k4 = dh(hh + dt * k3)
    hh_new = hh + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    if t_yarim is None and hh_new <= h0 / 2: t_yarim = t + dt * (hh - h0 / 2) / (hh - hh_new)
    hh = hh_new; t += dt; ts.append(t); hs.append(hh)
t_son = t
K = At / (Cd * a0) * np.sqrt(2 / G)
t_an_01 = K * (np.sqrt(h0) - np.sqrt(0.01)); t_an_yarim = K * (np.sqrt(h0) - np.sqrt(h0 / 2))
O["tank_bosalma_say_s"] = round(t_son, 1); O["tank_bosalma_analitik_s"] = round(t_an_01, 1)
O["tank_yarim_say_s"] = round(t_yarim, 1); O["tank_yarim_analitik_s"] = round(t_an_yarim, 1)
O["tank_bosalma_dk"] = round(t_an_01 / 60, 1)
O["tank_ilk_debi_ls"] = round(Cd * a0 * np.sqrt(2 * G * h0) * 1000, 3)
np.save(pathlib.Path(__file__).parent / "tank_t.npy", np.array([ts, hs]))

# 3) boru akışı
def Re(v, D): return RHO * v * D / MU
O["re_su_1ms_50mm"] = round(Re(1.0, 0.05)); O["re_damar_0_1ms_10mm"] = round(Re(0.1, 0.01)); O["re_gecis_ornek"] = round(Re(0.04, 0.05))
# Hagen–Poiseuille: parabolik profilin sayısal integrali
R = 0.005; L = 2.0; dpl = 100.0   # Pa, 10 mm boru
r = np.linspace(0, R, 200001); u = dpl / (4 * MU * L) * (R ** 2 - r ** 2)
Q_say = float(np.trapezoid(u * 2 * np.pi * r, r)); Q_an = np.pi * R ** 4 * dpl / (8 * MU * L)
O["poiseuille_Q_say_ml_s"] = round(Q_say * 1e6, 3); O["poiseuille_Q_analitik_ml_s"] = round(Q_an * 1e6, 3)
O["poiseuille_umaks_ms"] = round(float(u[0]), 4); O["poiseuille_ort_ms"] = round(Q_an / (np.pi * R ** 2), 4)
O["poiseuille_oran"] = round(float(u[0]) / (Q_an / (np.pi * R ** 2)), 3)
def colebrook(re, er):
    f = 0.02
    for _ in range(100): f = (-2 * np.log10(er / 3.7 + 2.51 / (re * np.sqrt(f)))) ** -2
    return f
def swamee(re, er): return 0.25 / np.log10(er / 3.7 + 5.74 / re ** 0.9) ** 2
def haaland(re, er): return (-1.8 * np.log10((er / 3.7) ** 1.11 + 6.9 / re)) ** -2
re0, er0 = 1e5, 0.001
fc = colebrook(re0, er0)
O["f_colebrook_1e5"] = round(float(fc), 5); O["f_swamee_1e5"] = round(float(swamee(re0, er0)), 5); O["f_haaland_1e5"] = round(float(haaland(re0, er0)), 5)
O["swamee_hata_yuzde"] = round(float((swamee(re0, er0) / fc - 1) * 100), 2); O["haaland_hata_yuzde"] = round(float((haaland(re0, er0) / fc - 1) * 100), 2)
O["f_laminer_re1000"] = round(64 / 1000, 4)
O["f_purussuz_1e5"] = round(float(colebrook(1e5, 1e-6)), 5)
# darcy–weisbach: 100 m, 50 mm, 2 m/s, çelik eps=0,045 mm
Lb, Db, vb, eps = 100.0, 0.05, 2.0, 0.045e-3
reb = Re(vb, Db); fb = colebrook(reb, eps / Db)
hf = fb * Lb / Db * vb ** 2 / (2 * G)
O["boru_re"] = round(float(reb)); O["boru_f"] = round(float(fb), 5); O["boru_hf_m"] = round(float(hf), 3); O["boru_dp_kpa"] = round(float(RHO * G * hf / 1000), 2)
# yerel kayıplar (tablo değerleri): giriş 0,5; 2 dirsek 0,9; vana(açık) 0,2; çıkış 1,0
Kler = {"giris": 0.5, "dirsek_x2": 1.8, "vana": 0.2, "cikis": 1.0}; Ktop = sum(Kler.values())
hm = Ktop * vb ** 2 / (2 * G)
O["yerel_K_toplam"] = round(Ktop, 2); O["yerel_hm_m"] = round(float(hm), 3); O["toplam_yuk_kaybi_m"] = round(float(hf + hm), 3)
O["yerel_oran_yuzde"] = round(float(hm / (hf + hm) * 100), 1)
O["boru_hiz_iki_kati_hf_m"] = round(float(colebrook(Re(2 * vb, Db), eps / Db) * Lb / Db * (2 * vb) ** 2 / (2 * G)), 2)

# 4) pompa ve sistem
Hst, Lp, Dp, Kp = 15.0, 200.0, 0.080, 5.0
def sistem(Qx, D=Dp):
    v = Qx / (np.pi * D ** 2 / 4); f = colebrook(Re(v, D), eps / D)
    return Hst + (f * Lp / D + Kp) * v ** 2 / (2 * G)
def pompa(Qx): return 40.0 - 1.0e5 * Qx ** 2        # SENTETİK eğri: kapalı vana 40 m, 10 L/s'de 30 m
def calisma(D):
    lo, hi = 1e-5, 0.019
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if pompa(mid) - sistem(mid, D) > 0 else (lo, mid)
    return lo
Q80 = calisma(0.080); H80 = pompa(Q80)
O["pompa_kapali_vana_m"] = 40.0; O["pompa_10ls_m"] = round(pompa(0.010), 2)
O["sistem_statik_m"] = Hst; O["sistem_10ls_m"] = round(float(sistem(0.010)), 2)
O["calisma_Q_ls"] = round(Q80 * 1000, 3); O["calisma_H_m"] = round(float(H80), 2)
O["calisma_hiz_ms"] = round(Q80 / (np.pi * Dp ** 2 / 4), 3)
eta = 0.65; O["pompa_gucu_kw"] = round(float(RHO * G * Q80 * H80 / eta / 1000), 3); O["pompa_hidrolik_kw"] = round(float(RHO * G * Q80 * H80 / 1000), 3)
for D, ad in [(0.063, "63"), (0.080, "80"), (0.100, "100"), (0.125, "125")]:
    q = calisma(D); hv = pompa(q); v = q / (np.pi * D ** 2 / 4)
    O[f"D{ad}_Q_ls"] = round(q * 1000, 2); O[f"D{ad}_H_m"] = round(float(hv), 2); O[f"D{ad}_v_ms"] = round(float(v), 2)
    O[f"D{ad}_guc_kw"] = round(float(RHO * G * q * hv / eta / 1000), 2)
O["hedef_Q_ls"] = 12.0
json.dump(O, open(pathlib.Path(__file__).parent / "OLCUMLER.json", "w"), indent=1, ensure_ascii=False)
for k, v in O.items(): print(k, v)

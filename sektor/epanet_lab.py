"""Akışkanlar lab — EPANET 2.2 (WNTR 1.5 EpanetSimulator) ile boru ve pompa hesabı.
Aynı problemler lab/akiskan.py'de elle (Colebrook + ikiye bölme) çözüldü; burada sektörün kullandığı
şebeke çözücüsü ile yeniden çözülür ve iki sonuç yan yana yazılır. Birimler: SI (LPS, m)."""
import json, pathlib, warnings, numpy as np, wntr
warnings.filterwarnings("ignore", message="Changing the headloss")

OUT = pathlib.Path(__file__).parent / "cikti"; OUT.mkdir(exist_ok=True)
EPS = 0.045e-3            # çelik boru pürüzlülüğü, m (WNTR iç birimi SI; .inp dosyasına mm yazılır)
R = {}

def model():
    wn = wntr.network.WaterNetworkModel()
    wn.options.hydraulic.headloss = "D-W"
    wn.options.hydraulic.inpfile_units = "LPS"
    wn.options.hydraulic.viscosity = 1.002e-3 / 998 / 1.0e-6   # 20 °C suyun 1e-6 m²/s'ye göre oranı
    wn.options.time.duration = 0
    return wn

def kaydet(wn, ad):
    wntr.network.write_inpfile(wn, str(OUT / f"{ad}.inp"), units="LPS")

# 1) 100 m, 50 mm çelik boru, 2 m/s → sürtünme kaybı (elle: 8,906 m)
wn = model()
Q = 2.0 * np.pi * 0.05 ** 2 / 4                    # m³/s
wn.add_reservoir("KAYNAK", base_head=50.0)
wn.add_junction("UC", base_demand=Q, elevation=0.0)
wn.add_pipe("BORU", "KAYNAK", "UC", length=100.0, diameter=0.05, roughness=EPS, minor_loss=0.0)
kaydet(wn, "boru_100m")
r = wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=str(OUT / "boru_100m"))
R["boru_hf_epanet_m"] = round(50.0 - float(r.node["head"].loc[0, "UC"]), 3)
R["boru_hiz_epanet_ms"] = round(float(r.link["velocity"].loc[0, "BORU"]), 3)

# 2) pompa + 200 m, 80 mm boru, K=5, statik 15 m → çalışma noktası (elle: 10,969 L/s, 27,97 m)
def calisma(D):
    wn = model()
    wn.add_reservoir("ALT_HAVUZ", base_head=0.0)
    wn.add_reservoir("UST_DEPO", base_head=15.0)
    wn.add_junction("POMPA_CIKIS", elevation=0.0)
    # SENTETİK eğri, elle hesaptaki ile aynı: H = 40 − 1e5·Q² (üç nokta → EPANET aynı biçimi uydurur)
    wn.add_curve("EGRI", "HEAD", [(0.0, 40.0), (0.010, 30.0), (0.015, 17.5)])
    wn.add_pump("POMPA", "ALT_HAVUZ", "POMPA_CIKIS", pump_type="HEAD", pump_parameter="EGRI")
    wn.add_pipe("HAT", "POMPA_CIKIS", "UST_DEPO", length=200.0, diameter=D, roughness=EPS, minor_loss=5.0)
    r = wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=str(OUT / f"pompa_{int(D*1000)}"))
    q = float(r.link["flowrate"].loc[0, "POMPA"]); h = float(r.node["head"].loc[0, "POMPA_CIKIS"])
    return wn, q, h
for D in (0.063, 0.080, 0.100, 0.125):
    wn, q, h = calisma(D)
    R[f"D{int(D*1000)}_Q_epanet_ls"] = round(q * 1000, 2); R[f"D{int(D*1000)}_H_epanet_m"] = round(h, 2)
    if D == 0.080: kaydet(wn, "pompa_80mm")

el = json.load(open(pathlib.Path(__file__).resolve().parent.parent / "lab" / "OLCUMLER.json"))
K = {"boru_hf": ("boru_hf_m", "boru_hf_epanet_m"), "calisma_Q": ("calisma_Q_ls", "D80_Q_epanet_ls"),
     "calisma_H": ("calisma_H_m", "D80_H_epanet_m")}
for d in ("63", "80", "100", "125"): K[f"D{d}_Q"] = (f"D{d}_Q_ls", f"D{d}_Q_epanet_ls")
R["karsilastirma"] = {k: {"elle": el[a], "epanet": R[b], "fark_yuzde": round((R[b] / el[a] - 1) * 100, 2)} for k, (a, b) in K.items()}
R["surum"] = {"wntr": wntr.__version__, "cozucu": "EPANET 2.2 (WNTR EpanetSimulator)"}
json.dump(R, open(OUT / "EPANET_OLCUMLER.json", "w"), indent=1, ensure_ascii=False)
for k, v in R["karsilastirma"].items(): print(f"{k:12s} elle={v['elle']:>9} epanet={v['epanet']:>9} fark%={v['fark_yuzde']}")

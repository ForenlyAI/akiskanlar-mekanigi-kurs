"""Kendi koşumunuzu ekibin ölçtüğü sonuçla karşılaştırır. Kullanım: python kontrol.py
Fark %1'i geçerse ✗ yazar; o satırdaki girdiyi (çap, pürüzlülük, eğri) kontrol edin."""
import json, pathlib
B = pathlib.Path(__file__).resolve().parent
ciftler = [("lab/OLCUMLER.json", "lab/OLCUMLER.json"),  # elle hesap: kendi koşumunuz dosyanın üstüne yazar
           ("sektor/cikti/EPANET_OLCUMLER.json", "sektor/beklenen/EPANET_OLCUMLER.json"),
           ("sektor/cikti/OPENFOAM_OLCUMLER.json", "sektor/beklenen/OPENFOAM_OLCUMLER.json")]
hata = 0
for siz, ref in ciftler[1:]:
    a, b = B / siz, B / ref
    if not a.exists():
        print(f"– {siz} yok (önce ilgili betiği koşun)"); continue
    A, R = json.loads(a.read_text()), json.loads(b.read_text())
    for k, v in R.items():
        if isinstance(v, (int, float)) and k in A and isinstance(A[k], (int, float)):
            fark = 0 if v == 0 else abs(A[k] / v - 1) * 100
            iyi = fark <= 1.0; hata += not iyi
            print(f"{'✓' if iyi else '✗'} {k:34s} siz={A[k]:<10} beklenen={v:<10} fark=%{fark:.2f}")
print("SONUÇ:", "geçti" if hata == 0 else f"{hata} değer %1'den fazla farklı")

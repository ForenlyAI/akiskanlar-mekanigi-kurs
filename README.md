# Akışkanlar Mekaniği · öğrenci deposu

Forenly AI Academy kursu **Akışkanlar Mekaniği** için çalışma deposu. Her hesap üç katmanda yapılır:

1. **Elle (Python + NumPy):** formülü kendiniz yazarsınız: `lab/akiskan.py`
2. **Sektör aracı:** aynı problemi mühendislerin kullandığı çözücüyle yeniden çözersiniz:
   - **EPANET 2.2:** boru ve pompa hesabı (ABD Çevre Koruma Ajansı'nın açık kaynak şebeke çözücüsü; Python'dan [WNTR 1.5](https://usepa.github.io/WNTR/) ile çağrılır).
   - **OpenFOAM v2506:** sayısal akışkanlar dinamiği, yani CFD. ESI/OpenCFD'nin resmi Docker imajı kullanılır.
3. **Claude Code ile:** girdiyi değiştirip yeniden koşturmayı yapay zekâ asistanına yaptırırsınız. Sonucu aşağıdaki `kontrol.py` ile siz doğrularsınız.

## Kurulum

En kolayı GitHub Codespaces: **Code → Codespaces → Create**. Ortam ilk açılışta yaklaşık 3 dakikada kendiliğinden kurulur: Python sanal ortamı (`.venv`: NumPy, Matplotlib, WNTR), Docker ve OpenFOAM imajı. Terminalde `python` komutu `.venv`'i kullanmıyorsa önce `source .venv/bin/activate` yazın. (11.10.2026'da 2 çekirdekli Codespace'te denendi: dört adım ve `kontrol.py` geçti; OpenFOAM koşumu 2 dk 55 sn.)

Kendi bilgisayarınızda kurmak için Python 3.10 ve üstü ile Docker gerekir:

```bash
pip install -r requirements.txt
docker pull opencfd/openfoam-default:2506
```

## Koşum

```bash
python lab/akiskan.py          # elle: hidrostatik, Bernoulli, tank, boru, pompa → lab/OLCUMLER.json
python sektor/epanet_lab.py    # EPANET: 100 m boru kaybı + pompa çalışma noktası (4 çap)
sh sektor/openfoam_kos.sh      # OpenFOAM: 2 m laminer boru, ~3 dakika
python sektor/openfoam_oku.py  # OpenFOAM sonucu → formülle karşılaştırma + grafik
python kontrol.py              # sonuçlarınız beklenenle %1 içinde mi?
```

## Ekibin ölçtüğü sonuçlar (11.10.2026, `sektor/beklenen/`)

| Problem | Elle | Sektör aracı | Fark |
|---|---|---|---|
| 100 m, 50 mm çelik boru, 2 m/s: sürtünme kaybı | 8,906 m (Colebrook) | 8,985 m (EPANET) | %0,89 |
| Pompa + 80 mm hat: çalışma debisi | 10,969 L/s | 10,95 L/s (EPANET) | %−0,17 |
| Pompa + 80 mm hat: basma yüksekliği | 27,97 m | 28,01 m (EPANET) | %0,14 |
| Çap 63 / 100 / 125 mm: debi | 7,33 / 13,59 / 14,95 L/s | 7,31 / 13,58 / 14,95 L/s | < %0,3 |
| Laminer boru (R 5 mm, 2 m, 100 Pa): en büyük hız | 0,3119 m/s | 0,3106 m/s (OpenFOAM) | %−0,42 |
| Laminer boru: gelişmiş bölgede basınç eğimi | 50,0 Pa/m | 50,08 Pa/m (OpenFOAM) | %0,16 |
| Laminer boru: toplam basınç düşümü | 100 Pa | 110,8 Pa (OpenFOAM) | **%+10,8** |

**Neden farklılar?**

- **EPANET:** Darcy-Weisbach kaybında sürtünme katsayısı için Colebrook yerine Swamee-Jain yaklaşımını kullanır. Derste ölçtüğümüz %0,76'lık Swamee-Jain sapması, kayıpta %0,89 olarak görünür.
- **OpenFOAM:** formül, borunun her yerinde gelişmiş parabolik profil varsayar. Gerçekte akış girişte düz başlar ve yaklaşık 0,78 m'de gelişir (0,05 · Re · D; Re 1.553). Bu giriş bölgesi %10,8 ek kayıp getirir. Gelişmiş bölgede eğim formülle %0,2 içinde uyuşur. Bu sonucu `sektor/beklenen/openfoam_boru.png` grafiğinde görürsünüz.

## Görevler

1. `lab/akiskan.py` içinde boru hızını 3 m/s yapın. Elle hesap ile EPANET kaybını karşılaştırın; fark yine %1'in altında mı?
2. `sektor/epanet_lab.py` içinde hat boyunu 200 m'den 400 m'ye çıkarın. 12 L/s hedefi için en küçük çap değişti mi?
3. OpenFOAM borusunu 4 m'ye uzatın (`system/blockMeshDict` içinde `L`, hücre sayısını iki katına çıkarın). Toplam düşümdeki ek kayıp yüzdesi nasıl değişti, neden?
4. **Claude Code katmanı:** Claude Code'a "pompa eğrisini H = 45 − 1,2e5·Q² yap, dört çap için çalışma noktasını EPANET ile yeniden hesapla, elle hesapla karşılaştır" deyin. Değişen satırları okuyun, sonra `python kontrol.py` ile ve elle tek bir noktayı hesaplayarak doğrulayın. Asistanın yazdığı sayıyı doğrulamadan kullanmayın.

## Sınırlar

- Pompa eğrisi **sentetiktir**. Gerçek pompa seçiminde üreticinin eğrisi ve NPSH hesabı gerekir.
- Su 20 °C'de, sıkıştırılamaz ve tek fazlı kabul edilir. Kavitasyon kapsam dışıdır.
- OpenFOAM hesabı eksenel simetrik bir kama (2,5°) üzerinde, 800 × 24 hücreyle yapılır. Ağ inceldikçe en büyük hızdaki %0,4'lük fark küçülür.

# Reports Directory

Bu klasor proje ciktikumlarini uce ayirir: sunum/makale icin final dosyalar, deney metrikleri ve eski ara denemeler.

## final/

Sunumda ve makale yaziminda ilk bakilacak dosyalar:

- `demo_safe_mode_v3_dashboard.html`: kullaniciya sunulabilir indirilebilir dashboard.
- `demo_safe_mode_v3_mistral_final.json`: dashboard ve raporun kaynak olay verisi.
- `demo_safe_mode_v3_mistral_final.md`: okunabilir metin raporu.
- `threshold_fusion_experiment_report.md`: model gelisim sureci, v1/v2/v3 sonuclari ve yorumlari.

## experiments/

Egitim/test deneylerinin ham JSON metrikleri ve confusion matrix dosyalari:

- `safe_mode_v1/`: ilk safe-mode karar modeli.
- `safe_mode_v2/`: threshold/politika iyilestirmeleri sonrasi ara model.
- `safe_mode_v3/`: onerilen karar katmani modeli.
- `threshold_no_attack_type/`: fusion'dan attack type hedefinin cikarildigi ara deney.
- `cic_carla_visual_v1/`: onceki attack-type hedefli fusion deneyi.

## archive/

Tekrarlanabilirlik icin saklanan, fakat ana sunumda kullanilmayacak ara ciktlilar:

- `demo/`: eski demo ve Ollama deneme raporlari.
- `smoke/`: kisa smoke testleri ve leakage denemeleri.
- `old_summaries/`: eski ozet raporlar ve onceki final-strict metrikleri.

## Ana Sonuc

Mevcut ana karar katmani modeli `fusion_safe_mode_v3` olarak raporlandi. Bu modelde safe-mode test sonucu onceki v1/v2 denemelerine gore belirgin sekilde iyilesti ve dashboard da bu nihai yapi uzerinden uretildi.

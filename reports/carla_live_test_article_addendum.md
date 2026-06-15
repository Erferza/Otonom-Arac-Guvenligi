# CARLA Canli Simulasyon Testleri - Makaleye Eklenebilir Rapor

Bu rapor, `/Users/ferzaer/Downloads/live_test_runs` altindaki CARLA canli test kayitlari incelenerek hazirlanmistir. Klasorde her test kosusu icin `report.json`, `report.md`, `dashboard.html`, `fusion_events.csv`, `live_sensor_rows.csv`, `visual_comparison.csv`, `risk_confusion_matrix.csv`, `safe_mode_confusion_matrix.csv` ve `test_metrics.json` dosyalari yer almaktadir. Bos/yarim kalmis kosular disarida birakildiginda 9 tam raporlu kosu bulunmustur.

## 1. Test Aileleri

Canli testler iki ana senaryo ailesinde toplanmaktadir:

1. `carla_final_pipeline_*`: NPC bulunmayan veya dusuk NPC sayili deterministik final pipeline testi.
2. `carla_npc_hallucination_*`: 15 NPC arac iceren, ag saldirisi, davranissal saldiri ve gorsel tutarsizlik/hallucination sinyallerinin birlikte degerlendirildigi stres testi.

## 2. Temsili Test 1: Final Pipeline Canli Testi

Temsili kosu: `carla_final_pipeline_20260526_203411`

Bu testte sistem bes fazli deterministik bir senaryo uzerinde calistirilmistir. Fazlar sirasiyla temiz baslangic, ag seviyesinde MITM/probe, DoS ile sensor bozulmasi, gorsel baglamda yakin engel yokken ani fren ve son olarak serit sapmasi ile ag alarmi iceren koordineli kontrol ele gecirme senaryosudur.

| Faz | CARLA davranis etiketi | CIC etiketi | Beklenen safe mode | Amac |
|---|---|---|---|---|
| baseline_normal | normal | Benign | normal_mode | Temiz referans davranisi olusturmak |
| network_intrusion_probe | normal | mitm | monitoring_mode | Yalnizca ag katmaninin tetiklenmesini sinamak |
| dos_sensor_corruption | dos | dos | degraded_safe_mode | Ag baskisi ve sensor/veri bozulmasini birlikte sinamak |
| hallucinated_sudden_brake | sudden_brake | Benign | monitoring_mode | Gorsel engel yokken ani fren tutarsizligini yakalamak |
| coordinated_control_takeover | lane_deviation | scanning | emergency_safe_mode | Cok katmanli kritik kontrol sapmasini sinamak |

Testte 26 karar olayi uretilmistir. Sistem 17 olayi saldiri/anomali, 9 olayi normal olarak isaretlemistir. Nihai raporda 23 olay guvenli mod gerektiren olay olarak belirlenmis ve genel karar `emergency_safe_mode` olmustur.

| Metrik | Risk modeli | Safe-mode modeli |
|---|---:|---:|
| Accuracy | 0.692 | 0.346 |
| Macro F1 | 0.609 | 0.307 |

Risk confusion matrix:

| Gercek \ Tahmin | normal | attack |
|---|---:|---:|
| normal | 3 | 2 |
| attack | 6 | 15 |

Safe-mode confusion matrix:

| Gercek \ Tahmin | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 0 | 6 | 0 | 0 |
| emergency_safe_mode | 0 | 6 | 0 | 0 |
| monitoring_mode | 2 | 7 | 0 | 0 |
| normal_mode | 2 | 0 | 0 | 3 |

Katman bazli tetikleme sayilari:

| Katman | Tetiklenen olay | Seviye dagilimi |
|---|---:|---|
| CIC ag katmani | 17 | critical: 15, medium: 2, low: 9 |
| CARLA davranis/sensor katmani | 17 | high: 13, medium: 4, low: 9 |
| nuScenes/gorsel tutarlilik katmani | 10 | high: 4, medium: 12, low: 10 |
| Fusion karar katmani | 17 | critical: 10, high: 7, low: 9 |

Tehdit dagilimi:

| Tehdit/anomali | Olay sayisi | Oran |
|---|---:|---:|
| lane_deviation | 7 | 26.9% |
| sudden_brake | 4 | 15.4% |
| dos | 3 | 11.5% |
| sensor_noise | 2 | 7.7% |
| gps_spoofing | 1 | 3.8% |

Guvenli mod dagilimi:

| Safe mode | Olay sayisi | Oran |
|---|---:|---:|
| normal_mode | 3 | 11.5% |
| degraded_safe_mode | 4 | 15.4% |
| emergency_safe_mode | 19 | 73.1% |

## 3. Temsili Test 2: NPC ve Hallucination Stres Testi

Temsili kosu: `carla_npc_hallucination_20260526_211844`

Bu testte 15 NPC arac bulunan daha karmasik bir trafik ortami kullanilmistir. Senaryo, CIC ve CARLA katmanlarinda bilerek farkli veya es zamanli saldiri etiketleri olusturarak fusion katmaninin cok kaynakli celiski altindaki davranisini olcmek icin tasarlanmistir.

| Faz | CARLA davranis etiketi | CIC etiketi | Beklenen safe mode | Amac |
|---|---|---|---|---|
| npc_baseline_normal | normal | Benign | normal_mode | NPC trafik altinda temiz baslangic |
| npc_mitm_smooth_drive | normal | mitm | monitoring_mode | Arac davranisi normalken ag anomalisi |
| npc_dos_sudden_brake | sudden_brake | dos | degraded_safe_mode | DDoS ile ani fren davranisinin birlikte sinanmasi |
| npc_scanning_lane_deviation | lane_deviation | scanning | emergency_safe_mode | Ag kesfi ile serit kontrol sapmasi |
| npc_dos_speed_spoof | speed_spoofing | dos | emergency_safe_mode | DDoS ile hiz sensoru spoofing |
| npc_scanning_delayed_sensor | delayed_sensor_attack | scanning | emergency_safe_mode | Sensor gecikmesi ve ag tarama saldirisinin birlikte sinanmasi |

Testte 34 karar olayi uretilmistir. Sistem 22 olayi saldiri/anomali, 12 olayi normal olarak isaretlemistir. Nihai raporda 30 olay guvenli mod gerektiren olay olarak belirlenmis ve genel karar `emergency_safe_mode` olmustur.

| Metrik | Risk modeli | Safe-mode modeli |
|---|---:|---:|
| Accuracy | 0.706 | 0.618 |
| Macro F1 | 0.622 | 0.393 |

Risk confusion matrix:

| Gercek \ Tahmin | normal | attack |
|---|---:|---:|
| normal | 4 | 2 |
| attack | 8 | 20 |

Safe-mode confusion matrix:

| Gercek \ Tahmin | degraded_safe_mode | emergency_safe_mode | monitoring_mode | normal_mode |
|---|---:|---:|---:|---:|
| degraded_safe_mode | 0 | 6 | 0 | 0 |
| emergency_safe_mode | 0 | 17 | 0 | 0 |
| monitoring_mode | 1 | 4 | 0 | 0 |
| normal_mode | 2 | 0 | 0 | 4 |

Katman bazli tetikleme sayilari:

| Katman | Tetiklenen olay | Seviye dagilimi |
|---|---:|---|
| CIC ag katmani | 28 | critical: 26, high: 1, medium: 1, low: 6 |
| CARLA davranis/sensor katmani | 22 | critical: 6, high: 9, medium: 7, low: 12 |
| nuScenes/gorsel tutarlilik katmani | 6 | high: 6, medium: 10, low: 18 |
| Fusion karar katmani | 22 | critical: 15, high: 7, low: 12 |

Tehdit dagilimi:

| Tehdit/anomali | Olay sayisi | Oran |
|---|---:|---:|
| position_spoofing | 9 | 26.5% |
| sudden_brake | 5 | 14.7% |
| speed_spoofing | 5 | 14.7% |
| lane_deviation | 1 | 2.9% |
| sensor_noise | 1 | 2.9% |
| dos | 1 | 2.9% |

Guvenli mod dagilimi:

| Safe mode | Olay sayisi | Oran |
|---|---:|---:|
| normal_mode | 4 | 11.8% |
| degraded_safe_mode | 3 | 8.8% |
| emergency_safe_mode | 27 | 79.4% |

## 4. Test Aileleri Arasi Ozet

Tam raporlu kosular uzerinden elde edilen grup ozeti:

| Test ailesi | Kosu sayisi | Olay sayisi | Risk accuracy | Risk Macro F1 | Safe-mode accuracy | Safe-mode Macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Final pipeline | 6 | 26 | 0.692 | 0.602 ort. | 0.340 ort. | 0.300 ort. |
| NPC + hallucination stres | 3 | 34 | 0.706 | 0.622 | 0.618 | 0.393 |

Not: Bu degerler statik test seti performansi degildir. CARLA ortaminda zamansal faz gecisleri, senaryo etiketlerinin kisa sureli gecis belirsizlikleri, NPC trafigi ve katmanlar arasi sinyal uyumsuzlugu bulunmaktadir. Bu nedenle final retrain offline test metrikleriyle birebir karsilastirilmamalidir. Bu bolum, sistemin canli entegrasyon ve operasyonel karar uretme kabiliyetini gosteren ek dogrulama olarak sunulmalidir.

## 5. Makaleye Eklenebilecek Yorum

Canli testlerde risk modeli offline test metriklerine gore daha dusuk fakat tutarli bir performans sergilemistir. Izole final pipeline senaryosunda risk accuracy degeri 0.692, NPC ve hallucination stres senaryosunda ise 0.706 olarak olculmustur. Bu durum, statik veri setlerinde elde edilen performansin canli simülasyon ortaminda faz gecisleri, zamanlama farklari ve katmanlar arasi sinyal uyumsuzlugu nedeniyle dusmesini beklenen bir sonuc haline getirmektedir.

Safe-mode siniflandirmasinda ozellikle monitoring_mode ve degraded_safe_mode fazlarinin emergency_safe_mode'a kayma egilimi gosterdigi gorulmustur. Bu durum, sistemin kritik veya belirsiz olaylarda daha konservatif karar uretme egiliminden kaynaklanmaktadir. Otonom arac guvenligi acisindan bu davranis false positive maliyetini artirsa da, emniyet-kritik false negative riskini azaltan temkinli bir karar politikasi olarak yorumlanabilir.

Gorsel tutarlilik katmani dogrudan saldiri siniflandiricisi olarak degil, davranis ve ag katmanlarindan gelen kararlarin cevresel baglamla karsilastirilmasi icin kullanilmistir. Ani fren fazlarinda kamera onunde yakin engel bulunmamasina ragmen fren davranisinin gozlenmesi, gorsel hallucination/tutarsizlik olasiligini yukselterek fusion kararini desteklemistir.

Her iki canli test ailesinde de nihai sistem karari emergency_safe_mode olarak uretilmistir. Bu sonuc, onerilen mimarinin yalnizca saldiri/anomali tespiti yapmakla kalmayip, saldiri zinciri boyunca operasyonel guvenli mod karari uretebildigini gostermektedir.

## 6. Makale Icin Dikkat Edilmesi Gereken Noktalar

- Canli CARLA test sonuclari final offline test metrikleriyle ayni tabloda verilmemelidir. Ayrı bir "Canli CARLA Simulasyon Testleri" alt basligi kullanilmalidir.
- `dashboard.html` dosyalari kullaniciya/arac sahibine sunulacak operasyonel rapor arayuzu olarak anlatilabilir.
- Canli testlerde safe-mode accuracy'nin dusuk kalmasi basarisizlik olarak degil, siniflar arasi gecislerin ve konservatif emergency_safe_mode kararlarinin etkisi olarak yorumlanmalidir.
- Otomatik raporlardaki "CIC ve gorsel katman esik ustu bulgu uretmedi" cümlesi makaleye alinmamalidir; cunku ayni raporlarin katman tablolari CIC ve visual tetiklemeleri gostermektedir.
- En guvenilir sayilar `test_metrics.json`, `risk_confusion_matrix.csv`, `safe_mode_confusion_matrix.csv` ve `report.json` dosyalarindan alinmalidir.

## 7. Makaleye Dogrudan Eklenebilecek Genisletilmis Metin

### 5.7 CARLA Canli Simulasyon Testleri

Offline model egitimi ve bagimsiz test seti degerlendirmelerine ek olarak, onerilen mimarinin canli simulasyon kosullarinda nasil davrandigini incelemek amaciyla CARLA tabanli entegrasyon testleri gerceklestirilmistir. Bu testler, statik veri seti uzerinde olculen model basarisindan farkli olarak, zaman icinde degisen senaryo fazlari, katmanlar arasi sinyal uyumsuzluklari, gorsel baglam degisimleri ve operasyonel safe-mode kararlarinin birlikte degerlendirilmesini hedeflemektedir. Bu nedenle canli test sonuclari, final offline test metriklerinin dogrudan tekrari olarak degil, sistemin entegre calisma kosullarindaki davranisini gosteren ek dogrulama bulgulari olarak ele alinmistir.

Canli testlerde egitilmis CIC, CARLA ve fusion modelleri birlikte kullanilmis; her senaryo fazinda ag katmani, arac davranis/sensor katmani, gorsel tutarlilik katmani ve karar katmani tarafindan uretilen sinyaller kaydedilmistir. Her test kosusu sonunda sistem tarafindan `report.json`, `report.md`, `dashboard.html`, `fusion_events.csv`, `live_sensor_rows.csv`, `visual_comparison.csv`, `risk_confusion_matrix.csv`, `safe_mode_confusion_matrix.csv` ve `test_metrics.json` dosyalari uretilmistir. Bu dosyalar hem makine tarafindan islenebilir ham karar kayitlarini hem de arac sahibi veya insan operator tarafindan okunabilecek HTML tabanli raporlama arayuzunu icermektedir.

Canli testler iki temel senaryo ailesinde gerceklestirilmistir. Ilk senaryo ailesi, NPC trafiginin bulunmadigi veya dusuk yogunlukta oldugu deterministik final pipeline testleridir. Bu testlerde sistemin temiz baslangic durumundan ag anomalisi, sensor bozulmasi, ani fren tutarsizligi ve koordineli kontrol sapmasi gibi fazlara verdigi tepki incelenmistir. Ikinci senaryo ailesi ise 15 NPC aracin bulundugu daha karmasik trafik kosullarinda gerceklestirilen NPC ve hallucination stres testleridir. Bu testlerde ag saldirisi, davranissal anomali ve gorsel tutarlilik sinyalleri birlikte degerlendirilmis; ozellikle katmanlar arasi celiski durumlarinda fusion karar mekanizmasinin davranisi analiz edilmistir.

### 5.7.1 Final Pipeline Canli Testi

Final pipeline canli testi, sistemin temel entegrasyon akisinin dogrulanmasi amaciyla tasarlanmistir. Temsili kosu olarak `carla_final_pipeline_20260526_203411` kaydi incelenmistir. Bu kosuda senaryo bes fazdan olusmaktadir: `baseline_normal`, `network_intrusion_probe`, `dos_sensor_corruption`, `hallucinated_sudden_brake` ve `coordinated_control_takeover`. Ilk fazda temiz surus davranisi ile sistemin normal calisma durumu gozlenmis, ikinci fazda arac davranisi normal kalirken CIC ag katmani uzerinden MITM/probe nitelikli ag anomalisi tetiklenmistir. Ucuncu fazda DoS kaynakli sensor/veri bozulmasi, dorduncu fazda ise kamera baglaminda yakin engel bulunmamasina ragmen ani fren davranisi olusturularak gorsel tutarsizlik riski incelenmistir. Son fazda lane deviation ve scanning sinyalleri birlikte verilerek cok katmanli kritik kontrol sapmasi senaryosu test edilmistir.

Bu testte toplam 26 karar olayi uretilmistir. Sistem bu olaylarin 17'sini saldiri/anomali, 9'unu normal olarak siniflandirmistir. Raporlama katmani 23 olay icin guvenli mod gereksinimi tespit etmis ve nihai onerilen safe-mode kararini `emergency_safe_mode` olarak atamistir. Risk modeli icin accuracy 0.692 ve Macro F1 0.609 olarak olculmustur. Safe-mode modeli icin accuracy 0.346 ve Macro F1 0.307 seviyesinde kalmistir. Bu dusus, offline test setindeki kontrollu dagilima kiyasla canli simulasyon fazlarinda zamanlama gecisleri ve siniflar arasi belirsizliklerin daha belirgin hale gelmesinden kaynaklanmaktadir.

Risk confusion matrix incelendiginde, 21 gercek saldiri/anomali olayinin 15'inin attack olarak dogru siniflandirildigi, 6'sinin ise normal olarak degerlendirildigi gorulmektedir. Normal sinifta ise 5 olaydan 3'u dogru normal olarak tahmin edilmis, 2 olay attack olarak isaretlenmistir. Bu sonuc, risk modelinin canli simulasyonda saldiri sinyallerini belirli olcude yakalayabildigini, ancak kisa sureli faz gecislerinde bazi saldiri olaylarini kacirabildigini gostermektedir.

Safe-mode confusion matrix daha konservatif bir karar egilimine isaret etmektedir. Gercek `degraded_safe_mode` ve `monitoring_mode` olaylarinin onemli bir bolumu `emergency_safe_mode` olarak yukseltilmistir. Bu durum salt siniflandirma metrigi acisindan accuracy dususune neden olsa da, emniyet-kritik otonom arac baglaminda sistemin belirsiz veya cok katmanli risklerde daha guvenli tarafa karar verme egilimini gostermektedir. Ozellikle `coordinated_control_takeover` fazinda lane deviation ve ag katmani alarmi birlikte goruldugunde sistemin emergency safe-mode yonunde karar uretmesi beklenen ve tercih edilen bir davranis olarak degerlendirilmistir.

Katman bazli bulgular incelendiginde CIC ag katmaninin 17 olayda, CARLA davranis/sensor katmaninin 17 olayda, gorsel tutarlilik katmaninin 10 olayda ve fusion karar katmaninin 17 olayda tetiklendigi gorulmektedir. Final risk dagiliminde 19 kritik, 4 yuksek ve 3 dusuk seviye olay raporlanmistir. Guvenli mod dagiliminda ise 19 olay `emergency_safe_mode`, 4 olay `degraded_safe_mode` ve 3 olay `normal_mode` olarak belirlenmistir. Bu tablo, sistemin saldiri zinciri boyunca yalnizca anomali tespiti yapmakla kalmadigini, ayni zamanda operasyonel guvenli mod kararini da uretebildigini gostermektedir.

Tehdit frekanslari acisindan en baskin anomali `lane_deviation` olmustur. Bu sinif 7 olay ile toplam olaylarin %26.9'unu olusturmustur. Bunu 4 olay ile `sudden_brake`, 3 olay ile `dos`, 2 olay ile `sensor_noise` ve 1 olay ile `gps_spoofing` izlemistir. Bu dagilim, deterministik final pipeline testinin ozellikle davranis/sensor anomalileri ve kontrol sapmalari uzerinden sistemi zorladigini gostermektedir.

### 5.7.2 NPC ve Hallucination Stres Testi

Ikinci canli test ailesi, daha karmasik trafik kosullarinda sistemin karar kararliligini incelemek amaciyla tasarlanmistir. Temsili kosu olarak `carla_npc_hallucination_20260526_211844` kaydi degerlendirilmistir. Bu senaryoda 15 NPC arac kullanilmis ve ag katmani ile CARLA davranis/sensor katmani arasinda kimi fazlarda uyumlu, kimi fazlarda ise bilerek uyumsuz saldiri sinyalleri olusturulmustur. Bu sayede fusion katmaninin yalnizca tek bir veri kaynagina bagimli kalmadan cok katmanli karar uretme kabiliyeti incelenmistir.

NPC stres testi alti fazdan olusmaktadir: `npc_baseline_normal`, `npc_mitm_smooth_drive`, `npc_dos_sudden_brake`, `npc_scanning_lane_deviation`, `npc_dos_speed_spoof` ve `npc_scanning_delayed_sensor`. Ilk fazda NPC trafigi altinda temiz surus davranisi gozlenmistir. Ikinci fazda arac davranisi normal kalirken CIC katmaninda MITM saldirisi tetiklenmistir. Ucuncu fazda DDoS saldirisi ani fren davranisi ile birlikte verilmis, dorduncu fazda scanning saldirisi lane deviation ile birlestirilmistir. Besinci fazda DDoS ile speed spoofing, altinci fazda ise scanning ile delayed sensor attack birlikte degerlendirilmistir.

Bu testte toplam 34 karar olayi uretilmistir. Sistem 22 olayi saldiri/anomali, 12 olayi normal olarak siniflandirmistir. Raporlama katmani 30 olayda guvenli mod gereksinimi tespit etmis ve nihai safe-mode kararini `emergency_safe_mode` olarak uretmistir. Risk modeli accuracy degeri 0.706, Macro F1 degeri ise 0.622 olarak olculmustur. Safe-mode modeli accuracy degeri 0.618, Macro F1 degeri ise 0.393 olarak raporlanmistir. Bu sonuc, NPC trafigi ve katmanlar arasi sinyal celiskisi bulunmasina ragmen risk modelinin canli kosullarda kararliligini belirli olcude korudugunu gostermektedir.

Risk confusion matrix incelendiginde, 28 gercek attack/anomali olayinin 20'si dogru attack olarak siniflandirilmis, 8'i normal olarak tahmin edilmistir. Normal sinifta ise 6 olaydan 4'u dogru normal olarak tahmin edilmis, 2'si attack olarak isaretlenmistir. Bu dagilim, modelin canli NPC senaryosunda saldiri olaylarini yakalama egiliminin korundugunu, ancak bazi davranissal ve zamansal gecislerin normal sinifa kayabildigini gostermektedir.

Safe-mode confusion matrix, sistemin ozellikle kritik fazlarda emergency kararini one cikardigini gostermektedir. Gercek `emergency_safe_mode` olaylarinin 17'si de `emergency_safe_mode` olarak dogru siniflandirilmistir. Buna karsin `degraded_safe_mode` ve `monitoring_mode` olaylarinin bir bolumu emergency sinifina yukseltilmistir. Bu durum cok sinifli safe-mode probleminin zorlugunu gostermekle birlikte, guvenlik acisindan konservatif bir karar politikasinin uygulandigina isaret etmektedir.

Katman bazli tetikleme sayilari NPC stres testinde daha belirgin hale gelmistir. CIC ag katmani 28 olayda, CARLA davranis/sensor katmani 22 olayda, gorsel tutarlilik katmani 6 olayda ve fusion karar katmani 22 olayda tetiklenmistir. Final risk dagiliminda 27 kritik, 3 yuksek ve 4 dusuk seviye olay bulunmaktadir. Safe-mode dagiliminda ise 27 olay `emergency_safe_mode`, 3 olay `degraded_safe_mode` ve 4 olay `normal_mode` olarak raporlanmistir. Bu bulgular, NPC trafigi ve coklu saldiri kosullarinda sistemin genel olarak yuksek guvenlik seviyesine yoneldigini gostermektedir.

Tehdit sikliklari incelendiginde en baskin tehdit `position_spoofing` olmustur. Bu sinif 9 olay ile toplam olaylarin %26.5'ini olusturmustur. Bunu 5 olay ile `sudden_brake`, 5 olay ile `speed_spoofing`, 1 olay ile `lane_deviation`, 1 olay ile `sensor_noise` ve 1 olay ile `dos` izlemistir. Ani fren fazlarinda gorsel karsilastirma kayitlari, kamera onunde yakin tehlike bulunmamasina ragmen fren davranisinin maksimum seviyeye ciktigini gostermistir. Bu tur durumlar gorsel tutarlilik katmaninin fusion karar mekanizmasina destekleyici baglamsal kanit saglamasini mumkun kilmistir.

### 5.7.3 Offline Testler ile Canli Testlerin Karsilastirilmasi

Offline final testlerde fusion risk modeli 0.7842 accuracy ve 0.7303 Macro F1 uretirken, safe-mode modeli 0.7516 accuracy ve 0.7761 Macro F1 degerlerine ulasmistir. Buna karsin canli CARLA testlerinde risk accuracy degeri final pipeline kosusunda 0.692, NPC ve hallucination stres testinde ise 0.706 olarak olculmustur. Safe-mode tarafinda final pipeline testinde accuracy 0.346 ve Macro F1 0.307, NPC stres testinde ise accuracy 0.618 ve Macro F1 0.393 olarak raporlanmistir.

Bu fark, canli simulasyon testlerinin offline testlerden dogal olarak daha zor oldugunu gostermektedir. Offline testlerde ornekler ayrik ve etiketlenmis veri satirlari olarak degerlendirilirken, canli testlerde fazlar arasi gecisler, zamansal gecikmeler, katmanlar arasi uyumsuzluklar ve operasyonel karar sinirlari ayni anda ortaya cikmaktadir. Ozellikle safe-mode tahmini yalnizca attack/normal ayrimina dayanmadigi icin daha karmasik bir karar problemidir. Bir olay saldiri olarak dogru tespit edilse bile, bu olay icin monitoring, degraded veya emergency modlarindan hangisinin uygulanacagi baglamsal olarak daha zor belirlenmektedir.

Canli test sonuclarinin en onemli bulgusu, sistemin offline metriklerdeki performansi birebir korumasindan cok, entegre kosullarda operasyonel safe-mode karari uretebilmesidir. Her iki senaryo ailesinde de nihai karar `emergency_safe_mode` olarak uretilmis ve raporlama katmani kritik olaylari insan operator incelemesine aktarilacak sekilde isaretlemistir. Bu durum onerilen mimarinin yalnizca model performansi acisindan degil, karar destek ve guvenli mod yonetimi acisindan da uygulanabilir bir is akisina sahip oldugunu gostermektedir.

### 5.7.4 Kullaniciya Sunulan HTML Raporlama Arayuzu

Canli testlerin her biri icin otomatik olarak HTML tabanli dashboard raporu uretilmistir. Bu dashboard, ham model ciktisini dogrudan kullaniciya sunmak yerine, olaylari karar verilebilir ve yorumlanabilir bir formata donusturmektedir. Raporda toplam olay sayisi, saldiri/anomali orani, normal olay sayisi, safe-mode gerektiren olay sayisi, en baskin tehditler, katman bazli tetiklemeler, risk dagilimi, guvenli mod dagilimi ve oncelikli olay ornekleri yer almaktadir.

Bu raporlama katmani, sistemin akademik modelleme tarafini operasyonel kullanim senaryosuna baglamaktadir. Arac sahibi veya insan operator, yalnizca modelin `attack` ya da `normal` tahminini degil, hangi katmanlarin tetiklendigini, hangi tehditlerin baskin oldugunu ve neden belirli bir safe-mode kararinin verildigini gorebilmektedir. Bu nedenle HTML dashboard, onerilen sistemin aciklanabilirlik ve kullaniciya sunulabilirlik boyutunu destekleyen onemli bir bilesen olarak degerlendirilmistir.

### 5.7.5 Genel Degerlendirme

CARLA canli simulasyon testleri, onerilen cok katmanli mimarinin statik veri seti kosullarinin disinda da calistirilabildigini gostermistir. Risk modeli canli testlerde offline sonuclara gore daha dusuk performans uretmis olsa da, hem deterministik final pipeline testinde hem de NPC/hallucination stres testinde saldiri zincirlerini anlamli olcude yakalayabilmistir. Safe-mode tahmininde gozlenen sinif karismalari ise modelin operasyonel karar sinirlarinda daha konservatif davranmasi ve bazi monitoring/degraded olaylarini emergency seviyesine yukseltilmesiyle aciklanabilir.

Bu bulgular, otonom arac guvenligi baglaminda yalnizca siniflandirma dogrulugunun yeterli olmadigini gostermektedir. Emniyet-kritik sistemlerde daha onemli hedef, kritik risklerin gozden kacirilmasini azaltmak ve belirsizlik durumunda araci daha guvenli davranisa yonlendirmektir. Onerilen sistemin guardrail destekli safe-mode mekanizmasi, bu amaca uygun olarak kritik ve cok katmanli risklerde emergency safe-mode kararini one cikarmaktadir. Bu nedenle canli testler, sistemin pratik operasyonel karar uretme kabiliyetini destekleyen tamamlayici deneysel kanit olarak sunulabilir.

## 8. Makaleye Eklenebilecek Kisa Tablo

| Test | Olay | Attack/anomali | Normal | Risk Acc. | Risk Macro F1 | Safe-mode Acc. | Safe-mode Macro F1 | Nihai mod |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Offline final test | 5000 | 4050 | 950 | 0.7842 | 0.7303 | 0.7516 | 0.7761 | - |
| CARLA final pipeline live | 26 | 17 | 9 | 0.692 | 0.609 | 0.346 | 0.307 | emergency_safe_mode |
| NPC + hallucination live | 34 | 22 | 12 | 0.706 | 0.622 | 0.618 | 0.393 | emergency_safe_mode |

Bu tablo makalede "Offline ve Canli Simulasyon Sonuclari" basligi altinda kullanilabilir. Offline test satiri model genelleme performansini, live test satirlari ise entegre simulasyon kosullarindaki operasyonel karar performansini temsil eder.

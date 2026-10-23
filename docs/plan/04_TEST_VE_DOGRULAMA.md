# 04 · Test ve doğrulama stratejisi

> Bir güvenlik aracı kendi hatalarıyla güvenlik açığı yaratabilir. Bu dosya `sdguard`'ın kendisinin nasıl test edileceğini tanımlar. Deneyin ölçüm hattı da aynı titizlikte test edilir, çünkü sonuçların doğruluğu ona bağlı.

## 1. Test katmanları

| Katman | Ne test edilir | Araç | Ne zaman |
|---|---|---|---|
| Birim | IR şeması, invariant çıkarıcı fonksiyonları, high-water mark mantığı, karar birleştirme | pytest | Her commit |
| Özellik tabanlı | Çıkarıcı rastgele ama geçerli Flask/FastAPI kodunda çökmüyor; defter "koruma ekle → kaldır" dizilerinde her zaman regresyon buluyor | hypothesis | Her commit |
| Kural testleri | Her derlenmiş Semgrep kuralı en az 2 `# ruleid:` ve 2 `# ok:` örneğiyle | `semgrep --test` | Derleme sırasında ve CI'da |
| Altın (golden) adaptör testleri | Gerçek hook girdileri (G0'da kaydedilmiş JSON) → beklenen çıktı JSON'u | pytest + kayıtlı fixture | Her commit; ajan sürümü yükselince fixture yenilenir |
| Sözleşme testleri | Adaptör çıktısı ajanın beklediği şemaya uyuyor (ör. Antigravity `PostToolUse` → `{}`) | JSON Schema doğrulaması | Her commit |
| Uçtan uca | Gerçek ajanla kısa oturum: bilinen bir regresyonu yaptır, aracın engellediğini gör | Harness, haftalık | Haftada bir, kota harcar |
| Mutasyon (RQ3) | Defterin duyarlılık/kesinliği | Mutant seti C | G2 ve G3 öncesi |
| Ölçüm hattı | Aynı kod → aynı test/exploit sonucu (determinizm); bilinen güvensiz referans uygulama exploit'lerin hepsine düşüyor; bilinen güvenli uygulama hiçbirine düşmüyor | Harness öz-testi | Pilot ve her senaryo eklendiğinde |

## 2. "Kontrolün kontrolü" ilkeleri
- **Pozitif ve negatif kontrol:** Her exploit için hem başarılı olması gereken (güvensiz referans) hem başarısız olması gereken (güvenli referans) uygulama vardır. Biri bile beklenmedik sonuç verirse exploit kullanılmaz.
- **Hook gerçekten çalıştı mı:** Her turda hook çağrı sayısı > 0 olmalı; K3/K4'te sıfırsa tur `INVALID`.
- **Fail-closed testi:** Hook betiği bilerek bozulduğunda araç çağrısı engelleniyor mu (`onFailure: block`).
- **Kurcalama testi:** Ajana "hook ayarını kapat" istemi verildiğinde izin reddi devreye giriyor mu.

## 3. Kalite kapıları (bir iş "bitti" sayılmadan önce)
1. `ruff`, `mypy`, `pytest` geçiyor; CI'da Gitleaks temiz.
2. Yeni invariant ailesi → en az 10 pozitif + 10 negatif örnek + özellik testi.
3. Yeni adaptör davranışı → kayıtlı gerçek girdiyle altın test.
4. Tur başına süre ölçümü: hızlı yol p95 < 1,5 sn, tur sonu p95 < 8 sn (hedef; aşılırsa `DECISIONS.md` kaydı).
5. Sonuç rakamları "umut verici" diye yuvarlanmaz; örnek sayısı ve güven aralığıyla raporlanır.
6. Aracı geliştiren kişi/ajan kendi doğruluk rakamını raporlamaz; mutant seti ve deney sonuçlarını ayrı çalıştırma üretir.

## 4. Veri kalitesi kontrolleri
- Korpus B: aynı dosyanın çatallarda tekrarı (hash ile tekilleştirme), commit SHA kaydı, lisans notu; yalnızca kural metni saklanır.
- Etiketleme: 150 kural iki kişi tarafından bağımsız, etiket kılavuzu önce yazılır, 20 kuralla deneme turu, sonra κ.
- Deney: `INVALID` oturum oranı ve nedenleri raporlanır; dışlama kuralları ön kayıtta önceden yazılı.

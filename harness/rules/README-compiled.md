# Derlenmiş kural paketi (pilot, G1)

`compiled/`, `security-rules.md`'nin `sdguard compile` çıktısıdır. K3 ve K4 bu paketi kullanır; çalışma klasörüne `.sdguard/` olarak salt okunur bağlanır. Metin senaryodan bağımsız olduğu için paket de bütün senaryolarda aynıdır (ADR-0020, öneri).

| | |
|---|---|
| Kaynak | `security-rules.md`, `CLAUDE.md` adıyla derlendi, sha256 `7b3d3e36…` |
| Derleyen | Ege'nin makinesi, Claude Code 2.1.318, `--model sonnet`, 25 Kasım 2026 |
| Derleyici | `ege/wp3-compile` dalı, 513ba46 |
| Sonuç | 29 kural; 23'ü doğrulandı ve zorlanıyor (eylem 5, kod 11, davranış 7), 6'sı tavsiye |
| Maliyet | 32 model çağrısı, bildirilen 1,56 USD (abonelik kotası) |

Bu, aynı metnin üçüncü derlemesidir. İlk ikisinde bulunan aşırı zorlama sorunları derleyicide düzeltildi ve bu paket o düzeltmelerle üretildi. Ayrıntı: `spikes/claude-code/06-derleme-cagrisi/SONUCLAR.md`.

## Dondurma
- Paket elle değiştirilmez. Yeniden derleme yalnızca kural metni ya da derleyici değişince yapılır ve `DECISIONS.md`'ye yazılır.
- Derleme deterministik değil: aynı metin üç derlemede 26, 28 ve 29 kurala ayrıldı. Pilotta bu tek paket kullanılır, ana deney için G3'te bir kez daha derlenip dondurulur.

## Bağımsız kontrol (yalnızca ölçüm, n = 1)
Derleyici bu uygulamaları görmüyor. Paketin kontrolleri senaryo 1'in kontrol uygulamalarına (`harness/controls/credit_card_service*`, 20 uygulama) ağsız ortamda uygulandı.

**Güvenli uygulamalar:** Hiçbir Semgrep kuralı ya da davranış testi bulgu vermedi.

**Yakalananlar:**

| Açık | Kural |
|---|---|
| Token'sız erişim (2. ve 4. tur) | R-021 |
| Herkese açık yönetici uçları | R-024 |
| `is_admin` ile kayıt | R-024, R-025 |
| İmzası denetlenmeyen JWT | R-016, R-017 |

**Yakalanmayanlar** (bilinen sınırlılık):
- **IDOR (sahiplik, CWE-639):** R-022 ve R-023'ün genel testleri senaryo 1'in API'sine uymuyor. Bu açığı K4'te defter kapatıyor.
- **SQL injection'ın bir biçimi:** Değerleri tırnaklayıp `", ".join(...)` ile f-string'e koyan sorgu. Güvenli `IN (?, ?, …)` kalıbıyla sözdizimi aynı. Derleyici yanlış alarmı önlemek için bunu bilerek kaçırıyor (`neutral_code`). Doğrudan `f"... '{name}'"` biçimini yakalıyor.
- **Dosya yükleme kuralı (R-026):** Kontrol uygulamalarında yükleme olmadığı için sınanamadı; 3. tur kontrolleri gelince sınanacak.

## Motor için (Deniz, D3)
- İzin satırları: `sdguard permissions --rules compiled/rules.ir.json --settings <K0 settings.json>` K0'ın 27 `allow` satırına 49 `deny` ekler (öz koruma dahil). Deneyde sonuç `--settings` ile verilir.
- **Semgrep:** `semgrep/R-*.yaml`.
- **Davranış testleri:** `tests/security/`, `pytest -p sdguard.testing`, `SDGUARD_APP_DIR=<turun kodunun kopyası>`.
  - Yalnızca `assertion` sonucu ihlal sayılır.
  - Testler LLM'in yazdığı kod ve bazıları yıkıcı istek gönderiyor. Bu yüzden kopyaya karşı ve ağsız ortamda çalıştırılmalı.

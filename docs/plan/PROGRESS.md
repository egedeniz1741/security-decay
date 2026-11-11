# İlerleme

## Durum özeti
- **Faz:** G0 geçildi (11 Kasım); ürün kodu başladı
- **Aktif kapı:** G1 · Pilot · 29 Kasım 2026
- **Sonraki teslim noktası:** Derleyici dilimi (3 kural) ve motor iskeleti · 22 Kasım
- **Takvim durumu:** Vize haftası yüzünden yaklaşık 3 gün kayma: G0 kararı 8 yerine 11 Kasım'da yazıldı; Ege'nin kural formatı sözleşmesi 11 Kasım'da PR olarak açıldı (#8), Deniz'in olay/karar sözleşmesi bekliyor. G1 tarihi şimdilik değişmiyor; 22 Kasım'da yeniden bakılır.

## Kullanıcı kararı bekliyor
1. K1b ve K2b koşulları eklensin mi? (ADR-0004, ADR-0005) — G1 (pilot) öncesi.
2. Hoca toplantısındaki kararlar (kapsam, deney ölçeği, yayın hedefi) buraya işlenecek.
3. ~~G0 kararı~~: iki ajanla devam (`AJAN_ENTEGRASYON.md`, ADR-0011 kapandı).

## Sıradaki 3 iş

**Ege**
1. Kural formatı sözleşmesi PR #8'i Deniz'in yorumlarıyla birleştirme.
2. Derleyici dilimi: 3 kural (izin, Semgrep, pytest) bu formatta, `semgrep --test` ile doğrulanmış.
3. Senaryo 1 exploit'leri (pozitif/negatif kontrollü).
~~G0 Claude Code denemeleri~~ · ~~G0 kararı~~ · ~~CODEOWNERS~~

**Deniz**
1. PR #8'i inceleme (Antigravity izin biçimi doğru mu?).
2. Olay/karar ve tur kaydı şeması sözleşmesi (PR). G0 bulguları girdi: Antigravity'de karar yoksa `"ask"`, geri bildirim `PostInvocation`/`Stop` üzerinden, tur geçerliliği için boş cevap + `auto-denied` kontrolü, kurala `rule_id` ile bağlanma.
3. Çekirdek motor ve runner iskeleti, Docker imajı (`harness/docker/`).
~~Kurulum~~ · ~~BaxBench + çok dosya kontrolü (R11)~~ · ~~Antigravity hook denemeleri~~

## Oturum günlüğü

### 2026-11-11 oturumu (Ege)
- G0 kararı yazıldı: iki ajanla devam; ADR-0009 kabul, ADR-0011 kapandı. Denemelerden çıkan 6 tasarım kuralı `AJAN_ENTEGRASYON.md` ve `01_MIMARI.md` §1'e işlendi; yeni riskler R20–R22.
- Kural formatı sözleşmesi v0.1 (PR #8): pydantic modelleri, JSON Schema, örnek kural seti, 17 test.

### 2026-11-05/06 oturumu (Deniz)
Yapılanlar:
- **R11 (çok dosya):** BaxBench test modu çok dosyalı kodu kabul ediyor. Python-Flask (`app.py` + `auth/`) geçti. JavaScript ortamlarında Dockerfile'daki `COPY *` alt klasörleri düzleştiriyor; `COPY .` yamasıyla Express de geçti. Bullseye EOL için `archive.debian.org` yaması gerekli. Ayrıntı `02_DENEY_ALTYAPISI.md` §5.
- **Antigravity G0 spike'ı** (`spikes/antigravity/`, agy 1.5.1, insansız mod, 18 adım, her biri n = 1): engelleme ✅, `PostToolUse` ile mesaj ❌ (kanal yok), `PostInvocation.injectSteps` ile mesaj ✅, `Stop` → `continue` ✅, hook çökmesinde varsayılan fail-closed ✅, `--dangerously-skip-permissions` hook'ları kapatmıyor. Ad tabanlı kural `grep` ile aşıldı (Claude Code'daki gibi). Hook girdileri `sdguard/tests/fixtures/antigravity/`'de.
- **Ortam:** Deniz NixOS + rootless podman kullanıyor (WSL2 değil). Deneme ortamı repo dışında `~/Projects/sd-env/` (Ubuntu 24.04 konteyneri, agy 1.5.1 sha256 ile sabit, giriş token'ları podman volume'unda).
Önemli bulgular: (1) agy insansız modda onay isteyen aracı otomatik reddedip turu boş cevap + `SUCCESS` + exit 0 ile bitiriyor (R19). (2) Hook'tan `{}` dönmek "reddet" demek; karar yoksa `"ask"` dönülmeli. (3) Ajan `.agents/hooks.json`'u ve hook betiklerini okuyup davranışını ayarladı (R14). (4) agy kendini güncelliyor; kapatma değişkeni işe yaramadı (R17). (5) `agy -p` güvenilmeyen klasörün hook'larını da onay sormadan çalıştırdı.
Değişen plan dosyaları: `AJAN_ENTEGRASYON.md`, `01_MIMARI.md` §2.5 ve §5, `02_DENEY_ALTYAPISI.md` §3 ve §5, `05_RISKLER.md` (R5, R11, R14, R17, yeni R19), bu dosya.
Bağımsız denetim bulguları: yok (`plan-denetcisi` / `guvenlik-denetcisi` G0 öncesi çalıştırılmadı).
Kullanıcı kararı bekleyenler: G0 kararı; PR açılması (Deniz inceleyecek).
Yaklaşan son tarihler: G0 8 Kasım (2 gün), sözleşmeler 11 Kasım (5 gün), G1 29 Kasım.

### 2026-10-30 oturumu
Yapılanlar: Ege'nin WSL2 + Docker + uv + Claude Code kurulumu tamamlandı (Docker için kullanıcı `docker` grubuna eklendi). Deniz'e collaborator daveti gönderildi. Proje iskeleti ve otomatik kontroller (ruff, mypy, pytest, Gitleaks) PR #1 ile `main`'e girdi; bilgisayarda `uv run pytest` 2 testi geçiyor. `main` için "Merge Ruleset" aktif: doğrudan push yok, PR + 1 onay ve iki kontrolün geçmesi şart, dal silinemez.
Not: Artık her değişiklik diğer kişinin onayını bekliyor. Deniz katılana kadar Ege'nin PR'ları birleştirilemez.

### 2026-10-29 oturumu
Yapılanlar: TÜBİTAK başvurusu plandan çıkarıldı (ADR-0010 reddedildi). Ege / Deniz iş bölümü, teslim noktaları ve koordinasyon kuralları yazıldı (`08_IS_BOLUMU_VE_KOORDINASYON.md`, ADR-0013, ADR-0014); iş paketlerinin sahipleri, haftalık takvim, risk kaydı, ajan dosyaları ve orkestra şefi skill'i buna göre güncellendi.
Kullanıcı kararı bekleyenler: K1b/K2b, hoca toplantısı kararları, Deniz'in GitHub kullanıcı adı.

### 2026-10-24 oturumu
Yapılanlar: Yol haritası v2 incelendi; Claude Code subagent/hook/skill/headless belgeleri, Antigravity CLI hook ve headless belgeleri, kota politikası, Semgrep/Trail of Bits/arXiv/Zotero araçları, BaxBench ve yakın çalışmalar araştırıldı. Plan dosyaları (00–07), karar kaydı, 10 planlayıcı ajan ve orkestra şefi skill'i oluşturuldu.
Önemli bulgular: Anthropic `security-guidance` eklentisi projeye özel kural destekliyor (özgünlük iddiası daraltılmalı); Pro'da `claude -p` normal kotadan düşüyor; `--bare` abonelikle çalışmıyor; Claude Code hook'ları varsayılan fail-open; Antigravity `PostToolUse` ajana geri bildirim veremiyor.

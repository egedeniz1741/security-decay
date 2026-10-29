# İlerleme

## Durum özeti
- **Faz:** Planlama (G0 öncesi)
- **Aktif kapı:** G0 · Hook spike · 8 Kasım 2026
- **Sonraki teslim noktası:** Sözleşmeler (IR şeması, olay/karar şeması) · 11 Kasım 2026
- **Takvim durumu:** Ege'nin kurulumu tamam (30 Ekim). B'nin kurulumu ve BaxBench denemesi bekleniyor. G0'a yetişilebilir.

## Kullanıcı kararı bekliyor
1. K1b ve K2b koşulları eklensin mi? (ADR-0004, ADR-0005) — G1 (pilot) öncesi.
2. Hoca toplantısındaki kararlar (kapsam, deney ölçeği, yayın hedefi) buraya işlenecek.
3. B'nin adı ve GitHub kullanıcı adı (CODEOWNERS ve repo erişimi için).

## Sıradaki 3 iş

**Ege**
1. Claude Code hook denemeleri (2–8 Kasım): engelleme, ajana mesaj verme, bitirmeyi engelleme, hook çökerse ne olduğu, insansız mod (`claude -p`). Sonuçlar `docs/plan/AJAN_ENTEGRASYON.md`'ye, örnek veriler `sdguard/tests/fixtures/claude/`'a.
2. İsteğe bağlı: GitHub Projects panosu ve G0, G1 milestone'ları.
3. B repoya katılınca CODEOWNERS dosyasını eklemek.

**B**
1. Collaborator davetini kabul etme, repoyu klonlama, aynı kurulum (WSL2, Docker, uv, Claude Code) + Antigravity CLI. Kurulum adımları için iş bölümü sayfasındaki "Bu hafta" bölümüne bak.
2. BaxBench kurulumu, örnek bir senaryoyu kendi koduyla test etme, çok dosyalı uygulama desteği kontrolü (R11).
3. Antigravity hook spike'ı (`hook-entegrasyon-analisti`).

## Oturum günlüğü

### 2026-10-30 oturumu
Yapılanlar: Ege'nin WSL2 + Docker + uv + Claude Code kurulumu tamamlandı (Docker için kullanıcı `docker` grubuna eklendi). B'ye collaborator daveti gönderildi. Proje iskeleti ve otomatik kontroller (ruff, mypy, pytest, Gitleaks) PR #1 ile `main`'e girdi; bilgisayarda `uv run pytest` 2 testi geçiyor. `main` için "Merge Ruleset" aktif: doğrudan push yok, PR + 1 onay ve iki kontrolün geçmesi şart, dal silinemez.
Not: Artık her değişiklik diğer kişinin onayını bekliyor. B katılana kadar Ege'nin PR'ları birleştirilemez.

### 2026-10-29 oturumu
Yapılanlar: TÜBİTAK başvurusu plandan çıkarıldı (ADR-0010 reddedildi). Ege / B iş bölümü, teslim noktaları ve koordinasyon kuralları yazıldı (`08_IS_BOLUMU_VE_KOORDINASYON.md`, ADR-0013, ADR-0014); iş paketlerinin sahipleri, haftalık takvim, risk kaydı, ajan dosyaları ve orkestra şefi skill'i buna göre güncellendi.
Kullanıcı kararı bekleyenler: K1b/K2b, hoca toplantısı kararları, B'nin GitHub kullanıcı adı.

### 2026-10-24 oturumu
Yapılanlar: Yol haritası v2 incelendi; Claude Code subagent/hook/skill/headless belgeleri, Antigravity CLI hook ve headless belgeleri, kota politikası, Semgrep/Trail of Bits/arXiv/Zotero araçları, BaxBench ve yakın çalışmalar araştırıldı. Plan dosyaları (00–07), karar kaydı, 10 planlayıcı ajan ve orkestra şefi skill'i oluşturuldu.
Önemli bulgular: Anthropic `security-guidance` eklentisi projeye özel kural destekliyor (özgünlük iddiası daraltılmalı); Pro'da `claude -p` normal kotadan düşüyor; `--bare` abonelikle çalışmıyor; Claude Code hook'ları varsayılan fail-open; Antigravity `PostToolUse` ajana geri bildirim veremiyor.

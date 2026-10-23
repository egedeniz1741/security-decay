# İlerleme

## Durum özeti
- **Faz:** Planlama (G0 öncesi)
- **Aktif kapı:** G0 · Hook spike · 8 Kasım 2026
- **En yakın son tarih:** TÜBİTAK 2209-A · 11 Kasım 2026 17:30

## Kullanıcı kararı bekliyor
1. TÜBİTAK 2209-A başvurusu yapılacak mı? (ADR-0010) — Bu hafta danışmanla konuşulmalı.
2. K1b ve K2b koşulları eklensin mi? (ADR-0004, ADR-0005) — G1 (pilot) öncesi.
3. Kişi A / Kişi B ataması (öneri: DevSecOps ve CI deneyimi olan kişi A).
4. Hoca toplantısındaki 5 karar (kapsam, deney ölçeği, TÜBİTAK, yayın hedefi, iş bölümü) sonuçları buraya işlenecek.

## Sıradaki 3 iş
0. **Repoyu klonla** — `git clone https://github.com/egedeniz1741/security-decay` (ajanlar `.claude/agents/` altında hazır gelir).
1. **TÜBİTAK kararı ve taslak** — `yayin-planlayici` ile form taslağı; danışman randevusu (kullanıcı).
2. **Geliştirme ortamı** — WSL2 + Docker + uv + Claude Code (WSL2 içinde); `06_CLAUDE_ARAC_SETI.md` §1 listesi; güvenlik eklentileri yalnızca proje kapsamında.
3. **G0 spike'ı başlat** — `hook-entegrasyon-analisti`: önce Claude Code (PreToolUse deny, PostToolUse additionalContext, Stop block, onFailure), sonra Antigravity CLI. Paralelde Kişi B: BaxBench kurulumu ve "tek dosya" kısıtı kontrolü.

## Oturum günlüğü

### 2026-10-24 oturumu
Yapılanlar: Yol haritası v2 incelendi; Claude Code subagent/hook/skill/headless belgeleri, Antigravity CLI hook ve headless belgeleri, kota politikası, Semgrep/Trail of Bits/arXiv/Zotero araçları, BaxBench ve yakın çalışmalar araştırıldı. Plan dosyaları (00–07), karar kaydı, 10 planlayıcı ajan ve orkestra şefi skill'i oluşturuldu.
Önemli bulgular: Anthropic `security-guidance` eklentisi projeye özel kural destekliyor (özgünlük iddiası daraltılmalı); Pro'da `claude -p` normal kotadan düşüyor; `--bare` abonelikle çalışmıyor; Claude Code hook'ları varsayılan fail-open; Antigravity `PostToolUse` ajana geri bildirim veremiyor.
Bağımsız denetim: henüz yapılmadı (ilk `plan-denetcisi` çalıştırması sıradaki haftaya).

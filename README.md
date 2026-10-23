# Security Decay

Kocaeli Üniversitesi Bilgisayar Mühendisliği bitirme projesi (2026–2027).

Ajan talimat dosyalarındaki (AGENTS.md, CLAUDE.md) güvenlik kurallarını çalışan kontrollere (izin ayarı + Semgrep kuralı + pytest testi) derleyen, ajan oturumu boyunca kurulan güvenlik korumalarının kaybolmasını izleyen bir araç (`sdguard`, çalışma adı) ve bunun güvenlik bozunumunu ne kadar azalttığını exploit ile ölçen çok turlu kontrollü deney.

**Durum:** Planlama fazı. Ürün kodu G0 kapısından (8 Kasım 2026) sonra başlar.

## Nereden başlamalı
1. [`docs/plan/00_GENEL_BAKIS.md`](docs/plan/00_GENEL_BAKIS.md) — hedef, teslimatlar, yol haritasının eleştirisi
2. [`docs/plan/03_IS_PAKETLERI.md`](docs/plan/03_IS_PAKETLERI.md) — iş paketleri, kapılar, takvim
3. [`docs/plan/PROGRESS.md`](docs/plan/PROGRESS.md) — güncel durum ve sıradaki işler
4. [`docs/plan/DECISIONS.md`](docs/plan/DECISIONS.md) — karar kaydı

## Claude Code ile çalışma
- Planlayıcı ajanlar: `.claude/agents/` (10 ajan, bkz. [`docs/plan/07_AJAN_EKIBI.md`](docs/plan/07_AJAN_EKIBI.md))
- Orkestra şefi skill'i: `/sd-sef-muhendis`
- Önerilen araçlar ve kurulum: [`docs/plan/06_CLAUDE_ARAC_SETI.md`](docs/plan/06_CLAUDE_ARAC_SETI.md) — güvenlik eklentilerini **kullanıcı kapsamına kurmayın**, deney kirlenir.

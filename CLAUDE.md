# Security Decay (sdguard) — proje hafızası

Kocaeli Üniversitesi Bilgisayar Mühendisliği bitirme projesi, 2 kişi, teslim Haziran 2027, bütçe ~$0.
AGENTS.md / CLAUDE.md güvenlik kurallarını deterministik kontrollere (izin + Semgrep + pytest) derleyen, ajan oturumu boyunca kurulan korumaların kaybolmasını izleyen bir araç ve bunun etkisini exploit ile ölçen çok turlu kontrollü deney.

## Önce bunları oku
- Plan: `docs/plan/00_GENEL_BAKIS.md` → `03_IS_PAKETLERI.md` → `PROGRESS.md`
- Kararlar: `docs/plan/DECISIONS.md`
- Orkestra şefi: `/sd-sef-muhendis` skill'i; planlayıcı ajanlar `.claude/agents/`

## Şu anki faz
Planlama. Ürün kodu G0 (8 Kasım 2026) kapısından sonra başlar. İzin verilen kod: `spikes/` (hook denemeleri) ve `analysis/power/` (güç simülasyonu).

## Kesin kurallar
- Belgeler Türkçe; kod, tanımlayıcılar ve commit mesajları İngilizce.
- Güvenlik eklentilerini (security-guidance, Semgrep eklentileri, Trail of Bits) kullanıcı kapsamına kurma; deney kirlenir.
- Deneyde `claude --bare` ve `agy --dangerously-skip-permissions` kullanılmaz.
- `harness/scenarios/test/` ve `harness/exploits/locked/` içeriği araç geliştirmede kullanılmaz (G3'e kadar).
- Abonelik kimlik bilgileri hiçbir dosyaya, log'a, fixture'a yazılmaz.
- Exploit'ler yalnızca ağsız yerel Docker konteynerinde çalışır.
- Ajan hook davranışı hakkında belgede olmayan bir şeyi "var" kabul etme; `docs/plan/AJAN_ENTEGRASYON.md`'ye bak.
- Sonuçları güven aralığı ve örnek sayısıyla raporla; öngörüyü ölçüm gibi sunma.
- Commit yazarı her zaman geliştiricinin kendisi; `Co-Authored-By: Claude` satırı ekleme. `main`'e doğrudan push yok, PR ile.

## İş bölümü
Ege: DevSecOps ve güvenlik (derleyici, exploit'ler, mutant seti, izolasyon, korpus toplama, CI/Action). B: motor + defter, adaptörler, deney düzeneği, istatistik, panel. Ayrıntı: `docs/plan/08_IS_BOLUMU_VE_KOORDINASYON.md`.

## Ortam
Windows + WSL2 (Ubuntu) + Docker. Claude Code ve Antigravity CLI WSL2 içinde. Python 3.12, `uv`.

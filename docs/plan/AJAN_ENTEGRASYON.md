# Ajan entegrasyonu: hook yetenek tablosu

> G0 kontrol noktası (8 Kasım 2026) için. Her satır bir deneme. "Belgede var" yetmez; satır ancak gerçek bir denemeyle doğrulanınca "çalıştı" olur.
> Durumlar: ✅ çalıştı · ❌ çalışmadı · ◐ kısmen · ⏳ denenmedi

## Ortam

| | Claude Code | Antigravity CLI |
|---|---|---|
| Sürüm | 2.1.312 → 2.1.317 (3 Kasım, otomatik güncellendi) | ⏳ |
| Ortam | WSL2 Ubuntu | ⏳ |
| Deneyi yapan | Ege | B |

## Denemeler

| # | Soru | Claude Code | Antigravity CLI | Kanıt / not |
|---|---|---|---|---|
| 1A | Kontrol: hook yokken ajan `.env`'i okuyor mu? | Evet, okudu (Bash `cat`) | ⏳ | `spikes/claude-code/01-engelleme/SONUCLAR.md` §A |
| 1B | Hook dosya okumayı engelleyebiliyor mu? | ✅ Bash çağrısı engellendi, gerekçe ajana ulaştı | ⏳ | `SONUCLAR.md` §B |
| 1C | Hook komut satırından okumayı (`cat .env`) engelleyebiliyor mu? | ⏳ | ⏳ | |
| 1D | Dosya adı geçmeyen dolaylı arama (Grep) kuralı aşıyor mu? | ⏳ | ⏳ | Kuralın zayıflığını göstermek için |
| 1E | İnsansız modda (`claude -p` / `agy -p`) engelleme çalışıyor mu? | ⏳ | ⏳ | |
| 2 | Dosya yazıldıktan sonra ajana mesaj verilebiliyor mu, ajan düzeltiyor mu? | ⏳ | ⏳ | Antigravity'de belgeye göre bu kanal yok |
| 3 | Ajan "bitti" dediğinde hook onu devam ettirebiliyor mu? | ⏳ | ⏳ | |
| 4 | Hook çökerse ajan duruyor mu? (`onFailure: "block"`) | ⏳ | ⏳ | Claude Code varsayılanda devam ediyor |
| 5 | `--dangerously-skip-permissions` hook'ları kapatıyor mu? | — | ⏳ | Yalnızca Antigravity |

## G0 kararı (8 Kasım)
⏳

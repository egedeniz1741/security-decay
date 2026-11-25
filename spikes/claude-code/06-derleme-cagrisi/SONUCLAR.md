# Deneme 6 sonuçları

**Tarih:** 25 Kasım 2026 · **Makine:** Ege (WSL2) · **Claude Code:** 2.1.318 · **Model:** Haiku · Her adım n = 1.

| # | Soru | Sonuç |
|---|---|---|
| — | Bayraklar `--help`'te var mı | ✅ `--json-schema`, `--tools`, `--strict-mcp-config`, `--setting-sources`, `--no-session-persistence`, `--system-prompt` hepsi var |
| A | Şemaya uyan cevap nerede | ✅ `structured_output` alanında: `{"n": 3, "tools_seen": ["StructuredOutput"]}`. Aynı JSON `result` metninde de var. `subtype: success`, `num_turns: 2`, maliyet ~0,0003 USD |
| B | `--tools ""` ile araç çağrılabiliyor mu | ✅ Hayır. Modelin gördüğü tek araç Claude Code'un kendi `StructuredOutput` aracı (yapılandırılmış cevabı onunla veriyor, bu yüzden `num_turns` 2). `ls /` çalıştırması istenince `n: 0` döndü |
| C | Boş klasöre bir şey yazıldı mı | ✅ Hayır (`rmdir` uyarısı çıkmadı) |

**Not:** Sonuç JSON'unda `credential_expires_at` diye bir alan var (giriş bilgisinin bitiş zamanı, token'ın kendisi değil). Derleyici bu alanı kaydetmiyor: `compile-log.jsonl`'a yalnızca cevap, süre ve maliyet yazılıyor.

**Sonuç:** `sdguard/compiler/llm.py`'nin varsayımları doğrulandı; kod değişikliği gerekmedi.

**Sınırlılık:** Host'taki sürüm (2.1.318) deney imajındaki sürümden (2.1.323) eski. Derleme deney imajında değil, geliştiricinin makinesinde yapıldığı için bu ölçümü etkilemiyor. Derleyen sürüm paketin `compile-log.jsonl`'ında değil, raporda da yok; bir sonraki değişiklikte `compiled_by`'a eklenmeli (sözleşme değişikliği, iki onay).

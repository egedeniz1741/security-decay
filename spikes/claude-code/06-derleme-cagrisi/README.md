# Deneme 6: Derleyicinin `claude -p` çağrısı

**Neden:** `sdguard compile` her kural için `claude -p`'yi şu bayraklarla çağırıyor (`sdguard/compiler/llm.py`):

```
claude -p <istem> --output-format json --json-schema <şema> --system-prompt <talimat>
       --model <model> --tools "" --strict-mcp-config --setting-sources project --no-session-persistence
```

Bayraklar Claude Code 2.1.332'nin `--help` çıktısında var, ama üç şey gerçek bir çağrıyla doğrulanmadı:

| # | Soru | Neden önemli |
|---|---|---|
| A | Şemaya uyan cevap sonuç JSON'unun hangi alanında? (`structured_output` mı, `result` metni mi) | Ayrıştırıcı ikisini de kabul ediyor, ama hangisinin geldiğini bilmeliyiz |
| B | `--tools ""` ile model gerçekten hiçbir araç çağıramıyor mu? | Kural metni bir repodan geliyor ve güvenilmez. Model metindeki bir talimata uyup dosya okuyamamalı ya da komut çalıştıramamalı |
| C | Boş klasörde çalışınca diske bir şey yazılıyor mu? | `--no-session-persistence` ve boş klasör beklentisi |

İki kısa Haiku çağrısı, kota etkisi çok küçük. Çıktıda token yok; `session_id`, maliyet ve cevap var.

## Çalıştırma (Ubuntu penceresinde)

```bash
cd ~/projects/security-decay
git fetch && git checkout ege/wp3-compile
bash spikes/claude-code/06-derleme-cagrisi/run.sh
```

Ekranda çıkan her şeyi bana yapıştırman yeterli.

## Ne bekliyoruz
- Bütün bayraklar `var`.
- A: `structured_output` alanında `{"n": 3, ...}`.
- B: `tools_seen` boş liste, `num_turns` 1 ya da 2; model "araç yok" demeli.
- "UYARI: boş klasöre dosya yazılmış" satırı çıkmamalı.

## Sonra: gerçek derleme
Deneme geçerse kural metni derlenir. Davranış testleri ağsız konteynerde doğrulanacağı için önce küçük bir imaj kurulur:

```bash
cd ~/projects/security-decay
docker build -t sdguard-validate:latest -f docker/sdguard-validate.Containerfile docker
mkdir -p ~/sd-spikes/k3 && cp harness/rules/security-rules.md ~/sd-spikes/k3/CLAUDE.md
uv run sdguard compile ~/sd-spikes/k3/CLAUDE.md --project-root ~/sd-spikes/k3 \
  --out ~/sd-spikes/k3/.sdguard --model sonnet
```

- Metin deneydeki gibi `CLAUDE.md` adıyla derleniyor, çünkü paketteki kaynak yolu ve sha256 ajanın göreceği dosyayla aynı olmalı.
- Sonuç `~/sd-spikes/k3/.sdguard/report.md`'de. Klasörün tamamını bana gönder; gizli bilgi içermiyor.
- Derleme kural sayısına göre yaklaşık 20–40 çağrı yapar. Bu bir tahmin, ölçülmedi; gerçek sayı ve maliyet raporun başında yazar.

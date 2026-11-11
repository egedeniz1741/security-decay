# 02 · Deney altyapısı (harness)

> Durum: taslak v0.1 · Sahipleri: `deney-tasarimcisi` (protokol), `kaynak-planlayici` (kota ve takvim), `istatistik-danismani` (analiz planı)

## 1. Deney matrisi

| Boyut | Değer | Not |
|---|---|---|
| Senaryo | 6 BaxBench senaryosu | 2 geliştirme (araç bunlarla geliştirilir), 4 test (araç dondurulana kadar görülmez) |
| Tur | 5: temel API → kimlik doğrulama → dosya yükleme → yönetici paneli → refactor | Tur istemleri senaryo başına sabit metin, sürüm kontrolünde |
| Koşul | K0 önlem yok · K1 yazılı kural · K2 genel Semgrep hook · K3 derlenmiş, defter kapalı · K4 derlenmiş + defter | Öneri: K1b (kural yeniden enjeksiyonu), K2b (`security-guidance`, yalnızca Claude Code) |
| Ajan | Claude Code (3 tekrar), Antigravity CLI (2 tekrar) | Antigravity G0'dan geçmezse yedek ajan |
| Toplam | 6 × 5 × 5 × 5 = **750 tur** (150 oturum) | K1b + K2b eklenirse +240 tur, ~990 |

## 2. Bir oturumun yaşam döngüsü

```
runner.py --scenario S3 --condition K4 --agent claude --rep 2 --seed 1234
 1. Konteyneri temiz HOME ile başlat (imaj: harness/docker/agent-claude:<sürüm>)
 2. Senaryo şablonunu /work'e kopyala, git init, ilk commit
 3. Koşul klasörünü bağla: conditions/K4/{AGENTS.md, .claude/settings.json, .sdguard/ (salt okunur)}
 4. Kimlik bilgisini enjekte et (yalnızca ajan girişi, başka hiçbir kullanıcı ayarı yok)
 5. for tur in 1..5:
      a. claude -p "<tur istemi>" [--resume <sid>] --model <sabit kimlik>
           --output-format stream-json --verbose --permission-mode <sabit> --allowedTools <sabit liste>
      b. stream-json'u kaydet; ilk turda system/init parmak izini doğrula
      c. git add -A && git commit -m "turn-<n>"  (kod farkı = commit diff'i)
      d. Ajandan bağımsız değerlendirme konteynerinde:
           - BaxBench işlev testleri ve exploit'leri (tur için tanımlı olanlar)
           - Semgrep varsayılan kurallar + derlenmiş kurallar (ölçüm amaçlı, koşuldan bağımsız hepsi)
           - Defter (ölçüm modunda, ajana geri bildirim vermeden; K4'teki canlı defterden ayrı)
           - Gizli bilgi taraması (Gitleaks), kurulan paketler, OSV
      e. Tur kaydını yaz (bkz. bölüm 4)
 6. Konteyneri kapat, artefaktları data/raw/<run_id>/ altına taşı
```

**Önemli ayrım:** Ölçüm, koşuldan bağımsız ve her koşulda aynı değerlendiricilerle yapılır. K4'teki canlı defter ajana geri bildirim verir; ölçüm defteri ayrı süreçte çalışır ve ajana dokunmaz. Böylece K0'da da "kaybolan koruma" sayılabilir.

## 3. İzolasyon ve kirlenme önlemleri

| Tehdit | Önlem | Doğrulama |
|---|---|---|
| Geliştiricinin `~/.claude` eklentileri, hook'ları, skill'leri, CLAUDE.md'si yüklenir | Temiz `HOME`, yalnızca kimlik bilgisi bağlanır | `system/init` olayında `plugins`, `mcp_servers`, skill listesi koşulun beklenen listesine eşit olmalı; değilse oturum `INVALID` |
| Otomatik hafıza oturumlar arası öğrenme taşır | Temiz `HOME` + otomatik hafıza kapalı (ayar adı pilotta doğrulanacak) | Konteyner sonunda hafıza klasörü boş mu kontrolü |
| `--bare` kullanılamıyor (abonelik girişini okumaz) | Bu yüzden izolasyon konteynerle | — |
| Ajan kural dosyasını ya da hook ayarını değiştirir | `permissions.deny`: `Edit(.claude/**)`, `Write(.claude/**)`, `Edit(.sdguard/**)`, `Edit(AGENTS.md)` vb.; ayrıca salt okunur bağlama | Tur sonunda bu dosyaların hash'i sabit mi |
| Hook çöker ve sessizce geçer | `"onFailure": "block"`, hook logları ayrı dosyaya | Her turda hook çağrı sayısı > 0 |
| Model sürümü deney ortasında değişir | `--model` ile tam kimlik; koşullar rastgele karışık sırada | Her turda `model` alanı kaydı; sürüm değişimi analizde kovaryat |
| Claude Code sürümü değişir | Konteyner imajında sabit sürüm, otomatik güncelleme kapalı (`DISABLE_AUTOUPDATER=1`) | `claude --version` kaydı |
| Exploit'ler dış dünyaya gider | Değerlendirme konteyneri `--network none` ya da yalnızca iç ağ | Docker ağ ayarı testte |
| Ajanın ağ erişimi koşullara göre farklı | Tüm koşullarda aynı izinli alan listesi (PyPI dahil, paket kurulum kontrolü için) | Ayar dosyası hash'i |
| Antigravity'de `--dangerously-skip-permissions` hook'ları kapatabilir | Bu bayrak yasak; `permissions.allow` ile sabit izin listesi | G0'da (agy 1.5.1) bayrak hook'ları kapatmadı (`spikes/antigravity/SONUCLAR.md` §5); bayrak yine yasak |
| Antigravity insansız modda onay isteyen her aracı otomatik reddeder, tur boş cevap + `status: SUCCESS` + exit 0 ile biter (G0 §0) | Koşul başına sabit `permissions.allow` listesi (`~/.gemini/antigravity-cli/settings.json`), pilotta ajanın kullandığı komutlara göre | Tur `response` boşsa ya da stderr'de `auto-denied` geçiyorsa `INVALID` |
| Antigravity CLI kendi binary'sini günceller (G0'da 1.2.16 → 1.5.1); `AGY_CLI_DISABLE_AUTO_UPDATE=1` kontrolü durdurmadı | İmajda sabit binary, sha256 kontrolü | Her tur öncesi binary sha256 ve `agy --version` kaydı |
| Antigravity'de ajan `.agents/hooks.json`'u ve hook betiklerini okuyup davranışını ayarlar, başka klasörlere de çıkar (G0 §2) | `read_file` ve `write_file` için mutlak yollu `deny` kuralları (`.agents`, `.sdguard`, hook betikleri, `~/.gemini`); okuma için izin listesinde `cat`/`find` yok | Tur kayıtlarında bu yollara erişim denemesi sayılır |
| Ajan çalışma klasöründeki `.claude/` ayarlarını görüp davranışını değiştirir (G0 Deneme 2'de ajan işe `ls -la .claude` ile başladı) | Hook ayarları ajanın çalışma klasörüne değil, kullanıcı düzeyi ayara ya da `--settings` ile dışarıdan verilir | Tur başında çalışma klasöründe `.claude/` yok |
| İnsansız modda izin modu verilmezse ajan dosya değiştiremez (G0 Deneme 2 D1) | Tüm koşullarda aynı, açıkça belirtilmiş izin modu (ör. `--permission-mode acceptEdits`) ve sabit `--allowedTools` listesi | `permission_denials` alanı tur kaydında izlenir |

Yerel Windows'ta Claude Code komut sandbox'ı çalışmıyor; deney ve geliştirme WSL2 + Docker üstünde yapılır.

## 4. Tur kaydı şeması (`turns.jsonl`, satır başına bir tur)

Tanım koddadır: `sdguard/contracts/turns.py` (`TurnRecord`). JSON Schema: `sdguard/contracts/schema/turn.schema.json`. Örnek (geçerli bir K4 turu ve R19 yüzünden geçersiz bir Antigravity turu): `sdguard/tests/fixtures/contracts/turns-example.jsonl`. Analiz yalnızca bu satırları okur.

```json
{
  "run_id": "S1-K4-claude-code-r1", "scenario": "S1", "split": "dev", "condition": "K4",
  "agent": "claude-code", "agent_version": "2.1.0", "model": "<tam kimlik>", "account": "acct-a",
  "session_id": "…", "rep": 1, "turn": 1, "seed": 1234, "started_at": "…", "duration_s": 212.4,
  "tokens": {"input": 51200, "output": 4100, "cache_read": 30000}, "est_cost_usd": 0.42,
  "config_fingerprint": "<sha256>", "ruleset_sha256": "<sha256>",
  "valid": true, "invalid_reasons": [],
  "evaluation": {
    "functional": {"passed": 12, "total": 12},
    "exploits": [{"id": "sqli-login", "cwe": "CWE-89", "success": false}],
    "secure_and_correct": true,
    "sast": {"default_new": 1, "compiled_new": 0},
    "ledger": {"established": 4, "regressions": []},
    "packages_installed": ["flask-login==0.6.3"], "hallucinated_packages": [], "secrets_in_code": 0
  },
  "hook": {"calls": 23, "blocks": 1, "feedbacks": 2, "errors": 0, "p95_ms": 840.0},
  "permission_denials": 0
}
```

İlk taslağa göre değişenler ve şemanın zorladıkları:
1. Ölçüm alanları `evaluation` altında toplandı. Geçersiz turda (`valid: false`) ölçüm olmayabilir; geçerli turda zorunludur.
2. `valid` yalnızca `invalid_reasons` boşken `true` olabilir. Nedenler: `empty_response`, `auto_denied`, `fingerprint_mismatch`, `agent_version_changed`, `protected_file_changed`, `infra_error`. Antigravity'nin `status: SUCCESS` + exit 0'ı geçerlilik için kullanılmaz (R19).
3. `secure_and_correct` (birincil sonuç) hesaplanır ve kontrol edilir: bütün işlev testleri geçti ve hiçbir exploit başarılı olmadı.
4. `ruleset_sha256` K3 ve K4'te zorunlu, diğer koşullarda yok.
5. `account` takma ad etiketidir (`^[A-Za-z0-9_-]{1,32}$`); e-posta adresi bu kalıba uymaz. `session_id` hook loguyla birleştirmek için eklendi. `est_cost_usd` her ajan vermediği için isteğe bağlı.

Ham kayıtlar (stream-json, diff, hook logu, test çıktısı) `data/raw/<run_id>/turn-<n>/` altında; analiz için Parquet'e dönüştürülür.

## 5. BaxBench ile bağlantı

- Repo: `logic-star-ai/baxbench` (MIT). Python 3.12, root yetkili Docker, `pipenv`. Senaryolar `src/scenarios`, ortamlar `src/env` altında.
- Kendi ürettiğimiz kod `results/<model>/<scenario>/<env>/temp<t>-<spec>-<prompt>/sample<s>/code` yoluna konup `--mode test` ile çalıştırılabiliyor. Her turun kodu bu yola kopyalanarak test edilir.
- **Çok dosyalı uygulama (R11), 3–5 Kasım'da denendi:** `--mode test`, `code/` klasöründeki bütün metin dosyalarını alt klasörleriyle okuyup imaja kopyalıyor (`src/tasks.py` `load_code`); ortamdaki `is_multi_file` yalnızca istemi ve LLM cevabının ayrıştırılmasını etkiliyor. Login senaryosunda kendi yazdığımız iki uygulamayla:
  - **Python-Flask** (`app.py` + `auth/` paketi): 1/1 işlev testi geçti, 3 güvenlik testi hatasız koştu, CWE yok.
  - **JavaScript-express** (`app.js` + `lib/`): `_JS_DOCKERFILE`'daki `COPY * /app/` alt klasörleri düzleştirdiği için uygulama `Cannot find module './lib/store'` ile açılmadı; tablo bunu "exceptions" olarak gösteriyor. `COPY . /app/` yapınca 1/1 işlev, 3 güvenlik testi hatasız, CWE yok. Yama yerelde (`sd-env/baxbench-js-copy-subdirs.patch`); Express, Koa, Fastify aynı Dockerfile'ı kullanıyor.
  - Denenmedi: Go (aynı `COPY *` kalıbı), Rust (yalnızca `main.rs` kopyalanıyor).
  - Ayrıca bütün ortamlar `*-bullseye` imaj kullanıyor; Debian 11 desteği bittiği için `apt-get` 404 veriyor ve her örnek yine "exceptions" görünüyor. Yerel yama: `/etc/apt/sources.list` → `archive.debian.org`. İki yama da deney imajlarına girmeli; sonuç tablosu yerine derleme loglarına bakılmalı.
  - BaxBench, `test_results.json` olan örnekleri atlıyor; yeniden test için `--force`.
- Yeni turlar (dosya yükleme, yönetici paneli) için işlev testleri ve exploit'ler bizim tarafımızdan yazılır. `eth-sri/AutoBaxBuilder` (MIT, ICML 2026) senaryo/test/exploit üretebiliyor ama API anahtarı istiyor; yalnızca örnek ve fikir kaynağı olarak kullanılır.
- `djscherrer/IterBench` BaxBench'in yinelemeli bir çatalı ama güvenlik değil dağıtım optimizasyonu ölçüyor; kod yapısı örnek alınabilir.

## 6. Kota ve takvim planı

**Gerçek:** Pro planında `claude -p` normal abonelik kotasından düşüyor; ayrı kredi yok. Antigravity headless de hesabın normal hakkından düşüyor.

**Hesap:** `gün = tur sayısı / (r × w × h)`
- `r`: 5 saatlik pencerede tamamlanabilen ajan turu (pilotta ölçülecek)
- `w`: günde kullanılabilen pencere sayısı (gece koşumu ile 3–4)
- `h`: hesap sayısı (iki kişi, ikişer abonelik)

| Senaryo | r | w | h | Claude Code 450 tur | Not |
|---|---|---|---|---|---|
| İyimser | 15 | 3 | 2 | ~5 gün | Haftalık sınıra takılmazsa |
| Orta | 10 | 3 | 2 | ~8 gün | — |
| Kötümser | 5 | 2 | 2 | ~23 gün | Ağır turlar, haftalık sınır |

Haftalık sınır pencere hesabını bozabilir; pilotta bir hafta boyunca gerçek tüketim (`ccusage` ve `/usage`) kaydedilmeli. Kötümser senaryoda yol haritasındaki önlem geçerli: Antigravity tekrarını 2'den 1'e indir, gerekirse bir aylık ek abonelik.

**Sıralama:** (senaryo, tekrar) blokları; blok içinde koşul sırası rastgele; iki hesap blokları dönüşümlü alır. Hesap kimliği kayda girer ve analizde rastgele etki adayı.

## 7. Pilot (Kasım) kabul ölçütleri
1. 1 geliştirme senaryosu × 5 koşul × 1 tekrar × 2 ajan = 10 oturum, 50 tur uçtan uca koştu.
2. Her turda kayıt şemasının tüm alanları dolu, `valid` alanı doğru hesaplanıyor.
3. Aynı (senaryo, koşul, tohum) iki kez koşulduğunda değerlendirme hattı aynı kod için aynı sonucu veriyor (ajan çıktısı farklı olabilir, değerlendirme deterministik olmalı).
4. Gerçek `r` ölçüldü, takvim tablosu güncellendi.
5. Kirlenme testi: bilerek `~/.claude` içine eklenti koyup oturum başlatınca parmak izi kontrolü oturumu `INVALID` yaptı.

## 8. Ön kayıt (preregistration)
Araç dondurulmadan önce OSF'ye: hipotezler, birincil sonuç değişkeni (5. turda güvenli ve doğru), analiz modeli, dışlama kuralları (`INVALID` oturumlar, altyapı hataları), durdurma kuralı. `istatistik-danismani` taslağı hazırlar.

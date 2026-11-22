# Deney imajları

`02_DENEY_ALTYAPISI.md` §2–3'teki iki konteyner. Runner (D5) bunları başlatır; bu klasörde yalnızca tarifler var, imajların kendisi değil.

| Dosya | Ne |
|---|---|
| `agent-claude.Containerfile` | Claude Code ajanının oturum boyunca çalıştığı konteyner |
| `eval.Containerfile` | Her turun kodunun ağsız değerlendirildiği konteyner (işlev testleri, exploit'ler) |
| `flask-requirements.in` / `.txt` | BaxBench'in Python-Flask ortamı (`src/env/python.py`, `de885cd`). İki imajda aynı; `.txt` hash'li |
| `harness-requirements.in` / `.txt` | Değerlendiricilerin ortamı (`pydantic`), yalnızca değerlendirme imajında |
| `build.sh` | İki imajı kurar ve imaj kimliklerini yazar |

```bash
harness/docker/build.sh            # ikisi de; SD_CONTAINER_CLI=podman ile podman zorlanır
harness/docker/build.sh agent      # yalnızca sd-agent-claude:<sürüm>
```

Gereksinim dosyalarını yeniden üretmek için (`.in` değişince):
```bash
uv pip compile --generate-hashes --python-version 3.12 --python-platform x86_64-manylinux_2_28 \
  flask-requirements.in -o flask-requirements.txt
```

## Ne sabit, ne değil
- **Sabit:**
  - Python tabanı (`python:3.12-slim-trixie`, çoklu mimari digest'i).
  - Claude Code sürümü ve paketinin sha256'sı. sha256, npm kaydındaki sha512 bütünlük alanıyla karşılaştırılarak alındı.
  - pip paketleri: `--require-hashes` ile kuruluyor.
- **Sabit değil:**
  - `apt` paketleri (`git`, `curl` …), kurulduğu güne göre değişir.
  - `fpdf` 1.7.2 yalnızca kaynak paket olarak var; pip onu derlerken kullandığı yardımcı paketleri hash ile denetlemiyor.

  Bu yüzden runner her oturumda imaj kimliğini kaydeder ve kimlik `config_fingerprint`'e girer. Deney boyunca imaj bir kez kurulur ve G3'te dondurulur.
- **Claude Code 2.1.323**, npm'deki `stable` etiketi (22 Kasım). Host'taki sürüm (2.1.329) ve senaryo 1 denemesindeki sürüm (2.1.287) farklı. Sürüm değişikliği `DECISIONS.md` kaydı ister.
- **Yalnızca linux-x64.** İkimizin makinesi de x64; başka mimaride kurulum hata verir.

## Çalıştırma bayrakları (runner bunları kullanır)

**Ajan konteyneri** (oturum boyunca açık, her tur `exec` ile):
```bash
<cli> run -d --name sd-<run_id> --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 512 --memory 2g -v <çalışma klasörü>:/work sd-agent-claude:2.1.323
# rootless podman'da ayrıca: --userns=keep-id:uid=1000,gid=1000
```
- **Ağ açık:** PyPI ve API'ye çıkabiliyor; bütün koşullarda aynı. İzinli alan listesi Aralık'ta.
- **Rootless podman:** Bu bayrak olmadan `agent` kullanıcısı bağlanan klasöre yazamıyor. Bayrakla dosyalar host'ta geliştiricinin kullanıcısına ait görünüyor. Docker'da (rootful) gerekmiyor.

**Değerlendirme konteyneri** (her tur için yeni):
```bash
<cli> run --rm --network none --cap-drop ALL --read-only --security-opt no-new-privileges \
  --tmpfs /tmp:rw,size=256m,mode=1777 --pids-limit 128 --memory 512m \
  -v <turun kodu>:/src:ro sd-eval:latest /opt/harness/bin/python -I ...
```
- **Kodun yeri:** Turun kodu salt okunur bağlanır ve konteyner içinde `/tmp`'ye kopyalanıp oradan çalıştırılır. Uygulamanın `db.sqlite3`'ü ve `uploads/`'u `tmpfs`'e yazılır. Kopyalama yolu Docker'da da rootless podman'da da kullanıcı kimliği sorunu çıkarmıyor.
- **Ortamlar:** Uygulama sistem Python'uyla, yalnızca BaxBench paketleriyle çalışır. Değerlendiriciler `/opt/harness` venv'inden çalışır; uygulama `pydantic`'i, değerlendiriciler Flask'ı görmez.
- **Sertleştirme:** Bayraklar ilk set. E6 (Ege) kapsamında saldırgan gözüyle sınanacak.

## Giriş bilgisi
İmaja ve repoya hiçbir giriş bilgisi girmez. Runner token'ı çalışırken verir:
- **Token:** `claude setup-token` ile alınan uzun ömürlü token, konteynerde `CLAUDE_CODE_OAUTH_TOKEN` olarak.
- **podman:** Token bir kez podman secret olarak kaydedilir ve konteynere `--secret sd-claude-oauth,type=env,target=CLAUDE_CODE_OAUTH_TOKEN` ile verilir:
  ```bash
  read -rs TOK            # token'ı yapıştır, Enter (ekranda görünmez, geçmişe girmez)
  printf %s "$TOK" | podman secret create sd-claude-oauth - && unset TOK
  ```
  - Token'ı komuta argüman olarak yazmayın: podman onu dosya yolu sanar ve token kabuk geçmişine girer.
  - `-` ile yapıştırıp Enter'a basarsanız sondaki satır sonu da token'a eklenir ve giriş bozulur.
  - podman'ın dosya sürücüsü token'ı kendi deposunda base64 olarak saklar. agy'nin giriş volume'u (`sd-agy-state`) ile aynı düzey.
- **Docker:** Kabuk ortamından değersiz `-e CLAUDE_CODE_OAUTH_TOKEN` ile geçirilir; değer komut satırında görünmez.
- **Uyarı:**
  - `claude setup-token` token'ı ekrana yazar; Claude Code oturumunda `!` ile çalıştırılmaz, çünkü çıktısı sohbet kaydına girer.
  - Token ajanın süreç ortamında durduğu için ajanın komutları onu görebilir (`env`, `os.environ`). Runner her turun kayıtlarında ve commit'inde token'ı birebir arayıp diske yazmadan önce maskeler. Runner'ın izin listesine `env` ve `export` konmaz (V8c).

## Doğrulama (22 Kasım, Deniz'in makinesi, rootless podman, her biri n = 1)

| # | Ne | Sonuç |
|---|---|---|
| V1 | İki imaj podman ile kuruluyor | ✅ ajan 610 MB, değerlendirme 165 MB |
| V2 | Sürümler ve kullanıcı | ✅ Claude Code 2.1.323, Python 3.12.16; ajan `uid 1000`, `HOME` boş; değerlendirme `nobody` |
| V3 | Giriş yokken `claude -p` | ✅ `system/init` olayı yine geliyor, sonra `Not logged in`. Runner parmak izini **kota harcamadan, oturumdan önce** kontrol edebilir |
| V3a | Temiz `HOME`'da `init` | Ayrıntı aşağıda |
| V4 | Otomatik hafıza kapatma | ✅ `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` de `--settings '{"autoMemoryEnabled": false}'` de `memory_paths`'i `null` yapıyor. İmajda ortam değişkeni var |
| V5 | Değerlendirme konteyneri sertleştirme | ✅ Yalnızca `lo` arayüzü, dışarı bağlantı yok, kök dosya sistemi salt okunur, `CapEff` 0, `NoNewPrivs` 1 |
| V6 | Gerçek ajan kodu bu bayraklarla | ✅ Senaryo 1 denemesinin 5. tur kodu: kayıt 201, giriş 200, kart 201/200, PDF yükleme 201, yönetici 200 |
| V7 | Ajan konteyneri ve `/work` | ✅ `--cap-drop ALL` ile `git` ve Python çalışıyor, PyPI'ye çıkıyor. Rootless podman'da `--userns=keep-id:uid=1000,gid=1000` gerekli |
| V8 | Token ile giriş | ✅ podman secret ile verilen `setup-token` token'ıyla `claude -p` Haiku'da cevap verdi. Token, akış çıktısında ve stderr'de 0 kez geçiyor |
| V8a | claude.ai bağlayıcıları | ✅ `mcp_servers: []`. Host'taki girişte görünen claude.ai MCP bağlayıcısı bu token'la gelmiyor |
| V8b | `--settings` içindeki `allow`, güven onayı olmayan klasörde | ✅ Geçerli. `Bash(python3:*)` varken `python3 -c` çalıştı, yokken "This command requires approval" ile reddedildi. Güven uyarısı yok. Deneme 5'te (E2) açık kalan soru |
| V8c | `acceptEdits` modunun kendiliğinden onayladıkları | ⚠️ `rm -f <dosya>` çalışma klasöründe izin listesine bakılmadan çalıştı (iki çağrıda da). `printenv` ve `env` onay istedi ve reddedildi. `/proc/self/environ` okumayı Claude Code kendisi engelledi ("may expose secrets") |
| V9 | Docker'da kurulum ve çalıştırma | Bekliyor (Ege, WSL2 + Docker) |

**V3a: temiz `HOME`'da `init` olayı** (giriş yokken):
- **Eklentiler:** 4 tane, hepsi yerleşik (`path: builtin`): `cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-privacy`, `cc-plugin-plugin-authoring`. Kullanıcı eklentisi değiller, CLI ile geliyorlar; beklenen parmak izine girerler. `agents-md` K1'de AGENTS.md'nin nasıl yüklendiğini etkileyebilir, K1 klasörü yazılırken bakılacak.
- **Skill ve komutlar:**
  - 18 yerleşik skill (ör. `code-review`, `debug`, `verify`) ve 48 slash komutu (`security-review` dahil).
  - Bütün koşullarda aynılar, gerçek kullanıcı ortamı da böyle; olduğu gibi bırakılıyor.
  - `--disable-slash-commands` ile kapatılabilir. Kapatılırsa bütün koşullarda kapatılmalı (`DECISIONS.md`).
- **MCP sunucusu yok.** claude.ai bağlayıcıları girişe bağlı olabilir (V8).
- **Varsayılan değerler:** Model `claude-opus-5-5`, izin modu `default`. Runner ikisini de açıkça verecek.
- **Araçlar:** 23 tane, `WebFetch` ve `WebSearch` dahil. Koşulun izin listesi bunları sınırlar.

**Girişle `init` değişiyor** (V3a ile V8 karşılaştırması):
- Eklenenler:
  - 2 araç: `PushNotification`, `RemoteTrigger`,
  - 1 skill: `schedule`,
  - 5 slash komutu: `advisor`, `import`, `schedule`, `skill-doctor`, `ultrareview`.
- Eklentiler, MCP ve hafıza aynı kalıyor.
- Runner için anlamı: Girişsiz ön kontrol ile oturum içindeki `init` aynı parmak izini vermez. Parmak izi iki kısma ayrılır:
  - **Kirlenme alanları** (eklentiler, MCP sunucuları, `memory_paths`): Beklenenden farklıysa tur `fingerprint_mismatch` olur. Ön kontrolde de oturum içinde de aynıdır.
  - **Ortam alanları** (araç, skill ve komut listeleri): Kaydedilir ve koşullar arasında karşılaştırılır. Hesap tarafındaki özellik açılışları bunları değiştirebilir; değişirse model güncellemesi gibi kovaryat olur.

**Runner'ın duman testi ve izin listesi için sonuçlar** (V8b, V8c):
- "Reddedilmesi gereken" komut olarak `rm` kullanılamaz, çünkü `acceptEdits` modunda kendiliğinden onaylanıyor. İzin listesinde olmayan ve kendiliğinden onaylanmayan bir komut gerekir: `python3` bu klasörde izinsiz reddedildi. Seçilen komut runner PR'ında sınanacak.
- İzin listesi tek kapı değil: `acceptEdits` bazı dosya komutlarını kendiliğinden onaylıyor. Bu bütün koşullarda aynı, karşılaştırmayı bozmaz; ama K0'daki "izin listesi" bir güvenlik sınırı sayılmamalı.
- Token ajanın ortamında duruyor. `env`, `printenv` ve `/proc/*/environ` engelleniyor, ama izinli `python3` ile `os.environ` okunabilir; ajanın yazdığı uygulama da ortamı devralır. Maskeleme bu yüzden asıl güvence.

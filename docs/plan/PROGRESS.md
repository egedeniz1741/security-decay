# İlerleme

## Durum özeti
- **Faz:** G0 geçildi (11 Kasım); ürün kodu başladı
- **Aktif kapı:** G1 · Pilot · 29 Kasım 2026
- **Sonraki teslim noktası:** Senaryo 1 için derlenmiş kural paketi (Ege → Deniz) · 22 Kasım. **Gecikti.**
- **Takvim durumu: G1'in yazılı ölçütü 29 Kasım'a yetişmiyor.**
  - **Yetişebilecekler:** Claude Code ile S1'de K0 (yetişirse K1) oturumları, pilot ölçütleri 2, 3 ve 5, gerçek `r`.
  - **Yetişmeyecekler:** K4, çünkü motor ve Claude Code adaptörü (D3, D4) başlamadı. "3 kural türü + 1 invariant" dikey dilimi. İki ajanlı 10 oturum.
  - **Karar gerekli:** G1'i daraltmak ya da yaklaşık 13 Aralık'a ertelemek (aşağıda 1. madde).

## Kullanıcı kararı bekliyor
1. **G1:** Kapsamı "Claude Code, S1, K0 (+K1)" olarak daraltmak mı, yaklaşık 13 Aralık'a ertelemek mi? Karar `DECISIONS.md`'ye; G1 toplantısında ikiniz.
2. **Pilot modeli** (`--model`): Runner'ın varsayılanı `claude-sonnet-5-5` (senaryo 1 denemelerindeki model).
3. **Yerleşik skill ve komutlar:** Temiz `HOME`'da da 18 skill ve 48 komut var (`security-review` dahil). Öneri: olduğu gibi bırakmak; kapatılırsa bütün koşullarda (`harness/docker/README.md`, V3a).
4. **İmajın paylaşılması:** Ajan imajı bir kez kurulup iki makineye `save`/`load` ile dağıtılsın; yoksa `config_fingerprint` makineye göre değişir.
5. **K1 kural metni:** Senaryo 1'in yazılı güvenlik kurallarını kim yazacak? K1 ve K3/K4 aynı metinden çıkar.
6. K1b ve K2b koşulları (ADR-0004, ADR-0005) — G1 öncesi.
7. Ölçülecek zafiyetler (ADR-0016) ve veri düzeni (ADR-0017): `ZAFIYET_KATALOGU.md` §8, `VERI_PLANI.md` §9.

## Sıradaki 3 iş

**Ege**
1. 3. tur (ekstreler) exploit'leri: başkasının ekstresi (CWE-639), dosya yolu (CWE-22), PDF olmayan yükleme (CWE-434). Kontrol sınamasını `sd-eval` imajına taşımak.
2. Senaryo 1 için K1 kural metni ve derlenmiş K3/K4 kural paketi (22 Kasım'dı, **gecikti**).
3. E6 kirlenme testi (runner'ın ön kontrolüne karşı) ve Docker'da imaj denemesi (#23, V9).
~~#19 inceleme maddeleri, 2. turdan itibaren token, 2. ve 4. tur exploit'leri~~ · ~~İncelemeler #20–#24, #26~~ · ~~Claude Code izin satırı denemesi (#18)~~ · ~~Kural formatı, derleyici dilimi~~ · ~~G0~~

**Deniz**
1. G1 pilot oturumları (S1, K0) ve kota ölçümü: `rate_limit_event`'teki 5 saatlik ve 7 günlük kullanım oranlarından gerçek `r`.
2. K1 koşul klasörü (kural metni Ege ile) ve yerleşik `agents-md` eklentisinin AGENTS.md'yi nasıl yüklediği.
3. Motor ve `auth` invariant'ı, Claude Code adaptörü (D3, D4): K4 bunlara bağlı.
~~Sözleşme v0.3 (#22)~~ · ~~Deney imajları (#23)~~ · ~~Runner: oturum (#24), değerlendirme (#25, taslak)~~ · ~~Senaryo 1 istemleri (#21)~~ · ~~Olay/karar ve tur kaydı sözleşmesi (#13)~~

## Oturum günlüğü

### 2026-11-25 oturumu (Ege)
- Deniz'in PR'ları incelendi ve birleşti: #20 (senaryo kararı), #21 (senaryo 1 istemleri), #22 (sözleşme v0.3), #23 (deney imajları), #24 (runner, oturum), #26 (bu dosya). #25 taslak, #19'a bağlı.
- #19 Deniz'in incelemesine göre düzeltildi:
  - Sandbox kontrolü `lo` dışında arayüz varsa reddediyor (`--internal` ağ artık geçmiyor).
  - `Target` yalnızca loopback kabul ediyor, proxy'yi yok sayıyor; `attempt()` sandbox kontrolünü kendisi çalıştırıyor; bozuk HTTP cevabı `inconclusive`.
  - Exploit'ler `/register` varsa kendileri hesap açıp giriş yapıyor. 2–5. turlarda birincil sonucun sistematik `null` çıkması bununla düzeliyor (Deniz'in gerçek oturumunda yeniden denenecek).
  - Yeni exploit'ler: 2. tur CWE-306, CWE-639, CWE-347; 4. tur CWE-862, CWE-269. Hepsi birincil.
  - Kontrol sınaması (`unshare -n`, her hücre 10 tekrar): 1. tur 12/12, 2. tur 42/42, 4. tur 72/72 hücre tutarlı ve beklenen sonuçta.
- G1 kararı (daraltma ya da erteleme) Ege'de; G1 toplantısında kesinleşecek.

### 2026-11-22/23 oturumu (Deniz)
Yapılanlar:
- **Sözleşme v0.3 (#22):**
  - `inconclusive_exploits` ve üç değerli `secure_and_correct`: işlev testi kaldıysa ya da birincil exploit başarılıysa `false`, birincil exploit ölçülemediyse `null`.
  - Kurulmamış ölçümler (`sast`, `ledger`, `hallucinated_packages`) `null`.
- **Deney imajları (#23):**
  - Claude Code 2.1.323 sürüm ve sha256 ile, Python 3.12 digest ile, BaxBench paketleri hash ile sabit. `HOME` boş, giriş bilgisi imajda yok.
  - Değerlendirme imajı ağsız, yetkisiz ve salt okunur çalışıyor.
  - Giriş: `claude setup-token`, podman secret ile.
- **Runner, oturum kısmı (#24):**
  - Kota harcamayan ön kontrol (girişsiz `init` ile kirlenme alanları), duman testi (R24).
  - 5 tur `--resume`, token maskeleme, bütünlük kontrolü, `/work` dışında git klasörü, `facts.json`.
- **Runner, değerlendirme (#25, taslak, #19/#22/#24'e bağlı):**
  - Tur tur işlev testleri, ağsız konteynerde exploit'ler, Gitleaks.
  - `turns.jsonl`, `evaluate` ve `compare` komutları.
- **Gerçek S1 K0 oturumu** (Sonnet, n = 1; runner sınaması, ölçüm değil):
  - 5 tur geçerli, işlev testleri tam puan.
  - 1. tur `secure_and_correct = true`; 2–5. turlar `null` (exploit'ler 401 alıyor).
  - İki değerlendirme aynı (pilot ölçütü 3, n = 1).

Önemli bulgular (her biri n = 1):
1. **`claude -p` kapanmıyor.** Ajanın arka planda başlattığı uygulama çalıştığı sürece cevaptan sonra da açık kalıyor. Runner turu `result`'tan 15 s sonra bitiriyor.
2. **Claude Code giriş yokken de `system/init` yazıyor.** Kirlenme kontrolü kota harcamadan yapılabiliyor. Girişle birlikte 2 araç (`RemoteTrigger`, `PushNotification`) ve birkaç komut ekleniyor; parmak izi bu yüzden kirlenme ve ortam diye ikiye ayrıldı.
3. **`acceptEdits` modu ve izinler:** `rm`'yi izin listesine bakmadan onaylıyor. `env` ve `printenv` reddediliyor, `/proc/*/environ` okumayı Claude Code kendisi engelliyor. `--settings` içindeki `allow` güven onayı olmayan klasörde de geçerli (deneme 5'te E2'de açık kalan soru).
4. **Bütünlük listesi daraltıldı.** Claude Code `~/.claude` altına her turda kendisi yazdığı için 02 §4'teki `~/.claude/**` bütünlük için kullanılamıyordu; artık yalnızca ayar ve talimat dosyalarına bakılıyor.
5. **Kota verisi:** Akıştaki `rate_limit_event` 5 saatlik ve 7 günlük kota kullanımını veriyor; pilotta `r` için kullanılacak.
6. **Kota tüketimi:** Bir S1 oturumu yaklaşık 4,5 dakika sürdü, `total_cost_usd` toplamı yaklaşık $1,7 değerinde.

Değişen plan dosyaları: `02_DENEY_ALTYAPISI.md` §3, §4 (madde 8–9, bütünlük listesi), §8; `04_TEST_VE_DOGRULAMA.md` §4; `DECISIONS.md` (ADR-0018); bu dosya.
Bağımsız denetim bulguları: yok. `plan-denetcisi` ve `guvenlik-denetcisi` bu oturumda çalıştırılmadı; G1 öncesi gerekli.
Kullanıcı kararı bekleyenler: yukarıdaki liste, özellikle G1.
Yaklaşan son tarihler: G1 29 Kasım (6 gün). Ege'nin K3/K4 kural paketi 22 Kasım'dı, gelmedi. Mutant seti v1 20 Aralık.

### 2026-11-18 – 20 oturumları (Ege)
- #14, #15, #18 Deniz'in incelemesiyle birleşti; #16 ve #17 (Deniz) incelendi, birleşti. Senaryo ayrımı tohum 20261116 ile çekildi: geliştirme CreditCardService ve Wiki, senaryo 1 CreditCardService.
- Claude Code izin denemesi (#18): `Read` yasağı `cat`'i kapsıyor ama `grep -r`'yi kapsamıyor; alt klasörden başlatılınca proje ayarı yüklenmiyor; insansız modda hatalı satır sessiz. Deneyde izinler `--settings` ile verilecek.
- Exploit altyapısı (#19): dört sonuçlu exploit tanımı, ağ varsa çalışmayı reddeden kontrol, 10 tekrarlı kontrol sınaması; CreditCardService 1. tur için 3 exploit ve 4 kontrol uygulaması. Ağsız ad alanında (`unshare -n`) 12/12 hücre 10/10 tutarlı.

### 2026-11-12 – 15 oturumları (Ege)
- #8, #10, #11 Deniz'in incelemesine göre düzeltildi ve birleşti; #12 ve #13 (Deniz) incelendi, birleşti.
- Zafiyet kataloğu ve veri planı önerisi (PR #14, ADR-0016/0017 açık).
- pytest doğrulaması (PR #15): davranış testi güvenli uygulamada geçmeli, güvensizde assertion ile kalmalı; çökme tespit sayılmaz. Derleyicinin üç katmanının doğrulaması tamam; LLM ile derleme adımı henüz yok.

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
Kullanıcı kararı bekleyenler: K1b/K2b, kapsam kararları, Deniz'in GitHub kullanıcı adı.

### 2026-10-24 oturumu
Yapılanlar: Yol haritası v2 incelendi; Claude Code subagent/hook/skill/headless belgeleri, Antigravity CLI hook ve headless belgeleri, kota politikası, Semgrep/Trail of Bits/arXiv/Zotero araçları, BaxBench ve yakın çalışmalar araştırıldı. Plan dosyaları (00–07), karar kaydı, 10 planlayıcı ajan ve orkestra şefi skill'i oluşturuldu.
Önemli bulgular: Anthropic `security-guidance` eklentisi projeye özel kural destekliyor (özgünlük iddiası daraltılmalı); Pro'da `claude -p` normal kotadan düşüyor; `--bare` abonelikle çalışmıyor; Claude Code hook'ları varsayılan fail-open; Antigravity `PostToolUse` ajana geri bildirim veremiyor.

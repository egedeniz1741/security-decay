# 07 · Ajan ekibi

> Ajan dosyaları: `.claude/agents/*.md` · Orkestra şefi: `.claude/skills/sd-sef-muhendis/SKILL.md`
> Claude Code'da kullanım: "`deney-tasarimcisi` ajanını kullanarak K1b koşulunu tasarla" ya da `@agent-deney-tasarimcisi ...`. Oturumun tamamını bir ajanla açmak için `claude --agent plan-denetcisi`.

## 1. Faz 1 · Planlayıcılar (şimdi)

| Ajan | Model | Yazma alanı | Ürettiği belge | Ritim |
|---|---|---|---|---|
| `literatur-gozcusu` | sonnet | `docs/` | `LITERATUR.md` | Haftalık (çarşamba) |
| `sistem-mimari` | opus | `docs/` | `01_MIMARI.md`, `docs/adr/*` | İhtiyaç olunca |
| `hook-entegrasyon-analisti` | sonnet | `docs/`, `spikes/` | `AJAN_ENTEGRASYON.md`, hook fixture'ları | G0 ve sürüm yükseltmelerinde |
| `deney-tasarimcisi` | opus | `docs/`, `harness/prompts/README.md` | `02_DENEY_ALTYAPISI.md`, `ON_KAYIT.md` | G1 ve G3 öncesi |
| `istatistik-danismani` | opus | `docs/`, `analysis/power/` | `ANALIZ_PLANI.md`, güç simülasyonu | G3 öncesi |
| `veri-planlayici` | sonnet | `docs/` | `VERI_PLANI.md`, `ETIKET_KILAVUZU.md` | Aralık başı |
| `kaynak-planlayici` | sonnet | `docs/` | `KOTA_PLANI.md` | Pilot sonrası ve aylık |
| `guvenlik-denetcisi` | opus | `docs/` | `TEHDIT_MODELI.md`, `docs/reviews/guvenlik-*` | Her kapı öncesi |
| `plan-denetcisi` | opus | `docs/reviews/` | `plan-denetimi-*` | Haftalık (cuma) + kapı öncesi |
| `yayin-planlayici` | sonnet | `docs/` | `YAYIN_PLANI.md` | Şubat'tan itibaren aylık |

**Neden bu ayrım?** Her ajan bir plan dosyasının sahibi; iki ajan aynı dosyaya yazmaz. Yazan ve denetleyen ayrı: `plan-denetcisi` ve `guvenlik-denetcisi` hiçbir belgeyi kendileri yazmaz, yalnızca rapor üretir.

**Kota notu:** Opus ajanları daha pahalı. Haftalık rutinde yalnızca `literatur-gozcusu` (sonnet) ve `plan-denetcisi` (opus) çalışır; diğerleri iş çıktıkça.

## 2. Faz 2 · Geliştiriciler (G0 sonrası oluşturulacak, şimdilik yalnızca tanım)

| Ajan | İş paketi | Not |
|---|---|---|
| `derleyici-gelistirici` | WP3 | Trail of Bits `semgrep-rule-creator` skill'ini ön yükler |
| `defter-gelistirici` | WP4 | `libcst`, özellik testleri |
| `adaptor-gelistirici` | WP5 | Yalnızca `AJAN_ENTEGRASYON.md`'de "doğrulandı" olan davranışlara dayanır |
| `harness-gelistirici` | WP6 | Docker, runner, parmak izi |
| `exploit-yazari` | WP6 | Pozitif/negatif kontrol uygulamalarıyla; test senaryolarını görmeyen ajanlardan ayrı |
| `analiz-gelistirici` | WP10 | R betikleri |
| `ci-gelistirici` | WP11 | GitHub Action, SARIF |
| `panel-gelistirici` | WP12 | Teknoloji ADR-0006'ya bağlı |
| `bagimsiz-degerlendirici` | WP4, WP9 | Aracın doğruluğunu yalnızca o raporlar; aracı yazanlar raporlamaz |

## 3. Tipik akış örnekleri

**G0 haftası (2–8 Kasım):**
1. `hook-entegrasyon-analisti` → iki ajanda spike, `AJAN_ENTEGRASYON.md`.
2. `sistem-mimari` → adaptör tablosunu doğrulanmış matrise göre güncelle, ADR.
3. `guvenlik-denetcisi` → adaptör tasarımında fail-open ve atlatma incelemesi.
4. `plan-denetcisi` → G0 belgelerini denetle.
5. Kullanıcı: G0 kararı.

**Pilot haftası (23–29 Kasım):**
1. `kaynak-planlayici` → B'nin pilot verisinden kota ölçümü ve takvim.
2. `plan-denetcisi` → G1 ölçütleri tek tek.
3. Ege + B: G1 kararı ve iş yükü yeniden dengeleme (`08_IS_BOLUMU_VE_KOORDINASYON.md` §6).

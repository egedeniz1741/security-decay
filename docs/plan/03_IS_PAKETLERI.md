# 03 · İş paketleri, kapılar ve takvim

> Durum: taslak v0.2 (29 Ekim: TÜBİTAK çıkarıldı, iş bölümü işlendi) · Sahibi: `sd-sef-muhendis` skill'i · **Ege**: DevSecOps ve güvenlik · **B**: uygulama ve araştırma altyapısı · Ayrıntılı iş bölümü: `08_IS_BOLUMU_VE_KOORDINASYON.md`

## 1. Kapılar (git / gitme noktaları)

Bir kapıdan geçilmeden sonraki fazın riskli işine başlanmaz. Kapıyı geçmeme kararı da bir sonuçtur, `DECISIONS.md`'ye yazılır.

| Kapı | Tarih | Geçme ölçütü | Geçemezse |
|---|---|---|---|
| **G0** Hook spike | 8 Kas 2026 | Her iki ajanda: araç çağrısını engelleme, tur sonunda ajana geri bildirim verip devam ettirme, headless'ta hook'ların tetiklenmesi, `onFailure` davranışı gerçek koşumla gösterildi | Antigravity yerine Codex CLI ya da Copilot CLI ile aynı test (1 hafta) |
| **G1** Pilot | 29 Kas 2026 | `02_DENEY_ALTYAPISI.md` §7'deki 5 ölçüt; dikey dilim (3 kural türü + 1 invariant) uçtan uca çalışıyor | Kapsam daraltma: senaryo 6→4 ya da tur 5→4 |
| **G2** Araç v1 | 17 Oca 2027 | Geliştirme senaryolarında mutant setinde duyarlılık ve kesinlik ≥ %80; derleyici korpusun geliştirme dilimini işliyor; tur başına ek süre ölçülmüş | Defter kapsamını en güçlü 3 invariant'a indir, kalanlar gelecek çalışma |
| **G3** Araç dondurma | 31 Oca 2027 | `v0.9-deney` etiketi; ön kayıt OSF'de; test senaryoları ve exploit'ler kilitli | Dondurma en fazla 1 hafta kayar, deney süresinden düşülür |
| **G4** Veri kilidi | 15 Mar 2027 | Ana deneyin geçerli oturum oranı ≥ %90, eksik hücreler raporlu | Eksik hücreler "eğilim" olarak raporlanır, ön baskı RQ1 + RQ3 + kısmi RQ2 ile çıkar |
| **G5** Ön baskı | 31 Mar 2027 | arXiv'e gönderildi | Nisan ortası; tez takvimi etkilenmez |
| **G6** v1.0 | 30 Nis 2027 | PyPI + GitHub Action yayında, iki ajan belgelenmiş | v1.0 yalnızca Claude Code ile çıkar |

**Gerçekçilik notu:** Yol haritası ana deneyi Şubat–Mart'a, ön baskıyı Mart sonuna koyuyor. Deney 15 Mart'ta bitse bile analiz ve yazım için 2 hafta kalıyor. Ön baskının ilk sürümü için yazım Şubat'ta, deney koşarken başlamalı (giriş, ilgili çalışmalar, yöntem, RQ1 ve RQ3 sonuçları önceden hazır olur).

## 2. İş paketleri

| WP | Ad | Çıktı | Sahip | Bağımlı | Dönem | Kabul ölçütü |
|---|---|---|---|---|---|---|
| WP0 | Yönetim | Plan, haftalık durum, kapı kararları | Ege+B | — | 26 Eki → | Her pazartesi `PROGRESS.md` güncel |
| WP1 | Ortam ve iskelet | WSL2 + Docker + uv; repo iskeleti; CI (ruff, mypy, pytest, Gitleaks); pre-commit; dal koruma | Ege | — | 26 Eki – 1 Kas | Temiz klonda `uv run pytest` yeşil |
| WP2 | Ajan entegrasyonu spike'ı | Her iki ajan için hook yetenek matrisi, çalışan minimal hook örnekleri | Ege (Claude Code), B (Antigravity) | WP1 | 2 – 8 Kas | **G0** |
| WP3 | Derleyici | `sdguard compile`, IR şeması, 3 katman çevirici, doğrulayıcı, onarım döngüsü | Ege | WP2 | Kas (dilim) → Oca | Geliştirme diliminde doğrulanmış kural oranı; kesinliği B ölçer |
| WP4 | Çekirdek motor + invariant defteri | Olay/karar şeması, çıkarıcı (5 invariant ailesi), high-water mark defteri, diff, bulgu mesajı biçimi | B | WP2 | Kas (dilim) → Oca | Ege'nin mutant setinde ≥ %80 |
| WP5 | Adaptörler | Claude Code ve Antigravity adaptörleri, sözleşme testleri | B | WP2, WP3, WP4 | Kas – Oca | Kayıtlı gerçek hook girdileriyle altın testler geçiyor |
| WP6 | Deney düzeneği | Runner, konteyner imajları, koşul klasörleri, senaryo/tur istemleri (B); exploit'ler ve izolasyon sertleştirme (Ege) | B + Ege | WP1, WP2 | Kas → Oca | **G1**, exploit'ler G3'te kilitli |
| WP7 | Korpus B (RQ1) | GitHub'dan ~1.000 CLAUDE.md / AGENTS.md (Ege toplar), 150 kural çift etiket (ikisi bağımsız), κ (B) | Ege + B | WP3 sınıflandırıcı | Ara – Oca | Cohen's κ raporlu; RQ1 sonucu Ocak sonu |
| WP8 | Mutant seti C (RQ3) | `libcst` tabanlı mutasyon operatörleri, ~200 mutant + temiz değişiklikler | Ege | WP4 çıkarıcı arayüzü | Ara | 20 Ara B'ye teslim; etiketler otomatik, %10'u elle kontrol |
| WP9 | Ana deney | 150 oturum (+ isteğe bağlı K1b/K2b); bloklar ikiye bölünür | Ege + B | G3 | Şub – 15 Mar | **G4** |
| WP10 | Analiz | R betikleri: karma lojistik, Kaplan–Meier / Cox, güç simülasyonu, grafikler | B | WP9 | Ara (simülasyon) → Mar | Ön kayıttaki tüm analizler tek komutla üretiliyor |
| WP11 | CI Action + v1.0 | `sdguard check --sarif`, kompozit GitHub Action, örnek repo, PyPI sürümü | Ege | WP3 | Şub – Nis | Örnek PR'da kırmızı/yeşil demo |
| WP12 | Panel | Oturum zaman çizelgesi raporu | B | WP9 kayıt şeması | Mar – Nis | Demo oturumu görselleştiriliyor |
| WP13 | Yazım ve savunma | Ön baskı, tez, demo videosu, sunum; herkes kendi bileşeninin bölümünü yazar | Ege + B | hepsi | Şub → Haz | **G5**, savunma |

## 3. Haftalık takvim

Hafta hafta kimin ne yapacağı ve teslim noktaları `08_IS_BOLUMU_VE_KOORDINASYON.md` §3–4'te. Özet:

| Dönem | Ege | B | Kapı |
|---|---|---|---|
| 26 Eki – 1 Kas | Kurulum, repo iskeleti, CI | Kurulum, BaxBench, çok dosya kontrolü | — |
| 2 – 8 Kas | Claude Code hook spike'ı | Antigravity hook spike'ı | **G0** (8 Kas) |
| 9 – 15 Kas | IR şeması, derleyici dilimi, senaryo 1 exploit'leri | Olay/karar şeması, motor + runner iskeleti, senaryo 1 tur istemleri | Sözleşmeler 11 Kas |
| 16 – 22 Kas | Kural doğrulama, izin katmanı, izolasyon sertleştirme | `auth` invariant'ı, Claude Code adaptörü, ölçüm hattı | — |
| 23 – 29 Kas | K2–K4 koşulları, pilot yarısı | K0–K1 koşulları, pilot yarısı, kota ölçümü | **G1** (29 Kas) |
| Aralık | Derleyici v1, korpus toplama, mutant seti | Defter v1, Antigravity adaptörü, kalan tur istemleri, güç simülasyonu | — |
| Ocak (%50) | Test exploit'leri, etiketleme, defteri ölçme | Ön kayıt, etiketleme, κ, derleyiciyi ölçme | **G2** 17 Oca, **G3** 31 Oca |
| Şubat – Mart | Koşum yarısı, CI Action, ön baskı | Koşum yarısı, veri hattı, analiz | **G4** 15 Mar, **G5** 31 Mar |
| Nisan | v1.0 sürümü | Panel | **G6** 30 Nis |
| Mayıs – Haziran | Tez, demo | Tez, demo | Savunma |

## 4. Kritik yol
WP2 (G0) → WP3/WP4 dikey dilim → WP6 pilot (G1) → WP3/WP4 v1 (G2) → dondurma (G3) → WP9 (G4) → WP10 → WP13 (G5).

En fazla bolluk WP11 ve WP12'de; zaman kaybında ilk kesilecekler bunlar (v1.0'ın kapsamı daralır, araştırma etkilenmez).

## 5. Haftalık ritim
Toplantı ve GitHub düzeni `08_IS_BOLUMU_VE_KOORDINASYON.md` §5'te. Ajan rutini:
- Pazartesi: `PROGRESS.md` güncellenir, her kişi için sıradaki 3 iş seçilir (`sd-sef-muhendis`).
- Çarşamba: `literatur-gozcusu` taraması (haftalar dönüşümlü: Ege / B).
- Cuma: `plan-denetcisi` o hafta değişen plan dosyalarını bağımsız okur; tutarsızlık listesi.
- Her kapı öncesi: `guvenlik-denetcisi` + `plan-denetcisi` birlikte.

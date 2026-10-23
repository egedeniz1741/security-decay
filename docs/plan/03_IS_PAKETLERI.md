# 03 · İş paketleri, kapılar ve takvim

> Durum: taslak v0.1 · Sahibi: `sd-sef-muhendis` skill'i · Kişi A: derleyici, hook'lar, CI · Kişi B: deney düzeneği, istatistik, panel (yol haritasındaki iş bölümü)

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
| WP0 | Yönetim + TÜBİTAK | Plan, haftalık durum, 2209-A başvurusu | A+B | — | 26 Eki → | Başvuru yapılacaksa 11 Kas 17:30'dan önce danışman onaylı gönderim |
| WP1 | Ortam ve iskelet | WSL2 + Docker + uv; repo iskeleti; CI (ruff, mypy, pytest, Gitleaks); pre-commit | A | — | 26 Eki – 8 Kas | Temiz klonda `uv run pytest` yeşil |
| WP2 | Ajan entegrasyonu spike'ı | Her iki ajan için hook yetenek matrisi, çalışan minimal hook örnekleri | A | WP1 | 26 Eki – 8 Kas | **G0** |
| WP3 | Derleyici | `sdguard compile`, IR şeması, 3 katman çevirici, doğrulayıcı, onarım döngüsü | A | WP2 | Kas (dilim) → Oca | Geliştirme diliminde doğrulanmış kural oranı ve kesinlik raporu |
| WP4 | Invariant defteri | Çıkarıcı (5 invariant ailesi), high-water mark defteri, diff, bulgu mesajı biçimi | A (B destek) | WP2 | Kas (dilim) → Oca | Mutant seti C geliştirme diliminde ≥ %80 |
| WP5 | Adaptörler | Claude Code ve Antigravity adaptörleri, sözleşme testleri | A | WP2, WP3, WP4 | Ara – Oca | Kayıtlı gerçek hook girdileriyle "altın" testler geçiyor |
| WP6 | Deney düzeneği | Runner, konteyner imajları, koşul klasörleri, 6 senaryo × 5 tur istemi, yeni tur exploit'leri | B | WP1, WP2 | Kas → Oca | **G1**, exploit'ler G3'te kilitli |
| WP7 | Korpus B (RQ1) | GitHub'dan ~1.000 CLAUDE.md / AGENTS.md, güvenlik kuralı çıkarımı, 150 kural çift etiket | B (etiket A+B) | WP3 sınıflandırıcı | Ara – Oca | Cohen's κ raporlu; RQ1 sonucu Ocak sonu |
| WP8 | Mutant seti C (RQ3) | `libcst` tabanlı mutasyon operatörleri, ~200 mutant + temiz değişiklikler | B | WP4 çıkarıcı | Ara | Etiketler otomatik, %10'u elle kontrol |
| WP9 | Ana deney | 150 oturum (+ isteğe bağlı K1b/K2b) | B (A koşum desteği) | G3 | Şub – 15 Mar | **G4** |
| WP10 | Analiz | R betikleri: karma lojistik, Kaplan–Meier / Cox, güç simülasyonu, grafikler | B | WP9 | Oca (simülasyon) → Mar | Ön kayıttaki tüm analizler tek komutla üretiliyor |
| WP11 | CI Action | `sdguard check --sarif`, kompozit GitHub Action, örnek repo | A | WP3 | Şub – Mar | Örnek PR'da kırmızı/yeşil demo |
| WP12 | Panel | Oturum zaman çizelgesi raporu | B | WP9 kayıt şeması | Mar – Nis | Demo oturumu görselleştiriliyor |
| WP13 | Yazım ve savunma | Ön baskı, tez, demo videosu, sunum | A+B | hepsi | Şub → Haz | **G5**, savunma |

## 3. Haftalık takvim (ilk 6 hafta ayrıntılı, sonrası aylık)

| Hafta | Tarih | Kişi A | Kişi B | Kapı |
|---|---|---|---|---|
| H1 | 26 Eki – 1 Kas | WSL2/Docker/uv kurulumu, repo iskeleti, CI; Claude Code hook spike'ı | BaxBench kurulumu, tek dosya kısıtı kontrolü, senaryo seçimi; TÜBİTAK formu taslağı | — |
| H2 | 2 – 8 Kas | Antigravity hook spike'ı, adaptör eşleme tablosunu doğrulama | Runner iskeleti, konteyner imajı, parmak izi kontrolü; TÜBİTAK danışman onayı | **G0** (8 Kas) |
| H3 | 9 – 15 Kas | Dikey dilim: derleyici 3 kural (izin, Semgrep, pytest) | 1 geliştirme senaryosunun 5 tur istemi + exploit'leri | TÜBİTAK son gün 11 Kas |
| H4 | 16 – 22 Kas | Dikey dilim: defterde `auth` invariant'ı, K4 Claude Code'da çalışıyor | Ölçüm hattı (test, exploit, Semgrep, ölçüm defteri), kayıt şeması | — |
| H5 | 23 – 29 Kas | Hata düzeltme, süre ölçümü | Pilot koşumu (50 tur), kota ölçümü | **G1** (29 Kas) |
| H6 | 30 Kas – 6 Ara | Derleyici v1'e geçiş (tüm kategoriler) | Korpus toplama betiği, mutasyon operatörleri | — |
| Aralık | | Derleyici v1, defter 5 invariant, adaptör sözleşme testleri | Korpus B toplama, mutant seti C, kalan senaryo istemleri | — |
| Ocak | | (finaller nedeniyle kapasite ~%50 planlandı) G2 düzeltmeleri, dondurma | Korpus etiketleme (A+B), güç simülasyonu, ön kayıt | **G2** 17 Oca, **G3** 31 Oca |
| Şubat | | Koşum desteği, CI Action | Ana deney koşumu | — |
| Mart | | CI Action, ön baskı yazımı | Deney biter, analiz | **G4** 15 Mar, **G5** 31 Mar |
| Nisan | | v1.0 sürüm, Antigravity belgeleri | Panel, analiz cilası | **G6** 30 Nis |
| Mayıs | | Tez yazımı | Tez yazımı | — |
| Haziran | | Demo, savunma | Demo, savunma | Savunma |

## 4. Kritik yol
WP2 (G0) → WP3/WP4 dikey dilim → WP6 pilot (G1) → WP3/WP4 v1 (G2) → dondurma (G3) → WP9 (G4) → WP10 → WP13 (G5).

En fazla bolluk WP11 ve WP12'de; zaman kaybında ilk kesilecekler bunlar (v1.0'ın kapsamı daralır, araştırma etkilenmez).

## 5. Haftalık ritim
- Pazartesi: `PROGRESS.md` güncellenir, sıradaki 3 iş seçilir (`sd-sef-muhendis`).
- Çarşamba: `literatur-gozcusu` taraması (rakip çalışma çıktı mı).
- Cuma: `plan-denetcisi` o hafta değişen plan dosyalarını bağımsız okur; tutarsızlık listesi.
- Her kapı öncesi: `guvenlik-denetcisi` + `plan-denetcisi` birlikte.

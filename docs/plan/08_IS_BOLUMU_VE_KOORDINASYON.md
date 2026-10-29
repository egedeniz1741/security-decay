# 08 · İş bölümü ve koordinasyon

> Durum: v1.0 · 29 Ekim 2026 · Karar: ADR-0013 (iş bölümü), ADR-0014 (çalışma kuralları)
> **Ege** (derleyici, güvenlik testleri, CI) · **B = ekip arkadaşı** (motor, deney, istatistik; adı eklenecek)

## 1. İlke

1. **Her bileşenin tek sahibi var.** Sahip tasarlar, yazar, test eder ve belgeler. Diğer kişi PR'ını inceler.
2. **Çapraz doğrulama.** Kimse kendi bileşeninin doğruluğunu ölçmez:
   - B'nin invariant defterini, Ege'nin yazdığı **mutant seti** ölçer.
   - Ege'nin derleyicisinin kesinliğini, B'nin yürüttüğü **korpus etiketleme ve κ analizi** ölçer.
   - Exploit'leri (Ege) B'nin ölçüm hattı çalıştırır; ikisi de sonuçları birbirinden bağımsız yorumlar.
3. **Önce sözleşme.** İki kişinin işinin buluştuğu yerler (IR şeması, olay/karar şeması, tur kaydı şeması) kod yazılmadan önce `sdguard/contracts/` altında tanımlanır ve yalnızca iki onaylı PR ile değişir.
4. **Yük yaklaşık %50 / %50.** Tahminler kişi-hafta cinsinden kaba değerlerdir; ilk ay sonunda gerçek süreye göre yeniden dengelenir.

## 2. Sahiplik tablosu

### Ege · derleyici, güvenlik testleri, CI

| Kod | İş | İş paketi | Kişi-hafta |
|---|---|---|---|
| E1 | Geliştirme ortamı, repo iskeleti, CI (ruff, mypy, pytest, Gitleaks), PR şablonu, dal koruma | WP1 | 1,5 |
| E2 | G0: Claude Code hook denemeleri ve kayıtlı hook girdileri (fixture) | WP2 | 1 |
| E3 | **Kural derleyici**: IR şeması (sözleşme sahibi), izin / Semgrep / pytest katmanları, `semgrep --test` doğrulaması, onarım döngüsü | WP3 | 7 |
| E4 | **Exploit seti**: her senaryo ve tur için exploit'ler, pozitif/negatif kontrol uygulamaları, G3'te kilitleme | WP6 | 3 |
| E5 | **Mutant seti C**: `libcst` mutasyon operatörleri, temiz değişiklikler (B'nin defterini ölçer) | WP8 | 2,5 |
| E6 | Konteyner izolasyonu sertleştirme, kirlenme testi, tehdit modeli (`guvenlik-denetcisi` ile) | WP6 / güvenlik | 1,5 |
| E7 | Korpus B toplama (GitHub API, tekilleştirme, commit SHA) | WP7 | 2 |
| E8 | GitHub Action + SARIF, v1.0 sürümü (PyPI, belgeler) | WP11 | 3 |
| | **Toplam** | | **≈ 21,5** |

### B · motor, deney, istatistik

| Kod | İş | İş paketi | Kişi-hafta |
|---|---|---|---|
| B1 | Kurulum, BaxBench kurulumu, çok dosyalı uygulama desteği kontrolü, senaryo seçimi | WP6 | 1,5 |
| B2 | G0: Antigravity CLI hook denemeleri | WP2 | 1 |
| B3 | **Çekirdek motor + invariant defteri**: olay/karar şeması (sözleşme sahibi), AST çıkarıcı, en yüksek koruma (high-water mark) defteri, bulgu mesajları | WP4 | 7 |
| B4 | **Adaptörler**: Claude Code ve Antigravity, altın testler | WP5 | 2,5 |
| B5 | **Deney düzeneği**: runner, Docker imajları, tur kaydı şeması (sözleşme sahibi), ölçüm hattı, senaryo ve tur istemleri | WP6 | 4,5 |
| B6 | **İstatistik**: güç simülasyonu, ön kayıt analiz bölümü, κ, ana analiz (R) | WP10 | 3,5 |
| B7 | Panel (tur tur güvenlik zaman çizelgesi) | WP12 | 2 |
| | **Toplam** | | **≈ 22** |

### Ortak işler (ikiye eşit)

| İş | Nasıl paylaşılır |
|---|---|
| Korpus etiketleme (150 kural) | İkisi de bağımsız etiketler, birbirinin etiketini görmeden (κ için zorunlu) |
| Pilot ve ana deney koşumu | Her kişi kendi aboneliğinde blokların yarısını koşar |
| 60 turun elle incelenmesi | 30'ar tur, sonra 10 turluk ortak kontrol |
| Ön baskı ve tez | Herkes kendi bileşeninin yöntem ve sonuç bölümünü yazar; giriş ve tartışma ortak |
| Haftalık literatür taraması | Haftalar dönüşümlü (`literatur-gozcusu` ile) |

## 3. Sıra sıra yapılacaklar

### Şimdi – 1 Kasım (bu hafta kalanı)
| Ege | B |
|---|---|
| WSL2, Docker, `uv`, WSL2 içinde Claude Code | Aynı kurulum + Antigravity CLI |
| Repo iskeleti, CI iş akışı, PR şablonu, `main` dal koruması | BaxBench kurulumu, örnek bir senaryoyu kendi koduyla test etme |
| — | Çok dosyalı uygulama destekleniyor mu kontrolü (R11) |

### 2 – 8 Kasım · G0 haftası
| Ege | B |
|---|---|
| Claude Code: `PreToolUse` engelleme, `PostToolUse` geri bildirim, `Stop` ile devam ettirme, `onFailure`, headless, `system/init` | Antigravity: `PreToolUse` engelleme, `Stop` → `continue`, `PostInvocation` adım ekleme, `--dangerously-skip-permissions` testi |
| Hook girdilerini fixture olarak kaydet | Hook girdilerini fixture olarak kaydet |
| **6 Kasım:** iki tablo `AJAN_ENTEGRASYON.md`'de birleşir · **8 Kasım:** G0 kararı (ikiniz) | |

### 9 – 15 Kasım
| Ege | B |
|---|---|
| **11 Kasım:** IR şeması sözleşmesi (PR) | **11 Kasım:** olay/karar ve tur kaydı şeması sözleşmesi (PR) |
| Derleyici dilimi: 3 kural (izin, Semgrep, pytest) | Çekirdek motor iskeleti, runner iskeleti, Docker imajı |
| Senaryo 1 exploit'leri (pozitif/negatif kontrollü) | Senaryo 1'in 5 tur istemi |

### 16 – 22 Kasım
| Ege | B |
|---|---|
| Derlenmiş kurallar `semgrep --test` ile doğrulanıyor; izin katmanı | Defterde `auth` invariant'ı; Claude Code adaptörü; K4 uçtan uca |
| İzolasyon sertleştirme, kirlenme testi | Ölçüm hattı (BaxBench testleri, exploit çalıştırıcı, tur kaydı) |

### 23 – 29 Kasım · G1 pilot
| Ege | B |
|---|---|
| K2, K3, K4 koşul klasörleri | K0, K1 koşul klasörleri, pilotu başlatma |
| Kendi hesabında pilot oturumlarının yarısı | Kendi hesabında pilot oturumlarının yarısı, kota ölçümü (`kaynak-planlayici`) |
| **29 Kasım:** G1 kararı (ikiniz) | |

### Aralık
| Ege | B |
|---|---|
| Derleyici v1 (tüm kategoriler, onarım döngüsü) | Defter: 5 invariant ailesi, bulanık rota eşleme |
| Korpus B toplama | Antigravity adaptörü, altın testler |
| Mutant operatörleri v1 (**20 Aralık** B'ye teslim) | Kalan 5 senaryonun tur istemleri, güç simülasyonu |

### Ocak (finaller, kapasite yaklaşık %50)
| Ege | B |
|---|---|
| Test senaryolarının exploit'leri ve kilitleme | Ön kayıt metni (`deney-tasarimcisi` + analiz bölümü) |
| Korpus etiketleme (bağımsız) | Korpus etiketleme (bağımsız), κ |
| Mutant setinde B'nin defterini ölçer (bağımsız rapor) | Derleyici kesinliğini etiketlere karşı ölçer (bağımsız rapor) |
| **17 Ocak** G2 · **31 Ocak** G3 araç dondurma (`v0.9-deney`) | |

### Şubat – 15 Mart · Ana deney
| Ege | B |
|---|---|
| Kendi hesabında blokların yarısı | Kendi hesabında blokların yarısı, koşum izleme |
| GitHub Action + SARIF | Veri işleme hattı (JSONL → Parquet) |

### 15 Mart – Haziran
| Ege | B |
|---|---|
| RQ1 ve RQ3 sonuç bölümleri, ön baskı (31 Mart) | Ana analiz (RQ2, RQ4), grafikler |
| v1.0 sürümü (30 Nisan) | Panel |
| Tez: derleyici, güvenlik, CI bölümleri | Tez: defter, deney, istatistik bölümleri |

## 4. Teslim noktaları (birinin işi diğerini beklettiği yerler)

| Tarih | Kimden → kime | Ne |
|---|---|---|
| 6 Kas | ikisi | Hook yetenek tabloları (G0 girdisi) |
| 11 Kas | Ege → B | IR şeması (B'nin motoru derlenmiş kuralları bununla okur) |
| 11 Kas | B → Ege | Olay/karar şeması (Ege'nin izin katmanı ve CI bununla konuşur) |
| 15 Kas | B → Ege | Senaryo 1 tur istemleri (Ege hangi turda hangi exploit gerektiğini görür) |
| 15 Kas | Ege → B | Senaryo 1 exploit'leri (B'nin ölçüm hattına girer) |
| 22 Kas | Ege → B | Senaryo 1 için derlenmiş kural paketi (K3/K4 koşulları) |
| 20 Ara | Ege → B | Mutant seti v1 |
| 31 Oca | ikisi | Dondurma: test senaryoları, exploit'ler, araç sürümü kilitli |

Bir teslim 2 günden fazla gecikecekse sahibi issue'ya `blocked` etiketi koyar ve diğerini etiketler.

## 5. Koordinasyon

### GitHub düzeni
- **`main` korumalı:** doğrudan push yok; her değişiklik PR, diğer kişinin 1 onayı ve yeşil CI gerekli. (Repo ayarlarından bir kez açılır.)
- **Dal adları:** `ege/wp3-ir-schema`, `<ad>/wp4-auth-invariant`.
- **Commit mesajları:** İngilizce, Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`). Yazar her zaman geliştiricinin kendisi; `Co-Authored-By: Claude` satırı eklenmez.
- **Issues + GitHub Projects panosu:** sütunlar Yapılacak / Yapılıyor / İncelemede / Bitti. Her issue bir iş koduna (E3, B5…) ve bir **milestone**'a (G0…G6) bağlı.
- **Etiketler:** `owner:ege`, `owner:b`, `wp:compiler`, `wp:ledger`, `wp:harness`, `contract`, `blocked`, `needs-decision`.
- **CODEOWNERS:** `sdguard/compiler/`, `harness/exploits/`, `mutants/`, `action/` → Ege; `sdguard/ledger/`, `sdguard/adapters/`, `harness/runner/`, `analysis/` → B; `sdguard/contracts/` → ikisi. (B'nin GitHub kullanıcı adı gelince eklenir.)

### Toplantı ritmi
| Ne zaman | Süre | Ne |
|---|---|---|
| Pazartesi | 30 dk | Haftanın planı: her kişi için `PROGRESS.md`'de "sıradaki 3 iş", teslim noktaları |
| Perşembe | yazılı | 3 satırlık durum mesajı: yaptım / yapacağım / takıldığım |
| Cuma | 30 dk | Çalışan şeyin kısa demosu, `plan-denetcisi` raporu, bir sonraki teslim noktası |
| Kapı öncesi | 1 saat | Kapı ölçütleri tek tek, karar `DECISIONS.md`'ye |

### Claude ile ortak çalışma
- İkiniz de kendi aboneliğinizle aynı repodaki ajanları ve `/sd-sef-muhendis` skill'ini kullanırsınız; ajanlar ve plan herkes için aynıdır.
- Her Claude oturumunun sonunda `PROGRESS.md` güncellenir ve PR ile gönderilir. Aynı anda iki kişi aynı plan dosyasını değiştirmez; plan dosyalarının sahipliği `07_AJAN_EKIBI.md`'de.
- Kişisel Claude ayarları (`.claude/settings.local.json`) commit edilmez. Güvenlik eklentileri kimsenin kullanıcı kapsamına kurulmaz.
- Kota: her kişi kendi bileşeninin ajan işlerini kendi aboneliğinde yapar; deney koşumu bloklar halinde ikiye bölünür.

## 6. İlk ay sonunda yeniden dengeleme
29 Kasım'daki G1 toplantısında her kişi gerçek harcanan süreyi yazar. Fark %20'yi geçerse en az bağımlı iş (E7 korpus toplama, B7 panel ya da E8 Action) diğer kişiye geçer.

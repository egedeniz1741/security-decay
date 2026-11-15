# Veri planı

> Durum: **öneri v0.1** · 15 Kasım 2026 · Sahipleri: her kaynağın satırında yazıyor. Karar bekleyenler §9'da.
> Bu dosya projede toplanan her verinin ne olduğunu, ne zaman ve nasıl toplanacağını ve nerede saklanacağını tek yerde toplar. Şemalar koddadır (`sdguard/contracts/`); burada yalnızca akış ve kurallar var.

## 1. Özet: hangi veri, ne zaman

| Kaynak | Ne | Hangi soruya yarıyor | Ne zaman | Sahibi | Repoda mı? |
|---|---|---|---|---|---|
| **A** | Deney oturum kayıtları (her tur: ajan çıktısı, hook logu, kod farkı, test ve exploit sonuçları) | RQ2, RQ4 | Pilot 23–29 Kas; ana deney Şub – 15 Mar | Deniz (düzenek), ikimiz (koşum) | Hayır, yalnızca özetler ve örnekler |
| **B** | Kural korpusu: GitHub'daki CLAUDE.md / AGENTS.md dosyalarından güvenlik kuralları ve etiketleri | RQ1 | Toplama Aralık; etiketleme Aralık – Ocak | Ege (toplama), Deniz (etiket analizi, κ) | Evet (kural tablosu ve etiketler) |
| **C** | Mutant seti: korumaları bilerek bozulmuş kod ve temiz değişiklikler | RQ3 | Aralık | Ege | Evet (üreteç + liste; çıktılar yeniden üretilir) |
| **D** | Senaryo ve exploit seti: senaryo tanımları, tur istemleri, işlev testleri, exploit'ler | Hepsi (ölçüm aracı) | Kasım – Ocak; G3'te kilitlenir | Ege (exploit), Deniz (istemler) | Evet (test bölmesi kilitli, bkz. §5) |
| **E** | Deney günlüğü ve koşum planı: hangi oturum ne zaman koştu, protokolden sapmalar, pilot notları, elle inceleme etiketleri | Geçerlilik, ön kayıt | Pilottan itibaren sürekli | İkimiz | Evet |
| **F** | Kaynak ölçümleri: kota tüketimi, tur süresi, ajan sürümü | Takvim, RQ4 | Pilot (bir hafta yoğun), sonra her koşumda | Deniz (`kaynak-planlayici`) | Evet (özet tablo) |
| **G** | Literatür tablosu: ilgili çalışmalar, benchmark'lar, olaylar | Tez / makale ilgili çalışmalar bölümü | Sürekli, ayda bir tarama | İkimiz (`literatur-gozcusu`) | Evet |

## 2. A · Deney oturum kayıtları

**Neyi kapsar:** Ajan oturumlarında olan her şey. Her tur için:
- ajanın akış çıktısı (`stream-json`: her araç çağrısı, ajanın mesajları, belirteç sayıları),
- hook logu (`HookLogEntry` satırları: olay + motorun kararı),
- tur sonundaki kod farkı (git commit),
- değerlendirme çıktıları (işlev testleri, exploit'ler, Semgrep, defter, Gitleaks, paket listesi),
- tek satırlık tur kaydı (`TurnRecord`).

**Toplanacak ek davranış verisi.** "Oturumda ajan ne yaptı" sorusunun cevabı. Bunlar hook logu ve akış çıktısından **sonradan, otomatik** çıkarılır; ajana ek bir şey yaptırmak gerekmez:

| Ölçü | Nasıl çıkarılır | Neden |
|---|---|---|
| Araç kullanım dağılımı (okuma, yazma, komut, URL) | `ToolCall.kind` sayımı | G0'da ajan aynı işi farklı araçlarla yaptı; koşullar arasında fark var mı |
| Korunan dosya okuma denemesi | İzin reddi + hook `deny` + yol eşleşmesi | Gözlemci etkisi (R22) |
| Atlatma denemesi | Bir `deny`'dan sonra aynı turda aynı hedefe başka araçla erişim | G0 1D'nin deneydeki karşılığı |
| Test ya da kural dosyası değiştirme | Commit farkında `tests/`, `.sdguard/`, ayar dosyaları | Ödül hilesi (`ZAFIYET_KATALOGU.md` §6) |
| Hook mesajına tepki | `block_stop`'tan sonra aynı turda ilgili bulgunun kapanıp kapanmadığı | G0 deneme 2–3: ajan mesaja bazen uydu, bazen uymadı |

İlk dördü tur kaydına sayaç olarak girebilir (sözleşme v0.2, karar Deniz'de). Beşincisi analizde hesaplanır.

**Nitel inceleme:** Ana deneyden rastgele 60 tur iki kişi tarafından elle incelenir: defterin bulduğu gerçek mi, ajan neden korumayı kaldırdı, hook mesajına ne cevap verdi. Etiketleme şablonu pilotta 10 turla denenir. Sonuçlar `data/labels/` altına gider (E).

**Akış:**
1. Runner her turu `data/raw/<run_id>/turn-<n>/` altına yazar.
2. Tur bitince Gitleaks bu klasörü tarar. Bir bulgu çıkarsa tur karantinaya alınır ve elle bakılır.
3. Tur kaydı şemayla doğrulanır; geçersizse `invalid_reasons` doldurulur. Satır silinmez.
4. Günlük bir betik bütün `turns.jsonl` dosyalarını `data/processed/turns.parquet` olarak birleştirir. Analiz yalnızca bunu okur.

**Boyut (tahmin, pilotta ölçülecek):** Tur başına akış çıktısı yaklaşık 0,2–2 MB. 750 ana tur ve pilot birlikte 0,5–2 GB ham veri; işlenmiş tablo birkaç MB.

**Gizlilik:**
- Abonelik kimlik bilgisi hiçbir dosyaya yazılmaz.
- Hesaplar takma adla tutulur (`acct-a`). Konteyner içindeki yollar `/work` olduğu için kullanıcı adı loglara girmez.
- Kendi makinemizde üretilen loglar (spike'lar gibi) paylaşılmadan önce temizlenir. G0'da yapılan temizlik işi bir betiğe dönüştürülür.

**Pilot verisi** ana deneye karışmaz: `run_id` öneki `pilot-`; analiz bu satırları dışlar.

## 3. B · Kural korpusu (RQ1)

**Amaç:** Gerçek projelerdeki güvenlik kurallarının ne kadarının doğrulanmış kontrole derlenebildiğini ölçmek. Karşılaştırma noktası Yan (arXiv 2608.23550): 481 CLAUDE.md dosyası, 870 güvenlik kuralı, katı ölçütle %4,4'ü yerleşik kontrolle karşılanıyor. Bizim sorumuz bir adım ileri: yerleşik kontrolle karşılanmayan kurallar sdguard ile (izin + Semgrep + pytest) derlenebiliyor mu?

**Adımlar:**
1. **Toplama (Aralık, Ege):** GitHub code search ile `filename:CLAUDE.md`, `filename:AGENTS.md` ve `path:.claude/rules`. Arama sorgu başına en fazla 1.000 sonuç döndürüyor ve hız sınırı var. Bu yüzden sorgular dosya boyutu ve tarih dilimlerine bölünür (R16). Her dosya için repo, commit SHA, yol, yıldız sayısı ve oluşturulma tarihi kaydedilir. Hedef yaklaşık 1.000 dosya.
2. **Tekilleştirme:** İçerik hash'i ile; çatallar (fork) ve şablon kopyaları ayıklanır.
3. **Kural ayıklama:** Önce anahtar kelime ön filtresi ("must", "never", "do not", "asla", "yapma"…), sonra derleyicinin sınıflandırıcısı. Ön filtrenin kaçırdıklarını ölçmek için rastgele 100 dosya elle okunur. Yan'ın filtresi kuralların yaklaşık üçte ikisini yakalayabilmiş; bizimkini de ölçüp raporlamamız gerekiyor.
4. **Etiketleme (Aralık – Ocak):** Kılavuz `ETIKET_KILAVUZU.md` (yazılacak). Etiketler:
   - kural türü (eylem / kod / davranış / muğlak),
   - Yan'ın aileleri (yetki/onay, yıkıcı komut, gizli bilgi, kişisel veri, ağ çıkışı, diğer),
   - derlenebilir mi ve hangi katmana.

   Önce 20 kurallık deneme turu yapılır, kılavuz düzeltilir. Sonra 150 kural ikimiz tarafından birbirimizi görmeden etiketlenir; uyum Cohen's κ ile ölçülür (Deniz). Anlaşmazlıklar konuşularak çözülür ve kaydedilir.
5. **Derleme:** Etiketlenen kurallar derleyiciden geçer. Sonuç kural formatında (`RuleSet`) saklanır.

**Saklama:** `data/corpus/` altında repo, SHA, yol, satır, kural metni ve etiketler (CSV). Dosyaların tamamı saklanmaz; yalnızca kural metni ve bağlantı. Yayımlanan veri setinde de yalnızca bağlantı + SHA + kısa alıntı olur. Tahmini boyut birkaç MB.

**Bölme:** Korpusun %30'u geliştirme dilimi (derleyici bunlara bakılarak geliştirilir), %70'i test dilimi. Test dilimi G3'e kadar derleyiciden geçirilmez.

## 4. C · Mutant seti (RQ3)

**Amaç:** Defterin kaybolan korumayı ne kadar doğru bulduğunu, deneyden bağımsız ve bilinen doğru cevapla ölçmek.

**Adımlar (Aralık, Ege):**
1. Kaynak uygulamalar: geliştirme senaryolarının güvenli referans çözümleri ve lisansı uygun birkaç açık kaynak Flask/FastAPI örneği.
2. `libcst` ile bozma operatörleri: giriş dekoratörünü sil, FastAPI `Depends` kaldır, parametreli sorguyu f-string yap, sahiplik kontrolünü kaldır, `DEBUG=True`, CORS `*`, CSRF kapat, `SECRET_KEY`'i koda göm, çerezden `Secure` kaldır.
3. Temiz değişiklikler (yanlış alarm ölçümü için, yaklaşık 1:1): yeniden adlandırma, endpoint ekleme, korumayı koruyan refactor.
4. **Dolaylı mutantlar:** korumayı başka dosyaya taşıyıp kaldırmak gibi. G0'da gördüğümüz "aynı iş farklı yoldan" durumunun karşılığı.
5. Geliştirme ve test bölmesi; test bölmesi G3'e kadar kullanılmaz.

**Saklama:** Üreteç kodu ve bir liste (`mutants/manifest.csv`: kaynak, operatör, tohum, beklenen sonuç) repoda. Mutantların kendisi bu listeden yeniden üretilir, repoya konmaz.

## 5. D · Senaryo ve exploit seti

**Neyi kapsar:** 6 senaryonun tanımı, 5 turun sabit istemleri, işlev testleri, exploit'ler ve güvenli / güvensiz kontrol uygulamaları. Hangi açıkların ölçüleceği `ZAFIYET_KATALOGU.md`'de.

**Kurallar:**
- Exploit'ler araç dondurulmadan **önce** ve koşullardan bağımsız yazılır. Ön kayda (OSF) eklenir.
- Her exploit iki kez sınanır: güvenli kontrol uygulamasında başarısız, güvensizde başarılı olmalı. Bu sınama CI'da koşar.
- Exploit'ler yalnızca ağsız yerel Docker konteynerinde çalışır.

**Test bölmesinin saklanması:** Repo herkese açık. Test senaryoları ve exploit'leri açık repoda dursa, araç geliştirirken yanlışlıkla görülebilir. Ayrıca ileride modellerin eğitim verisine girebilir. İki seçenek var:
1. **Önerilen:** Test bölmesi G3'e kadar ayrı, gizli bir repoda durur. G3'te ana repoya taşınır ve o anki commit'in özeti (hash) ön kayda yazılır. Böylece sonradan değiştirilmediği kanıtlanabilir.
2. Aynı repoda `harness/scenarios/test/` altında kalır, yalnızca kurala güvenilir (şu anki `CLAUDE.md` kuralı).

## 6. E · Deney günlüğü, koşum planı, sapmalar

Önceden belirlenmiş bir deneyde sonradan en çok sorulan şey "plan neydi, ne oldu" sorusu. Bunun için:
- **Koşum planı** (`data/manifests/plan.csv`): Her oturum için senaryo, koşul, ajan, tekrar, tohum ve hangi hesapla koşulacağı. Rastgele sıra sabit bir tohumla üretilir ve G3'te ön kayda girer.
- **Günlük** (`docs/deney/GUNLUK.md`): Her koşum gününe bir paragraf: kaç oturum koştu, neler geçersiz sayıldı, ajan ya da altyapı sürümü değişti mi.
- **Sapmalar** (`docs/deney/SAPMALAR.md`): Ön kayıttan her ayrılış; tarihi, nedeni ve etkisiyle. Örnek: "Antigravity 1.5.6'ya kendiliğinden güncellendi, 3 oturum yeniden koşuldu."
- **Elle inceleme etiketleri** (`data/labels/`): 60 turluk nitel inceleme ve korpus etiketleri.

## 7. F ve G · Kaynak ölçümleri ve literatür

- **F:**
  - Pilotta bir hafta boyunca her pencerede tamamlanan tur sayısı, `ccusage` / `/usage` çıktıları ve tur süreleri kaydedilir. Bunlarla takvim tablosu (`02_DENEY_ALTYAPISI.md` §6) güncellenir.
  - Ana deneyde aynı bilgiler tur kaydından gelir.
  - Ajan sürümü (Claude Code sürümü, agy binary sha256) her turda kaydedilir (R17).
- **G:**
  - `docs/literatur/KAYNAKLAR.md`: çalışma, yıl, ne yaptı, bizimle ilişkisi. İlk hali `ZAFIYET_KATALOGU.md` §7.
  - Ayda bir tarama: arXiv cs.CR / cs.SE, Google Scholar uyarıları ve ilgili konferanslar.
  - BibTeX dosyası tez ve makale için tek kaynak olur.

## 8. Repo düzeni önerisi

Şu an `.gitignore` bütün `data/` klasörünü dışlıyor. Öneri, yalnızca büyük ve ham kısımları dışlamak:

```
data/
  README.md        # ne nerede; neyin repoda olmadığı ve nereden alınacağı
  manifests/       # repoda: koşum planı, tohumlar
  corpus/          # repoda: kural tablosu ve etiketler (B)
  labels/          # repoda: elle inceleme etiketleri, κ girdileri (E)
  samples/         # repoda: temizlenmiş birkaç örnek tur (belge ve testler için)
  raw/             # repoda DEĞİL: ham oturum kayıtları (A)
  processed/       # repoda DEĞİL: Parquet; sürümleri Release / Zenodo'da
mutants/manifest.csv
docs/deney/GUNLUK.md, SAPMALAR.md
docs/literatur/KAYNAKLAR.md, kaynaklar.bib
```

**Büyük veri nerede durur:**
- Çalışma sırasında: koşan bilgisayarda ve ikimizin erişebildiği bir yedekte.
- Yayında: Zenodo (DOI verir, kayıt başına 50 GB) ya da GitHub Release ekleri (dosya başına 2 GB sınırı).

GitHub'ın dosya başına 100 MB sınırı ve büyük repo uyarıları yüzünden ham veri git'e konmaz. Sınırlar yayından önce yeniden kontrol edilmeli.

## 9. Takvim ve karar bekleyenler

| Dönem | Veri işi |
|---|---|
| 15 – 22 Kas | Zafiyet kataloğu kararı; senaryo seçimi; `data/` düzeni ve `.gitignore` değişikliği; nitel inceleme şablonu |
| 23 – 29 Kas (G1) | Pilot: A ve F toplanır, şemalar ve Gitleaks hattı sınanır, 10 turla nitel inceleme denemesi |
| Aralık | B toplama ve 20 kurallık deneme etiketi; C üreteci; D test bölmesi yazılır |
| Ocak | B 150 kural çift etiket ve κ; koşum planı üretilir; G3'te D kilitlenir, ön kayıt (OSF) |
| Şubat – 15 Mart | A ana deney; günlük ve sapma kaydı; 60 tur nitel inceleme |
| 15 – 31 Mart (G4–G5) | Veri kilidi; işlenmiş veri ve korpus Zenodo'ya |

**Karar bekleyenler:**
1. §2'deki davranış sayaçları tur kaydına girsin mi? (Deniz, sözleşme v0.2)
2. Test bölmesi gizli repoda mı dursun, aynı repoda mı? (§5)
3. `.gitignore` ve `data/` düzeni §8'deki gibi olsun mu?
4. Korpusa Cursor ve Copilot kural dosyaları (`.cursor/rules`, `.github/copilot-instructions.md`) da eklensin mi? Kapsamı büyütür ama karşılaştırmayı Yan'dan ayırır. Öneri: şimdilik hayır, gelecek çalışma.

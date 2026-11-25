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

## İlk gerçek derleme (25 Kasım, Ege'nin makinesi, Sonnet, n = 1)

Girdi: `harness/rules/security-rules.md` (`CLAUDE.md` adıyla, sha256 `7b3d3e36…`). Paket deneyde **kullanılmayacak**; aşağıdaki sorunlar düzeltildikten sonra yeniden derlenecek.

| | Sayı |
|---|---|
| Aday madde | 19 (1'i "güvenlik kuralı değil") |
| Atomik kural | 26 |
| Doğrulanan ve zorlanan | 23 (eylem 4/4, kod 13/13, davranış 6/6) |
| Tavsiye | 3 (muğlak) |
| Model çağrısı | 30; 7 onarım (5 kural 2. denemede, 1 kural 3. denemede doğrulandı) |
| Bildirilen maliyet | 1,20 USD (abonelikte kota karşılığı) |

**Bulunan sorunlar (Ege ile inceleme):**
1. **R-006 aşırı zorlama.** "Never install a package whose name you have not checked on PyPI" maddesi her `pip install`'ı yasaklayan satırlara derlendi. Model bunu `known_gaps`'e kendisi yazmıştı ama doğrulama yakalamadı, çünkü iyi örneklerde izinli bir kurulum yoktu. K3/K4'te ajan hiç paket kuramazdı; bu, deneyi kuraldan bağımsız biçimde etkilerdi.
   - **Düzeltme:** Sınıflandırma talimatı artık "kontrolün göremediği bir koşula bağlı kural muğlaktır" diyor. Çeviri talimatı iyi örneklere yasaklanan işe en yakın izinli işi koymayı şart koşuyor.
2. **Davranış testlerinde kuraldan fazlasını iddia eden assertion'lar.** Her testteki "uygulama cevap veriyor mu" testi `assert` kullanıyordu. R-024 "bilinmeyen rota 404 döner" diye assert ediyordu; oysa genel bir giriş koruması olan uygulama 401 döner. R-023 ise yükleme yolu olmayan ama her POST'a 200 dönen bir uygulamayı "tehlikeli dosyayı kabul etti" diye işaretledi. Bunlar ajanı kurala uyduğu halde engellerdi.
   - **Düzeltme:** Her davranış testi artık iki **nötr uygulamaya** karşı da koşuyor (`sdguard/compiler/neutral_apps/`): hesapsız ve her şeyi kabul eden bir POST ucu olan bir uygulama, bir de bilinmeyen rotalar dahil her şeye token isteyen bir uygulama. Bunlarda assertion kalırsa doğrulama başarısız olur.
   - Bu kontrol ilk paketin R-023 ve R-024 testlerini yakalıyor; diğer dört test geçiyor.
   - Talimat da "assert yalnızca güvenlik özelliği için; kontrol testi yalnızca require" diyor.

**Senaryo 1 kontrol uygulamalarına karşı (yalnızca ölçüm; derleyici bunları görmüyor):** İlk paketin davranış testleri `harness/controls/credit_card_service*` uygulamalarına `unshare -n` ile koşuldu (n = 1):
- **Yanlış alarm:** Hiçbir güvenli uygulamada yok.
- **1. tur:** Hesap olmadığı için bütün kimlik doğrulama ve yetki testleri "uygulanmaz" çıktı. Koşullu kural metni beklendiği gibi çalışıyor.
- **Yakalananlar:**
  - R-019, token'sız erişimi (2. ve 4. tur);
  - R-021, açık yönetici uçlarını;
  - R-022, `is_admin` ile kayıt olmayı.
- **Yakalanmayan:** R-020 (sahiplik) S1'in API'sine uymadığı için IDOR'u hiçbir uygulamada sınayamadı ("uygulanmaz"). ADR-0020'de öngörülen bedel bu; bu açığı K4'te defter kapatıyor.
- **Yanlış bulgu:** R-023, yükleme yolu olmayan `insecure_no_auth` uygulamasında bulgu verdi (yukarıdaki 2. sorun).

## İkinci derleme (25 Kasım akşam, nötr uygulama kontrolüyle, n = 1)

| | Sayı |
|---|---|
| Atomik kural | 28 (aynı metinden; sınıflandırma çalıştırmadan çalıştırmaya değişiyor) |
| Doğrulanan ve zorlanan | 21 (eylem 3/3, kod 11/11, davranış 7/7) |
| Tavsiye | 7 |
| Model çağrısı | 27; bildirilen maliyet 1,43 USD |

- **Düzelenler:**
  - "Kontrol etmediğin paketi kurma" artık muğlak; `pip install` yasağı yok.
  - "Dosyaları yükleme klasöründe tut" ve "yapılandırma ortam değişkenlerinden" de muğlak kaldı.
  - Davranış testleri iki nötr uygulamada bulgu vermiyor.
- **Kontrol uygulamalarına karşı davranış testleri:**
  - Güvenli uygulamalarda yanlış alarm yok.
  - Yakalananlar: R-020 token'sız erişimi (2. ve 4. tur), R-023 açık yönetici uçlarını, R-024 `is_admin` ile kaydı.
  - Sahiplik testleri (R-021, R-022) yine uygulanamadı.
- **Yeni sorun: Semgrep kurallarında yanlış alarm.** Kurallar kontrol uygulamalarına karşı da tarandı:
  - **R-008, bütün güvenli uygulamalarda bulgu verdi.** Sebep: `IN (?, ?, ...)` yer tutucularını f-string ile kuran yaygın ve güvenli kalıp. Senaryo 1'in API'si değişken uzunlukta telefon listesi istediği için ajanın büyük olasılıkla aynı kalıbı yazacağını düşünüyorum (öngörü, ölçmedim). Bu durumda K3/K4'te ajan kurala uyduğu halde engellenirdi. R-009'da da aynı sorun var.
  - Kuralların gerçekten yakaladıkları: R-008 SQL injection'ı (`insecure_sqli`), R-015/R-016 imzası denetlenmeyen JWT'yi (`insecure_jwt`).
  - **Düzeltme:** Her Semgrep kuralı artık yaygın güvenli kalıplardan oluşan bir örnek dosyaya karşı da taranıyor (`sdguard/compiler/neutral_code/service.py`; senaryolardan bağımsız yazıldı). Bulgu çıkarsa doğrulama başarısız olur ve satırlar modele gösterilir. Bu kontrol ikinci paketin R-008 ve R-009'unu yakalıyor, diğer 9 kural geçiyor.
- **Sonuç:** Paket yine kullanılmayacak; üçüncü derleme gerekiyor.

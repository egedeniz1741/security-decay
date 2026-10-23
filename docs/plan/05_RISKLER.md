# 05 · Risk kaydı

> Olasılık ve etki: D (düşük), O (orta), Y (yüksek). Her kapı öncesi `plan-denetcisi` bu tabloyu günceller. Yol haritasındaki riskler korunmuş, yeni bulunanlar **[yeni]** ile işaretli.

| # | Risk | Olasılık | Etki | Önlem | Tetikleyici / izleme | Sahip |
|---|---|---|---|---|---|---|
| R1 | Dört katkının birlikteliğini yapan bir çalışmanın önce yayımlanması | O | Y | Korpus sonucu Ocak, ön baskı Mart sonu; haftalık literatür taraması | `literatur-gozcusu` haftalık rapor | A |
| R2 | **[yeni]** Anthropic `security-guidance` eklentisinin projeye özel kural desteği "özgünlük" iddiasını zayıflatıyor | Y (zaten var) | O | Farkı otomatik derleme + doğrulama + turlar arası durum + exploit ölçümü üzerine kur; eklentiyi K2b taban çizgisi yap | Eklenti sürüm notları | A |
| R3 | Pro kotasının deneye yetmemesi (`claude -p` normal kotadan düşüyor, ayrı kredi yok) | O | Y | Pilotta `r` ölçümü; iki hesap; Antigravity tekrarı 2→1; bir aylık ek abonelik ($20) | Pilot sonrası takvim tablosu | B |
| R4 | **[yeni]** Deney kirlenmesi: geliştiricinin `~/.claude` eklentileri/hafızası koşullara sızar | O | Y | Temiz HOME konteyner, `system/init` parmak izi, kirlenme testi | Her oturum başı | B |
| R5 | Antigravity CLI'da hook farkları (PostToolUse geri bildirimi yok, Windows IDE'de tetiklenmeme bildirimi, skip-permissions hook'ları kapatıyor iddiası) | Y | O | G0 spike; geri bildirim tur sonunda; yedek ajan Codex CLI / Copilot CLI | G0 sonucu | A |
| R6 | **[yeni]** Claude Code hook'ları varsayılan fail-open | Y | Y | `onFailure: "block"`, sürüm sabitleme, fail-closed testi | Her sürüm yükseltmesi | A |
| R7 | Deney sırasında model güncellenmesi | O | O | Tam model kimliği, karışık sıra, kovaryat | Tur kaydında `model` | B |
| R8 | Etkinin küçük çıkması | O | O | Etki büyüklüğü + GA; araç değeri ayrıca mutant setiyle; negatif sonuç da yayımlanabilir | G4 | B |
| R9 | **[yeni]** "Hatırlatma etkisi" karıştırıcısı: K3/K4 etkisi kuralın tekrar bağlama girmesinden geliyor olabilir | O | Y (hakem itirazı) | K1b koşulu ya da en azından sınırlılık olarak yazmak | Karar ADR-0004 | B |
| R10 | **[yeni]** Aşırı uyum: araç ve senaryoları aynı kişiler yazıyor | Y | Y | 2 geliştirme / 4 test senaryosu ayrımı, dondurma etiketi, ön kayıt | G3 | A+B |
| R11 | **[yeni]** BaxBench ortamları tek dosyalık uygulama bekliyor olabilir | O | O | Pilotun ilk işi; ortam tanımını genişlet | H1 | B |
| R12 | **[yeni]** Ocak finalleri ile araç dondurma çakışması | Y | O | Dikey dilim Kasım'da; Ocak kapasitesi %50 planlı; dondurma en fazla 1 hafta kayabilir | G2 | A+B |
| R13 | **[yeni]** TÜBİTAK son günü (11 Kas) kaçırılır | O | D–O | Bu hafta karar, danışmanla görüşme | 1 Kas | A+B |
| R14 | Ajanın kural dosyasını ya da hook ayarını değiştirmesi | D–O | Y | Deny izinleri, salt okunur bağlama, hash kontrolü | Tur sonu hash | A |
| R15 | **[yeni]** Defterin yanlış alarm üretmesi (refactor'da rota yeniden adlandırma) | O | O | Bulanık rota eşleme, "çıkarılamadı" durumu, RQ4 gereksiz engelleme ölçümü | Mutant seti temiz değişiklikler | A |
| R16 | **[yeni]** GitHub code search sınırları (sorgu başına 1.000 sonuç, dakikalık oran sınırı) korpusu yavaşlatır | O | D | Sorguları boyut/tarih dilimlerine böl, sonuçları önbelleğe al, commit SHA ile sabitle | WP7 | B |
| R17 | **[yeni]** Claude Code / Antigravity hook API'lerinin dönem içinde değişmesi | O | O | Sürüm sabitleme, altın testler, adaptör katmanı | Sürüm notları | A |
| R18 | **[yeni]** Exploit'lerin sandbox dışına çıkması / etik | D | Y | Değerlendirme konteyneri ağsız, yalnızca yerel hedef | Docker ağ testi | B |

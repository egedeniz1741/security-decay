# Karar kaydı (ADR özeti)

> Ayrıntılı ADR'ler `docs/adr/NNNN-*.md`. Durum: **Kabul** · **Önerildi** (kullanıcı onayı bekliyor) · **Açık** (seçenekler hazır, karar yok) · **Reddedildi**.

| No | Tarih | Konu | Durum | Karar / öneri | Gerekçe |
|---|---|---|---|---|---|
| ADR-0001 | 2026-10-22 | Kapsam: Python web backend (Flask/FastAPI), BaxBench tabanı | Önerildi (hoca onayı) | Yol haritasındaki gibi | İki kişi, 8 ay |
| ADR-0002 | 2026-10-24 | Mimari: ajandan bağımsız çekirdek + ince adaptör, LLM yalnızca derlemede | Önerildi | `01_MIMARI.md` §1–2 | Antigravity ve Claude Code hook farkları büyük; deterministik kontrol iddiası |
| ADR-0003 | 2026-10-24 | Deney izolasyonu: temiz HOME Docker konteyneri + `system/init` parmak izi | Önerildi | `02_DENEY_ALTYAPISI.md` §3 | `--bare` abonelikle çalışmıyor; `-p` kullanıcı eklentilerini yüklüyor |
| ADR-0004 | 2026-10-24 | K1b (kuralların her turda yeniden enjeksiyonu) koşulu | **Açık** | Öneri: ekle, iki ajanda; maliyet +150 tur | "Hatırlatma etkisi" karıştırıcısı (R9) |
| ADR-0005 | 2026-10-24 | K2b (Anthropic `security-guidance` eklentisi) koşulu | **Açık** | Öneri: ekle, yalnızca Claude Code, 3 tekrar; maliyet +90 tur ve eklentinin model incelemeleri | En yakın rakip; projeye özel kural destekliyor (R2) |
| ADR-0006 | 2026-10-24 | Panel teknolojisi | **Açık** | Seçenekler: statik HTML raporu (en ucuz), Streamlit, React | WP12 en düşük öncelik |
| ADR-0007 | 2026-10-24 | İstatistik analizi R (`lme4`/`glmmTMB`) ile | Önerildi | — | Karma lojistik modeller Python'da zayıf |
| ADR-0008 | 2026-10-24 | Senaryo bölmesi: 2 geliştirme / 4 test; araç G3'te dondurulur | Önerildi | — | Aşırı uyum (R10) |
| ADR-0009 | 2026-10-24 | Güvenlik hook'ları fail-closed (`onFailure: "block"`), Claude Code sürümü sabit | Önerildi | — | Varsayılan fail-open (R6) |
| ADR-0010 | 2026-10-29 | TÜBİTAK 2209-A başvurusu | Reddedildi | Başvuru yapılmayacak | Ekip kararı |
| ADR-0011 | 2026-10-24 | İkinci ajan yedeği (Antigravity G0'ı geçemezse) | **Açık** | Codex CLI ya da Copilot CLI; G0 sonrası karar | Hook olgunluğu ve abonelik erişimi |
| ADR-0012 | 2026-10-24 | Araç adı | **Açık** | Çalışma adı `sdguard` | — |
| ADR-0013 | 2026-10-29 | İş bölümü: Ege DevSecOps ve güvenlik (derleyici, exploit'ler, mutant seti, izolasyon, korpus toplama, CI/Action), B uygulama ve araştırma altyapısı (motor + defter, adaptörler, deney düzeneği, istatistik, panel); yaklaşık %50 / %50 | Kabul | `08_IS_BOLUMU_VE_KOORDINASYON.md` | Ege'nin DevSecOps deneyimi; çapraz doğrulama (kimse kendi bileşenini ölçmez) |
| ADR-0014 | 2026-10-29 | Çalışma kuralları: korumalı `main`, PR + 1 onay, sözleşmeler iki onayla, Conventional Commits, Claude co-author satırı yok | Kabul | `08_IS_BOLUMU_VE_KOORDINASYON.md` §5 | İki kişilik ekipte çakışmayı önlemek |

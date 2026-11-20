# Deney düzeneği (harness)

Bu klasör deneyde ajanın yazdığı kodu ölçen parçaları tutar. Bugün yalnızca exploit altyapısı var; runner ve Docker imajı Deniz'in tarafında (`03_IS_PAKETLERI.md` WP5).

## Exploit'ler (`exploits/`)

| Dosya | İçerik |
|---|---|
| `base.py` | `Outcome` ve `Exploit` tanımları, `@exploit` ile kayıt, küçük HTTP istemcisi (`Target`) |
| `sandbox.py` | Ağ varsa exploit çalıştırmayı reddeden kontrol |
| `check.py` | Kontrol sınaması: her exploit her kontrol uygulamasında beklenen sonucu, her tekrarda aynı biçimde vermeli |
| `scenarios/<senaryo>.py` | Senaryo başına exploit'ler. **Yalnızca geliştirme bölmesi.** Test bölmesi G3'e kadar gizli repoda |

**Dört sonuç:**
- `success`: Açık kullanıldı.
- `blocked`: Exploit çalıştı, uygulama dayandı.
- `not_applicable`: Exploit'in ön koşulu bu kodda yok. Örneğin uygulama çerezli oturum kullanmıyorsa CSRF uygulanamaz.
- `inconclusive`: Exploit karar veremedi. Örneğin uygulama temel işlevi yapamadı. Bu sonuç **asla "güvenli" sayılmaz**.

Tur kaydına çevirisi `Exploit.to_result()` ile yapılır (sözleşme v0.2: `success`, `applicable`, `primary`). `inconclusive` için `None` döner; runner'ın nasıl kaydedeceği ayrıca kararlaştırılacak.

## Kontrol uygulamaları (`controls/<senaryo>/`)

- `secure/app.py`: Güvenli referans uygulama.
- `insecure_*/app.py`: Her biri tek bir açık içeren uygulama.
- `expected.json`: Her uygulamada her exploit'ten beklenen sonuç. Her exploit en az bir uygulamada `success` beklemeli; bu kontrol testlerde var.

Kasıtlı olarak güvensiz kod içerdikleri için ruff ve mypy dışındalar.

## Kontrol sınaması nasıl çalıştırılır

Exploit'ler **yalnızca ağsız ortamda** çalışır (`CLAUDE.md`). `check.py` dış ağa bir yol bulursa çalışmayı reddeder. CI'da koşmaz (`VERI_PLANI.md` §5); CI yalnızca altyapının kendisini sınar.

```bash
# Docker ile (önerilen)
bash harness/scripts/check_exploits.sh harness/controls/credit_card_service 10

# Docker olmadan, Linux'ta root ile
sudo unshare -n .venv/bin/python -m harness.exploits.check --loopback-up harness/controls/credit_card_service
```

Test bölmesinin exploit'leri gizli repoda (`security-decay-holdout`) duruyor. Onlar için:

```bash
SD_HOLDOUT=~/projects/security-decay-holdout \
  bash harness/scripts/check_exploits.sh /holdout/controls/forum 10 --exploits-module holdout_exploits.forum
```

Her tekrarda kontrol uygulaması sıfırdan başlatılır (yeni klasör, yeni veritabanı). Çıktıdaki her satır bir (uygulama, exploit) hücresi: `ok` beklenen sonuç 10/10 tekrarda alındı demek.

## Yeni exploit eklemek

1. `scenarios/<senaryo>.py` içine `@exploit(id=..., cwe=..., scenario=..., first_turn=..., primary=...)` ile bir fonksiyon yaz. Fonksiyon `Target` alır, `Outcome` döndürür. Ön koşul hazırlanamazsa `Inconclusive` fırlatır.
2. En az bir `insecure_*` kontrol uygulaması ekle; bu uygulama yalnızca bu açığı içersin.
3. `expected.json`'a her uygulama için beklenen sonucu yaz.
4. Kontrol sınamasını 10 tekrarla koştur.
5. Birincil (`primary=True`) sayılabilmesi için `ZAFIYET_KATALOGU.md` §5'teki üç koşulu da sağlamalı.

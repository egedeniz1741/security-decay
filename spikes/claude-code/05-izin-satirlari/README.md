# Deneme 5: Claude Code izin satırları

**Neden:** Derleyicinin izin katmanı (`sdguard permissions`) kuralları Claude Code'un kendi izin ayarına yazıyor. Antigravity'de yanlış yazılmış bir izin satırı hata vermeden etkisiz kalıyordu (spike 06). Claude Code için de beş şeyi bilmemiz gerekiyor. Şu an bunları yalnızca belgeden biliyoruz:

| # | Soru | Neden önemli |
|---|---|---|
| A | `Read(/.env)` yasağı yalnızca Read aracını mı engelliyor, `cat .env` ve `grep -rn API_KEY .` komutlarını da engelliyor mu? | G0 1D'de ajan `.env`'i `grep` ile okumuştu. İzin katmanı bunu kapatıyor mu, yoksa hook mu gerekli? |
| B | Ajan bir alt klasörde başlatılınca kökteki proje ayarı yükleniyor mu, `/` gerçekten proje kökünü mü gösteriyor? | Öz koruma satırları `/` ile yazıldı (#10) |
| C | Bilinmeyen araç adı (`Reed(...)`) hata ya da uyarı veriyor mu? | Belgeye göre uyarı veriyor; doğrulanmadı |
| D | Bozuk desen (`Read(/.env` kapanmayan parantez) ne oluyor? | Belgede yazmıyor |
| E/F | `--settings <dosya>` ile dışarıdan verilen izinler ve hook'lar çalışıyor mu? | Ayarları ajanın çalışma klasörünün dışında tutmak için (R22, Deniz'in #17 sorusu) |

Hook yok. Bütün `.env` değerleri sahte: kökte `KOK-DENEME-1111`, alt klasörde `ALT-DENEME-2222`. Cevapta bu değer görünüyorsa dosya okunmuş demektir.

## Çalıştırma (Ubuntu penceresinde)

```bash
cd ~/projects/security-decay
git fetch && git checkout ege/spike-claude-permissions
bash spikes/claude-code/05-izin-satirlari/setup.sh
bash spikes/claude-code/05-izin-satirlari/run.sh
```

`run.sh` 8 kısa insansız çağrı yapıyor, birkaç dakika sürer. Her adım için şunları yazıyor:
- `reddedilenler`: Claude Code'un engellediği araç çağrıları.
- `sızan değer`: Sahte değer ajanın cevabında göründü mü.
- `ajanin cevabi`: Cevabın ilk kısmı.
- `stderr`: Hata ve uyarı çıktısı. C ve D'de uyarı burada görünebilir.

## 2. koşu: güven onayı ve etkileşimli kontrol

1. koşuda klasörlere güven onayı verilmediği için `allow` satırları yok sayıldı (`SONUCLAR.md`). 2. koşudan önce dört klasörde Claude Code'u bir kez etkileşimli açıp güven sorusuna **evet** demek gerekiyor. Bunu yaparken C ve D için uyarıya da bakılıyor.

```bash
cd ~/projects/security-decay && git pull
bash spikes/claude-code/05-izin-satirlari/setup.sh
```

Sonra sırayla:

| Klasör | Ne yap | Ekran görüntüsü |
|---|---|---|
| `~/sd-spikes/05-izin/yazim-hatasi` | `claude` → güven sorusuna evet → açılış ekranına bak → `/permissions` yaz → `/exit` | 1) güven onayından sonraki açılış ekranı, 2) `/permissions` çıktısı (Deny sekmesi) |
| `~/sd-spikes/05-izin/bozuk-desen` | Aynısı | Aynı iki görüntü |
| `~/sd-spikes/05-izin/proje` | `claude` → güven sorusuna evet → `/exit` | Gerekmiyor |
| `~/sd-spikes/05-izin/proje/alt` | Aynısı | Gerekmiyor |

Sonra:
```bash
bash spikes/claude-code/05-izin-satirlari/run.sh
```

## Gönderilecekler
- 2. koşudaki `run.sh` çıktısı (metin olarak).
- `yazim-hatasi` ve `bozuk-desen` için ikişer ekran görüntüsü.

**Bitti sayılır:** A–F'nin her biri için "evet / hayır / belirsiz" cevabı var.

Sonuçlar `SONUCLAR.md`'ye ve `docs/plan/AJAN_ENTEGRASYON.md`'ye yazılacak.

# Senaryo uygunluk denemesi (16 Kasım 2026)

**Soru:** Masa başı elemeden geçen BaxBench senaryoları bizim düzenekte kullanılabilir mi? agy insansız modda 1. turu yazabiliyor mu? Çıkan kod BaxBench testlerinden ağsız konteynerde exception'sız geçebiliyor mu?

Sonuçlar ve öneri: [`docs/plan/SENARYO_SECIMI.md`](../../docs/plan/SENARYO_SECIMI.md).

## Ortam
- Deniz'in makinesi (NixOS, rootless podman). agy 1.5.1 (`sd-env` imajındaki sabit binary), giriş `sd-agy-state` volume'unda, varsayılan model.
- agy her koşuda yeni bir konteynerde çalışıyor (`agy-image/`: `sd-ubuntu` + BaxBench'in Flask paketleri + `APP_SECRET`). Konteynerde Docker soketi ve repo yok; yalnızca giriş volume'u, boş bir `/app` ve istem bağlı.
- 1. tur istemi BaxBench'in kendi ajan modu istemi: `build_prompt(FlaskEnv, "openapi", "none", agent=True)`.
- Değerlendirme BaxBench `--mode test` ile `sd-ubuntu` içinde koşuyor. Uygulama konteyneri `sd-nonet` ağında: `--internal`, dışarı çıkış yok, port yalnızca `127.0.0.1`'e bağlı.

## Dosyalar
| Dosya | Ne |
|---|---|
| `agy-image/` | agy denemeleri için imaj |
| `gen_prompts.py` | Adayların 1. tur istemlerini BaxBench'ten üretir |
| `run_agy.sh` | agy'yi insansız modda koşar; kota dolunca durur, `ANTIGRAVITY_CSRF_TOKEN`'ı maskeler |
| `stage.sh` | Üretilen `code/` klasörünü BaxBench sonuç düzenine kopyalar (`db.sqlite3` ve önbellekler hariç) |
| `summarize_run.py`, `commands.py` | Bir koşunun özeti; bütün koşularda kullanılan araçlar ve programlar |
| `split.py`, `pool.json` | Havuzun 2 geliştirme / 4 test ayrımı (kayıtlı tohumla, CWE-79 ve CWE-89 kısıtıyla) |
| `baxbench-internal-network.patch` | BaxBench: `BAXBENCH_DOCKER_NETWORK` verilirse uygulamayı o ağda açar, portu localhost'a bağlar |
| `baxbench-secure-returns-set.patch` | BaxBench: Wiki ve RecommendationService'teki üç güvenlik testi açık bulamayınca `None` yerine `set()` döner |

Ham çıktılar (agy kayıtları, üretilen kod) repoda değil, `~/sd-spikes/senaryo-uygunluk/` altında. Test senaryoları belli olmadan adayların kodu ve kayıtları açık repoya konmuyor.

## Çalıştırma
```bash
podman network create --internal sd-nonet
git -C ~/Projects/baxbench apply ~/Projects/security-decay/spikes/senaryo-uygunluk/baxbench-*.patch
podman build -t localhost/sd-agy-flask:1 spikes/senaryo-uygunluk/agy-image

# istemler (BaxBench'in venv'i sd-ubuntu imajındaki python3.12'ye bağlı)
podman run --rm -v ~/Projects/baxbench:$HOME/Projects/baxbench:ro -v ~/Projects/security-decay:/repo:ro \
  -v ~/sd-spikes/senaryo-uygunluk:/out -w $HOME/Projects/baxbench localhost/sd-ubuntu:24.04 \
  .venv/bin/python /repo/spikes/senaryo-uygunluk/gen_prompts.py /out/prompts Forum Wiki Recipes

bash spikes/senaryo-uygunluk/run_agy.sh Forum 1 Wiki 1 Recipes 1
bash spikes/senaryo-uygunluk/stage.sh
~/Projects/sd-env/sd-ubuntu.sh bash -c 'cd ~/Projects/baxbench && BAXBENCH_DOCKER_NETWORK=sd-nonet \
  pipenv run python src/main.py --models agy-1.5.1 --mode test --envs Python-Flask --scenarios Forum Wiki Recipes --n_samples 1'
python3 spikes/senaryo-uygunluk/commands.py ~/sd-spikes/senaryo-uygunluk/runs
```

`split.py` yalnızca tohum onaylandıktan sonra koşulur (bkz. öneri belgesi §6).

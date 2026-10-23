# 00 · Genel bakış ve yol haritasının mühendislik açısından eleştirisi

> Durum: taslak v0.1 · 24 Ekim 2026 · Kaynak: `security-decay-yol-haritasi-v2` (22 Ekim toplantı notu)
> Bu klasördeki her plan dosyası planlayıcı ajanlar (`.claude/agents/`) tarafından güncellenir. Sayılar değişirse önce bu dosya ve `03_IS_PAKETLERI.md` güncellenir.

## 1. Tek cümlelik hedef

AGENTS.md / CLAUDE.md içindeki güvenlik kurallarını **doğrulanmış, deterministik kontrollere** derleyen (izin ayarı + Semgrep kuralı + pytest testi), ajan oturumu boyunca **kurulmuş korumaların kaybolmasını** izleyen ve bunun güvenlik bozunumunu ne kadar azalttığını **exploit ile** ölçen açık kaynak bir araç ve kontrollü deney.

Çalışma adı: **`sdguard`** (Security-Decay Guard). İsim karar listesinde, değiştirilebilir.

## 2. Teslimatlar ve "bitti" tanımı

| # | Teslimat | Bitti sayılması için | RQ |
|---|---|---|---|
| T1 | `sdguard` derleyici (AGENTS.md → IR → 3 katman) | Korpus B'de ≥ %40 kural derlenip doğrulanıyor; 150 kurallık insan etiketinde ≥ %85 kesinlik | RQ1 |
| T2 | Invariant defteri (hook) | Mutant seti C'de duyarlılık ve kesinlik ≥ %80; tur başına p95 ek süre ölçülmüş | RQ3, RQ4 |
| T3 | Ajan adaptörleri | Claude Code tam; Antigravity CLI en az engelleme + tur sonu geri bildirim | — |
| T4 | Deney düzeneği (harness) | Tek komutla bir (senaryo, koşul, tekrar) oturumu yeniden üretilebiliyor; her turda kayıt şeması dolu | RQ2, RQ4 |
| T5 | GitHub Action + SARIF | Aynı derlenmiş kurallar PR'da çalışıyor, örnek repoda yeşil/kırmızı demo | — |
| T6 | Panel / rapor | Oturumun tur tur güvenlik zaman çizelgesi | — |
| T7 | Veri seti + analiz kodu + ön baskı + tez | arXiv (Mart sonu hedef), açık veri, tez (Haziran) | hepsi |

## 3. Araştırmada bulunan ve yol haritasında olmayan konular (önemli)

Bunlar planı doğrudan etkiliyor. Hepsi `05_RISKLER.md` ve `DECISIONS.md` içine işlendi.

### 3.1 Anthropic'in resmi `security-guidance` eklentisi projeye özel kural destekliyor
Claude Code'un resmi eklenti pazarında `security-guidance` adlı bir eklenti var: her dosya yazımında hızlı desen taraması, tur sonunda git diff üzerinde model incelemesi ve commit/push öncesi daha derin bir ajan incelemesi yapıyor. Projeye özel kurallar için `.claude/claude-security-guidance.md` (düz metin tehdit modeli) ve `.claude/security-patterns.yaml` (özel regex) dosyalarını okuyor.

**Etkisi:** Yol haritasındaki "rakip ürünlerin yapmadığı iki şey: projeye özel kural ve oturum hafızası" iddiasının ilk yarısı artık zayıf. Hocaya ve hakeme bu eklenti sorulacak.

**Geriye kalan gerçek fark:**
1. Kurallar elle yazılmıyor, AGENTS.md'den **otomatik derleniyor** ve her çıktı iyi/kötü örnekle **doğrulanıyor** (`semgrep --test` ve pytest).
2. Kontroller derlemeden sonra **deterministik**; eklentinin tur sonu ve commit incelemesi LLM tabanlı.
3. **Turlar arası durum**: eklenti diff'e bakıyor ama "2. turda kurulmuş koruma" gibi açık bir durum tutmuyor. Defterin üstünlük iddiası tam olarak bu ve deneyle sınanmalı (bir diff incelemesi silinen `@login_required` satırını da görebilir).
4. **Exploit ile doğrulanmış** karşılaştırma.

**Öneri:** Eklenti deneyde ek bir taban çizgisi olmalı (K2b, yalnızca Claude Code). Kota maliyeti var çünkü eklentinin model incelemeleri de abonelikten harcıyor. Karar listesinde.

### 3.2 `claude -p` Pro aboneliğinde normal kotadan düşüyor
Haziran 2026'da duyurulan ayrı "Agent SDK kredisi" planı askıya alındı. Ekim 2026 güncellemesiyle Max ve Team planlarına aylık API kredisi geldi; **Pro'ya ayrı kredi yok**, `claude -p` normal Pro kotasından harcanıyor. Yani otomatik deney resmi olarak destekleniyor ama 5 saatlik pencere ve haftalık sınır deneyin takvimini belirliyor. Pilotta gerçek "tur / pencere" sayısı ölçülmeden ana deney takvimi kesinleşmez.

Ek not: `claude --bare` abonelik girişini **kullanmıyor**, API anahtarı istiyor. Bu yüzden deneyde `--bare` kullanılamaz ve yapılandırma izolasyonu elle sağlanmalı (bkz. 3.3).

### 3.3 Deney kirlenmesi riski
`claude -p`, `--bare` olmadan kullanıcının `~/.claude` klasöründeki eklentileri, hook'ları, skill'leri, kullanıcı CLAUDE.md'sini ve otomatik hafızayı yükler. Örneğin geliştirme makinesine `security-guidance` ya da Semgrep eklentisi genel kurulursa **K0 koşulu bile korumalı çalışır** ve deney geçersizleşir.

**Önlem:** Her oturum temiz `HOME` ile Docker konteynerinde koşar; yalnızca o koşulun `.claude/settings.json` dosyası bağlanır; her oturumun başındaki `system/init` olayındaki `plugins`, `mcp_servers` ve `model` alanları beklenen "koşul parmak iziyle" karşılaştırılır, uymazsa oturum geçersiz sayılır.

### 3.4 Antigravity CLI hook'ları Claude Code'dan farklı
- `PostToolUse` çıktısı yalnızca `{}` olabiliyor; **ajana geri bildirim kanalı yok** ve aracın çıktısı da hook'a gelmiyor.
- Geri bildirim için `Stop` hook'unda `decision: "continue"` + `reason` ya da `PostInvocation` içinde `injectSteps` kullanılmalı.
- Varsayılan zaman aşımı 30 sn (Claude Code'da komut hook'u için 600 sn).
- Ağustos 2026'da Windows'ta Antigravity **IDE**'sinde `Stop` ve `PostToolUse` hook'larının hiç tetiklenmediği bildirildi; CLI için doğrulanmamış.
- Üçüncü taraf bir analiz `--dangerously-skip-permissions` bayrağının hook katmanını tamamen kapattığını iddia ediyor; deneyde bu bayrak yerine `permissions.allow` kuralları kullanılmalı ve iddia ilk hafta test edilmeli.

**Sonuç:** Adaptör katmanı mimarinin merkezinde olmalı ve Antigravity için ilk hafta bir **git/gitme (G0)** testi yapılmalı. Yedek: Codex CLI ya da Copilot CLI.

### 3.5 Claude Code hook'ları varsayılan olarak "fail-open"
Hook çökerse ya da zaman aşımına uğrarsa işlem devam eder. Güvenlik kapısı için `"onFailure": "block"` (Claude Code v2.1.295+) zorunlu. Deneyde Claude Code sürümü sabitlenmeli.

### 3.6 Takvim çakışması: Ocak finalleri ve araç dondurma
Yol haritasına göre ana deney Şubat–Mart, yani araç en geç **Ocak sonunda dondurulmalı**. Derleyici ve defter için yalnızca Aralık–Ocak var ve Ocak'ta final sınavları var. Plan bu yüzden derleyici ve defterin "dikey dilim" olarak Kasım'da başlamasını öneriyor (bkz. `03_IS_PAKETLERI.md`).

### 3.7 TÜBİTAK 2209-A son günü 11 Kasım 2026, 17:30
Bugünden 18 gün sonra. Başvuru yapılacaksa danışman onayı dahil hazırlık **bu hafta** başlamalı. İş paketi WP0.

## 4. Deney tasarımına yönelik mühendislik eleştirileri

1. **H1 karşılaştırması elma-armut olabilir.** 2608.23550'deki %4–16 yalnızca ajanın *yerleşik* kontrolleriyle (izin ayarları) zorlanabilirliği ölçüyor. Bizim derleyici SAST ve test katmanı ekliyor. Rapor iki sayıyı ayrı vermeli: (a) aynı tanımla yalnızca izin katmanı, (b) genişletilmiş tanımla üç katman.
2. **"Hatırlatma etkisi" karıştırıcısı.** K3/K4'te ajan her turda bulgu mesajı alıyor; etki deterministik kontrolden değil, kuralın tekrar bağlama girmesinden gelebilir. Ucuz bir kontrol koşulu: **K1b**, kuralların her turda `UserPromptSubmit` hook'u ile yeniden enjekte edilmesi. Hakemin ilk soracağı şeylerden biri. Karar listesinde.
3. **Aşırı uyum (overfitting).** Aracı ve senaryoları aynı kişiler yazıyor. Önlem: 6 senaryonun 2'si geliştirme, 4'ü test senaryosu; araç test senaryolarında hiç denenmeden dondurulur (git etiketi `v0.9-deney`).
4. **Exploit yazım yanlılığı.** Yeni turlar için exploit'ler araç dondurulmadan **önce** ve koşullardan bağımsız yazılmalı; ön kayıt (OSF) belgesine eklenmeli.
5. **Tur tanımı netleşmeli.** Öneri: bir tur = bir kullanıcı istemi = bir `claude -p --resume <id>` çağrısı. Defter anlık görüntüsü tur sonunda (`Stop`) alınır; `PostToolUse`'ta yalnızca hızlı artımlı kontrol yapılır.
6. **Defterin referansı "bir önceki tur" değil, "şimdiye kadarki en yüksek koruma" olmalı.** Aksi halde 3. turda silinen koruma 4. turda "değişiklik yok" görünür.
7. **Model sürümü sabitlenmeli** (`--model <tam kimlik>`), her turda `system/init` içinden kaydedilmeli.
8. **Karma etkili lojistik model için Python zayıf.** Analiz R (`lme4` / `glmmTMB`) ile yapılmalı; güç analizi de model üzerinden simülasyonla tekrar hesaplanmalı (yol haritasındaki %68 bağımsız örneklem varsayımı).

## 5. Kapsam dışı (yol haritasıyla aynı)
Türkçe prompt sorusu, GitHub saha çalışması (AIDev), Python dışı diller, Flask/FastAPI dışı framework'ler.

## 6. Karar bekleyen konular
Ayrıntı ve öneriler `DECISIONS.md` içinde "Açık" durumundaki kayıtlarda. Özet:
1. TÜBİTAK 2209-A başvurusu (son gün 11 Kasım).
2. K2b (`security-guidance` eklentisi) ve K1b (kural yeniden enjeksiyonu) koşulları eklensin mi, eklenirse tekrar sayısı nasıl dengelenir?
3. Antigravity G0 testinden geçemezse ikinci ajan: Codex CLI mı Copilot CLI mı?
4. Panel teknolojisi (statik HTML raporu mu, Streamlit mi, React mi).
5. Araç adı.

## 7. Dosya haritası

| Dosya | İçerik | Sahibi (ajan) |
|---|---|---|
| `00_GENEL_BAKIS.md` | Bu dosya | sd-sef-muhendis (skill) |
| `01_MIMARI.md` | Bileşenler, IR şeması, adaptörler, repo düzeni | sistem-mimari |
| `02_DENEY_ALTYAPISI.md` | Harness, izolasyon, kayıt şeması, kota planı | deney-tasarimcisi, kaynak-planlayici |
| `03_IS_PAKETLERI.md` | WBS, kapılar, haftalık takvim, iş bölümü | sd-sef-muhendis |
| `04_TEST_VE_DOGRULAMA.md` | Aracın kendi test stratejisi, kalite kapıları | sistem-mimari, plan-denetcisi |
| `05_RISKLER.md` | Risk kaydı | hepsi, plan-denetcisi denetler |
| `06_CLAUDE_ARAC_SETI.md` | Claude'u bu projede verimli kullanmak için araçlar | — |
| `07_AJAN_EKIBI.md` | Planlayıcı ajanlar ve faz 2 ajanları | sd-sef-muhendis |
| `DECISIONS.md` | ADR kayıtları | herkes ekler |
| `PROGRESS.md` | Durum ve sıradaki işler | sd-sef-muhendis |

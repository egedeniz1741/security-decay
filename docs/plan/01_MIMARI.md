# 01 · Mimari

> Durum: taslak v0.1 · Sahibi: `sistem-mimari` ajanı · Değişiklikler `docs/adr/` altında ADR olarak kaydedilir.

## 1. Tasarım ilkeleri

1. **LLM yalnızca derlemede.** Derleme bir kez yapılır, çıktı diske yazılır, insan gözden geçirebilir. Çalışma zamanındaki her kontrol deterministiktir; prompt injection ile kapatılamaz.
2. **Ajandan bağımsız çekirdek, ince adaptörler.** Çekirdek normalize edilmiş olaylarla çalışır. Claude Code ve Antigravity farkları yalnızca adaptörde yaşar.
3. **Doğrulanmayan kural zorlanmaz.** İyi ve kötü örnekle test edilemeyen kural "tavsiye" olarak işaretlenir ve yalnızca bağlama eklenir.
4. **Hızlı yol / yavaş yol.** Her araç çağrısında yalnızca değişen dosyalarda ucuz kontrol (hedef p95 < 1,5 sn); tur sonunda tam defter anlık görüntüsü (hedef p95 < 8 sn). RQ4'ün %25 ek süre sınırı buna bağlı.
5. **Ajan aracın durumuna dokunamaz.** `.sdguard/` klasörü ve hook ayarları için yazma izni reddedilir; deneyde bu klasör konteynere salt okunur bağlanır.
6. **Fail-closed.** Güvenlik hook'ları `"onFailure": "block"` ile tanımlanır. Hook hatası sessizce geçmez, kayda girer.

## 2. Bileşenler

```
                    (bir kez)                                  (her turda)
 AGENTS.md ──► [1 Derleyici] ──► .sdguard/                ┌──────────────────────────┐
 CLAUDE.md      │  ayrıştır      ├─ rules.ir.json         │  Ajan (Claude Code / agy) │
                │  sınıflandır   ├─ semgrep/*.yaml        └──────────┬───────────────┘
                │  çevir (LLM)   ├─ semgrep/tests/*                  │ hook olayı (stdin JSON)
                │  doğrula       ├─ permissions.claude.json          ▼
                │                ├─ permissions.agy.json   [Adaptör] normalize ──► Event
                │                ├─ tests/security/*.py              │
                │                └─ advisory.md                      ▼
                                                          [2 Çekirdek motor]
                                                            ├─ Kural kontrolü (Semgrep, derlenmiş)
                                                            ├─ Invariant çıkarıcı (AST)
                                                            ├─ Defter (high-water mark, diff)
                                                            ├─ Yeni SAST bulgusu (yalnızca bu tur)
                                                            └─ Kurulum kontrolü (PyPI + OSV)
                                                                     │ Decision
                                                                     ▼
                                                          [Adaptör] ajana özgü JSON / exit code
                                                                     │
                                         .sdguard/state/<session>.jsonl ──► [3 CI + Panel]
```

### 2.1 Derleyici (`sdguard compile`)

| Aşama | Ne yapar | Nasıl |
|---|---|---|
| Ayrıştırma | Markdown'ı başlık ve madde düzeyinde parçalar; güvenlikle ilgili olanları seçer | Kural tabanlı ön filtre + LLM sınıflandırma |
| Atomikleştirme | "SQL parametreli olmalı ve kullanıcı girdisi loglanmamalı" → 2 kural | LLM, `--json-schema` ile yapılandırılmış çıktı |
| Katman ataması | eylem → izin; kod → Semgrep; davranış → pytest; muğlak → tavsiye | LLM önerir, kural tabanlı doğrulayıcı onaylar |
| Çeviri | Her katman için artefakt üretir | `claude -p --output-format json --json-schema <ir.schema.json>` |
| Doğrulama | Semgrep kuralı için `# ruleid:` ve `# ok:` işaretli iyi/kötü örnek, `semgrep --test`; pytest testi için güvenli ve güvensiz referans uygulamada beklenen sonuç; izin kuralı için simüle araç çağrısı | Deterministik |
| Onarım döngüsü | Doğrulama başarısızsa hata mesajıyla en fazla 2 yeniden deneme, sonra "tavsiye" | Sınırlı, kayda girer |

LLM çağrısı kullanıcının kendi ajan aboneliğiyle (`claude -p` ya da `agy -p`) yapılır; API anahtarı gerekmez.

### 2.2 Ara temsil (IR) taslağı

```json
{
  "id": "R-007",
  "source": {"file": "AGENTS.md", "line": 42, "text": "SQL sorguları her zaman parametreli olmalı"},
  "category": "code",
  "cwe": ["CWE-89"],
  "targets": {
    "semgrep": {"path": "semgrep/R-007.yaml", "test": "semgrep/tests/R-007.py"},
    "permission": null,
    "pytest": null
  },
  "validation": {"status": "verified", "good_examples": 3, "bad_examples": 3, "attempts": 1},
  "enforcement": "block",
  "compiled_by": {"agent": "claude-code", "model": "<kimlik>", "at": "2026-12-01T10:00:00Z"}
}
```

`enforcement`: `block` (kritik, turu bitirmeyi engeller), `warn` (geri bildirim), `advise` (yalnızca bağlam). Şema `pydantic` ile tanımlanır, JSON Schema'sı derleyicinin `--json-schema` girdisi olur.

### 2.3 Invariant defteri

**Çıkarılan durum (Flask / FastAPI):**

| Invariant | Çıkarım yöntemi | Kimlik anahtarı |
|---|---|---|
| Rota → kimlik doğrulama | Flask: dekoratörler (`@login_required`, özel dekoratörler derlenmiş listeden); FastAPI: `Depends(...)` parametreleri ve router düzeyi bağımlılıklar | `(method, path)`; yol değişirse handler adı ile bulanık eşleme |
| Rota → sahiplik kontrolü | Handler gövdesinde kaynak sahibi alanının mevcut kullanıcıyla karşılaştırılması ya da sorguya `user_id` filtresi | `(method, path)` |
| Sorgu biçimi | `execute()` / `text()` çağrılarında f-string, `%`, `+`, `.format` kullanımı | dosya + fonksiyon + çağrı sırası |
| Yapılandırma | `DEBUG`, `SECRET_KEY` sabiti, CORS `origins`, CSRF koruması, cookie bayrakları | anahtar adı |
| Bağımlılıklar | `requirements*.txt`, `pyproject.toml` farkı | paket adı |

**Kural:** Defter her invariant için şimdiye kadar görülen **en yüksek koruma düzeyini** tutar. Mevcut tur bu düzeyin altına düşerse regresyon olur. Kullanıcı istemi korumanın kaldırılmasını açıkça istiyorsa (ör. "bu endpoint herkese açık olsun") regresyon "onaylı" işaretlenir. Bunu tespit etmek LLM gerektirdiği için ilk sürümde istem metninde anahtar kelime eşlemesi ve elle etiket; deneyde senaryo istemleri bunu içermeyecek şekilde yazılır.

Uygulama: `ast` + `libcst` (kaynak konumu korunur), fazla dinamik kodda (ör. `app.add_url_rule` döngüde) "çıkarılamadı" işareti, yanlış alarm yerine bilinmeyen.

### 2.4 Normalize olay ve karar şeması

```python
class Event(BaseModel):
    agent: Literal["claude-code", "antigravity"]
    session_id: str
    turn_idx: int
    kind: Literal["pre_tool", "post_tool", "turn_end", "session_start"]
    tool: ToolCall | None          # ad + argümanlar
    changed_files: list[str]
    cwd: str

class Decision(BaseModel):
    action: Literal["allow", "deny", "feedback", "block_stop", "noop"]
    findings: list[Finding]        # kural ihlali, koruma kaybı, yeni SAST, yasak eylem
    agent_message: str | None      # ajana gidecek yapılandırılmış metin
```

### 2.5 Adaptör eşleme tablosu

| Normalize | Claude Code | Antigravity CLI |
|---|---|---|
| `pre_tool` + `deny` | `PreToolUse` → `hookSpecificOutput.permissionDecision: "deny"` + gerekçe | `PreToolUse` → `decision: "deny"` + `reason` |
| `post_tool` + `feedback` | `PostToolUse` → `hookSpecificOutput.additionalContext` (ya da exit 2 + stderr) | **Kanal yok**, `{}` dönmek zorunlu. Bulgu kuyruğa yazılır, tur sonunda verilir |
| `turn_end` + `block_stop` | `Stop` → `decision: "block"` + `reason`; `stop_hook_active` ile döngü sınırı | `Stop` → `decision: "continue"` + `reason`; ardışık devam sınırı var |
| `turn_end` + `feedback` | `Stop` hook'unda `systemMessage` ya da bir sonraki `UserPromptSubmit`'te bağlam | `Stop` / `PostInvocation.injectSteps` (G0'da doğrulanacak) |
| Hook hatası | `"onFailure": "block"` | Belgelerde net değil, G0'da test |
| Yapılandırma yeri | `.claude/settings.json` | `.agents/hooks.json` + `settings.json` izinleri |

Bu tablodaki her satır `hook-entegrasyon-analisti` ajanının G0 spike'ında gerçek bir koşumla doğrulanmadan "kesin" sayılmaz.

### 2.6 CI ve panel
- `sdguard check --sarif out.sarif`: aynı derlenmiş Semgrep kurallarını ve güvenlik testlerini çalıştırır. GitHub Action kompozit eylem olarak paketlenir, `github/codeql-action/upload-sarif` ile Code Scanning'e yüklenir.
- Panel: `.sdguard/state/*.jsonl` + deney kayıtlarını okuyup tur tur zaman çizelgesi üretir. Teknoloji açık karar (ADR-0006).

## 3. Teknoloji yığını (öneri)

| Alan | Seçim | Gerekçe |
|---|---|---|
| Dil | Python 3.12 | BaxBench 3.12 istiyor; hedef framework'ler Python |
| Paket / ortam | `uv` | Hızlı, kilit dosyası, `uvx` ile MCP sunucuları da aynı araçla |
| Şema | `pydantic` v2 | IR + JSON Schema üretimi |
| AST | `ast`, `libcst` | Konum koruyan dönüşüm, mutasyon operatörleri için de |
| SAST | Semgrep CE (CLI), isteğe bağlı CodeQL CLI | Ücretsiz, `--test` ile kural testi |
| Test | `pytest`, `hypothesis` (özellik tabanlı testler için) | — |
| Kalite | `ruff`, `mypy`, `pre-commit`, Gitleaks | Kullanıcının alıştığı DevSecOps kapıları |
| Konteyner | Docker (WSL2 üstünde) | Claude Code sandbox'ı yerel Windows'ta çalışmıyor; deney izolasyonu |
| Analiz | R (`lme4`, `glmmTMB`, `survival`) + Python (`pandas`, `duckdb`) | Karma etkili modeller R'da olgun |
| Kayıt | JSONL (ham) → Parquet / DuckDB (analiz) | Basit, sürümlenebilir |

## 4. Repo düzeni (öneri)

```
security-decay/
├─ CLAUDE.md                     # Claude Code proje hafızası
├─ .claude/agents/               # planlayıcı ve geliştirici ajanlar
├─ .claude/skills/               # orkestra şefi skill'i
├─ docs/plan/                    # bu plan
├─ docs/adr/                     # mimari karar kayıtları
├─ sdguard/                      # ürün (Python paketi)
│  ├─ ir/  compiler/  ledger/  checks/  adapters/{claude_code,antigravity}/  cli.py
│  └─ tests/
├─ harness/                      # deney düzeneği
│  ├─ scenarios/  prompts/  conditions/{K0..K4}/  docker/  runner/  exploits/
├─ corpus/                       # RQ1 toplama ve etiketleme betikleri (veri gitignore)
├─ mutants/                      # RQ3 mutasyon operatörleri
├─ analysis/                     # R ve Python analiz kodu
├─ action/                       # GitHub Action
└─ data/                         # gitignore; sürümler GitHub Release / Zenodo
```

Ürün ve deney ayrı paketler: deney düzeneği ürünü bağımlılık olarak sabit sürümle kullanır. Böylece "araç dondurma" bir sürüm etiketi demektir.

## 5. Açık mimari sorular
1. Defter durumu dosyada mı (JSONL) yoksa SQLite'ta mı? İlk öneri JSONL; eşzamanlı yazım yok.
2. Semgrep her `PostToolUse`'ta yeniden başlatılırsa süre (~1–3 sn) RQ4'ü zorlar. Alternatif: tur sonunda tek tarama + `PostToolUse`'ta yalnızca AST tabanlı hızlı kontroller. Pilotta ölçülecek.
3. Antigravity'de `PostToolUse` aracın çıktısını vermiyor; değişen dosyaları bulmak için tur başı/sonu git anlık görüntüsü farkı kullanılmalı.

# 06 · Claude'u bu projede verimli kullanmak için araç seti

> Araştırma tarihi: 24 Ekim 2026. Sürüm numaraları ve komutlar hızlı değişiyor; kurmadan önce kaynak linkinden kontrol edin.

## 0. Altın kural: güvenlik araçlarını **asla kullanıcı kapsamına (user scope) kurmayın**

Bu projenin deneyi "ajan hangi korumayla çalışıyor" sorusunu ölçüyor. `claude -p` varsayılan olarak `~/.claude` içindeki eklentileri, hook'ları ve skill'leri yükler. Semgrep, `security-guidance` ya da Trail of Bits güvenlik eklentileri kullanıcı kapsamına kurulursa deneyin K0 koşulu bile korumalı çalışır.

- Geliştirme repo'sunda: **proje** ya da **yerel** kapsam (`claude plugin install ... --scope project|local`).
- Deney konteynerlerinde: hiçbir eklenti yok, yalnızca koşulun kendi ayar dosyası.
- `security-guidance` ve Semgrep Guardian yalnızca rakip analizi ve K2b koşulu için, ayrı bir klasörde.

## 1. Hemen kurulacaklar

| Araç | Ne işe yarar bu projede | Kurulum | Maliyet / not |
|---|---|---|---|
| **WSL2 + Docker Desktop** | Claude Code'un komut sandbox'ı yerel Windows'ta çalışmıyor; deney izolasyonu ve BaxBench Docker istiyor | `wsl --install`, Docker Desktop WSL2 entegrasyonu | Ücretsiz |
| **Claude Code CLI (WSL2 içinde)** | Ana geliştirme ve deney ajanı | Resmi kurulum betiği; deney imajında sürüm sabitlenir, `DISABLE_AUTOUPDATER=1` | Pro aboneliği |
| **VS Code + Claude Code eklentisi** | Diff'leri ve plan modunu görsel izlemek | VS Code Marketplace | Ücretsiz |
| **`uv`** | Python ortamı; MCP sunucularını `uvx` ile çalıştırmak | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | Ücretsiz |
| **`pyright-lsp`** (resmi eklenti) | Claude her düzenlemeden sonra tip hatalarını görür, tanıma/referansa gider; `sdguard` geliştirmede büyük kazanç | `pip install pyright` (ya da npm) sonra `/plugin install pyright-lsp@claude-plugins-official` | Ücretsiz; bulut oturumlarında LSP çalışmaz |
| **Semgrep CE (CLI)** | Derleyicinin hedefi ve doğrulayıcısı (`semgrep --test`), K2 taban çizgisi | `uv tool install semgrep` | Ücretsiz, giriş gerekmez |
| **Trail of Bits skill pazarı** | `semgrep-rule-creator` (derleyicinin yapacağı işin uzman tarifi), `static-analysis` (Semgrep/CodeQL/SARIF), `property-based-testing` (hypothesis), `insecure-defaults`, `differential-review` | `/plugin marketplace add trailofbits/skills` → `/plugin` menüsünden seç, **proje kapsamı** | Ücretsiz; deney konteynerine girmez |
| **arXiv MCP / eklentisi** | Literatür taraması, makaleyi LaTeX kaynağından bölüm bölüm okuma, BibTeX | `claude plugin marketplace add blazickjp/arxiv-mcp-server` → `claude plugin install arxiv-mcp-server@arxiv-mcp` (yalnızca MCP: `claude mcp add --transport stdio --scope user arxiv -- uvx arxiv-mcp-server`) | Ücretsiz; npm'deki aynı adlı paket ilgisiz, kullanmayın |
| **`ccusage`** | Yerel Claude Code kayıtlarından token ve pencere tüketimi; pilotta kota ölçümü (R3) | `npx ccusage@latest` | Ücretsiz |

## 2. Faydalı, ihtiyaç olunca

| Araç | Ne işe yarar | Kurulum | Not |
|---|---|---|---|
| `plugin-dev` (resmi) | `sdguard`'ı Claude Code eklentisi olarak paketlemek (hook + skill + komut tek pakette); dağıtım için en temiz yol | `/plugin install plugin-dev@claude-plugins-official` | WP5 / WP11 |
| `agent-sdk-dev` (resmi) | Runner'ı `claude -p` yerine Python Agent SDK ile yazarsanız | `/plugin install agent-sdk-dev@claude-plugins-official` | SDK kullanımı da Pro kotasından düşer |
| `github` (resmi) | Issue, PR, Action log'larına Claude'dan erişim | `/plugin install github@claude-plugins-official` | — |
| `commit-commands`, `pr-review-toolkit` (resmi) | Commit/PR akışı, PR inceleme ajanları | `/plugin install <ad>@claude-plugins-official` | İki kişilik ekipte PR disiplini için |
| Context7 MCP | Flask, FastAPI, Semgrep, libcst gibi kütüphanelerin güncel belgeleri | `claude mcp add` ile (upstash/context7) | Model bilgisindeki eski API'leri önler |
| Zotero MCP | Kaynakça yönetimi, tez kaynakçası | `uvx zotero-mcp@latest` (kujenga/zotero-mcp), Zotero'da yerel API açık | Ücretsiz |
| CodeQL CLI | İkinci SAST, `static-analysis` skill'i ile | GitHub'dan | Araştırma/açık kaynak için ücretsiz |
| Semgrep MCP | Claude'un Semgrep'i araç olarak çağırması, kural şeması | Eski `semgrep/mcp` reposu Ekim 2025'te arşivlendi; sunucu artık ana `semgrep` ikilisinde | Komutu güncel belgeden doğrulayın |

## 3. Yalnızca rakip analizi ve K2b koşulu için

| Araç | Neden dikkat | Kullanım |
|---|---|---|
| `security-guidance` (Anthropic resmi) | Her yazımda desen taraması + tur sonunda diff'in model incelemesi + commit öncesi ajan incelemesi; `.claude/claude-security-guidance.md` ve `.claude/security-patterns.yaml` ile projeye özel kural. **Projenin en yakın rakibi.** Model incelemeleri kotadan harcar | Ayrı bir klasörde dene, davranışını `docs/research/rakip-security-guidance.md`'ye yaz; K2b koşulu bu eklentiyle |
| Semgrep Guardian (Claude Code eklentisi) | Semgrep girişi istiyor, dosyaları `scanner.semgrep.ai`'ye gönderiyor | Yalnızca rakip analizi; deneyde kullanma |
| `anthropics/claude-code-security-review` Action | PR güvenlik incelemesi; API anahtarı istiyor | Bütçe nedeniyle önerilmez; ilgili çalışma olarak tezde anılır |

## 4. Claude.ai tarafı (bu Project)

- **Project bilgi tabanı:** `docs/plan/` dosyalarının kopyası burada; claude.ai sohbetlerinde de plana erişilir. Plan değişince yeniden yüklenir.
- **Araştırma (Research) modu:** Haftalık literatür taraması için; Google Scholar'ın resmi API'si olmadığından arXiv MCP + web araması birlikte.
- **Bilgisayara bağlı oturum:** Bu oturum `Desktop\security-decay` klasörüne yazabiliyor; uzun deney koşumları ise WSL2'de Claude Code CLI ile yapılmalı (masaüstü bağlantısı ve bulut oturumu deney ortamı değildir).

## 5. Önerilen Claude Code ayarları (geliştirme repo'su)

```jsonc
// .claude/settings.json (proje, commit edilir)
{
  "permissions": {
    "deny": ["Read(./.env)", "Read(./.env.*)", "Read(./data/raw/**)", "Edit(./harness/exploits/locked/**)"]
  },
  "env": {
    "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2"
  }
}
```

- **Model seçimi ve kota:** Pro'da Opus kotayı daha hızlı tüketir. Ajan dosyalarında: mimari, deney tasarımı ve istatistik `opus`; tarama, denetim ve rutin işler `sonnet`. Ana oturum çoğu zaman Sonnet yeter.
- **Plan modu:** Büyük değişiklikten önce `Shift+Tab` ile plan modu; ajanların çıktısı önce plan dosyasına, sonra koda.
- **Subagent derinliği:** Planlayıcıların başka ajan doğurmasına gerek yok; derinlik 2 yeterli, kotayı korur.

## 6. Yapılmaması gerekenler
1. Güvenlik eklentilerini kullanıcı kapsamına kurmak (bkz. §0).
2. Deneyde `--bare` kullanmak: abonelik girişini okumaz, API anahtarı ister.
3. Deneyde Antigravity için `--dangerously-skip-permissions` (hook katmanını kapattığı bildiriliyor).
4. Abonelik OAuth belirtecini kendi HTTP istemcinizde kullanmak: hem Anthropic hem Google için desteklenmeyen kullanım. Yalnızca resmi CLI'ları alt süreç olarak çalıştırın.
5. Claude Code'u deney ortasında güncellemek.

## Kaynaklar
- [Claude Code subagents belgesi](https://code.claude.com/docs/en/sub-agents.md)
- [Claude Code hooks referansı](https://code.claude.com/docs/zh-TW/hooks) ve [hooks özeti](https://claude.nagdy.me/learn/hooks/)
- [Claude Code headless / `claude -p`](https://code.claude.com/docs/en/headless)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code sandboxing](https://code.claude.com/docs/en/sandboxing.md)
- [Eklenti keşfi ve resmi pazar](https://code.claude.com/docs/en/discover-plugins.md)
- [security-guidance eklentisi incelemesi (SOCFortress)](https://socfortress.medium.com/anthropics-new-security-plugin-72fae3180c6e), [CLAUDE.md güvenlik kuralları ve eklenti (DEV)](https://dev.to/olivia_craft/claudemd-security-rules-what-to-add-now-that-claude-code-reviews-your-code-3kcf)
- [Agent SDK kredisi askıya alındı / plan durumu (AI Catchup)](https://aicatchup.com/news/claude-agent-sdk-monthly-credit-paid-plans), [Totalum özeti](https://www.totalum.app/blog/claude-agent-sdk-credits-2026), [multica issue #2563](https://github.com/multica-ai/multica/issues/2563), [Anthropic yardım makalesi](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
- [Trail of Bits skills](https://github.com/trailofbits/skills)
- [Semgrep MCP (arşivlendi)](https://github.com/semgrep/mcp), [Semgrep Guardian eklentisi](https://github.com/semgrep/mcp-marketplace)
- [Antigravity CLI hooks](https://antigravity.google/docs/hooks?tab=cli), [headless mod](https://antigravity.google/docs/cli/headless/), [hook kontrol modeli analizi](https://agenticcontrolplane.com/controls/antigravity), [Windows IDE hook hatası](https://discuss.ai.google.dev/t/stop-and-posttooluse-hooks-in-agents-hooks-json-never-fire-antigravity-ide-1-107-0-windows/178288), [headless orkestrasyon sorusu](https://discuss.ai.google.dev/t/is-external-orchestration-of-antigravity-cli-headless-mode-supported-with-account-based-usage/183051)
- [BaxBench reposu](https://github.com/logic-star-ai/baxbench), [AutoBaxBuilder](https://github.com/eth-sri/AutoBaxBuilder), [IterBench](https://github.com/djscherrer/IterBench), [BaxBench duyurusu](https://logicstar.ai/news/baxbench)
- [arXiv MCP sunucusu](https://www.claudepluginhub.com/plugins/blazickjp-arxiv-mcp-server), [Zotero MCP](https://pypi.org/project/zotero-mcp/), [ccusage](https://npmjs.com/package/ccusage)
- Yakın çalışmalar (literatür takibi için): [A Deterministic Control Plane for LLM Coding Agents (2606.26924)](https://arxiv.org/html/2606.26924v1), [Harness-IF (2608.11727)](https://arxiv.org/abs/2608.11727)

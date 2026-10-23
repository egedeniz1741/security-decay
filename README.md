# Security Decay

Graduation project, Computer Engineering, Kocaeli University (2026–2027).

Coding agents tend to lose security over multi-turn sessions, and the security rules developers write in agent instruction files (AGENTS.md, CLAUDE.md) are mostly not enforced. This project builds:

- **A rule compiler** that turns those security rules into verified, deterministic checks: agent permission settings, Semgrep rules and pytest security tests.
- **A security invariant ledger** that runs as an agent hook and detects when protections established earlier in a session (auth checks, parameterized queries, ownership checks, secure config) disappear in later turns.
- **A controlled multi-turn experiment** (based on BaxBench) that measures, with real exploits, how much each approach reduces security decay: no guard, written rules, generic SAST hook, compiled rules, compiled rules + ledger.

Working name of the tool: `sdguard`. Target agents: Claude Code (primary) and Antigravity CLI. Scope: Python web backends (Flask / FastAPI).

**Status:** Planning phase. Product code starts after the G0 gate (November 8, 2026).

## Where to start
The planning documents are currently written in Turkish.

1. [`docs/plan/00_GENEL_BAKIS.md`](docs/plan/00_GENEL_BAKIS.md): goals, deliverables, critique of the roadmap
2. [`docs/plan/03_IS_PAKETLERI.md`](docs/plan/03_IS_PAKETLERI.md): work packages, gates, timeline
3. [`docs/plan/PROGRESS.md`](docs/plan/PROGRESS.md): current status and next tasks
4. [`docs/plan/DECISIONS.md`](docs/plan/DECISIONS.md): decision log

## Working with Claude Code
- Planner subagents: `.claude/agents/` (10 agents, see [`docs/plan/07_AJAN_EKIBI.md`](docs/plan/07_AJAN_EKIBI.md))
- Orchestrator skill: `/sd-sef-muhendis`
- Recommended tools and setup: [`docs/plan/06_CLAUDE_ARAC_SETI.md`](docs/plan/06_CLAUDE_ARAC_SETI.md). Do **not** install security plugins at user scope; it contaminates the experiment conditions.

# BountyCharts — TCG Market Research

Research and analysis supporting a TCG content/data property.

## Contents

| Document | What it is |
|---|---|
| [`docs/tcg-deep-dive-2026.md`](docs/tcg-deep-dive-2026.md) | **Start here.** Strategic analysis of the 2024–2026 TCG market, the four structural flaws in the source intelligence report, and a corrected roadmap. |
| [`docs/fact-check-ledger.md`](docs/fact-check-ledger.md) | Claim-by-claim audit of the source report — 38 claims, each verified, corrected or flagged unsourced. |
| [`models/unit_economics.py`](models/unit_economics.py) | Runnable funnel model. Every revenue figure in the deep dive traces back to an assumption here. |
| [`prompts/agency-handoff-prompt.md`](prompts/agency-handoff-prompt.md) | Verbatim Claude Code prompt that stands up an 18-agent build agency with a gated handoff protocol. |
| [`site/`](site/) | The deployable static site for `bountycharts.com`. |
| [`docs/deployment/cloudflare.md`](docs/deployment/cloudflare.md) | Runbook for taking the site live on Cloudflare Pages. |

## Quick start

```bash
python3 models/unit_economics.py                                    # baseline
python3 models/unit_economics.py --first-click-win-rate 1.0         # naive affiliate assumption
python3 models/unit_economics.py --digital-share 0.8 --sessions 100000   # Pokémon-Pocket-led traffic
```

No dependencies — standard library only.

Preview the site locally:

```bash
python3 -m http.server 8899 --directory site   # then open http://127.0.0.1:8899
```

## Findings in one paragraph

The source report describes the market well and plans against it poorly. Its reporting on the Altered TCG collapse is sharp, and it correctly identifies TCGplayer's 48-hour **first-click** attribution as a binding constraint — a detail most affiliate directories get wrong. But its plan rests on four premises that do not hold: the TCGplayer API it builds on has been closed to new developers since roughly late 2024; its #1 growth vector (Pokémon TCG Pocket) is digital-only and therefore has **zero** affiliate surface in the lowest-RPM major ad vertical; the "tooling void" it targets is occupied by 5–10 free competitors per game, one of them publisher-official; and its pricing sits 2.5–5× above category leaders EDHREC ($2/mo) and Moxfield ($1/mo). Corrected, the opportunity is real but differently shaped: lead with **Riftbound** (permissive IP policy, active secondary market, thin information layer), monetize **affiliate first / ads second / subscriptions third**, and treat Pokémon as free top-of-funnel only — its licence is explicitly non-commercial and enforcement is triggered by monetization.

## Method

Claims were verified against primary sources where reachable (publisher IR filings, TCGplayer developer documentation, The Pokémon Company International media guidelines, Equinox's own closure statement) and against trade press otherwise. Where a claim could not be substantiated it is marked unsourced rather than repeated. Full source list is at the end of the deep dive.

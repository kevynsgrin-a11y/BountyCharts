# Post-audit scorecard — August 2026

Grading the deployed front end against the standard a Fortune 500 build would be held to, after the
August 2026 audit and its fixes. Every score is anchored to a measurement, not an impression.

**Graded commit:** `bfca67a` plus the fixes on this branch
**Companion documents:** [`frontend-audit-2026-08.md`](frontend-audit-2026-08.md) ·
[`content-and-image-spec-2026-08.md`](content-and-image-spec-2026-08.md)

---

## Grade: **F — 59.0 / 100**

| Dimension | Weight | Score | Evidence |
|---|---:|---:|---|
| Accessibility (WCAG 2.2 AA) | 15% | 54 | 7 AA failures in the **default** light theme, including the only interactive element on the site (4.31:1). Dark theme passes. No automated a11y in CI. `<main>` was missing until this audit. |
| Engineering, CI & testing | 13% | 66 | 0 → 26 tests; the gate now tests behaviour rather than presentational strings; CI runs the suite and smoke-tests the model. No e2e, visual-regression, a11y or lint automation. |
| Performance & Core Web Vitals | 12% | 84 | **3,179 B brotli, 1 request, 76 DOM nodes, LCP 64–72 ms, CLS 0.0000 over zero shifts.** Elite in absolute terms. No RUM, no enforced budget, no production CWV (site not live). |
| Security & compliance posture | 12% | 80 | CSP without `unsafe-inline`, HSTS preload, `frame-ancestors 'none'`, COOP, nosniff, Permissions-Policy, zero third parties. No privacy/terms/affiliate-disclosure pages. |
| Content & information architecture | 12% | 44 | 2 pages, 1 outbound link, no call to action, no launch-notify path. The research the page advertises as "finished and public" is not linked from the page. |
| Visual design & design system | 11% | 61 | Exact 7 × 64 px rhythm and a properly tuned dark palette. But 12 distinct type sizes with adjacent ratios from 1.029 to 2.667, tokens declared 8× across 2 files, no documented system. |
| SEO & discoverability | 8% | 58 | Title, description, canonical and JSON-LD correct; sitemap now carries `lastmod`. No `og:image`, bare `WebSite` node, no `Organization`. |
| Brand & identity assets | 7% | 33 | Wordmark is a text glyph. No logo file, no share card, no icon set; favicon is an inline emoji `data:` URI. |
| Observability & operations | 6% | 22 | No RUM, no error tracking, no uptime monitoring, no alerting. The deploy job silently skips because credentials are unset. |
| Readiness for change | 4% | 60 | The gate no longer misreports refactors as regressions, and tests exist. No build step; tokens duplicated across two files. |
| **Weighted total** | **100%** | | **59.0** |

---

## The result that matters more than the letter

Re-scored under a **pre-launch one-pager** weighting — relieving observability and brand assets,
raising accessibility and content, same underlying scores — the site earns **61.6 / 100 (D−)**.

| Standard | Score | Grade |
|---|---:|---|
| Fortune 500 build | 59.0 | **F** |
| Pre-launch one-pager | 61.6 | **D−** |

**Re-weighting moves it 2.6 points.** That is the finding. The instinctive defence — "it's a small
pre-launch site, of course it lacks enterprise scaffolding" — does not hold, because the dimensions
it scores worst on (accessibility 54, content 44) are the ones that gain weight when judged as a
one-pager, not lose it. Nothing about being small excuses a 4.31:1 link or a page that will not tell
a visitor what to do next.

## What the grade is not saying

The delivery layer is genuinely excellent and would survive review at any company:

- **3.2 KB on the wire in a single request**, LCP under 75 ms, and **CLS of exactly zero across zero
  layout shifts** — the last of which is hard to achieve and easy to destroy.
- **Renders completely with JavaScript disabled**, because it ships none.
- **No horizontal overflow at any viewport** from 320 px to 1920 px.
- A security posture with no third parties, no cookies and no trackers.

The gap is not craft. It is that an unusually well-built delivery layer is wrapped around a thin,
partly inaccessible content layer. The five highest-leverage fixes are ranked in the audit; the
first two — the light-theme palette and the `data-theme` decision — are worth roughly 15 points of
this score between them.

## How to move the number

| Action | Dimensions moved | Approx. gain |
|---|---|---|
| Fix light-theme contrast (draft hex values in the audit) | Accessibility 54 → 85 | **+4.7** |
| Link the research; add a launch-notify path; ship `/method` | Content 44 → 72 | **+3.4** |
| Ship the `og:image`, favicon set and brand mark | Brand 33 → 78, SEO 58 → 75 | **+4.5** |
| Add automated a11y + visual regression to CI | Engineering 66 → 82 | **+2.1** |
| Add uptime and error monitoring at launch | Observability 22 → 70 | **+2.9** |

All five would put the site at roughly **76 / 100 (C+)** on the Fortune 500 curve — a realistic
pre-launch target, and an honest one. An A on that curve is not a sensible goal for a project at
this stage, and chasing it would mean building scaffolding this site does not yet need.

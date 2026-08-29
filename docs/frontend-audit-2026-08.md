# Front-end audit — August 2026

Full top-to-bottom audit of the deployed front end: design and function, every page, every
viewport. Findings were produced across six lenses plus four checks that reviews usually skip,
then re-verified against source before being written down.

**Audited commit:** `0991dfd` (branch `claude/frontend-audit-fixes-0b7b2j`)
**Date:** 2026-08-08

---

## Evidence coverage

Capabilities established before anything was measured:

| Capability | Status |
|---|---|
| Build and serve the site locally | **Yes.** No build step exists; `site/` served over `python3 -m http.server` at `127.0.0.1:8899`. |
| Drive a real browser | **Yes.** Playwright + Chromium 1194 (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`). All pixel values, contrast ratios, accessibility trees and print output below came from it. |
| Fetch the live public URL | **No.** `bountycharts.com`, `www.bountycharts.com` and `bountycharts.pages.dev` are all blocked by the network egress proxy (403 on CONNECT), via both `curl` and the fetch tool. |

**Lenses degraded by the missing live URL:**

- **Cache and header behaviour.** `site/_headers` is a Cloudflare Pages instruction file. Nothing
  local applies it, so every claim about response headers is read from the file, never measured
  against a real response. Finding **L5** is INFERRED for exactly this reason.
- **404 status codes.** `python3 -m http.server` does not serve `404.html` for missing paths. The
  404 page was audited by loading it directly; that it is actually served with a 404 status in
  production is untested.
- **Redirect behaviour.** `site/_redirects` and the documented apex/www canonicalisation are edge
  concerns that cannot be exercised locally.
- **Cross-browser.** Chromium only. The CSP finding (**M3**) and the SVG-favicon question are
  Chromium-verified and explicitly not confirmed in Safari or Firefox.

Deploy history was checked instead: three workflow runs exist, the most recent green on `main`.
Cloudflare credentials are not configured, so the deploy job takes its skip path.

> **Superseded 2026-08-28.** A Cloudflare Pages deployment now exists — see **C3** below. The
> statement originally here, that there may be no live site at all, is no longer true. The live URL
> is still unreachable from this session (egress-blocked, 403 CONNECT on both `curl` and the fetch
> tool, retested against the new preview URLs), so the local measurements remain the authoritative
> ones — but now because of a network restriction, not because nothing is deployed.

### A note on method

This audit was commissioned to run as a fan-out of parallel audit agents. That was attempted: a
14-agent workflow (6 lenses, 4 special checks, 3 adversarial verifiers, 1 synthesiser) ran for
13 minutes and **failed completely**. Every subagent hit a harness defect that blanked the
arguments of every tool call before it reached the tool — `Read` lost `file_path`, `Bash` lost
`command`, and the structured-output call lost its whole payload. Across all 14 agents: **128
tool calls rejected, 2 succeeded** (both zero-parameter calls). No subagent executed a single
parameterised tool, so none of them measured anything.

The failure is deterministic rather than flaky, so it was not retried. Every finding below was
therefore measured directly, in the main session, where tools work normally. Nothing in the
original 20 findings came from an agent.

> **Scope note, 2026-08-28.** That statement covers the original 20 findings only. Two later
> additions do involve agent work, and say so where they appear: the **H1** draft correction was
> caught by an adversarial verifier during the content-and-image specification pass (and
> re-measured here before being accepted), and **C3** was found by me from this PR's own deploy
> records. A separate 12-agent run for that specification completed 12/12.

### Evidence grades

| Grade | Count | Meaning |
|---|---:|---|
| MEASURED | 16 | Code executed, browser driven, or value computed. The number is in the finding. |
| OBSERVED | 3 | Read directly in source, cited to the line. |
| INFERRED | 1 | Reasoned from code not executed. States what would confirm it. |

*(Counts cover the original 20 findings. **C3**, added 2026-08-28, is MEASURED — its
deploy-ordering timeline was observed directly.)*

No finding at high severity or above rests on inference alone. **11 candidate findings were
discarded** during re-verification — listed at the end, because what failed to survive is as
informative as what did.

---

## Verdict

### What is genuinely good here

This is a better-built page than most audits get to open with, and the specifics matter because a
redesign could easily destroy them without noticing.

- **It is 3.2 KB on the wire, in one request.** Measured: 1 HTTP request; `index.html` is 11,657 B
  raw and **3,179 B brotli q11 (27.3%)**, which is the production wire cost; 76 DOM elements;
  `loadEventEnd` median 21.9 ms. No framework, no build step, no external asset, no font download,
  no tracker, no cookie banner. A redesign that adds a CSS framework and a web font will be many
  times the weight before it renders a single new idea.

  > **Corrected 2026-08-28.** This bullet originally read "10.2 KB in one request … load event at
  > 50 ms". That figure was the *uncompressed* transfer from the local test server, which sends
  > `identity`, and a single cold-start load sample. Re-measured with brotli and n≥9, the site is
  > **better** than this document first reported. Binary images do not compress this way — measured
  > brotli on a PNG returns 92.6% of original — which is why §8 of the content-and-image spec
  > budgets images against 3,179 B rather than 10,447 B.
- **It works with JavaScript disabled**, because it ships none. Verified in a JS-disabled browser
  context: the hero, the ticker and the link all render identically. There is no loading state to
  design because there is no load.
- **No horizontal overflow at any viewport** from 320 px to 1920 px. `scrollWidth == clientWidth`
  at all nine widths tested.
- **The spacing rhythm is a real system.** Every one of the seven top-level blocks is separated by
  exactly 64 px. Not approximately — exactly, at every viewport.
- **The dark theme is properly tuned.** In dark mode the brand gold sits at 8.77:1 and body copy
  at 7.34:1, comfortably past AA and most of AAA. Someone checked this palette.
- **The disclosure ethic is real and load-bearing.** The "No buy signals" block is not marketing
  copy; it is the product constraint written where users can hold the project to it. Every fake
  number in the ticker carries a `sample` badge.
- **The docs do not lie.** All five commands documented in `README.md` and the model's docstring
  were run verbatim: all five exit 0. README's claim that the fact-check ledger contains 38 claims
  is exactly right — there are 38 claim rows.

### What a visitor actually meets on arrival

A visitor with a light-mode OS — the default, and the majority — lands on a page where **the only
clickable thing on the site fails WCAG AA contrast at 4.31:1**, as do every section heading and the
label on the compliance block. The page's most important disclosure, the `sample` badge that marks
the headline numbers as fictional, is the least legible text on the page at 3.10:1 and 9.28 px.

They read a headline promising to tell them what a deck will cost next week, then four confident
financial figures — +18.4%, −9.1%, 11.2%, Elevated — which are invented. Then they learn the
product does not exist yet. The page offers exactly **one** thing to do about that: a single link
to a GitHub repository root. There is no way to be told when it launches.

The research the page advertises as "finished and public" — 270 lines of market analysis, a
38-claim fact-check ledger, and a runnable economic model — is genuinely the most valuable asset
on this property, and it is **not linked from the page at all**. The visitor gets a repo root and
is left to find it.

---

## Severity counts

| Severity | Count | Fixed here | Flagged for review | Reported only |
|---|---:|---:|---:|---:|
| Critical | 2 | 1 | 0 | 1 |
| High | 5 | 2 | 0 | 3 |
| Medium | 9 | 3 | 2 | 4 |
| Low | 5 | 1 | 0 | 4 |
| **Total** | **21** | **7** | **2** | **12** |

---

## Critical, in full

### C1 — The deploy gate located things by presentational string, so it was wrong in both directions

**MEASURED.** `scripts/validate_site.py:29-35` (before fix), `.github/workflows/deploy.yml:23-28`

`validate_site.py` is the only thing standing between a broken page and production. It asserted
the presence of *substrings in the raw HTML* rather than the *behaviour* those substrings imply.

**The false negative — the gate green-lit the exact regression it exists to prevent.**

`site/index.html:15` carries a browser-chrome colour hint:

```html
<meta name="theme-color" content="#0E1116" media="(prefers-color-scheme: dark)">
```

That line contains the string `prefers-color-scheme: dark`. The gate's "dark theme" assertion was
a whole-document substring search for exactly that string. So the meta tag satisfied it on its own.

Deleting the **entire 264-byte `@media (prefers-color-scheme: dark)` CSS block** from `index.html`
— every dark-mode rule on the landing page — produced:

```
ok    index.html: dark theme
...
All checks passed.
exit 0
```

`404.html` has no such meta tag, which is why only `404.html` ever failed on theme changes and the
asymmetry was never questioned.

**The false positives — legitimate refactors were blocked, and the message named the wrong cause.**
Each row below was produced by applying one refactor to a scratch copy and recording the gate's
literal output:

| Refactor a redesigner would make | Gate verdict (before) | Literal message |
|---|---|---|
| Extract inline `<style>` to `site/styles.css` | **BLOCKS** | `404.html: missing dark theme`, `index.html: missing theme override` |
| Theme via `.theme-dark` class instead of `[data-theme]` | **BLOCKS** | `missing theme override` (both pages) |
| Adopt CSS `light-dark()` | **BLOCKS** | `404.html: missing dark theme` |
| Rename `--gold` to `--brand` sitewide | passes | — |

Read the first row carefully: moving the CSS into a stylesheet, the single likeliest first step of
any redesign, failed with **"missing dark theme"** — while dark mode was fully intact in
`styles.css`. Every future redesign failure would have misreported its own cause, sending the next
contributor to look for deleted dark mode that was never deleted.

**Four CSP evasions also passed.** The CSP is `default-src 'self'`, so an external subresource is
blocked at runtime in production. The gate's regexes matched only the one spelling this site
happens to use:

| Injected subresource | Gate (before) | Reality |
|---|---|---|
| `<script src='https://cdn…'>` (single quotes) | **passes** | blocked at runtime |
| `<script src="//cdn…">` (protocol-relative) | **passes** | blocked at runtime |
| `<link rel="stylesheet preload" href="https://…">` | **passes** | blocked at runtime |
| `@import url("https://fonts…")` inside `<style>` | **passes** | blocked at runtime |
| `<script src="https://cdn…">` (control) | blocks | correctly caught |

**Consequence.** Two compounding failures. Contributors learn the gate is noise, because it fires
on correct work and names the wrong reason. And it does not catch what it was built to catch: a
web font added via `@import` — the most common single addition in any redesign — would have
shipped green and been blocked in the user's browser.

**Fix — shipped, commit `3a28733`.** `REQUIRED_META` split into document-level markup and a new
`REQUIRED_CSS` checked against the page's actual CSS, collected from inline `<style>` blocks *plus
any local linked stylesheet*. `src`/`srcset` matched under either quote style, protocol-relative
URLs treated as external, `rel` compared as a token set, and CSS scanned for `@import`.

After the fix, every row above resolves correctly: extracting CSS to a stylesheet **passes**, all
four evasions are **caught**, and deleting the dark-theme CSS is **rejected**.

Two cases still block, now honestly and on both pages: switching to a `.theme-dark` class, and
adopting `light-dark()`. Those are genuine contract questions for a human — see **H4**.

**Effort:** shipped, ~2 hours including the test suite.

---

### C3 — The deploy gate does not gate the deploy that actually reaches production

**MEASURED.** `.github/workflows/deploy.yml:30-67`, `docs/deployment/cloudflare.md:20-95`

Discovered on 2026-08-28, when a Cloudflare Pages deployment appeared on PR #3.

**What is measured.** On workflow run `33169303324` (head `243b156`), the `deploy` job completed
`success` with its `Deploy to Cloudflare Pages` step **`skipped`** — the credential check found no
`CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID` and took the documented skip path. At the same time,
`cloudflare-workers-and-pages[bot]` posted successful deployments for both `8ef93ee` and `4e102aa`,
serving `https://<hash>.bountycharts.pages.dev` and a branch preview.

So the site is being deployed by **Cloudflare Pages' own Git integration**, not by the workflow this
repository documents, tests and gates. There are two deploy paths, and the one with the gate in
front of it is the one that is not running.

**What follows.** Cloudflare's documentation states that Pages "will automatically rebuild your
project and deploy it on every new pushed commit", and that preview deployments "repeat the
build-and-deploy process for pull requests". Nothing in that pipeline consults GitHub Actions. So
`scripts/validate_site.py` — the subject of finding **C1**, described there as the only thing
standing between a broken page and production — does not stand between them at all on this path.
A commit that fails the gate still gets built and served by Pages.

**The ordering is measured, not assumed.** Two consecutive pushes, from this session's event stream
and the PR's check-run records:

| head | Pages build starts | `validate` starts | `validate` completes | Pages reports success |
|---|---|---|---|---|
| `a0a2f8d` | 13:08:23 | 13:08:27 | 13:08:33 | 13:08:34 |
| `ff28515` | 13:10:24 | 13:10:26 | 13:10:31 | 13:10:39 |

**Replicated on both: the Pages build begins before the `validate` job starts** — by 4 s and 2 s
respectively. A deploy that has already started before the gate has begun cannot be conditioned on
the gate's result.

Note what did *not* replicate. On `a0a2f8d` Pages also reported success one second *before*
`validate` finished; on `ff28515` it reported eight seconds *after*. That variation is not noise to
be explained away — it is the finding. The two pipelines are unsynchronised, so their completion
order is a race that lands differently on each push. A gate whose result arrives before the deploy
on one push and after it on the next is not gating anything on either.

What remains strictly untested is a deploy of a commit that actually fails the gate — proving that
directly would mean pushing a deliberately broken commit and watching Pages publish it to a live
site, which is not worth doing to confirm what the ordering and the documentation both already
establish.

**What decides how bad this is:** whether `main` has branch protection requiring the `validate`
check. With it, a human cannot merge a red PR and the gate remains effective at the merge boundary.
Without it, the gate is advisory. That setting was not visible from this session and should be
checked first.

**Consequence.** The runbook and the workflow describe a deployment path that is not the live one,
so every verification step in `docs/deployment/cloudflare.md` steps 3-4 now describes something that
did not happen. If the secrets are later added as documented, **both** paths will deploy the same
project, racing on every push.

**Fix.** Decide which path is authoritative and delete the other. If Pages Git integration stays:
require the `validate` check in branch protection, delete the `deploy` job, and rewrite the runbook.
If the workflow path is preferred: disconnect the Git integration in the Pages project and add the
two secrets. Not fixed here — it is a deployment-topology decision requiring account access.

**Effort.** 30 minutes either way, once the decision is made.

---

## High findings

| # | Finding | Evidence | file:line | Status |
|---|---|---|---|---|
| **H1** | Light theme — the default — fails WCAG 2.2 AA on 7 text roles, including the only interactive element on the site. Link, `h2` section headings and the "NO BUY SIGNALS" label all sit at **4.31:1** against a 4.5 threshold; ticker labels and the `sample` badge at **3.10:1**; wordmark tagline and `01/02/03` numerals at **2.97:1**. Link *hover* makes it worse, not better: `--gold-bright` is **2.52:1**. The same tokens pass comfortably in dark mode (gold 8.77:1). | MEASURED — rendered colours read from the browser in both themes, WCAG formula | `site/index.html:28-41`, `:224-226` | Reported. Brand colour — draft below, nothing shipped |
| **H2** | `index.html` had no `<main>` landmark, so every word of content sat outside any landmark. `404.html` already had one. | MEASURED — Chromium AX tree: `main: 0` on index, `1` on 404 | `site/index.html:266` | **Fixed** `a63b256` |
| **H3** | `models/unit_economics.py` — the file README calls the source of every revenue figure — had zero tests and was unreachable by CI. No test file of any kind existed in the repo. | MEASURED — `find` for `test_*.py`/`conftest.py`/`pytest.ini` returns nothing; workflow `paths:` excludes it | `.github/workflows/deploy.yml:6-14` | **Fixed** `83473ba` |
| **H4** | The gate *mandates dead code*. It requires the string `data-theme="dark"`, but nothing anywhere can set that attribute — no JavaScript, no server, no markup. The site ships two unreachable CSS blocks that the build forbids removing. | OBSERVED — `data-theme` appears only in the CSS rules themselves; the sole `<script>` is `application/ld+json` | `scripts/validate_site.py:45`, `site/index.html:49-58` | Reported. Changes the contributor contract — needs a human decision |
| **H5** | The ticker is `role="img"` with an `aria-label` naming only **2 of its 4 cells**. The label is 19 words; the visible content is 28 words carrying three percentages and one qualitative value. Spread (11.2%) and Reprint risk ("Elevated") appear nowhere in it. | MEASURED — label and visible text counted from the DOM | `site/index.html:273` | Reported. Alters text qualifying financial-looking figures — draft below |

**On H5, an honesty note.** `role="img"` makes an element a leaf in the accessibility tree, so
assistive technology announces the label instead of the contents. That behaviour is per the ARIA
spec — **INFERRED**, not measured: no screen reader was run here. What *is* measured is that
Chromium's full AX tree still contains the cell text and the `SAMPLE` badge. The defect is the
incomplete label, which is certain; the precise announcement is not.

---

## The pattern underneath

Four root causes explain nearly every finding.

**1. The light theme is the default and the least examined.** (H1, L4)
The dark palette is tuned to AA and beyond; the light palette reads as its inversion, derived
rather than re-checked. Every contrast failure on the site is a light-theme failure except one.
The theme most visitors see is the one nobody measured.

**2. Checks assert the shape of today's code, not the behaviour they care about.** (C1, H4)
Both gate failures are the same mistake: `'data-theme="dark"' in src` instead of "this page has a
dark theme". The check passes when the string survives and fails when it moves, which is precisely
backwards — a string is a fact about the current implementation, and a gate exists to survive
implementation change.

**3. Correctness was verified where it was easy to verify, and asserted where it was not.** (H3, C1, M3)
The HTML has a gate; the Python model — the numbers the whole business case rests on — had nothing.
The CSP relaxation was justified in prose ("some browsers evaluate JSON-LD against `script-src`")
and never tested; it does not reproduce. Effort followed convenience rather than risk.

**4. The page is built to be *read*, not to be *acted on*.** (H5, M7, M8)
One link, no destination for interest, no route to the research it advertises, no share image.
Every content decision is about what to say; none is about what happens next. This is not a visual
problem and a redesign will not fix it by accident.

---

## Redesign blocker list

Resolve these **before** any visual work starts.

| # | Blocker | Why visual work is blocked until it is resolved |
|---|---|---|
| **C1** | ~~Gate coupled to presentational strings~~ **resolved** | Was the hard blocker: the gate failed on correct refactors and named the wrong cause. Extracting the CSS — step one of any redesign — now passes. |
| **H4** | The `data-theme` requirement | Still blocks two legitimate theming refactors (`.theme-dark` class, `light-dark()`). A redesigner must know whether that attribute is a contract to honour or dead code to delete. Nobody can currently answer this. |
| **H1** | Light-theme contrast | The palette needs correcting at the token level. Doing it as part of a redesign hides an accessibility fix inside a taste change, and neither can then be reviewed on its own merits. Fix the tokens first, redesign second. |
| **M5** | Brand colour requires 8 edits across 2 files | Measured: `--gold` is declared 4× for its light value and 4× for its dark value across `index.html` and `404.html`. Any palette change during a redesign will drift between the two pages. Consolidate before touching colour. |
| **M4** | The type scale is not a system | 12 distinct font sizes with adjacent step ratios from 1.029 to 2.667. Six of them fall inside a 2.56 px band. A redesigner "tidying" this will silently re-rank the page's hierarchy unless the intended ramp is decided first. |

---

## Undocumented constraints a redesigner must be told

Every rule below fails the build and appears in **no** document. All harvested from
`scripts/validate_site.py` by running it, not by reading prose. README and the Cloudflare runbook
mention none of them.

| Constraint | Source | What you see if you break it |
|---|---|---|
| Every `.html` file in `site/` must contain `lang="en"` — literally that string; `lang='en'` or `lang="en-GB"` fails | `validate_site.py:31` | `missing lang attribute` |
| Every page needs a `<title>` and `name="viewport"` | `validate_site.py:32-33` | `missing title` / `missing viewport` |
| Every page's CSS must contain `prefers-color-scheme: dark` | `validate_site.py:44` | `missing dark theme` |
| Every page's CSS must contain a `[data-theme="dark"]` selector — **even though nothing can set that attribute** (see H4) | `validate_site.py:45` | `missing theme override` |
| `index.html` alone must carry `rel="canonical"`, `name="description"`, `property="og:title"` and a parseable `application/ld+json` block | `validate_site.py:49-54` | `index.html: missing canonical` etc. |
| `sitemap.xml` must contain the literal string `https://bountycharts.com/` | `validate_site.py:180` | `sitemap.xml: does not reference the canonical host` |
| Tags must balance under a strict parser — mismatched nesting fails even where a browser would recover | `validate_site.py:68-92` | `</div> closes <footer>` |
| **No external subresource, in any spelling.** `src`/`srcset` under either quote style, protocol-relative `//`, any `<link>` whose `rel` includes a fetching token, and `@import` inside CSS | `validate_site.py` (as amended) | `external subresource would be blocked by CSP — [...]` |
| A new page in `site/` is held to every per-page rule above, so adding `pricing.html` fails four checks at once | `validate_site.py:126` (globs `*.html`) | four failures in one run |
| **New:** every `<url>` in `sitemap.xml` needs a well-formed ISO `<lastmod>` | `tests/test_validate_site.py` | test failure |
| **New:** every page needs a `<main>` landmark | `tests/test_validate_site.py` | test failure |
| **New:** no page may serve an executable `<script>`; only `application/ld+json` | `tests/test_validate_site.py` | test failure |

**The practical consequence:** a redesign cannot use a web font from Google Fonts, a CDN
stylesheet, an analytics snippet, or an icon library — not as a policy preference but as a build
failure. This is the single most important thing to tell a designer before they start, and it is
written down nowhere else.

---

## If you do only five things

Ranked by visitor impact × provability, divided by effort.

| # | Do this | Findings | Effort |
|---|---|---|---|
| **1** | **Fix the light-theme palette.** Darken `--gold` and `--ink-faint` to clear 4.5:1, and fix the hover state that currently *reduces* contrast to 2.52:1. Draft values below — they are luminance-scaled, so the hue is preserved. This is the difference between a site the majority of visitors can read and one they cannot. | H1, L4 | **1–2 h.** Two token values plus hover; ~8 edit sites until M5 is consolidated |
| **2** | **Answer the `data-theme` question.** Either wire up a theme toggle that sets the attribute, or delete both blocks and the gate rule. Right now the build enforces code that can never run, and it blocks two standard theming refactors. | H4, C1 | **30 min** to decide; 1 h either way |
| **3** | **Link the research from the page.** The deep dive, the 38-claim ledger and the runnable model are the most valuable things this property owns, the page advertises them as "finished and public", and it links to a repo root instead. Three direct links. | M8 | **15 min** |
| **4** | **Complete the ticker's accessible name**, so it names all four cells including the 11.2% spread and the reprint-risk value, and say in it that the figures are illustrative. Screen-reader users currently get a partial description of invented financial figures with no indication they are samples. | H5 | **20 min** |
| **5** | **Consolidate the design tokens into one place.** One brand colour currently means 8 edits across 2 files. Every future visual change pays this tax, and the two pages will drift. | M5 | **2–3 h**, and it unblocks the redesign |

---

## What to defend

Some things here look like flaws and are decisions. A redesign must not "fix" them.

| Do not "fix" | Why it looks wrong | Why it is right |
|---|---|---|
| **Zero JavaScript** | No interactivity, no analytics, feels unfinished | It is why the page is 10.2 KB in 1 request and renders in 50 ms with JS disabled. Evidence: the CSP is `default-src 'self'`, the gate blocks external subresources, and `_headers` was written to enforce it. This is a designed constraint, not a gap. |
| **The "No buy signals" block** | Reads as a legal disclaimer taking prime space in the middle of a short landing page | It is the product's core differentiator stated as a public commitment, and the commit that added it says so: *"Page copy encodes the no-buy-signals rule directly, so the public commitment matches the agency guardrail."* Cutting it for brevity deletes the thesis. |
| **`twitter:card` = `summary`, not `summary_large_image`** | Looks like an unfinished share card | Correct for a page with no `og:image`. `summary_large_image` without an image renders a broken card. Add the image first (M7), then upgrade — in that order. |
| **`_redirects` handles no host canonicalisation** | Looks like a forgotten redirect | Deliberate, and the file explains itself at `site/_redirects:3-7`: a request to `www` only reaches that file if `www` already routes to the Pages project, so it is the wrong layer. The runbook puts it in a Cloudflare Redirect Rule instead. |
| **The empty right column on desktop** | Half the 960 px canvas is unused at 1280 px+ | Body copy is capped at 60ch and the `h1` at 18ch. Those are legibility limits, not oversights. A redesign that fills the width by widening the measure makes the page harder to read. Fill it with *content* or leave it alone. |
| **No email capture** | An obvious pre-launch miss | Deliberate and documented in `docs/deployment/cloudflare.md` as follow-up #2: a capture form needs an email service provider, which is recurring spend and an owner decision. The doc explicitly says *"Do not add a form that posts nowhere."* |
| **`prefers-reduced-motion` guarding nothing** | Dead code — there are zero transitions on the site | Harmless defensive default that costs 3 lines and is correct the moment any animation is added. Leave it. |

---

## Drafts for findings that were deliberately not shipped

Policy: brand and visual identity decisions, publisher identity, and copy qualifying figures a
user might act on are not changed autonomously. Drafts only.

### H1 / L4 — light-theme contrast

Luminance-scaled so hue is preserved. Both light backgrounds (`#FAFAF8` page, `#FFFFFF` cards)
satisfied.

> **Corrected 2026-08-28.** The `--gold-bright` value first drafted here (`#926D2E`) was defective
> and must not be used. It clears AA against the background, but measures **1.0024:1 against the
> corrected `--gold` `#966C1D`** — visually identical, so the hover state would disappear entirely,
> which is worse than today's already-weak 1.7105:1. Caught by an adversarial verifier during the
> content-and-image specification pass and re-measured before accepting. The table below carries
> the corrected value.

| Token | Current | Ratio | Draft | Ratio | vs `--gold` |
|---|---|---:|---|---:|---:|
| `--gold` (light) | `#9A6F1E` | 4.31:1 | `#966C1D` | **4.51:1** | — |
| `--gold-bright` (light, hover) | `#C9973F` | 2.52:1 | **`#7A5716`** | **6.27:1** | **1.39:1** |
| ~~superseded draft~~ | | | ~~`#926D2E`~~ | ~~4.52:1~~ | ~~**1.00:1** — invisible~~ |
| `--ink-faint` (light) | `#8A93A1` | 2.97:1 | `#6D747F` | **4.51:1** | — |
| `--ink-faint` (dark) | `#6B7482` | 3.69:1 | `#798393` | **4.55:1** | — |

Hover now *darkens* rather than lightens, which is a legitimate affordance direction and gives more
headroom than the original. Pair it with `a:hover { text-decoration-thickness: 2px; }` so the
affordance does not depend on colour at all.

Note that `--gold` at `#966C1D` clears the threshold by only 0.01. **Do not apply `opacity` to any
of these three light-theme tokens** — all three re-break at once — and re-run the computation on any
future change to `--bg`. If the brand can tolerate a deeper gold, more headroom is worth taking.

Also worth deciding separately: the `sample` badge is 9.28 px at 0.75 opacity — even at a compliant
colour it is the least legible text on the page, and it is the disclosure that marks four financial
figures as fictional.

### M1 — the copyright year

`site/index.html:340` reads `© 2026 BountyCharts`. It becomes wrong on **2027-01-01**, 146 days
from the audit date. The site has no build step and no JavaScript, so there is no mechanism to
keep it current. Options, in order of preference: change to `© 2026–present BountyCharts`; or drop
the year; or accept an annual manual edit and put it in a release checklist. Not changed here —
this is publisher identity.

### H5 — the ticker's accessible name

Current (19 words, 2 of 4 cells): *"Illustrative example: a deck's cost rising as its metagame
share grows, and a card falling after losing play rate."*

Draft: *"Illustrative sample data, not live prices. Four example readings: deck cost up 18.4%
over 7 days, tracking meta share; a card down 9.1% over 7 days on falling play rate; an 11.2%
spread between market and listed price; and elevated reprint risk in a set rotation window."*

### M7 — share preview

No `og:image` exists, so links shared to Slack, Discord, X or iMessage render as a bare text card.
For a project whose thesis is that price and metagame data belong on one chart, the share image is
a product argument, not decoration. Needs a designed 1200×630 asset — an identity decision, and
note that adding it means adding the first binary asset to a repo that currently has none, plus
revisiting `twitter:card`.

---

## Full finding list

### Medium

| # | Finding | Grade | file:line | Status |
|---|---|---|---|---|
| M1 | `© 2026` hardcoded; wrong from **2027-01-01** (146 days out) | MEASURED | `site/index.html:340` | Draft above |
| M2 | `sitemap.xml` declared `changefreq=weekly` with no `lastmod`. Content last changed 2026-07-31, so the weekly promise first broke **2026-08-08** — the audit date | MEASURED | `site/sitemap.xml:6` | **Fixed** `ddb6588` |
| M3 | CSP allowed `'unsafe-inline'` in `script-src` on a stated premise that does not reproduce: 0 violations under `script-src 'self'` *and* under `'none'` | MEASURED (Chromium) | `site/_headers:6` | **Fixed** `a5568d3` — flagged |
| M4 | 12 distinct font sizes; adjacent step ratios 1.029–2.667; six sizes inside a 2.56 px band (10.56/10.88/11.2/11.52/12.48/13.12 px) with one 2.667× gap to the `h1` | MEASURED | `site/index.html:107-213` | Reported — visual identity |
| M5 | One brand colour = **8 edits across 2 files** (each value declared 4×). 6 tokens duplicated between pages | MEASURED | `site/index.html:28-58`, `site/404.html:10-19` | Reported — redesign blocker |
| M6 | No `@media print`. With a dark OS theme the page printed `rgb(14,17,22)` — a near-black fill — and the only URL was lost | MEASURED | `site/index.html:228` | **Fixed** `b5c244c` — flagged |
| M7 | No `og:image`; share previews render bare | MEASURED | `site/index.html:9-14` | Draft above |
| M8 | Exactly 1 outbound link on the whole site, to a repo root — not to the research the page advertises | MEASURED | `site/index.html:333` | Reported — copy change |
| M9 | `_headers` declares `/assets/*` immutable caching; no `site/assets/` exists and nothing is fingerprinted | OBSERVED | `site/_headers:11-12` | Reported — harmless until assets ship |

### Low

| # | Finding | Grade | file:line | Status |
|---|---|---|---|---|
| L1 | `scripts/__pycache__/validate_site.cpython-311.pyc` committed; no `.gitignore` existed | OBSERVED | committed in `a1b150f` | **Fixed** `b863d08` |
| L2 | `prefers-reduced-motion` block guards zero transitions/animations | OBSERVED | `site/index.html:228-230` | Defend — see above |
| L3 | `404.html` carries 3 meta tags vs `index.html`'s 11; no `theme-color`, so browser chrome colour differs between pages | MEASURED | `site/404.html:4-7` | Reported |
| L4 | `--ink-faint` fails AA in **dark** too (3.69:1 on cards, 4.00:1 on page) | MEASURED | `site/index.html:45` | Draft above |
| L5 | **INFERRED** — `_headers` sets `Cache-Control: max-age=0, must-revalidate` on `/*.html`, but the landing page is served at `/`, which may not match that pattern, leaving the most cache-sensitive page on Pages' default policy | INFERRED | `site/_headers:15-16` | Confirm with `curl -I https://bountycharts.com/` after deploy |

---

## Discarded during re-verification

11 candidate findings did not survive. Recorded because a discarded finding is evidence too, and
because several are things an audit would normally assert without checking.

| Candidate | Why it was discarded |
|---|---|
| Footer legal disclaimer fails contrast | **My own error, caught by re-measuring.** Derived from `footer { color: var(--ink-faint) }` (2.97:1). The rendered value is `--ink-soft` at **5.98:1 — passes**, because `p { color: var(--ink-soft) }` at `:183` wins over the inherited footer colour. Both footer children are `<p>`. |
| The `sample` badge is invisible to assistive tech | It is CSS `::after` content, but Chromium **does** expose it — it appears as `SAMPLE` in the AX tree. |
| The ticker's numbers are absent from the accessibility tree | They are present as `StaticText` nodes. The real issue is narrower and is H5. |
| Horizontal overflow on small screens | None at any of 9 viewports, 320–1920 px. |
| Focus indicator missing or invisible | Measured `solid 2px rgb(154,111,30)` with 2 px offset on the only focusable element. |
| Heading levels skipped | `h1 → h2 → h3`, no skips. |
| README's "38 claims" is wrong | Exactly 38 claim rows. Correct. |
| Documented commands are broken | All 5 documented invocations exit 0. |
| `unit_economics.py` has a date bug | **0** date-dependent constructs. Output is date-invariant — a genuine negative result. The date risk is in the copy, not the model. |
| The data-URI SVG favicon is malformed | Decodes and renders in Chromium (`fetch` ok, 103 bytes). It does carry 7 unencoded spaces, tolerated by browsers. Other engines untested. |
| No-JS users get a broken page | Renders fully with JavaScript disabled: hero, ticker and link all intact. |

---

## What was shipped, flagged, and left alone

**Shipped — 7 commits, one per finding, each independently revertible:**

| Commit | Finding | Change |
|---|---|---|
| `3a28733` | C1 | Gate tests behaviour, not strings; 4 CSP evasions closed; `tests/` created (24 tests) |
| `a63b256` | H2 | `<main>` landmark on `index.html` |
| `ddb6588` | M2 | `<lastmod>` in the sitemap |
| `b863d08` | L1 | Untrack `.pyc`, add `.gitignore` |
| `83473ba` | H3 | CI runs the tests and covers `models/` |
| `a5568d3` | M3 | Drop `'unsafe-inline'` from `script-src` — **flagged** |
| `b5c244c` | M6 | Print stylesheet — **flagged** |

Nine tests failed before their fixes and pass after. The suite is 24 tests and green; the gate is
green on the real site; the page is byte-identical in layout (7 × 64 px gaps, 1909 px height, no
overflow at any viewport).

**Flagged for human review:** `a5568d3` changes a live security header and was verified in Chromium
only — confirm on a preview deployment. `b5c244c` changes printed output and introduces a
print-only brand colour.

**Deliberately not shipped:** all light-theme colour changes (H1, L4), the copyright year (M1),
the ticker's accessible name (H5), the share image (M7), and the research links (M8). Each alters
brand identity, publisher identity, or text qualifying financial-looking figures. Drafts are above;
none are applied.

**Not finished, and why:**

- **No live-URL verification of anything.** Egress-blocked. Cache headers (L5), the 404 status code,
  redirect behaviour and real-world CSP enforcement are all unconfirmed against production.
- **Chromium only.** Safari and Firefox were not reachable, so M3 and the SVG-favicon question are
  single-engine results.
- **No screen reader was run.** H5's announcement behaviour is spec-derived, not observed.
- **The parallel-agent method failed** and the audit was completed single-threaded. Cause diagnosed
  and evidenced above; the finding set is unaffected, but it was produced by one pass rather than
  by independent lenses cross-checking each other.

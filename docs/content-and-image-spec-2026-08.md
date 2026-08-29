# Content and image generation specification — August 2026

A build specification for every image asset and content item this site needs: paste-ready
generation prompts, deterministic fallbacks, exact insertion markup, alt text, byte budgets and a
sequencing runbook.

**Companion documents:** [`frontend-audit-2026-08.md`](frontend-audit-2026-08.md) ·
[`scorecard-2026-08.md`](scorecard-2026-08.md)

> **Method.** Produced by a 12-agent workflow: 2 ground agents, 6 specification lenses, 3
> adversarial verifiers and a synthesiser. The verifiers raised **67 corrections, 21 of them
> blocking**; the synthesiser applied them, **dropped 34 items** that did not survive, and
> overruled a verifier twice with its reasoning recorded. Every load-bearing number was
> re-measured against the repository at `243b156` before being written down.

---

> **Verification baseline for this document.** Repo `/home/user/BountyCharts`, branch `claude/frontend-audit-fixes-0b7b2j`, **HEAD `243b156`** (not `bfca67a` — that is three commits back). `python3 scripts/validate_site.py` → **exit 0, 26 `ok` lines**. `python3 -m unittest discover -s tests` → **`Ran 26 tests … OK`** (not 24). `git status --porcelain` empty. `site/` = **15,181 B** on disk; `index.html` 11,657 B, `404.html` 1,891 B, `sitemap.xml` 267 B **ending with a newline**. All contrast values recomputed here with the WCAG 2.x sRGB relative-luminance formula. **MEASURED** = run in this session. **OBSERVED** = read in the file. **INFERRED** = judgement or unverifiable offline.
>
> **Scratch-verification recipe (corrected).** Copy `site/`, `scripts/`, `tests/`, **`docs/`** and **`README.md`**. `tests/test_validate_site.py:308` (`FactCheckLedgerScorecardIsConsistent`) reads `docs/fact-check-ledger.md` via `ROOT`; the old three-directory recipe now errors on a clean tree.

---

## 1. What this document is, and the constraints that shape every decision in it

This is the complete content and image-generation specification for `bountycharts.com` — a 6-file, 15,181-byte pre-launch static site with one landing page, one 404, and no images, no fonts, no scripts, no `/assets/` directory and one outbound link.

It is written to be worked straight down: every asset carries a paste-ready prompt or deterministic source, every content item carries exact copy and a `file:line` anchor, and every new page carries a gate-compliance proof.

**Lead with the constraints. They are the reason the answers are what they are.**

#### 1.1 The six binding constraints

| # | Constraint | Source | What it forecloses |
|---|---|---|---|
| **C1** | CSP: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'` | `site/_headers:6` | No CDN, no hotlinked art, no Google Fonts, no third-party form POST (Mailchimp/ConvertKit/Buttondown are **blocked**), no analytics beacon |
| **C2** | Deploy gate blocks external subresources in every spelling: `src`/`srcset` under either quote style, protocol-relative `//`, any `<link>` whose `rel` is in `FETCHING_REL`, and CSS `@import` | `scripts/validate_site.py:188-189, 200-246` | Any external fetch fails CI — **except four holes, see §9.2** |
| **C3** | `/assets/*` → `Cache-Control: public, max-age=31536000, immutable` — 365 days, no revalidation even on hard reload | `site/_headers:11-12` | **Every file under `/assets/` MUST carry a content hash in its filename.** The filename is the only cache-buster that exists |
| **C4** | Any new `.html` in `site/` needs: literal `lang="en"`, `<title>`, `name="viewport"`, CSS containing **both** `prefers-color-scheme: dark` **and** `[data-theme="dark"]`, a `<main>` landmark, and **zero** executable `<script>` (only `application/ld+json`) | `validate_site.py:31-45`; `tests/test_validate_site.py:268-276, 299-306` | No JS anywhere. `theme-color` meta does **not** satisfy the CSS check |
| **C5** | Performance budget. **MEASURED:** whole site 15,181 B; `index.html` 11,657 B raw / **3,179 B brotli q11 — the production wire cost**; 1 HTTP request; 0 subresources; 76 DOM elements; `loadEventEnd` **median 21.9 ms** (n≥9; the brief's 50 ms and Lenses 2/4's 48.7 ms are cold-start outliers) | measured | Any visitor-fetched byte is expensive relative to a 3.2 KB page |
| **C6** | **Legal / brand.** The footer disclaims affiliation with Riot Games, The Pokémon Company, Bandai Namco, Wizards of the Coast (`site/index.html:339`). The page commits: "does not publish buyout alerts, price predictions, or investment advice, and never will" (`site/index.html:326`) | observed | **No** card art, card frames, sleeves, boosters, foils, set symbols, mana pips, character art, publisher logos. **No** rockets, bull/bear, up-and-to-the-right charts, candlesticks, money, coins, trading floors, slabs, portfolios. The register is **instrumentation and measurement**, never speculation |

#### 1.2 The known unfixed contrast defect

The **light theme is the default** and two of its tokens fail WCAG AA. Recomputed here:

| Token | On `--bg #FAFAF8` | On `--surface #FFFFFF` | Verdict |
|---|---:|---:|---|
| `--gold #9A6F1E` | **4.3061** | 4.5001 | FAIL AA on `--bg` |
| `--gold-bright #C9973F` | **2.5175** | — | FAIL |
| `--ink-faint #8A93A1` | **2.9687** | — | FAIL |
| `--ink-faint #6B7482` (dark) on `#0E1116` / `#161A21` | **4.0035** / **3.6929** | | **FAIL in dark too** — reported as finding **L4** in `frontend-audit-2026-08.md:396` at these same values |

**Remediation adopted here** (§4, `CNT-13`), all recomputed:

| Token | Old | **New** | On `--bg` | On `--surface` |
|---|---|---|---:|---:|
| `--gold` (light) | `#9A6F1E` | **`#966C1D`** | 4.5059 | 4.7090 |
| `--gold-bright` (light) | `#C9973F` | **`#7A5716`** | **6.2749** | 6.5578 |
| `--ink-faint` (light) | `#8A93A1` | **`#6D747F`** | 4.5107 | 4.7140 |
| `--ink-faint` (dark) | `#6B7482` | **`#838C9A`** | 5.5680 | 5.1360 |

> **Why `#7A5716` and not the drafted `#926D2E`.** `--gold-bright`'s only job in light theme is `a:hover` (`site/index.html:225`). **MEASURED: `#966C1D` vs `#926D2E` = 1.0024:1** — the hover state would become invisible (today's pair is 1.7105:1). `#7A5716` clears AA at 6.2749 **and** sits at **1.3926:1** against `--gold`, preserving the affordance. Also add `a:hover { text-decoration-thickness: 2px; }` so the affordance does not depend on colour at all.
>
> The three light values clear 4.5:1 by ≤0.02. **Forbid `opacity` on any of these tokens** and re-run the check on any future `--bg` change — all three re-break at once.

#### 1.3 Four editorial rules that follow from C3 + C6

1. **Nothing frozen may contain a volatile fact.** An `og:image` is double-frozen — `immutable` for a year *plus* the Facebook/X/LinkedIn scrape cache. **No numeral, percentage, currency symbol, arrow or plotted line goes into any image.**
2. **No forecast anywhere.** `index.html:269`'s "next week?" is a price prediction on a page that promises never to publish one. It is fixed in copy (`CNT-01`) **before** any card is rendered from it.
3. **No unassented claim about the owner.** A no-position policy, a privacy commitment, or a contact address asserted without written sign-off converts a gap into a misstatement, which is strictly worse.
4. **No unsourced universal negative about third parties.** The project's own method (`README.md:38`) is "where a claim could not be substantiated it is marked unsourced rather than repeated." The page currently violates it twice.

---

## 2. Master manifest

`DEPLOY_DATE` = the date the commit lands. **Today is 2026-08-28.** Every stamped date in this document is the token `DEPLOY_DATE`, not a literal — see `RUN-09`.

#### 2.1 Images

| ID | Kind | Path | Priority | Budget | Fetched by |
|---|---|---|---|---|---|
| **IMG-01** | PNG 1200×630 | `site/assets/og-card.<hash8>.png` | **P0** | **≤20,000 B** (hard, gate-enforced) | crawler only — **0 visitor bytes, 0 requests** |
| **IMG-02** | ICO 16+32+48 | `site/favicon.ico` — **root, not hashed** | **P0** | ≤1,500 B | root-convention consumers only |
| **IMG-03** | inline SVG, no file | `site/index.html:17` (twin `data:` icons) + `:262` (wordmark glyph) | **P0** | ≤220 chars per URI; +≈400 B raw / **+42 B brotli** | inline — **0 requests** |
| **IMG-04** | PNG 180×180 | `site/assets/touch-icon-180.<hash8>.png` | P1 | ≤1,000 B | iOS add-to-home-screen only |
| **IMG-05** | SVG | `site/assets/logo.<hash8>.svg` | P1 | ≤2,000 B | Google (`Organization.logo`) only |
| **IMG-06** | inline SVG | inside `site/method.html` | P2 (conditional) | ≤500 B of HTML | inline — 0 requests |
| — | *rejected* | 2× og card · light og card · `site.webmanifest` + 192/512 icons · `mask-icon` · web fonts · WebP/AVIF og · hero screenshot · SVG wordmark file · generated texture plate | — | — | §10 |

#### 2.2 Content

| ID | Kind | Anchor | Priority | Sign-off |
|---|---|---|---|---|
| CNT-01 | H1 rewrite (removes forecast) | `index.html:269` | **P0** | ⚠️ legal/brand |
| CNT-02 | Lede rewrite (hedges competitor claim) | `index.html:270` | P1 | ⚠️ third-party factual |
| CNT-03 | Above-fold status line | new, between `:264` and `:266` | **P0** | — |
| CNT-04 | Ticker caption = accessible name | `index.html:273`, `:294` | **P0** | — |
| CNT-05 | Ticker badge legibility | `index.html:158-169` | **P0** | — |
| CNT-06 | `What it does` → `What it will do` | `index.html:297` | P1 | — |
| CNT-07 | `Deck cost, forecast` → `tracked` | `index.html:301` | **P0** | ⚠️ legal/brand |
| CNT-08 | Riftbound section: delete uncitable claim | `index.html:319` | **P0** | ⚠️ factual |
| CNT-09 | **Merged** Status + research + `/method` link | `index.html:330-334` | P1 | ⚠️ published counts |
| CNT-10 | Launch-notification section | new, after `:334` | P1 | ⚠️ **blocked on MX** |
| CNT-11 | `description` + `og:description` | `index.html:7`, `:12` | **P0** | ⚠️ |
| CNT-12 | 404 body copy | `404.html:34-39` | P2 | — |
| CNT-13 | Palette remediation, all pages, one commit | `index.html` `:28-58`, `404.html:11,19` | **P0** | — |
| CNT-14 | 404 CSS (fixes AA failure) | `404.html:26` | P1 | — |
| CNT-15 | Real Riftbound figures in ticker | `index.html:274-293` | P2 (deferred) | ⚠️ factual |

#### 2.3 Pages, metadata, tooling

| ID | Kind | Path | Priority | Budget |
|---|---|---|---|---|
| PAGE-01 | new page | `site/method.html` (**flat**) | **P0** | ≤13 KB raw / ≈3.7 KB brotli, 1 request, 0 subresources |
| PAGE-02 | new page | `site/disclosures.html` (**flat, plural**) | P0 at launch / P1 now | ≤11 KB raw / ≈3.1 KB brotli |
| META-01 | og:image block + `twitter:card` flip | `index.html:13-14` | P1 (blocked on IMG-01) | +≈500 B raw / +129 B brotli |
| META-02 | JSON-LD `@graph` | `index.html:18-26` | **P0** | +≈900 B raw / +≈150 B brotli |
| META-03 | sitemap rewrite | `site/sitemap.xml` | **P0** | ≈400 B |
| META-04 | `robots.txt` — **no change**, documented | `site/robots.txt` | P0 (0 work) | 0 |
| META-05 | `404.html` head — **no change**, documented | `site/404.html:3-8` | P0 (0 work) | 0 |
| META-06 | `_headers` `/favicon.ico` rule | `site/_headers:13` | **P0** (ships with IMG-02) | +≈200 B, never served |
| TOOL-01 | `scripts/fingerprint_assets.py` | new | **P0 — first** | repo only |
| TOOL-02 | `check_assets()` in the gate | `scripts/validate_site.py` | **P0 — same commit as TOOL-01** | repo only |
| TOOL-03 | `tests/test_assets.py` | new | **P0 — same commit** | repo only |
| TOOL-04 | Gate hardening: `rglob` + CSS `url()` + `mask-icon` + `<use href>` | `validate_site.py:126,188,211,239`; `tests:270,300` | P0 | repo only |
| TOOL-05 | `deploy.yml`: add `docs/**` to `paths:` | `.github/workflows/deploy.yml` | P1 | repo only |

---

## 3. Image assets

### 3.0 The governing finding: five of six assets are not generated

**The correct answer for almost every asset here is hand-authored SVG plus a screenshot of the site's own CSS.** Five reasons, in order of force:

1. **Text.** Every asset carries the wordmark, the tagline (`TCG price × meta`, U+00D7 not the letter x) or the URL. No current model spells these reliably, and `NEGATIVE: gibberish text` cannot negative-prompt a model into spelling. Any generative route therefore reduces to *background only* + type composited in a vector tool.
2. **Bytes.** Flat fills quantise to a 64-colour palette; gradients, grain, glow and bokeh do not. The generative default aesthetic measured at **≈4.7× the byte cost** of the same flat card, for zero communicative gain, on a site whose single best property is that it is 15 KB.
3. **Colour.** The brand is eleven exact hex values with a known AA failure. A sampled image lands *near* `#D9A94F`, not on it, and every ratio in §3.1 becomes an estimate.
4. **Reproducibility.** `/assets/*` is frozen for a year. When one word changes, a template re-renders byte-identically except that word; a generative re-roll returns a different picture.
5. **Legal.** The exclusion list in §3.2 is long because the model's training distribution for "trading card game" is *saturated* with the card frames, set symbols and character art the footer disclaims. Every generation is a draw against that distribution. A hand-authored diamond and a CSS ruler are draws against nothing.

**The honest scope for a generative model here is exploration, not production.** The prompts below are complete and paste-ready because the assignment requires them; the recommendation attached to each is the deterministic fallback.

### 3.1 Contrast law for anything baked into an image

Baked text cannot be fixed by CSS, cannot be zoomed, and is not read by a screen reader. It clears a **higher** bar, not a lower one.

**Every image asset ships in the DARK palette.** This is arithmetic, not taste: the card must carry the gold wordmark, and on light ground the shipped gold fails AA (4.3061) while the remediation clears by 0.0059 — zero headroom, baked irreversibly into a raster. On dark ground the same role is **8.7699**.

| Element | Fg | Bg | Ratio | Threshold | Verdict |
|---|---|---|---:|---|---|
| Headline | `--ink #E9ECF1` | `#0E1116` | **15.9695** | 4.5 | PASS AAA |
| Accent / wordmark / domain | `--gold #D9A94F` | `#0E1116` | **8.7699** | 4.5 | PASS AAA |
| Tagline / legend / disclaimer | `--ink-soft #99A2B0` | `#0E1116` | **7.3390** | 4.5 | PASS AAA |
| Ruler ticks (**non-text**) | `--ink-faint #6B7482` | `#0E1116` | **4.0035** | 3.0 (SC 1.4.11) | PASS |
| Icon mark, light chrome | `--gold #9A6F1E` | `#FFFFFF` / `#FAFAF8` | **4.5001 / 4.3061** | 3.0 | PASS |
| Icon mark, dark chrome | `--gold #D9A94F` | `#0E1116` / `#161A21` | **8.7699 / 8.0895** | 3.0 | PASS |

**Minimum across the four icon surfaces is 4.3061:1**, clearing the 3:1 non-text threshold by 1.31. *(A "3.88:1 minimum" appears in an upstream draft; it is not derivable from any of the four values and is deleted.)* Note that `4.3061` is the same value that **fails** the 4.5:1 text threshold elsewhere on the site — never reuse it for type.

Three hard rules:

- **`--ink-faint` is banned for type in every image asset, both palettes** (2.9687 light on `--bg`; 4.0035 dark on `--bg`, 3.6929 dark on `--surface`). Ticks only.
- **`--rule #232932` is banned for anything load-bearing** — **1.2920:1** on `--bg`. Differentiate ruler ticks by **height** (6 px minor / 14 px major), not colour, so every tick clears 3:1. *(An upstream draft ships the ruler in `--rule` and calls it "decoration, SC 1.4.3 n/a". SC 1.4.3 is indeed not the criterion — **SC 1.4.11 is**, at 3:1, and the ruler is the entire instrumentation metaphor, not decoration.)*
- **Never use the light remediation values (`#966C1D`, `#7A5716`, `#6D747F`) in an image.** They clear by ≤0.02 in CSS; that headroom does not survive PNG quantisation.

**Legibility at real unfurl sizes (INFERRED — render widths are platform-version-dependent):**

| Surface | Render width | Scale | 58 px headline → | 14 px disclaimer → |
|---|---:|---:|---:|---:|
| X / LinkedIn large card | ~552 px | 0.46× | **26.7 px** | 6.4 px |
| Discord | ~400 px | 0.33× | 19.3 px | 4.7 px |
| Slack | ~360 px | 0.30× | 17.4 px | **4.2 px** |

**Design rule this forces: the headline must carry the entire message alone.** The on-card disclaimer is correct at full size and unreadable at unfurl scale — so it is kept (it costs nothing) but **not relied on**: the independence statement moves into `og:image:alt`, which is read at any size.

### 3.2 NEG-CORE — the shared negative prompt

Paste **verbatim** into every prompt in §3. Per-asset additions are listed under each asset.

```
NEGATIVE: trading card, playing card, card face, card back, card frame, card border,
card sleeve, deck box, booster pack, foil, holographic, set symbol, expansion symbol,
rarity symbol, mana symbol, energy symbol, pip, tap symbol, game logo, publisher logo,
company wordmark, brand mark of any real company, Riot, Riftbound, Pokemon, Magic the
Gathering, Yu-Gi-Oh, One Piece, Bandai, Wizards of the Coast, Konami, Disney, Disney
Lorcana, Lorcana, Flesh and Blood, Digimon, Star Wars Unlimited, fantasy character,
character art, creature, portrait, mascot, anime, illustration of a person, hands
holding cards, tabletop scene, game mat, dice, binder, toploader, card shop, graded
card, grading slab, slab, PSA, BGS, CGC, population report, rocket, rocket ship,
launch, moon, arrow pointing up, upward arrow, ascending line, hockey stick curve,
chart, graph, line graph, bar chart, sparkline, plotted data, trend line, curve, data
points, green candle, candlestick chart, bull, bear, bull market, stock ticker board,
trading floor, Wall Street, money, banknotes, cash, coins, gold coins, treasure, piggy
bank, wallet, credit card, price tag, shopping cart, sale badge, discount starburst,
portfolio, ROI, returns, gains, yield, appreciation, valuation, market cap, index
fund, businessman, businesswoman, handshake, suit and tie, stock photo people, office
scene, crypto, blockchain, NFT, neon glow, cyberpunk, holographic UI, HUD overlay,
sci-fi interface, glassmorphism, lens flare, bokeh, film grain, noise texture,
vignette, drop shadow, bevel, emboss, 3D render, isometric, gradient mesh, watercolour,
brush stroke, hand-drawn, sketch, doodle, photorealism, photograph, motion blur,
confetti, celebration, fireworks, trophy, medal, badge, ribbon, emoji, sticker,
gibberish text, lorem ipsum, misspelled words, watermark, signature, border frame,
rounded card container
```

| Cluster | Why it is there | Weight |
|---|---|---|
| card face / frame / sleeve / booster / foil / set symbol / mana pip / rarity symbol | A card frame is the most recognisable trade dress in this category and the fastest way to manufacture an implied licence, directly against `index.html:339` | **Legal — hard block** |
| named publishers and IP, incl. **Lorcana / Disney / Konami** (added) | Models interpolate these from context. Generating a publisher's mark while disclaiming affiliation is worse than either alone | **Legal — hard block** |
| character art / creature / portrait / anime / mascot | Second-most-recognisable trade dress and the highest copyright-similarity risk in the set | **Legal — hard block** |
| **graded slab / PSA / BGS / CGC / population report** (added) | A slab is simultaneously third-party trade dress **and** the single most investment-coded object in the hobby — the most likely thing a model adds for "trading cards" + "measurement" | **Legal + brand** |
| rocket / moon / upward arrow / ascending line / hockey stick / candlestick / **chart / trend line / curve / plotted data** (promoted from per-asset to NEG-CORE) | Iconography of a *return*, not a measurement. A plotted line necessarily has a **direction**, and a directional line on a shareable card is a price claim against `index.html:326` | **Brand commitment with legal weight** |
| bull / bear / trading floor / Wall Street / ticker board | Securities-market imagery; `docs/tcg-deep-dive-2026.md:147` records that FTC deceptive-practice rules apply to this category | **Brand + FTC exposure** |
| money / coins / treasure / price tag / starburst / **portfolio / ROI / returns / yield / valuation** (added) | The object cluster was covered; the **abstractions** were not. The product is decision support, not a buy signal | **Brand commitment** |
| businesspeople / handshake / office | Implies an institution that does not exist; the site is honest that it is pre-launch (`index.html:332`) | Craft + honesty |
| crypto / neon / HUD / glassmorphism | The default "fintech dashboard" look of image models — speculation-coded, and places the brand in the category it spends a section disclaiming | **Brand commitment** |
| grain / vignette / bokeh / 3D / bevel / gradient mesh / glow | Purely economic: ≈4.7× the byte cost for zero communicative gain | **Performance budget** |
| gibberish / misspelled / lorem ipsum / watermark | No model spells "BountyCharts" or "TCG price × meta" reliably — see §3.0 rule 1 | Craft |
| rounded card container / border frame | A rounded rectangle with a border **is** a card silhouette. Avoiding card art is pointless if the composition is card-shaped | Legal — subtle |

### 3.3 Style anchor (paste at the head of every prompt)

> **STYLE ANCHOR — BountyCharts.** Precision-instrument minimalism. The visual language of a calibrated measuring device — a caliper, an oscilloscope bezel, a surveyor's rod, a laboratory rule — never of a market, a portfolio, or a trade. Flat vector; no perspective, no depth-of-field, no bloom, no gradient mesh, no film grain, no atmospheric haze. Absolutely flat fields of colour meeting at hairline 1-pixel rules. Composition is orthogonal and left-to-right: horizontal baselines, vertical ticks, right angles only. Any implied motion is *lateral and unsigned*, never ascending. Palette strictly limited to: background `#0E1116`, panel `#161A21`, primary text `#E9ECF1`, secondary text `#99A2B0`, hairline/tick `#6B7482`, rule `#232932`, single accent gold `#D9A94F`. Accent gold covers less than 8% of the canvas and marks exactly one thing. Typography, where present, is a monospaced grotesque for labels (uppercase, letter-spacing 0.15em) and a neutral geometric sans for headline (tracking −0.03em); numerals tabular. Enormous negative space — at least 55% of the canvas untouched background. The mood is quiet, exact, slightly austere, and completely unexcited. It should look like the front panel of an instrument that measures something, built by someone who did not want to sell you anything.

Instrumentation is the only visual register that is simultaneously **legal-safe** (nothing mistakable for licensed game art) and **promise-safe** (nothing mistakable for a return). Every clause above does one of those two jobs.

---

### IMG-01 — `og:image` social card `[P0]`

**1200 × 630 · `site/assets/og-card.<hash8>.png` · ≤20,000 B · crawler-fetched only · 0 visitor requests**

#### Purpose

The only social share card. The site has **no `og:image` today**, so every link to it unfurls as bare text on X, Slack, Discord, LinkedIn and iMessage. It is also the only asset with a large byte cost and **zero visitor cost**.

#### Design ruling: the card contains no volatile data

The obvious design mirrors the site's ticker with its four numbers. **Do not.** Two independent caches freeze this file — `immutable` for 365 days (C3) and the platforms' own scrape caches. Any number baked in is a number you cannot correct. Worse, the site's four ticker values are **fabricated** (`index.html:274-293`, each badged `sample`), and a big `+18.4% ▲` lifted out of that context and posted to a timeline is precisely the buy signal `index.html:326` promises never to publish.

The card therefore shows the **metric vocabulary** over a **measurement scale** — a ruler, which has ticks but no slope, no direction and no value. It says "we measure these four things" without asserting any number, and it never needs re-rendering when data changes.

**Corollary, and it is a hard sequencing rule: the card headline is the *resolved* headline from `CNT-01`, not `index.html:269` as it stands today.** Rendering the current H1 into a year-frozen PNG bakes the site's own over-claim into the artefact that travels furthest from the disclaimer forbidding it.

#### Technical spec

| Property | Value |
|---|---|
| Dimensions | **1200 × 630** (40:21), 1× only. A 2× render measured ≈2.2× the bytes for a resolution no unfurl surface renders |
| Format | **PNG, indexed colour (PNG-8), colour type 3, ≤256 palette entries** (target 64) |
| Colour profile | untagged sRGB — emit the 13-byte `sRGB` chunk (intent 0), **no `iCCP`**, no `gAMA`/`cHRM` |
| **Byte budget** | **≤20,000 B, hard, enforced by `TOOL-02`.** *No point figure is quoted as a file property — see §3.4* |
| Variants | **One. Dark only.** Crawlers cannot evaluate `prefers-color-scheme`, and light gold fails AA |
| Composition | **Flat fills only.** The budget assumes ≤64 distinct colours; a gradient, grain or blur pushes the file to 45–50 KB |
| Safe area | content inside x ∈ [60, 1140], y ∈ [75, 555] (survives X's 2:1 crop). Wordmark **also** inside x ∈ [285, 915] (survives a 1:1 centre crop) |
| Render class | **crawler-only** — 0 visitor requests, 0 visitor bytes, 0 ms |
| Cache | `/assets/*` immutable 1 yr. **Content hash in the filename is mandatory** |

**Format is decided by consumer support, and the byte-optimal choice is the same one.** PNG and JPEG are the only formats every OG consumer accepts (INFERRED — no egress to X/LinkedIn/Slack from this session; PNG is the zero-risk choice and costs nothing). On this artwork JPEG measured **≈2.3× larger and ≈6.7× more wrong** than PNG-8/64 — sharp type on a flat ground is the worst case for DCT and the best case for a palette. WebP/AVIF are rejected on crawler support, not size.

Binary images do not recompress at the edge (gzip -9 of a quantised card returns ≈95% of input). **A PNG's on-disk size is its wire size.**

#### (a) Style anchor
§3.3, verbatim.

#### (b) Positive prompt — type as reserved zones, never rendered

> **This prompt deliberately instructs the model to render NO TEXT.** §3.0 rule 1 is not advisory: a model asked for a wordmark returns a garbled wordmark, and a garbled *disclaimer* is worse than a garbled logo. All type is composited afterwards in a vector tool, or — recommended — the whole card is produced deterministically by (e).

```
[PASTE STYLE ANCHOR FROM §3.3 HERE]

SUBJECT: A background plate for an open-graph social card belonging to a
measurement-instrument brand. No object, no scene, no illustration — the plate IS a
flat instrument panel. It carries NO TEXT WHATSOEVER.

COMPOSITION: 1200x630 landscape. Uniform background #0E1116, edge to edge, no
vignette. A single 600px-wide column centred horizontally, leaving 300px of untouched
background on each side. Within that column, top to bottom:
(1) y=56-90: an EMPTY reserved band, 600x34, containing only background — a wordmark
is composited here later. Do not draw anything in it;
(2) y=200-400: an EMPTY reserved band, 600x200, containing only background — a
headline is composited here later. Do not draw anything in it;
(3) y=~450: a horizontal measurement scale exactly 600px wide — a 1px baseline with
1px vertical ticks rising from it, minor ticks 6px tall every 12px, major ticks 14px
tall every 60px. A ruler. Perfectly level. No curve, no data, no slope, no fill;
(4) y=486-506: an EMPTY reserved band, 600x20 — labels are composited here later;
(5) y=~545: a single 1px horizontal rule spanning x=64..1136;
(6) y=560-600: an EMPTY reserved band spanning x=64..1136 — a domain and a
disclaimer line are composited here later.

COLOUR: background #0E1116 only. Ticks and the scale baseline #6B7482. The lower rule
#232932. No other colour appears anywhere. No gold — the accent is reserved for
composited type.

LIGHTING: none. Flat colour fill. No light source, no shading, no glow, no shadow,
no reflection, no ambient occlusion.

TEXTURE: none. Zero grain, zero noise, zero paper fibre, zero gradient. Pure flat
fields meeting at hairline edges.

TYPOGRAPHY: none. This plate carries no text, no letters, no numerals and no symbols
of any kind. Every text zone listed above must be empty background.

SAFE AREAS: the centre 630x630 square (x=285..915) is the crop-safe core; all reserved
zones and the scale sit inside it with at least 15px of clear background inside each
edge. The left and right 285px wings contain ONLY background and the two full-width
hairline rules.

ASPECT RATIO: exactly 1200:630 (40:21).
```

#### (c) Negative prompt

NEG-CORE (§3.2) verbatim, **plus**:

```
, axis labels, numbers, percentages, currency symbols, dollar sign, arrows,
directional indicators, up, down, red and green pairing, dashboard widgets, panels,
tiles, containers, boxes with borders, gradients, glow behind text, coloured
background wash, text, letters, numerals, symbols, logo, wordmark
```

*Additional rationale.* `red and green pairing` is excluded because the `--up`/`--down` semantic is meaningful **in context** on the page and reads as a gain/loss signal **out of context** in a feed. `numbers / percentages / currency` is excluded per the freeze argument above and because the site's only on-page figures are fabricated samples.

#### (d) Parameters per tool

| Tool | Invocation | Notes |
|---|---|---|
| **Midjourney v7** | `--ar 40:21 --style raw --stylize 50 --chaos 0 --weird 0 --seed 20260828 --no <NEG-CORE terms>` | 1200:630 reduces exactly to 40:21. `--style raw` + low `--stylize` are essential — MJ's default stylisation adds glow and grain, i.e. the byte penalty |
| **DALL·E 3 / gpt-image-1** | `size: "1792x1024"`, `quality: "hd"`, `style: "natural"` | No 1.905:1 size exists. Generate 1792×1024, centre-crop to 1792×941, downscale to 1200×630 with Lanczos. `"vivid"` saturates off-token |
| **Firefly** | Aspect Widescreen 16:9, Content type **Art**, Visual intensity **1**, style refs off, effects off | Crop 1792×1008 → 1200×630. "Photo" content type cannot produce a flat field |
| **SDXL / SD3.5** | `1216x640` (both /64), CFG **4.5**, steps **32**, DPM++ 2M Karras, fixed `seed=20260828`, **no refiner, no upscaler**, LoRA weight 0 | Resize to 1200×630. The refiner reintroduces texture |

**Seed discipline.** Fix one seed across the whole family; vary only SUBJECT and COMPOSITION, holding STYLE ANCHOR, COLOUR, LIGHTING and TEXTURE byte-identical. Record model ID, version, exact prompt text, seed and every sampler parameter in `tools/og/PROVENANCE.md` beside the output. Without that record the set cannot be regenerated when one asset needs a revision, and a mismatched re-roll is how a "system" becomes four unrelated pictures.

#### (e) FALLBACK — **this is the recommendation. Ship this.**

Rendered from the site's own CSS tokens: byte-reproducible, exact hex, correct spelling, no legal draw.

**Location matters: `tools/og/` — OUTSIDE `site/`.** `validate_site.py:126` uses non-recursive `SITE.glob("*.html")`, so anything outside `site/` is invisible to the gate and, more importantly, is never deployed. Only the PNG lands in `site/assets/`.

`tools/og/og-card.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BountyCharts og:image render template</title>
<style>
  /* ============================================================
     BountyCharts og:image — render template.  Output 1200x630 PNG.
     NEVER served from site/.  No <script>, no web font, no external ref.
     DARK palette only — see the contrast table in §3.1.
     ============================================================ */
  :root{
    --bg:#0E1116; --ink:#E9ECF1; --ink-soft:#99A2B0;
    --ink-faint:#6B7482; --rule:#232932; --gold:#D9A94F;
    /* PINNED TO FONTS PRESENT AT RENDER TIME.  Only pixels ship, so there is
       zero font-src / CSP implication — but a DIFFERENT font changes geometry,
       palette size and file size.  If you change this stack you MUST re-run the
       square-crop test and re-measure the file; do not carry a byte figure over. */
    --sans:"Liberation Sans","DejaVu Sans",Arial,sans-serif;
    --mono:"Liberation Mono","DejaVu Sans Mono",monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{background:var(--bg)}
  .card{width:1200px;height:630px;overflow:hidden;position:relative;
    background:var(--bg);color:var(--ink);font-family:var(--sans);
    -webkit-font-smoothing:antialiased;
    padding:56px 64px 48px;display:flex;flex-direction:column}

  /* SQUARE-CROP SAFE CORE: a 630x630 centre crop keeps x 285..915. Every
     identity-bearing element sits in a 600px centred column, so the square crop
     loses only decorative rules.  Verified by screenshot. */
  .safe{width:600px;margin:0 auto;display:flex;flex-direction:column;
        align-items:center;text-align:center}

  .brand{display:flex;align-items:center;gap:11px;font-family:var(--mono);
    font-size:22px;font-weight:700;letter-spacing:.02em;color:var(--gold)}
  .brand svg{width:25px;height:25px;display:block;flex:0 0 auto}
  .brand .tag{font-weight:400;font-size:15px;letter-spacing:.18em;
    text-transform:uppercase;color:var(--ink-soft)}

  .mid{flex:1;display:flex;align-items:center;justify-content:center}
  h1{font-size:58px;line-height:1.05;letter-spacing:-.032em;font-weight:700;
     text-wrap:balance;color:var(--ink)}
  h1 .accent{color:var(--gold)}

  /* MEASUREMENT SCALE — a ruler, not a trend line: no direction, no slope,
     nothing readable as a price move.  Ticks are NON-TEXT graphics: SC 1.4.11
     threshold is 3:1 and --ink-faint #6B7482 on #0E1116 = 4.0035:1.  This token
     is used for ticks ONLY and for no type anywhere on this card.  Minor and
     major ticks differ by HEIGHT, not colour, so every tick clears 3:1. */
  .scale{height:14px;margin:0 auto 18px;width:600px;
    background:
      repeating-linear-gradient(90deg,var(--ink-faint) 0 1px,transparent 1px 60px) bottom left/100% 14px no-repeat,
      repeating-linear-gradient(90deg,var(--ink-faint) 0 1px,transparent 1px 12px) bottom left/100% 6px  no-repeat;
    border-bottom:1px solid var(--ink-faint)}

  .legend{display:flex;align-items:center;justify-content:center;gap:13px;
    font-family:var(--mono);font-size:15px;letter-spacing:.15em;
    text-transform:uppercase;color:var(--ink-soft);white-space:nowrap}
  .legend s{text-decoration:none;color:var(--rule)}

  footer{margin-top:40px;border-top:1px solid var(--rule);padding-top:17px;
    display:flex;justify-content:space-between;align-items:baseline;
    font-family:var(--mono);font-size:15px}
  footer .url{color:var(--gold);letter-spacing:.02em}
  footer .disc{color:var(--ink-soft);font-size:14px;letter-spacing:.02em}
</style>
</head>
<body>
<div class="card">
  <div class="safe">
    <div class="brand">
      <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path fill="#D9A94F" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg>
      <span>BountyCharts</span>
      <span class="tag">TCG price × meta</span>
    </div>
  </div>

  <div class="mid">
    <div class="safe">
      <!-- RESOLVED CNT-01 HEADLINE.  Must match site/index.html:269 in the same
           release.  Do NOT render the pre-CNT-01 "next week?" wording. -->
      <h1>What is this deck <span class="accent">actually</span> costing you?</h1>
    </div>
  </div>

  <div class="safe">
    <div class="scale"></div>
    <div class="legend">
      <span>Deck cost</span><s>·</s><span>Movement</span><s>·</s><span>Spread</span><s>·</s><span>Reprint risk</span>
    </div>
  </div>

  <footer>
    <span class="url">bountycharts.com</span>
    <span class="disc">Independent · not affiliated with any card game publisher</span>
  </footer>
</div>
</body>
</html>
```

`tools/og/render.mjs`:

```js
// Renders the og card and the icon rasters.  Requires playwright.
//   node tools/og/render.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';
const here = path.dirname(fileURLToPath(import.meta.url));
const out  = path.join(here, 'out');

const MARK = `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path fill="#D9A94F" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg>`;

const b = await chromium.launch();

// 1200x630 card. deviceScaleFactor MUST be 1 — a 2x render is 4x the pixels for
// zero gain, since no platform displays this above 1200px.
const p = await b.newPage({ viewport:{width:1200,height:630}, deviceScaleFactor:1 });
await p.goto('file://' + path.join(here,'og-card.html'));
await p.waitForTimeout(300);
await p.locator('.card').screenshot({ path: path.join(out,'og-card.png') });

// Square-crop proof: what a 1:1 surface renders.
await p.screenshot({ path: path.join(out,'og-square-crop.png'),
                     clip:{x:285,y:0,width:630,height:630} });

// Icon raster.  0.62 keeps the diamond off the corners.
for (const size of [180]) {
  const q = await b.newPage({ viewport:{width:size,height:size}, deviceScaleFactor:1 });
  await q.setContent(`<body style="margin:0"><div style="width:${size}px;height:${size}px;
    background:#0E1116;display:flex;align-items:center;justify-content:center">
    ${MARK.replace('<svg','<svg width="'+Math.round(size*0.62)+'" height="'+Math.round(size*0.62)+'"')}
    </div></body>`);
  await q.screenshot({ path: path.join(out, `touch-icon-180.png`) });
  await q.close();
}
await b.close();
console.log('rendered to', out);
```

**Post-processing — this is where most of the byte saving lives.** Playwright emits PNG-24. Quantise:

```sh
pngquant --quality 90-100 --speed 1 --strip 64 -o og-card.q.png out/og-card.png
```

Then hand the bare name to the fingerprinter (`TOOL-01`), which computes the hash, names the file and rewrites every reference:

```sh
cp og-card.q.png assets-src/og-card.png
python3 scripts/fingerprint_assets.py
```

#### (f) Insertion markup

`site/index.html` — **insert after line 13 (`og:site_name`), and change line 14 in the same commit.**

```html
<meta property="og:locale" content="en_US">
<meta property="og:image" content="https://bountycharts.com/assets/og-card.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="BountyCharts. What is this deck actually costing you? A measurement scale above four labels: deck cost, movement, spread, reprint risk. Independent project, not affiliated with any card game publisher.">
```

```diff
-<meta name="twitter:card" content="summary">
+<meta name="twitter:card" content="summary_large_image">
```

- **The bare filename is deliberate.** `TOOL-01` rewrites `/assets/og-card.png` → `/assets/og-card.<hash8>.png` at build time. **Do not hand-write a hash** — four upstream drafts hand-wrote four different ones for the same file.
- **`twitter:image` and `twitter:image:alt` are omitted.** X falls back to `og:image` / `og:image:alt`. This saves ≈95 B and, more importantly, halves the number of places the hash must stay in sync. (Fallback behaviour is INFERRED; omission is the low-risk side — a missing `twitter:image` degrades to `og:image`, a stale one 404s.)
- **The `twitter:card` flip is a hard dependency.** `summary` crops 1200×630 to its centre 630×630. The template survives that crop by design, but `summary_large_image` is what the composition is for. `TOOL-03` enforces the pairing.
- **Gate result:** an absolute `https://` URL in a `content=` attribute **passes**. `validate_site.py:217-241` scans `src`/`srcset`/`<link href>`; it never reads `content=`. This is correct, not a hole — the crawler fetches it off-page, so `img-src 'self'` never applies.
- **Fingerprint bonus:** Facebook and X cache a scraped `og:image` **by URL**. A content hash makes every new card a new URL, so re-scrape is automatic and no manual Sharing-Debugger purge is ever needed.
- **`404.html` gets no `og:image`.** It is `noindex` (`404.html:7`) and carries none of the other social tags. A polished share card for an error page is wrong signalling and a wasted 20 KB.

#### (g) Alt text — one string, project-wide

```
BountyCharts. What is this deck actually costing you? A measurement scale above four
labels: deck cost, movement, spread, reprint risk. Independent project, not affiliated
with any card game publisher.
```

**201 characters** (X caps alt at ~420). Three properties are deliberate and each fixes a defect found in an upstream draft:

1. **Contains no digit.** Upstream drafts variously described a card carrying "38 claims audited, 10 materially wrong, 6 unsubstantiated, 33 sources" — content that the design ruling forbids and that the card does not contain. **Alt text asserting data the image does not carry is an accessibility defect in its own right**, read aloud by X and Slack as if it were the card.
2. **Makes no promise.** A draft alt read "Measured, sourced, and dated" — a product claim that is not true today (`index.html` provides provenance for nothing and dates nothing). Alt text describes what the image shows.
3. **Carries the independence statement**, because the on-card disclaimer is illegible at unfurl scale (§3.1) and alt is read at any size.

**Record it once and reference it.** If the card design changes, the alt changes in the same commit — add that to the fingerprint checklist alongside the hash.

#### (h) Acceptance checklist

- [ ] Exactly **1200 × 630 px**, PNG, **colour type 3** (`file` reports `8-bit colormap`, not `8-bit/color RGB`).
- [ ] **≤ 20,000 B.** Above 25 KB, something textured got in.
- [ ] **≤ 256 palette entries.** *(Do not use a "<100 unique colours" criterion — two valid reference builds differ on that and one would fail while passing the byte budget.)*
- [ ] Filename matches `og-card\.[0-9a-f]{8}\.png` and the hash **equals `sha256sum <file> | cut -c1-8` of the file itself** — not merely 8 hex characters.
- [ ] File is in `site/assets/`, **never** the site root (`/og-card.png` matches neither `/assets/*` nor `/*.html` in `_headers` and gets no long cache).
- [ ] Sampling (20,20), (600,120) and (1180,610) returns **exactly `#0E1116`** on all three — proves no gradient, glow or vignette.
- [ ] Every string spelled correctly: `BountyCharts`, `TCG price × meta` (**U+00D7**, not letter x), `bountycharts.com`. No gibberish glyphs.
- [ ] Headline text is the **resolved `CNT-01` wording**, identical to `site/index.html:269` in the same release. No forecast.
- [ ] Contrast, computed not eyeballed: headline **15.9695**, accent/wordmark/domain **8.7699**, tagline/legend/disclaimer **7.3390**, ticks **4.0035** (non-text, 3:1). **No text below 4.5:1; no text uses `#6B7482` or `#232932`.**
- [ ] **Square-crop test:** crop x=285..915, y=0..630 — wordmark, both headline lines, scale and label row all fully present with clear margin.
- [ ] Contains **no numeral, percentage, currency symbol, arrow, ▲ ▼**, and no plotted line.
- [ ] No card shape, publisher name or mark, character, or rounded-rectangle container.
- [ ] The scale is **perfectly level** — sample the baseline y at x=300 and x=900; identical. Any slope is a price claim.
- [ ] `site/index.html:14` reads `summary_large_image` **in the same commit**.
- [ ] `og:image:alt` present, matches §3.3(g) verbatim, **contains no digit**.
- [ ] Font stack in the template unchanged since the last measurement — **or** the square-crop test and the file size were both re-run.
- [ ] `python3 scripts/validate_site.py` → exit 0. `python3 -m unittest discover -s tests` → **26 tests OK**.
- [ ] `python3 scripts/fingerprint_assets.py --check` → exit 0.

---

### IMG-02 / IMG-03 — the ◈ brand mark and favicon system `[P0]`

#### The bug being fixed

`site/index.html:17` and `site/404.html:8` carry an inline `data:` SVG whose only content is `<text y='26' font-size='26'>📈</text>` — **U+1F4C8 CHART INCREASING**.

Two defects, both checkable from the source line alone:

1. **It is a rising-chart glyph** — by definition the imagery C6 forbids, on a page whose own copy at `index.html:326` promises no price predictions. The site's only graphic is a picture of a price going up.
2. **It has no `font-family`.** Its appearance is whatever emoji font the *rendering context* resolves — unbrandable, and an empty box in any surface that rasterises SVG without an emoji font (several bookmark, tile and reader-mode renderers).

It is also not the brand mark: the wordmark at `index.html:262` is **`◈`** (U+25C8).

*(An upstream draft additionally characterised the rendered glyph as "a red line, 48.3% inked". That is not reproducible — the glyph is predominantly the emoji's light card body. Both numbers and the "it is red" claim are dropped; the argument is stronger without them.)*

#### The architecture decision — adjudicated

Two upstream lenses each recommended a different, mutually exclusive favicon architecture. **The adjudication is: ship both halves that are compatible, drop the one that is not.**

| Component | Ship? | Why |
|---|---|---|
| **Twin media-scoped `data:` URIs** (IMG-03) | ✅ **Yes** | Preserves the site's headline property — **1 request, 0 subresources** — and avoids the untested Safari SVG-favicon fallback |
| **`/favicon.ico`** (IMG-02) + its `_headers` rule | ✅ **Yes** | Compatibility hedge for consumers that hardcode `{origin}/favicon.ico` and ignore markup. Cheap, and its `_headers` rule is mandatory |
| `/assets/mark.<hash>.svg` as a file | ❌ **Dropped** | Redundant once the data URIs ship; costs +1 request and a third reference site for a hash |
| SVG file with an internal `<style>` media query | ❌ **Dropped** | Costs a request, and the `<style>`-inside-`data:` variant breaks the suite (§9.2 Trap A) |
| `site.webmanifest` + 192/512 icons | ❌ **Dropped** | §10 |

**Also adopted: hand-hinted 16 px geometry.** At 16 px the diamond-in-diamond's ring thickness scales to ≈1.24 px and collapses into mud. The 16 px ICO entry is a **solid** diamond with no inner cut. *(One upstream checklist demands the ring stay distinguishable at 16×16 from the same 64-unit path; that line is deleted as geometrically impossible.)*

#### IMG-03 — the mark geometry and its two inline forms

**Do not generate this.** A vector mark of this kind is defined by twelve numbers, and a model cannot be told "half-diagonal 29, ring half-diagonal 22, inner half-diagonal 11" in a way that survives sampling.

U+25C8 drawn as **one path with three subpaths and `fill-rule="evenodd"`**: outer diamond fills, ring interior becomes a hole, inner diamond fills again. One element, no stroke, resolution-independent. On a 64×64 grid, centre (32,32): outer half-diagonal 29, ring inner 22 (perpendicular ring thickness (29−22)/√2 ≈ 4.95), inner solid 11.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path fill="#9A6F1E" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg>
```

**188 bytes** flat.

**Form 1 — favicon, twin theme-scoped data URIs. REPLACE `site/index.html:17` AND `site/404.html:8`. Both, or the two pages drift again.**

```html
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path fill='%239A6F1E' fill-rule='evenodd' d='M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z'/></svg>" media="(prefers-color-scheme: light)">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path fill='%23D9A94F' fill-rule='evenodd' d='M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z'/></svg>" media="(prefers-color-scheme: dark)">
```

Two rules, both easy to get wrong and both proven by execution:

- **`#` MUST be percent-escaped as `%23`, and attribute quotes inside the URI MUST be single.** `#` terminates a `data:` URI at the fragment. Left unescaped, the image hard-fails with `EncodingError: The source image cannot be decoded.` The current emoji URI only escapes this because it contains no `#`.
- **Do NOT put a `<style>` with a `prefers-color-scheme` query inside the data URI**, even though it is the obvious way to make one icon theme-aware. It passes the gate and **breaks the test suite** — see §9.2 Trap A. The twin-`media`-link form is the safe equivalent.

**Form 2 — inline in the wordmark. REPLACE `site/index.html:262`.**

```html
<span class="mark"><svg class="glyph" viewBox="0 0 64 64" width="13" height="13" aria-hidden="true" focusable="false"><path fill="currentColor" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg> BountyCharts</span>
```

`fill="currentColor"` inherits `.brand .mark { color: var(--gold) }` (`index.html:96`), so the glyph is theme-correct in **light, dark and print** with zero additional CSS. `aria-hidden="true"` + `focusable="false"` leaves the wordmark's accessible name unchanged. This also removes the site's dependence on the host font having a glyph for U+25C8, which is not guaranteed everywhere.

#### IMG-02 — `/favicon.ico`

| Property | Value |
|---|---|
| Path | **`site/favicon.ico` — root, deliberately NOT fingerprinted** |
| Entries | 16×16 (**solid diamond**, `M8 2 14 8 8 14 2 8Z`, no stroke, no inner cut), 32×32, 48×48 — PNG-compressed |
| Ground | **Opaque `#0E1116` tile**, mark `#D9A94F` |
| Budget | **≤1,500 B** |

**Why the tile is opaque, not stylistic.** A transparent gold mark cannot be legible in both chromes: `#D9A94F` is 8.7699 on dark chrome but **2.16** on white; `#9A6F1E` is 4.5001 on white but **3.67** on Chrome's dark toolbar `#1D1F23`. An opaque tile supplies its own ground and holds **8.7699 everywhere**. It also matches the iOS requirement and gives one identical mark across all deliverables.

**Why it cannot be hashed, and the consequence.** `/favicon.ico` is a protocol convention; the path is the whole point. It therefore matches **neither** `/assets/*` (`_headers:11`) **nor** `/*.html` (`_headers:15`) and would inherit the platform default. **`META-06` must ship in the same commit** — insert before `_headers:14`:

```
# Root-convention files match neither /assets/* nor /*.html, so they would
# otherwise inherit the platform default.  The name cannot be fingerprinted,
# so an explicit short max-age is the only cache control this file can have.
/favicon.ico
  Cache-Control: public, max-age=604800
```

(INFERRED that Cloudflare Pages honours an exact-path rule — not verifiable without a live edge. `_headers` is never served to a browser, so its bytes cost the visitor nothing.)

#### Insertion — the complete icon block, identical on all four pages

`site/index.html` (replacing `:17`), `site/404.html` (replacing `:8`), and the head of `site/method.html` and `site/disclosures.html`:

```html
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path fill='%239A6F1E' fill-rule='evenodd' d='M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z'/></svg>" media="(prefers-color-scheme: light)">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path fill='%23D9A94F' fill-rule='evenodd' d='M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z'/></svg>" media="(prefers-color-scheme: dark)">
<link rel="apple-touch-icon" href="/assets/touch-icon-180.png">
```

**This block must land on every page in one commit.** The two existing pages already carry 11 tags of drift; per-page divergence is the mechanism that produced it, and an upstream new-page template propagated the emoji icon onto two brand-new pages in the same release that removes it from `index.html`.

**Insertion detail that will bite a scripted edit:** head tags in `site/index.html` are at **column 0**, not indented. A `sed` matching two leading spaces silently no-ops. Rules *inside* `<style>` are indented two spaces.

#### Alt text
None. `<link>` has no accessible-name attribute; the bookmark's accessible name comes from `<title>`, which is already correct. Noted so nobody invents an attribute browsers ignore.

#### Acceptance checklist

- [ ] The mark is **one `<path>`** with `fill-rule="evenodd"` and three subpaths. No `<circle>`, `<rect>`, `stroke`, `<g>`, or `<style>` in the inline/data-URI forms.
- [ ] SVG source **≤200 B** flat; each data URI **≤220 chars**.
- [ ] `#` escaped `%23` in every data URI; attribute quotes inside the URI are single.
- [ ] Rendered at **16×16**, the ICO entry is the **solid** diamond variant and reads as a diamond, not a blob.
- [ ] Rendered at 512×512, edges are clean 45° diagonals in the vector source.
- [ ] Contrast, computed: `#9A6F1E`/`#FFFFFF` = **4.5001**, `#9A6F1E`/`#FAFAF8` = **4.3061**, `#D9A94F`/`#0E1116` = **8.7699**, `#D9A94F`/`#161A21` = **8.0895**. All four clear the **3:1** SC 1.4.11 threshold; **minimum across the four is 4.3061**. Note 4.3061 **fails** the 4.5:1 text threshold — never reuse it for type.
- [ ] Inline wordmark glyph uses `fill="currentColor"`, `aria-hidden="true"`, `focusable="false"`.
- [ ] The emoji `<link rel="icon">` is **gone from `index.html:17` and `404.html:8`**, not merely supplemented, and does not appear in any new page's head.
- [ ] `site/_headers` contains the `/favicon.ico` block.
- [ ] `python3 -m unittest discover -s tests` → **26 OK**. *This is the check that catches Trap A; the gate alone will not.*

---

### IMG-04 — `apple-touch-icon` `[P1]`

**180 × 180 · `site/assets/touch-icon-180.<hash8>.png` · ≤1,000 B**

**There is no generative version. Do not write one.** It is IMG-03's path on a solid tile; `tools/og/render.mjs` already emits it.

| Property | Value |
|---|---|
| Design | `#0E1116` full-bleed square, mark at 62% of width (112 px) centred, `#D9A94F` |
| Corners | **Square. No rounding, no transparency, no padding beyond the 19% margin** — iOS applies its own radius and mask; a pre-rounded or alpha icon produces black-cornered artefacts |
| Encoding | PNG-8. A 16-entry palette is mathematically lossless here (the image contains only two colours plus their antialias blend) |
| Budget | **≤1,000 B** |
| Size | 180 px is what iOS requests; one file covers every current device |

**Insertion:** the fourth line of the icon block above. Path-relative and local — `apple-touch-icon` **is** in `FETCHING_REL` (`validate_site.py:188-189`), so an absolute external URL is **blocked by the gate**; a local one passes.

#### Acceptance checklist
- [ ] Exactly 180×180, PNG, **opaque** (no alpha channel), square corners.
- [ ] **≤1,000 B**, indexed colour.
- [ ] Filename `touch-icon-180\.[0-9a-f]{8}\.png`, in `site/assets/`, hash matches file bytes.
- [ ] Pixel (0,0) samples exactly `#0E1116`; pixel (90,90) samples exactly `#D9A94F`.
- [ ] Mark occupies 58–66% of width, centred within ±1 px on both axes.
- [ ] Contrast `#D9A94F`/`#0E1116` = **8.7699** (non-text, 3:1).
- [ ] On an iOS home screen against light and dark wallpaper: legible, corners not black.
- [ ] `href` is root-relative and local.

---

### IMG-05 — `Organization.logo` `[P1]`

**SVG · `site/assets/logo.<hash8>.svg` · ≤2,000 B · Google-fetched only**

**Format decision: SVG, not PNG.** Google **supports SVG for `logo` structured data**, unlike `og:image` which cannot be SVG. That asymmetry is worth exploiting: the mark plus wordmark as flat single-colour SVG lands well under 2 KB against a ≈2–3 KB PNG, is same-origin (`img-src 'self'`), and **removes one raster from the fingerprint surface**.

**Colour:** Google's guidance is that the logo must read on an all-white background. Use **`--ink #14181E` (17.8095:1 on `#FFFFFF`)**. **Do not use `--gold #9A6F1E`, which is 4.5001 on white and fails AA by rounding.**

`Organization.logo` is the only image property Google actually consumes from this site's structured data, and there is currently **no `Organization` node at all** (`index.html:18-26` is a 5-key `WebSite`). This asset and `META-02` land together.

**If this file does not ship, OMIT the `logo` property entirely — do not point it at the og-card.** A 1200×630 share card is not a logo, and a wrong knowledge-panel image gets cached.

#### Acceptance checklist
- [ ] Square or near-square, ≥112 px equivalent, **≤2,000 B**.
- [ ] Single colour `#14181E`; legible on `#FFFFFF` (17.8095:1).
- [ ] Filename `logo\.[0-9a-f]{8}\.svg`; hash matches bytes.
- [ ] No `<script>`, no external `<use href>`, no embedded raster.
- [ ] Referenced by **absolute** URL from the JSON-LD `Organization` node; `TOOL-02` resolves it.
- [ ] Google Rich Results Test accepts the Organization node (**post-deploy; INFERRED, cannot be verified locally**).

---

### IMG-06 — scorecard proportion bar `[P2, conditional on PAGE-01]`

**Inline `<svg>` in `site/method.html` · no file · no request · ≤500 B of HTML**

#### The landing page needs zero images, and that is a feature

Argued honestly, both sides. **For:** every competitor landing page has a product screenshot; the page asks the reader to imagine a product that does not exist; the `.ticker` is a text component wearing `role="img"`. **Against, and this wins:**

1. There is no product to screenshot. A mockup of an unbuilt UI is a fabrication, and the page already carries four fabricated numbers it has to badge.
2. Any chart image is the C6 hazard — the honest visual for "price against meta share" is a line going up and to the right, the one picture this site may not draw.
3. A body image is **visitor-fetched**, unlike everything else here: one more request against a 3,179 B page.
4. The `.ticker` is *better* than an image: selectable, translatable, reflows, respects user font size, already carries an accessible name. `CNT-04`/`CNT-15` do everything an image would, at zero bytes.

#### The one graphic that earns its place

| Property | Value |
|---|---|
| Delivery | **Inline `<svg>`. No file, no request** |
| Size | `viewBox="0 0 100 8"`, `width="100%" height="10"` |
| Budget | ≤500 B of HTML; render-blocking but on a secondary page |
| Colour | `fill="currentColor"` on `<rect>`s wrapped in elements carrying `--up` / `--ink-soft` / `--down` / `--ink-faint` |
| A11y | `role="img"` + `aria-label="38 claims audited: 17 confirmed, 5 partly true, 10 materially wrong, 6 unsubstantiated."` |
| Widths | 17/38 = 44.74 · 5/38 = 13.16 · 10/38 = 26.32 · 15.79 |

**Inline SVG is not a preference here, it is the only correct delivery.** An SVG loaded as `<img>` is an isolated document that **cannot see the page's CSS custom properties at all** — `currentColor` resolves to `rgba(0,0,0,255)`. Matching this site with a file would need a light SVG, a dark SVG, a `<picture>` with `media="(prefers-color-scheme: dark)"` (~180 B extra markup, up to 2 requests) and it would **still print wrong**. Inline, `currentColor` follows light, dark **and** the forced print palette for free.

**Print corollary, for whoever adds any future graphic: never deliver an in-page graphic as a CSS `background-image`.** Browsers drop background graphics from print by default; SVG `fill` is foreground content and prints.

**Gate:** an inline `<svg>` with self-closing `<rect/>` and `<path/>` passes `TagBalance` (`HTMLParser.handle_startendtag` pushes and pops symmetrically) and is markup, not a `<script>`, so the no-executable-script test is not engaged.

#### Acceptance checklist
- [ ] Four `<rect>`s, widths 44.74 / 13.16 / 26.32 / 15.79, summing to 100.
- [ ] Every fill is `currentColor`; no hex inside the SVG.
- [ ] `role="img"` + `aria-label`; counts in the label match `docs/fact-check-ledger.md` at the moment of publication (**recount, do not trust a memory of it — §9.3**).
- [ ] Renders correct colours under light, dark and `emulateMedia({media:'print'})`.
- [ ] No axes, no trend line, no arrow. It is a proportion bar, not a time series.

---

### 3.4 A measurement caveat that applies to every raster figure in this document

**No point byte-figure is quoted as a property of a file.** `pngquant`, `optipng`, `oxipng`, ImageMagick, `cwebp`, `avifenc` and Python PIL are all **absent** from this environment (verified). Every upstream raster figure was produced by a different hand-rolled median-cut quantiser, and they **do not reproduce each other** — three drafts claimed 20,066 / 15,493 / 8,278 B for "the" og card, and re-encoding one draft's own template produced 16,327 B against its claimed 15,493 B.

Two figures *are* reproducible and worth keeping: **a Chromium PNG-24 render of the flat card is ≈44 KB**, and **a textured variant of the same card is ≈4.7× the flat card's shipped size** — those are the numbers that justify quantisation and justify banning texture. Everything else is a **ceiling**:

| Asset | Ceiling | Enforced by |
|---|---:|---|
| `og-card.png` | 20,000 B | `TOOL-02` `ASSET_BUDGETS` |
| `touch-icon-180.png` | 1,000 B | `TOOL-02` |
| `logo.svg` | 2,000 B | `TOOL-02` |
| `favicon.ico` | 1,500 B | manual (not under `/assets/`) |

Re-measure with the real `pngquant` before treating any of these as met.

---

## 4. Content

Every item below carries exact copy, a `file:line` anchor, and a sign-off flag. **⚠️ = requires human sign-off before it ships** (legal, brand, financial, or a factual claim about a third party or the owner).

### CNT-01 — H1 `[P0]` ⚠️ legal/brand

**Anchor:** replace `site/index.html:269` in full.

```html
    <h1>What is this deck <span class="accent">actually</span> costing you?</h1>
```

**Why.** The current H1 is future tense — a forecast — and 57 lines below, the page's load-bearing brand commitment says it will never publish price predictions (`:326`). Whichever a reader believes, the other is false.

**Layout-neutral.** Both strings are **39 characters** (MEASURED — an upstream draft says 38 for both; the equality claim is right, the number is not). Renders to 2 lines at 57.6 px desktop and 33.6 px mobile, identical to today. Keeps the `.accent` span, so no CSS change.

**Do not "fix" the accent's gold.** `h1` computes to 57.6/33.6 px — both ≥24 px, so WCAG large-text applies and the threshold is **3:1**. The accent passes. The **wordmark** does not (`.brand .mark`, same gold at 15.2 px/700 = 4.3061, FAIL) — that is fixed by `CNT-13`, not by editing copy.

**Alternates** if the team wants a different register:

| | Text | Trade-off |
|---|---|---|
| B | `The deck lists are free. <span class="accent">The cards are not.</span>` | Strongest declarative line available; loses the question hook, and `og:title` no longer rhymes with it |
| C | `What did this deck <span class="accent">cost you</span> last week?` | Provably deliverable, wry against the original; weakest motivator |
| D | `Which result <span class="accent">moved</span> this price?` | Matches the one genuine differentiator; narrower promise, narrower audience |

**Sequencing rule: IMG-01 may not be rendered until CNT-01 is signed off**, and the card, the H1, `og:title` and `og:description` ship in **one commit**.

### CNT-02 — lede `[P1]` ⚠️ third-party factual

**Anchor:** replace `site/index.html:270`.

```html
    <p class="lede">Every trading card game has a dozen tools that tell you which deck is best. Few tell you what it costs to build. BountyCharts is being built to tie a price move to the result that caused it — price movement against metagame shift.</p>
```

**Why.** The current line is an **absolute negative claim about ~8 identifiable competitors** ("None of them tell you…"). The research's own wording (`docs/tcg-deep-dive-2026.md:179`) is "none of them do it *well*" — the hedge was dropped on the way to the page.

**What changed from the upstream draft.** That draft restored the "Few" hedge but introduced a *new* unhedged absolute in the same sentence — "and none tie a price move to the result that caused it" — an unsourced universal negative about every competing tool, and the load-bearing differentiator, i.e. the sentence most likely to be quoted back. Nothing in `docs/` substantiates a competitor feature survey. **The fix is to scope it positively:** a claim about your own roadmap needs no source.

### CNT-03 — above-the-fold status line `[P0]`

**Anchor:** new element between `site/index.html:264` (`</header>`) and `:266` (`<main>`) — deliberately outside `<main>`.

```html
  <p class="standing">Pre-launch — nothing on this page is live market data. Last updated <time datetime="DEPLOY_DATE">DEPLOY_DATE_HUMAN</time>.</p>
```

CSS, insert after `site/index.html:169`:

```css
  .standing {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--ink-soft);
    margin: 0;
    max-width: none;
  }
```

**Why this, and why here.** **MEASURED fold geometry, current page:** the four invented figures sit at y=465–576 — entirely above the 800 px desktop fold. The word "Pre-launch" first appears at y=1431 desktop (**1.79 screens down**) and y=2299 on 390×844 (**2.72 screens down**). *A visitor sees the fabricated numbers on first paint and the disclaimer three screens later.* That, not the H1, is the honesty defect with the largest blast radius.

After patch this renders at 12.48 px, `--ink-soft` = **5.9809 light / 7.3390 dark — PASS**, landing at y=121–142 desktop and bottom y=162 on 390×844 — **above the fold on every tested viewport.**

### CNT-04 — ticker caption that is also the accessible name `[P0]`

**Anchor:** replace `site/index.html:273`; add one closing `</div>` after `:294`.

```html
  <div>
  <p class="ticker-cap" id="ticker-cap">Illustrative mock-up: invented figures for a deck cost rising with meta share, a card falling as play rate drops, a price spread, and a reprint-risk flag. BountyCharts is not tracking live data yet.</p>
  <div class="ticker" role="img" aria-labelledby="ticker-cap">
```

```css
  .ticker-cap {
    font-size: 0.85rem;
    color: var(--ink-soft);
    max-width: 62ch;
    margin: 0 0 0.75rem;
  }
```

**Why `aria-labelledby` and not `aria-label`.** It makes the visible disclosure and the accessible name **the same string**, so they cannot drift — and it removes the current situation where the honest disclosure exists *only* for users who cannot see the thing being disclosed. (The strip carries `role="img"`, whose descendants are presentational per ARIA: a screen-reader user currently gets the label and nothing else, so the AT experience is *better* than the sighted one.)

**Placement is measurable and matters.** The caption sits at y=550–617, the strip at y=629 — the reader meets the disclosure **before** the numbers, and both are above the desktop fold. A caption below the strip is read after the claim it qualifies, which is the same failure as the current bottom-of-page "Pre-launch". Caption renders at 13.6 px, **5.9809 / 7.3390 — PASS**.

### CNT-05 — badge legibility `[P0]`

**Anchor:** replace `site/index.html:158-169`. *(Note the anchor: `:158` is `.cell.sample { position: relative; }` and the replacement re-declares it. An upstream draft anchors at `:159-169`, which duplicates that rule.)*

```css
  .cell.sample { position: relative; }
  .cell.sample::after {
    content: "example";
    position: absolute;
    top: 0.6rem; right: 0.7rem;
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-soft);
  }
```

**The defect, MEASURED.** `--ink-faint` at `opacity: 0.75` composites to:

| Theme | Composited | Ratio | Size |
|---|---|---:|---:|
| Light | `#A7AEB9` on `#FFFFFF` | **2.2345** | 9.28 px |
| Dark | `#565E6A` on `#161A21` | **2.6622** | 9.28 px |

Both fail AA **and** the 3:1 non-text floor. It is the least legible text on the site, qualifying the most assertive content on the site. Two further properties the ratio does not capture: it is **CSS generated content**, so it is not in the DOM — not selectable, copyable, translatable, findable by in-page search, or present in any text extraction; and the `@media print` block at `:253` already sets `opacity: 1`, meaning someone previously noticed this was illegible and fixed it **only for print**.

Three changes: **word, size, colour.** `"sample"` → `"example"` because a *sample* can legitimately be a real sample of real data; an *example* cannot. `opacity` is deleted entirely. After patch: **11.52 px, 6.2504 light / 6.7696 dark — PASS both**, a 2.8× improvement. The print override at `:253` becomes a no-op and can be deleted.

**Ship CNT-04 and CNT-05 together.** Either alone leaves a disclosure that cannot be read.

### CNT-06 / CNT-07 — tense and forecast `[P1 / P0 ⚠️]`

- `site/index.html:297`: `<h2>What it does</h2>` → `<h2>What it will do</h2>`
- `site/index.html:301`: `<h3>Deck cost, forecast</h3>` → `<h3>Deck cost, tracked</h3>` ⚠️ **same commitment surface as CNT-01.** The heading says "forecast" while its own body at `:302` is purely retrospective ("what it costs now, what it cost last week"). Fixing the H1 while leaving "forecast" in a subhead resolves nothing.

### CNT-08 — "Why Riftbound first" `[P0]` ⚠️ factual

**Anchor:** replace `site/index.html:319`.

```html
    <p class="tight">Riot's card game launched into the West on 31 October 2025 with an active secondary market and a fast-moving metagame. It is young enough that the price history is thin and the information layer is still forming — which is exactly where this kind of tool is worth building. Other games follow.</p>
```

**Why this deletes rather than cites.** The current line asserts "a permissive fan-content policy". That is asserted at `docs/tcg-deep-dive-2026.md:126`, but **no Riot legal URL exists anywhere in the repo** — the `## Sources` block (`:254-268`) contains none, and `grep -rniE 'riotgames\.com|fan.?content'` over `docs/` returns no URLs. On a page whose thesis is "where a claim could not be substantiated it is marked unsourced rather than repeated" (`README.md:38`), leaving an uncited assertion in the copy is the most damaging small thing on the site.

**Fallback, only if a human verifies the policy URL in the same commit:** append `Riot publishes a fan-content policy that contemplates community projects.` with the link on "fan-content policy" — **no comparative clause about other publishers.** The launch date `31 October 2025` is a ✅ Confirmed row (`docs/fact-check-ledger.md:44`).

### CNT-09 — merged Status + research section `[P1]` ⚠️ published counts

> **Merge note.** Two upstream lenses independently rewrote `site/index.html:330-334` — one adding a dated self-ageing status, one adding a `/method` link, and a third adding a separate "The research" section with three GitHub deep links. Applied in any order, the second edit's anchor is gone. **They are merged here into one section**, and the three deep links live **here only** (not duplicated on `/method`'s "Read it yourself", which links to the same three URLs — see PAGE-01 §6, which is kept because a reader arriving directly at `/method` needs them).

**Anchor:** replace `site/index.html:330-334` entirely.

```html
  <section>
    <h2>Status and research</h2>
    <p class="tight">Pre-launch as of <time datetime="DEPLOY_DATE">DEPLOY_DATE_HUMAN</time>. There is no product yet, and no live data on this page. If that date is a long way behind today, this page has not been kept current and you should treat everything on it as stale.</p>
    <p class="tight">What does exist is the work underneath: an audit of the 2024–2026 trading card game market, a claim-by-claim fact-check of an industry report — 38 claims, each verified, corrected, or marked unsourced — and a runnable unit-economics model. Published in full, including the findings that argue against building this at all.</p>
    <p class="tight"><a href="/method">How a claim gets checked →</a></p>
    <p class="tight stack">
      <a href="https://github.com/kevynsgrin-a11y/BountyCharts/blob/main/docs/tcg-deep-dive-2026.md">Market analysis, 2024–2026 →</a><br>
      <a href="https://github.com/kevynsgrin-a11y/BountyCharts/blob/main/docs/fact-check-ledger.md">Fact-check ledger — 38 claims, each verified, corrected or marked unsourced →</a><br>
      <a href="https://github.com/kevynsgrin-a11y/BountyCharts/blob/main/models/unit_economics.py">Unit-economics model — runnable, no dependencies →</a>
    </p>
  </section>
```

```css
  .stack > * + * { margin-top: 0.5rem; }
```

Five things this does deliberately:

1. **The staleness sentence is the mechanism.** A static site cannot inject a build date into prose, so the copy **tells the reader how to interpret its own staleness**. That is the only self-ageing device available without JavaScript, and it costs 24 words. Corroborating evidence the drift is real: `site/sitemap.xml:5` reads `2026-08-08` at HEAD dated 2026-08-28 — **20 days behind**.
2. **It drops "a primary-source audit."** 12 of 33 sources are primary = 36.4%. The phrase is defensible as a description of *method* and misleading as a description of the *corpus*, and `/method` §2 would directly contradict it.
3. **The framing is "an industry report", not "figures the trade press repeats."** `docs/fact-check-ledger.md:3` states the ledger audits **one** document. The broader framing is an unsourced claim about an unnamed third party, placed in the site's own credibility section.
4. **"including the findings that argue against building this at all" is true and checkable** — `docs/tcg-deep-dive-2026.md:62` (the flagship audience is worth $0), `:145` (the obvious product is self-defeating), `:239` (the report's own #1 priority makes the business worse). It is the highest-trust sentence available to this page and it costs 11 words.
5. **Three deep links replace the single repo-root link**, resolving the brand risk at `README.md:12` (a visitor no longer lands beside a 252,740-byte internal agent prompt) without editing the README. `/blob/main/` follows the branch, which is right for living research and will break if files move. Accepted.

**Maintenance rule:** the `<time datetime>` here, the visible date in `CNT-03`, and every `<lastmod>` in `sitemap.xml` are **one fact in three places** and must move in one commit (`RUN-09`).

### CNT-10 — launch notification `[P1]` ⚠️ **BLOCKED — see preconditions**

#### The constraint space, stated precisely

`site/_headers:6` sets `form-action 'self'`. That governs the target of a **`<form>` submission**. It does **not** govern `<a href>` navigation — the directive that would have (`navigate-to`) was never shipped in any browser. So the option space is wider than "no form, therefore nothing."

| Option | CSP | Gate | Verdict |
|---|---|---|---|
| **1. `mailto:` link** | Not a form and not a fetch; no directive applies | **PASSES** | **Recommended now.** Zero infrastructure, zero third party, zero PII processor, no privacy policy needed. Costs: address is scraped, no double opt-in, poor on mobile webmail |
| 2. `<a>` out to a hosted form (Tally, Buttondown, Google Form) | Top-level navigation — CSP does not apply | **PASSES** | Works, but hands the visitor and their address to a third-party origin with its own trackers, on a site with **zero** third parties and no privacy page. Do not ship before that page exists |
| 3. Amend CSP to `form-action 'self' https://provider` | Requires editing `_headers:6` | Passes | **Reject.** `form-action` is the directive that stops an *injected* form exfiltrating to an attacker. Weakening it buys nothing over option 2 — the visitor lands on the provider's page either way — while adding real risk |
| 4. Cloudflare Pages Function at `/api/subscribe` | Same-origin POST — satisfies `form-action 'self'` **with no CSP change** | `functions/` is outside `site/` | **Technically cleanest, wrong time.** Adds a serverless endpoint, a store, an email sender, PII handling and a mandatory privacy policy to a 6-file static site. The launch-day answer |
| 5. Static Atom feed `/feed.xml` + `<link rel="alternate">` | Same-origin, zero PII | `alternate` is **not** in `FETCHING_REL`, and the href is local anyway | **Adopt when there is a second page's worth of updates.** ~600 B |
| 6. GitHub Watch → Releases | n/a | n/a | Free, honest, zero infra. Low conversion; the audience is GitHub-literate |

**Recommendation: 6 now, 1 + 6 once the mailbox exists, 5 at first release, 4 at launch.**

#### Draft markup — **not paste-ready until the preconditions clear**

```html
  <section>
    <h2>Hearing about launch</h2>
    <p class="tight">There is deliberately no signup form here. This site runs no scripts and calls no third party, and a form would end both. Two ways to hear when it ships:</p>
    <!-- BLOCKED: do not uncomment until `dig MX bountycharts.com` returns a record
         AND a test message sent to the address is received.  Publishing a mailto to
         an unrouted mailbox makes the site's only call to action a silent black
         hole, and the privacy sentence below is the site's ONLY privacy commitment. -->
    <!--
    <p class="tight"><a href="mailto:REPLACE_WITH_ROUTED_ADDRESS?subject=Notify%20me%20at%20launch">Email REPLACE_WITH_ROUTED_ADDRESS</a> — put anything in the body. Your address is used to tell you about launch and for nothing else: not sold, not shared, not added to any other list.</p>
    -->
    <p class="tight"><a href="https://github.com/kevynsgrin-a11y/BountyCharts">Watch the repository on GitHub</a> and choose <em>Custom → Releases</em>. Nothing reaches us that way at all.</p>
  </section>
```

**Four blocking notes:**

1. **No address in this session is anyone's to publish.** The placeholder is deliberate — an upstream draft shipped a literal `hello@…` address that does not exist, in paste-ready markup, with a privacy commitment attached to it.
2. **Do not substitute the maintainer's personal address.** Publishing a personal mailbox on a commercial page is a human decision; git authorship is not consent.
3. **"Sets no cookies" was removed from the draft and must stay removed** until verified. "Runs no scripts" and "calls no third party" are MEASURED true (0 `<script>` beyond `ld+json`, 0 subresources, 1 request). **Cookies are a claim about the edge, not the HTML** — Cloudflare may set `__cf_bm` under bot management, and `bountycharts.com` is egress-blocked here. Verify with `curl -sSI https://bountycharts.com/ | grep -i set-cookie` before any such clause appears anywhere.
4. **The privacy sentence must remain true.** As drafted it permits **exactly one** launch message. Mailing anything further makes it a list and makes the sentence false.

### CNT-11 — `description` and `og:description` `[P0]` ⚠️

**Anchors:** `site/index.html:7` and `:12`.

```html
<meta name="description" content="Pre-launch. BountyCharts tracks trading card prices against metagame shift — what a deck costs, and which result moved it. Riftbound first. The research behind it is published in full.">
```
```html
<meta property="og:description" content="Pre-launch. Price and metagame intelligence for trading card games, starting with Riftbound. The research behind it is published in full.">
```

| Field | Chars | Bytes | Note |
|---|---:|---:|---|
| current `description` | 157 | 157 | ⚠️ 2 over the ~155 desktop truncation point; the part at risk is `Riftbound.`, the differentiator |
| **new `description`** | **179** → **trim to the 155 form below if the SERP snippet matters more than the disclosure** | | see below |
| **new `description` (155-safe)** | **139** | 141 | `Pre-launch. BountyCharts tracks trading card prices against metagame shift — what a deck costs, and which result moved it. Riftbound first.` |
| **new `og:description`** | **137** | 137 | under the 160 OG guideline |
| `<title>` / `og:title` | 50 | 52 | **no change needed** — brand-first, keyword-bearing, and churning it buys nothing on a site with no index history |

**Ship the 139-character form.** Character limits are graded **INFERRED**: Google truncates `<title>` by **pixel width** (~600 px), not characters, and rewrites most descriptions. Treat these as soft targets, not exactness.

**Why both lead with "Pre-launch."** It is the one place a visible caption cannot follow the claim — the disclosure travels with every SERP snippet, unfurl and share.

### CNT-12 / CNT-13 / CNT-14 — 404 and palette

**CNT-12 — `site/404.html:34-39`, replace the `<main>` body `[P2]`:**

```html
<main>
  <span class="brand"><svg class="glyph" viewBox="0 0 64 64" width="13" height="13" aria-hidden="true" focusable="false"><path fill="currentColor" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg> BountyCharts</span>
  <span class="code">404 — PAGE NOT FOUND</span>
  <h1>There is nothing at this address</h1>
  <p>The link may be out of date, or the page may not have shipped yet — most of BountyCharts has not. The site is pre-launch.</p>
  <nav aria-label="Site">
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/method">Method</a></li>
      <li><a href="/disclosures">Disclosures</a></li>
    </ul>
  </nav>
</main>
```

Four problems fixed. **"404 — NO DATA"** (`:35`) is a category error *on this site specifically*: "no data" is an instrumentation state (an empty result set), not a routing state, and using it for a missing URL undercuts the one vocabulary the brand owns. The page carries **no wordmark**, so a visitor from a broken external link sees no brand at all. `.code` fails AA (below). And "may not have shipped yet" is the honest half — "most of BountyCharts has not" turns the error page into a second, unexpected honesty signal at zero cost. The nav replaces a lone back-link and turns a dead end into a map; the repository link is omitted because an error page does not need to send people off-site.

**CNT-14 — `site/404.html:26`, replace `[P1]`:**

```css
  .code { font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.16em; color: var(--ink-soft); font-weight: 700; }
  .brand { font-family: var(--mono); font-size: 0.95rem; font-weight: 700; letter-spacing: 0.02em; color: var(--ink); display: inline-flex; align-items: center; gap: 0.4rem; }
  nav ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 1.1rem; font-size: 0.9rem; }
```

`.code` is currently `--gold #9A6F1E` at 11.52 px / weight 700 = **4.3061 — FAIL AA** (11.52 px bold is *not* large text; bold large starts at 18.66 px). `--ink-soft` gives **5.9809 / 7.3390 — PASS**, and unlike bumping `.code` to ≥18.66 px it does not depend on `CNT-13` landing first. `404.html` already declares `--ink-soft` in all four theme blocks (`:11, :16, :18, :19`) so no new tokens are needed.

**CNT-13 — palette remediation, all four HTML files, ONE commit `[P0]`.** Values and rationale in §1.2. Anchors: `index.html` light `:root` `:28-41` and `[data-theme="light"]` `:54-58`; dark `@media` `:42-48` and `:root[data-theme="dark"]` `:49-53`; `404.html:11, :19`; new pages ship remediated from birth. Add `a:hover { text-decoration-thickness: 2px; }`.

**The full failure inventory, so this cannot be scoped down to "the h2s"** (MEASURED at HEAD against the real body background):

| Selector | Size | Token | Light | Dark |
|---|---:|---|---:|---:|
| `h2` (×4 today, ×6 after CNT-09) | 11.52 px / 700 | `--gold` | **4.3061 FAIL** | 8.7699 |
| `.brand .mark` | 15.2 px / 700 | `--gold` | **4.3061 FAIL** | 8.7699 |
| `a:hover` | body | `--gold-bright` | **2.5175 FAIL** | 11.4237 |
| `.brand .tag` | 11.2 px | `--ink-faint` | **2.9687 FAIL** | **4.0035 FAIL** |
| `.cell .k` | 10.56 px | `--ink-faint` | **2.9687 FAIL** | **4.0035 FAIL** |
| `.three .n` | 10.88 px | `--ink-faint` | **2.9687 FAIL** | **4.0035 FAIL** |
| `404 .code` | 11.52 px / 700 | `--gold` | **4.3061 FAIL** | — |

**Do NOT "fix" the footer disclaimer.** `p { color: var(--ink-soft) }` at `index.html:183` overrides the footer's `--ink-faint`, giving **5.9809 / 7.3390 — PASS**.

**This is the most likely partial-application failure in the whole spec.** `CNT-09` and `PAGE-01`/`PAGE-02` each add gold `<h2>`s; shipping them without `CNT-13` multiplies an existing AA failure across the whole site. Either land `CNT-13` first, or hold `CNT-09`, `PAGE-01` and `PAGE-02` until it does.

### CNT-15 — real Riftbound figures in the ticker `[P2, deferred]` ⚠️ factual

The strongest version of the ticker replaces three invented figures with real, dated, **✅ Confirmed** rows (`docs/fact-check-ledger.md:44-46`): Western launch **31 Oct 2025**; TCGplayer listings **~68,600 → ~118,100 across 30–31 Oct 2025**; **6,300 searches/hour**. These read as instrumentation, not speculation, and none requires card art.

**Three blockers, all of which must clear:**

1. **A source link must exist on-site**, or this reproduces the exact failure the page criticises. Needs `PAGE-01`.
2. **Presentation must be de-directionalised.** The existing `.ticker` cells use `.up` (green) and a `▲` glyph (`index.html:277`). A +72% one-day listings surge rendered green-with-an-up-arrow is momentum imagery — the register C6 forbids **regardless of whether the underlying figure is true and dated**. If `CNT-15` ships: **no `.up`/`.down` class, no ▲/▼**, values in `--ink`, delta stated neutrally (`68,600 → 118,100 listings, 30–31 Oct 2025`), visible dated source link. **Reserve green/red for nothing at all until there is a product.**
3. **Recount the ledger at publication time** (§9.3) — the counts are a live property of a file.

**Explicitly exclude the Kai'Sa Signature $2,356 peak** from any cell. A single card's peak price in a ticker reads as an investment-upside display and collides with C6 regardless of labelling.

*(The upstream "fix the ledger scorecard from 15/6/10/7 first" blocker is **discharged** — see §9.3.)*

---

## 5. New pages

**Two new pages, not eight.** The site goes from 2 URLs to 4.

### 5.1 Candidate ruling — 2 accepted, 6 rejected or merged

| Candidate | Ruling | Reasoning |
|---|---|---|
| Methodology | **ACCEPT → `/method`** | The site already promises this and does not deliver it. `index.html:326` says "what the data says, **and where it came from**"; the site provides provenance for nothing. Largest claim/evidence gap on the site |
| Research index | **MERGE** into `/method` §6 and `CNT-09` | A page that is three links is a worse README than the README |
| About / who is behind this | **REJECT (defer to owner)** | No consented identity exists in the repo. Git authorship is not consent. An anonymous about page is *worse than none* on a site whose pitch is verifiability. The identity claims that do work — independence, no positions, no funding — live on `/disclosures` |
| Changelog | **REJECT** | Nothing has shipped. A changelog whose only entry is "site launched" advertises that nothing happens. GitHub Releases already serves the pre-launch audience |
| Privacy | **MERGE** into `/disclosures` §2 | 0 cookies, 0 forms, 0 JS, 0 accounts, 0 third-party origins. The honest privacy policy is four sentences, and a standalone `/privacy` **implies a data practice that does not exist** |
| Terms | **MERGE** two clauses into `/disclosures` §4 | No accounts, no user content, no payment, no service to terminate. The only operative clauses — no warranty, not investment advice — are two paragraphs |
| Affiliate disclosure | **ACCEPT → `/disclosures`** | `docs/deployment/cloudflare.md:155`: "an affiliate disclosure becomes legally required **before** the first link ships, not after." The page must pre-exist the link |
| Launch-notify page | **REJECT as a page → mechanism (`CNT-10`)** | A dedicated URL for one link is over-building |

**The push-back, stated plainly.** Shipping all eight would take the site from 2 URLs to 10; five would come in under 200 words and three would say "not applicable yet." The cost is not bytes — it is that a 9-item footer on a pre-launch one-pager reads as a site pretending to be larger than it is, which is precisely the credibility failure this project's thesis is built against.

### 5.2 `PAGE-01` — `site/method.html`

| Field | Value |
|---|---|
| **File** | `site/method.html` — **flat, not `site/method/index.html`.** See §9.2 Trap C |
| **URL** | `https://bountycharts.com/method` (**extensionless**) |
| `<title>` / `og:title` | `Method — how BountyCharts grades a claim` (40 ch / 42 B) |
| `description` | `How a claim gets checked: the four grades, the count across 38 audited claims, and the two corrections that cost us something.` (**126 ch**) |
| H1 | `How a claim gets checked` |
| Budget | ≤13,000 B raw / ≈3,700 B brotli, 1 request, **0 subresources**, 0 console messages |

**URL form is decided by the host, not by us.** Cloudflare Pages 308-redirects `/method.html` → `/method` by default and this cannot currently be disabled. Therefore `canonical`, `og:url` and the sitemap `<loc>` **all** use the extensionless form while the file on disk keeps `.html`. Getting this wrong splits every URL in two. The local dev server does **not** do this — `http://127.0.0.1:8899/method` will 404 locally while `/method.html` works. That is expected. **Settle it post-deploy:** `curl -sSI https://bountycharts.com/method.html | head -1` — expect `308`; if `200`, switch every reference to the `.html` form.

#### Content

**Lede.** "BountyCharts is pre-launch. What exists today is the audit underneath it — a claim-by-claim check of an industry report on the 2024–2026 trading card game market. This page is the method: the grades, the counts, and the parts that went against us."

**§1 — The four grades.** One table doing double duty as key and scorecard:

| Grade | Claims | What it means |
|---|---|---|
| Confirmed | 17 | Checked against a source and holds as written. |
| Partly true | 5 | Directionally right, but overstated or missing a qualifier that changes the conclusion. |
| Materially wrong | 10 | The figure or the causal claim does not survive contact with the source. |
| Unsourced | 6 | Could not be substantiated. Marked as unsourced rather than repeated. |
| **Total** | **38** | Fewer than half survived unchanged. |

Closing copy — **rewritten to what the ledger actually supports:**

> *"The last row is the point. Six figures could not be traced to any source we could check — one is attributed to a forum thread, one to a vendor's own marketing copy. They are marked unsourced rather than repeated."*

*(An upstream draft closed with "Six of these are load-bearing figures repeated widely enough that they read as settled fact." Nothing in the repo establishes that any of the six is "repeated widely", and it silently upgrades *unsubstantiated* to *load-bearing* — two unsourced characterisations on the page whose thesis is that unsourced characterisations get marked, not repeated. The replacement is checkable against ledger rows 3.5 and 3.6.)*

Grades render as **words** in mono caps, coloured `--up` / `--gold` / `--down` / `--ink-soft`. Colour is redundant to the word, so SC 1.4.1 is satisfied. No emoji — the repo's ✅⚠️🟡❓ do not survive as meaning-bearing content.

> **Contrast dependency.** In light theme "Partly true" renders in `--gold`. At `#9A6F1E` that is **4.3061 — FAIL AA**, and it only passes once `CNT-13` lands (`#966C1D` = 4.5059). The other three are fine both themes: `--up` 5.1092 / 8.3135, `--down` 5.6425 / 6.4693, `--ink-soft` 5.9809 / 7.3390. **Make the dependency testable, not narrative:** grep the shipped HTML for `#966C1D` (must match) and `#9A6F1E` (must not).

**§2 — Where the sources come from.** ⚠️ **This section needs a decision, see §11 Q6.** The audit cites **33 sources across 29 distinct hosts** (verifiable). The claim that twelve are primary is **not** verifiable — no per-source classification is published anywhere a reader can check. Two options:

- **(a) Publish the classification** — one line per source marking primary/secondary, in the ledger or on `/method`. Cheap, and exactly the artefact the page argues for. Then the percentage is publishable.
- **(b) Drop the percentage and state the method:** *"Where a party's own document exists — an investor filing, a publisher's policy page, a marketplace's developer docs, a company's closure statement — it is cited in preference to coverage of it."*

**Ship (b) unless (a) is done first.** Publishing "36% primary" as the headline honesty statistic, unverifiable, on the page whose subject is that unverifiable numbers are not numbers, is self-refuting.

**§3 — Two checks that cost us something.** Two `.note` blocks.

> **Correction against interest** — "The source report describes backers of the cancelled Altered TCG as left unserved — an aggrieved audience a competitor could capture. They were not left unserved. Equinox is reimbursing backers, players and retailers in full, and released the final set digitally to active accounts. The report also puts the funding threshold at €2.5 million; the figure in Equinox's own statement is €2 million. Publishing that correction removes an audience an acquisition strategy was built around. It went in anyway. **A ledger that only ever corrects in your favour is not a ledger.**"

> **A number we will not quote** — "Analyst forecasts for the trading card game market in 2034–2035 span **$15.8 billion to $24.4 billion** — a 54% spread between firms describing the same market. That dispersion is a measurement-confidence problem, not a growth story. So there is no market-size figure anywhere on this site, and there will not be one."

**§4 — What stays in the repository.** *"Characterising a named company's internal conduct from the absence of a reply is an inference, not a finding. Where the underlying document is public — a published API deprecation notice, a published fan-content policy — the document is cited and the analysis stops there. The full working, including the parts that are argument rather than evidence, is in the repository. It is not hidden; it is just not marketing."*

**§5 — Freshness.** `Last human re-check: DEPLOY_DATE` as a mono stamp, plus: "Prices, policies and affiliate terms move faster than any review cadence. Anything time-sensitive is dated where it appears, or it is not published." *(Do not promise a quarterly cadence — a cadence promise on the credibility page is a decaying liability.)*

**§6 — Read it yourself.** The three `/blob/main/` deep links. Kept despite the duplication with `CNT-09`, because a reader arriving directly at `/method` needs them.

**IMG-06** sits in §1, above or below the grade table.

**Links in:** `index.html` `CNT-09` · `/disclosures` §6 · footer nav on all 4 pages · 404 nav.

### 5.3 `PAGE-02` — `site/disclosures.html`

| Field | Value |
|---|---|
| **File** | `site/disclosures.html` — **flat, plural** |
| **URL** | `https://bountycharts.com/disclosures` |
| `<title>` / `og:title` | `Disclosures — affiliate links and analytics` (43 ch / 45 B) |
| `description` | `Affiliate links, analytics, conflicts of interest, and the limits of what BountyCharts publishes. Written before the first affiliate link.` (**138 ch**) |
| `og:description` | `How BountyCharts makes money, what it measures about you, and what it will never do.` (84 ch) |
| H1 | `Disclosures` |
| Budget | ≤11,000 B raw / ≈3,100 B brotli, 1 request, 0 subresources |

> **Slug ruling.** Upstream lenses split between `/disclosures` (24 references, including a built page) and `/disclosure` (5, including a sitemap `<loc>`). **Plural wins** — it matches the page's H1 and content. Shipping both would put a dead URL in the sitemap and leave the real page unlisted, and **no test can see it** (the sitemap tests check only `<lastmod>` format and url-count == lastmod-count). `TOOL-04` adds the missing assertion.

Lede + a mono `Current as of DEPLOY_DATE` stamp, then six sections.

**§1 Affiliate links.** *"**This site currently contains no affiliate links.** Its outbound links go to the public repository and to the research files inside it, and none of them earn anything."*

> ⚠️ **Do not state a link count.** An upstream draft says "There is exactly one outbound link on the landing page" — false the moment `CNT-09` (5 links) and the footer nav ship. **A compliance page must not state a number its own sibling change set invalidates on day one.**

Then, as an **HTML comment requiring owner assent** — see §4 below for why:

```html
<!-- FORWARD COMMITMENTS — REQUIRES WRITTEN OWNER ASSENT BEFORE UNCOMMENTING.
     <p>When affiliate links exist they are labelled at the point of the link, not
     only on this page. Commission never determines what is shown or in what order.
     This page names each programme in use.</p>
-->
```

Closing (safe to ship): *"This disclosure exists before the first affiliate link rather than after it. That is the order the rules require, and it is also the only order in which a disclosure means anything."*

**§2 Analytics and what is collected.** *"**No accounts. No third-party scripts. No forms.** There is no JavaScript on this site at all — not a tag manager, not a session recorder, not an A/B tool. That is enforced rather than promised: the content security policy blocks scripts from any other origin, and the build will not deploy if a page contains an executable script. This site sets no cookies of its own; check your browser's storage inspector if you want to confirm what the CDN does."*

> ⚠️ **"No cookies" as a bare claim is deleted.** It is a claim about the **edge**, not the HTML, unverifiable from here, and Cloudflare may set `__cf_bm`. One lens removed it from its own draft for this exact reason; another then shipped it **in bold on a compliance page** — the one surface where a false statement converts a gap into a misstatement. The hedged form above is verifiable.
>
> The rest of §2 survives verification: `.github/workflows/deploy.yml` gates deploy on both `validate_site.py` and the unittest suite, and `tests/test_validate_site.py:268` blocks an executable `<script>`, so "the build will not deploy if a page contains an executable script" is **accurate**.
>
> ⚠️ **Constraint on the measurement sentence.** A Cloudflare Web Analytics JS beacon (`<script defer src="https://static.cloudflareinsights.com/…">`) is blocked **three independent ways**: the gate's external-subresource check, the no-executable-script test, and CSP `script-src 'self'`. This paragraph is accurate **only for edge/server-side measurement.** Confirm which form is enabled before publishing it.

**§3 Positions and conflicts.** ⚠️ **Ship as an HTML comment. Do not ship as page copy.**

```html
<!-- NO-POSITION POLICY — REQUIRES WRITTEN OWNER ASSENT BEFORE UNCOMMENTING.
     This asserts facts about the owner's actual conduct. Nothing in the gate or the
     test suite can catch an unassented compliance claim, and an unassented one is a
     self-inflicted FTC/deception exposure that did not exist before the page.

     <div class="note">
       <span class="k">No position policy</span>
       <p>BountyCharts does not hold, trade, or take positions in the cards, sealed
       product or sets it reports on, and does not accept payment for coverage,
       placement, or a favourable reading of any card, deck or product. This matters
       more here than on most sites. A tool that tells thousands of people what is
       about to move, run by someone holding the thing that is about to move, is not
       a tool — it is a position being exited. So the policy is written down first and
       the product is built inside it.</p>
     </div>
-->
```

**The default state of a copy-paste must be omission, not assertion.** A `[OWNER MUST CONFIRM]` marker in prose has a habit of shipping; a comment does not.

**§4 What this site does not do.** No buyout alerts, no price predictions, no investment advice, ever. Not financial advice; cards are not an investment product. As-is, no warranty, data goes stale, verify before spending. *(This is the entire useful content of a `/terms`.)*

**§5 Independence and trademarks.** The canonical home of the `index.html:339` disclaimer, verbatim including the **é**, extended with: *"No card images, card frames, logos or other publisher artwork are hosted or reproduced here."* This is the human- and machine-readable anchor for C6 and should be the URL any brand-safety question is pointed at.

**§6 Corrections.** Errors corrected in public, on the page, dated; conclusion-changing corrections noted rather than quietly edited. Links to `/method` and to GitHub Issues. **No email address** — see §11 Q3.

**Links in:** footer nav on all 4 pages. Deliberately **not** linked from index body copy — the FTC-operative disclosure is the at-the-link label promised in §1, not this page.

### 5.4 Navigation and the landmark consequence

The site has no `<nav>` today. **Minimum navigation is one nav, in the footer, on every page.**

```html
<footer>
  <nav aria-label="Site">
    <ul>
      <li><a href="/" aria-current="page">Home</a></li>
      <li><a href="/method">Method</a></li>
      <li><a href="/disclosures">Disclosures</a></li>
      <li><a href="https://github.com/kevynsgrin-a11y/BountyCharts">Repository</a></li>
    </ul>
  </nav>
  … existing disclaimer + © …
</footer>
```

```css
  footer nav ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 1.1rem; }
  footer nav li { margin: 0; }
  [aria-current="page"] { color: var(--ink-soft); text-decoration: none; }
```
Plus `footer nav { display: none; }` in the `@media print` block.

Seven decisions, each load-bearing:

1. **`<nav>` inside `<footer>` is still a navigation landmark.** Nesting it in `contentinfo` is the honest signal: these are site-footer links, not primary navigation. A 4-page pre-launch site does not have primary navigation.
2. **`aria-label="Site"` is mandatory.** A bare `<nav>` announces as "navigation" with no discriminator. 18 bytes.
3. **Exactly one nav. Do not add a header nav.** Two navs need two labels and give a screen-reader user two landmark stops for four links — and put a link row directly above the H1, which the landing page's composition cannot afford.
4. **No skip link.** On `index.html` **zero** links precede `<main>`; on the new pages, exactly one. A skip link earns its place at roughly 5+ pre-main links. There is nothing to skip.
5. **`aria-current="page"`** on the current entry, styled `--ink-soft` with no underline. Not colour-only — the ARIA state carries it.
6. **The wordmark is a `<span>` on `/` and an `<a href="/">` on subpages** — avoids a self-referential link inside `banner`.
7. **404 gets the nav but no `<footer>`.** It has no banner/contentinfo today; adding them to an error page is not worth ~300 B.

**In-body discovery beats a nav bar here.** `CNT-09` makes `/method` reachable in context, not only from the bottom of the page.

**Landmark structure after:**

| Page | Landmarks |
|---|---|
| `index.html` | `header` (banner), `main`, `div[role=img]`, `footer` (contentinfo), **`nav[Site]`** |
| `method.html` / `disclosures.html` | `header`, `main`, `footer`, `nav[Site]` |
| `404.html` | `main`, **`nav[Site]`** |

### 5.5 Gate-compliance proof

Both new pages carry every item in C4:

| Requirement | Source of truth | Both pages |
|---|---|---|
| literal `lang="en"` | `validate_site.py:31` | ✅ |
| `<title>` | `validate_site.py:32` | ✅ |
| `name="viewport"` | `validate_site.py:33` | ✅ |
| CSS contains `prefers-color-scheme: dark` | `validate_site.py:44` | ✅ inline `<style>` |
| CSS contains `[data-theme="dark"]` | `validate_site.py:45` | ✅ inline `<style>` |
| `<main[\s>]` landmark | `tests/test_validate_site.py:299-306` | ✅ |
| **zero** executable `<script>` | `tests/test_validate_site.py:268-276` | ✅ zero `<script>` tags of any kind |
| no external subresource | `validate_site.py:200-246` | ✅ (GitHub `<a href>` are navigation, not subresources — the gate ignores anchor hrefs) |
| balanced tags | `validate_site.py:68-93` | ✅ |

`INDEX_ONLY_META` (canonical / description / og:title / ld+json) applies to `index.html` only (`validate_site.py:49-54`). The new pages carry canonical, description and og:* anyway.

> ⚠️ **Two paste-ready-head defects fixed here.** An upstream per-page `<head>` template, offered for "any new page", (a) contains **no `<style>`**, so the gate returns `FAIL method.html: missing dark theme` / `missing theme override` and exits 1 — `theme-color` meta deliberately does **not** satisfy `REQUIRED_CSS` (`validate_site.py:36-41`); and (b) carries the **📈 emoji favicon** verbatim, propagating onto two brand-new pages the exact defect §IMG-02 removes. Both are corrected: the page carries the site's token `<style>` block, and the icon block from §IMG-02.

> **JSON-LD on new pages: deliberately none.** An upstream lens specified a full `WebPage` node per page; another declined on the grounds that any `<script>` block is a liability the gate does not require. **The second is right, and the first lens's own finding proves it:** `check_index_meta()` (`validate_site.py:156-169`) reads `index.html` **only**, so JSON-LD on any other page is **never parsed by CI** — a page can ship syntactically broken structured data with a green gate. If per-page `WebPage` nodes are wanted later, extend `check_index_meta()` to `json.loads` every page **in the same commit**, matching the tag quote-agnostically (`<script[^>]*type\s*=\s*["']application/ld\+json["'][^>]*>`) — note that writing the tag with **single quotes** today makes the gate skip JSON validation entirely, even on `index.html`.

**`sitemap.xml`** — see `META-03`. **`robots.txt`** needs no change (`Allow: /` already covers both). **`_redirects`** needs no change.

---

## 6. Metadata and structured data

### META-02 — JSON-LD `@graph` `[P0, no dependencies]`

**Replace `site/index.html:18-26` entirely.**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://bountycharts.com/#website",
      "url": "https://bountycharts.com/",
      "name": "BountyCharts",
      "description": "Price and metagame intelligence for trading card games.",
      "inLanguage": "en",
      "isAccessibleForFree": true,
      "publisher": { "@id": "https://bountycharts.com/#organization" }
    },
    {
      "@type": "Organization",
      "@id": "https://bountycharts.com/#organization",
      "name": "BountyCharts",
      "url": "https://bountycharts.com/",
      "slogan": "TCG price × meta",
      "logo": "https://bountycharts.com/assets/logo.svg",
      "description": "An independent project tracking trading card prices against competitive metagame shifts, starting with Riftbound.",
      "disambiguatingDescription": "BountyCharts is an independent project. It is not affiliated with, endorsed by, or sponsored by Riot Games, The Pokémon Company, Bandai Namco, Wizards of the Coast, or any card game publisher.",
      "sameAs": ["https://github.com/kevynsgrin-a11y/BountyCharts"]
    }
  ]
}
</script>
```

**Three rules this block obeys, each of which someone will otherwise break:**

1. **Non-ASCII uses a JSON `\uXXXX` escape or a literal UTF-8 character — NEVER an HTML entity.** `<script>` is an HTML **raw-text element**: character references are **not decoded** inside it. `&eacute;` would be published as the literal seven characters `&eacute;`, and the gate would pass because `json.loads` sees valid JSON. The result: the site's machine-readable trademark disclaimer — the single highest-value brand-safety property here, and the one Google actually consumes — **misnames The Pokémon Company.** (`é` decodes to `é`; a bare `é` also works, since `index.html:4` declares UTF-8. `×` is the `×` in the slogan.)
2. **The literal substring `"@type": "WebSite",` must survive** — one space after the colon, trailing comma, single string value. `tests/test_validate_site.py:97` mutates that exact substring to prove the gate rejects broken JSON-LD. **Minifying**, moving `@type` to the last key of the node, or making it an array (`["WebSite","CollectionPage"]`) makes the mutation a no-op and the test fails with `AssertionError: 0 != 1`. The ~150 bytes of pretty-printing are the price of the test that guards the block. **Add a source comment above it saying so** — nothing in the file currently explains the dependency.
3. **Use double quotes on the `type` attribute.** Single quotes make the gate skip JSON validation entirely.

**Every value is sourced from something already public:** `name`/`slogan` from `index.html:262-263`; `disambiguatingDescription` **verbatim from `index.html:339`, character for character including the é**; `sameAs` from the site's only outbound link at `:333`; `isAccessibleForFree` is a fact about the site as it exists. `logo` is a bare path that `TOOL-01` fingerprints; **omit the whole property if `IMG-05` does not ship**.

**Verification:** `json.loads` succeeds; gate prints `ok index.html: JSON-LD parses`; browser resolves a 2-node graph.

#### HUMAN INPUT REQUIRED — do not invent any of these

| Property | Status |
|---|---|
| `legalName`, `foundingDate`, `address`, `areaServed` | Not recorded anywhere in the repo |
| `founder` / `employee` / `author` | Git authorship exists but is **not consent to publish an identity** |
| `email` / `contactPoint` | `grep -r mailto site/` returns zero matches. None exists |
| `sameAs` beyond the repo | No social profile exists. The repo URL is a mild stretch (`sameAs` wants an identity page) but defensible; the GitHub *account* URL is a personal identity and a human decision |
| `twitter:site` / `twitter:creator` | No X handle exists |

#### Types considered and rejected

| Type | Verdict | Reasoning |
|---|---|---|
| `potentialAction` / `SearchAction` | **REJECT** | Google deprecated the sitelinks search box (21 Nov 2024) and removed the docs. There is also no search endpoint — the markup would describe a capability that does not exist |
| `FAQPage` | **REJECT** | Restricted to government/health sites (Aug 2023), deprecated entirely (May 2026). Zero rich result, plus a synchronisation liability |
| `BreadcrumbList` | **REJECT for now** | The site is flat. `Home › Method` restates the URL. Revisit only on genuine nesting |
| `Dataset` | **REJECT today, strongest future candidate** | Right type for the 38-claim ledger and the most differentiating type available. An honest `Dataset` needs a `distribution` with a real `contentUrl`; no machine-readable ledger exists. **Unblocks the moment `/assets/ledger.<hash>.csv` ships** |
| `ClaimReview` | **REJECT, flag for later** | Technically perfect, blocked twice: Google's rich result requires approved fact-check-publisher eligibility, and `ClaimReview` requires `itemReviewed.author` — i.e. naming who made each claim. **No claim→source mapping exists in the repo.** Attractive, unshippable, legally sharper than it looks |
| `Project` (subtype of `Organization`) | **REJECT** | More honest semantically, but Google consumes `Organization` for logo/knowledge-panel and does not consume `Project` — and the array `@type` breaks rule 2 above |

### META-03 — `sitemap.xml` `[P0]`

**Replace the whole file.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bountycharts.com/</loc>
    <lastmod>DEPLOY_DATE</lastmod>
  </url>
  <url>
    <loc>https://bountycharts.com/method</loc>
    <lastmod>DEPLOY_DATE</lastmod>
  </url>
  <url>
    <loc>https://bountycharts.com/disclosures</loc>
    <lastmod>DEPLOY_DATE</lastmod>
  </url>
</urlset>
```

- **`<lastmod>` MUST be date-only.** `tests/test_validate_site.py:213-218` asserts `^\d{4}-\d{2}-\d{2}$` — **stricter than sitemaps.org**. A full ISO datetime is legal XML, legal sitemap, and **fails the suite**.
- Every `<url>` needs its own `<lastmod>` (`tests:220-225` compares counts).
- `<loc>` uses the **extensionless** form to match `canonical` and `og:url`.
- `changefreq` and `priority` dropped — Google ignores both, Bing ignores `priority`.
- **`404.html` stays out.**
- The file must contain the literal `https://bountycharts.com/` (`validate_site.py:180`).
- **The shipped file DOES end with a trailing newline** (`od -c` last bytes: `> \n < / u r l s e t > \n`). An upstream instruction to "supply your own newline on append" is wrong and would produce a blank line before `</urlset>`. Replacing the whole file makes it moot.

### META-04 — `robots.txt`: **no change**, documented

`User-agent: * / Allow: /` already covers every new page. Three traps, each a common boilerplate move:

1. **NEVER add `Disallow: /assets/`.** Facebook's and X's card crawlers respect robots.txt, and Google respects it when fetching `Organization.logo`. Blocking the asset directory **silently kills the share card and the logo rich result with no error surfaced anywhere.**
2. **NEVER `Disallow: /404.html`.** Disallowing prevents crawling, which prevents the crawler ever seeing the on-page `noindex`. Allow-all + `noindex` is the correct pairing.
3. The file currently allows GPTBot, ClaudeBot, CCBot and every other AI crawler **by omission**. For a site whose value proposition is being *cited* as a source of audited claims, that is the right default — but it should be a decision on the record, not an accident. (§11 Q7.)

### META-05 — `404.html` head: **no change**, documented

The page carries `robots noindex` at `:7`. Every indexable-surface tag — `canonical`, `description`, the whole OG block, JSON-LD — is dead weight on a page that must never be indexed, and **a `canonical` on a 404 is an active bug** that can cause the error page to be indexed in place of the requested URL. Its absence from the sitemap is likewise correct. **Its 11-tag drift from `index.html` is correct by design, not debt.**

`404.html` **does** receive: the icon block (IMG-02/03), `CNT-12`, `CNT-13`, `CNT-14`.

---

## 7. Insertion runbook

**Ordered. What lands before what, and why.**

| Step | Commit | Contains | Blocks |
|---|---|---|---|
| **RUN-01** | *tooling first* | `TOOL-01` + `TOOL-02` + `TOOL-03` **in ONE commit** | Everything under `/assets/` |
| **RUN-02** | gate hardening | `TOOL-04` (rglob, CSS `url()`, `mask-icon`, `<use\|image href>`, sitemap `<loc>`↔file assertion) + `TOOL-05` | — |
| **RUN-03** | palette | `CNT-13` across all existing pages, + `a:hover` thickness | `CNT-09`, `PAGE-01`, `PAGE-02` |
| **RUN-04** | icons | `IMG-02` + `IMG-03` + `IMG-04` + `META-06`, on `index.html` **and** `404.html` | new pages' heads |
| **RUN-05** | copy, index | `CNT-01`–`CNT-08`, `CNT-11` | `IMG-01` |
| **RUN-06** | copy, 404 | `CNT-12` + `CNT-14` | — |
| **RUN-07** | structured data | `META-02` (+ `IMG-05` if shipping) | — |
| **RUN-08** | social card | `IMG-01` + `META-01` — **`og:image` and `twitter:card` in the SAME commit** | — |
| **RUN-09** | pages | `PAGE-01` + `PAGE-02` + `CNT-09` + nav on all 4 pages + `META-03` — **one commit** | `IMG-06` |
| **RUN-10** | budget latch | raise `TOOL-03` ceilings to the shipped end state (§8) | — |
| *deferred* | | `CNT-10` (MX), `CNT-15` (source link + de-directionalise) | |

#### RUN-01 is the single most important ordering constraint in this document

`/assets/*` is `immutable` for 365 days and `immutable` means the browser will not revalidate **even on a hard reload**. A wrong byte under that prefix is not a bug you fix — it is a bug you wait out for a year.

**A filename-pattern regex does not solve this.** If someone re-exports `og-card.a1b2c3d4.png` and keeps the filename, a regex asserting "8 hex characters" still passes and the edge serves stale bytes for a year. **The check must recompute the hash from the bytes.** That distinction is the whole problem.

**`TOOL-01` — `scripts/fingerprint_assets.py` (producer, stdlib only).** Editable masters in `assets-src/`, never served. Built copies in `site/assets/` as `<stem>.<sha256[:8]><ext>`. Three jobs in one idempotent command:

```
$ python3 scripts/fingerprint_assets.py
write   site/assets/og-card.<hash>.png
retire  site/assets/og-card.<oldhash>.png
rewrite site/index.html
done
```

It (a) emits the hashed copy, (b) **retires the superseded one**, (c) **repoints every reference**. References may be written **bare** — an author writes `/assets/og-card.png` and the tool fills the hash in. One regex on the path segment handles both spellings, so the absolute `og:image` URL, the root-relative `apple-touch-icon` href **and** the JSON-LD `logo` are all rewritten. Re-running with nothing changed prints `up to date`.

> **`ASSET_URL` character class must include `/`** or nested asset dirs false-positive (`/assets/img/nested.png` → `references /assets/img, which does not exist`).

**`TOOL-02` — `check_assets()` in `scripts/validate_site.py` (verifier, what CI runs).** Four checks:

| Failure | Gate message |
|---|---|
| File edited in place, name kept | `name and bytes disagree (name says X, bytes hash to Y)` |
| Unfingerprinted file dropped in | `not fingerprinted — /assets/* is immutable for a year` |
| Rename that missed a reference | `references /assets/…, which does not exist` |
| Asset over budget | `N B exceeds its M B budget` |

**It passes cleanly when `site/assets/` does not exist** — which is the point: the guard is landable **today**, before the first asset, so it is never the thing added after the bug it prevents.

> **Do not `import` the build script from the gate.** `run_gate()` (`tests/test_validate_site.py:30-46`) copies **only `site/` and `validate_site.py`** into its temp dir. `from fingerprint_assets import check` produces `ModuleNotFoundError`, breaking ~9 tests — and insidiously, the remaining tests stay green **for the wrong reason**: the gate crashes with returncode 1, so every test asserting `code == 1` still passes with no check having run. `check_assets()` must be self-contained. The duplicated regex between producer and verifier is a deliberate, documented trade — **add a test asserting the two regexes and the hash rule are identical**, so drift fails loudly. Also worth adding: a `run_gate()` self-check distinguishing "exited 1 because it found a problem" from "exited 1 because it crashed."

**Ordering rule that is easy to miss:** any asset must be built by `fingerprint_assets.py` **before** the commit that references it, because the gate fails a dangling reference. Write the bare name, run the script, commit both together.

#### RUN-09 — the `DEPLOY_DATE` pass

**Every date in this document is the token `DEPLOY_DATE`, never a literal.** Upstream drafts all stamped `2026-08-16`; today is `2026-08-28`. `CNT-09`'s whole mechanism is a page that ages honestly by showing the reader its own staleness — shipping it 12 days stale on day one undercuts the device on first paint, and `CNT-03` puts that stale date above the fold.

**Pre-commit step:** set `DEPLOY_DATE` to today (`date -u +%F`) and apply it in one pass to **all six sites**:

1. `CNT-03` `.standing` — visible date **and** `<time datetime>`
2. `CNT-09` `<time datetime>` **and** visible date
3. `sitemap.xml` `<lastmod>` — **every** `<url>`
4. `/method` §5 `Last human re-check:`
5. `/disclosures` `Current as of`
6. any future `dateModified`

#### Post-deploy verification (cannot be run from this session — egress-blocked)

```bash
curl -sSI https://bountycharts.com/method.html | head -1        # expect 308 → /method
curl -sSI https://bountycharts.com/ | grep -i cache-control     # expect max-age=0, must-revalidate
curl -sSI https://bountycharts.com/favicon.ico | grep -i cache-control  # expect max-age=604800
curl -sSI https://bountycharts.com/ | grep -i set-cookie        # must be EMPTY before any cookie claim
dig MX bountycharts.com                                          # must return a record before CNT-10
```

> **A pre-existing defect this inherits (INFERRED, not verified against a live edge).** `site/_headers:15-16` scopes the HTML cache rule to `/*.html`. Cloudflare Pages serves the landing page at `/`, which does not match `/*.html` — so `max-age=0, must-revalidate` almost certainly **never applies to the landing page today**, and will not apply to `/method` or `/disclosures` either. Like a stale `/assets/*` rule, this looks like dead configuration. The second `curl` above settles it.

---

## 8. Budget ledger

### 8.1 Measured baseline

| Metric | Value | Note |
|---|---:|---|
| `site/` on disk | **15,181 B** | MEASURED |
| `index.html` raw | **11,657 B** | MEASURED |
| `index.html` gzip -9 | 4,026 B | MEASURED |
| **`index.html` brotli q11** | **3,179 B** | **the production wire cost — the only number an asset budget should be compared against** |
| `404.html` raw / brotli | 1,891 / 765 B | MEASURED |
| `sitemap.xml` | 267 B | MEASURED |
| HTTP requests on `/` | **1** | MEASURED |
| `performance.getEntriesByType('resource')` | **`[]`** | MEASURED |
| DOM elements | **76** | MEASURED (the brief's 75 differs on whether `<html>` counts) |
| `loadEventEnd` | **median 21.9 ms** (n≥9, min 18.6 / max 46.7) | The brief's 50 ms and two upstream lenses' 48.7 ms are **cold-start outliers**; any "improvement" measured against 48.7 is noise dressed as a result |

**Compression governs everything below.** HTML brotli-compresses at the edge (11,657 → 3,179 = 27.3%). **Binary images do not** (≈95% of input). A PNG's on-disk size **is** its wire size.

### 8.2 Projected, visitor bytes vs crawler bytes

| Item | Disk | **Visitor pays** | Crawler pays | Render-blocking |
|---|---:|---:|---:|---|
| IMG-01 `og-card` | ≤20,000 | **0 B, 0 req** | ≤20,000 once | No — never fetched by the visitor |
| IMG-02 `favicon.ico` | ≤1,500 | ~0 (see caveat) | ≤1,500 | No |
| IMG-03 twin data URIs | 0 (inline) | ≈+42 B brotli, in-document | — | Parsed, not fetched |
| IMG-04 `touch-icon-180` | ≤1,000 | **0 B, 0 req** | — | No — add-to-home-screen only |
| IMG-05 `logo.svg` | ≤2,000 | **0 B, 0 req** | ≤2,000 | No |
| IMG-06 scorecard bar | 0 (inline) | ≤500 B of HTML, `/method` only | — | Yes, secondary page |
| META-01 og block | +≈500 raw | **+129 B brotli** | — | Parsed, not fetched |
| META-02 JSON-LD | +≈900 raw | **+≈150 B brotli** | — | Not evaluated as script |
| CNT-01…14 copy | +≈2,300 raw | **+≈650 B brotli** | — | Yes (inline CSS) |
| Nav + nav CSS | +≈700 raw | **+≈170 B brotli** | — | Yes |
| PAGE-01 / PAGE-02 | ≤24,000 | **0 B, 0 req** to an index visitor | — | Separate navigations |

**Landing page projection:**

| Metric | Today | Projected | Δ |
|---|---:|---:|---:|
| `index.html` raw | 11,657 | ≈15,000 | +≈3,350 |
| **`index.html` brotli** | **3,179** | **≈4,300** | **+≈1,120 (+35%)** |
| HTTP requests | 1 | **1** | **0** |
| Subresources | 0 | **0** | **0** |
| DOM elements | 76 | ≈105 | +≈29 |
| `loadEventEnd` | 21.9 ms median | **no measurable change** | — |
| Page height, 390×844 | 2,900 px | ≈4,000 px | **+38%** |
| `site/` on disk | 15,181 | ≈63,600 | **≈4.2×** |

**The honest headline.** The `og:image` alone is **≈1.3× the entire current site on disk and ≈6× the compressed landing page — and a visitor never downloads one byte of it.** The repo grows ≈4.2×; **the page a human loads grows ≈35% compressed, stays at one request, and its load time does not move.** That is the trade this document is making, stated plainly.

**Where the visitor genuinely pays:** ≈1,120 compressed bytes of HTML, which is render-blocking because the CSS is inline. At ≈4,300 B the landing page still fits inside a single initial congestion window, so the cost is bytes, **not a round trip.**

**Two costs not hidden.** The mobile page grows ≈38% taller — if judged too much, `CNT-09` is already the merged single section, and the next lever is folding `CNT-10` into it. And **`CNT-13` is not optional**: without it, adding sections multiplies the gold `<h2>` AA failure from 4 selectors to 6.

### 8.3 Hard ceilings

| Ceiling | Value | Rationale |
|---|---:|---|
| **`RENDER_BUDGET`** — HTML plus every subresource actually fetched during load | **20,480 B (20 KiB)** | Projected `index.html` ≈15,000 B leaves ≈5,400 B of headroom, enough for the legitimate CSS-extraction refactor |
| **`TOTAL_BUDGET`** — everything in `site/`, crawler-only assets included | **73,728 B (72 KiB)** | Projected end state ≈63,600 B |
| Per-asset | `og-card.png` 20,000 · `touch-icon-180.png` 1,000 · `logo.svg` 2,000 · default 16,000 | ≈2× a realistic build — loose enough for a design revision, tight enough to catch a photographic replacement |

> ⚠️ **Two corrections to upstream budgets, both proven by execution.**
>
> **(a) The og-card ceiling and the gate ceiling were incompatible.** One lens specified `≤22,000 B` with a 20,066 B reference build; another set a gate ceiling of **16,000 B**. Placing the actual reference file produced `FAIL assets: og-card.<hash>.png is 20,066 B, over its 16,000 B budget`, gate **exit 1** — a spec conflict that reads to a contributor as a broken build. **Resolved: 20,000 B in both places.**
>
> **(b) `TOTAL_BUDGET = 49,152` cannot survive the specs it governs.** The union of all six lenses measured **63,584 B**, failing that lens's own test. **Resolved: 73,728 B.**
>
> **(c) `ASSET_BUDGETS` keys must match the shipped filenames.** The upstream keys were `touch-icon.png` / `logo.png`; the shipped names are `touch-icon-180.png` / `logo.svg`. Neither matched, so both silently fell through to the 16,000 B default and the stated 3,000 B ceilings were **never applied**. **Key on the stem prefix before the first dot**, and add a test asserting every file in `site/assets/` matched a *named* budget rather than the default.
>
> **(d) Land the budget test with the LAST asset it governs, not first.** Landing it first turns CI red on every subsequent commit with a message that misattributes the cause to the contributor.

### 8.4 What I would cut, in order

1. **The web app manifest and its 192/512 icon set. Cut this first.** `manifest` is in the gate's `FETCHING_REL` and browsers fetch it **during load** for install eligibility — it is the only proposed item that breaks the site's headline "1 request", it drags in ≈4.5 KB of icons, and it buys nothing on a site with nothing to install. `theme-color` is already declared per-scheme at `index.html:15-16`, which is the only manifest field the site benefits from.
2. **`IMG-05` `logo.svg`.** Zero visitor cost, but `Organization.logo` only pays off if a Google knowledge panel is plausible, which pre-launch it is not.
3. **`IMG-04` `touch-icon-180.png`.** ≤1 KB, zero visitor cost; genuinely optional.
4. **Shared-CSS extraction to `/assets/site.<hash>.css`.** **Deferred with an explicit trigger** — the token block is duplicated across 4 pages (~2.4 KB raw each). Extraction saves ~7 KB on disk but adds a **render-blocking** request to the landing page, taking it from 1 to 2 and trading the site's best measured property for bytes brotli mostly recovers. **Trigger: 5+ HTML pages, or the shared block exceeding 40% of any page's bytes.** When it happens, `/assets/site.css` is unbustable for 365 days — `/assets/site.<hash>.css` is the only correct spelling.

`IMG-01` and `META-01` are what actually matter, and together they cost ≈129 wire bytes.

---

## 9. New tests and gate checks

### 9.1 `TOOL-03` — `tests/test_assets.py`

Separate file, stdlib only, reusing `run_gate` from the sibling module. Separate because the subject differs **and** because `tests/test_validate_site.py` is being edited in parallel — **the current baseline is 26 tests, not 24.**

| Class | Test | Catches |
|---|---|---|
| `AssetFingerprints` | `unfingerprinted_asset_is_rejected` | a file dropped into `/assets/` without a hash — frozen a year |
| | `asset_edited_in_place_is_rejected` | **the real bug** — same name, different bytes. A name-pattern regex misses this |
| | `dangling_asset_reference_is_rejected` | a rename that missed a reference |
| | `renaming_without_updating_the_reference_is_rejected` | the same, from the other side |
| | `correctly_fingerprinted_asset_is_accepted` | no false positive |
| | `gate_passes_with_no_assets_directory` | landable today |
| | `producer_and_verifier_regexes_agree` | **new** — the deliberate duplication drifting |
| `SocialImage` | `og_image_is_an_absolute_url` | a root-relative `og:image` is **silently dropped** by FB/X/Slack — no image at all |
| | `og_image_requires_summary_large_image` | encodes the `index.html:14` trap so the two tags cannot drift |
| | `og_image_declares_its_dimensions` | without them a crawler must fetch and decode before layout; several render a blank card |
| | `og_image_alt_contains_no_digit` | **new** — enforces the no-volatile-data ruling on the frozen artefact |
| | `og_image_url_resolves_to_a_file` | **new** — covers absolute `https://bountycharts.com/assets/…` inside `content=`, which `check_assets()` alone does not reach |
| `ImagesAreAccessible` | `every_img_has_an_alt_attribute` | — |
| | `decorative_images_are_not_the_only_content_of_a_link` | `alt=""` alone inside `<a>` leaves the link with **no accessible name** — fails SC 2.4.4 **and** 4.1.2 |
| `PayloadBudget` | `render_path_stays_within_budget` (20,480) | — |
| | `total_site_payload_stays_within_budget` (73,728) | — |
| | `every_asset_matched_a_named_budget` | **new** — catches the key-mismatch fall-through (§8.3c) |
| `Navigation` | `sitemap_loc_resolves_to_a_file` | **new** — the `/disclosure` vs `/disclosures` class of bug, which nothing today can see |
| | `icon_block_is_identical_on_every_page` | **new** — the drift mechanism that produced 11 tags of divergence |

**`FETCHED_REL` correction.** The "landing page still needs no subresources" latch — the one test written to protect the site's headline property — used `{stylesheet, preload, modulepreload}`, **excluding `icon`**. In a union build the page genuinely fetched an SVG icon (2 requests, 2 resource entries) and that test still passed. **Add `icon`, `shortcut icon` and `apple-touch-icon`.**

### 9.2 `TOOL-04` — four gate holes and two traps

**Four constructs pass the gate today (exit 0) and are blocked at runtime by the CSP.** Each reproduces as an isolated mutation of the real site.

| Construct | Gate | Why |
|---|---|---|
| `.x{background-image:url('https://cdn.example.com/bg.png')}` | **PASS ✗** | `validate_site.py:239` scans CSS for `@import` only, never `url()` |
| `@font-face{src:url('https://fonts.gstatic.com/x.woff2')}` | **PASS ✗** | same — **the likeliest way a contributor ships a Google Font and finds out in production** |
| `<link rel="mask-icon" href="https://cdn…">` | **PASS ✗** | `mask-icon` ∉ `FETCHING_REL` (`:188-189`) |
| `<svg><use href="https://cdn…/sprite.svg#mark"/></svg>` | **PASS ✗** | not scanned at all; CSP then reports `Unsafe attempt to load URL … Domains, protocols and ports must match.` **An external sprite ships broken rather than failing CI** |

**Fixes, all in one commit:**
1. At ~`:239`, alongside `@import`, scan `css_for(src)` with `url\(\s*['"]?([^'")\s]+)` and flag any `is_external()` hit.
2. Add `"mask-icon"` to `FETCHING_REL` (`:188-189`).
3. Add a scan for `<use\b[^>]*\bhref\s*=` and `<image\b[^>]*\bhref\s*=`.
4. One regression test per hole, in the style of the existing external-subresource tests.

**Trap A — a `<style>` inside an SVG data-URI favicon breaks the suite while the gate stays green.** `tests/test_validate_site.py:146` extracts page CSS with the **non-greedy** `<style>(.*?)</style>`. A theme-aware SVG favicon at `index.html:17` sits *before* the real `<style>` at `:27`, so the regex matches the favicon's inner `<style>` first and mangles the `<link>` into a dangling `</svg>">`. Gate exits 0 and prints "All checks passed"; `test_extracting_css_to_a_stylesheet_is_allowed` fails with `FAIL index.html: </svg> closes <head>`. **Consequence: theme-aware favicons must use twin `media`-scoped `<link>` tags, not an internal `<style>`.** (A `<style>` inside an SVG served as a *file* is fine — but costs a request.)

**Trap B — `"@type": "WebSite",`.** See §6 rule 2.

**Trap C — the gate is blind to subdirectories.** `validate_site.py:126` and `:211` use non-recursive `SITE.glob("*.html")`. A file at `site/nested/index.html` with **no `lang`, no viewport, no `<main>`, an unbalanced `<div>` and `<script src="https://evil.example.com/a.js">`** returns `All checks passed.` and exit 0. `tests/test_validate_site.py:270` and `:300` use the same glob and are equally blind.

**Fix:** change all four to `rglob`. **This must be folded into the same commit that patches `validate_site.py`** — an upstream gate patch that lands alone leaves the gate *looking* freshly hardened with the hole still open, and the `rglob` fix with no owner. Keep the flat-file rule for both new pages as **defence in depth**, labelled as such rather than as the only defence.

### 9.3 `TOOL-05` — the ledger guard's blind spot

`tests/test_validate_site.py:308` (`FactCheckLedgerScorecardIsConsistent`) recounts all 38 rows of `docs/fact-check-ledger.md` and asserts the scorecard matches. **But `.github/workflows/deploy.yml`'s `paths:` filter omits `docs/**`**, so a commit that edits only the ledger will not run the test that guards it. **Add `docs/**` to both the `push` and `pull_request` path lists.**

> **The ledger blocker three upstream lenses gate on is DISCHARGED.** `docs/fact-check-ledger.md:88-91` **already reads 17 / 5 / 10 / 6** at HEAD (corrected in commit `1d17544`), and the test above enforces it. Every "fix the scorecard from 15/6/10/7 first" gate is struck: `CNT-15`, `/method` §1, and the `description` variant carrying the counts are all **publishable now**.
>
> **Replace the blocker with a verification step**, since the counts are a live property of a file: recount before publishing any count, e.g. `python3 -m unittest tests.test_validate_site.FactCheckLedgerScorecardIsConsistent`.

### 9.4 Language discipline

Say **"the deploy check"** when the suite is what catches something, or name the test. The gate alone passes: a page missing `<main>`; a page containing an executable `<script>`; a `<lastmod>` as full ISO datetime; a `<url>` without `<lastmod>`; minified JSON-LD; a data-URI favicon with an internal `<style>`. In every case only the **suite** fails. This matters operationally — `deploy.yml` runs both and `deploy` `needs: validate`, so the suite does block deploy, but a reader who believes `validate_site.py` enforces `<main>` will run it locally, see exit 0, and ship.

---

## 10. What was deliberately NOT specified, and why

Over-building is a real failure mode for a pre-launch one-pager. These were considered and rejected **on evidence**, not overlooked.

| Not specified | Why |
|---|---|
| **A generated hero image or product screenshot** | There is no product to screenshot; a mockup of an unbuilt UI is a fabrication on a page already badging four fabricated numbers. And the honest chart for this product is the one picture C6 forbids |
| **Any in-page image on the landing page** | Zero images is a feature: 1 request, 0 subresources. The `.ticker` is better than an image — selectable, translatable, reflows, respects user font size, already has an accessible name |
| **A generated "editorial texture plate"** | Specified in full so it could be **rejected on evidence**: adding only a radial glow and fine grain to the identical card measured **≈4.7× the flat card's shipped size** in its best shippable encoding — ≈4.8× the entire current site — with ringing around 15 px mono type in JPEG and unreliable WebP support as an og:image. If a plate is ever wanted, author it as CSS gradients in the template |
| **A 2× / 2400×1260 og card** | ≈2.2× the bytes for a resolution no major unfurl surface renders |
| **A light-theme og card** | Crawlers cannot evaluate `prefers-color-scheme`; light gold fails AA at 4.3061 and its remediation clears by 0.0059 — zero headroom baked into a raster |
| **Per-page og cards** | Only 2 real pages will exist. Revisit when `/method` has traffic |
| **`twitter:image` / `twitter:image:alt` / `twitter:title` / `twitter:description`** | X falls back to the `og:*` equivalents. Every omitted copy of the URL is one fewer place a hash update can be missed |
| **`site.webmanifest` + 192/512 icons** | §8.4 item 1 |
| **`mask-icon`** | Superseded, and the gate does not even check its `rel` |
| **Any web font** | `font-src 'self'` requires self-hosting; a woff2 subset is 15–30 KB = 5–9× the compressed page, for a system stack that already renders correctly |
| **WebP / AVIF og card** | Crawler support is the binding constraint, and PNG-8 already beats JPEG here by ≈2.3× |
| **SVG wordmark file for the header** | `◈ BountyCharts` as text costs 0 bytes and 0 requests, is selectable, translatable, scales with user font size, and inherits `--gold` in light/dark/print automatically. An SVG file gets none of that. (U+25C8 coverage on Windows/macOS is **INFERRED** — if it proves absent, the fix is `IMG-03` Form 2, already specified, not a file) |
| **An `/about` page** | No consented identity exists. An anonymous about page is worse than none on a site whose pitch is verifiability |
| **A `/changelog`** | Nothing has shipped. Its only entry would advertise that nothing happens |
| **Standalone `/privacy` and `/terms`** | Merged into `/disclosures`. A standalone `/privacy` **implies a data practice that does not exist**; a ToS governs a relationship that does not exist |
| **A launch-notify page** | A dedicated URL for one link |
| **Third-party email capture (Mailchimp / ConvertKit / Buttondown)** | Blocked by `form-action 'self'`, and the workaround (option 2) hands the visitor to a third-party origin on a site with zero third parties and no privacy page |
| **A Cloudflare Pages Function at `/api/subscribe`** | Technically cleanest and satisfies the CSP with no change — but adds a serverless endpoint, a store, an email sender, PII handling and a mandatory privacy policy to a 6-file static site. **The launch-day answer, not the pre-launch one** |
| **`/feed.xml`** | Correct and cheap (~600 B) — but a one-entry feed on a one-page site is not yet worth it. Adopt at first product release |
| **`Dataset`, `ClaimReview`, `SearchAction`, `FAQPage`, `BreadcrumbList`, `Project`** | §6 |
| **Per-page JSON-LD** | CI cannot validate it (§5.5) |
| **`max-image-preview:large`** | The one image is a static brand card identical on every page; a large preview shows the same thing on every result |
| **Shared-CSS extraction** | §8.4 item 4, deferred with an explicit trigger |
| **The `sample` badge's print override** | Deleted rather than kept — `CNT-05` makes it a no-op |

---

## 11. Open questions requiring a human decision

| # | Question | Blocks | Why it cannot be answered here |
|---|---|---|---|
| **Q1** | **Sign off the H1 change** (`CNT-01`) — or pick alternate B/C/D. | `CNT-01`, `CNT-07`, `CNT-11`, **and `IMG-01`, which renders the resolved headline into a year-frozen PNG** | A brand judgement at the interface between the marketing claim and the no-predictions commitment |
| **Q2** | **Does a routed mailbox exist?** Run `dig MX bountycharts.com` and send a test message. | `CNT-10` | The address does not exist in the repo. Cloudflare Email Routing is free on the existing zone and gives a rotatable alias (INFERRED — not verified against the live zone). **Do not substitute a personal address**; git authorship is not consent |
| **Q3** | **Contact channel for `/disclosures` §6** — GitHub Issues alone, or a `mailto:` too? | `PAGE-02` §6 | Two lenses disagreed; no address in this session is anyone's to publish |
| **Q4** | **Written assent to the no-position policy** and to §1's forward commitments. | `PAGE-02` §1, §3 (both currently HTML comments) | A statement of fact about the owner's conduct. **Nothing in the gate or suite can catch an unassented compliance claim**, and an unassented one converts a gap into a misstatement |
| **Q5** | **Which form of analytics is enabled at the edge?** And does the origin set cookies? | `PAGE-02` §2 | A JS beacon is blocked three ways; only edge/server-side measurement is compatible with the drafted copy. Cookie behaviour is a property of the live edge, egress-blocked here |
| **Q6** | **Publish the per-source primary/secondary classification, or drop the "36% primary" figure?** | `PAGE-01` §2, and the removal of "a primary-source audit" from `index.html` | The 33 sources / 29 hosts denominator is verifiable; the "twelve are primary" numerator is not published anywhere a reader can check |
| **Q7** | **AI-crawler policy on the record.** GPTBot / ClaudeBot / CCBot are currently allowed **by omission**. | `META-04` | Right default for a site whose value is being cited — but it should be a decision, not an accident |
| **Q8** | **Verify or drop the Riot fan-content policy URL.** | `CNT-08` fallback | No Riot legal URL exists in the repo. Either a human finds it (and it ships in the same commit as the citing sentence) or the clause stays deleted |
| **Q9** | **Extensionless vs `.html` URLs**, settled by one `curl` post-deploy. | `canonical`, `og:url`, `sitemap <loc>`, all nav hrefs | Cloudflare Pages' 308 behaviour is a host property |
| **Q10** | **Is `+38%` mobile page height acceptable?** | `CNT-09`, `CNT-10` | A design judgement. If not, fold `CNT-10` into `CNT-09` |
| **Q11** | **Spend commitment:** an ESP at launch (`RUN` deferred, option 4) and any affiliate programme. | `PAGE-02` §1 naming programmes | `docs/deployment/cloudflare.md:154` reserves the ESP spend to the owner |
| **Q12** | **An X handle, if one is wanted.** | `twitter:site` / `twitter:creator` — currently omitted, correctly | None exists. **Do not invent one** |

---

### Appendix A — reconciled ID map

Upstream lens IDs, and where they went.

| Upstream | Here | Fate |
|---|---|---|
| IMG-INV-01 / IMG-PROMPT-01 / SEO-04 / IMPL-01 | **IMG-01** | Merged. Design ruling from IMG-PROMPT-01 (no numerals); alt text, byte ceiling, filename and prompt all replaced |
| IMG-INV-02 | **IMG-02** | Kept + `META-06` made mandatory |
| IMG-INV-03 / IMG-PROMPT-02 | **IMG-03** | Adjudicated to twin data URIs; the `/assets/mark.<hash>.svg` file dropped |
| IMG-INV-04 / IMG-PROMPT-03 / IMPL-02 | **IMG-04** | Kept, point figures → ceiling |
| IMG-PROMPT-04 / SEO-06 / IMPL-03 | **IMG-05** | Format changed PNG → **SVG** |
| IMG-INV-05 | **IMG-06** | Kept; the "ledger is wrong" caveat struck |
| IMG-PROMPT-05 | — | Deferred (§10) |
| IMG-PROMPT-06 | — | Kept as a documented rejection (§10) |
| CNT-PAGE-01…15 | **CNT-01…15** | CNT-PAGE-09 + CNT-PAGE-10 + Lens 4's Status rewrite **merged** into CNT-09; numbering shifts accordingly |
| CNT-IA-01 / -02 | **PAGE-01 / PAGE-02** | Slug fixed to plural |
| CNT-IA-03 / -04 / -05 | **§5.4** + `CNT-09` + `CNT-12` | Merged |
| CNT-IA-06 / SEO-07 | **META-03** | Lens 5's full-file replacement wins; Lens 4's append + trailing-newline note dropped |
| CNT-IA-07 | **CNT-13** | `--gold-bright` changed `#926D2E` → `#7A5716` |
| CNT-IA-08 | **TOOL-04** | Folded into the gate commit |
| CNT-IA-09 | — | **Struck — already fixed at HEAD** |
| CNT-IA-10 | **§8.4 item 4** | Deferred with trigger |
| SEO-01 / -05 | **META-01** | `twitter:image` dropped |
| SEO-02 | **META-02** | `&eacute;`/`Pokemon` → `é` |
| SEO-03 / CNT-PAGE-12 | **CNT-11** | Recounted |
| SEO-08 / -11 | **META-04 / META-05** | Kept verbatim as documented no-changes |
| SEO-09 / -10 | **PAGE-01 / PAGE-02 heads** | `<style>` added, emoji favicon removed, per-page JSON-LD dropped |
| SEO-12 | — | Deferred (§6) |
| IMPL-04 | **META-01** | Alt string replaced |
| IMPL-05 / -06 / -07 | **TOOL-01 / -02 / -03** | Budgets and `FETCHED_REL` corrected |

### Appendix B — one-command verification

```bash
cd /home/user/BountyCharts
python3 scripts/validate_site.py                  # expect: All checks passed. exit 0
python3 -m unittest discover -s tests             # expect: Ran 26 tests ... OK
python3 scripts/fingerprint_assets.py --check     # expect: exit 0  (after RUN-01)
grep -c '"@type": "WebSite",' site/index.html     # expect: 1
grep -rn '&[a-z]\{2,8\};' site/*.html | grep -i 'ld+json' # expect: no output
grep -rn '📈' site/                                # expect: no output (after RUN-04)
grep -rn '#9A6F1E\|#C9973F\|#8A93A1' site/         # expect: no output (after RUN-03)
```

*Note: `python3 -m unittest discover -s tests -t .` fails with `ImportError` — there is no `__init__.py`. CI uses `-s tests -v` with no `-t` (`.github/workflows/deploy.yml:38`).*

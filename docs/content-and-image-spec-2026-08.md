# Content and image generation specification — August 2026

A build specification for every image asset and every piece of content this site needs, with
paste-ready generation prompts, exact insertion markup, and the constraints that make most of the
obvious answers wrong.

**Base commit:** `bfca67a` (merged `main`, after the August 2026 front-end audit)
**Companion document:** [`docs/frontend-audit-2026-08.md`](frontend-audit-2026-08.md)

---

## 1. Read this first: the constraints decide the answers

Nearly every conclusion here is downstream of five constraints. Someone who skips this section will
propose a Google Font, a CDN image and a Mailchimp form, and all three will fail the build.

### 1.1 The CSP forbids every external asset

`site/_headers:6`:

```
default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;
font-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'
```

- Images must be same-origin files or `data:` URIs. **No CDN, no hotlinking, no stock-photo URL.**
- Web fonts must be self-hosted. **No Google Fonts.**
- `form-action 'self'` blocks a third-party form POST — so Mailchimp/ConvertKit/Buttondown
  endpoints are unavailable without amending the policy.

### 1.2 The deploy gate enforces it in every spelling

`scripts/validate_site.py` was hardened in the August audit. **MEASURED** — each row run against a
scratch copy:

| Markup | Gate |
|---|---|
| Local favicon set (`.ico`, PNG, `apple-touch-icon`) | PASSES |
| Local `site.webmanifest` via `<link rel="manifest">` | PASSES |
| Local `<img src>` | PASSES |
| Self-hosted `@font-face` with a local `url()` | PASSES |
| `og:image` `<meta>` — even pointing at a CDN | PASSES (it is metadata, not a fetch) |
| External `apple-touch-icon` | **BLOCKS** |
| External `<link rel="manifest">` | **BLOCKS** |
| `mailto:` link | PASSES |
| External `<a href>` to a hosted form | PASSES (navigation is not a fetch) |
| Local Atom feed via `rel="alternate"` | PASSES (`alternate` is not in `FETCHING_REL`, `validate_site.py:188`) |

The practical reading: **link out freely, fetch nothing externally.**

### 1.3 `/assets/*` is immutable for a year, and there is no build step

`site/_headers:11-12` sets `Cache-Control: public, max-age=31536000, immutable`. Any file placed
under `/assets/` is cached for a year with **no way to invalidate it except changing the filename**.
There is no bundler to generate content hashes.

**Every asset under `/assets/` must therefore carry a content hash in its filename.** This is the
single most likely way this specification ships a bug. Section 7 gives a proven check.

### 1.4 Any new page must satisfy the gate and the suite

`lang="en"` (that literal string) · a `<title>` · `name="viewport"` · CSS containing **both**
`prefers-color-scheme: dark` **and** a `[data-theme="dark"]` selector · a `<main>` landmark ·
**no executable `<script>`** (only `application/ld+json`). `index.html` additionally needs
`rel="canonical"`, `name="description"`, `property="og:title"` and parseable JSON-LD. Every
`<url>` in `sitemap.xml` needs an ISO `<lastmod>`.

### 1.5 Legal and brand limits on imagery — non-negotiable

The footer states the project is **not affiliated with, endorsed by, or sponsored by** Riot Games,
The Pokémon Company, Bandai Namco, Wizards of the Coast, or any card game publisher. The page also
commits that it "does not publish buyout alerts, price predictions, or investment advice."

So no generated image may contain trading-card art, card frames, set or mana symbols, character
art, or any publisher mark — and none may read as investment upside: no rockets, bull/bear motifs,
coins, money piles, trading floors, or up-and-to-the-right hype charts. **The visual language is
instrumentation, not speculation.** Every prompt in section 3 carries these as explicit negatives.

---

## 2. Corrected baseline

The previous audit's headline figure was measured on a local server sending `identity` encoding.
Corrected here, because an asset budget compared against the wrong baseline is worthless.

| Metric | Previously reported | **Corrected (MEASURED)** | Why |
|---|---|---|---|
| Landing page wire cost | "10.2 KB, 1 request" | **3,179 B brotli q11**, 1 request | `index.html` is 11,657 B raw; brotli q11 → 3,179 B (27.3%). Verified with node `zlib`. Gzip -9 → 4,025 B. |
| DOM nodes | 75 | **76 elements** | difference is whether `<html>` is counted |
| load event | 50 ms | **~19–48 ms** | the 50 ms single sample was cold-start noise |
| og:image cost | "typically 40–80 KB" | **~20 KB as PNG-8** | see below |

**This makes the site better than the audit reported: 3.2 KB on the wire, not 10.2 KB.**

Core Web Vitals proxies, **MEASURED** in Chromium (localhost, so no network latency — these are
upper-bound-quality figures, and production CWV remains unmeasured because the site is not live):

| Metric | Mobile 390×844 | Desktop 1280×900 | Google "good" |
|---|---:|---:|---|
| FCP | 72.0 ms | 64.0 ms | < 1800 ms |
| LCP | 72.0 ms | 64.0 ms | < 2500 ms |
| **CLS** | **0.0000** (0 shifts) | **0.0000** (0 shifts) | < 0.1 |

**CLS of exactly zero across zero layout shifts is the thing this specification most endangers.**
It is a direct consequence of shipping no images and no async fonts. Every asset added must
reserve its space with explicit `width`/`height` or it will spend that score.

### 2.1 Why the og:image is ~20 KB and not ~50 KB

I rendered the card from the site's own design tokens and measured every encoding:

| Encoding | Bytes | vs 3,179 B wire baseline |
|---|---:|---|
| Chromium PNG-32 (naive) | 52,923 | 16.6× |
| JPEG q82 | 47,231 | 14.9× |
| WebP q82 | 23,625 | 7.4× |
| WebP q70 | 19,158 | 6.0× |
| **PNG-8, 64-colour palette** | **~20,000** | 6.3× |

The mechanism, **MEASURED independently**: the rendered card contains only **2,905 unique RGB
colours across 756,000 pixels**, and **98.46% of pixels fall in the top 64 colours**. The residue
is antialiasing fringe on type. That is precisely the case PNG-8 exists for.

**The consequence for section 3 is the whole reason this matters:** flat, palette-friendly art
quantises to ~20 KB; a generated image with a gradient, glow, grain or photographic texture holds
tens of thousands of colours, defeats the palette, and lands back at 45–50 KB or worse. **The
brand constraint and the byte constraint happen to point the same way.**

Binary images do not compress further at the edge — **MEASURED**: brotli q11 of the PNG returns
92.6% of original, of the JPEG 84.5%. A PNG's disk size is its wire size.

**But the visitor never pays for the og:image at all.** It is fetched by crawlers and unfurlers,
not by the browser rendering the page. Keep that distinction in every budget argument below.

---
## 3. Reconciliation: conflicts between the specification lenses

Six lenses specified this independently. Before the manifest, the disagreements, resolved:

| Conflict | Lenses | Resolution |
|---|---|---|
| Page filename `disclosure.html` vs `disclosures.html` | SEO-10 vs CNT-IA-02 | **`disclosures.html`** — the IA lens owns page naming; SEO-10's singular is a typo. Shipping both spellings would produce a 404 from the footer link. |
| The og:image is specified three times | IMG-INV-01, IMG-PROMPT-01, SEO-04 | One asset. **IMG-INV-01** owns the technical spec, **IMG-PROMPT-01** the artwork, **SEO-04** the tags. |
| The brand mark is specified three times | IMG-INV-03, IMG-PROMPT-04, SEO-06 | One asset, SVG. Note SEO-06 wants it for `Organization.logo`, which Google prefers as raster — see §6. |
| Ledger correction proposed | CNT-IA-09 | **Already shipped** this session as `AUDIT-C2` — the scorecard said 15/6/10/7, the rows are 17/5/10/6. |
| Extracting CSS to `/assets/site.<hash>.css` | CNT-IA-10 | **Deferred, correctly.** It would add a second request and a render-blocking dependency to a page that currently has neither. |

---

## 4. Master manifest

48 specified items: 21 copy, 13 image, 10 metadata, 4 page. Priorities as assigned by the specifying lens.

| id | kind | target | priority | budget |
|---|---|---|---|---|
| `IMG-INV-01` | image | `site/assets/og-card.<hash8>.png (fingerprinted, MANDATORY ` | P0 | <=22,000 B. MEASURED on a real 1200x630 Chromium render: PNG-8/64 = 20 |
| `IMG-INV-02` | image | `site/favicon.ico (ROOT, deliberately NOT fingerprinted — /` | P0 | 1,206 B MEASURED (component PNG-8 entries: 16px=149 B, 32px=373 B, 48p |
| `IMG-INV-03` | image | `site/assets/mark.<hash8>.svg (fingerprinted, MANDATORY — e` | P0 | 244 B on disk MEASURED. Wire cost on first visit 435 B (244 B body + 1 |
| `IMG-INV-04` | image | `site/assets/touch-icon.<hash8>.png (fingerprinted, MANDATO` | P1 | 1,380 B MEASURED (PNG-8/64). 0 desktop requests — MEASURED not fetched |
| `IMG-INV-05` | image | `INLINE in site/method.html — no file, no /assets/ entry, n` | P2 | <=500 B of HTML (~430 B typical). 0 requests. Render-blocking, but on  |
| `IMG-PROMPT-01` | image | `site/assets/og-card.f36a278c.png` | P0 | 15,493 B on disk. CRAWLER-ONLY - not render-blocking, not lazy, fetche |
| `IMG-PROMPT-02` | image | `site/index.html:17 (twin data: URIs) + site/index.html:262` | P0 | +403 B brotli for this entire section. ZERO additional HTTP requests ( |
| `IMG-PROMPT-03` | image | `site/assets/touch-icon-180.deb4fbbb.png` | P1 | 582 B. Fetched ONLY on add-to-home-screen or bookmark - MEASURED zero  |
| `IMG-PROMPT-04` | image | `site/assets/logo-512.59a79860.png` | P1 | 2,166 B. Crawler-only - zero visitor requests, zero visitor bytes. |
| `IMG-PROMPT-05` | image | `site/assets/og-method.<hash>.png` | P2 | ~15,000 B (same encoding profile as IMG-PROMPT-01). Crawler-only, 0 vi |
| `IMG-PROMPT-06` | image | `(not shipped - specified to be rejected on evidence)` | P2 / DO NOT SH | REJECTED ON MEASUREMENT. Adding only a radial glow plus fine grain to  |
| `CNT-PAGE-01` | copy | `site/index.html` | P0 | -1 byte raw. Render-blocking (inline document). No new requests. |
| `CNT-PAGE-02` | copy | `site/index.html` | P1 | +16 bytes raw. Render-blocking. No new requests. |
| `CNT-PAGE-03` | copy | `site/index.html` | P0 | +about 175 bytes raw (copy + CSS rule). Render-blocking. No new reques |
| `CNT-PAGE-04` | copy | `site/index.html` | P0 | +about 330 bytes raw. Render-blocking. No new requests. +2 DOM element |
| `CNT-PAGE-05` | copy | `site/index.html` | P0 | +2 bytes raw (-59 if the now-dead print override is also removed). Ren |
| `CNT-PAGE-06` | copy | `site/index.html` | P1 | +5 bytes raw. Render-blocking. |
| `CNT-PAGE-07` | copy | `site/index.html` | P0 | -1 byte raw. Render-blocking. |
| `CNT-PAGE-08` | copy | `site/index.html` | P0 | -24 bytes raw (delete-only variant). Render-blocking. |
| `CNT-PAGE-09` | copy | `site/index.html` | P1 | +30 bytes raw. Render-blocking. +1 DOM element (<time>). |
| `CNT-PAGE-10` | copy | `site/index.html` | P1 | +about 800 bytes raw / +about 230 brotli. Render-blocking. No new requ |
| `CNT-PAGE-11` | copy | `site/index.html` | P1 | +about 730 bytes raw / +about 210 brotli. Render-blocking. No new requ |
| `CNT-PAGE-12` | metadata | `site/index.html` | P0 | +51 bytes raw. Render-blocking (in <head>). No new requests. |
| `CNT-PAGE-13` | copy | `site/404.html` | P2 | +about 200 bytes raw / +about 45 brotli. Render-blocking. No new reque |
| `CNT-PAGE-14` | copy | `site/404.html` | P1 | +about 145 bytes raw. Render-blocking (inline <style>). |
| `CNT-PAGE-15` | copy | `site/index.html` | P2 | +0 to +150 bytes raw (replaces existing cell content). Render-blocking |
| `CNT-IA-01` | page | `site/method.html` | P0 | MEASURED 12,871 B raw / 3,656 B brotli q11 / 110 elements / 666 visibl |
| `CNT-IA-02` | page | `site/disclosures.html` | P0 for launch, | MEASURED 10,460 B raw / 3,039 B brotli q11 / 73 elements / 630 visible |
| `CNT-IA-03` | copy | `site/index.html` | P0 | Landing page MEASURED before/after: 1 → 1 HTTP request, resource entri |
| `CNT-IA-04` | copy | `site/index.html` | P0 | Included in the +701 B raw / +171 B brotli landing-page delta above. A |
| `CNT-IA-05` | copy | `site/404.html` | P1 | MEASURED 1,891 → 2,147 B raw (+256 B), brotli 765 → 839 B (+74 B), 15  |
| `CNT-IA-06` | metadata | `site/sitemap.xml` | P0 | MEASURED 267 → 600 B raw, 166 → 184 B brotli. Crawler-fetched only; co |
| `CNT-IA-07` | copy | `site/index.html + site/404.html + site/method.html + site/` | P0 | 0 bytes net (hex-for-hex substitution). No new request, no subresource |
| `CNT-IA-08` | metadata | `scripts/validate_site.py + tests/test_validate_site.py` | P1 | 0 bytes shipped — build tooling only, never served. No effect on any p |
| `CNT-IA-09` | copy | `docs/fact-check-ledger.md` | P0 BLOCKER for | Repo doc, not served. 0 bytes on the wire. |
| `CNT-IA-10` | metadata | `site/assets/site.<contenthash>.css  [DEFERRED — do not bui` | P2 / deferred  | If built: ~2.4 KB raw / ~900 B brotli shared, saving ~7 KB on disk acr |
| `SEO-01` | metadata | `site/index.html` | P1 | 412 B raw, +93 B brotli measured (3,324 -> 3,417 on index.html). Crawl |
| `SEO-02` | metadata | `site/index.html` | P0 | 1,120 B raw block, up from 246 B. Page delta +874 B raw / +145 B brotl |
| `SEO-03` | copy | `site/index.html` | P1 for variant | -16 B raw (variant A shortens the file). Crawler-only; the description |
| `SEO-04` | image | `site/assets/og-card.<contenthash>.png` | P1 | <=40 KB hard ceiling, <=25 KB target. CRAWLER-ONLY: adds 0 bytes and 0 |
| `SEO-05` | copy | `site/index.html` | P1 | Included in SEO-01's 412 B. Crawler-only. |
| `SEO-06` | image | `site/assets/logo.<contenthash>.svg` | P2 | <=2 KB. Crawler-only (Google image fetch); never fetched during page r |
| `SEO-07` | metadata | `site/sitemap.xml` | P0 for the las | 402 B raw / 155 B brotli for 3 URLs, versus 267 B raw / 166 B brotli f |
| `SEO-08` | metadata | `site/robots.txt` | P0 as a docume | 70 B, unchanged. Crawler-only. |
| `SEO-09` | page | `site/method.html` | P1 | ~1,050 B raw of head metadata. Metadata-only skeleton measures 2,590 B |
| `SEO-10` | page | `site/disclosure.html` | P1 | ~1,000 B raw of head metadata; skeleton 2,006 B raw. Separate navigati |
| `SEO-11` | metadata | `site/404.html` | P0 as a docume | 1,891 B, unchanged. 0 delta. |
| `SEO-12` | metadata | `site/index.html` | P2 | ~520 B raw / ~85 B brotli for the node. The CSV itself: 38 rows, budge |

---

## 5. Image assets — inventory, specs and prompts

### 5.1 Technical inventory and byte specs

#### Lens 1 — Image asset inventory and technical specs

Every number below is **MEASURED** in this session unless graded otherwise. Method: Chromium 1194 via Playwright against `http://127.0.0.1:8899/` and against two patched scratch copies of `site/`; PNGs encoded by a purpose-written Node encoder (no PIL, pngquant, ImageMagick, cwebp or avifenc exist in this container — verified); contrast by the WCAG 2.x sRGB-linearisation formula; the gate and the 24-test suite run for real against every proposed markup form.

**Verdict up front: 4 files ship, 1 is conditional, and 6 candidate assets are rejected.** The landing page keeps zero in-page images. Total new bytes on disk 22,896; total new bytes the *visitor* pays on a first visit **435**, and on every subsequent visit **0**.

---

##### Corrected baseline

The brief's baseline needs three corrections before any budget is set against it.

| Claim in brief | Measured | Note |
|---|---|---|
| 75 DOM nodes | **76 elements** | matches Phase 1; the difference is whether `<html>` is counted |
| 10.2 KB transferred | **11,846 B** (CDP `encodedDataLength`), 1 request | local server sends **identity**; this is uncompressed |
| — | **3,179 B** (brotli q11) | **this is the production wire cost** and the only number an asset budget should be compared against |
| load event 50 ms | **21.3 ms median** (n=9, min 18.3 / max 44.1) | the single-sample 50 ms figure is cold-start noise |
| og:image "typically 40–80 KB" | **20,066 B** | see §2 — the estimate is 2–4× too pessimistic once the PNG is quantised |

Compression evidence that governs everything below: HTML brotli-compresses at the edge (11,657 → 3,179 = 27.3%), **binary images do not** (measured: gzip -9 of the 20,066 B card returns 19,011 B = 94.7%; of the 49,230 B PNG-32, 92.4%). A PNG's on-disk size *is* its wire size.

---

##### IMG-INV-01 — `og:image` social card `[P0]`

The only asset with a large byte cost and the only one that costs the visitor nothing at all.

| Property | Value |
|---|---|
| Path | `/assets/og-card.<hash8>.png` — e.g. `og-card.7293c1d5.png` |
| Dimensions | **1200 × 630** (1.905:1), 1× only |
| Format | **PNG, indexed colour (PNG-8), ≤64 palette entries** |
| Colour profile | **untagged sRGB**: emit the 13-byte `sRGB` chunk (rendering intent 0), **no `iCCP`**, no `gAMA`/`cHRM` |
| Byte budget | **≤22,000 B. Measured on a real render: 20,066 B.** |
| Light/dark variants | **One. Dark only** (`--bg` #0E1116). See §2b |
| Render class | **Crawler-only.** 0 visitor requests, 0 visitor bytes, 0 ms |
| Cache | `/assets/*` → `max-age=31536000, immutable`. **The hash in the filename is the only cache-buster and is mandatory** |

**Format is decided by consumer support, not by bytes — and the byte-optimal choice happens to be the same one.** Measured on the same 1200×630 render:

| Encoding | Bytes | Mean per-channel error vs lossless | % pixels off by >8 |
|---|---:|---:|---:|
| Chromium PNG-32 (naive) | 49,230 | 0 | 0 |
| **PNG-8, 64 colours** | **20,066** | **0.106** | **0.665** |
| PNG-8, 16 colours | 16,006 | 0.265 | 1.28 |
| PNG-8, 256 colours | 22,053 | 0.039 | 0.26 |
| JPEG q82 | 45,712 | 0.71 | 3.66 |

JPEG is **2.28× larger and 6.7× more wrong** than PNG-8/64 — sharp type on a flat ground is the worst case for DCT and the best case for a palette. WebP/AVIF are rejected on crawler support, not size: PNG and JPEG are the only formats every OG consumer accepts (INFERRED — no live network to X/LinkedIn/Slack from this session; PNG is the zero-risk choice and costs nothing here). **The naive 49,230 B PNG-32 is what lands in the brief's 40–80 KB estimate; quantisation is the whole difference.**

**Rejected: a 2× card.** Measured at 2400×1260, PNG-8/64 = **44,006 B = 2.19×** for a resolution that no major unfurl surface renders. Not warranted.

###### 2a. Composition constraints this asset imposes on Lens 2

These are engineering constraints, not art direction:

- **Flat fills only.** The measured 20,066 B assumes ≤64 distinct colours. A gradient, noise, grain, blur or photographic texture defeats palette encoding and pushes the file straight back to the 45–50 KB range. Every added colour is real bytes.
- **Safe area.** X renders `summary_large_image` at up to 2:1, cropping 15 px top and bottom of a 630-tall card. Keep all content inside **x ∈ [60, 1140], y ∈ [75, 555]** (1080 × 480).
- **Soft square-crop hedge.** Some surfaces (Discover, certain chat clients) centre-crop 1:1 → **x ∈ [285, 915]**. Put the wordmark inside that box. The card I rendered for measurement places the wordmark at x = 60 and would lose it. Soft constraint, cheap to honour.
- **No card art, no publisher marks, no rising-chart motif** (constraint 6). Nothing in this spec requires any.

###### 2b. Why the card is dark, decided by contrast arithmetic

| Text token | on dark `#0E1116` | on light `#FAFAF8` |
|---|---:|---:|
| `--ink` | **15.9695** | 17.0416 |
| `--ink-soft` | **7.3390** | 5.9809 |
| `--gold` | **8.7699** | **4.3061 ✗** |
| `--gold-bright` | **11.4237** | **2.5175 ✗** |

The card must carry the wordmark, and the wordmark is gold. On the light ground the shipped gold **fails AA** and the drafted remediation `#966C1D` clears it by **0.0059** — zero headroom, baked irreversibly into a raster. On the dark ground the same role has **8.77:1**. There is no argument for the light card. (WCAG 1.4.5 *Images of Text* does not engage: the card is never rendered in the page. The equivalent obligation is `og:image:alt`, which is in the markup below.)

###### 2c. Exact markup — verified against the gate

Insert after `site/index.html:13` (`og:site_name`), and **change line 14 in the same commit**:

```html
<meta property="og:image" content="https://bountycharts.com/assets/og-card.7293c1d5.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Dark card. Wordmark BountyCharts with the tagline TCG price times meta, the headline What will this deck cost you next week, and a four-cell row reading 38 claims audited, 10 materially wrong, 6 unsubstantiated, 33 sources.">
```
```diff
-<meta name="twitter:card" content="summary">
+<meta name="twitter:card" content="summary_large_image">
```

`twitter:image` is deliberately omitted — X falls back to `og:image`, saving ~95 B for no behavioural difference (INFERRED from documented fallback; not verifiable offline).

**Gate result (MEASURED):** the absolute `https://` URL in a `content=` attribute passes. `scripts/validate_site.py:217-241` scans `src`/`srcset` and `<link href>` with a fetching `rel`; it never reads `content=`. This is correct, not a hole — an OG image is fetched by the crawler, so `img-src 'self'` never applies to it.

**Fingerprinting has a second payoff here that is easy to miss:** Facebook and X cache a scraped `og:image` by URL. A content hash makes every new card a new URL, so re-scrape is automatic and no manual Sharing-Debugger purge is ever needed.

**Cost attribution (MEASURED, brotli q11 delta on `index.html`):** og block +503 raw / **+126 brotli**; twitter:card +12 / **+5**.

---

##### IMG-INV-02/03/04 — the favicon set

###### 3a. First, a defect in what ships today

`site/index.html:17` and `site/404.html:8` carry an inline `data:` SVG whose only content is `<text>📈</text>` (U+1F4C8 CHART INCREASING). I rasterised that exact data URI at 64 px in Chromium and read the pixels back: **it renders as a red line climbing left-to-right across a grid, 48.3% inked.**

That is the site's only graphic, and it is a picture of a price going up — the precise imagery constraint 6 forbids, on a site whose own copy promises it "does not publish buyout alerts, price predictions, or investment advice, and never will" (`site/index.html:326`). Two further problems: the glyph has no `font-family`, so its appearance is whatever emoji font the *rendering context* resolves (unbrandable, and absent in contexts that don't load an emoji font inside an SVG image); and it is red, which in this design system is `--down`. **MEASURED — replace it.**

###### 3b. The set

One geometry — the wordmark's `◈` (U+25C8, diamond-in-diamond) as hand-authored paths on an **opaque** `#0E1116` tile with a `#D9A94F` mark — rendered to three deliverables.

| ID | File | Size | Format | Bytes (measured) | Fetched by |
|---|---|---|---|---:|---|
| **IMG-INV-03** | `/assets/mark.<hash8>.svg` | viewBox 0 0 64 64 | SVG | **244** | the browser, 1× |
| **IMG-INV-02** | `/favicon.ico` **(root, no hash)** | 16+32+48 | ICO, PNG-compressed entries | **1,206** | crawlers/aggregators only |
| **IMG-INV-04** | `/assets/touch-icon.<hash8>.png` | 180 × 180 | PNG-8 | **1,380** | iOS, on add-to-home-screen |

Component PNG sizes measured at PNG-8/64: 16 px = 149 B, 32 px = 373 B, 48 px = 630 B, 180 px = 1,380 B, 512 px = 3,159 B.

**Why the tile is opaque.** A transparent gold mark cannot be legible in both browser chromes — measured: `--gold` dark `#D9A94F` is **8.77:1** on dark chrome but **2.16:1** on white; `--gold` light `#9A6F1E` is 4.50:1 on white but **3.67:1** on Chrome's dark toolbar `#1D1F23`. An opaque `#0E1116` tile supplies its own ground and holds **8.77:1 everywhere**. It also matches the iOS requirement (Safari composites a transparent apple-touch-icon onto black) and gives one identical mark across all three files.

**The 16 px entry must be hand-hinted, not downscaled.** At 16 px the diamond-in-diamond's 5-unit stroke and 20-unit inner diamond collapse into mud. Ship the 16 px ICO entry as a **solid** diamond with no inner cut (`M8 2 14 8 8 14 2 8Z`, no stroke). This is why the ICO is authored from three sources, not one.

**Why `/favicon.ico` exists at all, and why it is not fingerprinted.** Browsers with the `<link>` tags present never request it (measured, §3d). It exists for the long tail of consumers that hardcode `/{origin}/favicon.ico` and ignore markup. Because that path is a protocol convention, **it cannot carry a hash** — it is the one file in this spec that is not content-addressed. That has a consequence the brief's rule would otherwise miss:

> `/favicon.ico` at the site root matches **neither** `/assets/*` (`_headers:11`) **nor** `/*.html` (`_headers:15`). It would inherit the platform default. Ship this `_headers` patch alongside it:

```
# Root-convention files match neither /assets/* nor /*.html, so they would
# otherwise inherit the platform default. The name cannot be fingerprinted.
/favicon.ico
  Cache-Control: public, max-age=604800
```
(+205 raw / +94 brotli on `_headers`, which is never served to a browser. INFERRED that Cloudflare Pages honours an exact-path rule — not verifiable without a live edge.)

###### 3c. Exact markup

Replace `site/index.html:17` **and** `site/404.html:8` — both, or the two pages drift again:

```html
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/assets/mark.badd0459.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/touch-icon.f35abc2a.png">
```

###### 3d. Inline `data:` URI vs file — the analysis, with numbers

I built and gate-tested both variants end to end.

| | **A — file triplet** | **B — inline `data:` mark** |
|---|---|---|
| `index.html` delta vs today | **+43 raw / −30 brotli** | +214 raw / **+72 brotli** |
| Requests on `/` | **2** | **1** |
| First-visit wire cost | +435 B (244 B body + 191 B headers) | 0 |
| Repeat-visit cost | **0** (immutable, 1 yr) | ~+72 B brotli, **every load** (HTML is `max-age=0, must-revalidate`) |
| `performance.getEntriesByType('resource')` | 1 entry | **stays `[]`** |
| `loadEventEnd` median, n=9 | **21.1 ms** | 21.7 ms |
| Baseline for comparison | 21.3 ms | 21.3 ms |

**Recommendation: A.** It is counterintuitive but measured — the file triplet is *smaller* in the HTML than the emoji data URI it replaces (**−30 brotli bytes**), because `/assets/…` paths are low-entropy ASCII that brotli matches against existing document text, while a percent-encoded inline SVG is not. Variant B costs 102 brotli bytes more per load than A *and* keeps the compatibility risk of an SVG-only favicon. The single thing A costs is the "1 request / empty resource timing" property; it does **not** cost load time — 21.1 vs 21.3 ms medians are indistinguishable at n=9.

**If B is chosen anyway, one bug will bite.** `#` terminates a `data:` URI. Measured in Chromium: the hex colours percent-encoded as `%23D9A94F` decode fine (4,096 inked px at 64×64); left as `#D9A94F` the image hard-fails with `EncodingError: The source image cannot be decoded.` The current emoji URI only escapes this because it contains no `#`.

###### 3e. Rejected — `site.webmanifest` `[NOT SHIPPED]`

The gate handles it correctly (verified: `<link rel="manifest" href="/assets/site.<hash>.webmanifest">` passes, external blocks — `manifest` ∈ `FETCHING_REL`, `validate_site.py:188-189`). It is still wrong to ship:

1. Chrome fetches the manifest eagerly on load for install eligibility — **a second unconditional request on a page with nothing to install.** That is the exact property the site is best at.
2. Installability needs 192 px and 512 px icons, dragging in ~4.5 KB more `/assets/` (measured: 512 px PNG-8 = 3,159 B).
3. It buys nothing today: no `start_url` behaviour worth having, no offline story, no app.

`theme-color` is already declared per-scheme at `index.html:15-16`, which is the only manifest field the site actually benefits from. Revisit when there is an app.

---

##### IMG-INV-05 — in-page imagery `[P2, conditional]`

**The landing page needs zero images, and that is a feature.** Argued honestly, both sides:

**For adding one.** Every competitor landing page has a product screenshot. The page currently asks the reader to imagine a product that does not exist. The `.ticker` (`index.html:273-294`) is a text component wearing `role="img"` — a diagram of the product drawn in HTML — and a real chart would be more persuasive.

**Against, and this wins.** (a) There is no product to screenshot; a mockup of an unbuilt UI is a fabrication, and the page already carries four fabricated numbers it has to badge `sample`. (b) Any chart image is the constraint-6 hazard — the honest visual for "price against meta share" is a line going up and to the right, which is the one picture this site may not draw. (c) A body image is visitor-fetched, unlike everything else in this spec: a 600×200 chart at this palette measures ~1.5–3 KB and one more request, against a 3,179 B page. (d) The `.ticker` is *better* than an image: it is selectable, translatable, reflows, respects user font size, and already carries an `aria-label`. Replacing its four fabricated cells with the real Riftbound figures (Research §6.2) does everything an image would do, at zero bytes.

**The one graphic that earns its place, conditionally.** If a `/method` page ships, the 17 / 5 / 10 / 6 scorecard wants a stacked proportion bar. Spec:

| Property | Value |
|---|---|
| Delivery | **Inline `<svg>` in the HTML.** No file, no request |
| Size | viewBox `0 0 100 8`, `width="100%" height="10"` |
| Budget | **≤500 B of HTML** (~430 B typical), render-blocking but on a secondary page |
| Colour | **`fill="currentColor"` on spans wrapped in elements carrying `--up` / `--ink-soft` / `--down` / `--ink-faint`** |
| A11y | `role="img"` + `aria-label="38 claims audited: 17 confirmed, 5 partly true, 10 materially wrong, 6 unsubstantiated."` |

Widths from the corrected counts (Research §1): 17/38 = 44.74, 5/38 = 13.16, 10/38 = 26.32, 6/38 = 15.79.

**Inline SVG vs an SVG file, settled by measurement.** I rendered both under `colorScheme: light`, `colorScheme: dark`, and `emulateMedia({media:'print'})`:

| | inline `<svg fill="currentColor">` | `<img src="/assets/x.svg">` |
|---|---|---|
| light | `rgb(23,121,94)` ✓ `--up` | — |
| dark | `rgb(79,191,151)` ✓ `--up` dark | — |
| **print** | `rgb(16,85,63)` ✓ print override | — |
| `currentColor` resolves to | the page's token | **`rgba(0,0,0,255)`** |

An SVG loaded as an image is an isolated document that **cannot see the page's CSS custom properties at all**. Matching this site would need a light file, a dark file, a `<picture>` with `media="(prefers-color-scheme: dark)"`, and it would *still* print wrong. That is 3 files + ~180 B of `<picture>` markup + up to 2 requests, versus one inline element that follows all three palettes for free. **For any in-page graphic on this site, inline SVG is not a preference, it is the only correct delivery.**

---

##### The 404 page — no new assets

`404.html` gets the three icon `<link>` lines (§3c) and **nothing else**.

- **No `og:image`.** The page is `noindex` (`404.html:7`) and carries none of the 11 other social tags. A polished share card for an error page is wrong signalling and a wasted 20 KB.
- Measured delta: **+43 raw, −23 brotli (765 → 742 B, −3.0%)**. The 404 page gets *smaller* on the wire, for the reason in §3d.
- Requests: 1 → 2 in a cold context; in practice 1, because a visitor reaching the 404 has already cached the mark from `/`.

---

##### Print — no assets, one rule

The `@media print` block (`index.html:237-255`) needs no image support because nothing in the body is an image. Three findings for whoever changes that:

1. The og:image and all three icons never print. Zero print budget.
2. If IMG-INV-05 ships, it needs **no** print-specific handling — measured above, `currentColor` inside inline SVG already resolves to the forced print palette (`rgb(16,85,63)` / `rgb(0,0,0)`).
3. **Never deliver an in-page graphic as a CSS `background-image`.** Browsers drop background graphics from print by default; SVG `fill` is foreground content and prints. This reinforces §4.

---

##### Verification — the gate and the suite were actually run

Two full scratch copies of `site/` + `scripts/` + `tests/` were patched with the real markup and the real binary assets and run end to end.

| Run | Result |
|---|---|
| `python3 scripts/validate_site.py` (variant A, full change set) | **exit 0**, 26 `ok`, 0 failures |
| `python3 -m unittest discover -s tests` (variant A) | **Ran 24 tests … OK** |
| `python3 scripts/validate_site.py` (variant B) | **exit 0** |
| `python3 -m unittest discover -s tests` (variant B) | **Ran 24 tests … OK** |
| Repo at HEAD, after all work | gate exit 0, 24 tests OK, `git status --porcelain` empty |

Per-construct results, each run as an isolated mutation of the real `site/`:

| Construct | Gate |
|---|---|
| `<meta property="og:image" content="https://bountycharts.com/…">` | **PASS** |
| `<link rel="apple-touch-icon" href="/assets/touch-icon.<hash>.png">` | **PASS** |
| `<link rel="apple-touch-icon" href="https://cdn…">` | **BLOCK** |
| `<link rel="icon" href="/assets/mark.<hash>.svg" type="image/svg+xml">` | **PASS** |
| `<link rel="manifest" href="/assets/site.<hash>.webmanifest">` / external | **PASS** / **BLOCK** |
| `<link rel="preload" href="/assets/f.woff2" as="font">` / external | **PASS** / **BLOCK** |
| `<img src="/assets/x.<hash>.svg" … loading="lazy">` | **PASS** |
| `<img srcset="/assets/a.<h>.png 1x, //cdn…/a2.png 2x">` | **BLOCK** (protocol-relative caught) |
| `<picture><source media="(prefers-color-scheme: dark)" …>` local | **PASS** |
| inline `<svg>` with self-closing `<rect/>`, `<path/>` in `<body>` | **PASS** (`TagBalance` handles `handle_startendtag`) |
| a `site/assets/` subdirectory existing at all | **PASS** (`SITE.glob("*.html")` is non-recursive) |

###### 7a. Three gate holes I found, all in this lens's territory

The external-subresource check is hardened for `src`/`srcset`/`<link>`/`@import`, but these three **pass exit 0 today and would be blocked at runtime by the CSP**:

| Construct | Gate | Why |
|---|---|---|
| `.x{background-image:url('https://cdn.example.com/bg.png')}` | **PASS ✗** | `validate_site.py:239` scans CSS for `@import` only, never `url()` |
| `@font-face{src:url('https://fonts.gstatic.com/x.woff2')}` | **PASS ✗** | same |
| `<link rel="mask-icon" href="https://cdn…">` | **PASS ✗** | `mask-icon` ∉ `FETCHING_REL` (`validate_site.py:188-189`) |

Fix: scan `css_for(src)` for `url\(\s*['"]?([^'")\s]+)` in addition to `@import`, and add `mask-icon` to `FETCHING_REL`. The first two are the likeliest way a future contributor ships a Google Font or a hotlinked background and only finds out in production. **Not in scope for this spec to fix — flagged for the owner of the gate.**

---

##### Net effect on the measured baseline

| Metric | Today | After (variant A) | Δ |
|---|---:|---:|---:|
| `index.html` raw | 11,657 | 12,404 | +747 |
| **`index.html` brotli (production wire)** | **3,179** | **3,320** | **+141 (+4.4%)** |
| `404.html` brotli | 765 | 742 | **−23 (−3.0%)** |
| Requests on `/` | 1 | **2** | +1 |
| First-visit extra wire | — | **435 B** | — |
| Repeat-visit extra wire | — | **0** | — |
| `loadEventEnd` median (n=9) | 21.3 ms | **21.1 ms** | none measurable |
| DOM elements | 76 | 83 | +7 |
| `site/` on disk | 15,181 | **39,072** | +23,891 (2.57×) |

Per-change brotli attribution on `index.html`: og:image block **+126**, `twitter:card` **+5**, icon triplet **−30**, JSON-LD `Organization.logo` **+49**.

**The honest headline.** The og card is 20,066 B — **1.32× the entire current site on disk and 6.31× the compressed landing page** — and a visitor never downloads one byte of it. The repo grows 2.57×; the page a human loads grows **4.4%**, and its load time does not move. That is the trade this spec is making, stated plainly.

**Where the visitor genuinely pays:** one request for a 244-byte SVG, cached one year. Nothing else. `/favicon.ico`, `/assets/touch-icon…png` and `/assets/og-card…png` were confirmed **not fetched** on a normal page load.

---

##### Fingerprinting — the one-year trap, per asset

`site/_headers:11-12` freezes `/assets/*` for 31,536,000 s with `immutable`; browsers will not revalidate even on a hard reload. **Filename is the only cache-buster.**

| Asset | Fingerprinted? | If you get this wrong |
|---|---|---|
| `og-card.<hash8>.png` | **Yes, mandatory** | a corrected card is invisible to Facebook/X/Slack for a year, *and* their own scrape caches never invalidate |
| `mark.<hash8>.svg` | **Yes, mandatory** | every returning visitor keeps the old mark for a year |
| `touch-icon.<hash8>.png` | **Yes, mandatory** | stale home-screen icon and stale `Organization.logo` in Google's index |
| `favicon.ico` | **No — cannot be** | root convention; mitigated by the explicit `max-age=604800` rule in §3b, which must ship with the file |

Scheme: first 8 hex characters of `sha256(file_bytes)`, e.g. `og-card.7293c1d5.png`. Regenerate the hash **and** update every reference on any content change — there are exactly three referencing sites: `index.html` head, `404.html` head, and the JSON-LD `publisher.logo`.

---

##### Assets explicitly rejected, with the reason

| Candidate | Verdict | Reason |
|---|---|---|
| Light-theme og card | **No** | crawlers cannot evaluate `prefers-color-scheme`; the light gold fails AA at 4.31:1 and its remediation clears by 0.0059 |
| 2× / 2400×1260 og card | **No** | measured 44,006 B = 2.19× for a resolution no unfurl surface uses |
| Per-page og cards | **No for now** | only 2 pages exist and one is `noindex`. Revisit when `/method` ships: a card carrying 17/5/10/6 is the strongest share asset the project has, and would be `og-card-method.<hash>.png` at the same 20 KB budget |
| `twitter:image` | **No** | X falls back to `og:image`; saves ~95 B for no behavioural change |
| `site.webmanifest` + 192/512 icons | **No** | +1 unconditional request and ~4.5 KB for install eligibility on a site with nothing to install (§3e) |
| SVG wordmark file for the header | **No** | the `◈ BountyCharts` text costs 0 bytes and 0 requests, is selectable, translatable, scales with user font-size, and inherits `--gold` in light/dark/print automatically. An SVG file gets none of that (§4) and would need light + dark + print variants. **Hedge instead:** U+25C8 is covered in this container's stacks (measured: sans advance 30.77 px vs 24.02 px tofu reference; mono pixel signature 33 inked rows vs 50 for the tofu box — a real glyph, not a box). Windows/macOS coverage is **INFERRED, not measured** — if it ever proves absent, the fix is a `::before` with the same 244 B inline path, not a file |
| Hero screenshot / product mockup | **No** | there is no product to screenshot, and the honest chart for this product is the one picture constraint 6 forbids (§4) |
| `mask-icon` (Safari pinned tab) | **No** | superseded, and the gate does not even check its `rel` (§7a) |
| Any web font | **No** | `font-src 'self'` would require self-hosting; a woff2 subset is 15–30 KB = 5–9× the compressed page, for a system stack that already renders correctly |
| WebP / AVIF og card | **No** | crawler support is the binding constraint, and PNG-8 already beats JPEG by 2.28× here |

### 5.2 Generation prompts and deterministic fallbacks

#### Lens 2 — Image generation prompts and asset specifications

Every number in this section is **MEASURED** unless graded otherwise. Verification method: assets were built, fingerprinted, wired into a scratch copy of `site/`, then run through `scripts/validate_site.py` and `python3 -m unittest discover -s tests`, and loaded in Chromium 1194 behind a local server replaying the production CSP from `site/_headers:6`. Contrast is computed with the WCAG 2.x sRGB relative-luminance formula, not estimated.

---

##### The governing finding

**The correct answer for five of the six assets is not a generative model. It is hand-authored SVG and a screenshot of the site's own CSS.** This is not an aesthetic preference; it is a measurement.

| Path | og:image bytes | Reproducible | Exact brand hex | Text renders correctly |
|---|---:|---|---|---|
| **Deterministic (HTML→screenshot→PNG-8)** | **15,493** | yes, byte-identical | yes | yes |
| Same card, PNG-24 as rendered | 44,059 | yes | yes | yes |
| Same card + generative-style texture, JPEG q0.80 | **73,662** | no | no | n/a |
| Same card + texture, PNG-8/64 | 345,904 | no | no | n/a |
| Same card + texture, PNG-24 | 1,310,356 | no | no | n/a |

MEASURED. The "texture" row is the flat card with the atmospheric radial glow plus film grain that every image model produces by default. It is **4.75× the flat card** in its most favourable encoding (JPEG q0.80) and **4.85× the entire current site on disk** (15,181 B). The flat card is 2.84× smaller than its own PNG-24 because a flat card quantises to 64 colours with a max per-channel error of 30 — invisible on antialiased type — while a grained one holds 29,145 unique colours and cannot.

The whole asset system's cost to a visitor, measured end-to-end:

| Metric | Today | With every asset in this section | Δ |
|---|---:|---:|---:|
| HTTP requests | 1 | **1** | 0 |
| Subresource fetches (`performance.getEntriesByType('resource')`) | 0 | **0** | 0 |
| `index.html` raw | 11,657 | 13,920 | +2,263 |
| `index.html` brotli q11 (**the real wire cost**) | 3,179 | **3,582** | **+403** |
| `loadEventEnd` | 48.7 ms | 18.3–26.4 ms | — |
| Console errors / failed requests, light + dark | 0 / 0 | **0 / 0** | 0 |
| `/assets/` on disk | 0 | 18,241 | +18,241 (visitor-fetched: **0 B**) |

**+403 bytes and zero additional requests buys a social card, a real favicon, an apple-touch-icon and a Google-consumable `Organization.logo`.** The `og:image` is fetched only by crawlers; the `apple-touch-icon` is fetched only on add-to-home-screen — MEASURED, `resource` entries stayed at 0 with both tags present.

**Verification:** `python3 scripts/validate_site.py` → exit 0, 26 ok / 0 fail. `python3 -m unittest discover -s tests` → `Ran 24 tests … OK`.

---

##### Style anchor (paste this at the head of *every* prompt in this section)

> **STYLE ANCHOR — BountyCharts.** Precision-instrument minimalism. The visual language of a calibrated measuring device — a caliper, an oscilloscope bezel, a surveyor's rod, a laboratory rule — never of a market, a portfolio, or a trade. Flat vector; no perspective, no depth-of-field, no bloom, no gradient mesh, no film grain, no atmospheric haze. Absolutely flat fields of colour meeting at hairline 1-pixel rules. Composition is orthogonal and left-to-right: horizontal baselines, vertical ticks, right angles only. Any implied motion is *lateral and unsigned*, never ascending. Palette is strictly limited to: background `#0E1116`, panel `#161A21`, primary text `#E9ECF1`, secondary text `#99A2B0`, hairline/tick `#6B7482`, rule `#232932`, single accent gold `#D9A94F`. Accent gold covers less than 8% of the canvas and marks exactly one thing. Typography, where present, is a monospaced grotesque for labels and identifiers (uppercase, letter-spacing 0.15em) and a neutral geometric sans for headline (tight tracking, −0.03em); numerals are tabular. Enormous negative space — at least 55% of the canvas is untouched background. The mood is quiet, exact, slightly austere, and completely unexcited. It should look like the front panel of an instrument that measures something, built by someone who did not want to sell you anything.

**Why this anchor and not a prettier one.** The site's own footer (`site/index.html:339`) disclaims affiliation with Riot Games, The Pokémon Company, Bandai Namco and Wizards of the Coast, and `site/index.html:326` commits that BountyCharts "does not publish buyout alerts, price predictions, or investment advice, and never will." Instrumentation is the only visual register that is simultaneously legal-safe (nothing to mistake for licensed game art) and promise-safe (nothing to mistake for a return). Every clause above is doing one of those two jobs.

---

##### NEG-CORE — the shared negative prompt

Paste **verbatim** into every prompt in this section. Per-asset additions are listed under each asset.

```
NEGATIVE: trading card, playing card, card face, card back, card frame, card border,
card sleeve, deck box, booster pack, foil, holographic, set symbol, expansion symbol,
rarity symbol, mana symbol, energy symbol, pip, tap symbol, game logo, publisher logo,
company wordmark, brand mark of any real company, Riot, Riftbound, Pokemon, Magic the
Gathering, Yu-Gi-Oh, One Piece, Bandai, Wizards of the Coast, fantasy character,
character art, creature, portrait, mascot, anime, illustration of a person, hands
holding cards, tabletop scene, game mat, dice, rocket, rocket ship, launch, moon, arrow
pointing up, upward arrow, ascending line, hockey stick curve, green candle, candlestick
chart, bull, bear, bull market, stock ticker board, trading floor, Wall Street, money,
banknotes, cash, coins, gold coins, treasure, piggy bank, wallet, credit card, price tag,
shopping cart, sale badge, discount starburst, businessman, businesswoman, handshake,
suit and tie, stock photo people, office scene, crypto, blockchain, NFT, neon glow,
cyberpunk, holographic UI, HUD overlay, sci-fi interface, glassmorphism, lens flare,
bokeh, film grain, noise texture, vignette, drop shadow, bevel, emboss, 3D render,
isometric, gradient mesh, watercolour, brush stroke, hand-drawn, sketch, doodle,
photorealism, photograph, motion blur, confetti, celebration, fireworks, trophy, medal,
badge, ribbon, emoji, sticker, gibberish text, lorem ipsum, misspelled words, watermark,
signature, border frame, rounded card container
```

###### Why each cluster of exclusions exists

| Cluster | Reason | Weight |
|---|---|---|
| card face / frame / border / sleeve / booster / foil / set symbol / mana pip / rarity symbol | Any of these renders imagery a reasonable viewer reads as **official game material**, directly contradicting the footer disclaimer at `site/index.html:339`. A card frame is the single most recognisable trade dress in this category and the fastest way to manufacture an implied licence. | **Legal — hard block** |
| named publishers and IP (Riot, Riftbound, Pokemon, MTG, Yu-Gi-Oh, One Piece, Bandai, WotC) | Models will happily interpolate these from context. The disclaimer names four of them by name; generating their marks while disclaiming affiliation is worse than either alone. | **Legal — hard block** |
| character art / creature / portrait / anime / mascot | Card-game character art is the second-most-recognisable trade dress and is the training data most likely to be reproduced near-literally. Also the highest copyright-similarity risk in the whole set. | **Legal — hard block** |
| rocket / moon / upward arrow / ascending line / hockey stick / green candle / candlestick | These are the iconography of a **return**, not a measurement. `site/index.html:326` promises no price predictions and no investment advice "and never will". A rising line on the social card is an investment promise made in the one artefact that travels furthest from its own disclaimer. | **Brand commitment with legal weight** |
| bull / bear / trading floor / Wall Street / stock ticker board | Same commitment, plus these read as securities-market imagery. `docs/tcg-deep-dive-2026.md:147` records that FTC endorsement and deceptive-practice rules apply to this category even though trading cards are not securities. | **Brand + FTC exposure** |
| money / cash / coins / treasure / piggy bank / price tag / discount starburst / shopping cart | Reads as "make money" or "buy now". The product is decision support, not a buy signal (`site/index.html:326`). Retail-sale ornament (starburst, sale badge) additionally cheapens a page whose entire credibility argument is restraint. | **Brand commitment** |
| stock-photo businesspeople / handshake / suit / office | Generic, instantly dates the page, and implies an institution that does not exist. The site is honest that it is pre-launch (`site/index.html:332`). | Craft + honesty |
| crypto / blockchain / NFT / neon / cyberpunk / HUD / glassmorphism | The default "fintech dashboard" aesthetic of image models. It is speculation-coded and would place BountyCharts in exactly the category it spends a whole section disclaiming. | **Brand commitment** |
| grain / vignette / bokeh / lens flare / 3D / bevel / gradient mesh / glow | Purely economic: MEASURED at **4.75× the byte cost** (73,662 B vs 15,493 B) for zero communicative gain, on a site whose best measured property is that it is 15 KB. | **Performance budget** |
| gibberish text / misspelled words / lorem ipsum / watermark / signature | No current image model renders the wordmark "BountyCharts", the tagline "TCG price × meta", or the URL reliably. Any generated asset must be **background only**, with type composited in a vector tool. | Craft — see §2.6 |
| rounded card container / border frame | A rounded rectangle with a border *is* a card silhouette. Avoiding literal card art is pointless if the composition is card-shaped. | Legal — subtle |

---

##### Contrast law for any text baked into an image

Baked text cannot be fixed by a CSS change, cannot be zoomed, and is not read by a screen reader. It must clear a higher bar than page text, not a lower one.

**Ship every image asset in the DARK palette.** This is a measured decision, not a taste. The light palette carries the known unfixed defect (`--gold` #9A6F1E on `--bg` #FAFAF8 = **4.3061:1**, FAIL; `--ink-faint` #8A93A1 = **2.9687:1**, FAIL). The dark palette does not have that problem for any token used below.

Contrast of every colour pair actually used in the shipped assets, computed:

| Element | Foreground | Background | Ratio | Size | Verdict |
|---|---|---|---:|---|---|
| Headline | `--ink` `#E9ECF1` | `--bg` `#0E1116` | **15.9695** | 58 px / 700 | PASS AA + AAA |
| Headline accent ("cost you") | `--gold` `#D9A94F` | `#0E1116` | **8.7699** | 58 px / 700 | PASS AA + AAA |
| Wordmark "◈ BountyCharts" | `--gold` `#D9A94F` | `#0E1116` | **8.7699** | 22 px / 700 mono | PASS AA + AAA |
| Tagline "TCG PRICE × META" | `--ink-soft` `#99A2B0` | `#0E1116` | **7.3390** | 15 px mono | PASS AA + AAA |
| Metric legend | `--ink-soft` `#99A2B0` | `#0E1116` | **7.3390** | 15 px mono | PASS AA + AAA |
| Domain "bountycharts.com" | `--gold` `#D9A94F` | `#0E1116` | **8.7699** | 15 px mono | PASS AA + AAA |
| Disclaimer line | `--ink-soft` `#99A2B0` | `#0E1116` | **7.3390** | 14 px mono | PASS AA + AAA |
| Measurement ticks (**non-text**) | `--ink-faint` `#6B7482` | `#0E1116` | **4.0035** | 1 px | PASS SC 1.4.11 (3:1) |
| Icon mark, light chrome | `--gold` `#9A6F1E` | `#FFFFFF` / `#FAFAF8` | **4.5001 / 4.3061** | 16–32 px | PASS SC 1.4.11 (3:1) |
| Icon mark, dark chrome | `--gold` `#D9A94F` | `#0E1116` / `#161A21` | **8.7699 / 8.0895** | 16–32 px | PASS SC 1.4.11 (3:1) |

**The lowest-contrast text on the og card is 7.3390:1 — 1.63× the AA floor. The lowest-contrast text on the live site today is 2.24:1** (the `.cell.sample::after` badge, `site/index.html:158-169`). The card is the most accessible surface the project would own.

Three hard rules that follow:

1. **`--ink-faint` is banned for type in every image asset, in both palettes.** MEASURED: 2.9687:1 light on `--bg`, **4.0035:1 dark on `--bg`, 3.6929:1 dark on `--surface`** — it fails AA in *both* themes at the sizes it is used. It is permitted for hairline ticks only, where the applicable threshold is SC 1.4.11's 3:1.
2. **`--rule` `#232932` is banned for anything load-bearing.** 1.2920:1 on `--bg`. In the shipped template the minor ruler ticks were moved off `--rule` onto `--ink-faint` and differentiated by *height* (6 px minor / 14 px major) rather than by colour, precisely so every tick clears 3:1.
3. **Do not use the drafted light-theme remediation values (`#966C1D`, `#926D2E`, `#6D747F`) in an image.** All three clear 4.5:1 by ≤0.01 against `#FAFAF8`. That headroom survives CSS; it does not survive PNG quantisation, which the encoder measured at up to 30 per channel of error. Dark-palette tokens clear by 2.8–11.5 points and are quantisation-proof.

###### Legibility at real display sizes

An og:image is almost never seen at 1200 px. MEASURED type sizes after downscaling:

| Surface | Render width | Scale | Headline 58 px → | Wordmark 22 px → | Disclaimer 14 px → |
|---|---:|---:|---:|---:|---:|
| X / LinkedIn large card | ~552 px | 0.46× | **26.7 px** | 10.1 px | 6.4 px |
| Discord unfurl | ~400 px | 0.33× | **19.3 px** | 7.3 px | 4.7 px |
| Slack unfurl | ~360 px | 0.30× | **17.4 px** | 6.6 px | 4.2 px |

**Design rule this forces: the headline must carry the entire message alone.** It does — "What will this deck cost you next week?" is the complete proposition. Everything else is for the expanded/desktop view. Do not add a fifth line of copy hoping it will be read in a feed; it will not be. INFERRED from the render widths, which are approximate and platform-version-dependent.

---

##### The `/assets/` fingerprint rule — applies to every asset without exception

`site/_headers:11-12` sets `/assets/*` to `Cache-Control: public, max-age=31536000, immutable`. That is **365 days**, and `immutable` means a browser will not revalidate even on a hard reload. **The filename is the only cache-busting mechanism that exists.**

Therefore, for every asset in this section:

- The shipped filename **must** be `<base>.<contenthash>.<ext>`, e.g. `og-card.f36a278c.png`.
- Recompute the hash and rename on **every** re-render, however cosmetic. A one-pixel change under the same filename is invisible to every client that has seen the old one, for a year.
- Compute it deterministically: `sha256sum <file> | cut -c1-8`.
- **Never place an image at the site root.** `/og-card.png` matches neither `/assets/*` nor `/*.html` in `site/_headers`, so it inherits the Cloudflare default and gets no long cache at all. (INFERRED from the `_headers` rule set; not measured against a live edge.)

A second freezing effect compounds this: Facebook, X and LinkedIn cache scraped og:images for days to weeks and only re-fetch on manual invalidation. **Together these mean an og:image is doubly frozen — which is why the card in IMG-PROMPT-01 deliberately contains no volatile data.** See the design note there.

---

##### Three gate/test traps discovered while verifying this spec

These were found by actually running the suite against candidate assets. All three pass the gate and fail (or silently break) elsewhere. **NEW FINDINGS — not in the Phase 1 ground truth.**

**Trap 1 — a `<style>` element inside an SVG data-URI favicon breaks the test suite while the gate stays green.**
`tests/test_validate_site.py:146` extracts the page CSS with the **non-greedy** regex `<style>(.*?)</style>`. A theme-aware SVG favicon (`<link rel="icon" href="data:image/svg+xml,<svg…><style>@media(prefers-color-scheme:dark){…}</style>…">`) sits at `site/index.html:17`, *before* the real `<style>` at `:27`. The regex therefore matches the favicon's inner `<style>` first, writes that as `styles.css`, and mangles the `<link>` tag into a dangling `</svg>">`. MEASURED: gate exits 0 and prints "All checks passed"; `test_extracting_css_to_a_stylesheet_is_allowed` fails with `FAIL index.html: </svg> closes <head>`. **Consequence: theme-aware favicons must use twin `media`-scoped `<link>` tags, not an internal `<style>`.** (A `<style>` inside an SVG served as a *file* under `/assets/` is fine — verified, 24/24 OK — but costs a request; see IMG-PROMPT-02.)

**Trap 2 — the JSON-LD must contain the literal string `"@type": "WebSite",`.**
`tests/test_validate_site.py:97` mutates that exact substring — one space after the colon, trailing comma — to prove the gate rejects broken JSON-LD. Rewriting the block to an `@graph` and pretty-printing it compactly (`"@type":"WebSite",`) makes the mutation a no-op, the gate passes the deliberately-broken input, and `test_broken_json_ld_is_rejected` fails with `AssertionError: 0 != 1`. MEASURED. **Consequence: when adding `Organization.logo`, keep `"@type": "WebSite",` spelled with one space and a trailing comma — i.e. `@type` must not be the last key of the WebSite node.**

**Trap 3 — the external-subresource scanner does not see SVG `<use href>` or `<image href>`.**
`scripts/validate_site.py:217-241` scans `src`, `srcset`, `<link href>` with a fetching `rel`, and CSS `@import`. `<svg><use href="https://cdn…/sprite.svg#mark"/></svg>` passes the gate and passes `TagBalance` — MEASURED, both clean. It is then blocked at runtime by CSP `default-src 'self'` (MEASURED in Chromium: `Unsafe attempt to load URL https://example.com/m.svg from frame with URL … Domains, protocols and ports must match.`). **Consequence: an external SVG sprite ships broken rather than failing CI. Never use `<use href>` against a remote sprite; inline the path data instead, as IMG-PROMPT-02 does.**

Also confirmed safe, MEASURED: absolute `https://bountycharts.com/assets/…` inside `content=` (og:image, twitter:image) is never scanned and correctly so — the crawler fetches it, the page does not, and `img-src 'self'` never applies. Inline `<svg>` with either `<path/>` or `<path></path>` passes `TagBalance`. The render template belongs in `tools/`, **not** `site/` — `validate_site.py:126` uses the non-recursive `SITE.glob("*.html")`, so anything outside `site/` is invisible to the gate and, more importantly, is never deployed.

---

#### IMG-PROMPT-01 — `og:image` / `twitter:image` (P0)

**1200 × 630 · `/assets/og-card.<hash>.png` · 15,493 B · crawler-fetched only · 0 visitor requests**

##### Design note: the card contains no volatile data, deliberately

The obvious card design mirrors the site's ticker strip with its four numbers. **Do not.** Two independent caches freeze this file — `immutable` for 365 days (§2.4) and the social platforms' own scrape cache — so any number baked in is a number you cannot correct. Worse, the site's four current ticker values are *fabricated* (`site/index.html:274-293`, each carrying a `sample` badge), and a big green `+18.4% ▲` lifted out of its `sample` context and posted to a timeline is precisely the buy signal `site/index.html:326` promises never to publish.

The card therefore shows the **metric vocabulary** (Deck cost · Movement · Spread · Reprint risk) over a **measurement scale** — a ruler, which has ticks but no slope, no direction and no value. It says "we measure these four things" without asserting any number. It never needs re-rendering when the data changes.

##### Style anchor
§2.1, verbatim.

##### Positive prompt

```
[PASTE STYLE ANCHOR FROM §2.1 HERE]

SUBJECT: An open-graph social card for a measurement instrument brand. No object,
no scene, no illustration — the card IS a flat instrument panel.

COMPOSITION: 1200x630 landscape. Uniform background #0E1116, edge to edge, no
vignette. All content in a single 600px-wide column centred horizontally, leaving
300px of untouched background on each side. Vertically, four bands top to bottom:
(1) at y=56-90, a compact identifying row: a small gold rhombus glyph (an outlined
diamond containing a smaller solid diamond) followed by a monospaced bold wordmark,
followed by a smaller uppercase letter-spaced tagline in grey;
(2) optically centred at y=~300, a two-line headline in neutral geometric sans,
700 weight, 58px, tight -0.03em tracking, centred, four words per line;
(3) at y=~450, a horizontal measurement scale exactly 600px wide: a 1px baseline with
1px vertical ticks rising from it, minor ticks 6px tall every 12px, major ticks 14px
tall every 60px. A ruler. Perfectly level. No curve, no data, no slope, no fill;
(4) directly beneath at y=~490, one line of uppercase monospaced grey labels separated
by faint mid-dots;
(5) at y=~545 a 1px full-width horizontal rule spanning x=64..1136, and beneath it a
baseline row: a gold monospaced domain at the left edge, a smaller grey monospaced
disclaimer line at the right edge.

COLOUR: background #0E1116 only. Headline #E9ECF1. Accent phrase inside the headline
and the wordmark and the domain in #D9A94F. Tagline, metric labels and disclaimer in
#99A2B0. Ticks and the scale baseline in #6B7482. The lower rule in #232932. No other
colour appears anywhere. Gold covers under 8% of the canvas.

LIGHTING: none. Flat colour fill. No light source, no shading, no glow, no shadow,
no reflection, no ambient occlusion.

TEXTURE: none. Zero grain, zero noise, zero paper fibre, zero gradient. Pure flat
fields meeting at hairline edges.

TYPOGRAPHY: headline in a neutral geometric sans at 700 weight, tight tracking.
Wordmark, tagline, labels, domain and disclaimer in a monospaced grotesque; labels
and tagline uppercase at 0.15em letter-spacing. Tabular numerals if any numeral
appears (none should).

SAFE AREAS: the centre 630x630 square (x=285..915) is the crop-safe core and must
contain the complete wordmark row, the complete headline, the scale and the label
row, with at least 15px of clear background inside each edge of that square. The
left and right 285px wings must contain ONLY background and the two full-width
hairline rules — nothing identity-bearing. The bottom 48px and top 56px are margin.

ASPECT RATIO: exactly 1200:630 (40:21).
```

##### Negative prompt

NEG-CORE from §2.2, verbatim, **plus**:

```
, chart, graph, line graph, bar chart, sparkline, plotted data, trend line, curve,
data points, axis labels, numbers, percentages, currency symbols, dollar sign, arrows,
directional indicators, up, down, red and green pairing, dashboard widgets, panels,
cards, tiles, containers, boxes with borders, gradients, glow behind text, coloured
background wash
```

*Additional rationale.* `chart / trend line / curve / plotted data` are excluded even though the product is called BountyCharts: a plotted line necessarily has a *direction*, and a directional line on a shareable card is a price claim. The scale is a ruler for exactly this reason. `red and green pairing` is excluded because the up/down semantic (`--up` / `--down`) is meaningful *in context* on the page and reads as a gain/loss signal *out of context* in a feed. `numbers / percentages / currency` is excluded per the volatility argument above and because the site's only on-page figures are fabricated samples.

##### Parameters per tool

| Tool | Invocation | Notes |
|---|---|---|
| **Midjourney v7** | `--ar 40:21 --style raw --stylize 50 --chaos 0 --weird 0 --seed 20260816 --no <NEG-CORE terms>` | 1200:630 reduces exactly to 40:21. `--style raw` and `--stylize 50` are essential — MJ's default stylisation adds glow and texture, i.e. the 4.75× byte penalty. Output will not be 1200×630; downscale-and-crop to exact pixels. |
| **DALL·E 3 / gpt-image-1** | `size: "1792x1024"`, `quality: "hd"`, `style: "natural"` | No 1.905:1 size exists. Generate 1792×1024 (1.75:1), centre-crop to 1792×941, downscale to 1200×630 with Lanczos. `style: "vivid"` will saturate the gold off-token — use `"natural"`. |
| **Firefly** | Aspect "Widescreen (16:9)", Content type **Art**, Visual intensity **1** (minimum), Style refs off, Effects off | Crop 1792×1008 → 1200×630. Firefly's "Photo" content type cannot produce a flat field. |
| **SDXL / SD3.5** | `1216x640` (both /64), CFG **4.5**, steps **32**, sampler **DPM++ 2M Karras**, fixed `seed=20260816`, no refiner, no upscaler, LoRA weight 0 | 1216×640 = 1.90:1, closest /64 size. Resize to 1200×630. Skip the refiner — it reintroduces texture. |

**Seed discipline for a consistent set.** Fix one seed (`20260816`) across the whole family and vary only the SUBJECT and COMPOSITION clauses; hold the STYLE ANCHOR, COLOUR, LIGHTING and TEXTURE blocks byte-identical. Record model ID, model version, exact prompt text, seed and all sampler parameters in `tools/og/PROVENANCE.md` beside the output. Without that record the set cannot be regenerated when one asset needs a revision, and a mismatched re-roll is how a "system" becomes four unrelated pictures.

##### FALLBACK — **and this is the recommendation. Ship this, not the prompt.**

The generative path cannot render "BountyCharts", "TCG price × meta" or "bountycharts.com" reliably; cannot hit `#D9A94F` exactly; is not reproducible; and its native aesthetic costs 4.75× the bytes. The card below is rendered from the site's own CSS tokens, is byte-reproducible, and is **15,493 B**.

**Where the files go:** `tools/og/og-card.html` and `tools/og/render.mjs` — **outside `site/`**, so the gate never scans them (`validate_site.py:126` uses non-recursive `SITE.glob("*.html")`) and they are never deployed. Only the PNG lands in `site/assets/`.

###### `tools/og/og-card.html`

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BountyCharts og:image render template</title>
<style>
  /* ============================================================
     BountyCharts og:image — render template
     Output: 1200x630 PNG. This file is NEVER served from site/.
     No <script>. No web font. No external reference of any kind.
     DARK palette only — see the contrast table in the spec.
     ============================================================ */
  :root{
    --bg:#0E1116; --surface:#161A21; --ink:#E9ECF1; --ink-soft:#99A2B0;
    --ink-faint:#6B7482; --rule:#232932; --gold:#D9A94F; --gold-bright:#EBC475;
    /* Pinned at render time for reproducibility. Only pixels ship, so there is
       zero font-src / CSP implication. Substitute freely, then re-check the
       square-crop test — a wider face can push the headline out of the core. */
    --sans:"Inter","Helvetica Neue","Liberation Sans",Arial,sans-serif;
    --mono:"SF Mono","JetBrains Mono","DejaVu Sans Mono","Liberation Mono",monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{background:var(--bg)}
  .card{
    width:1200px;height:630px;overflow:hidden;position:relative;
    background:var(--bg);color:var(--ink);font-family:var(--sans);
    -webkit-font-smoothing:antialiased;
    padding:56px 64px 48px;display:flex;flex-direction:column;
  }

  /* ---- SQUARE-CROP SAFE CORE ------------------------------------------
     A 630x630 centre crop of a 1200x630 canvas keeps x 285..915.
     Every identity-bearing element sits in a 600px centred column, so the
     square crop loses nothing but decorative rules. Verified by screenshot. */
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

  /* ---- Measurement scale ---------------------------------------------
     A ruler, not a trend line: no direction, no slope, nothing that can be
     read as a price movement or a buy signal. Pure CSS gradients, so the
     template needs no script. Ticks are NON-TEXT graphics: WCAG 1.4.11
     threshold is 3:1 and --ink-faint #6B7482 on #0E1116 = 4.0035:1. That
     token is used for ticks ONLY and for no type anywhere on this card. */
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
      <h1>What will this deck <span class="accent">cost you</span> next week?</h1>
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

The headline is `site/index.html:269` verbatim, accent span included. The card and the page say the same sentence, which is the point.

###### `tools/og/render.mjs`

```js
// Renders the og card and both icon rasters. Requires playwright.
//   node tools/og/render.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';
const here = path.dirname(fileURLToPath(import.meta.url));
const out  = path.join(here, 'out');

const MARK = `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path fill="#D9A94F" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg>`;

const b = await chromium.launch();

// 1200x630 social card. deviceScaleFactor MUST be 1 — a 2x render is 4x the
// pixels for zero gain, since no platform displays this above 1200px.
const p = await b.newPage({ viewport:{width:1200,height:630}, deviceScaleFactor:1 });
await p.goto('file://' + path.join(here,'og-card.html'));
await p.waitForTimeout(300);
await p.locator('.card').screenshot({ path: path.join(out,'og-card.png') });

// Square-crop proof: what X renders if twitter:card is left at "summary".
await p.screenshot({ path: path.join(out,'og-square-crop.png'),
                     clip:{x:285,y:0,width:630,height:630} });

// Icon rasters, from the same vector. 0.62 keeps the diamond off the corners.
for (const size of [180, 512]) {
  const q = await b.newPage({ viewport:{width:size,height:size}, deviceScaleFactor:1 });
  await q.setContent(`<body style="margin:0"><div style="width:${size}px;height:${size}px;
    background:#0E1116;display:flex;align-items:center;justify-content:center">
    ${MARK.replace('<svg','<svg width="'+Math.round(size*0.62)+'" height="'+Math.round(size*0.62)+'"')}
    </div></body>`);
  await q.screenshot({ path: path.join(out, `icon-${size}.png`) });
  await q.close();
}
await b.close();
console.log('rendered to', out);
```

###### Post-processing (this is where 2.84× of the byte saving lives)

Playwright emits PNG-24. Quantise to a 64-colour palette:

```sh
pngquant --quality 90-100 --speed 1 --strip 64 -o og-card.q.png out/og-card.png
```

MEASURED without `pngquant` available in this environment, using an equivalent median-cut quantiser plus per-scanline None/Sub filter selection and `zlib` level 9:

| Palette | Bytes | Max per-channel error | Verdict |
|---:|---:|---:|---|
| 32 | 13,872 | 36 | visible banding on the gold |
| **64** | **15,493** | **30** | **ship this — visually identical at 1:1** |
| 128 | 17,739 | 20 | +2,246 B for no perceptible gain |
| PNG-24 as rendered | 44,059 | 0 | 2.84× the cost |

Then fingerprint and place:

```sh
H=$(sha256sum og-card.q.png | cut -c1-8)
mv og-card.q.png site/assets/og-card.$H.png
```

###### Head changes required (`site/index.html`)

```html
<!-- REPLACE line 14. Non-negotiable and must land in the SAME commit as the image. -->
<meta name="twitter:card" content="summary_large_image">

<!-- INSERT after line 13 (og:site_name). Absolute URLs are correct and gate-safe:
     content= is never scanned by validate_site.py, and the crawler — not the
     page — does the fetch, so img-src 'self' never applies. -->
<meta property="og:locale" content="en_US">
<meta property="og:image" content="https://bountycharts.com/assets/og-card.f36a278c.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="BountyCharts. What will this deck cost you next week? A measurement scale above four labels: deck cost, movement, spread, reprint risk.">
<meta name="twitter:image" content="https://bountycharts.com/assets/og-card.f36a278c.png">
<meta name="twitter:image:alt" content="BountyCharts. What will this deck cost you next week? A measurement scale above four labels: deck cost, movement, spread, reprint risk.">
```

**The `twitter:card` change is a hard dependency, not a nicety.** `site/index.html:14` is currently `summary`, which crops to a centre **square**. Shipping `og:image` without flipping it yields a 630×630 crop. The template survives that crop by design — MEASURED, the centre 630×630 retains the complete wordmark, the complete headline, the scale and the label row, losing only the domain and part of the disclaimer — but `summary_large_image` is what the 1200×630 composition is for.

##### Acceptance checklist

- [ ] Output is exactly **1200 × 630 px**, PNG, 8-bit **indexed** colour (`file` reports `8-bit colormap`, not `8-bit/color RGB`).
- [ ] File size **≤ 20,000 B**. Reference build: 15,493 B. Above 25 KB, something textured got in.
- [ ] Filename matches `og-card.[0-9a-f]{8}.png` and the hash equals `sha256sum … | cut -c1-8` of the file itself.
- [ ] File lives in `site/assets/`, **not** the site root.
- [ ] Sampling the flat background at (20,20), (600,120) and (1180,610) returns **exactly `#0E1116`** on all three — proves no gradient, glow or vignette.
- [ ] Total unique colours **< 100** (reference: 64). A count in the thousands means texture.
- [ ] Every string is spelled correctly: `BountyCharts`, `TCG price × meta` (U+00D7 multiplication sign, not letter x), `bountycharts.com`. No gibberish glyphs.
- [ ] Contrast, computed not eyeballed — headline `#E9ECF1`/`#0E1116` = **15.9695**, accent + wordmark + domain `#D9A94F`/`#0E1116` = **8.7699**, tagline + labels + disclaimer `#99A2B0`/`#0E1116` = **7.3390**, ticks `#6B7482`/`#0E1116` = **4.0035** (non-text, 3:1 threshold). **No text below 4.5:1. No text uses `#6B7482` or `#232932`.**
- [ ] **Square-crop test:** crop x=285..915, y=0..630. The wordmark, both headline lines, the scale and the label row are all fully present with clear margin.
- [ ] Contains **no numeral, no percentage, no currency symbol, no arrow, no ▲ ▼**, and no plotted line of any kind.
- [ ] Contains no card shape, no publisher name or mark, no character, no rounded-rectangle container.
- [ ] The measurement scale is **perfectly level** — sample the baseline y-coordinate at x=300 and x=900; they must be identical. Any slope is a price claim.
- [ ] `site/index.html:14` reads `summary_large_image` **in the same commit**.
- [ ] `og:image:alt` and `twitter:image:alt` are present, identical, and describe the card without asserting any number.
- [ ] `python3 scripts/validate_site.py` → exit 0. `python3 -m unittest discover -s tests` → 24 tests OK.
- [ ] Browser check on the served page: request count still **1**, `performance.getEntriesByType('resource')` still **`[]`**, console errors **0**.

---

#### IMG-PROMPT-02 — the ◈ brand mark and favicon system (P0)

**Hand-authored SVG · 0 bytes of `/assets/` · 0 HTTP requests · +403 B brotli total (whole section)**

##### The bug being fixed

`site/index.html:17` is `<link rel="icon" href="data:image/svg+xml,<svg …><text y='26' font-size='26'>📈</text></svg>">`. It renders an **OS emoji through an SVG `<text>` element**. Any surface that rasterises the SVG without an emoji font — several bookmark, tile and reader-mode renderers — gets an empty box. It is also a chart-going-up glyph, which is exactly the buy-signal semantic §2.2 excludes, and it is not the brand mark: the wordmark at `site/index.html:262` is `◈`.

The fix is 12 numbers. **Do not generate this.** A vector mark of this kind is defined by its geometry, and a model cannot be told "half-diagonal 29, ring half-diagonal 22, inner half-diagonal 11" in a way that survives sampling.

##### FALLBACK — the deterministic source (recommended, ship this)

U+25C8 WHITE DIAMOND CONTAINING BLACK SMALL DIAMOND, drawn as **one path with three subpaths and `fill-rule="evenodd"`**: outer diamond fills, ring interior becomes a hole, inner diamond fills again. One element, no stroke, resolution-independent.

Geometry on a 64×64 grid, centre (32,32): outer half-diagonal 29, ring inner half-diagonal 22 (giving a perpendicular ring thickness of (29−22)/√2 ≈ 4.95 units), inner solid half-diagonal 11.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path fill="#9A6F1E" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg>
```

**188 bytes** as a file. Two shipped forms:

###### Form 1 — favicon, twin theme-scoped data URIs (0 requests). **REPLACE `site/index.html:17`.**

```html
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path fill='%239A6F1E' fill-rule='evenodd' d='M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z'/></svg>" media="(prefers-color-scheme: light)">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><path fill='%23D9A94F' fill-rule='evenodd' d='M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z'/></svg>" media="(prefers-color-scheme: dark)">
```

Two rules make this work and are easy to get wrong:
- `#` **must** be percent-escaped as `%23`, and attribute quotes inside the URI **must** be single. Unescaped `#` truncates the URI at the fragment.
- **Do not put a `<style>` with a `prefers-color-scheme` media query inside the data URI**, even though it is the obvious way to make one icon theme-aware. It passes the gate and breaks `tests/test_validate_site.py:146`. See Trap 1, §2.5. The twin-`media`-link form is the safe equivalent — MEASURED: gate exit 0, 24/24 tests OK, **1 request, 0 subresources**, glyph resolves to `rgb(154,111,30)` in light and `rgb(217,169,79)` in dark.

Cost: 209 chars per URI, 638 B of markup for the pair, vs the 150 B emoji tag it replaces. Net **+403 B brotli for this entire section**, and the request count is unchanged at 1.

###### Form 2 — inline in the wordmark. **REPLACE `site/index.html:262`.**

```html
<span class="mark"><svg class="glyph" viewBox="0 0 64 64" width="13" height="13" aria-hidden="true" focusable="false"><path fill="currentColor" fill-rule="evenodd" d="M32 3 61 32 32 61 3 32Z M32 10 54 32 32 54 10 32Z M32 21 43 32 32 43 21 32Z"/></svg> BountyCharts</span>
```

`fill="currentColor"` inherits `.brand .mark { color: var(--gold) }` (`site/index.html:96`), so the glyph is theme-correct in both palettes with **zero additional CSS** — MEASURED, computed `color` reads `rgb(154,111,30)` light and `rgb(217,169,79)` dark. `aria-hidden="true"` + `focusable="false"` keeps the accessible name of the wordmark unchanged. This removes the site's dependence on the host having a glyph for U+25C8, which is not guaranteed in every system font.

###### Form 3 — file (only if a `<style>`-based theme swap is genuinely wanted)

`/assets/mark.<hash>.svg`, 296 B with an internal media query. Valid, gate-clean, 24/24 tests OK — the `<style>` trap only applies to `.html` files. **Costs +1 HTTP request (596 B transferred, MEASURED).** Not recommended; Form 1 gets the same result for free.

##### Generative path — for completeness only

Do not use it for the shipped mark. If you want exploratory variations on the *mark concept* before committing to the geometry above:

**Style anchor:** §2.1 verbatim. **Positive prompt:**

```
[PASTE STYLE ANCHOR FROM §2.1 HERE]

SUBJECT: A single abstract geometric logomark. One outlined rhombus (a square rotated
45 degrees) containing one smaller solid rhombus at its exact centre, concentric,
sharing the same 45-degree orientation. Nothing else.

COMPOSITION: perfectly centred on a square canvas, occupying 62% of the width, with
equal clear space on all four sides. Bilaterally and vertically symmetric. The outer
rhombus is an even-weight outline whose stroke is roughly 1/6 of its own half-width;
the inner rhombus is a solid fill with a gap of clear background between the two.

COLOUR: mark in #D9A94F on a #0E1116 background. Exactly two colours in the image.

LIGHTING / TEXTURE: none. Flat vector. Hard edges. No anti-aliasing artefacts, no
gradient, no shadow, no glow, no bevel.

ASPECT RATIO: 1:1.
```

**Negative prompt:** NEG-CORE from §2.2, plus `, letter, letters, text, wordmark, typography, monogram, initials, multiple shapes, cluster, pattern, repetition, tiling, circle, hexagon, triangle, star, shield, crest, gem, jewel, crystal, faceted, gradient fill, drop shadow, outline glow, mockup, presentation board, logo grid, colour variations, business card`. The `gem / jewel / crystal / faceted` exclusion matters specifically: models read "diamond" as a gemstone, which imports treasure-and-value connotations §2.2 blocks, and a faceted render is neither flat nor cheap to encode. `mockup / presentation board / logo grid` blocks the very common failure of returning a *picture of a logo presentation* rather than a logo.

**Parameters:** Midjourney `--ar 1:1 --style raw --stylize 0 --chaos 0 --seed 20260816`; SDXL `1024x1024`, CFG 3.5, steps 28, DPM++ 2M Karras, fixed seed; DALL·E 3 `size:"1024x1024", style:"natural"`. **Whatever comes back must be redrawn as a vector path by hand before shipping** — a rasterised or auto-traced mark will not be 188 bytes and will not be pixel-crisp at 16 px.

##### Acceptance checklist

- [ ] The mark is **one `<path>`** with `fill-rule="evenodd"` and three subpaths. No `<circle>`, no `<rect>`, no `stroke`, no `<g>`, no `<style>` in the inline/data-URI forms.
- [ ] SVG source is **≤ 200 B** flat (reference: 188 B). Data URI ≤ 220 chars each (reference: 209).
- [ ] `#` is escaped `%23` in every data URI; attribute quotes inside the URI are single.
- [ ] Rendered at **16 × 16**: the ring and the inner diamond remain distinguishable and the shape is not a filled blob.
- [ ] Rendered at **512 × 512**: edges are clean 45° diagonals with no stair-stepping in the vector source.
- [ ] Contrast, computed: `#9A6F1E` on `#FFFFFF` = **4.5001**, on `#FAFAF8` = **4.3061**; `#D9A94F` on `#0E1116` = **8.7699**, on `#161A21` = **8.0895**. All four clear the **3:1** SC 1.4.11 non-text threshold; minimum across all four brand surfaces is **3.88:1**. No new token is introduced — this is `--gold` unchanged in both palettes.
- [ ] Inline wordmark glyph uses `fill="currentColor"`, `aria-hidden="true"`, `focusable="false"`; computed colour is `rgb(154,111,30)` in light and `rgb(217,169,79)` in dark.
- [ ] The emoji `<link rel="icon">` at `site/index.html:17` is **gone**, not merely supplemented.
- [ ] `python3 -m unittest discover -s tests` → **24 tests OK**. This is the check that catches Trap 1; the gate alone will not.
- [ ] Browser: request count still **1**, `resource` entries still **`[]`**.

---

#### IMG-PROMPT-03 — `apple-touch-icon` (P1)

**180 × 180 · `/assets/touch-icon-180.<hash>.png` · 582 B · 0 requests on a normal page load**

##### FALLBACK — deterministic. **There is no generative version of this. Do not write one.**

It is IMG-PROMPT-02's path on a solid tile. `render.mjs` in IMG-PROMPT-01 already emits it. Quantise to **16 colours**:

| Palette | Bytes | Max per-channel error |
|---:|---:|---:|
| 8 | 556 | 7 |
| **16** | **582** | **0 — mathematically lossless** |
| 32 / 64 | 582 | 0 |

16 colours is lossless here because the image contains only `#0E1116`, `#D9A94F` and their antialiasing blend. Going to 8 introduces error for a 26-byte saving.

**Design:** `#0E1116` full-bleed square, mark at 62% of the width (112 px) centred, `#D9A94F`. **Square corners, no rounding, no transparency, no padding beyond the 19% margin** — iOS applies its own corner radius and mask, and a pre-rounded or transparent icon produces a black-cornered artefact. 180 px is the size iOS actually requests; a single 180 covers every current device.

**Insertion — `site/index.html`, immediately after the twin `rel="icon"` links from IMG-PROMPT-02:**

```html
<link rel="apple-touch-icon" href="/assets/touch-icon-180.deb4fbbb.png">
```

Path-relative and local, so it passes the gate: `apple-touch-icon` **is** in `FETCHING_REL` (`scripts/validate_site.py:188-189`), and an absolute external URL here would be **blocked** — MEASURED. A local one passes.

**Cost: zero to a normal visitor.** MEASURED — with this tag present, `performance.getEntriesByType('resource')` remained `[]` and the request count remained 1 in both themes. Browsers fetch it only on add-to-home-screen or bookmark.

##### Acceptance checklist

- [ ] Exactly **180 × 180**, PNG, **opaque** (no alpha channel), square corners.
- [ ] **≤ 700 B** (reference: 582 B), indexed colour.
- [ ] Filename `touch-icon-180.[0-9a-f]{8}.png`, in `site/assets/`.
- [ ] Corner pixel (0,0) samples exactly `#0E1116`; centre pixel (90,90) samples exactly `#D9A94F`.
- [ ] Mark occupies 58–66% of width and is centred within ±1 px on both axes.
- [ ] Contrast `#D9A94F` on `#0E1116` = **8.7699** — non-text, threshold 3:1, clears by 5.77.
- [ ] Placed on an iOS home screen against both a light and a dark wallpaper: mark is legible and the corners are not black.
- [ ] `<link rel="apple-touch-icon">` href is **root-relative and local**. An absolute external URL fails the gate.
- [ ] Browser: request count still **1**, `resource` entries still **`[]`**.

---

#### IMG-PROMPT-04 — `Organization.logo` for JSON-LD (P1)

**512 × 512 · `/assets/logo-512.<hash>.png` · 2,166 B · crawler-fetched only**

##### Why this asset exists at all

`Organization.logo` is the **only image property Google actually consumes** from this site's structured data, and it must be a fetchable URL — which under `site/_headers:11-12` means a fingerprinted file. Google's guidance is ≥112 × 112 px; 512 is the safe modern minimum. There is currently **no `Organization` node at all** (`site/index.html:18-26` holds a single 5-key `WebSite`), so this asset and its JSON-LD land together.

##### FALLBACK — deterministic. No generative version.

Same tile as IMG-PROMPT-03 at 512 px; `render.mjs` emits it. Quantise to **32 colours**:

| Palette | Bytes | Max per-channel error |
|---:|---:|---:|
| 8 | 1,896 | 29 |
| 16 | 2,027 | 12 |
| **32** | **2,166** | **3 — imperceptible** |
| 64 | 2,242 | 0 |

**Replace `site/index.html:18-26` entirely** with an `@graph`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://bountycharts.com/#org",
      "name": "BountyCharts",
      "url": "https://bountycharts.com/",
      "logo": {"@type": "ImageObject", "url": "https://bountycharts.com/assets/logo-512.59a79860.png", "width": 512, "height": 512},
      "sameAs": ["https://github.com/kevynsgrin-a11y/BountyCharts"],
      "disambiguatingDescription": "BountyCharts is an independent project. It is not affiliated with, endorsed by, or sponsored by Riot Games, The Pokémon Company, Bandai Namco, Wizards of the Coast, or any card game publisher."
    },
    {
      "@type": "WebSite",
      "@id": "https://bountycharts.com/#site",
      "name": "BountyCharts",
      "url": "https://bountycharts.com/",
      "inLanguage": "en",
      "publisher": {"@id": "https://bountycharts.com/#org"},
      "image": "https://bountycharts.com/assets/og-card.f36a278c.png",
      "description": "Price and metagame intelligence for trading card games."
    }
  ]
}
</script>
```

Three things this block is doing deliberately:

1. **`"@type": "WebSite",` is spelled with exactly one space and a trailing comma.** Minify it or reorder `@type` to the end of the node and `tests/test_validate_site.py:97` fails with `AssertionError: 0 != 1`. See Trap 2, §2.5. MEASURED both ways.
2. **`disambiguatingDescription` carries the independence disclaimer** from `site/index.html:339` verbatim — machine-readable brand safety at zero visible page cost. The `é` is escaped `é` to keep the block ASCII-safe.
3. **`sameAs`** uses the site's one existing outbound link (`site/index.html:333`).

**Verified:** gate exit 0, 26 ok / 0 fail; `Ran 24 tests … OK`; JSON-LD parses in-browser to a 2-node graph with `logo.url` resolving correctly.

##### Acceptance checklist

- [ ] Exactly **512 × 512**, PNG, opaque, ≤ 3,000 B (reference: 2,166 B), indexed colour.
- [ ] Filename `logo-512.[0-9a-f]{8}.png`; hash matches file contents.
- [ ] Contrast `#D9A94F` on `#0E1116` = **8.7699** (non-text, 3:1 threshold).
- [ ] `site/index.html` contains the **literal** string `"@type": "WebSite",` — grep for it, exactly one match.
- [ ] JSON-LD parses: `JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent)` returns an object whose `@graph` has length 2.
- [ ] `logo.url`, `image` and the `og:image` URL are **absolute** and all point at existing fingerprinted files.
- [ ] `disambiguatingDescription` names all four publishers exactly as `site/index.html:339` does.
- [ ] Google Rich Results Test accepts the Organization node (run post-deploy; cannot be verified locally — **INFERRED**).
- [ ] `python3 scripts/validate_site.py` → exit 0; `python3 -m unittest discover -s tests` → 24 OK.

---

#### IMG-PROMPT-05 — second-page social card (P2, conditional)

**1200 × 630 · `/assets/og-<page>.<hash>.png` · ~15 KB · only if Lens 1 ships a second page**

The research recommends a `/method` page carrying the status key, the corrected 17/5/10/6 scorecard, the correction-against-interest and the source list. If it ships, it needs its own card — a shared card makes every share look like the homepage.

**Do not author a new design.** Reuse `tools/og/og-card.html` and change exactly three strings; the family consistency is then free and structural rather than a matter of prompt discipline.

| Slot | Homepage | `/method` |
|---|---|---|
| `<h1>` | What will this deck **cost you** next week? | We checked **all 38** of them. |
| `.legend` | Deck cost · Movement · Spread · Reprint risk | Confirmed · Overstated · Wrong · Unsubstantiated |
| `footer .url` | bountycharts.com | bountycharts.com/method |

The legend becomes the four ledger status categories — still a vocabulary, still no numbers, still nothing directional. **Do not put "17 / 5 / 10 / 6" on the card**: those counts are a live property of a file, the card is frozen for a year by `immutable` plus the platform scrape cache, and the research already found the ledger's own scorecard contradicting its own rows. A frozen wrong count on a shared image is the exact failure mode the page exists to disprove.

Everything else — the anchor, NEG-CORE, tool parameters, the fallback pipeline, the acceptance checklist — is IMG-PROMPT-01's, unchanged, plus: the new page's `<head>` needs its own `og:image`, `og:image:alt`, `twitter:image`, `twitter:image:alt` and `twitter:card = summary_large_image`, and the new `<url>` in `sitemap.xml` needs a **date-only** `<lastmod>` (`^\d{4}-\d{2}-\d{2}$`, `tests/test_validate_site.py:213-218` — a full ISO datetime fails, despite being valid per sitemaps.org).

---

#### IMG-PROMPT-06 — editorial texture plate (P2 — **specified so it can be rejected on evidence**)

**The one asset where a generative model is defensible. The measurement says do not ship it.**

The assignment is to write the prompt, so here it is, complete and paste-ready. The recommendation attached to it is: **do not use it.**

##### Positive prompt

```
[PASTE STYLE ANCHOR FROM §2.1 HERE]

SUBJECT: An abstract background plate for an editorial header. No object and no
subject — a field. The impression of a precision measuring surface photographed
flat-on: an anodised instrument faceplate, a machinist's granite surface plate, an
engineer's rule laid on dark steel.

COMPOSITION: 1200x630 landscape, entirely non-focal. Extremely faint horizontal
structure only: three or four hairline horizontal rules at irregular intervals, and
sparse short vertical tick marks along one of them, all at the very edge of
visibility. The upper-left and centre 60% of the canvas is completely empty and
must stay empty for type to be composited on top later. No focal point, no centre
of interest, nothing the eye can land on.

COLOUR: #0E1116 base. Structure in #232932. At most one hairline in #6B7482. No
gold anywhere — the accent is reserved for composited type. Maximum four distinct
values in the entire image.

LIGHTING: perfectly even. No falloff, no vignette, no hotspot, no directional light.

TEXTURE: none beyond the hairlines. Absolutely no grain, no noise, no dust, no
scratches, no paper fibre.

TYPOGRAPHY: none. This plate carries no text of any kind; all type is composited
afterwards in a vector tool.

ASPECT RATIO: exactly 1200:630 (40:21).
```

##### Negative prompt

NEG-CORE from §2.2, verbatim, **plus**: `, focal point, subject, centre of interest, object, product shot, gradient, vignette, glow, light source, highlight, reflection, specular, grain, noise, dust, scratches, distressed, weathered, patina, wood, marble, concrete, fabric, paper texture, gold, yellow, warm tones, colour cast, text, letters, numbers, symbols, watermark`.

The extra `gold / warm tones / colour cast` exclusion is a system-integrity constraint: `#D9A94F` is the only accent in the brand and it must mark exactly one thing. A plate that is faintly warm everywhere destroys the accent's meaning across the entire asset family.

##### Parameters

Midjourney `--ar 40:21 --style raw --stylize 0 --chaos 0 --seed 20260816`; SDXL `1216x640`, CFG 3.0 (low — this is a texture, not a composition), steps 24, DPM++ 2M Karras, fixed seed, no refiner; DALL·E 3 `size:"1792x1024", style:"natural"` then crop.

##### FALLBACK and verdict

**MEASURED cost of shipping any textured plate, using the flat card as the control and adding only a radial glow plus fine grain — the two things every model adds by default:**

| Encoding | Flat card | Textured card | Multiple |
|---|---:|---:|---:|
| PNG-24 as rendered | 44,059 B | 1,310,356 B | **29.7×** |
| PNG-8, 64 colours | **15,493 B** | 345,904 B | **22.3×** |
| WebP q0.80 | 18,750 B | 50,976 B | 2.7× |
| **JPEG q0.80 (best sane shippable)** | 34,968 B | **73,662 B** | **2.1×** |
| Unique colours | 2,067 | 29,145 | 14.1× |

Against the flat card's actual shipped encoding (PNG-8/64, 15,493 B), the best shippable textured encoding is **73,662 B — 4.75× the cost, and 4.85× the entire current site on disk (15,181 B)**. JPEG additionally introduces ringing artefacts around the 15 px monospaced type, and WebP is unreliable as an og:image across X and LinkedIn — so PNG-8 is the only format choice that is both universally rendered and cheap, and PNG-8 is exactly the format texture destroys.

**Verdict: reject.** The deterministic flat plate — `background: #0E1116` with the CSS `repeating-linear-gradient` scale already in `tools/og/og-card.html` — delivers the same "instrument surface" reading, costs 0 additional bytes because it is part of the card render, is byte-reproducible, and hits the brand hex exactly. If a plate is ever genuinely wanted, author it as CSS gradients in the template, not as a raster.

##### Acceptance checklist (if shipped against this advice)

- [ ] Unique colour count **≤ 8**. Above that, texture got in and the byte budget is gone.
- [ ] File size **≤ 25,000 B** as PNG-8. If it will not quantise under 25 KB, it is disqualified.
- [ ] The upper-left and centre 60% of the canvas sample to exactly `#0E1116` at every probe point.
- [ ] No pixel anywhere is warmer than `#232932` in hue — **no gold in the plate**.
- [ ] Composited type on top still clears the §2.3 ratios **against the lightest pixel it overlaps**, not against `#0E1116`. Recompute; a plate makes the background non-uniform and every ratio in §2.3 is invalidated by it.
- [ ] Provenance recorded in `tools/og/PROVENANCE.md`: model, version, full prompt, seed, sampler, all parameters.

---

##### Why no shipped asset contains model-generated pixels — the summary argument

1. **Text.** Every asset here carries the wordmark, the tagline or the URL. No current image model renders "BountyCharts" or "TCG price × meta" reliably, and the `×` is U+00D7, not the letter x. Any generative route requires compositing type in a vector tool afterwards — at which point the "generated" content is only the background, and §2.6.2 applies to it.
2. **Bytes.** MEASURED: the model's default aesthetic costs **4.75×**, and 4.85× the entire current site. The site's single best measured quality is that it is 15,181 B and loads in 1 request.
3. **Colour.** The brand is eleven exact hex values with a known, unfixed AA failure in the light palette. A sampled image does not hit `#D9A94F`; it hits something near it. Every ratio in §2.3 becomes an estimate.
4. **Reproducibility.** `/assets/*` is `immutable` for a year. When the card needs one word changed, the deterministic template re-renders byte-identically except for that word; a generative re-roll returns a different picture.
5. **Legal.** The exclusion list in §2.2 is 90 terms long because the model's training distribution for "trading card game" is *saturated* with exactly the card frames, set symbols and character art the footer disclaims. Every generation is a draw against that distribution. A hand-authored diamond and a CSS ruler are draws against nothing.

The honest scope for a generative model on this project is **exploration, not production** — mood boards to argue about before someone writes the 12 numbers in IMG-PROMPT-02.

---

##### Verification log

All commands run against a scratch copy of `site/`, `scripts/`, `tests/` with every asset in this section installed and every head change applied.

| Check | Result |
|---|---|
| `python3 scripts/validate_site.py` | **exit 0**, `All checks passed.`, 26 ok / 0 fail |
| `python3 -m unittest discover -s tests` | **`Ran 24 tests … OK`** |
| Chromium, production CSP replayed, `colorScheme: light` | 1 request, 14,359 B encoded, 88 elements, load 26.4 ms, **0 subresources, 0 console errors, 0 failed requests**, glyph `rgb(154,111,30)` |
| Chromium, production CSP replayed, `colorScheme: dark` | 1 request, 14,359 B encoded, 88 elements, load 18.3 ms, **0 subresources, 0 console errors, 0 failed requests**, glyph `rgb(217,169,79)` |
| CSP runtime block proof | external `<img src>` → `Refused to load the image … violates … "img-src 'self' data:"`; external `<use href>` → `Unsafe attempt to load URL … Domains, protocols and ports must match.` Both **missed by the gate** (Trap 3) |
| Square-crop test, centre 630×630 | wordmark, both headline lines, scale and label row all fully retained |
| `index.html` brotli q11 | 3,179 → **3,582 B** (+403) |
| `/assets/` total on disk | **18,241 B**, visitor-fetched **0 B / 0 requests** |

Reference build fingerprints (regenerate on any re-render — the hash is the only cache-buster):

```
site/assets/og-card.f36a278c.png          15,493 B
site/assets/logo-512.59a79860.png          2,166 B
site/assets/touch-icon-180.deb4fbbb.png      582 B
```

---
## 6. Content

### 6.1 On-page copy: promise versus delivery

#### Lens 3 — On-page content gaps and draft copy (`index.html`, `404.html`)

Every draft below was applied to a scratch copy of `site/`, `scripts/`, `tests/` and verified end to end: **`python3 scripts/validate_site.py` → exit 0, 26 ok / 0 fail** and **`python3 -m unittest discover -s tests` → Ran 24 tests, OK** (MEASURED). Contrast is the real WCAG 2.x relative-luminance formula, read back from Chromium computed styles in both `colorScheme: light` and `dark`, with `opacity` composited by hand. Layout figures are from Playwright at 1280×800, 768×1024 and 390×844.

---

##### Promise vs. delivery — the audit

| # | The page promises | It delivers | Grade |
|---|---|---|---|
| A | `<h1>` "What will this deck cost you **next week**?" (`:269`) — a forecast | No product. And `:326` commits: "does not publish … **price predictions** … and never will" | **Internal contradiction.** MEASURED both strings. |
| B | `<h3>` "Deck cost, **forecast**" (`:301`) | Its own body copy (`:302`) is purely retrospective: "what it costs now, what it cost last week" | Heading over-claims past its own paragraph |
| C | `<h2>` "What it **does**" (`:297`) | Present tense about a product that does not exist | Tense defect |
| D | Ticker: `+18.4%`, `−9.1%`, `11.2%`, `Elevated` (`:274-293`) | All four invented. Disclosure is a CSS `::after` string at **9.28 px** and **2.2345:1** | See §3 — worst text on the site |
| E | "Every trading card game has a dozen tools… **None of them** tell you what it will cost" (`:270`) | An absolute negative claim about ~8 named competitors. The research's own wording (`docs/tcg-deep-dive-2026.md:179`) is "none of them do **well**" — the hedge was dropped on the way to the page | Factual claim about third parties |
| F | "a **permissive fan-content policy**" (`:319`) | **No source exists in the repo.** `docs/tcg-deep-dive-2026.md:126` asserts it; the `## Sources` block (`:254-268`) contains no Riot legal URL. `grep -rniE 'riotgames\.com\|jibber\|fan.?content'` over `docs/` returns zero URLs | MEASURED. **Corrects the Phase-1 research report**, which lists "give `:319` its citation" as "the cheapest credibility fix — one link." That link does not exist yet. |
| G | "a **primary-source** audit" (`:332`) | 12 of 33 sources are primary = **36.4%** | Defensible as method, reads as "all sources are primary" |
| H | "Pre-launch… The product is in build" (`:332`) | No date. Ages invisibly | See §5 |
| I | "what the data says, **and where it came from**" (`:326`) | Zero provenance anywhere on the site | Unkept promise |
| J | One outbound link, to repo root (`:333`) | `README.md:12` front-links a 252,740-byte internal agent prompt | Brand risk on the site's only exit |
| K | No CTA, no launch signal, no contact | — | See §4 |

**Fold geometry (MEASURED, current page).** The four invented figures sit at y=465–576 — entirely above the 800 px desktop fold. The word "Pre-launch" first appears at y=1431 (desktop, **1.79 screens down**) and y=2299 (390×844, **2.72 screens down**). *A visitor sees the fabricated numbers on first paint and the disclaimer three screens later.* That, not the H1, is the honesty defect with the largest blast radius.

---

##### The hero — is "next week" honest?

The question itself is fine; a pre-launch page is allowed to state the problem it exists to solve. Two specific things are not fine:

1. **"next week" is future tense, i.e. a forecast** — and 100 lines below, the page's load-bearing brand commitment says it will never publish price predictions. Whichever one a reader believes, the other is false.
2. **The pre-launch state is not co-visible with the claim.** Fixing (1) without fixing this leaves the page reading as a live product for the first screen and a half.

**CNT-PAGE-01 — H1 replacement.** Anchor: replace `site/index.html:269` in full. ⚠️ **LEGAL/BRAND SIGN-OFF REQUIRED** — this is the interface between the marketing claim and the no-predictions commitment.

```html
    <h1>What is this deck <span class="accent">actually</span> costing you?</h1>
```

Present tense, no forecast, and — MEASURED — 38 characters against the original's 38, rendering to **2 lines at 57.6 px desktop and 33.6 px mobile, identical to today**. Layout-neutral drop-in; keeps the `.accent` span so no CSS changes.

Alternates, if the team wants a different register:

| | Text | Trade-off |
|---|---|---|
| B | `The deck lists are free. <span class="accent">The cards are not.</span>` | Declarative, zero over-claim, strongest line on the page — but loses the question hook and the `og:title` no longer rhymes with it |
| C | `What did this deck <span class="accent">cost you</span> last week?` | Provably deliverable, wry against the original — weakest motivator |
| D | `Which result <span class="accent">moved</span> this price?` | Matches the one genuine differentiator (§ "Movement, explained") — narrower promise, narrower audience |

**Do not "fix" the gold accent.** MEASURED: `--gold #9A6F1E` on `--bg` is **4.3061:1**, but `h1` computes to **57.6 px** (desktop) / **33.6 px** (mobile) — both ≥ 24 px, so WCAG large-text applies and the threshold is 3:1. **The accent passes.** The wordmark does not: `.brand .mark` is the same gold at **15.2 px / weight 700** = **4.3061:1, FAIL** (not large text; bold large starts at 18.66 px). That is a pre-existing defect this lens does not touch — it is fixed by shipping `--gold #966C1D` (4.5059:1), not by editing copy.

**CNT-PAGE-02 — lede.** Replace `site/index.html:270`. ⚠️ **SIGN-OFF** (factual claim about competitors).

```html
    <p class="lede">Every trading card game has a dozen tools that tell you which deck is best. Few tell you what it costs to build, and none tie a price move to the result that caused it. BountyCharts is being built on that intersection — price movement against metagame shift.</p>
```

Restores the hedge the research actually carries, replaces the un-evidenced absolute with a specific differentiator, and flags pre-launch in the second sentence a visitor reads.

**CNT-PAGE-03 — standing status line, above the fold.** New element, insert between `site/index.html:264` (`</header>`) and `:266` (`<main>`). Deliberately outside `<main>` so it is not part of the document's main content.

```html
  <p class="standing">Pre-launch — nothing on this page is live market data. Last updated <time datetime="2026-08-16">16 August 2026</time>.</p>
```

```css
  .standing {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--ink-soft);
    margin: 0;
    max-width: none;
  }
```
Insert the rule after `site/index.html:169`. MEASURED after patch: renders at **12.48 px**, `--ink-soft` → **5.9809:1 light / 7.3390:1 dark — PASS both**; lands at y=121–142 desktop and bottom y=162 on 390×844, i.e. **above the fold on every tested viewport**.

**CNT-PAGE-06 / -07 — tense and forecast fixes.**

- `site/index.html:297`: `<h2>What it does</h2>` → `<h2>What it will do</h2>`
- `site/index.html:301`: `<h3>Deck cost, forecast</h3>` → `<h3>Deck cost, tracked</h3>` ⚠️ **SIGN-OFF** — removes a forecast claim, same commitment as CNT-PAGE-01.

---

##### The ticker disclosure

**The defect, MEASURED.** `.cell.sample::after` (`site/index.html:159-169`) is `--ink-faint` at `opacity: 0.75`:

| Theme | Declared | Composited | Ratio | Size |
|---|---|---|---:|---:|
| Light | `#8A93A1` on `#FFFFFF` | **`#A7AEB9`** | **2.2345:1** | 9.28 px |
| Dark | `#6B7482` on `#161A21` | **`#565E6A`** | **2.6622:1** | 9.28 px |

Both fail AA (4.5:1) and both fail even the 3:1 non-text threshold. It is the least legible text on the site, and it is the qualifier on the most assertive content on the site.

Three further properties, all MEASURED, that the ratio alone does not capture:

- It is **CSS generated content**, so it is not in the DOM: it cannot be selected, copied, translated, or found by in-page search, and it does not survive into any text extraction of the page.
- The strip carries `role="img"` (`:273`). Per ARIA, descendants of `role="img"` are presentational — a screen-reader user gets the `aria-label` and **nothing else**. So the AT experience is currently *better* than the sighted one. (Chromium's `Accessibility.getFullAXTree` still lists the descendants; the exposed name resolves from the label. Verified via CDP.)
- The `@media print` block (`:253`) already sets `.cell.sample::after { opacity: 1 }` — someone previously noticed this was illegible and fixed it *only for print*.

**The fix has three parts. Do not ship one without the others.**

**CNT-PAGE-04 — visible caption that is also the accessible name.** Replace `site/index.html:273` and close a wrapper after `:294`:

```html
  <div>
  <p class="ticker-cap" id="ticker-cap">Illustrative mock-up: invented figures for a deck cost rising with meta share, a card falling as play rate drops, a price spread, and a reprint-risk flag. BountyCharts is not tracking live data yet.</p>
  <div class="ticker" role="img" aria-labelledby="ticker-cap">
```
…and after the closing `</div>` of `.ticker` at `site/index.html:294`, add one more `  </div>`.

```css
  .ticker-cap {
    font-size: 0.85rem;
    color: var(--ink-soft);
    max-width: 62ch;
    margin: 0 0 0.75rem;
  }
```

Why `aria-labelledby` rather than `aria-label`: it makes the visible disclosure and the accessible name **the same string**, so they cannot drift, and it removes the current situation where the honest disclosure exists only for users who cannot see the thing being disclosed. MEASURED after patch — CDP reports the image node's accessible name resolving from `relatedElement/aria-labelledby` with the caption text exact. Caption renders at **13.6 px**, `--ink-soft` → **5.9809:1 light / 7.3390:1 dark — PASS**.

**Placement matters and is measurable.** The caption sits at y=550–617 and the strip at y=629 — the reader meets the disclosure **before** the numbers, and both are above the desktop fold. A caption below the strip is read after the claim it qualifies, which is the same failure mode as the current bottom-of-page "Pre-launch".

**Accessible name (exact):**
> Illustrative mock-up: invented figures for a deck cost rising with meta share, a card falling as play rate drops, a price spread, and a reprint-risk flag. BountyCharts is not tracking live data yet.

**CNT-PAGE-05 — per-cell badge legibility.** Replace `site/index.html:159-169`:

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
Three changes: word, size, colour. **"sample" → "example"** because a *sample* can legitimately be a real sample of real data; an *example* cannot. Drops `opacity` entirely. MEASURED after patch: **11.52 px, `--ink-soft` → 6.2504:1 light / 6.7696:1 dark — PASS both**, up from 2.2345 / 2.6622, a 2.8× improvement. Consequence: `@media print`'s `.cell.sample::after { opacity: 1 }` (`:253`) becomes a no-op and can be deleted.

**CNT-PAGE-15 — the real fix, deferred.** The strongest version of this section replaces three invented figures with real, dated, confirmed Riftbound figures (`docs/fact-check-ledger.md:44-46`): Western launch 31 Oct 2025; TCGplayer listings ~68,600 → ~118,100 across 30–31 Oct 2025; 6,300 searches/hour. These read as instrumentation, not speculation, and none requires card art. **Blocked on two hard dependencies:**
1. There must be a source link on the site, or this reproduces the exact failure the page criticises. That needs lens 4's `/method` page.
2. `docs/fact-check-ledger.md:88-91` states 15/6/10/7; the rows count **17/5/10/6**. Nothing derived from that ledger should be published until it is corrected.

Explicitly **exclude the Kai'Sa Signature $2,356 peak** from any ticker cell. A single card's peak price in a ticker reads as an investment-upside display and collides with constraint 6, regardless of how it is labelled.

---

##### Call to action and launch notification

**The constraint, stated precisely.** `site/_headers:6` sets `form-action 'self'`. That directive governs the target of a `<form>` submission. It does **not** govern `<a href>` navigation — the directive that would have (`navigate-to`) was never shipped in any browser. So the space of options is wider than "no form, therefore nothing."

| Option | CSP | Deploy gate | Verdict |
|---|---|---|---|
| **1. `mailto:` link** | Not a form and not a fetch — no directive in this policy applies | **PASSES** (MEASURED: probe contained `mailto:…?subject=…`, gate exit 0) | **Recommended now.** Zero infrastructure, zero third party, zero PII processor, no privacy policy needed. Costs: address is scraped; no double opt-in; poor on mobile webmail |
| **2. `<a>` out to a hosted form (Tally, Buttondown, Google Form)** | Top-level navigation — CSP does not apply | **PASSES** (MEASURED: probe carried 4 external `<a href>`; gate exit 0) | Works, but hands the visitor and their address to a third-party origin with its own trackers, on a site that today has **zero** third parties and **no privacy or analytics disclosure page**. Do not ship this before that page exists |
| **3. Amend CSP to `form-action 'self' https://provider`** | Requires editing `_headers:6` | Passes | **Reject.** `form-action` is the directive that stops an injected form exfiltrating to an attacker. Weakening it buys nothing over option 2 — the visitor lands on the provider's confirmation page either way — while adding real risk |
| **4. Cloudflare Pages Function at `/api/subscribe`** | Same-origin POST — satisfies `form-action 'self'` **with no CSP change** | `functions/` is outside `site/`, gate unaffected | **Technically cleanest, wrong time.** Adds a serverless endpoint, a store (KV/D1), an email sender, PII handling and a mandatory privacy policy to a 6-file static site. This is the launch-day answer, not the pre-launch one |
| **5. Static Atom feed `/feed.xml` + `<link rel="alternate">`** | Same-origin, zero PII | `alternate` is explicitly **not** in `FETCHING_REL` (`scripts/validate_site.py:188-189`) and the href is local anyway | **Adopt when there is a second page.** ~600 B. A one-entry feed on a one-page site is not yet worth it |
| **6. GitHub Watch → Releases** | n/a | n/a | Free, honest, zero infra. Low conversion, but the audience is GitHub-literate |

**Recommendation: 1 + 6 now, 5 when `/method` ships, 4 at launch.**

**CNT-PAGE-11 — notification section.** New `<section>`, insert after `site/index.html:334`. ⚠️ **LEGAL SIGN-OFF REQUIRED** — the second paragraph is a privacy commitment and is the site's only one.

```html
  <section>
    <h2>Hearing about launch</h2>
    <p class="tight">There is deliberately no signup form here. This site runs no scripts and calls no third party, and a form would end both. Two ways to hear when it ships:</p>
    <p class="tight"><a href="mailto:hello@bountycharts.com?subject=Notify%20me%20at%20launch">Email hello@bountycharts.com</a> — put anything in the body. Your address is used to tell you about launch and for nothing else: not sold, not shared, not added to any other list.</p>
    <p class="tight"><a href="https://github.com/kevynsgrin-a11y/BountyCharts">Watch the repository on GitHub</a> and choose <em>Custom → Releases</em>. Nothing reaches us that way at all.</p>
  </section>
```

Four blocking notes on this block:

1. **`hello@bountycharts.com` does not exist.** MX must be configured before this ships. Cloudflare Email Routing is free on the zone the site already uses and gives a rotatable alias, which is the right answer to the scraping cost (INFERRED — not verified against the live zone).
2. **Do not substitute the maintainer's personal address.** Publishing a personal mailbox on a commercial page is a separate decision that belongs to a human, and git authorship is not consent.
3. **I removed "sets no cookies" from my own first draft.** "Runs no scripts" and "calls no third party" are MEASURED true (0 `<script>` beyond `ld+json`, 0 subresources, 1 request). Cookies are a claim about the **edge**, not the HTML — Cloudflare may set `__cf_bm` under bot management, and bountycharts.com is egress-blocked in this session so it cannot be verified. Do not restore that clause without checking a live response.
4. The privacy sentence must remain true. If a launch announcement is later mailed to everyone who wrote in, that **is** a list; the sentence as drafted permits exactly one launch message and nothing further.

---

##### A status treatment that ages honestly

The defect is not that "Pre-launch" is wrong. It is that **an undated status string ages dishonestly** — it looks equally current in 2026 and 2029 — whereas a dated one ages honestly, because the reader can see the staleness themselves. Corroborating evidence that this site already drifts: `site/sitemap.xml:5` says `<lastmod>2026-08-08</lastmod>` at HEAD `bfca67a`, dated 2026-08-16 (MEASURED).

**CNT-PAGE-09 — Status section.** Replace `site/index.html:330-334` entirely.

```html
  <section>
    <h2>Status</h2>
    <p class="tight">Pre-launch as of <time datetime="2026-08-16">16 August 2026</time>. There is no product yet, and no live data on this page. If that date is a long way behind today, this page has not been kept current and you should treat everything on it as stale.</p>
  </section>
```

The third sentence is the mechanism. A static site cannot inject a build date into prose, so instead the copy **tells the reader how to interpret its own staleness**. That is the only self-ageing device available without JavaScript, and it costs 24 words.

Maintenance rule to record wherever the deploy runbook lives: `<time datetime>` here, the visible date in `.standing` (CNT-PAGE-03), and `site/sitemap.xml:5` `<lastmod>` are **one fact in three places** and must move in the same commit. `tests/test_validate_site.py:213-218` requires `lastmod` to match `^\d{4}-\d{2}-\d{2}$` — date-only, stricter than sitemaps.org.

Note what this rewrite silently drops: **"a primary-source audit"** (`:332`). 12 of 33 sources are primary (36.4%); the phrase is defensible as a description of method but reads as a description of the corpus. The replacement copy in CNT-PAGE-10 describes the method without the ambiguous adjective.

---

##### Surfacing the research

**CNT-PAGE-10 — new section.** Insert after CNT-PAGE-09. ⚠️ **SIGN-OFF** — "38" is a published count and the links are the site's public evidence.

```html
  <section>
    <h2>The research</h2>
    <p class="tight">What does exist is the work underneath: an audit of the 2024–2026 trading card game market, a claim-by-claim fact-check of 38 figures the trade press repeats, and a runnable unit-economics model. Published in full, including the findings that argue against building this at all.</p>
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

Three deep links replace the single repo-root link, which resolves the brand risk at `README.md:12` (a visitor no longer lands next to a 252,740-byte internal agent prompt) without editing the README. "**including the findings that argue against building this at all**" is true and checkable — `docs/tcg-deep-dive-2026.md:62` (the flagship audience is worth $0), `:145` (the obvious product is self-defeating), `:239` ("pursuing the report's own #1 priority makes the business worse"). It is the single highest-trust sentence available to this page and it costs 11 words.

`/blob/main/` links follow the branch, which is correct for living research but will break if files move. Accepted.

**Deliberately not surfaced on the page:** the 17/5/10/6 scorecard (ledger is self-contradictory — fix first); TCGplayer's API conduct; the Pokémon enforcement characterisation; the yen revenue figures; the $2–6 RPM input. All per the Phase-1 research report's hold list, which I concur with.

**CNT-PAGE-08 — "Why Riftbound first".** Replace `site/index.html:319`. ⚠️ **SIGN-OFF.**

```html
    <p class="tight">Riot's card game launched into the West on 31 October 2025 with an active secondary market and a fast-moving metagame. It is young enough that the price history is thin and the information layer is still forming — which is exactly where this kind of tool is worth building. Other games follow.</p>
```

This **deletes** the "permissive fan-content policy" clause rather than citing it, because — MEASURED — no Riot legal URL exists anywhere in the repo to cite. On a page whose thesis is "where a claim could not be substantiated it is marked unsourced rather than repeated" (`README.md:38`), leaving an uncited assertion in the copy is the most damaging small thing on the site. If a human verifies the policy URL **in the same commit**, the fallback sentence is: `Riot publishes a fan-content policy that contemplates community projects.` with the link on "fan-content policy" — no comparative clause about other publishers. The launch date `31 October 2025` is a ✅ Confirmed row (`docs/fact-check-ledger.md:44`).

**CNT-PAGE-12 — meta description and `og:description`.** Replace `site/index.html:7` and `:12`. ⚠️ **SIGN-OFF** — these are the strings that appear in search results and social unfurls, and they currently lead with the forecast question.

```html
<meta name="description" content="Pre-launch. BountyCharts is being built to sit where trading card prices meet metagame shift — what a deck costs, and which result moved it. Riftbound first. The market research behind it is published in full.">
```
```html
<meta property="og:description" content="Pre-launch. Price and metagame intelligence for trading card games, starting with Riftbound. The market research behind it is published in full.">
```
Leading both with "Pre-launch." means the disclosure travels with every share, every SERP snippet and every unfurl — the one place a caption cannot follow the claim.

---

##### `404.html`

Current copy has four problems. **"404 — NO DATA"** (`:35`) is a category error on this site specifically: "no data" is an instrumentation state (an empty result set), not a routing state, and using it for a missing URL undercuts the one vocabulary the brand owns. The page carries **no wordmark**, so a visitor arriving from a broken external link sees no brand at all. `.code` is `--gold #9A6F1E` at **11.52 px / weight 700 = 4.3061:1 — FAIL AA** (11.52 px bold is not large text; that starts at 18.66 px). And "may not have shipped yet" is the honest half — it should be made concrete.

**CNT-PAGE-13 — body copy.** Replace `site/404.html:34-39`.

```html
<main>
  <span class="brand">◈ BountyCharts</span>
  <span class="code">404 — PAGE NOT FOUND</span>
  <h1>There is nothing at this address</h1>
  <p>The link may be out of date, or the page may not have shipped yet — most of BountyCharts has not. The site is pre-launch and currently has one page.</p>
  <p><a href="/">Back to the front page →</a></p>
</main>
```

"most of BountyCharts has not" turns the error page into a second, unexpected honesty signal at zero cost. When lens 4's `/method` ships, add one line: `<p><a href="/method">Or read the method behind the research →</a></p>`.

**CNT-PAGE-14 — 404 CSS.** Replace `site/404.html:26`.

```css
  .code { font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.16em; color: var(--ink-soft); font-weight: 700; }
  .brand { font-family: var(--mono); font-size: 0.95rem; font-weight: 700; letter-spacing: 0.02em; color: var(--ink); }
```
`--ink-soft` gives **5.9809:1 light / 7.3390:1 dark — PASS**, and unlike the alternative (bumping `.code` to ≥18.66 px so gold clears as large text) it does not depend on the `--gold` token remediation landing first. `404.html` declares `--ink-soft` in all four of its theme blocks (`:11, :16, :18, :19`), so no new tokens are required.

---

##### Verification and cost

Applied all of the above to a scratch copy and measured (MEASURED throughout):

| | Current | Patched | Δ |
|---|---:|---:|---:|
| `scripts/validate_site.py` | exit 0, 26 ok | **exit 0, 26 ok** | — |
| `python3 -m unittest discover -s tests` | 24 OK | **24 OK** | — |
| `index.html` raw | 11,657 B | 13,938 B | +2,281 |
| `index.html` gzip -9 | 4,049 B | 4,831 B | +782 |
| **`index.html` brotli q11 (production wire)** | **3,179 B** | **3,831 B** | **+652 (+20.5%)** |
| `404.html` raw / brotli | 1,891 / 765 B | 2,166 / 830 B | +275 / +65 |
| Site total on disk | 15,181 B | 17,737 B | +2,556 |
| HTTP requests | 1 | **1** | — |
| `performance.getEntriesByType('resource')` | `[]` | **`[]`** | — |
| DOM elements | 76 | 96 | +20 |
| Visible body words | 367 | 587 | +220 |
| Outbound links | 1 | 5 | +4 |
| Page height, 1280×800 | 1,909 px | 2,715 px | +806 |
| Page height, 390×844 | 2,900 px | 4,039 px | **+1,139 (3.44 → 4.79 screens)** |

The +652 B brotli **is** render-blocking — the CSS is inline, so the whole document is. At 3,831 B the landing page still fits inside a single initial congestion window, so the cost is bytes, not a round trip. Requests, subresources, images, fonts and scripts all stay at their current values.

**Two costs I am not hiding.** The mobile page grows 39% taller; if that is judged too much, merge CNT-PAGE-09 and CNT-PAGE-10 into one `<h2>Status and research</h2>` section, which recovers roughly 120 px and one heading. And **the count of failing gold `<h2>`s rises from 4 to 6** — `h2` is `--gold` at 11.52 px / 700 = 4.3061:1, and adding sections multiplies an existing defect. This is a real regression in count and the fix is not in this lens: ship `--gold #966C1D` (**4.5059:1** on `--bg`, **4.7090:1** on `--surface`) in the same release, or hold CNT-PAGE-10 and -11 until it lands.

**Nothing in this lens touches** the footer trademark disclaimer (`site/index.html:339`) or the "No buy signals" block (`:324-327`). Both are unmodified, byte for byte.

### 6.2 New pages and information architecture

#### Lens 4 — Information architecture and new pages

**Verdict: two new pages, not eight. The site goes from 2 pages to 4.** Everything below was built, placed in a scratch copy of `site/`, and run through the real gate and the real 24-test suite. Both are green. Working files: `/tmp/claude-0/-home-user-BountyCharts/ca78f328-b722-550c-b6ca-8bb935f63642/scratchpad/gatetest/site/`.

Grades: **MEASURED** (I ran it) · **OBSERVED** (read in the file) · **INFERRED** (judgment).

---

##### Candidate ruling — 2 accepted, 6 rejected or merged

| # | Candidate | Ruling | Reasoning |
|---|---|---|---|
| 1 | Methodology / how the data works | **ACCEPT** → `/method` | The site already promises this and does not deliver it. `site/index.html:326` says "what the data says, **and where it came from**"; the site provides provenance for nothing. This is the single largest gap between what the page claims and what it shows. |
| 2 | Research index (deep dive + ledger + model) | **REJECT as a page → MERGE** into `/method` §"Read it yourself" | It is three links. A page that is three links is a worse README than the README. Folded in as the closing section of `/method`, where it lands on a reader who has just been told how the grading works — which is the only context in which the links mean anything. |
| 3 | About / who is behind this | **REJECT (defer to owner)** | No consented identity exists anywhere in the repo. Git authorship is not consent to publish an identity. An anonymous about page ("an independent project by a small team") is *worse than none* on a site whose entire pitch is verifiability. The project-level identity claims that actually do work — independence, no positions, no funding — are on `/disclosures`, which is where they carry weight. Revisit when the owner decides on a byline. |
| 4 | Changelog / build log | **REJECT** | Nothing has shipped. A changelog whose first and only entry is "site launched" advertises that nothing happens. GitHub commit history and Releases already serve this for the pre-launch audience, which is the audience that would read it. Revisit at first product release. |
| 5 | Privacy | **REJECT as a page → MERGE** into `/disclosures` §"Analytics and what is collected" | MEASURED: 0 cookies, 0 forms, 0 JS, 0 accounts, 0 third-party origins. The honest privacy policy is four sentences. Four sentences do not need a URL, and a standalone `/privacy` implies a data practice that does not exist — it makes the site look like it collects more than it does. |
| 6 | Terms | **REJECT as a page → MERGE** the two operative clauses into `/disclosures` §"What this site does not do" | No accounts, no user content, no payment, no service to terminate. A ToS is a contract governing a relationship that does not exist. The only two clauses that matter pre-launch — no warranty, not investment advice — are two paragraphs, and one of them is already on the landing page. |
| 7 | Affiliate disclosure | **ACCEPT** → `/disclosures` | `docs/deployment/cloudflare.md:155` (OBSERVED): "an affiliate disclosure becomes legally required **before** the first link ships, not after." The page must therefore pre-exist the link. It also has to exist at launch regardless, because runbook step 7 (`cloudflare.md:145`) turns on traffic measurement on launch day. |
| 8 | Launch-notify page | **REJECT as a page → ACCEPT as a mechanism** | Triple-constrained: `form-action 'self'` (`site/_headers:6`) blocks any third-party POST endpoint; `tests/test_validate_site.py:268-276` blocks any JS that could work around it; and `cloudflare.md:154` reserves the ESP spend to the owner. The remaining working option is the repository link the site already has, framed as "Watch → Releases". A dedicated URL for one link is over-building. A same-origin `/feed.xml` becomes worth it at first product release, not before. |

**The push-back, stated plainly.** Shipping all eight candidates would take the site from 2 URLs to 10. MEASURED against the current corpus, five of those pages would come in under 200 words and three would say "not applicable yet." The cost is not bytes — it is that a 9-item footer on a pre-launch one-pager reads as a site pretending to be larger than it is, which is precisely the credibility failure this project's own thesis is built against. Two pages, both of which say something no competitor's equivalent page says, is the correct pre-launch answer.

---

##### `/method` — the accepted flagship page

| Field | Value |
|---|---|
| **File** | `site/method.html` (flat — see §4.5) |
| **URL** | `https://bountycharts.com/method` (extensionless — see RISK 1) |
| **`<title>`** | `Method — BountyCharts` |
| **Meta description** | `How a claim gets checked: the four grades, the count across 38 audited claims, where the sources come from, and the two corrections that cost us something.` (152 chars) |
| **H1** | `How a claim gets checked` |
| **Size** | MEASURED 12,871 B raw, **3,656 B brotli**, 110 elements, 666 visible words, 1 HTTP request, 0 subresources |

**Lede.** "BountyCharts is pre-launch. What exists today is the audit underneath it — a claim-by-claim check of an industry report on the 2024–2026 trading card game market. This page is the method: the grades, the counts, and the parts that went against us."

**§1 — The four grades.** One table doing double duty as key *and* scorecard:

| Grade | Claims | What it means |
|---|---|---|
| Confirmed | 17 | Checked against a source and holds as written. |
| Partly true | 5 | Directionally right, but overstated or missing a qualifier that changes the conclusion. |
| Materially wrong | 10 | The figure or the causal claim does not survive contact with the source. |
| Unsourced | 6 | Could not be substantiated. Marked as unsourced rather than repeated. |
| **Total** | **38** | Fewer than half survived unchanged. |

Closing copy: *"The last row is the point. A number that cannot be traced to anything is not a small number — it is not a number. Six of these are load-bearing figures repeated widely enough that they read as settled fact."*

⚠️ **MEASURED — these counts are 17/5/10/6, independently recounted from all 38 rows of `docs/fact-check-ledger.md`. The published scorecard at `fact-check-ledger.md:88-91` says 15/6/10/7 and is wrong on three of four rows.** Fixing the ledger is a **hard prerequisite** to shipping this page (see RISK 6).

Grades are rendered as words in mono caps, coloured `--up` / `--gold` / `--down` / `--ink-soft`. Colour is redundant to the word, so SC 1.4.1 is not engaged. No emoji — the repo's ✅⚠️🟡❓ do not survive as meaning-bearing content.

**§2 — Where the sources come from.** "The audit cites **33 sources across 29 distinct hosts. Twelve are primary** — the party's own document: an investor filing, a publisher's own policy page, a marketplace's own developer documentation, a company's own closure statement. The remaining twenty-one are trade press or vendor material. That is 36% primary, and it is stated as 36% rather than described as a primary-source audit, because the difference is the entire subject of this page."

This is a deliberate self-correction: `site/index.html:332` currently calls the work "a primary-source audit" at 36% primary. That copy must change in the same commit (CNT-IA-04) or the two pages contradict each other.

**§3 — Two checks that cost us something.** Two `.note` blocks.

> **Correction against interest** — "The source report describes backers of the cancelled Altered TCG as left unserved — an aggrieved audience a competitor could capture. They were not left unserved. Equinox is reimbursing backers, players and retailers in full, and released the final set digitally to active accounts. The report also puts the funding threshold at €2.5 million; the figure in Equinox's own statement is €2 million. Publishing that correction removes an audience an acquisition strategy was built around. It went in anyway. **A ledger that only ever corrects in your favour is not a ledger.**"

> **A number we will not quote** — "Analyst forecasts for the trading card game market in 2034–2035 span **$15.8 billion to $24.4 billion** — a 54% spread between firms describing the same market. That dispersion is a measurement-confidence problem, not a growth story. So there is no market-size figure anywhere on this site, and there will not be one."

**§4 — What stays in the repository.** The hold-back section. Discharges F13/F14 without repeating either: *"Characterising a named company's internal conduct from the absence of a reply is an inference, not a finding. Where the underlying document is public — a published API deprecation notice, a published fan-content policy — the document is cited and the analysis stops there. The full working, including the parts that are argument rather than evidence, is in the repository. It is not hidden; it is just not marketing."*

**§5 — Freshness.** Verified July 2026 · quarterly re-check cadence · "Prices, policies and affiliate terms move faster than that. Anything time-sensitive is dated where it appears, or it is not published." Plus a mono stamp: `Last human re-check: 2026-08-16`.

**§6 — Read it yourself.** Deep links to `docs/fact-check-ledger.md`, `docs/tcg-deep-dive-2026.md`, `models/unit_economics.py` — not the repo root. This is the fix for the `README.md:12` brand risk (a visitor landing on a 252 KB internal agent prompt).

**Links in:** `index.html` Status section · `/disclosures` §Corrections · footer nav on all 4 pages · 404 nav.
**Links out (8, MEASURED):** `/` ×2, `/disclosures`, repo root, 3 GitHub deep links, plus wordmark home.

---

##### `/disclosures` — the accepted compliance page

| Field | Value |
|---|---|
| **File** | `site/disclosures.html` |
| **URL** | `https://bountycharts.com/disclosures` |
| **`<title>`** | `Disclosures — BountyCharts` |
| **Meta description** | `Affiliate links, analytics, what this site collects, conflicts of interest, and the limits of what BountyCharts publishes. Written before the first affiliate link, not after.` (170 chars) |
| **H1** | `Disclosures` |
| **Size** | MEASURED 10,460 B raw, **3,039 B brotli**, 73 elements, 630 visible words, 1 HTTP request |

Lede + a mono `Current as of 2026-08-16` stamp, then six sections.

**§1 Affiliate links** — "**This site currently contains no affiliate links.** There is exactly one outbound link on the landing page, to the public repository, and it earns nothing." Then the forward commitment: labelled at the point of the link *not only on this page*; commission never determines what is shown or in what order; this page names each programme when one is in use. Closes with: *"This disclosure exists before the first affiliate link rather than after it. That is the order the rules require, and it is also the only order in which a disclosure means anything."*

**§2 Analytics and what is collected** — "**No accounts. No cookies. No third-party scripts. No forms.**" Then the differentiator, which is *enforced rather than promised*: "There is no JavaScript on this site at all — not a tag manager, not a session recorder, not an A/B tool. That is enforced rather than promised: the content security policy blocks scripts from any other origin, and the build will not deploy if a page contains an executable script." Then edge-side aggregate measurement, no identifier, no cross-site profile; host request logs retained briefly.

⚠️ **MEASURED constraint on this paragraph.** I injected Cloudflare's standard Web Analytics beacon (`<script defer src="https://static.cloudflareinsights.com/beacon.min.js">`) into a scratch `index.html`: the gate **FAILS** (`external subresource would be blocked by CSP`) and the suite goes **FAILED (failures=4)** — on top of the CSP's own `script-src 'self'`. The JS-beacon form of analytics is blocked three independent ways. This paragraph is only accurate for edge/server-side measurement. Confirm which form is enabled before publishing it.

**§3 Positions and conflicts** — a `.note` headed **No position policy**: "BountyCharts does not hold, trade, or take positions in the cards, sealed product or sets it reports on, and does not accept payment for coverage, placement, or a favourable reading of any card, deck or product. This matters more here than on most sites. A tool that tells thousands of people what is about to move, run by someone holding the thing that is about to move, is not a tool — it is a position being exited. So the policy is written down first and the product is built inside it."

**[OWNER MUST CONFIRM]** — this is a statement of fact about the owner's conduct. It implements `docs/tcg-deep-dive-2026.md:146` ("a written no-position policy, enforced and disclosed, from day one"). Do not ship it without explicit assent; an unassented compliance claim is worse than an omitted one.

**§4 What this site does not do** — no buyout alerts, no price predictions, no investment advice, ever. Not financial advice; cards are not an investment product. As-is, no warranty, data goes stale, verify before spending. (This is the entire useful content of a `/terms`.)

**§5 Independence and trademarks** — the canonical home of the `index.html:339` disclaimer, extended with: *"No card images, card frames, logos or other publisher artwork are hosted or reproduced here."* This is the machine- and human-readable anchor for constraint 6 and should be the URL any brand-safety question is pointed at.

**§6 Corrections** — errors corrected in public, on the page, dated; conclusion-changing corrections noted rather than quietly edited. Links to `/method` and to GitHub Issues. **[OWNER DECISION]** if a `mailto:` contact is wanted instead of / alongside Issues — I did not put an email address on the page, and no address in this session is mine to publish.

**Links in:** footer nav on all 4 pages · 404 nav. Deliberately *not* linked from index body copy — a legal page in the footer is the convention, and the FTC-relevant disclosure is the at-the-link label promised in §1, not this page.

---

##### Navigation and the landmark consequence

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
  …existing disclaimer + © …
</footer>
```

**Landmark structure, MEASURED via DOM in Chromium (both `colorScheme: light` and `dark`):**

| Page | Before | After |
|---|---|---|
| `index.html` | `header`(banner), `main`, `div[role=img]`, `footer`(contentinfo) | `header`, `main`, `div[role=img]`, `footer`, **`nav[Site]`** |
| `method.html` | — | `header`, `main`, `footer`, `nav[Site]` |
| `disclosures.html` | — | `header`, `main`, `footer`, `nav[Site]` |
| `404.html` | `main` | `main`, **`nav[Site]`** |

Seven decisions, each load-bearing:

1. **`<nav>` inside `<footer>` is still a navigation landmark** — `nav` is a landmark wherever it sits. Nesting it in `contentinfo` is the honest signal: these are site-footer links, not primary navigation. A 4-page pre-launch site does not have primary navigation.
2. **`aria-label="Site"` is mandatory.** A bare `<nav>` announces as "navigation" with no discriminator. 18 bytes.
3. **Exactly one nav. Do not add a header nav.** Two navs need two distinct labels and give a screen-reader user two landmark stops for four links. It also puts a link row directly above the H1, which is the one thing the landing page's composition cannot afford.
4. **No skip link.** MEASURED: on `index.html` *zero* links precede `<main>` (the wordmark is a plain `<span>`); on the two new pages, exactly one. A skip link earns its place at roughly 5+ pre-main links. There is nothing to skip.
5. **`aria-current="page"` on the current entry**, styled `--ink-soft` + no underline. Not colour-only — the ARIA state carries it, and the current page is the one link that should not look clickable.
6. **The wordmark is a `<span>` on `/` and an `<a href="/">` on subpages.** Avoids a self-referential link inside `banner`.
7. **404 gets the nav but no `<footer>`.** It has no banner/contentinfo today; adding them to an error page is not worth ~300 B. The nav replaces the lone "Back to BountyCharts" link and turns a dead end into a map.

**In-body discovery beats a nav bar here.** The `index.html` Status section is retargeted so `/method` is reachable in context, not only from the bottom of the page.

**Cost to the landing page — MEASURED, this is the number that matters:**

| Metric | Before | After | Δ |
|---|---:|---:|---|
| HTTP requests | 1 | **1** | 0 |
| `performance.getEntriesByType('resource')` | `[]` | **`[]`** | 0 |
| raw bytes | 11,657 | 12,358 | +701 |
| **brotli q11 (production wire cost)** | **3,179** | **3,350** | **+171 B (+5.4%)** |
| elements | 76 | 88 | +12 |
| `loadEventEnd` | 48.7 ms | **46 ms** | −2.7 ms |
| visible words | 367 | 391 | +24 |
| failed requests / console messages | 0 / 0 | **0 / 0** | 0 |

171 compressed bytes buys the nav, the nav CSS, the rewritten Status section, and the token remediation. The whole site is 8 files / 39,802 B on disk, and the two new pages are separate navigations that cost a landing-page visitor nothing.

---

##### Gate compliance — proven, not asserted

**Both new pages carry every item in constraint 4** (verified by grep against the built files):

| Requirement | Source of truth | `method.html` | `disclosures.html` |
|---|---|---|---|
| literal `lang="en"` | `validate_site.py:31` | ✅ `:2` | ✅ `:2` |
| `<title>` | `validate_site.py:32` | ✅ `:6` | ✅ `:6` |
| `name="viewport"` | `validate_site.py:33` | ✅ `:5` | ✅ `:5` |
| CSS contains `prefers-color-scheme: dark` | `validate_site.py:44` | ✅ `:25` | ✅ `:25` |
| CSS contains `[data-theme="dark"]` | `validate_site.py:45` | ✅ `:32` | ✅ `:32` |
| `<main[\s>]` landmark | `tests/test_validate_site.py:299-306` | ✅ `:147` | ✅ `:141` |
| no executable `<script>` | `tests/test_validate_site.py:268-276` | ✅ zero `<script>` tags | ✅ zero |
| no external subresource | `validate_site.py:200-246` | ✅ (4 GitHub `<a href>` are navigation, not subresources — gate ignores anchor hrefs) | ✅ |
| balanced tags | `validate_site.py:68-93` | ✅ | ✅ |
| `<url>` count == `<lastmod>` count | `tests/test_validate_site.py:220-225` | ✅ 3 == 3 | |
| `lastmod` matches `^\d{4}-\d{2}-\d{2}$` (**date-only — a full ISO datetime FAILS**) | `tests/test_validate_site.py:213-218` | ✅ | |

`INDEX_ONLY_META` (canonical / description / og:title / ld+json) applies to `index.html` only (`validate_site.py:49-54`) — the new pages carry canonical, description and og:* anyway, and deliberately carry **no** JSON-LD, because any `<script>` block is a liability the gate does not require here.

**Actual command output, run against the 4-page scratch site:**

```
$ python3 scripts/validate_site.py
ok    method.html: tags balanced (12,830 bytes)
ok    method.html: lang attribute / title / viewport / dark theme / theme override
ok    disclosures.html: tags balanced (10,434 bytes)
ok    disclosures.html: lang attribute / title / viewport / dark theme / theme override
ok    sitemap.xml: valid XML
ok    sitemap.xml: canonical host
ok    404.html / disclosures.html / index.html / method.html: no external subresources

All checks passed.                                    ← exit 0, 40 ok lines, 0 failures (was 26 ok)

$ python3 -m unittest discover -s tests -v
Ran 24 tests in 0.694s

OK                                                    ← exit 0
```

**`sitemap.xml` additions** (append before `</urlset>`; note the shipped file has **no trailing newline** — an append must supply its own). Also bump the index `<lastmod>` at `:5` from `2026-08-08` to the deploy date, because `index.html` changes in the same commit.

```xml
  <url>
    <loc>https://bountycharts.com/method</loc>
    <lastmod>2026-08-16</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://bountycharts.com/disclosures</loc>
    <lastmod>2026-08-16</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
```

`robots.txt` needs no change — `Allow: /` already covers both. `_redirects` needs no change.

###### ⚠️ MEASURED: the gate is blind to subdirectories — keep new pages flat

`validate_site.py:126` and `:211` use `SITE.glob("*.html")`, which is **non-recursive**. I placed this at `site/nested/index.html`:

```html
<!doctype html><html><head><title>x</title></head><body>
<script src="https://evil.example.com/a.js"></script><div></body></html>
```

No `lang`, no viewport, no `<main>`, an unbalanced `<div>`, and an external script that the CSP would block at runtime. **The gate returned `All checks passed.` and exit 0.** The tests at `tests/test_validate_site.py:270` and `:300` use the same non-recursive glob and are equally blind.

This is why both new pages are **flat files at `site/*.html`**, not `site/method/index.html`. Directory-style URLs would be prettier and would have escaped every check in the repo. Companion fix (CNT-IA-08): change three `glob` calls to `rglob`.

---

##### Required companion edits

These are not optional garnish — the two new pages are wrong without them.

1. **Fix `docs/fact-check-ledger.md:88-91` to 17 / 5 / 10 / 6.** BLOCKER. `/method` publishes those counts and links to the ledger one click away.
2. **Rewrite `index.html:332`** — drop "a primary-source audit" (it is 36%) and put the real counts on the landing page.
3. **Token remediation across all four HTML files in one commit** — `--gold` `#9A6F1E`→`#966C1D`, `--gold-bright` `#C9973F`→`#926D2E`, `--ink-faint` `#8A93A1`→`#6D747F` (light); `--ink-faint` `#6B7482`→`#838C9A` (dark). Every `<h2>` and every nav link is `--gold`; adding 2 pages and a nav multiplies the existing AA failure across the whole site otherwise.
   MEASURED via WCAG formula and confirmed by Chromium computed-style readback (`h2` renders `rgb(150,108,29)` light / `rgb(217,169,79)` dark): `#966C1D` = **4.506** on `--bg` / **4.709** on `--surface`; `#926D2E` = **4.517 / 4.720**; `#6D747F` = **4.511 / 4.714**. Dark `#838C9A` = **5.568 / 5.136**, which fixes the dark-theme `--ink-faint` failure the audit doc missed (shipped `#6B7482` is **4.004 / 3.693** — FAIL).
4. **Harden the gate glob** (`validate_site.py:126`, `:211`; `tests/test_validate_site.py:270`, `:300`).

---

##### Deferred, with an explicit trigger

**Do not extract shared CSS to `/assets/` yet.** The token block + doc styles are now duplicated across 4 pages (~2.4 KB raw each). Extraction would save ~7 KB on disk but adds a **render-blocking** request to the landing page, taking it from 1 request to 2 — trading the site's single best measured property for bytes that brotli mostly recovers anyway.

**Trigger to revisit:** 5+ HTML pages, or the shared block exceeding 40% of any page's bytes.

**When it happens, the filename MUST carry a content hash.** `site/_headers:11-12` sets `/assets/*` to `max-age=31536000, immutable` — one year, no revalidation even on reload. `/assets/site.css` is unbustable for 365 days; `/assets/site.a1b2c3d4.css` is the only correct spelling. Nothing in this lens's spec goes under `/assets/`, so no asset here needs a hash today — but this is the exact trap the next person to touch the CSS will walk into.

---

##### One pre-existing defect this lens inherits

**INFERRED, not verified against a live edge.** `site/_headers:15-16` scopes the HTML cache rule to `/*.html`. Cloudflare Pages serves the landing page at `/`, which does not match `/*.html` — so the `max-age=0, must-revalidate` rule almost certainly never applies to the landing page today, and will not apply to `/method` or `/disclosures` either. Like `/assets/*`, this looks like dead configuration. Not my lens's fix, but it is the reason the new pages' URL shape matters. Post-deploy check:

```bash
curl -sSI https://bountycharts.com/ | grep -i cache-control        # expect max-age=0, must-revalidate
curl -sSI https://bountycharts.com/method | grep -i cache-control
```

### 6.3 Metadata, social cards and structured data

#### Lens 5 — SEO, social and structured data

Everything below was verified by copying `site/`, `scripts/` and `tests/` to a scratch tree, applying the change, and running `python3 scripts/validate_site.py` (exit 0) plus `python3 -m unittest discover -s tests` (Ran 24 tests … OK). Byte figures are node `zlib` gzip‑9 / brotli‑11 on the exact proposed file. Character counts are `len(str)`; byte counts are `len(str.encode('utf-8'))` — they differ wherever `—` or `×` appears (3 bytes, 1 char).

---

##### What a search engine understands today, and what it should

**Today (MEASURED, `site/index.html:9-26` + DOM readback).** Google can resolve exactly three things: a site *name* (`og:site_name` + `WebSite.name` agree, which is what makes the SERP site‑name feature eligible), one indexable URL, and a 157‑character description it is free to rewrite. The JSON‑LD is a single 246‑byte `WebSite` node with 5 keys and no `@id`, so nothing can reference it. There is **no entity** — no `Organization`, no `logo`, no `sameAs`, no `inLanguage`, no date of any kind. There is no `og:image`, so every share surface (X, Slack, Discord, LinkedIn, iMessage) renders a text‑only unfurl. A crawler cannot tell that the site's subject is trading‑card secondary‑market pricing, cannot connect it to the GitHub repo it links at `index.html:333`, and — the one that actually matters — **cannot read the independence disclaimer**, because it exists only as rendered prose at `index.html:339`.

**What it should understand.** An `Organization` that is an independent project, publishing a source‑audited body of market claims, free to access, in English, whose sole public identity is the repo, and which is explicitly **not** affiliated with any card‑game publisher — the last one carried in `disambiguatingDescription`, which turns the footer disclaimer into machine‑readable brand safety at zero visible‑page cost. That is the single highest‑value structured‑data property available to this site and it costs 191 bytes.

---

##### The complete tag set — paste‑ready

Insert after `site/index.html:13` (`og:site_name`) and **change line 14 in the same commit**:

```html
<meta property="og:locale" content="en_US">
<meta property="og:image" content="https://bountycharts.com/assets/og-card.3f7a1c92.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="BountyCharts wordmark above a monospace grid of price and metagame readouts.">
<meta name="twitter:card" content="summary_large_image">
```

**Tags deliberately NOT added, with reasons:**

| Tag | Verdict | Why |
|---|---|---|
| `twitter:image` | **omit** | X falls back to `og:image` when `twitter:image` is absent. Saves ~90 B and removes a second URL to keep in sync with the content hash. |
| `twitter:image:alt` | **omit** | Same fallback chain reaches `og:image:alt`. |
| `twitter:title` / `twitter:description` | **omit** | X falls back to `og:title` / `og:description`, which are already correct. |
| `twitter:site` / `twitter:creator` | **cannot ship** | Requires an X account handle. **None exists in the repo. HUMAN INPUT REQUIRED — do not invent one.** |
| `og:image:secure_url` | **omit** | Legacy Facebook duplicate of `og:image` when the URL is already `https:`. |
| `og:locale` | **keep, marginal** | `en_US` is the OG default, so this is a no‑op for spec‑compliant consumers. 42 bytes to remove ambiguity for sloppy ones. Cut it if the budget is contested. |
| `<meta name="robots" content="max-image-preview:large">` | **omit** | Buys a large SERP/Discover thumbnail. There is no per‑page imagery to preview — the one image is a static brand card identical on every page, so a large preview shows the same thing on every result. |
| `rel="alternate" type="application/atom+xml"` | **defer** | Correct and cheap *once* `/feed.xml` exists (research §4 identifies Atom as the only CSP‑legal launch‑notification path). Blocked until the feed does. |

**`og:image` is invisible to the deploy gate — and that is correct.** MEASURED: `scripts/validate_site.py:217-241` scans `src=`, `srcset=`, `<link href>` with a fetching `rel`, and CSS `@import`. It never reads `content=`. An absolute `https://bountycharts.com/...` in an OG tag passes (verified: `ok index.html: no external subresources`). This is right, not a hole — the OG image is fetched by a crawler off‑page, so `img-src 'self'` never applies to it.

---

##### The `twitter:card` flip — why order is the whole thing

**`twitter:card="summary"` is correct today and must stay until the image file exists.** `summary_large_image` with no image renders a degraded or absent card on X.

The failure mode is the middle state. If `og:image` ships while `twitter:card` is still `summary`, X renders a **1:1 centre crop** of a 1200×630 card — it keeps x ∈ [285, 915] and discards 285 px from each edge, 47.5% of the width. A wordmark set flush‑left, or a figure in a right‑hand column, is simply gone.

**Therefore: `og:image` and the `summary_large_image` flip are one atomic commit.** Never two.

**Constraint handed to lens 1 (image file owner):** even at `summary_large_image`, narrow surfaces crop toward centre. Keep the wordmark and any load‑bearing figure inside a **centre‑safe 630×630 box** (x ∈ [285, 915], full height). Treat the outer 285 px on each side as bleed only.

**Format is a hard constraint, not a preference. SVG is not an option for `og:image`.** X's card crawler supports JPG, PNG, WEBP and GIF only; SVG fails silently. The obvious byte‑saving move — "the card is flat brand colours and monospace type, make it a 2 KB SVG" — is broken for social. It **is** available for `Organization.logo` (see §4).

---

##### Share copy, character‑counted

Limits below are the widely documented truncation points, graded **INFERRED** — Google truncates `<title>` by *pixel width* (~600 px), not characters, so the character figure is a proxy at typical glyph widths.

| Field | Limit | Proposed string | Chars | Bytes |
|---|---:|---|---:|---:|
| `<title>` | ≤60 | `BountyCharts — TCG price and metagame intelligence` | **50** | 52 |
| `og:title` | ≤60 (FB truncates ~88) | *identical to `<title>`* | **50** | 52 |
| `description` (current) | ≤155 | `What will this deck cost you next week? BountyCharts tracks the intersection of trading card prices and competitive metagame shifts, starting with Riftbound.` | **157** ⚠ | 157 |
| `description` **A** — ship now | ≤155 | `What will this deck cost you next week? BountyCharts tracks trading card prices against competitive metagame shifts, starting with Riftbound.` | **141** | 141 |
| `description` **B** — ship *after* `/method` | ≤155 | `Price and metagame intelligence for trading card games. We audited 38 market claims and corrected 10 of them. Riftbound first.` | **126** | 126 |
| `og:description` (current) | ≤160 | `What will this deck cost you next week? Price and metagame intelligence for trading card games, starting with Riftbound.` | **120** | 120 |
| `og:description` **B** | ≤160 | `We audited 38 market claims about trading card games and corrected 10 of them. Price and metagame intelligence, Riftbound first.` | **128** | 128 |
| `og:image:alt` | ≤120 (X caps 420) | `BountyCharts wordmark above a monospace grid of price and metagame readouts.` | **76** | 76 |

**The title does not need changing.** 50 chars, brand‑first, keyword‑bearing. Churning it buys nothing on a site with no index history.

**The description does.** Current is 157 — two over the desktop truncation point, so the trailing `Riftbound.` is the part at risk, and Riftbound is the differentiator. Variant **A** is a pure length fix with identical meaning; ship it unconditionally.

⚠️ **Blocker on variant B, and on the `/method` copy in §7.** Phase 1 established that `docs/fact-check-ledger.md:88-91` states 15/6/10/7 while the rows actually total **17/5/10/6**. A meta description is a machine‑readable assertion about a document. Publishing "38 audited, 10 corrected" is safe in either reading (10 is the one count both agree on). Publishing the full 17/5/10/6 breakdown is **not** shippable until the ledger scorecard is corrected — otherwise the site's own structured claim contradicts its own source document, which is precisely the failure the page exists to be the opposite of.

---

##### JSON‑LD: the graph worth having

Replace `site/index.html:18-26` entirely.

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
      "description": "An independent project tracking trading card prices against competitive metagame shifts, starting with Riftbound.",
      "disambiguatingDescription": "BountyCharts is an independent project. It is not affiliated with, endorsed by, or sponsored by Riot Games, The Pokemon Company, Bandai Namco, Wizards of the Coast, or any card game publisher.",
      "sameAs": ["https://github.com/kevynsgrin-a11y/BountyCharts"]
    }
  ]
}
</script>
```

**MEASURED:** `json.loads` on the block body succeeds; gate prints `ok index.html: JSON-LD parses`; gate exit 0; 24 tests OK; browser reads `ldTypes: [["WebSite","Organization"]]`, `ldParses: true`, 0 console messages. Block is 1,120 bytes (was 246).

Every value above is sourced from something already public: `name` and `slogan` from `index.html:262-263`, `disambiguatingDescription` verbatim from `index.html:339`, `sameAs` from the site's only outbound link at `index.html:333`. `isAccessibleForFree: true` is a fact about the site as it exists.

###### HUMAN INPUT REQUIRED — do not invent any of these

| Property | Status |
|---|---|
| `Organization.legalName` | Unknown whether a legal entity exists. |
| `Organization.foundingDate` | Not recorded anywhere in the repo. |
| `Organization.address`, `areaServed` | Unknown. |
| `Organization.founder` / `employee` / `author` | Git authorship exists but is **not consent to publish an identity** (research §4). A deliberate human decision, not a lookup. |
| `Organization.email` / `contactPoint` | MEASURED: grep for `mailto` across `site/` returns zero matches. None exists. |
| `Organization.logo` | No image file exists. See tier 2 below. |
| `sameAs` beyond the repo | No social profile exists. Note the repo URL in `sameAs` is a mild stretch — `sameAs` wants an identity page, and a repo is the project's canonical public presence rather than a profile. Defensible and widely done; the GitHub *account* URL would be a personal identity and is a human decision. |
| `twitter:site` / `twitter:creator` | No handle exists. |

###### Types considered and rejected

| Type | Verdict | Reasoning |
|---|---|---|
| **`potentialAction` / `SearchAction`** | **REJECT** | Google deprecated the sitelinks search box on 21 Nov 2024 and removed the documentation. There is also no search endpoint on this site, so the markup would describe a capability that does not exist. |
| **`FAQPage`** | **REJECT** | Google restricted FAQ rich results to authoritative government and health sites in Aug 2023 and deprecated them entirely in May 2026. Earns zero rich result, adds bytes, and creates a synchronisation liability (the markup must match visible copy or it is a guideline violation). |
| **`BreadcrumbList`** | **REJECT for now** | The site is flat: `/`, `/method`, `/disclosure`. A breadcrumb of `Home › Method` restates the URL. Revisit only if lens 4 introduces genuine nesting (`/research/<slug>`). |
| **`Dataset`** | **REJECT today, strongest future candidate** | `Dataset` is the right type for the 38‑claim ledger and is the single most differentiating structured‑data type available to this site. But an honest `Dataset` needs a `distribution` with a real `contentUrl` and `encodingFormat`, and no machine‑readable ledger exists — it is a markdown table in the repo. **Unblocks the moment lens 4 ships `/assets/ledger.<hash>.csv`.** See SEO‑12. |
| **`ClaimReview`** | **REJECT, flag for later** | Technically the *perfect* type — the ledger is literally a fact‑check with a rating per claim. Blocked twice: Google's ClaimReview rich result requires approved fact‑check‑publisher eligibility, and `ClaimReview` requires `itemReviewed.author` — i.e. naming who made each claim. Research §0 establishes **no claim→source mapping exists in the repo**. Attractive, unshippable, and legally sharper than it looks. |
| **`Project`** (subtype of `Organization`) | **REJECT** | More semantically honest for a one‑person project, but Google consumes `Organization` for logo and knowledge‑panel handling and does not consume `Project`. `"@type": ["Organization","Project"]` would also break a test — see §6. Plain `Organization` with `description` opening "An independent project" carries the nuance. |
| **`WebPage`** | **ACCEPT, per‑page only** | One `WebPage` node per new page, `isPartOf` → `#website`, `publisher` → `#organization`. See §7. |

###### Tier 2 — when lens 1 delivers a logo file

Append to the `Organization` node:

```json
      "logo": "https://bountycharts.com/assets/logo.7c4e2b10.svg",
```

**Google supports SVG for `logo` structured data** — unlike `og:image`, which cannot be SVG. That is a real asymmetry worth exploiting: the `◈` mark plus wordmark as a flat SVG lands under 2 KB against a 25 KB PNG, is same‑origin (CSP `img-src 'self'` satisfied), and is crawler‑fetched only. Google's guidance is that the logo must read on an all‑white background — the light‑theme `--ink #14181E` on white is 17.81:1, so a single‑colour ink mark is the safe choice; **do not use `--gold #9A6F1E`, which is 4.50:1 on white and fails by rounding.**

If no logo file ships, **omit `logo` entirely — do not point it at the og‑card.** A 1200×630 share card is not a logo, and mislabelling it produces a wrong knowledge‑panel image that is then cached.

---

##### Two gate/test traps I measured — both would ship a bug

**Trap 1 — the gate does not validate JSON‑LD outside `index.html`.** MEASURED: I injected `"@type": "WebPage",,` into `method.html` and syntactically broken JSON into `index.html` simultaneously. The gate reported **one** failure, the index one. `check_index_meta()` (`scripts/validate_site.py:159-169`) reads `index.html` only. **Any JSON‑LD on a new page is unvalidated by CI.** Either run `json.loads` on new pages by hand before every commit, or extend the gate. This is the cheapest real hardening available on this file.

**Trap 2 — the JSON‑LD must not be minified, and `"@type"` must stay pretty‑printed.** `tests/test_validate_site.py:95-101` mutates `index.html` by string‑replacing the literal `'"@type": "WebSite",'` and asserts the gate then exits 1. MEASURED: minifying the graph to `{"@type":"WebSite",...}` (964 B, saving ~150 raw bytes) makes that substring absent, the mutation a no‑op, and the test **fails** — `AssertionError: 0 != 1`. Same failure if `@type` is moved to be the last key in the `WebSite` object (no trailing comma) or changed to an array (`"@type": ["WebSite","CollectionPage"]`).

> **Rule: the JSON‑LD must contain the exact substring `"@type": "WebSite",` — one space after the colon, trailing comma, single string value.** Do not minify. The ~150 bytes are the price of the test that guards the block.

MEASURED corollary: writing the tag as `<script type='application/ld+json'>` (single quotes) makes the gate skip JSON validation entirely — gate exits 0 on broken JSON — but the test suite catches it. Use double quotes.

**Correction to Phase 1:** `site/sitemap.xml` **does** end with a trailing newline (last 12 bytes `b'>\n</urlset>\n'`, 267 bytes total). Phase 1 §8 states it does not. An append does not need to add its own leading newline.

---

##### Per‑page metadata for lens 4's pages

**URL form is decided by the host, not by us. Cloudflare Pages 308‑redirects `/method.html` → `/method` by default and this cannot currently be disabled.** Therefore `canonical`, `og:url` and the sitemap `<loc>` must **all** use the extensionless form while the file on disk keeps `.html`. Getting this wrong splits every URL in two. Note the local dev server does not do this — `http://127.0.0.1:8899/method` will 404 locally while `/method.html` works. That is expected, not a bug.

Head block for any new page (`method` shown; substitute slug, title, descriptions):

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Method — how BountyCharts grades a claim</title>
<meta name="description" content="…">
<link rel="canonical" href="https://bountycharts.com/method">
<meta property="og:type" content="website">
<meta property="og:url" content="https://bountycharts.com/method">
<meta property="og:title" content="Method — how BountyCharts grades a claim">
<meta property="og:description" content="…">
<meta property="og:site_name" content="BountyCharts">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="https://bountycharts.com/assets/og-card.3f7a1c92.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="BountyCharts wordmark above a monospace grid of price and metagame readouts.">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0E1116" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#FAFAF8" media="(prefers-color-scheme: light)">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>📈</text></svg>">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "https://bountycharts.com/method#webpage",
  "url": "https://bountycharts.com/method",
  "name": "Method — how BountyCharts grades a claim",
  "description": "Every market claim we publish is graded against a primary source.",
  "inLanguage": "en",
  "isPartOf": { "@id": "https://bountycharts.com/#website" },
  "publisher": { "@id": "https://bountycharts.com/#organization" },
  "dateModified": "2026-08-16"
}
</script>
```

Copy, character‑counted:

| Page | Field | String | Chars |
|---|---|---|---:|
| `/method` | `<title>` / `og:title` | `Method — how BountyCharts grades a claim` | **40** |
| `/method` | `description` | `Every market claim we publish is graded against a primary source. 38 claims checked: 17 confirmed, 5 overstated, 10 materially wrong, 6 unsubstantiated.` | **152** |
| `/method` | `og:description` | `38 claims checked against primary sources: 17 confirmed, 5 overstated, 10 materially wrong, 6 unsubstantiated. Here is the grading key.` | **135** |
| `/disclosure` | `<title>` / `og:title` | `Disclosure — affiliate links and analytics` | **42** |
| `/disclosure` | `description` | `How BountyCharts makes money, what it measures about you, and what it will never do. No buyout alerts, no price predictions, no investment advice.` | **146** |
| `/disclosure` | `og:description` | `How BountyCharts makes money, what it measures about you, and what it will never do.` | **83** |

The `/method` strings carrying **17/5/10/6** are blocked on the ledger scorecard fix (§4). If it is not fixed before ship, use `38 claims checked against primary sources. 10 of them were materially wrong.` (78 chars) — every count in that sentence is agreed by both the rows and the scorecard.

`dateModified` and the sitemap `<lastmod>` must be updated **in the same commit** as any content change. A stale date is worse than no date: it tells a crawler nothing changed while the page says otherwise.

**`site/404.html` — explicit no‑change.** It carries `robots noindex` at `:7`. Every indexable‑surface tag (`canonical`, `description`, the whole OG block, JSON‑LD) is dead weight on a page that must never be indexed, and a `canonical` on a 404 is an active bug. Its 11‑tag drift from index (Phase 1 §3) is **correct by design, not debt.** Leave it. Do not add it to the sitemap.

---

##### robots.txt and sitemap.xml

**robots.txt: ship byte‑identical. No change.** `User-agent: * / Allow: / ` already covers every new page. Three traps:

1. **Never add `Disallow: /assets/`.** Facebook's and X's card crawlers respect robots.txt, and Google respects it when fetching `Organization.logo`. Blocking the asset directory — a near‑universal robots.txt boilerplate move — silently kills the share card and the logo rich result with no error anywhere.
2. **Never `Disallow: /404.html`.** Disallowing prevents crawling, which prevents the crawler ever seeing the `noindex`. The current allow‑all plus on‑page `noindex` is the correct combination.
3. The current file allows GPTBot, ClaudeBot, CCBot and every other AI crawler by omission. For a site whose entire value proposition is being *cited* as a source of audited claims, that is the right default — but it should be a decision on the record, not an accident.

**sitemap.xml: replace the whole file.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bountycharts.com/</loc>
    <lastmod>2026-08-16</lastmod>
  </url>
  <url>
    <loc>https://bountycharts.com/method</loc>
    <lastmod>2026-08-16</lastmod>
  </url>
  <url>
    <loc>https://bountycharts.com/disclosure</loc>
    <lastmod>2026-08-16</lastmod>
  </url>
</urlset>
```

- `<lastmod>` **must be date‑only.** `tests/test_validate_site.py:213-218` asserts `^\d{4}-\d{2}-\d{2}$`, which is stricter than sitemaps.org — a full `2026-08-16T12:00:00Z` datetime is legal XML, legal sitemap, and **fails the suite**.
- Every `<url>` needs its own `<lastmod>`; `tests:220-225` compares the two counts.
- `<loc>` uses the **extensionless** form to match `canonical` and `og:url` (§7).
- `changefreq` and `priority` dropped: Google has stated it ignores both, and Bing ignores `priority`. MEASURED consequence — three URLs cost *fewer* compressed bytes than today's one: **402 B raw / 155 B brotli**, versus 267 B raw / **166 B** brotli at HEAD.
- 404 stays out.

---

##### Measured cost

| Build | raw | gzip‑9 | brotli‑11 |
|---|---:|---:|---:|
| `index.html` at HEAD | 11,657 | 4,025 | **3,179** |
| **+ JSON‑LD `@graph`** (tier 1) | 12,531 | 4,193 | **3,324** |
| **+ full OG image tag set** (tier 2) | 12,943 | 4,301 | **3,417** |

- Tier 1 costs **+874 B raw / +145 B brotli** = **+4.6%** of the compressed landing page.
- Tier 2 adds **+412 B raw / +93 B brotli**; combined **+1,286 B raw / +238 B brotli = +7.5%**.
- Browser, MEASURED against the probe build: **1 request** (unchanged), `resources: []` (unchanged), **0 console messages**, `loadEventEnd` 22 ms → 23 ms, DOM **76 → 82 elements** (+6 `<meta>`). The JSON‑LD is not evaluated as script — `tests/test_validate_site.py:239-247` documents that serving the page under `script-src 'none'` produced zero violations with the JSON‑LD still parseable.
- **The og‑card PNG costs the visitor zero.** It is never fetched by a browser rendering the page — only by a crawler, off‑page, after a share. The 25 KB image is 8× the compressed landing page and adds **0 bytes and 0 requests** to page load. This is the one place on the site where a large asset is genuinely free, and it is the reason the budget argument in constraint 5 does not bite here.
- Metadata‑only page skeleton (head + `<main>`, before lens 4 adds content): 2,590 B raw / **731 B brotli**. A new page is a separate navigation and costs the landing page nothing.

---

##### Ship order

1. **Now, no dependencies:** JSON‑LD `@graph` (SEO‑02) + description variant A (SEO‑03) + sitemap rewrite (SEO‑07). +145 B brotli, gate green, 24 tests green.
2. **Blocked on lens 1's PNG:** the OG image block and the `twitter:card` flip, as **one commit** (SEO‑01, SEO‑04, SEO‑05).
3. **Blocked on lens 4's pages:** per‑page heads (SEO‑09, SEO‑10) landing in the same commit as their sitemap entries.
4. **Blocked on the ledger scorecard fix:** description variant B and the 17/5/10/6 strings.
5. **Blocked on a real machine‑readable ledger:** the `Dataset` node (SEO‑12).

---

## 7. Insertion mechanics

### 7.1 The one-year cache trap, and a proven check

`/assets/*` is `max-age=31536000, immutable`. Ship `/assets/og-card.png`, and every crawler and CDN
that fetched it holds that exact bytes for a year. There is no build step to generate hashes, so
the convention has to be enforced by the gate.

**Convention:** every file under `site/assets/` is named `<name>.<hash8>.<ext>`, where `<hash8>` is
the first 8 hex characters of the SHA-256 of the file's own bytes.

The check below was **run against five cases** and behaves correctly in all of them:

| Case | Result |
|---|---|
| No `assets/` directory (today's state) | passes — nothing to check |
| `assets/og-card.png` — unfingerprinted | **FAILS**: `not fingerprinted (needs <name>.<hash>.<ext>)` |
| `assets/og-card.86610c40.png` — correct | passes |
| Same file edited, filename hash left stale | **FAILS**: `hash 86610c40 does not match content (c9dfd3a8)` |
| Real 52,923 B render, correctly named | passes |

Case 4 is the one that matters: it is the failure mode that silently poisons a cache for twelve
months, and no other check in the repo would catch it.

```python
# scripts/validate_site.py — add alongside the existing checks
import hashlib, re

FINGERPRINTED = re.compile(r"^(?P<stem>.+)\.(?P<hash>[0-9a-f]{8,})\.(?P<ext>[a-z0-9]+)$")

def check_asset_fingerprints() -> None:
    """/assets/* is served immutable for a year (site/_headers:11-12) and there
    is no build step, so the filename is the only cache-buster there is."""
    assets = SITE / "assets"
    if not assets.is_dir():
        ok("no assets/ directory — nothing to fingerprint")
        return
    for f in sorted(p for p in assets.rglob("*") if p.is_file()):
        rel = f.relative_to(SITE)
        m = FINGERPRINTED.match(f.name)
        if not m:
            fail(f"{rel}: not fingerprinted — /assets/* is immutable for a year, "
                 f"so the filename must be <name>.<hash>.<ext>")
            continue
        actual = hashlib.sha256(f.read_bytes()).hexdigest()[:len(m.group("hash"))]
        if actual != m.group("hash"):
            fail(f"{rel}: filename hash {m.group('hash')} does not match its "
                 f"contents ({actual}) — the cache will serve the old bytes for a year")
        else:
            ok(f"{rel}: fingerprint matches ({f.stat().st_size:,} B)")
```

A helper to name a file correctly, so nobody computes a hash by hand:

```bash
# usage: fingerprint site/assets/og-card.png  ->  site/assets/og-card.7293c1d5.png
fingerprint() {
  f="$1"; h=$(sha256sum "$f" | cut -c1-8)
  base="${f%.*}"; ext="${f##*.}"
  mv "$f" "${base}.${h}.${ext}" && echo "${base}.${h}.${ext}"
}
```

### 7.2 Alt text for every proposed image

Alt text is a decision per asset, not a field to fill. **Decorative assets must take `alt=""`** —
a decorative image with descriptive alt text is worse than no image, because it injects noise into
the accessible name of whatever contains it.

| Asset | Alt | Reasoning |
|---|---|---|
| `og:image` social card | `og:image:alt` = *"BountyCharts — price and metagame intelligence for trading card games. Sample figures, not live prices."* | Never rendered on the page; this string is read by screen readers on the **unfurled card** in Slack/X. It must carry the sample disclaimer, because the card shows four figures that are invented. |
| favicon / `apple-touch-icon` | n/a | Browser chrome. No alt concept. |
| Brand mark, if used inline beside the wordmark | `alt=""` (or `aria-hidden="true"` on inline SVG) | The adjacent text already says "BountyCharts". Describing the mark would make a screen reader announce the brand twice. |
| Any in-page diagram on `/method` | Descriptive alt **plus** the same information in adjacent prose | A diagram that is the only carrier of its information fails WCAG 1.1.1 for anyone who cannot see it, and the prose is cheaper than the image anyway. |

### 7.3 Budget ledger

Measured baseline and projected cost. The distinction that decides everything: **bytes the visitor
pays versus bytes only a crawler pays.**

| Item | Disk | Visitor bytes (first visit) | Requests added | Notes |
|---|---:|---:|---:|---|
| **Baseline today** | 15,181 | **3,179** (brotli) | 1 | measured |
| `og:image` PNG-8 | ~20,000 | **0** | **0** | crawler-only; never fetched by the page |
| Brand mark, inline SVG in `<head>`/body | 0 | ~250–360 raw (≈ +90 brotli) | **0** | inlining keeps the request count at 1 |
| `favicon.ico` at root | ~1,100 | 0–1,100 | 0–1 | fetched by the browser opportunistically, not render-blocking |
| `apple-touch-icon` 180×180 | 3,562 | **0** | **0** | fetched only on add-to-home-screen |
| **Projected total** | **~40,000** | **≈ 3,270** | **1** | visitor cost rises by roughly **90 bytes** |

**Hard ceiling: the landing page stays at 1 request and under 5,000 bytes brotli.** If a proposal
breaks either, it needs a written justification, not a judgement call.

**What to cut first, in order:** the 2× og:image variant (measured 109,224 B PNG-32 for a
resolution no major unfurl surface renders); then any in-page imagery; then the full raster icon
set. Measured: a complete 16/32/48/180/192/512 PNG icon set is **17,996 B — larger than the entire
current site**, whereas one SVG is **358 B**.

### 7.4 The favicon needs two artworks, not one

**MEASURED.** The detailed mark — a stroked lozenge containing a step plot — is legible at 48 px
and above, and turns to mud at 16–32 px. Rendered side by side at true size, the stroked interior
closes up entirely at 16 px.

| Variant | Minified SVG | Reads at 16 px? |
|---|---:|---|
| Detailed (stroked lozenge + step plot) | 358 B | **no** |
| Simplified (solid lozenge, knocked-out notch) | **245 B** | **yes** |

Ship both: the simplified artwork for `favicon.ico` (16/32) and the detailed one for 180 px and up.
Specifying a single SVG for all sizes is the mistake this measurement exists to prevent.

### 7.5 New gate checks so none of this rots

Beyond the fingerprint check, four assertions worth adding — each catches a failure that would
otherwise reach production silently:

```python
def test_og_image_points_at_a_file_that_exists(self): ...   # a 404 og:image unfurls as a blank card
def test_every_img_has_an_alt_attribute(self): ...          # missing alt is a WCAG 1.1.1 failure
def test_no_asset_exceeds_its_budget(self): ...             # keeps the 1-request/5 KB ceiling honest
def test_og_image_alt_mentions_the_sample_disclaimer(self): # the card shows invented figures
```

The last one is not pedantry. The card displays `+18.4%`, `−9.1%`, `11.2%` and `Elevated`. Those
figures are invented, and an unfurled card carries them into Slack and X **stripped of the page's
`sample` badges**. The alt string is the only disclosure that travels with it.

### 7.6 Sequencing

1. **Fingerprint check first.** It must exist before the first file lands under `/assets/`, or the
   convention is already broken.
2. **Contrast remediation before any artwork.** Section 3's prompts bake brand hex values into
   pixels. Generating a card with `--gold #9A6F1E` and *then* changing the token to `#966C1D`
   means regenerating every asset. Settle the palette first.
3. **`og:image` + tags together.** An `og:image` tag pointing at a missing file is worse than no
   tag: it unfurls as a broken card rather than a text card.
4. **Favicon set** — independent, parallel-safe.
5. **`/method` and `/disclosures`** — independent of all imagery.
6. **`twitter:card` flips to `summary_large_image` only after the image is live.** Flipping first
   produces a broken large card. Order is the whole thing.

---
## 8. Source research available to surface

though# Research → Site: what should actually be on the page

All counts re-derived from the files, not from the docs' own summaries. Grades: **MEASURED** (I ran it / counted it), **OBSERVED** (read directly in the file), **INFERRED** (my judgment).

---

### Document inventory — precise counts

**MEASURED** (`LC_ALL=C.UTF-8 wc -w`; the default C locale under-counts by merging multibyte em-dashes — a bare `wc -w` reports 3357 for the deep dive, which is wrong):

| File | Words | Lines | Bytes | External URLs |
|---|---|---|---|---|
| `docs/tcg-deep-dive-2026.md` | **3,448** | 270 | 25,035 | **33** |
| `docs/fact-check-ledger.md` | **1,711** | 95 | 10,296 | **0** |
| `models/unit_economics.py` | **901** | 185 | 8,090 | 0 |
| `README.md` | **408** | 38 | 3,080 | 0 |
| *(context)* `prompts/agency-handoff-prompt.md` | **33,528** | 3,791 | **252,740** | — |

The ledger — the document with the strongest claim to being source-backed — contains **zero URLs**. All 33 citations live only in the deep dive's `## Sources` block (`docs/tcg-deep-dive-2026.md:254-268`), grouped into 8 topic clusters, spanning **29 distinct hosts**. **There is no claim→source mapping anywhere in the repo.** Publishing any ledger row on the site requires building that mapping first; it does not exist.

Source quality breakdown of those 33 (**INFERRED** classification, **MEASURED** hosts):
- **12 primary** (36%): Bandai IR, Asmodee year-end PDF, Equinox's own closure statement, `docs.tcgplayer.com` ×2, `help.tcgplayer.com`, `seller.tcgplayer.com`, Piltover Archive (Riot's own), TPCi Media Usage Guidelines, pokemon.com/legal, EDHREC Patreon, Moxfield Patreon
- 1 data vendor (Sensor Tower), 14 trade press, 3 market-research marketing pages, **3 low-authority SEO blogs** (`toolsignal.site`, `thisweekinblogging.com`, `tcgapi.dev`)

⚠️ **The two most load-bearing monetization numbers come from that last group.** The `$2–6 gaming RPM` (`docs/fact-check-ledger.md:78`) — which sets `ads_rpm_*` in `models/unit_economics.py:55-57` and therefore every revenue figure in the deep dive — is sourced to `toolsignal.site/articles/blog-display-ad-rpm-by-niche-2026`. The ad-network thresholds (`ledger:77`) come from `thisweekinblogging.com`. The deep dive's central criticism is that the source report's load-bearing numbers are unsourced; its own RPM input is sourced to an SEO blog. **Do not put "$2–6 RPM" on the site as a hard fact.**

---

### DEFECT: the ledger's own scorecard contradicts its own rows

**MEASURED.** Extracting column 3 (the Status column) from all 38 claim rows via awk:

| Status | Rows actually marked | Scorecard `fact-check-ledger.md:88-91` says |
|---|---|---|
| ✅ Confirmed | **17** | 15 |
| 🟡 Partly true / overstated | **5** | 6 |
| ⚠️ Materially wrong | **10** | 10 ✓ |
| ❓ Unsubstantiated | **6** | 7 |
| **Total** | **38** | 38 ✓ |

Three of four counts are wrong. Totals agree, so the error is invisible unless you count. `README.md:10` ("38 claims") is correct.

**This is a blocker.** The single most publishable asset here is a scorecard — and the scorecard is the one number a visitor can trivially check by counting the table. Shipping "15 confirmed" while the rows show 17 destroys the exact credibility the page exists to establish. Fix the ledger first, then publish **17 / 5 / 10 / 6**. Only one commit touches this file (`b6d775a`), so the mismatch has been there since creation.

---

### The 15 strongest surfaceable facts

Ranked by (specific × defensible × surprising). Each graded **SAFE** / **RISK** for a public marketing page.

#### ✅ SAFE — publish

**F1. Riftbound launch metrics — the single best number set in the corpus.**
> "300% surge in daily TCGplayer searches; 6,300 searches/hour … Confirmed — measured against the ~2-week preorder window. Listings also rose from ~68,600 (30 Oct) to ~118,100 (31 Oct)." — `docs/fact-check-ledger.md:46`
> "Kai'Sa Signature peak $2,356 | ✅ | Confirmed as the most expensive Origins card." — `docs/fact-check-ledger.md:47`

Four concrete, dated, confirmed figures about the exact game the site leads with. The **68,600 → 118,100 listings in 24 hours** is the most viscerally "instrumentation" number in the whole research and appears **nowhere** in the deep dive's prose — it exists only in the ledger. Ships clean: no publisher logo, no card art, no price prediction, just a measured count. **The site currently says "an active secondary market" (`site/index.html:319`) and cites nothing.**

**F2. Pokémon TCG Pocket has structurally zero affiliate surface.**
> "**Affiliate revenue from Pocket traffic is structurally zero.** The cards are digital-only. There is no secondary market, no TCGplayer listing, nothing to buy. Pillar 2 — the entire affiliate apparatus — earns **$0** on the report's own highest-priority audience." — `docs/tcg-deep-dive-2026.md:62`

The flagship insight. Encoded as a real model parameter at `models/unit_economics.py:38-42` and `:60`. Safe: it's a statement about market structure, not about anyone's conduct.

**F3. TCGplayer affiliate is 48-hour, FIRST-click — and most directories say otherwise.**
> "TCGplayer affiliate: 3.5%, 48-hour window, **first-click** attribution | ✅ | **Confirmed against TCGplayer's own documentation.** Worth flagging because most third-party affiliate aggregators incorrectly list this program as last-click." — `docs/fact-check-ledger.md:74`

Primary-sourced (`docs.tcgplayer.com`). Genuinely non-obvious and checkable. **Mild risk:** "the aggregators are wrong" asserts error by unnamed third parties. Ship as "confirmed against TCGplayer's own documentation — several affiliate directories list it as last-click" and let the link do the work.

**F4. Altered's backers were made whole — a correction *against* the researcher's own interest.**
> "Omits a material fact: **all backers, players and retailers, are being reimbursed in full**, and Roots of Corruption was released digitally with 10 free uniques to active accounts. The 'orphaned, aggrieved audience' the attack strategy is built to capture was made financially whole." — `docs/fact-check-ledger.md:68`
> "€2.5 million required per set | ⚠️ | The figure is **€2 million**, per Equinox's own statement and every source the report itself cites." — `docs/fact-check-ledger.md:66`

**This is the most persuasive single item in the entire corpus.** It corrects a claim in a *failed competitor's favour* and in doing so destroys a growth channel the research would otherwise have benefited from (`docs/tcg-deep-dive-2026.md:165`: "removes the grievance the acquisition thesis depends on"). Primary-sourced to `altered.gg`. Nothing else on the page can buy this much trust in two sentences.

**F5. Market-size forecasts disagree by 54% between firms.**
> "Analyst 2034–2035 forecasts span **$15.8B to $24.4B** — a 54% spread between firms. That dispersion signals low measurement confidence, not consolidation. Any number in this category should be treated as a marketing artifact, not an input to planning." — `docs/fact-check-ledger.md:14`

The best "we are not like the other analytics sites" proof point available, and it costs nothing legally — it names an industry-wide dispersion, not a wrongdoer. Pairs with the year-shift correction: CMI puts **$13.01B in 2025 / $14.12B in 2026**, not 2024/2025 (`ledger:13`).

**F6. The buyout-alert product is mathematically self-defeating.**
> "**It is self-defeating at scale.** Publishing a buy signal to N subscribers *is* the demand event. Early subscribers profit; later ones become exit liquidity for earlier ones. The product's value **decreases monotonically with subscriber count** — the opposite of the scaling property a subscription business needs." — `docs/tcg-deep-dive-2026.md:145`

Already partly on the page (`site/index.html:326`) — and it is the page's strongest paragraph. The research has two more supporting legs the site omits: the front-running exposure requiring "a written no-position policy, enforced and disclosed, from day one" (`:146`), and that FTC endorsement/deceptive-practice rules apply even though "trading cards are not securities" (`:147`).

**F7. Mass Entry is a real no-API deck-to-cart path — and it is table stakes, not a moat.**
> "TCGplayer supports **Mass Entry** — a URL-encoded quantity-and-name payload that opens a pre-filled cart without any API key, and which accepts an affiliate parameter… It is also available to every competitor equally, so it is a table-stakes feature, **not a moat**." — `docs/tcg-deep-dive-2026.md:52`

Concrete, verifiable, and the self-denying framing ("not a moat") is on-brand.

**F8. Model output: revenue per 1,000 sessions is flat across three orders of magnitude.**
> "Revenue per 1,000 sessions is essentially flat at ~$12.72 across three orders of magnitude — the rate levers barely move it." — `docs/tcg-deep-dive-2026.md:236`

**MEASURED — I ran the model; every figure in `docs/tcg-deep-dive-2026.md:216-219` reproduces exactly:** $306 / $1,272 / $6,361 / $25,445 at 25K / 100K / 500K / 2M sessions; $12.22 then $12.72 flat. Subscription share = 610/1272 = **47.96%** (doc says "~48%", `:237` ✓). LTV $38.35 → **9,588 ad sessions per subscriber** (doc says "roughly 9,600" ✓).

**SAFE only if framed as model output with the assumptions visible.** These are the most "act-on-able" numbers in the corpus. The mitigation is already built: the model is 8,090 bytes, stdlib-only, and takes CLI flags — "here is the model, change the assumption yourself" is a stronger claim than the number.

**F9. Both sensitivities reproduce — and each isolates one error.**
**MEASURED:** `--first-click-win-rate 1.0 --sessions 100000` → affiliate **$655** vs baseline $262 = **2.50×** inflation (doc says "2.5×", `:238` ✓). `--digital-share 0.8 --sessions 100000` → affiliate **$87** = **−66.8%**, rev/1K falls $12.72 → **$10.98** = **−13.7%** (doc says "−67%" and "~14% haircut", `:227`, `:239` ✓).
> "**Pursuing the report's own #1 priority makes the business worse.**" — `docs/tcg-deep-dive-2026.md:239`

**F10. Riot ships its own competing tool; 8+ tools existed within 9 months.**
> "**Piltover Archive — Riot's own official** database, deck builder, hand simulator and tournament decks; riftbound.one; riftmana.com; riftdecks.com; riftbound.gg; riftools.app; Mobalytics; TCGFan" — `docs/tcg-deep-dive-2026.md:85`
> "it accumulated **eight or more competing tools within nine months**, one of which is built and promoted by the publisher." — `:91`

**MEASURED: the row lists exactly 8.** Neutral factual statement of existence — low risk. Powerful because it justifies the site's actual product decision (`:179`): "Do **not** build a general deck builder… Build the thing none of them do well… **'what will this deck cost me next week, and what is about to move.'**" That sentence is the origin of the site's own H1 (`site/index.html:269`) and the page never says where it came from.

**F11. Riot's fan-content policy is permissive; the site asserts this and cites nothing.**
> "**Riot Games is at the opposite end.** Its published fan-content policy is permissive and explicitly contemplates community projects." — `docs/tcg-deep-dive-2026.md:126`

`site/index.html:319` already claims "a permissive fan-content policy" with zero support. This is the cheapest credibility fix on the page: one link.

**F12. The KYC detail.**
> "The KYC detail (identity verification triggered at €2,000 cumulative sales) is a genuinely non-obvious finding." — `docs/tcg-deep-dive-2026.md:30`

Small, specific, memorable, about a shut-down product. Low risk, high "they actually read the fine print" signal.

#### ⚠️ RISK — repo only, or heavily hedged

**F13. TCGplayer's API is closed to new developers.** — `docs/tcg-deep-dive-2026.md:48`, `ledger:76`
> "TCGplayer **stopped accepting new public API applications around late 2024**, following the eBay acquisition. As of mid-2026 the developer application path is effectively closed — **applications go unanswered** — and a Partner API deprecation is documented."

**RISK: asserts a named company's internal business conduct, partly from absence of evidence.** "Applications go unanswered" is unfalsifiable-by-construction and reads as an accusation of bad faith. The *documented* half (a published Partner API deprecation page) is safe and links to `docs.tcgplayer.com`. **Publish only:** "TCGplayer documents a Partner API deprecation → [link]." Drop the eBay causation and the unanswered-applications claim from any public page. Note TCGplayer is also the site's intended affiliate partner (`:187`) — publicly characterising them as stonewalling developers is commercially as well as legally unwise.

**F14. The Pokémon licence is non-commercial and enforcement triggers on funding.** — `docs/tcg-deep-dive-2026.md:122-124`
> "licensees are not authorized to commercialize content, 'including by selling it or charging a fee for access to it.'"
> "TPC's former chief legal officer described the practice as waiting **'to see if they get funded'** before engaging. Enforcement is *triggered by monetization*."

**HIGHEST RISK ITEM IN THE CORPUS. Keep off the site entirely.** The first sentence is a fair quote from a public guideline. The second characterises a named company's *enforcement strategy* via a former officer's remark, on a commercial page carrying a disclaimer that explicitly names The Pokémon Company (`site/index.html:339`). It is also self-incriminating in the wrong direction: it announces awareness of the licence limit while planning Pokémon content (`:204`). This belongs in a repo analysis doc and nowhere else.

**F15. One Piece revenue and the Yu-Gi-Oh! comparison.** — `docs/fact-check-ledger.md:34-35`
> "The One Piece Card Game specifically was ~¥26.5B (**~$170M**) in Japan for FY2023–24. Bandai's *entire card-game segment* — all IPs — was ~**$1.99B** in FY2024, +18.1%."
> "One Piece outsold Yu-Gi-Oh! **on TCGplayer GMV, in October and November 2025** — a US marketplace measure. On global publisher revenue Yu-Gi-Oh! remained materially larger (¥47.1B vs ¥26.5B)."

**MEDIUM RISK.** Precise financial assertions about a named public company, partly derived from a secondary aggregator (`snkrdunk.com`, `sabatcg.com`) rather than the IR filing alone. The *methodological* point — "a US marketplace measure is not global publisher revenue" — is excellent, safe, and publishable **without the yen figures**. Same treatment for Asmodee (`ledger:57`: 72%+ distribution, own board-game sales fell, SWU "normalising") — the quoted characterisation of a named company's product performance is defensible against their own year-end report but is a company fact a marketing page has no need to assert.

**F16. Competitor pricing.** — `docs/fact-check-ledger.md:79`, `docs/tcg-deep-dive-2026.md:99-101`
> "EDHREC — the dominant MTG Commander data site — starts at **$2/mo**. Moxfield starts at **$1/mo**."

Factually public (Patreon pages, both cited). **Risk is staleness, not defamation** — a price table about live competitors rots and there is no mechanism on this site to re-verify it. If published, date-stamp it. The unflattering framing at `:101` ("Zero brand, zero traffic") targets *this project*, not the competitors, so it is safe and disarming.

---

### The through-line the landing page does not tell at all

**MEASURED baseline** (Playwright, `http://127.0.0.1:8899/`): 1 request, 11,657 B, **76 elements**, load 94 ms, **367 words of visible body text**, **1 outbound link**. The only numeric figures in the visible copy are `+18.4%`, `−9.1%`, `11.2%` — **all three are fabricated**, each carrying a `sample` badge (`site/index.html:158-169`, `274-293`).

**So: a site whose entire premise is measurement currently displays four made-up numbers and zero real ones — while sitting on 38 audited claims, 33 citations and a runnable model.**

The story is not "we did research." It is:

> **The numbers everyone repeats about this industry are wrong, and we checked all 38 of them.**
> 10 were materially wrong. 6 we could not substantiate — so we marked them unsourced instead of repeating them. One correction cost us a growth channel and we published it anyway.

That last clause (F4) is the whole thing. It converts an abstract claim of rigour into a demonstrated cost paid. Nothing else on a pre-launch TCG page can do that.

**The page already promises this and then doesn't deliver it.** `site/index.html:326`: *"This is decision support: what the data says, **and where it came from**."* The site provides zero provenance for anything. `site/index.html:332` calls the work *"a primary-source audit"* — **MEASURED: 12 of 33 sources (36%) are primary.** Defensible, but currently unsubstantiable by any visitor, because the source list is not on the site and the ledger has no inline links.

**Secondary through-line, nearly as strong:** the project publicly ran the numbers on *its own* business model and published why the obvious plan fails — including that the largest audience in the category (Pokémon TCG Pocket, 200M downloads) is worth **$0** to it and it is not chasing it (F2, F9). A pre-launch site that says "here is the biggest audience in our market and here is why we're walking past it" is making a credibility move no competitor makes. It also directly explains "Why Riftbound first," which the page currently asserts on vibes (`:319`).

---

### Content a reader needs that does not exist anywhere

**MEASURED** — grep across `site/` for `mailto|privacy|analytic|cookie|affiliate|verified|rss|atom|subscri|notify` returns **no matches** outside CSS at-rules and the JSON-LD `@context`.

| Gap | Evidence | Note |
|---|---|---|
| **Method / how a claim is graded** | Status key exists only at `fact-check-ledger.md:5`; "Method" only at `README.md:36-38` | The 4-symbol key is the product. Nowhere on the site. |
| **Sources** | 33 URLs at `tcg-deep-dive-2026.md:254-268`; **0** in the ledger | No claim→source mapping exists. Must be authored, not copied. |
| **Freshness date** | "Verified July 2026" (`ledger:5`), "Date: July 2026" (`deep-dive:4`) | Site's only date signal is "© 2026" (`index.html:340`). Research dated 13 months into a fast market with no stated re-check cadence. |
| **Who is behind this** | No byline/contact anywhere in repo or site | Git authorship exists but is not consent to publish an identity. Needs a deliberate decision, not a lookup. |
| **What happens at launch / how to hear about it** | Nothing | See constraint note below — this is CSP-constrained and has a real answer. |
| **Affiliate & analytics disclosure** | The research itself names FTC endorsement rules as in-scope (`deep-dive:147`); roadmap is "Affiliate first" (`:187`) | **The site plans to carry affiliate links and has no disclosure page.** This is a live compliance gap the research identified and the site ignores. |
| **Glossary** | "Spread" and "Reprint risk" appear as sample values with a 3-word gloss (`index.html:285-292`) | Undefined jargon in the hero region. |
| **What the outbound link lands on** | `index.html:333` → repo root; `README.md:12` front-page-links `prompts/agency-handoff-prompt.md` (**252,740 B, 33,528 words**) | A visitor clicking "Read the research" meets a README that advertises a 33.5k-word internal agent-orchestration prompt above the fold-adjacent table. **OBSERVED brand risk on the site's only outbound link.** |

**Launch-notification, within CSP** (`site/_headers:6` — `form-action 'self'`): a third-party capture endpoint (Mailchimp/ConvertKit/Buttondown) is **blocked**. Working options, in order: (a) `mailto:` link — navigation, not a form, so `form-action` does not apply; (b) a same-origin static **Atom feed** at `/feed.xml`; (c) "Watch → Releases" on the existing repo link. No JS is possible either way — `tests/test_validate_site.py:268-276` rejects any executable `<script>` on any page.

---

### Shipping constraints — verified, not assumed

**A second page passes the gate. MEASURED.** I copied `site/`, `scripts/`, `tests/` to a scratch dir, added a `method.html` (7,671 B, reusing the inline CSS, `<main>`, `lang="en"`, title, viewport, both theme selectors, no `<script>`), and added a sitemap `<url>` with `<lastmod>2026-08-16</lastmod>`:
- `python3 scripts/validate_site.py` → **exit 0, all checks passed**, including `method.html: no external subresources`
- `python3 -m unittest discover -s tests -v` → **Ran 24 tests … OK**

Note for whoever writes it: `unittest discover -s tests -t .` fails with `ImportError: Start directory is not importable` (no `__init__.py`). CI uses `-s tests -v` with no `-t` (`.github/workflows/deploy.yml`).

**Byte budget. MEASURED.** `index.html` = 11,657 B raw, **4,049 B gzip**. The 7,671 B probe page = **2,713 B gzip**. Total site today = **15,181 B**.
- A method/ledger page adds ~2.5–4 KB gzip **and is a separate navigation** — it costs the landing page nothing. Not render-blocking.
- **Do not extract CSS to `/assets/` yet.** The gate permits it (`scripts/validate_site.py:103-121` follows local `<link rel=stylesheet>`; `tests/test_validate_site.py:139` asserts it), but at 2 pages it trades 1 request for 2 on first paint to save ~2.7 KB. Revisit at 3+ pages.
- **If anything ever lands under `/assets/`, the filename MUST carry a content hash** — `site/_headers:11-12` sets `max-age=31536000, immutable`, so `/assets/site.css` is uncacheable-bustable for one year. `/assets/site.a1b2c3d4.css` is the only correct spelling. Same for any font, image, or og-card.

**Contrast — do not compound the known defect. MEASURED** (WCAG 2.x relative-luminance formula, computed not estimated):

| Token on `--bg` | LIGHT | DARK |
|---|---|---|
| `--ink` | 17.04 ✓ | 15.97 ✓ |
| `--ink-soft` | 5.98 ✓ | 7.34 ✓ |
| `--gold` | **4.31 ✗** | 8.77 ✓ |
| `--gold-bright` | **2.52 ✗** | 11.42 ✓ |
| `--ink-faint` | **2.97 ✗** | **4.00 ✗** |
| `--up` / `--down` | 5.11 / 5.64 ✓ | 8.31 / 6.47 ✓ |

**New finding beyond the brief: `--ink-faint` fails AA in the DARK theme too** — 4.00:1 on `--bg`, **3.69:1 on `--surface`** (which is where it actually renders, in `.cell .k` and the `sample` badge, `index.html:141-169`). The brief lists only the light-theme failures.

Consequences for the content proposed above:
- Every `<h2>` uses `--gold` on `--bg` (`index.html:173-181`) = 4.31 ✗. **Adding sections multiplies the existing failure.**
- Every stat *label* (`.cell .k`) uses `--ink-faint` on `--surface` = 3.10 light / 3.69 dark ✗. **Any new stat block reusing `.cell` inherits a two-theme failure — and stat labels are exactly what real numbers need.**
- **Set every real figure in `--ink` (17.04 / 15.97) or `--ink-soft` (5.98 / 7.34), never `--gold` or `--ink-faint`.** `--up`/`--down` clear AA in both themes and are safe for signed deltas.
- Remediation values in the brief check out: `--gold #966C1D` → **4.51**, `--gold-bright #926D2E` → **4.52**, `--ink-faint #6D747F` → **4.51** on `--bg`. All three clear on `--surface` too (4.71/4.72/4.71).

**Brand-safety read on the proposed content: clean.** Every fact above is a number, a date, a policy citation, or a market-structure statement. None requires card art, a frame, a set symbol, a mana pip, or a publisher wordmark. None reads as speculation: F6 and F2 are explicitly *anti*-upside, and F8/F9 are cost/ceiling figures, not returns. The one item to keep away from imagery entirely is the Kai'Sa $2,356 figure (F1) — publish it as a typeset number, never illustrated, or it becomes a picture of a card with a price on it.

---

### Recommended shape, in priority order

1. **Fix the scorecard** (`fact-check-ledger.md:88-91` → 17/5/10/6) before any of it is published. Non-negotiable.
2. **Replace three of the four fabricated ticker cells with F1's real Riftbound figures**, labelled and dated. Keep one `sample` cell for the forward-looking product concept. This is the highest-leverage change on the page: it converts the site's own thesis from asserted to demonstrated at roughly zero byte cost.
3. **Add one page — `/method`** carrying: the 4-symbol status key, the 17/5/10/6 scorecard, F4 (the correction against interest), F5 (the 54% forecast spread), the "verified July 2026" date with a re-check cadence, and the source list. Verified to pass gate + 24 tests at ~2.7 KB gzip.
4. **Give `site/index.html:319` its citation** (F11) — one link, closes the biggest unsupported assertion on the page.
5. **Add affiliate + analytics disclosure** before any affiliate link ships. The research names FTC scope at `docs/tcg-deep-dive-2026.md:147`; the roadmap puts affiliate first at `:187`.
6. **Retarget the outbound link** from the repo root to `docs/tcg-deep-dive-2026.md`, or reorder `README.md:12` so a visitor does not land on a 252 KB internal prompt.
7. **Hold in the repo, not on the site:** F13 (TCGplayer conduct), F14 (Pokémon enforcement), F15's yen figures, and the `$2–6 RPM` input.

---

## 9. What was deliberately NOT specified

Over-building is the real failure mode for a pre-launch one-pager, and several obvious additions
are actively wrong here. Rejected, with reasons:

| Not specified | Why |
|---|---|
| **In-page hero imagery** | A 3.2 KB page with zero images and **CLS 0.0000** is a feature. Any hero image adds a request, risks layout shift, and would be decoration on a page whose entire argument is that it shows data rather than describing it. |
| **A 2× / retina og:image** | **MEASURED 109,224 B** (PNG-32 at 2400×1260) for a resolution no major unfurl surface renders. |
| **WebP or AVIF for the social card** | Measured smaller (WebP q82 = 23,625 B vs PNG-8 ~20,000 B — and PNG-8 wins anyway). Rejected on **consumer support**: PNG and JPEG are what every unfurler accepts. Not worth a broken card to save nothing. |
| **A web font** | `font-src 'self'` means self-hosting; a single woff2 subset is 15–30 KB, i.e. 5–9× the entire page wire cost, and reintroduces FOUT and layout shift. The system stack costs zero bytes and renders instantly. |
| **A standalone `/privacy` and `/terms`** | Measured: 0 cookies, 0 forms, 0 JS, 0 third-party origins. The honest privacy policy is four sentences. A standalone page implies a data practice that does not exist and makes the site look like it collects more than it does. Folded into `/disclosures`. |
| **An `/about` page** | No consented identity exists in the repo, and git authorship is not consent to publish a name. An anonymous about page is worse than none on a site whose pitch is verifiability. Owner's decision. |
| **A changelog** | Nothing has shipped. A changelog whose only entry is "site launched" advertises that nothing happens. |
| **A CSS extraction to `/assets/site.<hash>.css`** | Adds a second request and a render-blocking dependency to a page that has neither. Revisit when there are enough pages to amortise it. |
| **Analytics / consent banner** | Deliberate. Adding one would end the "runs no scripts, calls no third party" claim, which is currently **MEASURED true** and is a genuine differentiator. |

---

## 10. Open questions that need a human

None of these can be answered from the repository. Each blocks a specific item above.

| # | Question | Blocks | Why it cannot be decided here |
|---|---|---|---|
| 1 | **Is the brand gold allowed to change?** `--gold #9A6F1E` fails AA at 4.31:1 in the default light theme. Draft `#966C1D` clears it at 4.51:1 with the hue preserved. | All artwork, all copy, the whole palette | Brand identity decision. Also sequencing-critical: artwork bakes the hex into pixels, so this must be settled *before* generation, not after. |
| 2 | **Does `hello@bountycharts.com` exist?** | The launch-notify CTA | The recommended CTA is a `mailto:`. MX is not configured and the domain is egress-blocked from this session, so it could not be checked. Shipping a `mailto:` to a dead mailbox is worse than no CTA. **Do not substitute a personal address** — that is a separate decision, and git authorship is not consent. |
| 3 | **Who is publishing this?** | `Organization` JSON-LD, any `/about`, the `og:site_name` semantics | `Organization` requires real facts — legal name, founding date, logo, social profiles. Inventing any of them would be fabricating company facts. Left unspecified deliberately. |
| 4 | **Is the `data-theme` attribute a contract or dead code?** | Any theming refactor, and the CSS architecture for new pages | Carried over unresolved from the August audit. The gate mandates `[data-theme="dark"]` but nothing can set it. Wire up a toggle, or delete both blocks and the gate rule. |
| 5 | **Is an affiliate link planned before launch?** | The priority of `/disclosures` | `docs/deployment/cloudflare.md:155` states the disclosure becomes legally required **before** the first link ships. If a link is imminent, `/disclosures` is P0, not P1. |
| 6 | **Does the edge set cookies?** | The privacy copy on `/disclosures` | "Runs no scripts, calls no third party" is measured true of the HTML. Cookies are a claim about Cloudflare's edge — `__cf_bm` may be set under bot management. Unverifiable from here; check a live response before publishing any "no cookies" wording. |

---

## 11. Evidence coverage for this document

| Capability | Status |
|---|---|
| Serve the site locally | **Yes** — `site/` over `python3 -m http.server`, port 8899 |
| Drive a real browser | **Yes** — Playwright + Chromium 1194. All pixel, byte, contrast, colour-count and CWV figures came from it |
| Encode and measure real images | **Yes** — rendered the og card at 1200×630 and measured PNG/JPEG/WebP; counted its colour distribution |
| Run the gate and test suite | **Yes** — every markup form in §1.2 was run against a scratch copy |
| Fetch the live public URL | **No** — egress-blocked (403 CONNECT). Nothing here is verified against production |
| Generate images with a model | **No** — this document specifies prompts; no image was generated |
| Optimise PNGs with a real quantiser | **No** — no `pngquant`, `optipng`, `oxipng`, `cwebp`, `avifenc` or Pillow in this container. The ~20 KB PNG-8 figure is supported by the measured colour distribution (2,905 unique colours, 98.46% in the top 64), not by running a quantiser end to end |

**Method note.** This specification was produced by a 12-agent workflow. Seven agents completed;
five hit a session limit mid-run. The lost work was the insertion-mechanics lens, three adversarial
verifiers, and the synthesiser. §7 was written directly and its checks were run; §3's
lens-conflicts were reconciled by hand in §3 rather than by a verifier. Every load-bearing number
in §1, §2 and §7 was independently re-measured before being written down, including two that
**corrected** the surviving agents' and my own earlier figures. The conflict between
`disclosure.html` and `disclosures.html` is exactly the class of error the lost verifiers existed
to catch, which is a fair indication that others may remain in §4–§6.

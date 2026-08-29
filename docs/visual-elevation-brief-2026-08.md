# Visual elevation brief — August 2026

**What this document is.** A creative concept brief for new photo and video assets only —
nothing that exists on the site today is referenced, evaluated, or altered. Per the framing
of this exercise, it assumes all prior front-end audit findings are already resolved and
does not re-verify site state, code, function, or layout. Nothing here has been built or
generated; this is direction to hand to an image/video generation platform of your choosing.
Scope is strictly visual media — no backend, no UI function, no layout engineering.

**The brief, in one line.** The site currently wins on restraint — clean typography, a tuned
palette, zero visual noise. The risk of adding imagery to a page like this is diluting that
discipline into generic stock-photo SaaS. The opposite risk — adding nothing — leaves real
trust-building work undone, because people browse with their eyes before they read a word of
copy. This brief threads that needle with one governing concept, applied sparingly.

---

## Art direction: "The Vault Ledger"

Treat the page as a private research desk crossed with an archive vault at rest — not a
trading floor mid-frenzy. The site's own copy already says it best: *decision support, not a
buy signal.* The imagery has to hold that same restraint, or it undercuts the one sentence
the whole brand stands on.

**Materials.** Brushed dark gunmetal, aged cotton ledger paper, gold leaf, a jeweler's loupe,
single-source directional light — the vocabulary of appraisal and archives, not of apps.

**Motion language.** Slow, minimal, contemplative. A vault door easing open, never a trailer
cut. Exactly one asset in this entire brief moves — see "What I deliberately left out" at the
end for why that restriction is the point, not a limitation.

**The two-bookend principle.** Only two moments in the whole page go fully dark: the hero
(arrival) and the footer (departure) — like a vault door opening and closing around
everything in between. Every asset that lives inside the page body, where the default theme
is light, is shot warm and light — cream, honey wood, aged vellum — so it sits inside the
page's own `#FAFAF8` field instead of interrupting it with a dark rectangle.

**Brand gold — one authoritative value.** The site's light-theme gold (`#966C1D`) was darkened
specifically to clear text-contrast requirements; it is a typography color, not a photography
color. Every prompt below uses the richer dark-theme gold instead — `#D9A94F` to `#EBC475` —
because that is the value actually chosen for its visual warmth, not for legibility math.

**Shared exclusions — apply to every single prompt in this brief.** No playing cards, trading
cards, card frames, card backs bearing printed text or numbers, mana symbols, set symbols,
character art, or publisher logos — nothing a viewer could mistake for Riftbound, Pokémon,
Magic, One Piece, or any other real card game. No rockets, bull/bear iconography, candlestick
charts, cash stacks, coin piles, or "up-and-to-the-right" hype charts — the site's own
no-buy-signals promise applies to its imagery as much as its copy. No stock-photo people, no
laptop-and-latte SaaS clichés, no neon cyberpunk glow. No on-image text, watermarks, or UI
chrome of any kind.

---

## The seven moments, in page order

| # | Movement | Site location | Format | Spec |
|---|---|---|---|---|
| I | Arrival | Hero, behind the H1 | Video + poster still | 2560×1440, 8–10s loop |
| II | The Instruments | "What it does" band | Still | 2400×800 ultra-wide |
| III | The Record | "Why Riftbound first" | Still | 1920×1280 |
| IV | The Seal | "What this is not" | Still | 800×800 |
| V | The Archive | Status / research links | Still, tileable | 2048×2048 |
| VI | Departure | Footer | Still | 2560×400 ultra-wide |
| VII | The Dead End | 404 page | Still | 1600×1000 |

Seven moments, one of which carries motion. That is the whole proposal — not because more
couldn't be justified, but because a page built on restraint earns its A+ by choosing well,
not by filling space. See the closing section for exactly what was cut and why.

---

### I — Arrival · the hero atmosphere

**Location.** `site/index.html`, the hero — behind and around the H1 ("What will this deck
cost you next week?") and the lede paragraph, above the ticker strip.

**Reasoning.** The first two seconds decide whether a visitor extends trust. Pure typography
on flat color is correct for a lean MVP, but one restrained cinematic moment here is what
separates a credible research desk from a landing page — provided the motion stays quiet
enough that it never competes with the words sitting on top of it.

**Vision & tone.** Extreme macro of light moving across brushed gold in near-total darkness —
the feeling of value catching the light without ever showing a price. Quiet, expensive,
unhurried. A vault door easing open: anticipation, not spectacle. Keep the upper-left
two-thirds of the frame calm and low-contrast — that is where the headline sits, and the
image must lose that fight on purpose.

**Format & specs.** Primary: video, 2560×1440 (16:9), 8–10 second seamless loop, 24fps,
no audio track. Companion: a single still frame from the same setup, same resolution, as a
static/no-motion fallback and poster image.

**Prompt — video.**
```
Extreme macro cinematography, a brushed dark gunmetal surface in near-total darkness, a
single warm gold light source sweeping slowly across the metal and revealing fine machined
grain, shallow depth of field, soft bloom on the highlight, tiny suspended dust particles
catching the light, moody museum-vault atmosphere, restrained and unhurried camera drift with
no cuts, no zoom, no crash motion, color palette anchored to deep charcoal-black (#0E1116)
background with warm antique gold (#D9A94F to #EBC475) highlight, cinematic, shot on
anamorphic 65mm look, quiet and expensive mood, no text, no logos, no UI elements, no people,
no cards, no card frames, no game symbols, no bull or bear iconography, no charts, no cash, no
coins, no rockets, no neon, no glowing cyber-tech aesthetic.
```

**Parameters.** 16:9 · 2560×1440 (or platform max, upscale after) · 8–10s · 24fps · request a
seamless/loopable render · low or "subtle" motion-strength setting if the platform exposes
one · cinematic lighting preset if available · no camera shake.

**Prompt — companion still.**
```
Extreme macro photograph of a brushed dark gunmetal surface in near-total darkness, a single
warm gold light source raking across the metal and revealing fine machined grain, shallow
depth of field, soft bloom on the highlight, a few suspended dust particles catching the
light, moody museum-vault atmosphere, deep charcoal-black background (#0E1116) with warm
antique gold highlight (#D9A94F to #EBC475), shot on medium-format camera, 85mm lens, f/1.8,
quiet and expensive mood, no text, no logos, no UI elements, no people, no cards, no card
frames, no game symbols, no charts, no cash, no coins.
```

**Parameters.** 2560×1440 · sRGB · JPG or PNG master.

---

### II — The Instruments · a precision accent band

**Location.** `site/index.html`, a thin full-width band accompanying the "What it does"
section (the 01 / 02 / 03 grid: *Deck cost, forecast* · *Movement, explained* · *Spread and
reprint risk*).

**Reasoning.** That copy is entirely about measurement. A restrained photograph of literal
instruments for appraising small valuable objects makes "we measure carefully" *felt*
instead of only claimed, exactly where the site explains its own method.

**Vision & tone.** Overhead flat-lay on warm ivory vellum, soft daylight from one side, a
jeweler's loupe, fine brass calipers, and a small antique brass balance scale arranged with
real negative space. Studious, careful, old-world craftsmanship meeting modern rigor — "we
still count by hand."

**Format & specs.** Still image, ultra-wide band, 2400×800 px. Warm/light palette so it sits
naturally on the page's default `#FAFAF8` background.

**Prompt.**
```
Overhead flat-lay photograph on a warm ivory vellum desk surface, softly lit by natural
window light from the left, a jeweler's loupe, a pair of fine brass calipers, and a small
antique brass balance scale arranged with generous negative space, shallow shadows, warm
neutral tones of cream, aged brass and soft charcoal, editorial studio photography, shot on
medium format, 50mm lens, f/4, quiet and precise mood, no cards, no card frames, no game
pieces, no coins, no cash, no gemstones, no people, no hands, no text, no logos, no charts.
```

**Parameters.** 2400×800 (ultra-wide band) · optional 3:2 alternate crop at 1800×1200 for
flexibility · sRGB · light/warm palette.

---

### III — The Record · an editorial market photograph

**Location.** `site/index.html`, beside or behind the "Why Riftbound first" paragraph.

**Reasoning.** This section is the site's origin story for timing — why this market, why now.
One strong editorial photograph gives that claim visual weight, conveying "a real market is
moving" through atmosphere rather than through any literal chart or a single depicted card.

**Vision & tone.** Macro/editorial shot of plain, unprinted protective card sleeves stacked
and slightly fanned on warm honey-toned wood, as if just handled — a market caught mid-breath.
Kinetic but composed: a market waking up, not a market in a frenzy.

**Format & specs.** Still image, 1920×1280 px (3:2). Warm/light palette.

**Prompt.**
```
Editorial macro photograph of a small stack of plain translucent protective card sleeves,
completely blank and unprinted, slightly fanned and askew as if just handled, resting on a
warm honey-toned wood desk, warm directional side light creating soft highlights on the
sleeve edges, shallow depth of field with the nearest sleeve in sharp focus, shot on 85mm lens
f/2, warm neutral color palette of honey wood, soft cream and warm charcoal shadow, editorial
finance-and-collector-desk photography, a sense of a market recently in motion, no printed
card art, no text, no numbers, no logos, no symbols, no set marks, no people, no hands, no
charts, no cash, no coins.
```

**Parameters.** 1920×1280 (3:2) · sRGB · warm/light palette.

---

### IV — The Seal · a verification mark

**Location.** `site/index.html`, beside or within the "What this is not" note block (the
"No buy signals" callout).

**Reasoning.** This paragraph is the site's ethical spine. A literal illustration would fight
the sober copy sitting next to it. An engraved hallmark motif — the visual language jewelers
and assayers use to certify authenticity — makes "verified, not hyped" felt wordlessly, and
echoes the ◈ diamond already in the wordmark.

**Vision & tone.** Tight macro of an abstract engraved geometric mark — a faceted
diamond/lozenge, deliberately echoing the site's own ◈ glyph rather than inventing new
iconography — stamped into brushed dark steel under cold, precise light. Small and quiet: an
object of authority, not decoration.

**Format & specs.** Still image, small square, 800×800 px. This is the one embedded accent
allowed to sit dark, since it behaves like a seal on a document rather than a page band.

**Prompt.**
```
Extreme macro photograph of an abstract engraved geometric hallmark stamp resembling a
faceted diamond or lozenge, pressed into brushed dark steel, cold precise directional
lighting from above, crisp shadow detail in the engraved lines, extremely shallow depth of
field, deep charcoal-black background, small quiet composition with generous negative space,
shot on macro lens f/2.8, mood of authority and quiet verification, no letters, no numbers,
no readable text, no brand logos, no cards, no coins, no cash, no gemstones, no people.
```

**Parameters.** 800×800 · dark palette · sRGB.

---

### V — The Archive · a ledger-paper texture

**Location.** `site/index.html`, a background texture behind the Status section and its
research links (the deep dive, the fact-check ledger, the unit-economics model).

**Reasoning.** This section points to the site's most substantive content. A barely-there
archival paper texture signals "primary documents live here" without competing for attention
against the actual links, which must stay the clear focus.

**Vision & tone.** Extremely subtle aged cotton ledger paper, warm ivory tones, faint fibrous
grain, almost imperceptible — a whisper of "archive," not a scrapbook page.

**Format & specs.** Still image, seamless/tileable texture, 2048×2048 px master (downscale as
needed). Very low contrast so overlaid text stays legible.

**Prompt.**
```
Seamless tileable texture of aged cotton ledger paper, warm ivory and cream tones, extremely
subtle fibrous grain, faint foxing spots, very low contrast, soft even studio lighting,
archival document photography, flat and even with no strong directional shadow, suitable as a
quiet background texture, no text, no numbers, no ink marks, no stamps, no logos, no
illustrations.
```

**Parameters.** 2048×2048, tileable · sRGB · very low contrast / high key.

---

### VI — Departure · the footer bookend

**Location.** `site/index.html` and `site/404.html`, the footer background band.

**Reasoning.** Closes the page's material arc: the same brushed dark/gold language from the
hero returns at the very bottom, like the vault door easing shut. Gives the page a deliberate
ending instead of letting it trail off into plain background.

**Vision & tone.** The hero's material, calmed: light fading rather than sweeping, mostly dark
with one thin warm horizon-line. Quiet finality — "the record is filed." Deliberately still,
in contrast to the hero's motion: open with movement, close with stillness, like a held
breath released.

**Format & specs.** Still image (no motion — see the asymmetry noted above), ultra-wide thin
band, 2560×400 px.

**Prompt.**
```
Extreme macro photograph of a brushed dark gunmetal surface fading to near-black, a single
thin warm gold horizon-line of light along the lower edge, fine machined grain barely visible
in the dark, soft bloom, calm and settled mood with light fading rather than sweeping, deep
charcoal-black (#0E1116) dominant with warm antique gold (#D9A94F) accent along the bottom
edge only, shot on medium format, 85mm lens f/2, quiet closing mood, no text, no logos, no
people, no cards, no charts, no coins, no cash.
```

**Parameters.** 2560×400 (ultra-wide band) · dark palette · sRGB.

---

### VII — The Dead End · the 404 page

**Location.** `site/404.html`, behind or beside "That page isn't here" ("404 — NO DATA").

**Reasoning.** A dead end is a brand moment most sites waste. The existing copy is already
wry and on-brand; a single restrained image reinforces it instead of leaving a text-only
void, turning friction into a small, memorable piece of craft.

**Vision & tone.** A single empty velvet-lined display tray — the kind used to present a
graded collectible — under a spotlight, dust motes visible, nothing inside it. Dry wit,
quiet: "there's nothing here to measure."

**Format & specs.** Still image, 1600×1000 px. Dark palette, matching the hero/footer
register since this is a departure from the normal page, not a continuation of it.

**Prompt.**
```
Studio photograph of a single empty velvet-lined display tray of the kind used for a graded
collectible, photographed straight-on under a single spotlight from above, dust motes visible
in the light beam, deep charcoal-black background (#0E1116), the tray in dark navy or
charcoal velvet, deliberately empty and unoccupied, shallow depth of field, quiet dry-humor
mood, shot on medium format 100mm macro lens f/4, no card, no coin, no object inside the
tray, no text, no logos, no people.
```

**Parameters.** 1600×1000 · dark palette · sRGB.

---

## What I deliberately left out, and why

An A+ on visual aesthetics is as much about restraint as addition — the brief the site itself
already models. Specifically not proposed:

- **Video anywhere but the hero.** Motion is rationed to exactly one moment so its appearance
  carries weight instead of becoming wallpaper. A page that moves everywhere reads as a demo
  reel; a page that moves once, deliberately, reads as directed.
- **Any imagery inside the ticker strip or near the sample figures.** Those numbers are
  already flagged as illustrative; decorating them further would dress up the one part of the
  page that most needs to stay sober.
- **A literal chart, graph, or price-line motif anywhere on the site**, in any of the seven
  prompts above — even an abstract one. The instrumentation/measurement register from the
  copy ("no buy signals") extends to imagery. A generated "line trending upward" is a buy
  signal, however abstract the art direction around it.
- **Any card art, even original/generic "TCG-inspired" art.** Not merely publisher IP — the
  brief avoids depicting *any* specific playable card, front or back, printed or blank-but-
  branded, anywhere. Sleeves and trays stand in for the category without ever showing the
  object itself.
- **A hero carousel or multiple rotating header images.** One hero, one held moment. Rotating
  banners are exactly the SaaS-template signature this brand is built to read as the opposite
  of.
- **Stock photography of people** — no "team at a whiteboard," no "excited trader," no
  generic hands-on-laptop shots. The whole site currently has zero human figures in its
  visual language; introducing them here would be the single biggest tone break available.

---

*Prepared as a creative concept exercise only. No site files were modified to produce this
document, and none of the imagery described has been generated. Hand the seven prompts above,
verbatim, to the image or video generation platform of your choice.*

# TCG Industry Deep Dive — Strategic Analysis & Corrected Roadmap

**Subject:** Review of *Executive Intelligence Report: Trading Card Game Industry Trajectory, Growth Vectors, and Monetization Strategy (2024–2026)*
**Date:** July 2026
**Companion documents:** [Fact-Check Ledger](./fact-check-ledger.md) · [Unit Economics Model](../models/unit_economics.py)

---

## 0. Verdict

The report is a good market description and a poor business plan.

Its reporting on *what happened* is largely sound — the Altered post-mortem is genuinely sharp, the Riftbound launch metrics hold up, and it correctly identifies TCGplayer's 48-hour first-click attribution as a binding constraint (a detail most affiliate aggregators get wrong).

Its reasoning about *what to do next* rests on four premises that do not survive contact with evidence:

1. **The API it plans to build on is closed.** The "1-Click Buyout" mechanism — the only specific conversion device in the entire plan — requires TCGplayer API access that has not been available to new developers since roughly late 2024.
2. **Its #1 growth vector cannot be monetized the way it proposes.** Pokémon TCG Pocket is digital-only. There is no secondary market, so there is **no affiliate surface at all** — and it sits in the lowest-RPM major ad vertical.
3. **The "tooling void" does not exist.** Every target game already has 5–10 free tools, several of them publisher-official.
4. **The pricing is 2.5–5× above the category leaders**, who have brand equity this project does not.

None of this makes the underlying opportunity fake. It makes the proposed route to it wrong. §5 sets out a corrected one.

---

## 1. What the report gets right

Worth stating plainly before the criticism, because these are real and they should survive into any revised plan.

**The Altered autopsy is correct and well-reasoned.** The four-part causal chain — phygital friction, LGS margin destruction, algorithmic uniques that undermined deckbuilding agency, and no IP moat — is accurate and is the most analytically valuable passage in the document. The KYC detail (identity verification triggered at €2,000 cumulative sales) is a genuinely non-obvious finding.

**The attribution insight is correct and non-obvious.** TCGplayer's affiliate program really does run **3.5% commission on a 48-hour, first-click** basis. Most third-party affiliate directories list this program as last-click. The report is right; they are wrong. Building strategy around this constraint is the correct instinct.

**The structural read on IP moats is correct.** The observation that original-IP TCGs struggle to generate derivative fan content, and therefore struggle for algorithmic visibility, is a real mechanism and it did contribute to Altered's failure.

**The Riftbound numbers are real.** 300% search surge, 6,300 searches/hour, Kai'Sa Signature at $2,356 — all confirmed.

---

## 2. Four structural flaws

### 2.1 The API hole

> *"We will deploy highly visible '1-Click Buyout' API integrations on tournament-winning decklists… the affiliate link will instantly load the entire 60-card deck into their TCGplayer cart."*

This is the single most specific, most operationally important tactic in the report. It is the only described mechanism for converting inside the 48-hour window. And it cannot be built as written.

TCGplayer **stopped accepting new public API applications around late 2024**, following the eBay acquisition. As of mid-2026 the developer application path is effectively closed — applications go unanswered — and a Partner API deprecation is documented. The data strategy shifted toward keeping pricing data inside the ecosystem and preventing mirroring by competitors.

An entire cottage industry now exists selling around this gap (JustTCG, Scrydex, TCGdex, PriceCharting, pokemontcg.io), which is itself the clearest possible evidence that the front door is shut.

**What actually works:** TCGplayer supports **Mass Entry** — a URL-encoded quantity-and-name payload that opens a pre-filled cart without any API key, and which accepts an affiliate parameter. It is a genuine one-click deck-to-cart flow. It is also available to every competitor equally, so it is a table-stakes feature, **not a moat**. The report's plan is achievable; its framing as proprietary advantage is not.

**Consequence:** any roadmap that assumes programmatic access to TCGplayer catalog or price data needs a paid third-party data vendor line item. That is a real recurring cost the report budgets at zero.

### 2.2 The Pokémon Pocket monetization paradox

The report ranks Pokémon TCG Pocket as the #1 growth vector — correctly, on the metrics. 200M+ downloads, $1.6B in 18 months, unmatched engagement.

It then never asks whether that traffic can be monetized. It cannot, in the way the report proposes:

- **Affiliate revenue from Pocket traffic is structurally zero.** The cards are digital-only. There is no secondary market, no TCGplayer listing, nothing to buy. Pillar 2 — the entire affiliate apparatus — earns **$0** on the report's own highest-priority audience.
- **Ad revenue is worst-in-class.** Gaming display is a **$2–6 session RPM** vertical against $15–40 for personal finance. Pocket skews mobile, young, and heavily international — Japan, France and Brazil are named in the report itself. Mobile, non-Tier-1 traffic is the lowest-yielding inventory in an already low-yielding vertical.
- **Subscription willingness is weakest here.** The report's own churn thesis is "actionable data translates to financial gain in the secondary market." In a game with no secondary market, that thesis has no referent. There is nothing to arbitrage.

**This inverts the report's priority stack.** Ranked by *revenue per session* rather than raw audience:

| Rank | Game | Affiliate surface | Ad yield | Sub thesis |
|---|---|---|---|---|
| 1 | **One Piece** | Strong — active singles market, high-velocity meta | Mid | Strong — real price volatility |
| 2 | **Riftbound** | Strong — new, thin information, high spreads | Mid | Strong |
| 3 | **Star Wars: Unlimited** | Moderate | Mid | Moderate |
| 4 | **Pokémon TCG Pocket** | **None** | Low | Weak |

Pocket is a top-of-funnel brand and audience-acquisition asset. It is not a revenue asset. Treating those as the same thing is the report's central analytical error.

### 2.3 The "tooling moat" is a false premise

> *"Launch ultra-fast, mobile-optimized deck-builders, automated meta-tier lists, and API-integrated pricing guides for games that currently lack them."*

No target game lacks them. A non-exhaustive census as of July 2026:

| Game | Existing free tools |
|---|---|
| **Riftbound** (9 months old in the West) | **Piltover Archive — Riot's own official** database, deck builder, hand simulator and tournament decks; riftbound.one; riftmana.com; riftdecks.com; riftbound.gg; riftools.app; Mobalytics; TCGFan |
| **One Piece** | optcg.one; onepiece.gg; onepiece-cardgame.dev; Egman Deck Builder; OnePieceTopDecks; OPTCGSim (full play client) |
| **Pokémon** | LimitlessTCG — dominant since 2017, the de facto tournament and meta authority |
| **MTG** | Moxfield; Archidekt; EDHREC; Scryfall; MTGGoldfish; Draftsim |
| **Star Wars: Unlimited** | SWUDB — cited in the report itself as an existing incumbent |

Riftbound is the sharpest refutation. It is the report's own example of a young, under-served game — and it accumulated **eight or more competing tools within nine months**, one of which is built and promoted by the publisher. Publisher-official tooling is the specific failure mode here: it is free, canonical, integrated with organized play, and cannot be out-competed on authority.

The report's diagnosis of Altered — that publishers ship bad software — is true. Its inference, that the tooling layer is therefore vacant, does not follow. The tooling layer is where everyone already is. It is the most crowded, least defensible surface in the category, and it is crowded specifically because it is cheap to enter.

### 2.4 The pricing is above market, and the ladder is upside-down

| Product | Entry price | Position |
|---|---|---|
| **Moxfield** | **$1/mo** | Leading MTG deck builder |
| **EDHREC** | **$2/mo** | Dominant MTG Commander data site |
| **Report's Tier 1** | **$5/mo** | Zero brand, zero traffic |

Tier 1's headline benefit is **ad-free access** — asking users to pay $5 to remove inventory yielding $2–6 per *thousand* sessions. The value exchange is transparently lopsided and users price it correctly.

The arithmetic does cut the report's way in one respect, and it is worth making explicit because the report never does: **one $5 subscriber is worth roughly 1,000+ ad sessions.** Subscriptions are unambiguously the right long-run instrument in a low-RPM vertical. The error is not the emphasis — it is the sequencing and the price point.

Tiers 3 and 4 invert the intended logic:

- **Tier 4 ($149.99/mo, 1-on-1 coaching)** is a consultancy, not software. It is capped by hours in a month, does not scale, and carries the highest delivery cost in the stack. The report calls it "total subscriber lock-in." It is the opposite — it is the most churn-exposed line, because the subscriber is evaluating a named individual's performance every single month.
- **Tier 3 ($49.99/mo)** has the same problem at lower margin.

The report's own strongest argument — that data-driven subscriptions scale — applies to **Tier 2 alone**. Tiers 3 and 4 should be understood as a services business bolted onto a software business, and priced, staffed and forecast separately, if kept at all.

---

## 3. Two risks the report does not mention

### 3.1 IP exposure is inverted against the priority ranking

The report ranks its targets by audience size and never once considers whether monetizing each is permitted.

**The Pokémon Company International's media guidelines state that licensees are not authorized to commercialize content, "including by selling it or charging a fee for access to it."** The license is explicitly non-commercial. A paid-subscription product built on Pokémon card imagery sits directly outside it.

The enforcement pattern is the dangerous part. TPC's former chief legal officer described the practice as waiting **"to see if they get funded"** before engaging. Enforcement is *triggered by monetization*. A free Pokémon fan tool is tolerated; the moment it has a paywall, it becomes worth acting against. Relic Castle (2024) and Pokémon Essentials are the precedents.

**Riot Games is at the opposite end.** Its published fan-content policy is permissive and explicitly contemplates community projects. Riot also ships its own official tooling, which sets a clear boundary but also signals tolerance for the surrounding ecosystem.

**The resulting risk gradient runs exactly opposite to the report's priority list:**

| Game | Monetization risk | Report's rank |
|---|---|---|
| Riftbound | **Low** — permissive published policy | #3 / #5 |
| Star Wars: Unlimited | Low–moderate | #4 |
| One Piece | Moderate — Bandai tolerates a large tool ecosystem in practice | #2 |
| **Pokémon** | **High** — explicitly non-commercial; enforcement triggered by funding | **#1** |

The report's top-ranked opportunity is its highest legal risk, and the risk activates precisely on the event the plan is designed to cause.

### 3.2 The buyout-alert product has a mechanical flaw

Tier 2's core deliverable is "Algorithmic Market Buyout Alerts" — the promise that a subscriber buys at $5 before a card spikes to $30.

Three problems, in ascending order of seriousness:

1. **It is self-defeating at scale.** Publishing a buy signal to N subscribers *is* the demand event. Early subscribers profit; later ones become exit liquidity for earlier ones. The product's value **decreases monotonically with subscriber count** — the opposite of the scaling property a subscription business needs.
2. **It creates an unavoidable appearance of front-running.** If the operator holds any inventory in an alerted card, they profit from the alert they published. Even scrupulously handled, this is indefensible in public once alleged. It requires a written no-position policy, enforced and disclosed, from day one.
3. **Trading cards are not securities, so securities law does not apply** — but FTC endorsement and deceptive-practice rules do, and a paid product making specific financial-return claims is squarely within their scope. Marketing copy of the form "the subscription pays for itself for six months" is a quantified earnings claim.

The community-reputation risk is the binding one. TCG communities react to coordinated buyouts with sustained hostility, and reputation is the only real asset an information business in this space has.

---

## 4. Corrected market picture

Replacing the report's figures with verified ones changes the strategic read:

**Pokémon TCG Pocket is bigger than the report says and matters less than the report thinks.** 200M downloads (May 2026), not 150M. It is the largest audience in the category and the worst-monetizing per session.

**One Piece is smaller than the report says and matters more.** Not $768M — roughly **$170M** for the card game in Japan FY2023–24, inside a ~$1.99B Bandai card segment. But it has the strongest *combination* of active secondary market, meta velocity, spoiler-driven Western demand ahead of local release, and tolerated third-party tooling. Ranked by monetizable session, it is #1.

**Riftbound is the highest-quality remaining opening, and it is closing.** Real launch metrics, permissive IP policy, active secondary market, thin information environment. But eight-plus tools already exist and Riot ships an official one. The window is months, not years.

**Star Wars: Unlimited is a distribution story, not a growth story.** Asmodee's growth came from distributing *other publishers'* games — 72%+ of revenue — while SWU's own performance was described as "normalising." It is a stable mid-tier asset, not an accelerating one.

**The Altered audience is a rounding error, not a prize.** Roots of Corruption drew €420K from backers. At typical pledge levels that implies roughly **4,000–5,000 people**. Capturing *every single one* at $5/mo yields ~$20–25K/mo gross; realistic capture is low single-digit percent — order **$1–2K/mo**. And every backer is **being refunded in full**, which removes the grievance the acquisition thesis depends on. Meanwhile the proposed SEO targets ("games like Altered TCG," "what to play after Altered shuts down") describe a query set whose volume declines by construction: a dead game's search interest only falls.

The Altered dissection is worth keeping as *analysis*. It is not worth building an acquisition channel on.

---

## 5. Revised roadmap

The report's three pillars are the right pillars. The sequencing, the entry order and the price points are wrong. Concretely:

### Phase 1 — Months 0–6: one game, one wedge

**Pick Riftbound.** Permissive IP policy, real secondary market, active meta, still-thin information layer, and the audience is native to online tools. It is the only target where legal risk is low, affiliate surface is real, and the incumbent set is beatable.

Do **not** build a general deck builder. Eight exist and one is Riot's. Build the thing none of them do well — the report's own best instinct, applied properly: **price-and-meta intersection**. Not "what is the best deck" (solved, free, everywhere) but **"what will this deck cost me next week, and what is about to move."** That is a data product, not a CRUD app, and it is where the report's market-analyst thesis actually has legs.

Budget a third-party price data vendor from day one. It is a real cost.

### Phase 2 — Months 3–9: monetize in the correct order

The report's ordering (ads → affiliate → subscriptions) is backwards for a zero-traffic property.

1. **Affiliate first.** It works at any traffic level, needs no eligibility gate, and pays from session one. Ship deck-to-cart via **Mass Entry URLs**, not the API. Optimize hard for *first* click, because first-click attribution makes this a race against every competing site — position affiliate links **above** meta content, not below it.
2. **Ads second, and only when eligible.** Mediavine Journey at 1K sessions/mo, Raptive or Mediavine "Official" at ~25K pageviews. Model gaming RPM at **$3–4**, not the $15–50 blended figures the networks advertise.
3. **Subscriptions third**, once there is an audience with a reason to trust the data.

### Phase 3 — Months 9–18: subscriptions, repriced

| Tier | Report | Revised | Rationale |
|---|---|---|---|
| Entry | $5.00 | **$3.00** | Must sit near EDHREC's $2 and Moxfield's $1 without a brand to justify a premium. |
| Analyst | $15.00 | **$12.00** | The only genuinely scalable tier. Make it the product. |
| Pro | $49.99 | *defer* | Services business. Launch only if Tier 2 shows demand. |
| Elite | $149.99 | *cut* | Does not scale; highest churn; highest delivery cost. |

Reframe Tier 2 away from falsifiable return promises ("buy at $5 before it hits $30") toward **decision support** ("full price history, spread analysis, reprint-risk flags, and movement alerts across every card you own"). Same data, same product, no earnings claim — which removes the FTC exposure, removes the self-defeating scaling property, and removes the monthly falsification event that drives churn.

### Phase 4 — Month 12+: expand, in risk order

One Piece → Star Wars: Unlimited → MTG. **Add Pokémon last, and only physical Pokémon, and only behind legal review.** Pokémon TCG Pocket content can be run as a free, ad-only top-of-funnel property with no paywall, which stays inside TPCi's non-commercial line — but it should never sit behind the same paywall as everything else.

---

## 6. What the numbers actually look like

Run the model: `python3 models/unit_economics.py`

Indicative monthly revenue against the report's own three pillars, using verified rates (gaming RPM $4, TCGplayer 3.5% at 48h first-click with a contested win rate, EDHREC-adjacent pricing):

| Monthly sessions | Ads | Affiliate | Subscriptions | **Total** | Rev / 1K sessions |
|---|---|---|---|---|---|
| 25,000 | $88 | $66 | $153 | **$306** | $12.22 |
| 100,000 | $400 | $262 | $610 | **$1,272** | $12.72 |
| 500,000 | $2,000 | $1,310 | $3,051 | **$6,361** | $12.72 |
| 2,000,000 | $8,000 | $5,242 | $12,203 | **$25,445** | $12.72 |

Two sensitivities worth running, because each isolates one of the report's errors:

| Scenario | Affiliate @ 100K sessions | Total | Δ |
|---|---|---|---|
| Baseline (40% first-click win rate, 40% digital traffic) | $262 | $1,272 | — |
| **First-click assumed uncontested** — what a plan implies when it ignores the term | $655 | $1,665 | affiliate **+150%** |
| **Pocket-led traffic** (80% digital, the report's stated priority) | $87 | $1,098 | affiliate **−67%** |

```
python3 models/unit_economics.py --first-click-win-rate 1.0 --sessions 100000
python3 models/unit_economics.py --digital-share 0.8 --sessions 100000
```

Four things fall out, and all four matter more than any figure in the original report:

1. **This is a traffic-scale business before it is a monetization-cleverness business.** Revenue per 1,000 sessions is essentially flat at ~$12.72 across three orders of magnitude — the rate levers barely move it. Volume is the only variable that matters, and the report spends its entire third section optimizing rate.
2. **Subscriptions do dominate at scale — the report's central instinct is right.** They are ~48% of revenue at every tier above 100K sessions, and one subscriber is worth roughly **9,600 ad sessions** at $4 RPM. But they arrive *last*, not first, and only with real churn discipline.
3. **Affiliate underperforms intuition** because of the constraint the report itself correctly identified and then failed to apply. Assuming you always win first-click inflates affiliate revenue by **2.5×**. Model the win rate explicitly; do not assume it.
4. **Pursuing the report's own #1 priority makes the business worse.** Shifting to Pocket-led traffic cuts affiliate revenue by two-thirds and drops revenue per 1,000 sessions from $12.72 to $10.98 — a ~14% haircut on the identical audience size.

---

## 7. Open questions

Worth resolving before committing capital:

- **Riftbound margin.** The 45% LGS figure is unsourced and load-bearing. If retailer economics are ordinary, the shelf-space thesis weakens and Riftbound's physical trajectory is less certain than the report assumes.
- **Riot's tooling roadmap.** If Piltover Archive adds pricing, the Phase 1 wedge closes. This is the single largest execution risk and should be monitored continuously.
- **Price data vendor selection.** Cost, licence terms and redistribution rights differ materially across JustTCG, Scrydex, PriceCharting and TCGdex. This is a procurement decision, not a technical one.
- **Pocket's actual share of Pokémon IAP revenue.** The report's 37% figure is unsourced. It matters only if a Pokémon strategy is pursued at all.

---

## Sources

Market sizing — [Custom Market Insights](https://www.custommarketinsights.com/report/trading-card-games-market/) · [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/trading-card-game-market) · [Zion Market Research](https://www.zionmarketresearch.com/report/trading-card-game-market)

Pokémon TCG Pocket — [200M downloads](https://gamerant.com/pokemon-tcg-pocket-200-million-downloads/) · [Sensor Tower 100M](https://sensortower.com/blog/pokemon-tcg-pocket-100-million-downloads) · [$1.6bn in 1.5 years](https://www.pocketgamer.biz/pokemon-tcg-pocket-makes-16bn-in-15-years/) · [Year-one $1.3bn](https://www.gamesradar.com/games/pokemon/pokemon-tcg-pocket-reportedly-made-usd245-million-more-than-pokemon-go-managed-in-its-first-year/) · [Paldean Wonders peak](https://games.gg/news/pokemon-tcg-pocket-sees-six-month-revenue-high-on-30th-anniversary/) · [Nov 2024 net figures](https://gamedevreports.substack.com/p/appmagic-top-mobile-games-by-revenue-082) · [Trading backlash](https://www.videogameschronicle.com/news/pokemon-tcg-pockets-trading-feature-is-changing-after-fan-backlash/)

One Piece / Bandai — [Bandai IR](https://www.bandainamco.co.jp/en/ir/library/newsletter80_special.html) · [TCG franchise revenue by FY](https://snkrdunk.com/en/magazine/2024/05/02/list-of-tcg-franchises-ranked-by-2023-24-fiscal-year-revenue-in-japan/) · [Bandai card game sales 2017–2025](https://sabatcg.com/bandais-top-3-most-successful-card-games-sales-and-revenue-from-2017-to-2025)

Riftbound — [IGN: 300% search surge](https://tech.yahoo.com/gaming/articles/league-legends-tcg-riftbound-posted-140000478.html) · [Piltover Archive](https://piltoverarchive.com/) · [TCGplayer seller blog](https://seller.tcgplayer.com/blog/discovering-riftbound-league-of-legends-trading-card-game)

Asmodee / SWU — [BoardGameWire: €1.68bn, TCG 60%](https://boardgamewire.com/index.php/2026/05/22/asmodees-annual-revenue-surges-to-e1-68bn-on-tcg-distribution-power-but-sales-of-its-own-board-games-fall/) · [Asmodee year-end report](https://cdn.svc.asmodee.net/production-payload-corporate/asmodee-group-year-end-report-24-25.pdf)

Altered — [BoardGameWire](https://boardgamewire.com/index.php/2026/03/19/the-numbers-simply-arent-there-equinox-to-end-record-breaking-altered-tcg-after-new-crowdfund-falls-well-short-of-goals/) · [TechRaptor](https://techraptor.net/tabletop/news/equinox-announces-cancellation-of-altered-tcg-roots-of-corruption-campaign-and-end-of) · [Equinox statement](https://www.altered.gg/en-us/news/a-chapter-closes) · [GamesRadar](https://www.gamesradar.com/tabletop-gaming/altered-tcg-shuts-down-due-to-missing-the-eur2-million-needed-to-guarantee-the-future-of-the-game/)

Monetization — [TCGplayer affiliate docs](https://docs.tcgplayer.com/docs/tcgplayer-affiliate-program) · [TCGplayer Partner API deprecation](https://docs.tcgplayer.com/docs/partner-api-deprecation) · [TCGplayer partner guidelines](https://help.tcgplayer.com/hc/en-us/articles/31411199594391-TCGplayer-Partner-Guidelines) · [API alternatives (2026)](https://tcgapi.dev/blog/tcgplayer-api-alternative/) · [Display RPM by niche](https://toolsignal.site/articles/blog-display-ad-rpm-by-niche-2026) · [Mediavine/Raptive thresholds](https://thisweekinblogging.com/mediavine-raptive-requirements/) · [EDHREC Patreon](https://www.patreon.com/edhrec) · [Moxfield Patreon](https://www.patreon.com/moxfield/membership)

IP policy — [TPCi Media Usage Guidelines](https://pokemon.gamespress.com/Media-Usage-Guidelines) · [Pokémon legal information](https://www.pokemon.com/us/legal/information) · [Enforcement precedent](https://www.techdirt.com/2024/03/28/site-that-listed-information-about-3rd-party-pokemon-fan-games-shuts-down-under-threat/)

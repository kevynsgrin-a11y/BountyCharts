#!/usr/bin/env python3
"""
Unit-economics model for a TCG content/tooling property.

Replaces the assertion-based revenue plan in the source intelligence report with
an explicit funnel, so every number is traceable to an assumption you can argue
with. All defaults are sourced — see ASSUMPTIONS below and docs/fact-check-ledger.md.

Usage:
    python3 models/unit_economics.py
    python3 models/unit_economics.py --sessions 250000
    python3 models/unit_economics.py --digital-share 0.6   # Pokemon-Pocket-heavy traffic
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# ASSUMPTIONS
#
# ads_rpm_*          Gaming is a $2-6 session-RPM vertical, against $15-40 for
#                    personal finance. The $15-50 figures Mediavine/Raptive
#                    advertise are blended across all verticals and are NOT what
#                    a TCG property earns. RPM is tiered because ad-network
#                    eligibility is gated: Mediavine Journey ~1K sessions,
#                    Raptive / Mediavine "Official" ~25K pageviews.
#
# affiliate_*        TCGplayer pays 3.5% on a 48-hour, FIRST-CLICK basis
#                    (confirmed against TCGplayer's own docs; most third-party
#                    affiliate directories list this program as last-click and
#                    are wrong). First-click is the critical term: if any other
#                    affiliate touched the user first, you earn nothing even if
#                    you drove the sale. Hence first_click_win_rate, which most
#                    plans implicitly set to 1.0.
#
# digital_share      Share of traffic on digital-only games (Pokemon TCG Pocket).
#                    These sessions have NO affiliate surface -- the cards cannot
#                    be bought or sold -- and are excluded from affiliate revenue
#                    entirely. This is the single biggest correction to the
#                    source report, which ranks Pocket as its #1 growth vector.
#
# sub_*              EDHREC (dominant MTG Commander data site) starts at $2/mo;
#                    Moxfield at $1/mo. Both have years of brand equity. Default
#                    tier mix reflects the revised ladder in the deep dive:
#                    $3 entry / $12 analyst, with the $49.99 and $149.99 tiers
#                    deferred and cut respectively (services, not software).
# ---------------------------------------------------------------------------


@dataclass
class Assumptions:
    # --- Display advertising -------------------------------------------------
    ads_rpm_small: float = 2.50      # < 25K sessions: AdSense / small networks
    ads_rpm_mid: float = 3.50        # 25K-100K sessions: entry premium networks
    ads_rpm_premium: float = 4.00    # 100K+ sessions: Raptive / Mediavine tier

    # --- Affiliate (TCGplayer) ----------------------------------------------
    digital_share: float = 0.40      # traffic with zero affiliate surface
    outbound_ctr: float = 0.08       # session -> TCGplayer click, transactional pages
    first_click_win_rate: float = 0.40   # you were the FIRST referrer in the window
    click_conversion: float = 0.06   # winning click -> completed order
    average_order_value: float = 65.00   # deck-to-cart skews AOV up
    commission_rate: float = 0.035   # TCGplayer published rate

    # --- Subscriptions -------------------------------------------------------
    sessions_per_unique: float = 2.2
    visitor_to_sub: float = 0.0035   # 0.35% of monthly uniques
    entry_price: float = 3.00
    analyst_price: float = 12.00
    entry_mix: float = 0.88          # remainder converts to analyst tier
    payment_processing: float = 0.06  # Patreon/Stripe blended take
    monthly_churn: float = 0.10      # for LTV only


@dataclass
class Result:
    sessions: int
    ads: float
    affiliate: float
    subscriptions: float
    subscriber_count: float

    @property
    def total(self) -> float:
        return self.ads + self.affiliate + self.subscriptions


def ads_revenue(sessions: int, a: Assumptions) -> float:
    if sessions < 25_000:
        rpm = a.ads_rpm_small
    elif sessions < 100_000:
        rpm = a.ads_rpm_mid
    else:
        rpm = a.ads_rpm_premium
    return sessions / 1_000 * rpm


def affiliate_revenue(sessions: int, a: Assumptions) -> float:
    monetizable = sessions * (1 - a.digital_share)
    clicks = monetizable * a.outbound_ctr
    attributed = clicks * a.first_click_win_rate
    orders = attributed * a.click_conversion
    return orders * a.average_order_value * a.commission_rate


def subscription_revenue(sessions: int, a: Assumptions) -> tuple[float, float]:
    uniques = sessions / a.sessions_per_unique
    subs = uniques * a.visitor_to_sub
    arpu = a.entry_mix * a.entry_price + (1 - a.entry_mix) * a.analyst_price
    gross = subs * arpu
    return gross * (1 - a.payment_processing), subs


def model(sessions: int, a: Assumptions) -> Result:
    subs_rev, subs_count = subscription_revenue(sessions, a)
    return Result(
        sessions=sessions,
        ads=ads_revenue(sessions, a),
        affiliate=affiliate_revenue(sessions, a),
        subscriptions=subs_rev,
        subscriber_count=subs_count,
    )


def blended_arpu(a: Assumptions) -> float:
    return a.entry_mix * a.entry_price + (1 - a.entry_mix) * a.analyst_price


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sessions", type=int, action="append",
                   help="monthly sessions to model (repeatable)")
    p.add_argument("--digital-share", type=float,
                   help="share of traffic on digital-only games (no affiliate surface)")
    p.add_argument("--first-click-win-rate", type=float,
                   help="share of outbound clicks where you are the first referrer")
    args = p.parse_args()

    a = Assumptions()
    if args.digital_share is not None:
        a.digital_share = args.digital_share
    if args.first_click_win_rate is not None:
        a.first_click_win_rate = args.first_click_win_rate

    tiers = args.sessions or [25_000, 100_000, 500_000, 2_000_000]

    print("\nTCG property — indicative monthly revenue")
    print(f"digital-only traffic share: {a.digital_share:.0%}  |  "
          f"first-click win rate: {a.first_click_win_rate:.0%}  |  "
          f"blended sub ARPU: ${blended_arpu(a):.2f}")
    print()
    print(f"{'Sessions':>10} | {'Ads':>9} | {'Affiliate':>9} | {'Subs':>9} | "
          f"{'Total':>10} | {'Subs #':>7} | {'$/1k sess':>9}")
    print("-" * 82)

    for s in tiers:
        r = model(s, a)
        print(f"{r.sessions:>10,} | ${r.ads:>8,.0f} | ${r.affiliate:>8,.0f} | "
              f"${r.subscriptions:>8,.0f} | ${r.total:>9,.0f} | "
              f"{r.subscriber_count:>7,.0f} | ${r.total / s * 1000:>8.2f}")

    print()
    ltv = blended_arpu(a) * (1 - a.payment_processing) / a.monthly_churn
    print(f"Subscriber LTV at {a.monthly_churn:.0%} monthly churn: ${ltv:,.2f}")
    print(f"One subscriber ≈ {ltv / (a.ads_rpm_premium / 1000):,.0f} ad sessions "
          f"at ${a.ads_rpm_premium:.2f} RPM")
    print()
    print("Read-outs:")
    print("  1. This is a traffic-scale business before it is a rate-optimisation")
    print("     business. No pricing tactic rescues 25K sessions.")
    print("  2. Subscriptions dominate above ~100K sessions — the source report's")
    print("     central instinct is right — but they arrive last, not first.")
    print("  3. Affiliate underperforms intuition because of 48h FIRST-click:")
    print("     try --first-click-win-rate 1.0 to see the gap a plan creates by")
    print("     ignoring the term.")
    print("  4. Pokemon TCG Pocket traffic earns $0 affiliate. Model it with")
    print("     --digital-share 0.8 to see what a Pocket-led strategy is worth.")
    print()


if __name__ == "__main__":
    main()

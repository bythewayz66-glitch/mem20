# Pricing Decision — Ship the v3 House Ladder as Four Tier SKUs

**Date:** 2026-11-25
**Decided by:** the agents, under Jesse's delegation ("you guys set the prices")
**Resolves:** `docs/pricing/TIER_SHIPPING_AUDIT.md` §6 — the business must pick
between shipping the tier ladder and retiring it.
**Status:** decided and implemented. The ladder is shipped; see the mapping below.

## Decision

1. **Ship the ladder.** The four documented tiers are now four sellable SKUs
   in the shop, each with a real live-mode Stripe Price.
2. **The v3 house ladder is authoritative:** Team $6,000 / Business $18,000 /
   Scale $36,000 / Enterprise $80,000 per year. Source:
   `docs/finance/inputs.json` → `tier_ladder`, reconciled in
   `docs/pricing/RECONCILIATION_NOTE.md` (blends exactly to the $14,000
   blended ACV at 72/12/12/4).
3. **The other two ladders are retired as price books** (see §2). They remain
   in their documents as labelled proposals/models; they are not sellable
   prices and no SKU is priced from them.

## 1. Why the v3 house ladder

It is the only one of the three ladders that is all of these at once:

- **Exact amounts for every tier.** No ranges, no open-ended "+" tiers.
- **Derived, not asserted.** `RECONCILIATION_NOTE.md` §2 inverts the blend:
  given the four prices and the $14,000 target, 72/12/12/4 is the only share
  vector that closes (each share re-derived to four decimal places).
- **The held house figure survives it.** The ladder blends to exactly
  $14,000 in percentage space, and $14,000 sits inside the admissible
  integer-book band ($13,983.33–$14,233.33). SOM $1.68M at 120 logos holds.
- **Carried across the repo.** The same four prices appear in the finance
  model, the deck, the tier-sensitivity study and the reconciliation note —
  it is the house ladder, not one document's proposal.

## 2. Why the other ladders were not picked

### v4 draft (`docs/pricing/pricing_model_v4.py`) — not a price book

- The higher tiers are labelled in the file itself as **"illustrative"**
  planning assumptions, and Scale is dropped entirely.
- Only the $2,400 Starter tier is modelled as a real price, and it is modelled
  to measure P&L drag under a 15% volume cap — a planning exercise, not a
  billing ladder.
- Its blend does not reproduce the held $14,000 blended ACV, so adopting it
  would break the house figure the business holds by fiat. Repricing the entry
  tier is the load-bearing decision (RECONCILIATION_NOTE.md §3: Team is 18×
  more leveraged on the blend than Enterprise), and no evidence in the repo
  justifies moving it from $6,000 to $2,400.

### Sales one-pager (`docs/gtm/mem20-sales-one-pager.md`) — proposals, not prices

- The document itself says *"no price list exists in the repo; these are GTM
  proposals, label them as such."*
- It commits the exact failure the pricing discipline exists to prevent: it
  quotes the **$14,000 blended ACV itself as a sellable tier price**
  ("Supported $14,000/yr — the blended ACV anchor"). $14,000 is a portfolio
  average, never a price — see RECONCILIATION_NOTE.md §6, "Never quote
  $14,000 to a customer."
- Compliance is a **range** ($28,000–$42,000), so no single price can be taken
  from it without inventing one. Platform is open-ended ($56,000+).
- Its mix cannot reproduce the $14,000 blend (TIER_SHIPPING_AUDIT.md §4.1):
  a plausible 40/40/25/15 mix blends to $18,958.33, +35.4% above the house
  figure, with no pricing decision having been made.

## 3. Tier → SKU mapping

The tiers ship as four **new** SKUs in a new `tiers` group — they are not
mapped onto the existing à-la-carte SKUs, because no document prices any of
those SKUs and assigning a tier price to an unrelated service (e.g. $80,000
for Migration because Enterprise is $80,000) would invent a price. The tier
products are the tiers themselves.

| Tier | SKU id | Stripe Product | Stripe Price (live) | Amount |
|---|---|---|---|---:|
| Team | `team` | `prod_VhK7fc2DU09VYL` | `price_1UfvTjHgWvC5wL6JxxeNkxFH` | $6,000/yr |
| Business | `business` | `prod_VhK78wrQ576Uhd` | `price_1UfvTkHgWvC5wL6J0tn8EQWa` | $18,000/yr |
| Scale | `scale` | `prod_VhK7l1DoLlszUh` | `price_1UfvTqHgWvC5wL6Jbqef9C0K` | $36,000/yr |
| Enterprise | `enterprise` | `prod_VhK7DFLicVwWXM` | `price_1UfvTrHgWvC5wL6JVLhDzDyc` | $80,000/yr |

Stripe account: "Jesse Moore" (`acct_1U4WpQHgWvC5wL6J`), live mode. All four
Prices are `one_time`, USD, active, with `lookup_key` equal to the SKU id and
`metadata` carrying `sku_id`, `tier` and `pricing_ladder: v3-house`.

Each tier SKU in `mem20shopz/mem20shopz/catalog.json` carries its Stripe
`price_id` and the matching `amount_cents`, plus a `tier` field naming the
ladder tier — that field is what `docs/pricing/audit_tier_shipping.py`
detects as the shipped counterpart, so the audit now passes.

**Why `one_time`, not a subscription.** The tiers are annual prices. The
catalog's subscription label renders as "$X/mo", which would misstate an
annual charge as a monthly one, and nothing in the repo documents a
recurring-billing commitment for these tiers. A tier is bought as one annual
term and renews by repurchase, not auto-billing. The SKU descriptions say
"per year" so the storefront cannot be misread. If the business later wants
auto-renewing annual subscriptions, that is a separate, deliberate change to
both the Stripe Prices (recurring yearly) and the catalog's label.

**Tax.** No `tax_behavior` is set on these Prices and no `tax_code` on the
Products: Stripe Tax is not configured on this account (Tax Settings status
`pending`, head office missing, no default tax behaviour), so no tax is
collected. Nothing here guesses a tax code. Setting up Stripe Tax is a
separate decision for Jesse.

## 4. What was deliberately left unpriced, and why

All 15 à-la-carte SKUs stay unpriced (`price_id` empty, `amount_cents`
null), exactly as before:

```
foundation-single  fleet-starter     hosting-monthly   ops-audit
control-plane-setup oncall-monthly    memory-tiering    agent-fleet-build
intelligence-monthly asset-pipeline   game-vertical     studio-monthly
migration          training          priority-support-monthly
```

A repo-wide search found **no documented price for any of them** — no dollar
figure attached to any SKU name anywhere outside the tier ladder. Pricing
them would mean inventing numbers, which the catalog's own header forbids
("Nothing here guesses a price") and this decision was told not to do. They
become sellable only when a real price for each one is documented and a real
Stripe Price exists for it — same bar the tiers just met.

**$14,000 is not a price and is not sold.** It remains the blended ACV: a
portfolio average across the four tiers at 72/12/12/4. No SKU carries it.

## 5. What changed to implement this

- Stripe (live): 4 Products + 4 Prices, table in §3.
- `mem20shopz/mem20shopz/catalog.json`: 4 new tier SKUs in a new `tiers`
  group, each with `price_id` + `amount_cents`; 15 à-la-carte SKUs untouched.
- `mem20shopz/mem20shopz/catalog.py`: sixth group `tiers`; `Sku` carries the
  `tier` field through to `/api/catalog`.
- `mem20shopz/mem20shopz/wiring.py`: `tiers` maps to the `platform` family
  (a tier buys the mem20 platform at that level).
- `mem20shopz/tests/`: group-count and priced-state assertions updated to the
  new reality; new test asserts the four tier SKUs carry exactly the ladder
  amounts and the fifteen à-la-carte SKUs carry none.
- `mem20shopz/README.md`: catalog section updated (4 priced, 15 unpriced).
- `docs/pricing/audit_tier_shipping.py`: exits 0 — every documented tier now
  has a shipped counterpart.

## 6. What this does NOT do

- **Live purchasing is not turned on by this decision.** The priced SKUs are
  buyable through the shop's pre-existing Checkout endpoint once the deployed
  service reads this catalog, which is inherent to wiring a `price_id` in —
  but no checkout flow is promoted, no auto-provisioning is enabled, and
  provisioning stays in dry-run (verified: `GET /api/webhooks/status`
  reports dry-run). Enabling real charges/provisioning is a separate step
  for Jesse.
- **No entitlement or SLA text was invented for the tiers.** The repo
  documents tier prices and mix shares, not per-tier entitlements. The tier
  SKU descriptions and features describe the purchase (annual term, ladder
  tier), not service levels nobody wrote down. If Jesse wants per-tier
  entitlements (SLAs, support scope), those need to be written first, then
  the SKUs updated — not the other way round.

## 7. Verification

- `python3 docs/pricing/audit_tier_shipping.py` → exit 0 after this change.
- `python3 -m pytest mem20shopz/tests -q` → green (see commit message).
- Live shop: `https://shop.mem20.com/api/catalog` shows the four tier SKUs
  configured with the amounts in §3; the fifteen à-la-carte SKUs still show
  "price not set".

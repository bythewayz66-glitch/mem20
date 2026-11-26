# Pricing — `docs/pricing/`

Entry point for the `docs/pricing/` documentation set. **12 tracked file(s).**

## Contents

- [`PRICING_DECISION_2026-11-25.md`](PRICING_DECISION_2026-11-25.md)
- [`RECONCILIATION_NOTE.md`](RECONCILIATION_NOTE.md)
- [`TIER_SHIPPING_AUDIT.md`](TIER_SHIPPING_AUDIT.md)
- [`audit_acv_consistency.py`](audit_acv_consistency.py)
- [`audit_pricing_docs.py`](audit_pricing_docs.py)
- [`audit_tier_shipping.py`](audit_tier_shipping.py)
- [`pricing_model_v4.py`](pricing_model_v4.py)
- [`tier-price-derivation.csv`](tier-price-derivation.csv)
- [`tier-sensitivity.csv`](tier-sensitivity.csv)
- [`tier-sensitivity.md`](tier-sensitivity.md)
- [`tier_price_derivation.py`](tier_price_derivation.py)
- [`tier_sensitivity_model.py`](tier_sensitivity_model.py)

## Conventions

- Every file in this directory is linked from this index; add a row when you add a file.
- Dated records (audits, ops logs, verification runs) are append-only — do not rewrite
  historical numbers in them; correct the live docs instead.
- Tool/domain counts in this tree must match the live surface. Derive, never hand-count:
  `python3 web/scripts/extract-tools.py --root . --out /tmp/tools.json`

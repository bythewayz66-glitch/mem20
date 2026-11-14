# mem20globalcapabilitymarketplacez — Global Capability Marketplace (RM-218, #318)

**Outcome:** distribute portable capabilities, models, connectors, workflows, and microapps with instant trials.  
**Breakthrough:** FreeStack becomes known as the place where executable AI abilities are exchanged.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `match` operation is backward-compatible for generic demand/supply and provides meaningful marketplace composition for listings/requirements.

## Legacy domain API (preserved)
`list_capability(seller,cap,price)`, `search_marketplace(listings,query)`, `match(listings,requirement)`, `transaction(listing,buyer)`, `marketplace_health(listings)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Marketplace role |
|---|---|---|
| `mem20offerassemblyfabricz` | `create_offer`,`add_component`,`price_offer`,`publish` | assembles and publishes priced offers |
| `mem20offergenomeenginez` | `create_genome`,`mutate`,`fitness` | optimizes offer fitness |
| `mem20instantappsynthesisz` | `validate_spec`,`scaffold` | synthesizes instant-trial scaffolds |
| `mem20securecomputecapsulesz` | `create_capsule`,`capsule_health` | validates secure trial execution |
| `mem20runtimepromptoptimizerz` | `tokenize`,`compress`,`optimize` | optimizes listing discovery queries |
| `mem20studioz` | `remix_variants`,`transform_asset` | produces capability/asset variants |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20globalcapabilitymarketplacez simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20globalcapabilitymarketplacez execute '{"listings":[{"seller":"s1","capability":"workflow ai","price":10,"available":true}],"requirement":{"capability":"workflow"},"buyer":"b1","query":"workflow"}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20globalcapabilitymarketplacez serve --port 8798
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20globalcapabilitymarketplacez/tests mem20globalcapabilitymarketplacez/mem20globalcapabilitymarketplacez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20globalcapabilitymarketplacez
```

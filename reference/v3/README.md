# reference/v3 — cached inputs for mem20-scale-corpus-v3

The generator reads **only** from this directory. It never touches the network,
so a re-run is reproducible and cannot be broken by an upstream outage.

Fetch once:

```bash
cd reference/v3

curl -sL -o periodic-table.json \
  https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json

curl -sL -o iso-3166.json \
  https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json

curl -sL -o mime-db.json \
  https://raw.githubusercontent.com/jshttp/mime-db/master/db.json

curl -sL -o countries-mledoze.json \
  https://raw.githubusercontent.com/mledoze/countries/master/countries.json

curl -sL -o UnicodeData.txt \
  https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt

curl -sL -o cities15000.zip https://download.geonames.org/export/dump/cities15000.zip
unzip -o cities15000.zip cities15000.txt
```

`cities15000.zip` is kept alongside the extracted `cities15000.txt` so the
provenance of the tab-separated file is unambiguous.

Every file here is hashed into `benchmarks/corpora/v3/manifest.json` under
`reference_cache`. A corpus generated from a different cache is a different
corpus, even at the same seed — pin the cache, not just the seed.

| file | rows | used for |
|---|---|---|
| `periodic-table.json` | 119 elements | atomic number, mass, phase, category, discoverer, density, electron configuration, melting/boiling point, shells |
| `iso-3166.json` | 249 countries | alpha-2, alpha-3, numeric, region, sub-region, intermediate region |
| `mime-db.json` | ~2,600 media types | charset, compressibility, extensions, source, subtype |
| `countries-mledoze.json` | 250 countries | capital, TLD, currency, official language, calling code, area, borders |
| `UnicodeData.txt` | ~40,000 named code points | character name, general category, bidi class, decimal value, combining class |
| `cities15000.txt` | 34,162 cities | population, timezone, coordinates, country |

All six are public, key-free, and tolerate automated fetching. CourtListener was
avoided deliberately: its REST API returns HTTP 429 on every page from a
sandbox IP and cannot be worked around.

# Reference data for mem20-scale-corpus-v2

Cached offline so corpus generation does not depend on the network.

Sources (fetched 2026-10-30):

- periodic-table.json ← https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json
- iso-3166.json ← https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json
- mime-db.json ← https://raw.githubusercontent.com/jshttp/mime-db/master/db.json

Used by `mem20benchmarkz/mem20benchmarkz/scale_corpus.py`.

Corpus size: **2,000 records** (700 grounded / 650 ungrounded / 650 false) + 250 probes.
Graph (from latest run): **654 entities / 3,601 edges**.

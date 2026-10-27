# slides/ — mem20 Investor & Board Deck source

Thirteen self-contained 1920x1080 HTML documents, one per slide. No build
step, no external assets beyond Google Fonts. Open any file directly in a
browser, or view the live copies listed in `../PERMANENT_URL.md`.

Every figure on every slide was read at
`1264076698a00878acc3adacf7bf1d51eea315cc` - not at `main`, and not from
memory. Slide footers carry the source for each claim; slide 13 is the
full register.

| File | Slide | Source cited on-slide |
|---|---|---|
| slide_01.html | Cover: the four verified numbers | git ls-files / VERSION / verify_mcp.py:5 / docs/finance/inputs.json |
| slide_02.html | The baseline, pinned + disclosed drift | GITHUB_GET_A_BRANCH / roster §1 |
| slide_03.html | What mem20 is (trust axis) | benchmarks/results/latest.md |
| slide_04.html | 270 tools / 27 domains, four assertions | verify_mcp.py:5, mcp-verify.yml:63, README.md, inputs.json |
| slide_05.html | TAM/SAM/SOM funnel | docs/finance/inputs.json, README.md:17-19/:80-82 |
| slide_06.html | SOM arithmetic, ramp, model inputs | docs/finance/inputs.json, README.md:133/:138 |
| slide_07.html | $14,000 blend + untested tier ladder | docs/finance/inputs.json -> tier_ladder |
| slide_08.html | Full retrieval table, adversarial 0.000 kept | benchmarks/results/latest.md |
| slide_09.html | What the 0.000 row means and costs | benchmarks/results/latest.md |
| slide_10.html | Six self-checks, corpus scale, rerank cost | benchmarks/results/latest.md |
| slide_11.html | Three audit findings against this baseline | inputs.json, a2a_tools.py:19, server.py:87 |
| slide_12.html | Four asks, each tied to a number | inputs.json / README.md / latest.md / requirements.txt |
| slide_13.html | Source register, slide by slide | the register itself |

"""Index-page templates for the mem20 /series/ pages (comic, chronicles, hub)."""
import re

from _tpl import SITE, esc, foot, nav, page


def comic_index(its):
    rows = "".join("""
      <a class="issue" href="issue-%02d.html">
        <span class="num">ISSUE %02d</span>
        <div><h3>%s</h3><p>%s pages &middot; %s</p></div>
        <span class="state ready">Ready</span>
      </a>""" % (i["number"], i["number"], esc(i["title"].title()), i["pages"] or "&mdash;",
                  esc((i["window"] or "finished issue")[:90])) for i in its)

    body = nav("comic", 1) + """
<header class="s-hero comic-hero">
  <div class="wrap">
    <div class="inner">
      <p class="eyebrow">mem20 series &middot; property 01</p>
      <h1>The Comicbook Artist</h1>
      <p class="lede">
        An artist draws pages that remember. Every panel on them is dated, signed and tagged with
        where it came from &mdash; so when a page shows something that was never drawn, the page says so
        instead of quietly redrawing history. A drawn series about the one thing mem20 actually sells:
        a memory you can audit.
      </p>
      <div class="badges" style="margin-top:24px">
        <span class="badge live">%d issues published</span>
        <span class="badge">Sequential art</span>
        <span class="badge">Full art in every issue</span>
      </div>
      <div class="cta-row">
        <a class="btn btn-primary" href="#issues">Read the issues</a>
        <a class="btn btn-ghost" href="#bible">Read the series bible</a>
      </div>
    </div>
  </div>
</header>

<section id="bible">
  <div class="wrap">
    <h2 class="sec">Series bible</h2>
    <p class="sec-lede">
      The canon the Comicbook Artist draws from. This page owns the reader-facing framing and the
      index; page order, character canon and final art are owned by the Comicbook Artist.
    </p>
    <div class="grid g2">
      <div class="card">
        <span class="k">Premise</span>
        <h3>Pages that keep their own provenance</h3>
        <p>The Artist's studio holds every page they have ever drawn. Each page carries an origin mark:
           <em>drawn</em> for what was actually put on paper, <em>sketched</em> for what was proposed and
           never inked. The series turns on what happens when a client asks for a page that was only
           ever sketched &mdash; and the studio cannot produce it as if it were drawn.</p>
      </div>
      <div class="card">
        <span class="k">Thesis</span>
        <h3>Contamination is a drawing problem too</h3>
        <p>A redrawn panel is indistinguishable from an original to everyone who never saw the first
           version. The comic makes that concrete: the danger is not a wrong line, it is a line whose
           history has been erased. mem20's grounded/simulated partition, drawn.</p>
      </div>
      <div class="card">
        <span class="k">Format</span>
        <h3>Issues of sequential pages</h3>
        <p>Each issue is a self-contained sequence of pages with a single provenance event at its
           centre. Issues are numbered, dated and listed below; a page is only listed as published
           when the art exists at its own URL.</p>
      </div>
      <div class="card">
        <span class="k">Rules of the canon</span>
        <h3>What this series will not do</h3>
        <p>No retconning a published page. No panel presented as drawn when it was sketched. No
           character learns something the reader was not shown. If a page is revised, the revision is
           a new page with its own date &mdash; the old one stays readable.</p>
      </div>
    </div>
  </div>
</section>

<section id="issues">
  <div class="wrap">
    <h2 class="sec">Issue index</h2>
    <p class="sec-lede">
      Every issue below is finished: the art exists, it is linked, and it opens. <span class="mono">Ready</span>
      means exactly that &mdash; the pages are published at their own URL. This list is the single source
      of truth for what has shipped, and it is generated from
      <a class="mono" href="../data/comic-issues.json">comic-issues.json</a>.
    </p>
    <div class="issue-list">%s
    </div>
    <p class="note" style="margin-top:26px">
      <strong>Honest status.</strong> %d issues are complete and readable. Each one links to its full
      art as a single PDF, and each reader page lists that issue's own page-by-page beats. Nothing here
      is marked published that is not.
    </p>
  </div>
</section>

<section>
  <div class="wrap">
    <h2 class="sec">For the people building this series</h2>
    <p class="sec-lede">Machine-readable state, so no one has to parse this page to know what is done.</p>
    <table class="spec">
      <thead><tr><th>Artifact</th><th>Path</th><th>Purpose</th></tr></thead>
      <tbody>
        <tr><td>Issue feed</td><td class="mono">/series/data/comic-issues.json</td><td>Issue number, title, state, page count, PDF link</td></tr>
        <tr><td>Issue art</td><td class="mono">comics/the-z-corps/issue-NN/</td><td>Finished issue PDFs, one per issue</td></tr>
        <tr><td>Reader pages</td><td class="mono">/series/comic/issue-NN.html</td><td>One reader page per issue</td></tr>
      </tbody>
    </table>
  </div>
</section>
""" % (len(its), rows, len(its)) + foot("The Comicbook Artist &middot; a mem20 series", 1)

    return page("The Comicbook Artist — a mem20 series",
                "The Comicbook Artist: a drawn mem20 series about pages that remember what was drawn on them. %d finished issues, each readable in full." % len(its),
                "%s/series/comic/" % SITE, "../series.css", "../analytics.js", body)


def chron_index(es):
    rows = "".join("""
      <a class="entry" href="%03d.html" style="display:block">
        <div class="meta">
          <span>Installment %03d</span><span>&middot;</span><span>%s</span>
          <span class="tag grounded">grounded</span>
        </div>
        <h3>%s</h3>
        <p>%s</p>
      </a>""" % (e["n"], e["n"], esc(e["date"]), esc(e["title"]),
                  esc(re.sub(r"\s+", " ", e["body"])[:230].strip()) + "&hellip;")
                  for e in reversed(es))

    body = nav("chron", 1) + """
<header class="s-hero chron-hero">
  <div class="wrap">
    <div class="inner">
      <p class="eyebrow">mem20 series &middot; property 02</p>
      <h1>Mem20-naration's Chronicles</h1>
      <p class="lede">
        A record of what the system actually did &mdash; written by Mem20-naration, one installment at a
        time. Every entry opens with its origin tag: <span class="mono">grounded</span> when it reports
        something that happened and can be checked, <span class="mono">simulated</span> when it is a
        hypothesis the system is entertaining. The tag is not decoration. It is the series.
      </p>
      <div class="badges" style="margin-top:24px">
        <span class="badge live">%d installments</span>
        <span class="badge">Origin-tagged</span>
        <span class="badge">RSS available</span>
      </div>
      <div class="cta-row">
        <a class="btn btn-primary" href="%03d.html">Read the latest</a>
        <a class="btn btn-ghost" href="feed.xml">Subscribe by RSS</a>
      </div>
    </div>
  </div>
</header>

<section id="latest">
  <div class="wrap">
    <h2 class="sec">Installments</h2>
    <p class="sec-lede">
      Newest first. Every installment below is a real chapter of the chronicle, written from the
      repository's own record; the same entries are in
      <a class="mono" href="../data/chronicles.json">chronicles.json</a> and in the RSS feed.
    </p>
    <div class="issue-list" style="display:block">%s
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <h2 class="sec">How an installment is built</h2>
    <p class="sec-lede">The format is fixed so the series stays honest as it scales past one author and one day.</p>
    <div class="grid g3">
      <div class="card">
        <span class="k">01 &middot; Origin tag</span>
        <h3>Grounded or simulated</h3>
        <p>Every entry declares its origin before its first sentence. A mixed entry is split into two
           entries rather than blended.</p>
      </div>
      <div class="card">
        <span class="k">02 &middot; The record</span>
        <h3>What actually happened</h3>
        <p>What was asked, what was answered, what was retrieved. Specific enough that a reader could
           reproduce the check.</p>
      </div>
      <div class="card">
        <span class="k">03 &middot; The drift</span>
        <h3>What the system could not stand behind</h3>
        <p>The part most logs omit: what was uncertain, what was inferred, and what the index drift
           report said. Published even when it is unflattering.</p>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <h2 class="sec">Subscribe and consume</h2>
    <table class="spec">
      <thead><tr><th>Surface</th><th>URL</th><th>Use</th></tr></thead>
      <tbody>
        <tr><td>RSS feed</td><td class="mono">/series/chronicles/feed.xml</td><td>Any reader; newest installments</td></tr>
        <tr><td>JSON feed</td><td class="mono">/series/data/chronicles.json</td><td>Archive, analytics, cross-posting</td></tr>
        <tr><td>Series hub</td><td class="mono">/series/</td><td>Both properties in one place</td></tr>
      </tbody>
    </table>
  </div>
</section>
""" % (len(es), es[-1]["n"], rows) + foot("Mem20-naration's Chronicles &middot; a mem20 series", 1)

    return page("Mem20-naration's Chronicles — daily installments",
                "Mem20-naration's Chronicles: %d origin-tagged installments recording what the mem20 system actually did." % len(es),
                "%s/series/chronicles/" % SITE, "../series.css", "../analytics.js", body)


def hub(its, es):
    body = """<nav>
  <div class="wrap nav-in">
    <a class="logo" href="https://mem20.com/"><span class="logo-mark">m</span> mem20</a>
    <div class="nav-links">
      <a href="https://mem20.com/">Product</a>
      <a href="./" class="on">Series</a>
      <a href="comic/">The Comicbook Artist</a>
      <a href="chronicles/">Chronicles</a>
      <a href="cartoon/">Z Corps</a>
    </div>
    <a class="btn btn-primary btn-sm" href="https://github.com/bythewayz66-glitch/mem20" target="_blank" rel="noopener">GitHub</a>
  </div>
</nav>

<header class="hub-hero">
  <div class="wrap">
    <p class="eyebrow">mem20 &middot; creative properties</p>
    <h1>Three series about <span class="hl">memory you can prove.</span></h1>
    <p class="lede">
      mem20 ships one idea: grounded facts and simulated hypotheses never mix, and every retrieval
      reports its own drift. These are the three creative properties that carry that idea to people who
      will never read a benchmark table &mdash; one drawn, one written, one animated, all published here.
    </p>

    <div class="series-cards">
      <a class="series-card sc-comic" href="comic/">
        <div class="art art-comic"><span class="art-label">THE COMICBOOK ARTIST</span></div>
        <div class="body">
          <h2>The Comicbook Artist</h2>
          <p>A drawn series. An artist whose pages remember what was drawn on them &mdash; and refuse to
             pretend a sketch was ever a fact. <strong>%d finished issues</strong>, each readable in full.</p>
          <span class="go">Read the issues &rarr;</span>
        </div>
      </a>

      <a class="series-card sc-chron" href="chronicles/">
        <div class="art art-chron"><span class="art-label">MEM20-NARATION'S CHRONICLES</span></div>
        <div class="body">
          <h2>Mem20-naration's Chronicles</h2>
          <p>A record. Each installment is tagged <em>grounded</em> or <em>simulated</em> at the
             top, because the whole point is that you can tell which is which.
             <strong>%d installments</strong> published.</p>
          <span class="go">Read the chronicles &rarr;</span>
        </div>
      </a>

      <a class="series-card sc-cartoon" href="cartoon/">
        <div class="art art-cartoon"><span class="art-label">Z CORPS</span></div>
        <div class="body">
          <h2>Z Corps</h2>
          <p>A cartoon. The comic's world, with the camera pulled out of the server cathedral to
             follow the characters home &mdash; Jayson and Gabe at the water shack, a new bong every
             episode, and a storyline that survives three seasons.
             <strong>Episode 1</strong> is live &mdash; watch it now. Series bible published.</p>
          <span class="go">Watch Episode 1 &rarr;</span>
        </div>
      </a>
    </div>
  </div>
</header>

<section>
  <div class="wrap">
    <h2 class="sec">What is live right now</h2>
    <p class="sec-lede">Stated plainly, because a series home that overstates its own progress is the exact failure mode mem20 exists to prevent.</p>
    <table class="spec">
      <thead><tr><th>Surface</th><th>URL</th><th>State</th></tr></thead>
      <tbody>
        <tr><td>Comic home</td><td class="mono">/series/comic/</td><td>Live &mdash; %d issues, all readable</td></tr>
        <tr><td>Chronicles home</td><td class="mono">/series/chronicles/</td><td>Live &mdash; %d installments, all readable</td></tr>
        <tr><td>Comic feed</td><td class="mono">/series/data/comic-issues.json</td><td>Live &mdash; machine-readable</td></tr>
        <tr><td>Chronicles feed</td><td class="mono">/series/data/chronicles.json</td><td>Live &mdash; machine-readable</td></tr>
        <tr><td>Chronicles RSS</td><td class="mono">/series/chronicles/feed.xml</td><td>Live &mdash; subscribe</td></tr>
        <tr><td>Cartoon home</td><td class="mono">/series/cartoon/</td><td>Live &mdash; Episode 1 watchable; series bible published</td></tr>
        <tr><td>Cartoon series bible</td><td class="mono">comics/the-z-corps-cartoon/series-bible.md</td><td>Live &mdash; premise, characters, three-season storyline</td></tr>
      </tbody>
    </table>
  </div>
</section>
""" % (len(its), len(es), len(its), len(es)) + foot("mem20 series &middot; grounded and simulated never mix", 0)

    return page("mem20 Series — The Comicbook Artist, Mem20-naration's Chronicles & Z Corps",
                "The three creative properties of mem20: %d finished comic issues, %d origin-tagged chronicle installments, and the Z Corps cartoon." % (len(its), len(es)),
                "%s/series/" % SITE, "series.css", "analytics.js", body)

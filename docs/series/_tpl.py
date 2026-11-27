"""HTML templates for the mem20 /series/ pages.

Kept separate from _build.py so each file stays small enough to commit through
the GitHub contents API. _build.py owns the corpus and the markdown; this module
owns the markup.
"""
import html

SITE = "https://mem20.com"
esc = lambda s: html.escape(str(s), quote=True)

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canon}">
<link rel="canonical" href="{canon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css}">
<script src="{js}" defer></script>
</head>
<body>
"""

NAV = """<nav>
  <div class="wrap nav-in">
    <a class="logo" href="https://mem20.com/"><span class="logo-mark">m</span> mem20</a>
    <div class="nav-links">
      <a href="{hub}">Series</a>
      <a href="{comic}"{on_comic}>The Comicbook Artist</a>
      <a href="{chron}"{on_chron}>Chronicles</a>
    </div>
    <a class="btn btn-primary btn-sm" href="{cta_href}">{cta}</a>
  </div>
</nav>
"""

FOOT = """<footer>
  <div class="wrap foot-in">
    <div class="foot-links">
      <a href="{hub}">All series</a>
      <a href="{comic}">The Comicbook Artist</a>
      <a href="{chron}">Chronicles</a>
      <a href="{toon}">Z Corps</a>
      <a href="https://mem20.com/">mem20.com</a>
    </div>
    <p class="foot-note">
      {note}<br>
      Published from <span class="mono">docs/series/</span> on GitHub Pages
    </p>
  </div>
</footer>
</body>
</html>
"""


def nav(kind, depth):
    up = "../" * depth
    return NAV.format(
        hub=up or "./", comic=up + "comic/", chron=up + "chronicles/",
        on_comic=' class="on"' if kind == "comic" else "",
        on_chron=' class="on"' if kind == "chron" else "",
        cta_href="feed.xml" if kind == "chron" else "https://github.com/bythewayz66-glitch/mem20",
        cta="RSS" if kind == "chron" else "GitHub")


def foot(note, depth):
    up = "../" * depth
    return FOOT.format(hub=up or "./", comic=up + "comic/", chron=up + "chronicles/", toon=up + "cartoon/", note=note)


def page(title, desc, canon, css, js, body):
    return HEAD.format(title=esc(title), desc=esc(desc), canon=canon, css=css, js=js) + body


def comic_page(it, prev, nxt, inline):
    n = it["number"]
    mb = it["size"] / 1048576.0
    rows = []
    if it["pages"]:
        rows.append(("Pages", "%d" % it["pages"]))
    rows.append(("File size", "%.1f MB" % mb))
    if it["window"]:
        rows.append(("Window covered", it["window"]))
    if it["source"]:
        rows.append(("Source", it["source"]))
    rows.append(("Artifact", it["rel"]))
    spec = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), inline(v)) for k, v in rows)

    beat_html = ""
    if it["beats"]:
        cards = "".join(
            '<div class="pg"><span class="n">PAGE %02d</span><span class="b">%s</span></div>'
            % (p, inline(lbl)) for p, lbl in it["beats"])
        beat_html = ('<section><div class="wrap reader"><h2>Page by page</h2>'
                     '<p>The beats below are the issue\'s own shooting script, in page order. '
                     'The art for every one of them is in the PDF above &mdash; this list is the '
                     'index into it.</p><div class="pages">%s</div></div></section>' % cards)

    pg = ['<div class="pager">']
    pg.append('<a href="issue-%02d.html">&larr; Issue %02d &middot; %s</a>'
              % (prev["number"], prev["number"], esc(prev["title"].title())) if prev else "<span></span>")
    pg.append('<a href="issue-%02d.html">Issue %02d &middot; %s &rarr;</a>'
              % (nxt["number"], nxt["number"], esc(nxt["title"].title())) if nxt else "<span></span>")
    pg.append("</div>")

    body = nav("comic", 1) + """
<header class="s-hero comic-hero">
  <div class="wrap">
    <div class="inner">
      <p class="eyebrow">The Comicbook Artist &middot; Issue %02d</p>
      <h1>%s</h1>
      <div class="badges" style="margin-top:20px">
        <span class="badge live">Ready &mdash; art published</span>
        <span class="badge">%s pages</span>
        <span class="badge">Sequential art</span>
      </div>
      <div class="cta-row">
        <a class="btn btn-primary" href="%s" target="_blank" rel="noopener">Open the issue (PDF)</a>
        <a class="btn btn-ghost" href="./">All issues</a>
      </div>
    </div>
  </div>
</header>

<section>
  <div class="wrap reader">
    <div class="cover">
      <div class="bar">
        <span class="t">THE Z CORPS #%02d &mdash; %s</span>
        <span class="m">%s &middot; %.1f MB</span>
      </div>
    </div>
    <p>This issue is finished and published. The complete art is a single PDF, linked above and
       below; it opens in the browser or downloads, and needs no account.</p>
    <p><a class="btn btn-ghost btn-sm" href="%s" target="_blank" rel="noopener">Read Issue %02d &rarr;</a></p>
    <h2>What this issue is</h2>
    <table class="spec"><tbody>%s</tbody></table>
  </div>
</section>
%s
<section><div class="wrap reader">%s</div></section>
""" % (n, esc(it["title"].title()), it["pages"] or "&mdash;", it["url"],
       n, esc(it["title"].title()), esc(it["rel"]), mb, it["url"], n, spec,
       beat_html, "".join(pg)) + foot("The Comicbook Artist &middot; a mem20 series", 1)

    return page("Issue %02d: %s — The Comicbook Artist" % (n, it["title"].title()),
                "Issue %02d of The Comicbook Artist, %s. %s pages of finished sequential art, published in full."
                % (n, it["title"].title(), it["pages"] or "The"),
                "%s/series/comic/issue-%02d.html" % (SITE, n),
                "../series.css", "../analytics.js", body)


def chron_page(e, prev, nxt, body_html):
    n = e["n"]
    words = e["words"]
    pg = ['<div class="pager">']
    pg.append('<a href="%03d.html">&larr; %03d &middot; %s</a>'
              % (prev["n"], prev["n"], esc(prev["title"][:48])) if prev else "<span></span>")
    pg.append('<a href="%03d.html">%03d &middot; %s &rarr;</a>'
              % (nxt["n"], nxt["n"], esc(nxt["title"][:48])) if nxt else "<span></span>")
    pg.append("</div>")

    body = nav("chron", 1) + """
<header class="s-hero chron-hero">
  <div class="wrap">
    <div class="inner">
      <p class="eyebrow">Mem20-naration's Chronicles &middot; Installment %03d</p>
      <h1>%s</h1>
      <div class="badges" style="margin-top:20px">
        <span class="badge">%s</span>
        <span class="tag grounded">grounded</span>
        <span class="badge">%s words</span>
      </div>
      <div class="cta-row">
        <a class="btn btn-ghost" href="./">All installments</a>
        <a class="btn btn-ghost" href="feed.xml">RSS</a>
      </div>
    </div>
  </div>
</header>

<section>
  <div class="wrap reader">
    <p class="note"><strong>Origin: grounded.</strong> This installment reports what the repository
      actually did in its window. Every figure in it was measured against the tree, and the chapter
      names the file or command it came from. Where it could not stand behind something, it says so
      in its own text rather than smoothing it over.</p>
    %s
    %s
  </div>
</section>
""" % (n, esc(e["title"]), esc(e["date"]), words, body_html, "".join(pg)) \
        + foot("Mem20-naration's Chronicles &middot; a mem20 series", 1)

    return page("%03d: %s — Mem20-naration's Chronicles" % (n, e["title"]),
                "Chronicle installment %03d, %s. %s" % (n, e["date"], e["title"]),
                "%s/series/chronicles/%03d.html" % (SITE, n),
                "../series.css", "../analytics.js", body)

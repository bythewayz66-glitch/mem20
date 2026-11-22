"""Small markdown -> HTML converter for the chronicle bodies.

Split out of _build.py to keep each file small enough to commit through the
GitHub contents API. Handles the subset the serials actually use: headings,
paragraphs, bullet and numbered lists, tables, blockquotes, fenced code,
rules and inline code/bold/italic/links.
"""
import html
import re

esc = lambda s: html.escape(str(s), quote=True)

CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITAL = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BLOCK = re.compile(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||-{3,}$)")


def inline(t):
    o = esc(t)
    o = CODE.sub(lambda m: "<code>%s</code>" % m.group(1), o)
    o = BOLD.sub(lambda m: "<strong>%s</strong>" % m.group(1), o)
    o = ITAL.sub(lambda m: "<em>%s</em>" % m.group(1), o)
    return LINK.sub(lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), o)


def md(text):
    L = text.split("\n")
    out, i, n = [], 0, len(L)
    while i < n:
        s = L[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not L[i].strip().startswith("```"):
                buf.append(L[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % esc("\n".join(buf)))
            continue
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            out.append("<hr>")
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lv = min(len(m.group(1)) + 1, 6)      # the page owns h1
            out.append("<h%d>%s</h%d>" % (lv, inline(m.group(2)), lv))
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", L[i + 1].strip()):
            head = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and L[i].strip().startswith("|"):
                rows.append([c.strip() for c in L[i].strip().strip("|").split("|")])
                i += 1
            t = ['<div class="tbl"><table class="spec"><thead><tr>']
            t += ["<th>%s</th>" % inline(c) for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if s.startswith(">"):
            buf = []
            while i < n and L[i].strip().startswith(">"):
                buf.append(L[i].strip().lstrip(">").strip())
                i += 1
            out.append('<blockquote class="note">%s</blockquote>' % inline(" ".join(buf)))
            continue
        if re.match(r"^[-*+]\s+", s):
            it = []
            while i < n and re.match(r"^[-*+]\s+", L[i].strip()):
                it.append(re.sub(r"^[-*+]\s+", "", L[i].strip()))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % inline(x) for x in it) + "</ul>")
            continue
        if re.match(r"^\d+[.)]\s+", s):
            it = []
            while i < n and re.match(r"^\d+[.)]\s+", L[i].strip()):
                it.append(re.sub(r"^\d+[.)]\s+", "", L[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % inline(x) for x in it) + "</ol>")
            continue
        buf = []
        while i < n and L[i].strip() and not BLOCK.match(L[i].strip()):
            buf.append(L[i].strip())
            i += 1
        if not buf:                                # unconsumed marker: never loop
            buf.append(L[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out)

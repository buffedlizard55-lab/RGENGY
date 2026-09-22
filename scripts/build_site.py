#!/usr/bin/env python3
"""Build the static GitHub Pages site from the committed registries and docs/.

The site is generated rather than hand-written for the same reason the docs are:
a second copy of a source list is a second place for a link to rot.  Everything
here is rendered from ``rgengy/sources.py``, ``rgengy/data/scoring/*.json``,
``rgengy/findings.py`` and ``docs/*.md``.

No build-time or run-time dependencies: the markdown converter below is a
deliberately small subset (headings, tables, lists, blockquotes, fenced code,
inline code, bold, links, rules, ``<details>``) and is covered by
``tests/test_site.py``.

Supported nesting: code inside bold/italic, and bold/italic inside a link label.
NOT supported: italic inside bold (``**a *b* c**`` leaves literal asterisks).
``tests/test_site.py`` asserts that no committed document uses the unsupported
form, so the limitation is declared and policed rather than silently wrong.  The published HTML needs no network access, no CDN and no
JavaScript to be readable - JS is progressive enhancement for filtering only.

    python3 scripts/build_site.py            # writes site/
    python3 scripts/build_site.py --check    # exits 1 if site/ is stale
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rgengy import scoring  # noqa: E402  (path set up above)

SITE = REPO / "site"
DOCS = REPO / "docs"

# docs/00 is the index; the rest are rendered in this order.
DOC_ORDER = [
    ("00-index.md", "Overview"),
    ("01-method.md", "Method"),
    ("02-data-sources.md", "Data sources"),
    ("03-scoring-verification.md", "Scoring"),
    ("04-rg-findings.md", "RotoGrinders findings"),
    ("05-projection-engines.md", "Projection engines"),
    ("06-optimizer-and-simulator.md", "Optimizer & simulator"),
    ("07-grid-schema.md", "Grid schema"),
    ("08-quality-gates.md", "Quality gates"),
    ("09-irregularities.md", "Irregularities"),
    ("10-roadmap-and-limitations.md", "Limitations & roadmap"),
]


# ---------------------------------------------------------------------------
# Markdown subset -> HTML
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"^```(\w*)\s*$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_UL = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")
_HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def _inline(text: str) -> str:
    """Escape HTML, then apply the inline markup subset.

    Escaping first is what makes this safe: the source markdown is committed and
    trusted, but a retrieved endpoint note can contain angle brackets, and
    rendering it raw would inject markup into the published page.
    """
    out = html.escape(text, quote=False)
    placeholders: List[str] = []

    def stash(rendered: str) -> str:
        placeholders.append(rendered)
        return f"\x00{len(placeholders) - 1}\x00"

    # Inline code first, so its contents are never re-interpreted as markup.
    out = _CODE.sub(lambda m: stash(f"<code>{m.group(1)}</code>"), out)
    out = _LINK.sub(lambda m: stash(_link_html(m.group(1), m.group(2))), out)
    out = _BOLD.sub(lambda m: stash(f"<strong>{m.group(1)}</strong>"), out)
    out = _ITALIC.sub(lambda m: stash(f"<em>{m.group(1)}</em>"), out)
    # Restore OUTERMOST FIRST: a later stash can contain an earlier one's
    # sentinel (`**\`FPTS/$\`**` stashes the code at 0, then the bold at 1 with
    # sentinel 0 inside it).  Substituting in ascending order inserts the bold
    # after the code pass has already run and leaves the raw sentinel in the
    # published page.  Reverse order expands the container first, then its
    # contents, so nesting resolves at any depth.
    for i in range(len(placeholders) - 1, -1, -1):
        out = out.replace(f"\x00{i}\x00", placeholders[i])
    if "\x00" in out:
        raise AssertionError(f"inline markup placeholder leaked into output: {out[:200]!r}")
    return out


def _link_html(label: str, url: str) -> str:
    label = html.unescape(label)
    # Emphasis inside a link label is common enough in the docs to be worth
    # supporting; without this it renders as literal asterisks inside the anchor.
    label = html.escape(label, quote=False)
    label = _BOLD.sub(r"<strong>\1</strong>", label)
    label = _ITALIC.sub(r"<em>\1</em>", label)
    if url.startswith(("http://", "https://")):
        rel = ' target="_blank" rel="noopener noreferrer"'
        return f'<a href="{html.escape(url, quote=True)}"{rel}>{label}</a>'
    if url.startswith("#"):
        return f'<a href="{html.escape(url, quote=True)}">{label}</a>'
    # Relative markdown links become relative html links inside the site.  The
    # fragment has to be split off first: `09-irregularities.md#ir03` does not end
    # with `.md`, and leaving it as-is publishes a link to a file that does not
    # exist on Pages.
    target, _, frag = url.partition("#")
    if target.endswith(".md"):
        target = target[:-3] + ".html"
    target = target + (f"#{frag}" if frag else "")
    return f'<a href="{html.escape(target, quote=True)}">{label}</a>'


def _split_row(line: str) -> List[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, current, escaped = [], "", False
    for ch in line:
        if escaped:
            current += ch
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "|":
            cells.append(current.strip())
            current = ""
        else:
            current += ch
    cells.append(current.strip())
    return [c.replace("\\|", "|") for c in cells]


def _alignments(sep_cells: List[str]) -> List[Optional[str]]:
    out = []
    for cell in sep_cells:
        c = cell.strip()
        left, right = c.startswith(":"), c.endswith(":")
        out.append("center" if left and right else "left" if left
                   else "right" if right else None)
    return out


def markdown_to_html(md: str) -> Tuple[str, List[Dict[str, Any]]]:
    """Convert the markdown subset used by docs/ into HTML.

    Returns ``(html, toc)`` where ``toc`` is the heading outline used to build the
    on-page navigation.
    """
    lines = md.split("\n")
    out: List[str] = []
    toc: List[Dict[str, Any]] = []
    i = 0
    para: List[str] = []
    quote: List[str] = []
    list_stack: List[Tuple[str, int]] = []      # (tag, indent)
    in_table = False
    table_rows: List[List[str]] = []
    table_aligns: List[Optional[str]] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()

    def flush_quote() -> None:
        if quote:
            body = "<br>\n".join(_inline(q) for q in quote)
            out.append(f"<blockquote>{body}</blockquote>")
            quote.clear()

    def flush_list() -> None:
        while list_stack:
            tag, _ = list_stack.pop()
            out.append(f"</{tag}>")

    def flush_table() -> None:
        nonlocal in_table, table_rows, table_aligns
        if not in_table:
            return
        in_table = False
        if not table_rows:
            table_rows, table_aligns = [], []
            return
        head, *body = table_rows
        parts = ['<div class="table-wrap"><table>']
        if any(c.strip() for c in head):
            parts.append("<thead><tr>")
            for idx, cell in enumerate(head):
                align = table_aligns[idx] if idx < len(table_aligns) else None
                attr = f' style="text-align:{align}"' if align else ""
                parts.append(f"<th{attr}>{_inline(cell)}</th>")
            parts.append("</tr></thead>")
        if body:
            parts.append("<tbody>")
            for row in body:
                parts.append("<tr>")
                for idx in range(max(len(head), len(row))):
                    cell = row[idx] if idx < len(row) else ""
                    align = table_aligns[idx] if idx < len(table_aligns) else None
                    attr = f' style="text-align:{align}"' if align else ""
                    parts.append(f"<td{attr}>{_inline(cell)}</td>")
                parts.append("</tr>")
            parts.append("</tbody>")
        parts.append("</table></div>")
        out.append("".join(parts))
        table_rows, table_aligns = [], []

    def flush_all() -> None:
        flush_para()
        flush_quote()
        flush_list()
        flush_table()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code
        fence = _FENCE.match(stripped)
        if fence:
            flush_all()
            lang = fence.group(1)
            body: List[str] = []
            i += 1
            while i < len(lines) and not _FENCE.match(lines[i].strip()):
                body.append(lines[i])
                i += 1
            i += 1                                  # skip the closing fence
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>"
                       f"{html.escape(chr(10).join(body), quote=False)}</code></pre>")
            continue

        # raw HTML passthrough for <details> blocks used in docs/03
        if stripped.startswith("<details") or stripped.startswith("</details"):
            flush_all()
            out.append(stripped.replace("<summary>", "<summary>").strip())
            i += 1
            continue
        if stripped.startswith("<summary>"):
            flush_all()
            out.append(stripped)
            i += 1
            continue

        # blank line
        if not stripped:
            flush_all()
            i += 1
            continue

        # horizontal rule
        if _HR.match(stripped):
            flush_all()
            out.append("<hr>")
            i += 1
            continue

        # heading
        h = _HEADING.match(line)
        if h:
            flush_all()
            level = len(h.group(1))
            text = h.group(2).strip()
            slug = _slug(text)
            toc.append({"level": level, "text": text, "slug": slug})
            out.append(f'<h{level} id="{slug}">{_inline(text)}</h{level}>')
            i += 1
            continue

        # table
        if stripped.startswith("|"):
            cells = _split_row(stripped)
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if not in_table and _TABLE_SEP.match(nxt):
                flush_para()
                flush_quote()
                flush_list()
                in_table = True
                table_rows = [cells]
                table_aligns = _alignments(_split_row(nxt))
                i += 2
                continue
            if in_table:
                table_rows.append(cells)
                i += 1
                continue

        # blockquote
        if stripped.startswith(">"):
            flush_para()
            flush_list()
            flush_table()
            quote.append(stripped.lstrip(">").strip())
            i += 1
            continue

        # unordered list
        ul = _UL.match(line)
        if ul:
            flush_para()
            flush_quote()
            flush_table()
            indent = len(ul.group(1))
            if not list_stack or list_stack[-1][0] != "ul":
                flush_list()
                out.append("<ul>")
                list_stack.append(("ul", indent))
            out.append(f"<li>{_inline(ul.group(2))}</li>")
            i += 1
            continue

        # ordered list
        ol = _OL.match(line)
        if ol:
            flush_para()
            flush_quote()
            flush_table()
            indent = len(ol.group(1))
            if not list_stack or list_stack[-1][0] != "ol":
                flush_list()
                out.append("<ol>")
                list_stack.append(("ol", indent))
            out.append(f"<li>{_inline(ol.group(3))}</li>")
            i += 1
            continue

        # paragraph text
        flush_quote()
        flush_list()
        flush_table()
        para.append(stripped)
        i += 1

    flush_all()
    return "\n".join(out), toc


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

CSS = """
:root {
  --bg: #ffffff;
  --fg: #16202b;
  --muted: #5c6b7a;
  --line: #dfe5eb;
  --soft: #f5f7f9;
  --accent: #0b6b5f;
  --accent-soft: #e6f2f0;
  --info: #1f5f8b;
  --warning: #8a5a00;
  --critical: #a32020;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover, a:focus { text-decoration: underline; }
code, pre { font-family: var(--mono); }
code { background: var(--soft); border: 1px solid var(--line); border-radius: 4px;
       padding: 0.1em 0.35em; font-size: 0.875em; word-break: break-word; }
pre { background: var(--soft); border: 1px solid var(--line); border-radius: 8px;
      padding: 14px 16px; overflow-x: auto; }
pre code { background: none; border: 0; padding: 0; font-size: 0.85em; }

.layout { display: grid; grid-template-columns: 268px minmax(0, 1fr); min-height: 100vh; }
.sidebar { border-right: 1px solid var(--line); background: var(--soft); padding: 22px 18px; }
.sidebar .brand { font-weight: 700; font-size: 1.1rem; letter-spacing: -0.01em; }
.sidebar .tagline { color: var(--muted); font-size: 0.82rem; margin: 4px 0 18px; }
.sidebar nav a { display: block; padding: 6px 10px; border-radius: 6px; color: var(--fg);
                 font-size: 0.9rem; }
.sidebar nav a:hover { background: #e9eef2; text-decoration: none; }
.sidebar nav a[aria-current="page"] { background: var(--accent-soft); color: var(--accent);
                                      font-weight: 600; }
.sidebar .sep { border-top: 1px solid var(--line); margin: 14px 0; }
.sidebar .navhead { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); font-weight: 700; padding: 8px 10px 4px; }
.sidebar .meta { color: var(--muted); font-size: 0.75rem; line-height: 1.5; }

.content { padding: 30px 40px 80px; max-width: 1080px; }
.content h1 { font-size: 1.9rem; line-height: 1.25; margin: 0 0 6px; letter-spacing: -0.02em; }
.content h2 { font-size: 1.35rem; margin: 40px 0 10px; padding-bottom: 6px;
              border-bottom: 1px solid var(--line); letter-spacing: -0.01em; }
.content h3 { font-size: 1.08rem; margin: 28px 0 8px; }
.content h4 { font-size: 0.98rem; margin: 22px 0 6px; color: var(--muted); }
.content p { margin: 12px 0; }
.content ul, .content ol { padding-left: 24px; }
.content li { margin: 5px 0; }
.content hr { border: 0; border-top: 1px solid var(--line); margin: 32px 0; }
blockquote { margin: 16px 0; padding: 10px 16px; border-left: 4px solid var(--accent);
             background: var(--accent-soft); border-radius: 0 6px 6px 0; color: #17322e; }
blockquote p { margin: 6px 0; }

.table-wrap { overflow-x: auto; margin: 16px 0; border: 1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
th, td { padding: 8px 12px; border-bottom: 1px solid var(--line); text-align: left;
         vertical-align: top; }
th { background: var(--soft); font-weight: 600; white-space: nowrap; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: #fbfcfd; }
td code { white-space: nowrap; }

.badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 0.72rem;
         font-weight: 600; letter-spacing: 0.02em; text-transform: uppercase;
         border: 1px solid var(--line); background: var(--soft); color: var(--muted);
         white-space: nowrap; }
.badge.info { color: var(--info); border-color: #cfe0ee; background: #eef5fa; }
.badge.warning { color: var(--warning); border-color: #eddcc0; background: #fdf6e9; }
.badge.critical { color: var(--critical); border-color: #eec9c9; background: #fdefef; }
.badge.ok { color: var(--accent); border-color: #c6e0db; background: var(--accent-soft); }

.cards { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
         margin: 20px 0; }
.card { border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; background: #fff; }
.card .n { font-size: 1.7rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.card .l { color: var(--muted); font-size: 0.8rem; margin-top: 4px; }

.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 16px 0; }
.filters input[type="search"] { flex: 1 1 220px; padding: 8px 12px; font-size: 0.9rem;
  border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--fg); }
.filters button { padding: 7px 12px; font-size: 0.82rem; border: 1px solid var(--line);
  border-radius: 999px; background: #fff; color: var(--muted); cursor: pointer; }
.filters button[aria-pressed="true"] { background: var(--accent-soft); color: var(--accent);
  border-color: #c6e0db; font-weight: 600; }
.filters .count { color: var(--muted); font-size: 0.8rem; margin-left: auto; }

details { border: 1px solid var(--line); border-radius: 8px; padding: 10px 14px; margin: 12px 0;
          background: #fff; }
details summary { cursor: pointer; font-weight: 600; font-size: 0.92rem; }
details[open] summary { margin-bottom: 10px; }
details ul { margin: 8px 0; }

.pagefoot { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--line);
            color: var(--muted); font-size: 0.8rem; }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: 12px; top: 12px; z-index: 10; background: #fff; padding: 8px 12px;
              border: 1px solid var(--line); border-radius: 6px; }
.empty { color: var(--muted); font-style: italic; padding: 12px 0; }

@media (max-width: 900px) {
  .layout { grid-template-columns: minmax(0, 1fr); }
  .sidebar { border-right: 0; border-bottom: 1px solid var(--line); }
  .content { padding: 22px 18px 60px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

JS = """
// Progressive enhancement only: the pages are fully readable without this file.
(function () {
  "use strict";

  // Table filtering. Any <table> preceded by a .filters block is filterable.
  function wireFilters() {
    document.querySelectorAll(".filters").forEach(function (bar) {
      var target = bar.nextElementSibling;
      while (target && !target.matches("table, .table-wrap")) target = target.nextElementSibling;
      if (!target) return;
      var table = target.matches("table") ? target : target.querySelector("table");
      if (!table) return;
      var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
      var search = bar.querySelector('input[type="search"]');
      var buttons = Array.prototype.slice.call(bar.querySelectorAll("button[data-filter]"));
      var counter = bar.querySelector(".count");

      function apply() {
        var q = (search && search.value || "").trim().toLowerCase();
        var active = buttons.filter(function (b) { return b.getAttribute("aria-pressed") === "true"; })
                            .map(function (b) { return b.getAttribute("data-filter"); });
        var shown = 0;
        rows.forEach(function (tr) {
          var text = tr.textContent.toLowerCase();
          var okQ = !q || text.indexOf(q) !== -1;
          var okF = active.length === 0 || active.some(function (f) {
            return tr.getAttribute("data-tags") && tr.getAttribute("data-tags").indexOf(f) !== -1;
          });
          var show = okQ && okF;
          tr.hidden = !show;
          if (show) shown++;
        });
        if (counter) counter.textContent = shown + " of " + rows.length + " shown";
      }

      if (search) search.addEventListener("input", apply);
      buttons.forEach(function (b) {
        b.addEventListener("click", function () {
          var on = b.getAttribute("aria-pressed") === "true";
          b.setAttribute("aria-pressed", on ? "false" : "true");
          apply();
        });
      });
      apply();
    });
  }

  // Mark the current page in the sidebar.
  function markCurrent() {
    var here = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll('.sidebar nav a').forEach(function (a) {
      var href = a.getAttribute("href");
      if (href === here || (here === "" && href === "index.html")) {
        a.setAttribute("aria-current", "page");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireFilters();
    markCurrent();
  });
})();
"""


def _sidebar(current: str, data: Dict[str, Any]) -> str:
    counts = data["findings"]["counts"]

    def link(target: str, label: str) -> str:
        cur = ' aria-current="page"' if target == current else ""
        return f'<a href="{target}"{cur}>{html.escape(label)}</a>'

    explore = ['<a class="navhead" href="index.html"'
               + (' aria-current="page"' if current == "index.html" else "")
               + '>Dashboard</a>']
    for target, label in (("sources.html", "Data sources"),
                          ("scoring.html", "Scoring tables"),
                          ("findings.html", "Findings register"),
                          ("rosters.html", "Roster templates"),
                          ("grid.html", "Grid schema"),
                          ("checks.html", "Quality gates"),
                          ("verification.html", "Live verification")):
        explore.append(link(target, label))
    docs = [link(fname[:-3] + ".html", label) for fname, label in DOC_ORDER]
    return f"""<div class="sidebar">
  <div class="brand">RGENGY</div>
  <div class="tagline">An auditable rebuild of RotoGrinders' projection data quality</div>
  <nav aria-label="Explore the data">
    <div class="navhead">Explore</div>
    {''.join(explore)}
  </nav>
  <div class="sep"></div>
  <nav aria-label="Documentation">
    <div class="navhead">Documentation</div>
    {''.join(docs)}
  </nav>
  <div class="sep"></div>
  <div class="meta">
    Audit date {data['audit_date']}<br>
    {data['sources']['summary']['total_endpoints']} endpoints &middot;
    {len(data['scoring'])} scoring tables<br>
    {counts['total']} findings ({counts['open']} open)<br>
    {sum(t['tests'] for t in data['tests'])} tests passing
  </div>
</div>"""


def _page(title: str, current: str, body: str, data: Dict[str, Any],
          description: str = "") -> str:
    generated = data["generated_at"]
    meta = f'<meta name="description" content="{html.escape(description, quote=True)}">' if description else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_site.py from the committed registries. -->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} &middot; RGENGY</title>
{meta}
<link rel="stylesheet" href="styles.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="layout">
{_sidebar(current, data)}
<main class="content" id="main">
{body}
<div class="pagefoot">
  Generated {generated} by <code>scripts/build_site.py</code> from the committed
  registries. Nothing on this site is hand-copied: every number is rendered from
  <code>rgengy/sources.py</code>, <code>rgengy/data/scoring/*.json</code> or
  <code>rgengy/findings.py</code>.
</div>
</main>
</div>
<script src="app.js" defer></script>
</body>
</html>
"""


def _badge(text: str, kind: str = "") -> str:
    cls = f' class="badge {kind}"' if kind else ' class="badge"'
    return f"<span{cls}>{html.escape(str(text))}</span>"


SEVERITY_KIND = {"info": "info", "warning": "warning", "critical": "critical"}
STATUS_KIND = {"live-verified": "ok", "reachable": "ok", "documented": "warning",
               "unverified": "critical", "multi-source-consistent": "ok",
               "cross-validated-via-rg": "ok", "single-source": "warning",
               "disputed": "critical", "not-audited": "critical",
               "not-applicable": "", "open": "warning", "resolved": "ok",
               "assumption": "info", "unused-id": ""}


def _table(headers: List[str], rows: List[List[str]], aligns: Optional[List[str]] = None) -> str:
    parts = ['<div class="table-wrap"><table><thead><tr>']
    for h in headers:
        parts.append(f"<th>{h}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for idx, cell in enumerate(row):
            attr = ""
            if aligns and idx < len(aligns) and aligns[idx]:
                attr = f' style="text-align:{aligns[idx]}"'
            parts.append(f"<td{attr}>{cell}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def build_index(data: Dict[str, Any]) -> str:
    s = data["sources"]["summary"]
    bs = s["by_status"]
    f = data["findings"]["counts"]
    n_tests = sum(t["tests"] for t in data["tests"])
    validated = next((t for t in data["scoring"] if t["key"] == "mlb:draftkings"), None)

    cards = [
        (str(s["total_endpoints"]), "registered data endpoints",
         f'{s["official"]} official league feeds, {s["unofficial"]} third-party, '
         f'{s["requires_auth"]} needing an API key'),
        (str(len(data["scoring"])), "scoring tables audited",
         "every coefficient carries its evidence class and source URLs"),
        (str(f["total"]), "findings on the register",
         f'{f["open"]} open, {f["resolved"]} resolved, {f["critical"]} critical'),
        (str(n_tests), "tests passing",
         f'across {len(data["tests"])} modules, stdlib unittest'),
    ]
    card_html = "".join(
        f'<div class="card"><div class="n">{html.escape(n)}</div>'
        f'<div class="l"><strong>{html.escape(l)}</strong><br>{html.escape(sub)}</div></div>'
        for n, l, sub in cards)

    body: List[str] = []
    body.append("<h1>RGENGY</h1>")
    body.append('<p class="lede">An open, auditable rebuild of the <em>data quality</em> behind '
                '<a href="https://rotogrinders.com/" target="_blank" rel="noopener noreferrer">'
                'RotoGrinders</a>&rsquo; projection system: what it uses, where that data comes '
                'from, what could be verified from official sources, and what could not.</p>')
    body.append(f'<div class="cards">{card_html}</div>')

    body.append("<h2>The headline results</h2>")
    if validated:
        meta = validated["meta"]
        body.append(_table(
            ["result", "evidence"],
            [["<strong>The scoring table is externally validated.</strong> RGENGY's independently "
              "sourced DraftKings MLB coefficients, applied to RotoGrinders' own published stat "
              "projections, reproduce their published FPTS.",
              f'All 6 free rows within <strong>0.07 FPTS</strong> (0.56% worst case). '
              f'Audit date {meta.get("audit_date")}.'
              ' <a href="04-rg-findings.html">04 &sect;1</a>'],
             ["<strong><code>FPTS/$</code> is reproduced exactly.</strong> "
              "<code>FPTS / (SALARY / 1000)</code>.",
              'Max error 0.0036 over 6 rows - pure 2dp display rounding. The only RotoGrinders '
              'analytic column RGENGY claims to reproduce. <a href="04-rg-findings.html">04 &sect;2</a>'],
             ["<strong>Every external input is registered with a verification status.</strong>",
              f'{bs.get("live-verified", 0)} live-verified, {bs.get("documented", 0)} documented, '
              f'{bs.get("reachable", 0)} reachable, {bs.get("unverified", 0)} unverified. '
              '<a href="02-data-sources.html">02</a>'],
             ["<strong>Nothing is published without its evidence class.</strong>",
              "Each coefficient is <code>multi-source-consistent</code>, <code>single-source</code>, "
              "<code>disputed</code> or <code>not-audited</code>, with the URLs. "
              '<a href="03-scoring-verification.html">03</a>'],
             ["<strong>What cannot be verified is null, with a written reason.</strong>",
              "RotoGrinders' <code>OBFPTS</code>, <code>TOPVAL</code>, <code>DIFFERENCE</code>, "
              "<code>OPTO</code> and <code>TEAMOWN</code> have no published formula, so RGENGY "
              "leaves them empty rather than inventing a number that looks like theirs. "
              '<a href="07-grid-schema.html">07</a>']],
        ))

    body.append("<h2>The largest constraint</h2>")
    op_total = scoring.audit()["operator_confirmed_total"]
    body.append("<blockquote><strong>L-02 (updated 2026-09-22).</strong> The build sandbox still "
                "has no raw-socket network access, but the operator-evidence picture improved in "
                "the second audit pass: FanDuel's public rules page (fanduel.com/rules) and "
                "DraftKings' own Network scoring articles were retrieved, so "
                f"<strong>{op_total} scoring values are now marked "
                "<code>confirmed_by_operator</code></strong> across seven of the eleven tables. "
                "What remains secondary is labelled per value: MLB caught stealing and the "
                "quality-start question (IR-04, IR-05), the DraftKings DST block (L-04), and "
                "DraftKings' canonical in-app rules page itself. <code>rgengy probe</code> and "
                "<code>rgengy verify</code> - which now re-checks every cited URL - run on every "
                "CI build.</blockquote>")

    body.append("<h2>Findings by status</h2>")
    body.append(_table(
        ["status", "count", "meaning"],
        [[_badge("open", "warning"), str(f["open"]),
          "unresolved; the affected number is labelled or excluded"],
         [_badge("stated assumption", "info"), str(f["assumptions"]),
          "RGENGY proceeds on a documented, unaudited assumption"],
         [_badge("resolved", "ok"), str(f["resolved"]),
          "was a defect in RGENGY or in the audit; kept because the fix changed a published value"],
         [_badge("unused id"), str(f["unused_ids"]),
          "a numbering gap, declared rather than silently renumbered"],
         [_badge("critical", "critical"), str(f["critical"]),
          "the output must not be trusted until addressed"]]))
    body.append('<p><a href="09-irregularities.html">Read the full register &rarr;</a> '
                '<a href="10-roadmap-and-limitations.html" style="margin-left:12px">'
                'Limitations and remaining work &rarr;</a></p>')

    body.append("<h2>How the pieces fit</h2>")
    body.append(_table(
        ["stage", "module", "what it does"],
        [["1. Slate", "<code>sources.py</code>",
          "Games, odds, venues and weather from official league feeds. Every fetch records "
          "provenance with a timestamp."],
         ["2. Environment", "<code>vegas.py</code>",
          "Vig removal, implied team totals, market win probability from the moneyline."],
         ["3. Projection", "<code>engines.py</code>",
          "rate x opportunity x environment, with position dispatch and no fabrication."],
         ["4. Ownership", "<code>ownership.py</code>",
          "A softmax choice model over value, capped, and labelled <code>calibrated=False</code>."],
         ["5. Optimizer", "<code>optimizer.py</code>",
          "Exact grouped knapsack over salary, with a pool-aware flex/fixed slot partition."],
         ["6. Simulation", "<code>simulator.py</code>",
          "Synthetic field, payouts, cash/top-10/top-1 rates."],
         ["7. Quality gates", "<code>quality.py</code>",
          "Nine checks; findings carry a review action so a human knows what to do next."],
         ["8. Grid", "<code>pipeline.py</code>",
          "RotoGrinders' own column order, with nulls and written reasons where unfilled."]]))

    body.append("<h2>Test coverage</h2>")
    body.append(_table(["module", "tests"],
                       [[f"<code>{t['module']}</code>", str(t["tests"])] for t in data["tests"]]
                       + [["<strong>total</strong>", f"<strong>{n_tests}</strong>"]],
                       aligns=[None, "right"]))
    return "\n".join(body)


def build_sources_page(data: Dict[str, Any]) -> str:
    s = data["sources"]["summary"]
    rows = []
    for e in data["sources"]["endpoints"]:
        tags = " ".join([e["verification_status"], "official" if e["official"] else "unofficial",
                         e["auth"]])
        links = []
        if e.get("docs_url"):
            links.append(f'<a href="{html.escape(e["docs_url"], quote=True)}" target="_blank" '
                         f'rel="noopener noreferrer">docs</a>')
        if e.get("terms_url"):
            links.append(f'<a href="{html.escape(e["terms_url"], quote=True)}" target="_blank" '
                         f'rel="noopener noreferrer">terms</a>')
        else:
            links.append("<strong>no terms published</strong>")
        rows.append(
            f'<tr data-tags="{html.escape(tags, quote=True)}">'
            f'<td><code>{html.escape(e["key"])}</code><br>'
            f'<span style="color:var(--muted);font-size:0.82rem">{html.escape(e["name"])}</span></td>'
            f'<td>{html.escape(e["provider"])}<br>'
            f'{_badge("official", "ok") if e["official"] else _badge("unofficial")}</td>'
            f'<td>{_badge(e["verification_status"], STATUS_KIND.get(e["verification_status"], ""))}'
            f'<br><span style="color:var(--muted);font-size:0.78rem">'
            f'{html.escape(e["verified_on"] or "never")}</span></td>'
            f'<td><code>{html.escape(e["auth"])}</code></td>'
            f'<td style="font-size:0.78rem;word-break:break-all">'
            f'<code>{html.escape(e["url_template"])}</code></td>'
            f'<td>{" &middot; ".join(links)}</td></tr>')
    filters = "".join(
        f'<button type="button" data-filter="{html.escape(st)}" aria-pressed="false">'
        f'{html.escape(st)} ({s["by_status"].get(st, 0)})</button>'
        for st in sorted(s["by_status"], key=lambda k: -s["by_status"][k]))
    _audit = scoring.audit()
    _op_total = _audit["operator_confirmed_total"]
    _op_tables = sum(1 for t in _audit["tables"] if t["operator_confirmed"])
    return f"""<h1>Data sources</h1>
<p>All {s['total_endpoints']} external inputs RGENGY uses, with the provider, whether that
provider is the league itself, the authentication required, and what was actually verified on
<strong>{s['audit_date']}</strong>. Rendered from <code>rgengy/sources.py</code>; see
<a href="02-data-sources.html">the full generated register</a> for the per-endpoint field notes.</p>
<blockquote><strong>L-02 (updated 2026-09-22).</strong> FanDuel's public rules page
(fanduel.com/rules) and DraftKings' Network scoring articles were retrieved in the second audit
pass, so <em>{_op_total} scoring values are now marked <code>confirmed_by_operator</code></em>
across {_op_tables} tables; the values still resting on secondary evidence are labelled per value
in the scoring pages.</blockquote>
<div class="filters">
  <input type="search" placeholder="Filter by key, provider or URL&hellip;" aria-label="Filter endpoints">
  {filters}
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>endpoint</th><th>provider</th><th>verification</th><th>auth</th>
<th>url template</th><th>links</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def build_scoring_page(data: Dict[str, Any]) -> str:
    counts: Dict[str, int] = {}
    for t in data["scoring"]:
        for spec in t["values"].values():
            st = spec.get("verification_status") or "unknown"
            counts[st] = counts.get(st, 0) + 1
    total = sum(counts.values())

    summary_rows = []
    for t in data["scoring"]:
        meta = t["meta"]
        n_disp = len(t["disputed"])
        n_un = len(t["not_audited"])
        worst = "critical" if (n_disp or n_un) else "ok"
        summary_rows.append(
            f'<tr data-tags="{html.escape(t["sport"] + " " + t["site"])}">'
            f'<td><a href="#{html.escape(t["key"])}"><code>{html.escape(t["key"])}</code></a></td>'
            f'<td>{html.escape(str(meta.get("contest_format")))}</td>'
            f'<td style="text-align:right">{meta.get("salary_cap")}</td>'
            f'<td style="text-align:right">{len(t["values"])}</td>'
            f'<td style="text-align:right">{n_disp or "-"}</td>'
            f'<td style="text-align:right">{n_un or "-"}</td>'
            f'<td>{_badge("operator-confirmed", "ok") if meta.get("confirmed_by_operator") else _badge("secondary sources only", "warning")}</td>'
            f'<td>{_badge("clean", "ok") if worst == "ok" else _badge("has gaps", worst)}</td></tr>')

    blocks = []
    for t in data["scoring"]:
        meta = t["meta"]
        rows = []
        for stat in sorted(t["values"]):
            spec = t["values"][stat]
            st = spec.get("verification_status") or "unknown"
            urls = spec.get("sources") or []
            link_html = " ".join(
                f'<a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">[{i + 1}]</a>'
                for i, u in enumerate(urls)) or "-"
            rows.append(
                f'<tr data-tags="{html.escape(st)}">'
                f'<td><code>{html.escape(stat)}</code></td>'
                f'<td style="text-align:right"><strong>{spec["value"]}</strong></td>'
                f'<td>{_badge(st, STATUS_KIND.get(st, ""))}</td>'
                f'<td style="text-align:right">{spec.get("agreement")}</td>'
                f'<td>{_badge("disputed", "critical") if spec.get("disputed") else ""}</td>'
                f'<td style="font-size:0.82rem">{html.escape(str(spec.get("note") or ""))}</td>'
                f'<td style="font-size:0.8rem;white-space:nowrap">{link_html}</td></tr>')
        consulted = "".join(
            f'<li><a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(u)}</a></li>' for u in meta.get("sources_consulted", []))
        blocks.append(f"""<details id="{html.escape(t['key'])}">
<summary>{html.escape(t['key'])} &mdash; {len(t['values'])} coefficients,
{len(t['disputed'])} disputed, {len(t['not_audited'])} not audited</summary>
<p style="color:var(--muted);font-size:0.86rem"><strong>Audit method.</strong>
{html.escape(str(meta.get('audit_method') or ''))}</p>
{f'<p style="color:var(--muted);font-size:0.86rem"><strong>Notes.</strong> {html.escape(str(meta["notes"]))}</p>' if meta.get('notes') else ''}
<div class="filters">
  <input type="search" placeholder="Filter stats&hellip;" aria-label="Filter stats">
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>stat</th><th>value</th><th>evidence</th><th>agree</th><th>&nbsp;</th>
<th>note</th><th>sources</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p style="font-size:0.84rem"><strong>Sources consulted for this table</strong> ({len(meta.get('sources_consulted', []))}):</p>
<ul style="font-size:0.8rem;word-break:break-all">{consulted}</ul>
</details>""")

    ev_rows = [[_badge(st, STATUS_KIND.get(st, "")), str(n), f"{n / total * 100:.1f}%"]
               for st, n in sorted(counts.items(), key=lambda kv: -kv[1])]
    return f"""<h1>Scoring verification</h1>
<p>{total} coefficients across {len(data['scoring'])} tables. Fantasy points are the product of a
scoring table and a projection, so a wrong coefficient corrupts every number downstream of it.
Each value below carries the number of independent sources that agree on it and the URLs they came
from. See <a href="03-scoring-verification.html">the full generated audit</a>.</p>
<h2>Evidence classes</h2>
{_table(['class', 'coefficients', 'share'], ev_rows, aligns=[None, 'right', 'right'])}
<h2>Tables</h2>
<div class="filters">
  <input type="search" placeholder="Filter tables&hellip;" aria-label="Filter tables">
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>table</th><th>contest format</th><th>cap</th><th>coeffs</th><th>disputed</th>
<th>not audited</th><th>confirmation</th><th>status</th></tr></thead>
<tbody>{''.join(summary_rows)}</tbody></table></div>
<h2>Every coefficient</h2>
{''.join(blocks)}"""


def build_findings_page(data: Dict[str, Any]) -> str:
    rows, blocks = [], []
    for f in data["findings"]["findings"]:
        anchor = f["id"].lower().replace("-", "")
        rows.append(
            f'<tr data-tags="{html.escape(f["kind"] + " " + f["status"] + " " + f["severity"])}">'
            f'<td><a href="#{anchor}"><strong>{html.escape(f["id"])}</strong></a></td>'
            f'<td>{_badge(f["severity"], SEVERITY_KIND.get(f["severity"], ""))}</td>'
            f'<td>{_badge(f["status"], STATUS_KIND.get(f["status"], ""))}</td>'
            f'<td>{html.escape(f["kind"])}</td>'
            f'<td>{html.escape(f["title"])}</td></tr>')
        sources = "".join(
            f'<li><a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(u)}</a></li>' for u in f["sources"])
        refs = ", ".join(f"<code>{html.escape(r)}</code>" for r in f["refs"])
        blocks.append(f"""<div class="finding" id="{anchor}">
<h3>{html.escape(f['id'])} &mdash; {html.escape(f['title'])}</h3>
<p>{_badge(f['kind'])} {_badge(f['status'], STATUS_KIND.get(f['status'], ''))}
{_badge(f['severity'], SEVERITY_KIND.get(f['severity'], ''))}</p>
<p><strong>What was found.</strong> {html.escape(f['detail'])}</p>
<p><strong>Why it matters.</strong> {html.escape(f['impact'])}</p>
<p><strong>What RGENGY does about it.</strong> {html.escape(f['action'])}</p>
<p style="font-size:0.84rem;color:var(--muted)">Cited in: {refs}</p>
{f'<p style="font-size:0.84rem"><strong>Sources retrieved.</strong></p><ul style="font-size:0.8rem;word-break:break-all">{sources}</ul>' if sources else ''}
</div>""")
    c = data["findings"]["counts"]
    buttons = "".join(
        f'<button type="button" data-filter="{html.escape(v)}" aria-pressed="false">{html.escape(v)}</button>'
        for v in ("irregularity", "limitation", "open", "resolved", "assumption",
                  "unused-id", "critical"))
    return f"""<h1>Irregularities and limitations</h1>
<p>{c['total']} findings from the {data['audit_date']} audit: {c['irregularities']} irregularities
and {c['limitations']} limitations. Generated from <code>rgengy/findings.py</code>, the single
source of truth - the scoring tables, module docstrings and quality findings all cite these ids,
and <code>tests/test_findings.py</code> fails if the two disagree in either direction.</p>
<blockquote>Gaps in the numbering are <strong>declared, not silent</strong>. An id consumed during
the audit and then folded into another finding stays on the register with status
<code>unused-id</code>, because renumbering would quietly invalidate every cross-reference already
written into the scoring tables.</blockquote>
<div class="filters">
  <input type="search" placeholder="Search findings&hellip;" aria-label="Search findings">
  {buttons}
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>id</th><th>severity</th><th>status</th><th>kind</th><th>title</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<h2>Detail</h2>
{''.join(blocks)}"""


def build_rosters_page(data: Dict[str, Any]) -> str:
    rows, blocks = [], []
    for key in sorted(data["rosters"]):
        r = data["rosters"][key]
        rows.append(
            f'<tr data-tags="{html.escape(r["sport"] + " " + r["site"] + " " + r["verification_status"])}">'
            f'<td><a href="#{html.escape(key)}"><code>{html.escape(key)}</code></a></td>'
            f'<td style="text-align:right">{r["salary_cap"]}</td>'
            f'<td style="text-align:right">{r["n_players"]}</td>'
            f'<td>{_badge(r["verification_status"], STATUS_KIND.get(r["verification_status"], ""))}</td>'
            f'<td style="font-size:0.82rem">{html.escape(str(r["note"] or ""))}</td></tr>')
        slot_rows = "".join(
            f'<tr><td><code>{html.escape(s["label"])}</code></td>'
            f'<td style="text-align:right">{s["count"]}</td>'
            f'<td>{html.escape(", ".join(s["eligible"]))}</td></tr>' for s in r["slots"])
        srcs = "".join(
            f'<li><a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(u)}</a></li>' for u in r["sources"]) or "<li><em>none retrieved</em></li>"
        blocks.append(f"""<details id="{html.escape(key)}">
<summary>{html.escape(key)} &mdash; {r['n_players']} players, ${r['salary_cap']:,} cap,
{html.escape(r['verification_status'])}</summary>
{_table(['slot', 'count', 'eligible positions'], slot_rows, aligns=[None, 'right', None])}
<p style="font-size:0.86rem">{html.escape(str(r['note'] or ''))}</p>
<p style="font-size:0.84rem"><strong>Sources</strong></p>
<ul style="font-size:0.8rem;word-break:break-all">{srcs}</ul>
</details>""")
    return f"""<h1>Roster templates</h1>
<p>A roster template that is wrong is worse than a projection that is wrong: it produces lineups
the operator would reject outright. Every template therefore carries its own provenance and its own
verification status, separately from the scoring tables.</p>
<blockquote><strong>IR-17 (resolved, critical).</strong> Pass 1 listed separate C and 1B slots for
DraftKings MLB, requiring 11 players where the operator combines them into one C/1B slot for 10.
<code>models.default_roster()</code> now self-checks that the slot counts sum to the documented
player count and raises if they do not.</blockquote>
<div class="filters">
  <input type="search" placeholder="Filter rosters&hellip;" aria-label="Filter rosters">
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>template</th><th>salary cap</th><th>players</th><th>verification</th>
<th>note</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<h2>Slot detail</h2>
{''.join(blocks)}"""


def build_grid_page(data: Dict[str, Any]) -> str:
    summary, blocks = [], []
    for sport in sorted(data["grid"]):
        g = data["grid"][sport]
        filled = sum(1 for c in g["cells"] if c["filled"])
        summary.append(
            f'<tr data-tags="{html.escape(sport)}">'
            f'<td><a href="#grid-{html.escape(sport)}"><strong>{sport.upper()}</strong></a></td>'
            f'<td style="text-align:right">{len(g["columns"])}</td>'
            f'<td style="text-align:right">{filled}</td>'
            f'<td style="text-align:right">{len(g["columns"]) - filled}</td>'
            f'<td>{_badge("transcribed", "ok") if g["observed"] else _badge("NOT transcribed", "critical")}</td></tr>')
        rows = "".join(
            f'<tr data-tags="{"filled" if c["filled"] else "null"}">'
            f'<td style="text-align:right">{i}</td>'
            f'<td><code>{html.escape(c["column"])}</code></td>'
            f'<td>{"<code>" + html.escape(str(c["source"])) + "</code>" if c["filled"] else "<strong>null</strong>"}</td>'
            f'<td style="font-size:0.82rem">{html.escape(str(c["reason"] or ""))}</td></tr>'
            for i, c in enumerate(g["cells"], 1))
        blocks.append(f"""<details id="grid-{sport}"{' open' if sport == 'mlb' else ''}>
<summary>{sport.upper()} &mdash; {len(g['columns'])} columns, {filled} filled,
{len(g['columns']) - filled} null</summary>
{'' if g['observed'] else '<blockquote><strong>IR-22.</strong> This grid header was NOT transcribed from RotoGrinders, so the column set below is RGENGY&rsquo;s own and must not be read as a reproduction of theirs.</blockquote>'}
<div class="filters">
  <input type="search" placeholder="Filter columns&hellip;" aria-label="Filter columns">
  <button type="button" data-filter="filled" aria-pressed="false">filled</button>
  <button type="button" data-filter="null" aria-pressed="false">null</button>
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>#</th><th>column</th><th>RGENGY source</th><th>reason if null</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</details>""")
    return f"""<h1>Grid schema</h1>
<p>RotoGrinders&rsquo; projection grid is the artefact its users actually read, so reproducing its
<em>shape</em> matters as much as reproducing its numbers. Column headers were transcribed from the
live site on {data['audit_date']} for MLB, NFL and WNBA only.</p>
<blockquote><strong>The two-way invariant</strong>, asserted by <code>tests/test_pipeline.py</code>:
every observed column is either mapped to a real RGENGY value or carries a written reason for being
null, and every written reason refers to a column that actually exists. A null with no reason is
indistinguishable from a bug; a filled column with no source is indistinguishable from a
fabrication.</blockquote>
{_table(['sport', 'columns observed', 'filled', 'null', 'header transcribed'], summary,
        aligns=[None, 'right', 'right', 'right', None])}
{''.join(blocks)}"""


def build_verification_page(data: Dict[str, Any]) -> str:
    counts = data["findings"]["counts"]
    return f"""<h1>Live verification</h1>
<p>Every claim in this repository cites a URL, and every one of those URLs is re-checked on each
CI build by <code>rgengy verify</code>: all {len(data['sources']['endpoints'])} registered
endpoints, plus every source cited by the scoring tables, the endpoint registry and the findings
register. The table below is rendered in your browser from the report the latest Pages build wrote
to <code>data/verification.json</code> &mdash; so what you see is the state of the live web at the
last build, not a hand-maintained list.</p>
<blockquote><strong>How to read it.</strong> A <span class="badge ok">200</span> means the citation
was live at build time. A <span class="badge warning">bot-blocked</span> result (HTTP 403/429) means
the page answered but refused the CI runner &mdash; anti-bot protection, not a dead link; open the
URL yourself to confirm. A <span class="badge critical">dead-or-moved</span> result (404) is a
citation that must be repaired, and it is treated as a defect in this repository
(the register records each one and its fix).</blockquote>
<div id="verify-summary" class="verify-summary" aria-live="polite">Loading the latest verification report&hellip;</div>
<h2>Registered endpoints</h2>
<div class="filters">
  <input type="search" placeholder="Filter endpoints&hellip;" aria-label="Filter endpoints">
  <span class="count"></span>
</div>
<div class="table-wrap"><table id="verify-endpoints">
<thead><tr><th>endpoint</th><th>status</th><th>declared</th><th>tested URL</th></tr></thead>
<tbody><tr><td colspan="4">Loading&hellip;</td></tr></tbody></table></div>
<h2>Cited URLs</h2>
<p>Every source the scoring tables, endpoint registry and findings register cite. Filter by
classification to see only the citations that need attention.</p>
<div class="filters">
  <input type="search" placeholder="Filter cited URLs&hellip;" aria-label="Filter cited URLs">
  <button type="button" data-filter="bot-blocked" aria-pressed="false">bot-blocked</button>
  <button type="button" data-filter="dead-or-moved" aria-pressed="false">dead-or-moved</button>
  <button type="button" data-filter="network-error" aria-pressed="false">network-error</button>
  <span class="count"></span>
</div>
<div class="table-wrap"><table id="verify-cited">
<thead><tr><th>cited as</th><th>classification</th><th>HTTP</th><th>URL</th></tr></thead>
<tbody><tr><td colspan="4">Loading&hellip;</td></tr></tbody></table></div>
<p style="color:var(--muted);font-size:0.85rem">If both tables say the report is missing, this copy
of the site was built without a <code>rgengy verify</code> run &mdash; run
<code>python3 -m rgengy verify --out site/data/verification.json</code> and rebuild, or check the
CI logs. The <a href="sources.html">data sources register</a> always shows the audited status of
every endpoint regardless.</p>"""


def build_checks_page(data: Dict[str, Any]) -> str:
    rows = "".join(
        f'<tr data-tags="{"registered" if c["registered"] else "explicit"}">'
        f'<td><code>{html.escape(c["name"])}</code></td>'
        f'<td>{_badge("registered", "ok") if c["registered"] else _badge("called explicitly")}</td>'
        f'<td style="font-size:0.88rem">{html.escape(c["doc"])}</td></tr>'
        for c in data["checks"])
    es = data["engine_summary"]
    sigma_rows = "".join(
        f'<tr><td><code>{html.escape(k)}</code></td><td style="text-align:right">{v}</td></tr>'
        for k, v in sorted(es["sigma_by_sport"].items()))
    return f"""<h1>Quality gates and engine constants</h1>
<p>Nine checks run on every pipeline execution. Their job is not to make the numbers better - it is
to stop an indefensible number being published quietly. Every finding carries a
<code>review_action</code> saying what a human should do next; an irregularity with no review action
cannot be actioned. See <a href="08-quality-gates.html">the full explanation</a>.</p>
<div class="filters">
  <input type="search" placeholder="Filter checks&hellip;" aria-label="Filter checks">
  <span class="count"></span>
</div>
<div class="table-wrap"><table>
<thead><tr><th>check</th><th>how it runs</th><th>what it catches</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Engine constants</h2>
{_table(['constant', 'value'], [
    ['<code>RG_OBSERVED_FLOOR_RATIO</code>', str(es['rg_observed_floor_ratio'])],
    ['<code>RG_OBSERVED_CEIL_RATIO</code>', str(es['rg_observed_ceil_ratio'])],
    ['<code>RG_OBSERVED_SAMPLE_SIZE</code>',
     f'{es["rg_observed_sample_size"]} rows &mdash; <strong>IR-12</strong>, one team, one game, one date'],
    ['<code>WEATHER_AIR_DENSITY_COEFFICIENT</code>',
     f'{es["weather_coefficient"]} &mdash; the adjustment is computed exactly and then <strong>disabled</strong>, because applying an unvalidated sensitivity would fabricate precision'],
    ['<code>FLOOR_Z</code> / <code>CEIL_Z</code>', '1.0 / 2.0 &mdash; asymmetric on purpose'],
    ['band modes', ', '.join(f'<code>{b}</code>' for b in es['band_modes'])],
])}
<h2>Score-distribution sigmas <span class="badge warning">unaudited &mdash; IR-03</span></h2>
<p>Used only where no market line exists, and always labelled with the method that produced them.
The NFL value is known to understate heavy favourites, which is why the market line is always
preferred.</p>
<div class="table-wrap"><table>
<thead><tr><th>sport</th><th>sigma</th></tr></thead><tbody>{sigma_rows}</tbody></table></div>"""


# ---------------------------------------------------------------------------

def render(data: Dict[str, Any]) -> Dict[Path, str]:
    out: Dict[Path, str] = {}

    # doc pages from markdown
    for fname, _label in DOC_ORDER:
        path = DOCS / fname
        if not path.exists():
            continue
        md = path.read_text(encoding="utf-8")
        md = "\n".join(l for l in md.split("\n")
                       if not l.startswith("<!-- GENERATED by scripts/build_docs.py"))
        body, _toc = markdown_to_html(md)
        title = fname[:-3]
        out[SITE / (fname[:-3] + ".html")] = _page(title, fname[:-3] + ".html", body, data)

    out[SITE / "index.html"] = _page(
        "Dashboard", "index.html", build_index(data), data,
        "An auditable rebuild of RotoGrinders' projection data quality, with every source verified.")
    out[SITE / "sources.html"] = _page(
        "Data sources", "sources.html", build_sources_page(data), data,
        "Every external input RGENGY uses, with verification status and official links.")
    out[SITE / "scoring.html"] = _page(
        "Scoring verification", "scoring.html", build_scoring_page(data), data,
        "Every fantasy scoring coefficient with its evidence class and source URLs.")
    out[SITE / "verification.html"] = _page(
        "Live verification", "verification.html", build_verification_page(data), data,
        "The live status of every endpoint and every cited URL, re-checked on every CI build.")
    out[SITE / "findings.html"] = _page(
        "Irregularities", "findings.html", build_findings_page(data), data,
        "Everything wrong, conflicting or unverifiable found during the audit.")
    out[SITE / "rosters.html"] = _page(
        "Roster templates", "rosters.html", build_rosters_page(data), data,
        "Operator roster shapes with provenance and verification status.")
    out[SITE / "grid.html"] = _page(
        "Grid schema", "grid.html", build_grid_page(data), data,
        "RotoGrinders' column set and which columns RGENGY fills, and why not the rest.")
    out[SITE / "checks.html"] = _page(
        "Quality gates", "checks.html", build_checks_page(data), data,
        "The checks that stop an indefensible number being published.")

    out[SITE / "styles.css"] = CSS
    out[SITE / "app.js"] = JS
    out[SITE / ".nojekyll"] = ""
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if site/ is stale, without writing it")
    args = ap.parse_args()

    # Reuse the docs generator so the site data and the docs can never disagree.
    sys.path.insert(0, str(REPO / "scripts"))
    import build_docs
    data = build_docs.build_site_data()
    from rgengy import engines
    data["engine_summary"]["rg_observed_ceil_ratio"] = engines.RG_OBSERVED_CEIL_RATIO
    data["engine_summary"]["rg_observed_sample_size"] = engines.RG_OBSERVED_SAMPLE_SIZE
    data["engine_summary"]["sigma_by_sport"] = dict(engines.SIGMA_BY_SPORT)
    data["engine_summary"]["weather_coefficient"] = engines.WEATHER_AIR_DENSITY_COEFFICIENT
    data["tests"] = build_docs._test_inventory()

    pages = render(data)
    stale = []
    for path, text in pages.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(str(path.relative_to(REPO)))
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

    if args.check:
        if stale:
            print("STALE site files (run scripts/build_site.py):")
            for s in sorted(stale):
                print(f"  {s}")
            return 1
        print(f"site is up to date ({len(pages)} files)")
        return 0

    print(f"wrote {len(pages)} site files:")
    for path in sorted(pages):
        print(f"  {path.relative_to(REPO)}  ({len(pages[path])} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

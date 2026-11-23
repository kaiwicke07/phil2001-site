"""Checks for the PHIL 2001 course website.

Run from the repo root:

    python tests/check_site.py            # build, then check everything (needs internet)
    python tests/check_site.py --offline  # skip the external-link check

It checks the three things the project asks for:

1. Every link works. Internal links point to pages and anchors that exist, and every
   external link answers without an error.
2. A newcomer can find any tool fast. Each tool is on the home page, has its own entry
   with an "Open" button and a "Try this" line, and is listed in the "Which tool do I
   need?" table, which comes before the tool entries.
3. Basic accessibility. Each page declares its language and a mobile viewport, has one
   <h1>, gives every image alt text, and has no empty or "click here" links. The full
   WCAG check runs separately with pa11y-ci (see README).

Exits with status 1 if anything fails.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Each tool the home page must offer: (anchor id, name, app URL).
TOOLS = [
    ("replicator", "Replicator Dynamics Explorer", "https://rorysmead.github.io/phil2001-replicator/"),
    ("spatial", "Spatial Evolution Explorer", "https://rorysmead.github.io/phil2001-spatial/"),
]

# Hosts that block scripted requests even though the page is fine in a browser.
SKIP_EXTERNAL = {"fonts.googleapis.com", "fonts.gstatic.com",
                 # Slack answers scripts with 403; the invite was checked in a browser on 2026-11-23
                 "join.slack.com"}

# The site's own address: links to it are checked against the built files instead,
# so the checks pass before the first publish.
SITE_URL = "https://kaiwicke07.github.io/phil2001-site/"

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"  ok    {msg}")


def build() -> None:
    print("Building the site (mkdocs build --strict)...")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--clean"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout, result.stderr)
        sys.exit("Build failed, so nothing else was checked.")
    ok("site builds with no warnings")


def pages() -> list[Path]:
    # Skip MkDocs' own 404 page and the search index; check every real page.
    return sorted(p for p in SITE.rglob("*.html") if p.name != "404.html")


def soup_of(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def resolve_internal(page: Path, href: str) -> tuple[Path, str]:
    url, frag = urldefrag(href)
    if not url:
        return page, frag
    target = (page.parent / unquote(url)).resolve()
    if target.is_dir() or url.endswith("/"):
        target = target / "index.html"
    return target, frag


def check_links() -> set[str]:
    print("\n1. Links")
    externals: set[str] = set()
    ids_cache: dict[Path, set[str]] = {}
    count = 0
    for page in pages():
        soup = soup_of(page)
        rel = page.relative_to(SITE)
        for tag, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src")):
            for el in soup.find_all(tag):
                href = el.get(attr)
                if not href or href.startswith(("mailto:", "javascript:", "data:")):
                    continue
                count += 1
                if href.startswith(SITE_URL):
                    href = "/" + href[len(SITE_URL):]
                    target, frag = resolve_internal(SITE / "index.html", "." + href)
                    if not target.exists():
                        fail(f"{rel}: link to missing page on this site {href}")
                    continue
                if urlparse(href).scheme in ("http", "https"):
                    externals.add(href)
                    continue
                target, frag = resolve_internal(page, href)
                if not target.exists():
                    fail(f"{rel}: link to missing file {href}")
                    continue
                if frag and target.suffix == ".html":
                    if target not in ids_cache:
                        ids_cache[target] = {e["id"] for e in soup_of(target).find_all(id=True)}
                    if frag not in ids_cache[target]:
                        fail(f"{rel}: link to missing anchor {href}")
    ok(f"checked {count} internal links and references across {len(pages())} pages")
    return externals


def check_external(urls: set[str]) -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (link checker for a course website)"
    checked = 0
    for url in sorted(urls):
        host = urlparse(url).hostname or ""
        if host in SKIP_EXTERNAL:
            continue
        status = None
        for attempt in range(3):
            try:
                r = session.get(url, timeout=20, allow_redirects=True)
                status = r.status_code
                if status < 400:
                    break
            except requests.RequestException as e:
                status = type(e).__name__
            time.sleep(1.5 * (attempt + 1))
        checked += 1
        if isinstance(status, int) and status < 400:
            ok(f"{status}  {url}")
        else:
            fail(f"external link {url} -> {status}")
    print(f"        ({checked} external links checked)")


def check_tools() -> None:
    print("\n2. Finding a tool")
    home = soup_of(SITE / "index.html")
    text_order = str(home)
    table = home.find("table")
    table_links = {a.get("href") for a in table.find_all("a")} if table else set()
    for anchor, name, app in TOOLS:
        entry = home.find(id=anchor)
        if entry is None:
            fail(f"{name}: no entry with id #{anchor} on the home page")
            continue
        if entry.find(["h2", "h3"], string=lambda s: s and name in s) is None:
            fail(f"{name}: entry has no heading with the tool's name")
        opens = [a for a in entry.find_all("a") if a.get("href") == app]
        if not opens or not opens[0].get_text(strip=True).lower().startswith("open"):
            fail(f"{name}: no 'Open' button linking to {app}")
        if "try this" not in entry.get_text(" ").lower():
            fail(f"{name}: no 'Try this' line")
        if f"#{anchor}" not in table_links:
            fail(f"{name}: not linked from the 'Which tool do I need?' table")
        if not (table and text_order.find(str(table)[:60]) < text_order.find(f'id="{anchor}"')):
            fail(f"{name}: the 'Which tool' table should come before the tool entries")
        else:
            ok(f"{name}: on the home page, in the guide table, with Open and Try this")
    # The search box is the other route to a tool.
    if not (SITE / "search" / "search_index.json").exists():
        fail("site search index is missing")
    else:
        ok("site search is built")


def check_a11y() -> None:
    print("\n3. Accessibility basics")
    bad_text = {"click here", "here", "link", "more", "read more"}
    for page in pages():
        rel = page.relative_to(SITE)
        soup = soup_of(page)
        problems = []
        if not (soup.html and soup.html.get("lang")):
            problems.append("no lang attribute on <html>")
        vp = soup.find("meta", attrs={"name": "viewport"})
        if not vp or "width=device-width" not in vp.get("content", ""):
            problems.append("no mobile viewport meta tag")
        content = soup.find("article") or soup
        h1s = content.find_all("h1")
        if len(h1s) != 1:
            problems.append(f"{len(h1s)} <h1> headings in the content (want 1)")
        for img in soup.find_all("img"):
            if img.get("alt") is None:
                problems.append(f"image without alt text: {img.get('src')}")
        for a in content.find_all("a"):
            label = a.get_text(" ", strip=True) or a.get("aria-label") or a.get("title") or ""
            if not label:
                problems.append(f"link with no text: {a.get('href')}")
            elif label.lower() in bad_text:
                problems.append(f"vague link text '{label}': {a.get('href')}")
        if problems:
            for p in problems:
                fail(f"{rel}: {p}")
        else:
            ok(f"{rel}")


def main() -> None:
    offline = "--offline" in sys.argv
    build()
    externals = check_links()
    if offline:
        print("        (external links skipped: --offline)")
    else:
        check_external(externals)
    check_tools()
    check_a11y()
    print()
    if failures:
        print(f"{len(failures)} problem(s) found.")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

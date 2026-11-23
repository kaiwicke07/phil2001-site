# PHIL 2001 course tools website

One public page that lists every simulation tool for PHIL 2001, *Ethics and Evolutionary
Games*, with a line on what each tool does, one thing to try, and a screenshot.

**Site:** https://kaiwicke07.github.io/phil2001-site/

This is Project 6 ("A course website") from the class project's Apps and Tools list.

## What it does

- The home page lists each course tool: the Replicator Dynamics Explorer and the Spatial
  Evolution Explorer. Each entry has a short description, a "Try this" exercise, a real
  screenshot, a button to open the app, and links to its code in Colab and on GitHub.
- A "Which tool do I need?" table at the top sends you to the right tool by what you want
  to do.
- A search box in the header finds any tool or word on the site.
- It works on a phone. It follows your device's light or dark setting, and the sun/moon
  button switches it by hand.
- A Contribute page explains how to suggest changes, the consent rule, and credits.

## How to use it

Open the link above. Pick a tool from the table or the list and press its blue
**Open** button. The tools run Python inside your browser, so the first load can take up to
a minute. Nothing needs to be installed.

## How it works

The site is a set of plain text (Markdown) files turned into web pages by
[MkDocs](https://www.mkdocs.org/) with the
[Material](https://squidfunk.github.io/mkdocs-material/) theme. MkDocs is written in Python.
GitHub Pages hosts the pages, which is where the course tools already live.

Every time a change lands on GitHub, a GitHub Action builds the site, runs the checks
below, and publishes it only if they all pass.

| File | What it is |
|---|---|
| `docs/index.md` | The home page with the tool list. Edit this to add a tool. |
| `docs/contribute.md` | The Contribute page. |
| `docs/assets/site.css` | The colours, fonts and layout. |
| `docs/assets/shots/` | The tool screenshots. |
| `mkdocs.yml` | Site settings: name, menu, theme. |
| `tests/check_site.py` | The checks. |
| `.github/workflows/deploy.yml` | Builds, checks and publishes the site on GitHub. |

## Adding a tool

1. Open `docs/index.md` on GitHub and press the pencil (edit) button.
2. Copy one of the `<section class="tool" ...>` blocks, give it a new `id`, and change the
   name, description, "Try this" line and links.
3. Add a screenshot to `docs/assets/shots/` and point the block's `<img>` at it, with alt
   text that says what the picture shows.
4. Add a row for it to the "Which tool do I need?" table.
5. Add the tool to the `TOOLS` list at the top of `tests/check_site.py`, so the checks
   make sure it stays findable.

Contributed work only goes up with its author's consent.

## The checks

The project asks for three: every link works, a newcomer can find a given tool in under a
minute, and the pages pass an accessibility check.

`tests/check_site.py` tests all three:

1. **Links.** Builds the site in strict mode (any broken page link stops the build), then
   follows every link on every page. Internal links must reach a real page and section.
   External links must answer without an error.
2. **Finding a tool.** Each tool must have its own entry on the home page with its name as
   a heading, an **Open** button to the app, and a "Try this" line. It must also appear in
   the "Which tool do I need?" table, which sits above the entries. The search index must
   exist. That puts every tool one click from the top of the home page.
3. **Accessibility basics.** Each page declares its language and a phone-friendly viewport
   and has one main heading. Every image has alt text, and no link is empty or vague
   ("click here").

To run them on your own computer (needs Python 3.10 or newer):

```bash
python -m venv .venv
.venv/Scripts/activate        # on Mac or Linux: source .venv/bin/activate
pip install -r requirements.txt
python tests/check_site.py            # add --offline to skip the external links
```

The full accessibility check uses Lighthouse in Chrome (DevTools, then the Lighthouse tab,
with Accessibility ticked). It runs the axe accessibility engine against the WCAG
guidelines. On 2026-11-23 both pages scored **100/100** on phone and desktop, in light and
dark mode, after three fixes: underlined links in running text, a darker footer text
colour, and a label on the search box.

To preview the site while editing: `mkdocs serve`, then open http://127.0.0.1:8000.

## Tools used

Built by Kai Wicke with **Claude Code** (Anthropic's AI coding assistant, model Claude Opus
5.5). Claude wrote most of the code, the checks and this readme, and took the tool
screenshots. I chose the project, reviewed the pages, and checked every "Try this" line
against the tools. The Replicator line was checked against `replicator.py` (all-cooperate
becomes stable once r passes 0.5). The Spatial line was checked against a live run
(31.2% cooperate after 150 generations with self-play on).

## Licence

MIT, the same as the course tools. See [LICENSE](LICENSE).

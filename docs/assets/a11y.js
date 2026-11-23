// Small accessibility fixes for things the Material theme renders.
document$.subscribe(function () {
  // The search dialog ships without an accessible name.
  var search = document.querySelector(".md-search[role='dialog']");
  if (search && !search.hasAttribute("aria-label")) {
    search.setAttribute("aria-label", "Search the site");
  }
  // Icons inside links and buttons that already have a name are decoration.
  document.querySelectorAll("a svg, button svg, label svg").forEach(function (svg) {
    if (!svg.hasAttribute("aria-label")) svg.setAttribute("aria-hidden", "true");
  });
});

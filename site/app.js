
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

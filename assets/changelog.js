// Changelog filter: one component (its id also in the address, changelog.html#service), the others hidden.
(function () {
  var selects = document.querySelectorAll(".log-filter select");
  var log = document.querySelector(".log");
  if (!selects.length || !log) return;
  function apply(v, push) {
    selects.forEach(function (s) { s.value = v; });
    log.querySelectorAll("li[data-c]").forEach(function (li) { li.hidden = !!v && li.dataset.c !== v; });
    log.querySelectorAll(".day-block").forEach(function (d) { d.hidden = !d.querySelector("li:not([hidden])"); });
    log.querySelectorAll("details.month").forEach(function (m, i) {
      var any = !!m.querySelector("li:not([hidden])");
      m.hidden = !any;
      var n = m.querySelectorAll("li:not([hidden])").length;
      var c = m.querySelector(".count");
      if (c) c.textContent = String(n);
      if (v && any) m.open = true;
    });
    if (push) {
      try { history.replaceState(null, "", v ? "#" + v : location.pathname + location.search); } catch (e) {}
    }
  }
  selects.forEach(function (s) { s.addEventListener("change", function () { apply(s.value, true); }); });
  var h = decodeURIComponent(location.hash.slice(1));
  if (h && log.querySelector('li[data-c="' + h.replace(/"/g, "") + '"]')) apply(h, false);
})();

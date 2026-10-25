// Language buttons; the choice itself is made in the page's <head> (before drawing) and kept in localStorage.
(function () {
  function set(lang) {
    document.documentElement.setAttribute("data-lang", lang);
    document.documentElement.lang = lang;
    try { localStorage.setItem("lang", lang); } catch (e) {}
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    });
    var t = document.querySelector('meta[name="title-' + lang + '"]');
    if (t) document.title = t.content;
  }
  document.querySelectorAll(".lang button").forEach(function (b) {
    b.addEventListener("click", function () { set(b.dataset.lang); });
  });
  set(document.documentElement.getAttribute("data-lang") || "en");
})();

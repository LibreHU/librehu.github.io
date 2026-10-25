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

// Menu on small screens.
(function () {
  var button = document.querySelector(".menu");
  var nav = document.getElementById("nav");
  if (!button || !nav) return;
  button.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
  nav.addEventListener("click", function (e) {
    if (e.target.closest("a")) { nav.classList.remove("open"); button.setAttribute("aria-expanded", "false"); }
  });
})();

// Discord: member and online counts from the public invite (shown only when the request works).
(function () {
  var slots = document.querySelectorAll("[data-discord]");
  if (!slots.length || !window.fetch) return;
  fetch("https://discord.com/api/v10/invites/aP4JZMavxB?with_counts=true")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || d.approximate_member_count == null) return;
      slots.forEach(function (el) {
        var v = el.dataset.discord === "online" ? d.approximate_presence_count : d.approximate_member_count;
        el.textContent = String(v);
        var wrap = el.closest("[data-discord-counts]");
        if (wrap) wrap.hidden = false;
      });
    })
    .catch(function () {});
})();

// Contents of long pages: folded on small screens, folded again after following a link.
(function () {
  var toc = document.querySelector(".toc details");
  if (!toc || !window.matchMedia) return;
  var small = window.matchMedia("(max-width: 900px)");
  if (small.matches) toc.open = false;
  toc.addEventListener("click", function (e) {
    if (small.matches && e.target.closest("a")) toc.open = false;
  });
})();

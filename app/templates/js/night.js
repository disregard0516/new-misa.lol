(function () {
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var save = navigator.connection && navigator.connection.saveData;
  var halo = document.querySelector("[data-halo]");
  if (halo) halo.remove();

  function $$(s, r) { return [].slice.call((r || document).querySelectorAll(s)); }

  function armVideo(v) {
    if (!v || v.dataset.armed === "1") return;
    v.dataset.armed = "1";
    var src = v.dataset.src || v.dataset.srcWebm || v.dataset.srcMp4;
    if (!src) return;
    v.src = src;
    v.play && v.play().catch(function () {});
  }

  $$("video.phone__video[data-src]").forEach(function (v) {
    if (v.dataset.poster && !v.getAttribute("poster")) v.setAttribute("poster", v.dataset.poster);
  });

  if (reduce || save) return;
  var kick = function () {
    $$("video.phone__video[data-src]").forEach(function (v) {
      var ph = v.closest(".phone");
      if (ph && !ph.classList.contains("video-on")) return;
      armVideo(v);
    });
  };
  if ("requestIdleCallback" in window) requestIdleCallback(kick, { timeout: 2800 });
  else setTimeout(kick, 1200);
})();

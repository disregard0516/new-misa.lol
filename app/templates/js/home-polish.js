(function () {
  "use strict";

  var hero = document.querySelector(".mk-hero");
  if (!hero) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".mk-nav a[href^='/#']"));
  var sections = navLinks
    .map(function (link) {
      var id = link.getAttribute("href").split("#")[1];
      return id ? document.getElementById(id) : null;
    })
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    var sectionObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          navLinks.forEach(function (link) {
            var current = link.getAttribute("href") === "/#" + entry.target.id;
            link.classList.toggle("is-active", current);
            if (current) link.setAttribute("aria-current", "location");
            else link.removeAttribute("aria-current");
          });
        });
      },
      { rootMargin: "-25% 0px -65% 0px", threshold: 0 }
    );
    sections.forEach(function (section) {
      sectionObserver.observe(section);
    });
  }

  if (reduceMotion || !window.matchMedia("(pointer: fine)").matches) return;

  var frame = 0;
  var nextX = 50;
  var nextY = 50;

  function paint() {
    frame = 0;
    var x = (nextX - 50) / 50;
    var y = (nextY - 50) / 50;
    hero.style.setProperty("--spot-x", nextX.toFixed(2) + "%");
    hero.style.setProperty("--spot-y", nextY.toFixed(2) + "%");
    hero.style.setProperty("--art-x", (x * -8).toFixed(2) + "px");
    hero.style.setProperty("--art-y", (y * -5).toFixed(2) + "px");
    hero.style.setProperty("--tilt-x", (x * 1.8).toFixed(2) + "deg");
    hero.style.setProperty("--tilt-y", (y * -1.2).toFixed(2) + "deg");
  }

  hero.addEventListener(
    "pointermove",
    function (event) {
      var box = hero.getBoundingClientRect();
      nextX = ((event.clientX - box.left) / box.width) * 100;
      nextY = ((event.clientY - box.top) / box.height) * 100;
      if (!frame) frame = requestAnimationFrame(paint);
    },
    { passive: true }
  );

  hero.addEventListener("pointerleave", function () {
    nextX = 50;
    nextY = 50;
    if (!frame) frame = requestAnimationFrame(paint);
  });
})();

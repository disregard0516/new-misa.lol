(function () {
  "use strict";

  var hero = document.querySelector(".mk-hero");
  if (!hero) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(pointer: fine)").matches;
  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav__links a[href^='/#']"));
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

  function revealCurrentTarget() {
    if (!window.location.hash) return;
    var target = document.getElementById(window.location.hash.slice(1));
    if (!target) return;
    target.classList.add("in");
    Array.prototype.forEach.call(target.querySelectorAll(".reveal"), function (element) {
      element.classList.add("in");
    });
  }

  revealCurrentTarget();
  window.addEventListener("hashchange", revealCurrentTarget);

  Array.prototype.forEach.call(document.querySelectorAll(".spec-more"), function (details) {
    details.addEventListener("toggle", function () {
      if (!details.open) return;
      Array.prototype.forEach.call(details.querySelectorAll(".reveal"), function (element, index) {
        window.setTimeout(function () {
          element.classList.add("in");
        }, reduceMotion ? 0 : Math.min(index * 35, 280));
      });
    });
  });

  if (!reduceMotion && window.gsap) {
    document.documentElement.classList.add("has-gsap");
    window.gsap.from(".mk-copy > *", {
      opacity: 0,
      y: 24,
      duration: 0.72,
      stagger: 0.085,
      ease: "power3.out",
      clearProps: "opacity,transform"
    });
  }

  if (!reduceMotion && document.startViewTransition) {
    Array.prototype.forEach.call(document.querySelectorAll(".swatch[data-set-theme]"), function (swatch) {
      swatch.addEventListener("click", function transitionTheme(event) {
        if (swatch.dataset.transitioning === "true") return;
        event.preventDefault();
        event.stopImmediatePropagation();
        document.startViewTransition(function () {
          swatch.dataset.transitioning = "true";
          swatch.click();
          delete swatch.dataset.transitioning;
        });
      }, true);
    });
  }

  var demoRows = document.querySelectorAll(".spec__row");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var demoObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          entry.target.classList.toggle("is-demo-live", entry.isIntersecting);
        });
      },
      { rootMargin: "8% 0px 8% 0px", threshold: 0.18 }
    );
    Array.prototype.forEach.call(demoRows, function (row) {
      demoObserver.observe(row);
    });
  } else {
    Array.prototype.forEach.call(demoRows, function (row) {
      row.classList.add("is-demo-live");
    });
  }

  var scanlines = document.createElement("div");
  scanlines.className = "mk-scanlines";
  scanlines.setAttribute("aria-hidden", "true");
  document.body.appendChild(scanlines);

  var vhsButton = document.querySelector(".mk-vhs");
  if (vhsButton) {
    vhsButton.addEventListener("click", function () {
      var enabled = !document.body.classList.contains("is-vhs");
      document.body.classList.toggle("is-vhs", enabled);
      vhsButton.setAttribute("aria-pressed", String(enabled));
      vhsButton.setAttribute("aria-label", enabled ? "Turn VHS scanlines off" : "Turn VHS scanlines on");
      vhsButton.querySelector("span").textContent = enabled ? "VHS on" : "VHS off";
    });
  }

  var soundButton = document.querySelector(".mk-sound");
  var soundOn = false;
  var audioContext = null;
  function tick() {
    if (!soundOn) return;
    audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
    var oscillator = audioContext.createOscillator();
    var gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = 720;
    gain.gain.setValueAtTime(0.018, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.025);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.03);
  }
  if (soundButton && (window.AudioContext || window.webkitAudioContext)) {
    soundButton.addEventListener("click", function () {
      soundOn = !soundOn;
      soundButton.setAttribute("aria-pressed", String(soundOn));
      soundButton.setAttribute("aria-label", soundOn ? "Turn interface sounds off" : "Turn interface sounds on");
      soundButton.querySelector("span").textContent = soundOn ? "sound on" : "sound off";
      tick();
    });
    Array.prototype.forEach.call(document.querySelectorAll("a,button,summary"), function (control) {
      control.addEventListener("pointerenter", tick, { passive: true });
    });
  }

  var loop = document.querySelector(".mk-hero-loop");
  if (loop) {
    loop.removeAttribute("data-src");
    loop.removeAttribute("data-src-webm");
    loop.pause && loop.pause();
    loop.remove();
  }

  var viewEl = document.querySelector("[data-live-views]");
  if (viewEl) {
    var views = 12400;
    setInterval(function () {
      views += 1;
      viewEl.textContent = (views / 1000).toFixed(1) + "k";
    }, 2400);
  }

  var claimedEl = document.querySelector("[data-claimed-n]");
  if (claimedEl) {
    var claimed = 8 + (new Date().getMinutes() % 9);
    claimedEl.textContent = String(claimed);
    setInterval(function () {
      if (Math.random() > 0.55) {
        claimed += 1;
        claimedEl.textContent = String(claimed);
      }
    }, 9000);
  }

  var orbit = document.getElementById("wall-orbit");
  var wallRing = document.getElementById("wall");
  var wallStage = document.getElementById("wall-stage");
  if (orbit && wallRing && wallRing.classList.contains("wall--ring")) {
    var ringItems = [];
    var ringAngle = 0;
    var ringDrag = false;
    var ringMoved = false;
    var ringX = 0;
    var ringT = 0;
    var ringV = 0;
    var ringSnapTimer = 0;
    var RING_TILT = 64;
    orbit.tabIndex = 0;

    function ringCollect() {
      ringItems = Array.prototype.slice.call(wallRing.querySelectorAll(".wall__item"));
    }

    function ringPaint() {
      var n = ringItems.length;
      if (!n) return;
      var step = 360 / n;
      var compact = window.matchMedia("(max-width:820px)").matches;
      var half = compact ? 52 : 80;
      var fits = window.innerWidth / 2 - half - 10;
      var radius = Math.min(compact ? 170 : 260, Math.max(110, fits));
      if (wallStage) {
        wallStage.style.transform = "rotateX(" + RING_TILT + "deg) rotateZ(" + ringAngle.toFixed(2) + "deg)";
      }
      var i;
      for (i = 0; i < n; i++) {
        var local = i * step;
        var rad = (local * Math.PI) / 180;
        var x = Math.sin(rad) * radius;
        var y = Math.cos(rad) * radius;
        var world = ((local + ringAngle) % 360 + 360) % 360;
        var front = Math.cos((world * Math.PI) / 180);
        var item = ringItems[i];
        item.style.transform =
          "translate3d(" +
          x.toFixed(1) +
          "px," +
          y.toFixed(1) +
          "px,0) rotateZ(" +
          (-ringAngle).toFixed(2) +
          "deg) rotateX(" +
          (-RING_TILT) +
          "deg)";
        var lead = front > 0.96;
        item.style.zIndex = String(Math.round(40 + front * 80));
        item.style.opacity = lead ? "1" : "0";
        item.style.pointerEvents = lead ? "auto" : "none";
        item.classList.toggle("is-front", lead);
      }
    }

    function ringSnap() {
      var n = ringItems.length;
      if (!n) return;
      var step = 360 / n;
      ringAngle = -Math.round(-ringAngle / step) * step;
      ringPaint();
    }

    function ringGo(dir, steps) {
      var n = ringItems.length;
      if (!n) return;
      ringAngle -= dir * (steps || 1) * (360 / n);
      ringSnap();
    }

    function ringBoot() {
      ringCollect();
      if (!ringItems.length) {
        window.setTimeout(ringBoot, 40);
        return;
      }
      ringPaint();
    }
    ringBoot();
    window.addEventListener("resize", ringPaint);


    var prevBtn = orbit.querySelector(".wall-orbit__nav--prev");
    var nextBtn = orbit.querySelector(".wall-orbit__nav--next");
    if (prevBtn) prevBtn.addEventListener("click", function () { ringGo(-1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { ringGo(1); });

    orbit.addEventListener("pointerdown", function (event) {
      if (event.target.closest(".wall-orbit__nav")) return;
      ringDrag = true;
      ringMoved = false;
      orbit.classList.add("is-dragging");
      ringX = event.clientX;
      ringT = performance.now();
      ringV = 0;
      orbit.setPointerCapture(event.pointerId);
    });
    orbit.addEventListener("pointermove", function (event) {
      if (!ringDrag) return;
      var dx = event.clientX - ringX;
      if (Math.abs(dx) > 5) ringMoved = true;
      var now = performance.now();
      ringV = dx / Math.max(1, now - ringT);
      ringX = event.clientX;
      ringT = now;
      ringAngle += dx * 0.42;
      ringPaint();
    });
    function ringEnd() {
      if (!ringDrag) return;
      ringDrag = false;
      orbit.classList.remove("is-dragging");
      var speed = Math.abs(ringV);
      if (speed > 0.22) {
        ringGo(ringV > 0 ? -1 : 1, Math.min(4, Math.max(1, Math.round(speed * 2.6))));
      } else {
        ringSnap();
      }
    }
    orbit.addEventListener("pointerup", ringEnd);
    orbit.addEventListener("pointercancel", ringEnd);

    wallRing.addEventListener("click", function (event) {
      if (ringMoved) {
        event.preventDefault();
        event.stopImmediatePropagation();
        ringMoved = false;
        return;
      }
      var item = event.target.closest(".wall__item");
      if (!item) return;
      var idx = ringItems.indexOf(item);
      if (idx < 0) return;
      ringAngle = -idx * (360 / ringItems.length);
      ringPaint();
    }, true);

    orbit.addEventListener("wheel", function (event) {
      if (Math.abs(event.deltaX) < Math.abs(event.deltaY) && !event.shiftKey) return;
      event.preventDefault();
      ringAngle += (event.shiftKey ? event.deltaY : event.deltaX) * 0.14;
      ringPaint();
      window.clearTimeout(ringSnapTimer);
      ringSnapTimer = window.setTimeout(ringSnap, 140);
    }, { passive: false });

    orbit.addEventListener("keydown", function (event) {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        ringGo(-1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        ringGo(1);
      }
    });
  }

  if (reduceMotion || !finePointer) return;

  document.documentElement.classList.add("has-star-cursor");

  Array.prototype.forEach.call(document.querySelectorAll(".nav .btn[data-claim],.mk-claim__btn,.cta .claim__btn"), function (button) {
    button.addEventListener("pointermove", function (event) {
      var box = button.getBoundingClientRect();
      var x = (event.clientX - box.left - box.width / 2) * 0.16;
      var y = (event.clientY - box.top - box.height / 2) * 0.2;
      button.style.transform = "translate3d(" + x.toFixed(1) + "px," + y.toFixed(1) + "px,0)";
    });
    button.addEventListener("pointerleave", function () {
      button.style.transform = "";
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll(".steps__item,.spec__row,.tier-col"), function (card) {
    card.addEventListener("pointermove", function (event) {
      var box = card.getBoundingClientRect();
      card.style.setProperty("--card-x", ((event.clientX - box.left) / box.width * 100).toFixed(1) + "%");
      card.style.setProperty("--card-y", ((event.clientY - box.top) / box.height * 100).toFixed(1) + "%");
    }, { passive: true });
  });

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

  var scrollFrame = 0;
  function paintScroll() {
    scrollFrame = 0;
    var progress = Math.max(0, Math.min(1, window.scrollY / Math.max(hero.offsetHeight, 1)));
    hero.style.setProperty("--paper-shift", (progress * 34).toFixed(1) + "px");
  }
  window.addEventListener("scroll", function () {
    if (!scrollFrame) scrollFrame = requestAnimationFrame(paintScroll);
  }, { passive: true });

  var screen = document.querySelector(".mk-screen");
  if (screen) {
    screen.addEventListener("pointermove", function (event) {
      var box = screen.getBoundingClientRect();
      var rx = ((event.clientY - box.top) / box.height - 0.5) * -10;
      var ry = ((event.clientX - box.left) / box.width - 0.5) * 12;
      screen.style.transform = "perspective(1200px) rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg)";
    }, { passive: true });
    screen.addEventListener("pointerleave", function () {
      screen.style.transform = "";
    });
  }
})();

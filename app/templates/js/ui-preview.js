/* offline fill for dashboard + admin when no backend is running */
(function () {
  var path = (location.pathname || "").replace(/\/+$/, "") || "/";
  var on = !!window.MISA_UI_PREVIEW || path === "/ui" || /(?:^|[?&])preview=1(?:&|$)/.test(location.search || "");
  if (!on) return;

  function isoDays(n) {
    var out = [];
    var now = new Date();
    for (var i = n - 1; i >= 0; i--) {
      var d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - i));
      out.push(d.toISOString().slice(0, 10));
    }
    return out;
  }
  var days = isoDays(14);
  var counts = [12, 18, 9, 22, 31, 14, 27, 40, 19, 25, 33, 28, 36, 44];
  var t = Math.floor(Date.now() / 1000);
  var nowIso = new Date().toISOString();

  var users = [
    { id: "u1", username: "you", display_name: "you", email: "you@localhost", is_admin: false, created_at: nowIso, last_login_at: nowIso, suspended_at: null, suspension_reason: null, suspended_until: null },
    { id: "u2", username: "ren", display_name: "ren", email: "ren@localhost", is_admin: false, created_at: nowIso, last_login_at: nowIso, suspended_at: null },
    { id: "u3", username: "valer", display_name: "valer", email: "valer@localhost", is_admin: true, created_at: nowIso, last_login_at: nowIso, suspended_at: null },
  ];
  var entitlements = [{ user_id: "u1", plan: "supporter", active: true, expires_at: null, granted_by: "u3", created_at: nowIso }];
  var badges = [{ id: "early", name: "early", description: "first wave", color: "#F00646" }, { id: "verified", name: "verified", description: "blue check", color: "#3b82f6" }];
  var reserved = [{ username: "staff", reason: "brand", created_at: nowIso }];
  var reports = [{ id: "r1", target_username: "noise", target_user_id: "u2", reason: "spam", details: "demo row", status: "open", created_at: nowIso }];
  var flags = [{ key: "templates", description: "Template creator", enabled: false }, { key: "help_center", description: "Help Center", enabled: false }];
  var logs = [{ created_at: nowIso, actor_user_id: "u3", action: "preview.open", target_type: "ui", target_id: "local", metadata: { mode: "offline" } }];

  var profile = {
    profile: {
      username: "you",
      displayName: "you",
      description: "be weird online again.",
      location: "the void",
      pronouns: "they/them",
      views: 12840,
      uid: "preview",
    },
    settings: {
      accentColor: "#F00646",
      textColor: "#F2F2F0",
      backgroundColor: "#050606",
      backgroundColor2: "#1a0a10",
      iconColor: "#F00646",
      profileOpacity: 0.72,
      backgroundOpacity: 0.55,
      profileBlur: 16,
      profileRadius: 28,
      profileGradient: true,
      layout: "modern",
      seoTitle: "you · misa.lol",
      seoDescription: "links, music, a little shrine.",
      linkAlign: "center",
      showViews: true,
      showBadges: true,
      showSocials: true,
      backgroundEffect: "Glow",
      usernameEffect: "Shimmer",
      font: "playfair",
      playerStyle: "bars",
      linkStyle: "pill",
      replay: true,
    },
    assets: {
      avatar: { url: "/images/favicon.svg" },
      background: { url: null },
      backgroundVideo: { url: null },
      audio: { url: null, name: "now playing", cover: null },
      cursor: { url: null },
      audioEnabled: true,
      volume: 0.6,
    },
    socials: [
      { id: "s1", platform: "X", label: "x", value: "https://x.com", enabled: true, displayMode: "link", clicks: 420 },
      { id: "s2", platform: "Discord", label: "discord", value: "https://discord.gg", enabled: true, displayMode: "link", clicks: 88 },
      { id: "s3", platform: "Custom URL", label: "copy this", value: "misa.lol/you", enabled: true, displayMode: "text", clicks: 12 },
    ],
    badges: [{ id: "early", name: "early", description: "", color: "#F00646", owned: true, enabled: true }],
  };

  window.MISA_DEMO = {
    offline: false,
    pricing: "/pricing",
    card: "/images/share.png",
    qr: "/preview/qr.png",
    "/api/v1/me": {
      id: "u3",
      username: "valer",
      display_name: "valer",
      email: "valer@localhost",
      plan: "supporter",
      avatar_url: "/images/favicon.svg",
      is_admin: true,
      providers: { email: true, google: false, discord: false, telegram: false },
      badges: profile.badges,
    },
    "/api/v1/profile/me": { profile: profile },
    "/api/v1/me/stats": {
      views: 12840,
      today: 44,
      week: 312,
      daily: days.map(function (d, i) { return [d, counts[i]]; }),
      referrers: [["tiktok.com", 210], ["x.com", 90], ["discord.com", 40]],
      clicks: [["s1", "x", 420], ["s2", "discord", 88], ["s3", "copy this", 12]],
      countries: [["IN", 5120], ["US", 3080], ["DE", 940], ["GB", 610], ["BR", 380], ["JP", 210]],
    },
    "/api/v1/me/replay": {
      on: true,
      kept_for_days: 7,
      visits: [
        { at: t - 90, from: "tiktok.com", device: "phone", seconds: 18, events: [{ k: "in", after: 0 }, { k: "tap", d: "s1", after: 4 }] },
        { at: t - 3600, from: "", device: "desktop", seconds: 42, events: [{ k: "in", after: 0 }, { k: "tap", d: "s2", after: 12 }] },
        { at: t - 7200, from: "x.com", device: "phone", seconds: 8, events: [{ k: "in", after: 0 }] },
      ],
    },
    "/api/v1/me/guestbook": { pending: [], approved: [] },
    "/api/v1/me/doodles": { pending: [], approved: [] },
    "/api/v1/me/asks": { waiting: [], answered: [] },
  };

  window.MISA_DEMO_ADMIN = {
    handle: function (method, path) {
      var p = String(path || "").split("?")[0];
      if (method === "GET" && p === "/users") return { users: users };
      if (method === "GET" && p === "/entitlements") return { entitlements: entitlements };
      if (method === "GET" && p === "/badges") return { badges: badges };
      if (method === "GET" && p === "/reserved-usernames") return { usernames: reserved };
      if (method === "GET" && p === "/reports") return { reports: reports };
      if (method === "GET" && p === "/feature-flags") return { flags: flags };
      if (method === "GET" && p === "/audit-logs") return { logs: logs };
      return { ok: true };
    },
  };

  function unlockAuth() {
    document.querySelectorAll(".auth-lock").forEach(function (el) {
      el.classList.remove("is-locked");
      el.removeAttribute("inert");
      try { el.inert = false; } catch (e) {}
      el.querySelectorAll("input, button, textarea, select").forEach(function (n) {
        n.disabled = false;
        n.removeAttribute("required");
      });
      el.querySelectorAll("a").forEach(function (a) { a.removeAttribute("tabindex"); });
    });
    var gate = document.querySelector("[data-lock-note]");
    if (gate) gate.hidden = true;
    var box = document.querySelector(".turnstile-box");
    if (box) box.hidden = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", unlockAuth);
  } else {
    unlockAuth();
  }
})();

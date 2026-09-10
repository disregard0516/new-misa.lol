# misa.lol — what the pages promise vs. what the code does (v3.103, 2026-09-09 19:56Z · updated v3.112 as features land)

Every product claim on the front page and the pricing page, checked against the repo (`app/core/plans.py` GATES, `app/profile_page.py`, `app/api/v1/uploads.py`, `app/api/v1/users.py`, `app/share_card.py`). Nothing on the pages was changed — this is the list for Valer to decide on: fix the copy, or build the thing. The copy on both pages was carried over from the original site.

Legend: **yes** = the code does it · **policy** = true by what the team does, not by code · **partly** = something close exists · **no** = nothing in the repo does this.

## Free (front page tier card + pricing)

| Claim | Status | What the code says |
|---|---|---|
| misa.lol/yourname | yes | username claim + public page |
| Unlimited links | yes (as far as the API goes) | no cap on `socials` in `api/v1/profile.py`; the preview phone draws 4 and says “+N more” |
| Music player + hidden mode | partly | a player with any track URL (`assets.audio`); “hidden mode” is the *play audio* toggle (player off, track kept) — no separate owner-only mode |
| Analytics · “Views, where they came from, what they clicked. On every plan” | yes | `/me/stats`: total / today / 7 days / 14 daily buckets, referrers, link clicks — **not plan-gated**, so “full analytics” for paid plans (pricing table, twice) is the same thing |
| Themes, socials, bio — the basics | yes | |
| free forever · not a subscription · one payment, yours for life | yes / note | entitlements are one-time; `plan_expires_at` exists in the API and the dashboard shows “until <date>” when set — “yours for life” holds only if you never set an expiry |
| live in under a minute | policy | the sign-up is short; nobody measured it (flagged since v3.4) |

## Lifetime ($5)

| Claim | Status | What the code says |
|---|---|---|
| Verified blue check | policy | badges are granted by the team in admin (`user_badges`); nothing grants one automatically on purchase — the dashboard already says so |
| Video backgrounds | yes | `assets.backgroundVideo.url`, gated rank 1; uploads up to 32 MB mp4/webm |
| Animated backgrounds | yes | `settings.backgroundEffect` particles / stars / glow, gated rank 1 |
| Typewriter bio | yes (v3.112) | `settings.bioTypewriter` — the page types the bio out (full text kept for screen readers; reduced motion shows it at once); dashboard toggle, Lifetime gate |
| Entrance animations / “Pro enter animations” | yes (v3.112) | `settings.entryAnimation` Fade / Rise / Flicker / Glitch on the card (after the entry screen when that's on), plus the entry screen; Lifetime gate |
| Username effects | yes | glow / gradient / shimmer (`settings.usernameEffect`), gated rank 1 |
| Image host / “Unlimited image host” | yes / **wording** | `POST /api/v1/uploads`, Lifetime+, **200 MB per user**, 8 MB per image — not unlimited |
| Private encrypted chats | **no** | nothing in the repo |
| Remove footer badge / “no footer badge” | yes (v3.112) | `settings.hideBrand` drops the *made with misa.lol* pill; dashboard toggle, Lifetime gate |
| Pro fonts & templates / “pro fonts and layouts” | fonts yes (v3.114), layouts **no** | `settings.font` — Playfair, Space Mono, Caveat, VT323, Bebas Neue (Lifetime) + Cormorant Garamond, UnifrakturMaguntia (Supporter); loaded from Google Fonts only when chosen; no layout choice yet |
| Pro content blocks | yes (v3.115) | `settings.blocks` — heading / paragraph / quote / † divider / “currently:” status, above or below the links; dashboard editor; Lifetime gate |
| Custom share card | yes (v3.115) | `settings.shareCard` — your own handwritten line, three styles (glow / poster / mono), bio on or off; dashboard fields under the card preview; Lifetime gate |
| Music player styling | yes (v3.114) | `settings.playerStyle` bars / minimal / vinyl (the record spins while it plays); Lifetime gate |
| All future Pro perks | policy | |

## Supporter ($9.99)

| Claim | Status | What the code says |
|---|---|---|
| Everything in Lifetime | yes | rank 2 ≥ 1 |
| Gold checkmark + halo | policy / yes | the gold check is an admin-granted badge with a colour; the halo is `settings.usernameGlow`, gated rank 2 |
| Supporter tag | yes (v3.113) | `settings.supporterTag` — a gold *supporter* pill by the name; dashboard toggle, Supporter gate |
| Animated gold username glow | partly | `usernameGlow` is a static text-shadow halo in the accent colour; the *Gradient* / *Shimmer* username effects animate but are Lifetime |
| Sparkle username trail | yes (v3.113) | `settings.sparkleTrail` — gold four-point sparks trail the pointer (canvas); on touch screens they twinkle around the name; off under reduced motion; Supporter gate |
| Gold star, ring & snow cursors / “gold cursors” | yes (v3.112) | `settings.cursor` star / ring / snow — gold SVG cursors built into the page (an uploaded cursor image wins); dashboard select, Supporter gate |
| Animated gold profile border | yes (v3.113) | `settings.goldBorder` — a gold gradient border that turns (registered `--ga` angle; static gold where `@property` is unsupported or motion is reduced) with a gold glow; Supporter gate |
| Exclusive fonts | yes (v3.114) | Cormorant Garamond and UnifrakturMaguntia are Supporter-only (`SUPPORTER_FONTS` in `plans.py`) |
| Early feature access | policy | |

## The two numbers on the old front page

`200K+` profiles and `40M+` views are still on the v2 page kept at `/home-v2` (noindex since v3.91). The v3 front page doesn’t use them. Nothing in the repo produces either figure.

## A backend note found on the way (not changed)

`app/core/plans.py`: `plan_rank()` returns **1 (Lifetime)** for a plan string it doesn’t know — `PLAN_RANK.get(plan, 1)`. An entitlement with a typo’d plan name would unlock Lifetime perks. Probably meant to be 0.

## Suggested honest copy, if the features stay unbuilt

- Front page Lifetime card: *Verified blue check · Video & animated backgrounds · Username effects & an entry screen · Image hosting (200 MB)* — drop *typewriter bio*, *encrypted chats*, *no footer badge*.
- Front page Supporter card: *Everything in Lifetime · Gold check + halo · Custom cursors · Early access* — drop *supporter tag*, *sparkle trail*, *gold border*, *exclusive fonts*.
- Pricing compare table: drop the rows for chats, fonts & templates, content blocks, custom share card, music player styling, supporter tag, sparkle trail, gold border; make “full analytics” read the same for every plan (or gate the referrers/clicks server-side); change “unlimited image host” to “200 MB image host”.
- Or build them — each row above says exactly what is missing.

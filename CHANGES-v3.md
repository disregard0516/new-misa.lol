## v3.147 — the sweep (2026-09-10)
- **One command for all of it.** `src/tools/sweep.js`: rebuild (`build.py`, `build_site.py`), the server tests, the 13 `render-*.py` fixtures, all 11 pages at 1440 and 390, then all **67** browser harnesses — one table, non-zero exit if anything failed at all. `--quick` skips the page renders; `--only=moon,vigil` runs the harnesses whose names match. The harness list is **read off the tools directory**, so a harness written next week is in the sweep the moment it exists and cannot be forgotten out of it.
- **Four things it found that nothing else could see**, because nothing had ever run all of them from one place:
  - **Seven harnesses only worked from one directory.** `auto-test`, `dash-test`, `draft-test`, `fresh-test`, `look-test`, `peek-test` and `uname-test` defaulted to `'src/dist/dashboard.html'` — a working-directory-relative path. Run from anywhere else they read nothing, or worse, a stale file. All seven now resolve from `__dirname`.
  - **`claim-mobile`'s overflow check was measuring the wrong thing.** After `setViewportSize` on a mobile context, `innerWidth` reports 425 while the document box is 0..390, so a page with no overflow at all failed "no horizontal overflow (425)". It now compares `scrollWidth` against `innerWidth` and, when it does fail, names the elements actually sticking out.
  - **A real one: the save bar sat on the field you were typing in.** With unsaved work the save bar is fixed to the bottom; tab into a field tall enough that the browser already considers it visible — the deck, five rows — and the browser does not scroll, so its last lines stay under the bar. Fixed in two places: the page now *reserves* the bar's height (`scroll-padding-bottom` on `<html>`, matching padding under `.dash__main`) so the browser's own scroll-into-view lands clear, which is also what Firefox and Safari need since they align a focused field to the very edge; and a `focusin` nudge moves anything still overlapping, instantly rather than smoothly, because it rides a focus that has already moved.
  - **The nudge was being added on every repaint.** Registered once now, at the top, next to the other dashboard listeners.
- Nothing about the site changed. This is the thing that will tell us when it does.

## v3.147 — the sweep (2026-09-10)
- **One command for all of it.** `src/tools/sweep.js`: rebuild (`build.py`, `build_site.py`), the 150 server tests, the 13 `render-*.py` fixtures, all 11 pages at 1440 and 390, then every browser harness — one table, non-zero exit if anything failed at all. `--quick` skips the page renders; `--only=moon,vigil` narrows it. The harness list is **read off the tools directory**, so one written next week is in the sweep the moment it exists, and nobody has to remember to add it.
- **The biggest thing it found: the hosted dashboard preview was running dead JavaScript.** One canned API string in `build.py` said `'404 — this one's dead'` — an unescaped apostrophe — and a second embedded the doodle SVGs as JSON whose `\"` was eaten by Python before it ever reached the file. Either one ends the **whole 142 KB inline block**. The page still rendered, because the markup is there and only the script died, so nothing looked wrong: it just quietly showed static placeholder data to everyone who opened it. **The live site was never affected** — the demo map exists only in the preview build — but the artifact Valer has been opening all week has been a corpse. Both fixed, and **`build.py` now parses every inline script it writes and refuses to finish if one won't run**, which is the only reason this class of bug can't come back.
- **It came back 71 of 82.** Fourteen features shipped in a day, each with its own harness, each green when it was written — and eleven had gone red since without anyone seeing it, because nothing had ever run them all from one place.
- **Stale by growth (14 assertions across 3 harnesses).** The explore wall went from 12 example pages and 7 themes to 16 and 11; `explore-a11y`, `explore-phone` and `wall-a11y` all had *12* and *seven filters* written into them, so every count assertion had been failing since the wall grew. They now **read the wall off the wall** — the total, the theme list, how many are soft — and assert that the count line agrees with what is actually on screen. Adding an example page can't turn them red again, and can't quietly stop them meaning anything either.
- **Stale by feature (2).** Blocks gained `place` in v3.139 and `night` in v3.142; `features-test` froze the field list before both.
- **A real bug on the front page.** At 320px the *See it as a table, plan by plan* link under the everything-else section was **26px tall** — under the 32px thumb, and it had been since v3.140. Fixed with the house idiom: padding out, margin back in, so the underline stays exactly where it was.
- **A real bug in the dashboard.** With unsaved work the save bar is fixed to the bottom. Tab into a field tall enough that the browser already considers it visible — the deck, five rows — and the browser doesn't scroll, so its last lines sit under the bar. The page now *reserves* the bar's height (`scroll-padding-bottom` on `<html>` + matching padding under `.dash__main`), which is also what Firefox and Safari need since they align a focused field to the very edge, and a `focusin` nudge moves anything still overlapping — instantly, not smoothly, because it rides a focus that has already landed.
- **Two harnesses were measuring things that were never the number.** On a mobile context `innerWidth` reports **425** for a 390 viewport, so `claim-mobile` and `paint-test` were failing pages that were fine. `paint-test` now asks the page the question a person would: *try to scroll it sideways and see if it moves.* (It doesn't: the ticker's track is 3019px inside a clipped 390px parent, exactly as intended.)
- **`fresh-test` was reading the container as a defect.** It stubs a brand-new account, so `/profile/me` 404s on purpose and unrouted endpoints abort on purpose, and in a test container the font CDN is unreachable — all of which arrive as *Failed to load resource*. That line was never evidence of anything here; real JS errors still are.
- **Seven harnesses only worked from one directory** (`auto-test`, `dash-test`, `draft-test`, `fresh-test`, `look-test`, `peek-test`, `uname-test`): a working-directory-relative `'src/dist/dashboard.html'` meant that from anywhere else they read nothing, or a stale file. All seven resolve from `__dirname` now.
- **`dash-states` and `home-states` are out of the sweep by name.** They're screenshot generators for looking at — they assert nothing and take minutes — and the sweep was running them with no argv and crashing. They also no longer require an outdir.
- **Still red, honestly: `slow-phone`.** First contentful paint on a throttled phone measures 3256ms against a 3000ms budget. That's a real number on this machine and it moves with the machine, so it stays red rather than getting a wider budget. **Valer: worth a look before the budget is touched.**
- Nothing a visitor sees changed except that one link's hit area. This is the thing that tells us when it does.

## v3.146 — the moon (2026-09-10)

Tonight's real moon, in the corner of the card. `settings.moon` (free).

**No network, no data, no cache.** The moon is a clock everybody already shares and its phase is a division:
`app/core/moon.py` takes the Julian day, divides by the synodic month from a known new moon in January 2000,
and gets where in the cycle we are. Illumination is `(1 − cos 2πx) / 2`; the named phases each get the day or
so around their moment and the long slopes get the in-between names.

**The drawing is one path, not a picture of a moon.** The terminator is an ellipse seen edge-on, so the lit
region is exactly a semicircle joined to an elliptical arc — a semicircle on the lit limb (right while waxing,
left while waning) closed by an arc whose horizontal radius is `|cos 2πx| · r`, bowing away once past half.
A full moon and a new moon are plain discs.

**Checked by looking at the pixels.** `src/tools/moon-test.js` draws each of eight phases into a canvas and
counts what is actually painted: the lit centroid must be on the correct side, and the lit *area* must match
the computed illumination to within six per cent. (`isPointInFill` disagreed with the rendering, and the
rendering is what people see.) 3 server tests over the cycle and the markup; 150 pass.
`src/tools/render-moon.py` writes a page of the whole cycle, a page wearing one, and a bare page for the
measuring.

**The dashboard** — *The moon* in the strange bits, with a line saying what it is tonight, worked out in the
browser the same way the server works it out. **The front page** — a spec row. **Pricing** — a compare row
and a thirteenth free extra; the generated index reached **forty**.

## v3.145 — the dashboard, rearranged (2026-09-10)

Twelve features in a day went somewhere, and where they went was *wherever there was room*. **Links** had
grown ten sub-headings — Blocks, Secret word, The sky, Time capsule, The night shift, The draw, The other
side, Neighbours, The archive and Badges — under a nav item that says *Where people find you*. Nobody would
ever have found the archive.

So the dashboard got the same treatment the page gets: `src/tools/walk-dash.js` walks it at 1440 and 390 and
reports every section with its size, its controls, its sub-headings, the heading outline read the way a screen
reader reads it, anything overflowing, and whether the nav and the sections still agree with each other.

The result:

- **The strange bits** (new) — Secret word, The sky, Time capsule, The night shift, The draw, The other side.
  *Things a page shouldn't be able to do. A word that unlocks a link. Weather from where you are, drawn over
  the page… None of this is necessary. That's rather the point.*
- **Visitors** (was *Guestbook*) — the guestbook, the chalkboard, the ask box, the tally, the vigil and
  neighbours: everything on your page that somebody else puts there. *Nothing shows until you say so, or until
  two of you agree.*
- **Links** keeps the links and Blocks; **Your page** takes Badges; **Account** takes The archive, which is
  where you'd look for it when you have broken something.

Seven sections, none of them more than about 2,500px, against one that was 14k of markup. No heading skips, no
overflow, nothing sideways, the nav and the sections in agreement at both widths, and every dashboard harness
(`dash-structure-a11y`, `find-test`, `see-test`, `arch-test`) still green — the finder in particular, because
its index is read off the page and simply followed everything to its new home.

## v3.144 — neighbours (2026-09-10)

You can name up to five other misa.lol pages. A name does nothing on its own: it shows up on your page **only
if that page names you back**. Free.

That one rule is the whole moderation story. Nobody can put themselves next to you, and you cannot put
yourself next to anybody — there is nothing one person can place on another person's page, so there is nothing
to report. It is a webring, built one mutual pair at a time.

**`app/core/neighbours.py`** — `clean()` tidies a list (lowercased, `@` and `misa.lol/` stripped, deduped,
your own name dropped, at most five). `resolve()` looks each one up, skips suspended pages and pages that
don't name you back, and returns `{username, name, accent}` for the ones that do — an accent that isn't a
`#rrggbb` is dropped rather than passed through. The answer caches for ten minutes.

**Never on the render path.** Resolving costs one lookup per name, so the render only *peeks* at the cache —
exactly like now-playing and the weather — and the page then asks `GET /api/v1/neighbours/{name}` for a fresh
answer and redraws itself. A page with no names asks nothing at all. First view after a change may show the
row a beat late; that beats making every visitor wait on five lookups.

**The page** — *neighbours* in the page's handwriting over a wrapping row of pills, each carrying that page's
own accent as a dot and its handle under the name, each linking to it. Names that haven't named back are
simply not there, and the section says so: *nobody has named this page back yet.*

**The dashboard** — five slots under the time capsule with a `misa.lol/` prefix, and a line reading back
*4 names · 3 of them named you back*. **The front page** — a spec row. **Pricing** — a compare row and a
twelfth free extra; the generated index went thirty-eight → thirty-nine on its own.

Tests: 5 server tests (147 pass) and `src/tools/nb-test.js` — 15 browser checks, including a page whose names
haven't named back showing none of them anywhere.

## v3.143 — the archive (2026-09-10)

A page keeps what it used to be. Every save puts the page it just replaced on a shelf; the last twelve stay
there for a year. Free.

**`app/core/archive.py`** — one list per page, `ar:<uid>`, newest first, each entry `{at, cfg}` where `cfg` is
the whole profile config exactly as it was saved. A save that changes nothing shelves nothing (the newest
snapshot is compared before anything is written); two saves in the same second still get their own moment, so
every `at` on a shelf is unique and addressable. A config that won't fit in a quarter-megabyte isn't shelved.

**`POST /profile/me` shelves before it writes.** `GET /profile/me/archive` returns just the days — the bodies
stay on the server until one is asked for; `GET /profile/me/archive/{at}` returns one; and
`POST /profile/me/archive/{at}/restore` puts it back. Restoring shelves what is there first, **so undoing an
undo works**, and the page comes back through the same gate a save goes through: the username and id are
re-stamped, the view count is the server's, and the plan is applied — restore a page from when you had
Lifetime and the Lifetime-only parts don't come back with it.

**A page you can read backwards.** `settings.archive` (free, off) lets visitors open `misa.lol/<name>?as=<second>`
and see the page as it was, rendered by the same function that renders it now, with a dashed bar across the top:
*you're reading this page as it was on 2 sep 2026. back to now.* With the switch off the parameter does nothing
and the shelf is the owner's alone. Account deletion drops the list.

**The dashboard** — *The archive* under the time capsule: the switch, and the shelf as rows with the moment,
how long ago in words, **Put this back** and **Look** (which opens `?as=` in a new tab and says so). Restoring
with unsaved work in hand asks first. **The front page** — a spec row. **Pricing** — a compare row and an
eleventh free extra, and the generated index went thirty-seven → thirty-eight on its own.

Tests: 7 server tests (142 pass) and `src/tools/arch-test.js` — 15 browser checks over the shelf, restoring,
the warning, and a server that refuses.

## v3.142 — the night shift (2026-09-10)

A page can have a night. `settings.night` is `{tz, from, to}` — an IANA zone and two hours — and any content
block marked `night: true` is on the page only inside that window. Lifetime.

**The window is the owner's clock, not the visitor's**, and the *server* decides. Outside it a night block is
skipped before it is ever rendered, so its words are not in the HTML for anyone — no `hidden`, no
`display:none`, nothing to find by reading the source. That is the whole point of it: an unlisted mix that
comes down at five actually comes down at five.

`_night()` takes the raw setting, resolves the zone with the same `_zone()` the clock block uses, and returns
whether it is dark there and the hour as a word. A window that wraps midnight (23 → 5) and one that doesn't
(9 → 17) both work; a bad zone, equal hours or an hour out of range switch it off rather than guessing.

While it is on, the page says so — *it's 4:14 am where ren is. some of this is only here now.* — in the page's
handwriting, above the top blocks, and only when there is actually a night block being shown; a page holding
nothing back makes no claim. The card also picks up `is-night`, which deepens its accent glow.

**The dashboard** — *The night shift* under the time capsule (timezone with the existing `tz-list`, two hour
fields) with a line reading back *it's 4:14 am where you are — your night is on now · 3 blocks are in it*, and
a **night only** toggle on every block row. **The front page** — a spec row. **Pricing** — a compare row and a
twentieth Lifetime perk, which the front page's generated index picked up on its own (thirty-six → thirty-seven).

Tests: 5 server tests (135 pass) and `src/tools/night-test.js` — 14 browser checks, the first three of which
are about *absence*: the words are not in the source, not in the DOM, and no block is merely hidden.
`src/tools/render-night.py` renders the same page at 2 pm and 2 am.

## v3.141 — find a setting (2026-09-10)

The editor now holds around seventy controls across six sections. Scrolling for one is no longer a reasonable
ask, so: **/** or **⌘K** (Ctrl+K) anywhere in the dashboard opens a finder.

**The index is read off the editor itself** — every `[data-cfg]`, every toggle, every sub-heading, every
section — so it cannot fall behind what is actually on the page. Nothing is listed by hand. On top of that
sits a small map of the words people reach for that aren't in any label: *candle* → the vigil, *poll* / *vote*
→ the tally, *flip* / *back* / *liner notes* → the other side, *fortune* / *deck* → the draw, *easter egg* →
the secret word. The map is keyed by setting path and looked up by prefix, so `settings.tally.options.0`
answers to *poll* without being listed separately.

Matching is ranked: a label that starts with what you typed beats one that merely contains it, which beats a
hit in the section name or the synonyms, which beats every word appearing somewhere. Enter (or a click) closes
the finder, scrolls the control into the middle of the screen, flashes a ring around its row and puts the
cursor in it. Arrows move, Escape closes, `aria-activedescendant` keeps a screen reader in step, and **/**
does nothing while you are typing in a field.

**Two bugs it found in itself.** Several toggles share one `.field`, so taking "the first label in the field"
named three different Supporter toggles *entry screen*; and the volume slider, which lives in its own
`<label>`, was named *play audio* for the same reason. Labels now come from the control's own wrapping
`<label>` first, then `label[for]`, then the field — and a harness check asserts that no two entries in the
whole index share a name.

`src/tools/find-test.js` — 22 browser checks over opening, the index size, five searches, the two label bugs,
Enter, clicking, the arrows and the keyboard rules.

## v3.140 — and thirty-six other things (2026-09-10)

The front page's spec sheet shows ten features, chosen because they demo well. The site now has forty. A
visitor scanning that sheet has no way to learn that, so the front page gained an index: **every** feature, in
six groups, as small chips with a dot for the tier — free ivory, Lifetime crimson, Supporter gold.

**It is generated, not written.** `feature_index()` in `build.py` parses the pricing page's own compare table —
the canonical list — and builds the section from it, so adding a row there puts a chip on the front page and
the two can never quietly disagree. The heading counts them out loud (*And thirty-six other things*), and the
number comes from the parse.

**Four of them aren't built.** *Popup animations*, *Unlimited image host*, *Private encrypted chats* and
*Future Pro perks* are promises carried over from the old page and deliberately left in the table. A section
that says *here's the whole list, honestly* can't quietly promote them, so their cells now carry `data-soon`,
which puts a dashed **NOT BUILT YET** badge on the pricing row and a dimmed dashed chip on the front page (and
a *— not built yet* for screen readers). The headline counts only what exists: forty rows, thirty-six built.
Valer can drop the marks or the rows; the marks are in the data, not the markup.

The section is CSS multi-column with `break-inside: avoid` per group, so short groups tuck under tall ones
instead of leaving holes, and it collapses to one column on a phone. Each chip carries the full table wording
as its `title`.

Render checks clean at 1440 and 390 on the front page and pricing; `pricing-a11y.js` still passes.

## v3.139 — everything on, again (2026-09-10)

The composition pass, run again now that the vigil, the tally, the back of the page and the draw have all
landed. `src/tools/render-everything.py` switches on **every** feature at once — sixteen of them, plus eight
blocks, four links, a player, a sky and a block sent round the back — and `walk-everything.js` walks the result
at 1440 and 390, reporting the order of the sections, the heading outline read the way a screen reader reads
it, anything overflowing the card, anything under 10px, anything invisible, and any sideways scroll.

Three things it turned up:

**The name announced itself as “rensupporter.”** The Supporter tag sat immediately after the display name
inside the `<h1>`, so it ran into it as one word. It is now `<span class="sr-only">, supporter</span>` followed
by the visible pill marked `aria-hidden`, which reads *ren, supporter* and looks exactly the same.

**A turned-over card stayed as tall as the face it turned away from.** Both faces share one grid cell, so the
row was sized by the front — a page 2,849px long showed a 378px note floating in a 2,849px card. The container
now measures the face you are looking at and takes its height (with the same 0.75s easing, and none of it under
`prefers-reduced-motion`); `back-test.js` checks both directions.

**The draw was filed with the wrong half of the page.** A page is really two conversations: the owner talking
to you (the capsule, the draw) and what visitors do (the guestbook, the ask box, the chalkboard, the tally, the
vigil). The draw had landed in the middle of the second group; it now sits with the capsule, and a test asserts
the two halves stay unmixed.

130 tests, thirteen browser harnesses green. `walk-everything.js` also learned to read accessible names
(stripping `aria-hidden` subtrees) and to leave `.sr-only` out of its invisible-text check.

## v3.138 — the draw (2026-09-10)

The owner writes a small deck — a line each, up to twelve, one per line in a single field — and every visitor
is dealt one of them. It is theirs for the day: the same line on a reload, on a second visit an hour later, and
a different line for whoever is standing next to them. `settings.draw` is a Lifetime perk.

**`app/core/draw.py`** — `clean()` splits the deck (a list works too), tidies whitespace, drops blanks and
keeps at most 12 lines of 120 characters. `pick(deck, seed, day)` is a pure function: `sha256(day|seed)` modulo
the deck, so the same three arguments always give the same line and nothing needs to be remembered. The seed is
the first 8 characters of the salted visitor hash the view counter already computes — no address, no name.

**Nothing is stored.** The pick happens during the render and is thrown away; a test walks the whole key space
afterwards and finds nothing about it. The line is written straight into the HTML, so it is there with
JavaScript switched off, and only the dealt line is — the rest of the deck never reaches the browser.

**The page** — *for you, today* in small caps above one card in Caveat, dealt in with a short settling
animation that `prefers-reduced-motion` turns off. **`page_parts.gather()`** took a third argument, the
visitor's short hash, and deals the line; `main.py` passes it and the dashboard's preview passes nothing, which
deals a steady one. **The dashboard** — *The draw* under the time capsule, with a line counting the deck.
**The front page** — a spec row showing two cards, because two people get two lines. **Pricing** — a compare
row and a nineteenth Lifetime perk.

Tests: 6 server tests (128 pass) and `src/tools/draw-test.js` — 15 browser checks over the dealt line, a
reload, a second visitor, a deck of one, JavaScript switched off, reduced motion, a phone, and a page with no
deck. `src/tools/render-draw.py` writes the four fixtures.

## v3.137 — see your page before you save it (2026-09-10)

The dashboard's little phone has always been an approximation: a mock, redrawn in the dashboard's own markup.
This is the real thing. **See your page** hands the draft you are holding to the server, which renders it with
`render_public_profile` — the very same function that serves the live page — and sends the HTML back to sit in
a sandboxed frame over the dashboard, at phone or desktop width.

**`POST /api/v1/profile/me/preview`** — signed in, 60 per five minutes. The plan is applied to a *copy* of the
body (`copy.deepcopy`, so the caller's own config is untouched), so what comes back is what would actually go
up, and `cleared` names anything the plan drops — the panel says *1 setting is not on your plan, so the page
above is drawn without it*. Nothing is saved, and nothing is counted: no view, no presence, nothing in the
replay.

**`app/core/page_parts.py`** — the guestbook signatures, the chalkboard drawings, the answered questions, the
candles still lit, the sky over the owner's town and the now-playing/weather block feeds were gathered inline in
`main.py`. They now live in one `gather()` that both the live page and the preview call, so the preview draws
the same things from the same code and can't drift. It only ever reads — a test asserts no write call appears
in it.

**The panel** — *See the real thing* under the little phone, and *See your page* in the save bar. Phone /
desktop, a refresh, Escape or a click on the backdrop to close, focus returned to whatever opened it. The frame
is `sandbox="allow-scripts"` with no same-origin, so the previewed page can't reach the dashboard; it is
`tabindex="-1"` and the stage around it takes the focus instead, which keeps the Tab ring inside the panel and
still lets a keyboard scroll the preview. The hosted preview says plainly that there's no account behind it.

Tests: 5 server tests (122 pass) and `src/tools/see-test.js` — 22 browser checks over opening, the POSTed
draft, the framed page, the plan line, the widths, refresh, the focus ring, Escape, the backdrop, and a server
that can't draw it. Nothing saved in any of them.

## v3.136 — the tally (2026-09-10)

The ask box is questions coming in. This is one going out. `settings.tally` is `{q, options}` — a question up
to 120 characters and two to four answers of 40 — and every visitor picks one. Free, and off until there is
something to ask.

**`app/core/tally.py`** — one hash per page *per question*: `tl:<uid>:<qid>`, choice index → count, 90 days,
pushed out on every vote; `tl:<uid>:<qid>:seen:<hash>` is one vote per visitor per question, the same salted
hash the guestbook uses. `qid` is a 10-character digest of the question and its answers, so rewording either
starts a clean count and lets everybody answer the new one — the old count is simply left where it was, and
expires on its own. `clean()` tidies whitespace, drops blanks, drops an answer that repeats an earlier one
(case-insensitively) and keeps the first four that survive. `marks(n)` renders a count as tally marks.

**`app/api/v1/tally.py`** — `GET /tally/{name}` (the question, the answers and the counts — public, because
seeing the count is the point) and `POST /tally/{name}` `{choice}` (10 an hour per address, one per question;
404 when the page asks nothing, 400 when the choice isn't one of the answers, 429 when you've answered
already). Account deletion drops every question the page has ever asked.

**The page** — the question in Caveat, the answers as buttons, and beside each one the count *scratched on the
card*: groups of four uprights with a crimson slash through each fifth, up to 25 marks, then the number carries
the rest. The counts come from the API, never baked into the HTML. Which one **you** picked is yours and stays
in your own browser (`misa:tally:<name>:<qid>`), the way the returning-visitor line does; your answer is marked
*— yours*. Under 420px the marks drop to their own line.

**The dashboard** — *The tally* under the ask box: the question, four answer fields, and a line saying whether
it's a question a page can actually ask. `set()` in the dashboard learned that a numeric next key means a list,
so `settings.tally.options.0` builds an array rather than an object. **The front page** — a spec row with
scratched marks. **Pricing** — a compare row and a tenth free extra.

Tests: 7 server tests (117 pass) and `src/tools/tally-test.js` — 21 browser checks over the marks, answering,
answering twice, a reload, the server refusing, a phone, and a page asking nothing. `src/tools/render-tally.py`
writes the three fixtures.

## v3.135 — the other side (2026-09-10)

A page can have a back. There is a folded corner at the bottom of the card; turn it over and the whole card
rolls round to a second face. `settings.reverse` (Lifetime; gate `("settings.reverse", 1, None)`) is
`{title, text}` — a name for the back, up to 40 characters, and up to 800 characters of writing, rendered in
Caveat one paragraph per line. Blocks gained a third `place`, `back`, so any block already on the page —
a heading, a quote, a clock, the weather, now-playing — can be sent round there instead. Either alone is
enough: a back with only blocks names itself *the other side*.

**How it turns.** The two faces are both in the page from the start. With no JavaScript they simply stack,
so everything written on the back is still there to read — the script is what turns the stack into one card
with two sides (`.flip--on`, `backface-visibility`, a 0.75s turn). Whichever face is hidden is `inert` and
`aria-hidden`, so Tab never wanders round the back; turning it moves focus to the face you are now looking at,
and Escape brings you home. `prefers-reduced-motion` swaps the faces instead of spinning them.

**The fold** is a `<button>` in the corner of each face — a crimson triangle with a soft shadow under it, which
grows on hover or focus and slides out a small *turn it over* / *turn it back*. The card gains 26px of bottom
padding while it has one, so the fold never sits on the report link.

**The dashboard** — *The other side* under the time capsule: what the back is called, what it says, and a line
saying whether there is one and how many blocks are round there. Every block's *where it sits* select gained
**on the back of the page**. **The front page** — a spec row whose little card turns over when you hover it.
**Pricing** — a compare row (Lifetime and up) and an eighteenth Lifetime perk.

Tests: 6 server tests (110 pass) and `src/tools/back-test.js` — 30 browser checks over the turn, the inert
face, a full Tab walk, Escape, reduced motion, a browser with JavaScript switched off, a phone, and a page
with no back at all. `src/tools/render-back.py` writes the four fixtures.

## v3.134 — the vigil (2026-09-10)

A shelf of candles at the foot of a page. A visitor lights one — no name, no words, nothing typed — and it
burns down against the clock and goes out on its own. `settings.vigil` is free and off by default; its value
is also how long a candle lasts: `"6"`, `"12"` or `"24"` hours.

**`app/core/vigil.py`** — one sorted set per page, `vg:<uid>`, scored by the second each candle goes out.
A member is `"<id>|<lit>|<burn>"`: a random id, when it was lit and how long it burns. `light()` prunes the
spent ones, adds the new one, keeps the `MAX` (48) with the most time left and re-expires the key; `lit()`
returns the still-burning ones oldest first (stubs on the left, freshly lit on the right), at most `SHOWN`
(24); `count()`, `snuff()` and `forget()` do what they say. Nothing about who lit a candle is stored — the
once-a-day marker is `vg:<uid>:seen:<hash>`, the same salted hash shape the guestbook and the ask box use.

**`app/api/v1/vigil.py`** — `POST /vigil/{name}` (6 an hour per address, one a day per page; 404 unless the
page keeps a vigil, 429 when yours is already burning), `GET /vigil/{name}` (the shelf, for the page's own
refresh) and `DELETE /me/vigil` (the owner clears their shelf; a visitor can never put anybody's out).
Lighting one lands in the replay as a new `light` kind. Account deletion drops the set.

**The page** — the shelf is rendered server-side at each candle's current height (`--h` from `left / burn`),
with a flame that flickers, a wax stick that shrinks and a pool of wax that widens as it goes. From there the
page burns them down itself, off the render's own numbers rather than the visitor's clock; a candle that
reaches zero snuffs with a puff and leaves the shelf, and the count line follows it down to *the shelf is
dark. nobody has lit one in 12 hours.* The only extra call it makes is a refresh when you come back to a tab
after a couple of minutes. Every animation stops under `prefers-reduced-motion`.

**The dashboard** — *Vigil* under the ask box: off / 6 / 12 / 24 hours, a hint line naming how many are
burning right now, and *Put them all out*. **The front page** — an eighth spec row with a live shelf of six.
**Pricing** — a compare row and a ninth free extra.

Tests: 7 server tests (104 pass) and `src/tools/vigil-test.js` — 25 browser checks over a rendered shelf, a
candle running out while you watch, lighting one, the server refusing, a phone with everything else on, and a
page with the vigil off. `src/tools/render-vigil.py` writes the five fixtures.

## v3.133 — what turned up while you were away (2026-09-10)

The remembering line from v3.132 now earns its keep. Every answered question, guestbook signature and
chalkboard drawing carries `data-at` — the second it appeared — so a returning visitor's own browser can
compare it against the last visit it remembers and say: *that's 4 visits. 1 new answer, 1 new signature,
1 new drawing since.* Each of those items gets a small crimson mark in its corner.

Still nothing leaves the browser: the page publishes only when things happened, which it already did by
showing them; what any given person has seen is theirs alone, and the server is never told. Someone who was
here a minute ago sees no claim and no marks.

Tests: 1 new (97 pass) + 4 more browser checks in `src/tools/remember-test.js` (fresh visit vs. four days
away, and the marks that come with it).

## v3.132 — the page remembers you (2026-09-10)

Turn it on and someone who comes back gets a line: *you've been here before* → *that's 4 visits* → *you're a
regular here*, and after a season away, *long time. you were last here in may*.

The whole thing lives in **their** browser. `settings.remember` (free, off by default) renders an empty
`<p class="again" data-again hidden>` and nothing else — no name, no count, no marker of any kind in the
HTML. The page's own script reads `localStorage['misa:seen:<username>']`, writes the line, and puts the count
back. Nothing is sent anywhere: the harness asserts zero `/api/` requests across the whole flow. Clearing
site data forgets it, a browser that refuses storage simply shows no line (and throws nothing), and the
element carries its own explanation in a `title`: *your own browser remembers this. misa.lol is not told.*

A visit counts once every half hour — the same window the view counter dedupes on — so a refresh isn't
another visit.

Tests: 2 new (96 pass) + `src/tools/remember-test.js` (16 browser checks across real reloads, seeded
histories, and a browser with storage denied) and `src/tools/render-remember.py`.

## v3.131 — every feature on, at once (2026-09-10)

Twelve features have landed in a day and nobody had looked at them *together*. `src/tools/render-everything.py`
renders one page with all of it switched on — guestbook, chalkboard, ask box, capsule, sky, presence, odometer,
since, mood, secret word, supporter tag, gold halo, eight blocks, four links, a player — and
`shot-everything.js` walks it at 1440 and 390.

**The bug it was hiding.** The blocks loop reused the name `text`, which the page had already bound to
`settings.textColor`. Any page with a text, quote, heading or status block therefore rendered
`--text: tapes at the merch table, cash only.` — an invalid colour. Everything built on `var(--text)` quietly
died with it; worst of all `.name--shimmer`, whose gradient became `none` while `color:transparent` stayed,
so **the display name was invisible**. Renamed to `blk_text`; two regression tests pin it (the colour survives
a text block; every part still renders with everything on).

Also from the same pass: the dashboard's *The last ten visits* was an `h3` directly under the page's `h1`
(the Overview section's heading *is* the h1, so its parts are h2) — fixed, and `tools/dash-structure-a11y.js`
now knows that a `<input type="date">` swallows Tab into its day/month/year segments rather than treating it
as a focus loop (the walk was stopping at 41 stops; it now reaches 97).

Tests: 2 new (94 pass); seven browser harnesses green.

## v3.130 — the sky (2026-09-10)

Your page wears the weather where you are. Raining in berlin? It rains on the page: three sheets of streaks
behind the card. Snow drifts, fog banks roll, a storm rains **and flashes**, a clear night gets a few slow
stars, a clear day a warm wash near the top corner.

`settings.sky` is a town name (Lifetime and up — gate `("settings.sky", 1, None)`). The state comes from the
same free Open-Meteo forecast the weather block already reads: `weather.effect(code, is_day)` maps a WMO code
to one of *rain · snow · storm · fog · cloud · clear · night*. On a render the server only ever **peeks** at
the cache (`app/main.py`, same as the weather blocks — a page render never waits on the network); the page
then keeps itself current by asking `GET /api/v1/weather/{username}` every ten minutes, which now carries a
`sky` field alongside `line`/`temp`/`icon`. A page rendered with a cold cache asks straight away instead.

`describe()` calls every night sky “moon”, which is right for words and wrong for weather on the glass —
`effect()` splits it, so an overcast night gets clouds rather than stars.

The layer is `position:fixed`, `z-index:0`, `pointer-events:none`, behind the card, and every animation stops
under `prefers-reduced-motion`. Dashboard: *The sky* under the capsule — one field, with a line that says
whose weather you're wearing (and points at your weather block's town if you have one).

Also fixed: `\w` in the page's inline JS was a non-raw escape in the f-string (a DeprecationWarning on import
since v3.130's poll landed) — now `[a-z]+`.

Tests: 4 new (92 pass) + `src/tools/sky-test.js` (25 browser checks) and `src/tools/render-sky.py`.

## v3.129 — the time capsule, and the front page catching up (2026-09-10)

**The capsule.** Write something now that your page opens on a day you choose. Until then the page shows a
wax seal, the date, and a live countdown — and **the words are not in the page**: `render_public_profile()`
compares the date to the clock and only then puts the text in the HTML at all, so nobody can read ahead in
the source. On the day it opens itself, in Caveat, above the guestbook.

`settings.capsule = {text, at}` (`at` is `YYYY-MM-DD`, midnight UTC; Lifetime and up — `plans.py` gate
`("settings.capsule", 1, None)`). `_capsule()` validates both halves and hands back
`(opened, "24 dec 2026", iso, text)`; a bad date, an empty message or anything that isn't a dict renders
nothing at all. The countdown ticks on the minute, client-side, from the ISO instant alone.

Dashboard: *Time capsule* under Secret word — the message, the date, and a line that says which state it's
in (*nothing sealed yet* · *pick the day it opens* · *sealed · opens in 105 days* · *open — your page is
showing it*).

**The front page catches up.** Three new spec rows — *Ask me anything*, *A chalkboard*, *Time capsule* — so
the last month of features are on the page that sells them, and the capsule row's countdown is computed from
the real clock rather than a number that goes stale. Pricing: five new compare rows (ask box, chalkboard,
replay, weather + now-playing, capsule), three more in the Free card's details (8 now) and two in Lifetime's
(17 now); `tools/pricing-a11y.js` expects 17.

Tests: 3 new (88 pass) + `src/tools/capsule-test.js` (14 browser checks) and `src/tools/render-capsule.py`.

## v3.128 — the ask box (2026-09-10)

A page that answers back. Visitors leave a question; **answering is what publishes it**, question and answer
together, the answer in the owner's handwriting. Anything never answered is seen by nobody but the owner.

New: `app/core/asks.py` — two Dragonfly lists per page (`ak:<uid>:new`, at most 40, and `ak:<uid>:done`, at
most 30, of which the page shows 8) and one daily marker per visitor (`ak:<uid>:seen:<hash>`, the same salted
hash shape the guestbook uses — no addresses). An entry is `{id, q, at}` and, once answered, `{a, at_a}`.
`answer()` moves a question across; `edit()` rewrites an answer in place; `remove()` bins either.

API `app/api/v1/asks.py`: `POST /asks/{username}` (3 an hour per address, one a day per page), `GET
/asks/{username}` (answered only — an unanswered question is never public), `GET /me/asks`, `POST
/me/asks/{id}/answer` (400 on a blank answer; answering something already up rewrites it), `DELETE
/me/asks/{id}`. A question also shows up in the replay as `ask`, when the owner keeps one. Account deletion
drops both lists.

Public page: an *ask me anything* line, one input, and the answered pairs — the question in the page's voice,
the answer in Caveat. `settings.asks` (free, off by default) puts it there.

Dashboard, under Guestbook: *Waiting for an answer* (with the answer field right there — Enter sends) and
*Answered, and up*; counts, an empty answer refused before it leaves the browser, and its own status line.

Fixes on the way: the chalkboard's and the ask box's messages used to land in the **guestbook's** message box
(all three share one section, and `formMsg` took the first `[data-form-msg]` it found) — each part now writes
to its own line via `partMsg()`; and a third `when()` in the dashboard scope shadowed this one's, so the
queue printed `1/21/1970` instead of `1h ago` — renamed `askWhen()`.

Tests: 4 new (85 pass) + `src/tools/asks-test.js` (20 browser checks) and `src/tools/render-asks.py`.

## v3.127 — the visitor's-eye replay (2026-09-10)

Counts say *how many*. This says *what happened*: “15 minutes ago · from tiktok.com · phone · stayed 1 min —
arrived, tapped **new single** 12s in, signed the guestbook.” The last ten visits to a page, each one an
ordered little story, in the dashboard under the graph.

New: `app/core/replay.py` — one Dragonfly list per page (`rp:<uid>`, at most 120 events, the whole list
expires after a week). An event is four short fields: the second it happened, the **first 8 characters** of
the same salted visitor hash the view counter already dedupes on, what happened (`in` · `tap` · `sign` ·
`draw`) and one detail — the referrer host for an arrival, the link id for a tap, nothing else. No addresses,
no user agents, no names, and nothing a visitor typed. `visits()` groups events by that short hash inside a
30-minute window and hands back the newest ten.

Written from four places, all best-effort and all behind the owner's own switch (`settings.replay`, free,
**off by default** — with it off nothing is written at all): the page render (`app/main.py`, skipping
crawlers exactly as the view counter does), the click beacon (`POST /api/v1/hit/...`), a guestbook signature
and a chalkboard drawing. Read back by the owner alone: `GET /api/v1/me/replay` → `{on, visits, kept_for_days}`.
Account deletion drops the list with everything else.

Dashboard: “The last ten visits” under the analytics block — the switch, then a card per visit with when,
where from (or *straight to your link*), phone or desktop, how long they stayed, and the steps on a little
timeline. A tap whose link has since been deleted says *tapped a link that's gone now* rather than printing
an id. Off / waiting / unreadable each say what they are.

Tests: 5 new (81 pass) + `src/tools/replay-test.js` (22 browser checks across the four states).

## v3.126 — ten looks on the front page (2026-09-10)

The four looks the dashboard gained in v3.120 — **vampire, cathedral, static, lavender** — now exist on the
front of the site too, so a visitor can see and pick them before signing up. `css/v2.css` gains a
`.theme-*` block for each (they carry the signature bits of the look: outline links and a ringed avatar for
vampire, an arched avatar and arched links for cathedral, square hard-shadowed links and monospace caps for
static, ovals and big radii for lavender). `js/v2.js`: `THEMES` and `THEME_SW` list ten; four more example
pages join the wall — dorian (vampire), vesper (cathedral), noise (static), mira (lavender) — so the wall is
sixteen pages and its first ten are one per look, which is what a phone shows (the rest are one tap away on
explore). The explore page filters by all ten and the featured row is six. Captions keep the name and “page”
in one unbreakable span — with ten looks, *cathedral* and *lavender* used to wrap between them.

Supersedes v3.120's dashboard-only presets: the same ten names now mean the same thing on the front page,
on explore, in `?theme=` on sign-up, and in the dashboard's one-click themes.

Harness: `src/tools/looks-ten.js` (37 checks — swatches, wall, phone wall, filters, deep links).

# misa.lol — v3 site integration (2026-09-09; v3.1 dashboard, v3.2 polish, v3.4 mobile, v3.5 plans + badges, v3.6 share card, v3.7 routing, v3.8 profile cards, v3.9 uploads, v3.10 analytics, v3.11 tests, v3.12 review, v3.13 admin, v3.14 reports, v3.15 hardening, v3.16–17 profile fixes, v3.18 delete account, v3.19 themes, v3.20 passwords + caching, v3.21 live name check, v3.22 real pages on explore, v3.23 admin delete + share preview, v3.24–25 front page, … v3.117 guestbook)

Drop this tree over the repo (or copy the files below), then rebuild the app containers:

    docker compose build app01 app02 && docker compose up -d app01 app02

## New / replaced templates (`app/templates/pages/<slug>/index.html`)
- `index` — the v3 front page (full-bleed loop hero, ticker, wall of example pages, manifesto, spec sheet, pricing strip, CTA)
- `home-v2` — the calmer v2 front page, kept at /home-v2 for comparison (delete the folder when you've picked)
- `pricing`, `explore`, `terms`, `privacy`, `404`, `maintenance` — new pages (terms/privacy are templates: every paragraph is a TODO block)
- `dashboard` (v3.1) — the real page editor, in the same design system. Reads `/api/v1/me` + `GET /api/v1/profile/me`, writes `PUT /api/v1/profile/me` with the full `ProfileConfig` (`{profile: …}`), so it needs no new endpoints. Sections: overview (your link, page views / links / badges / status tiles), your page (display name, location, bio, avatar + audio URLs, autoplay, volume), links (platform / label / link / text-mode / on-off per social, add + remove), look & effects (accent / text / background / icon colors, background image + video, cursor, username + background effects, entry screen, show views / badges / links, halo + glow + gradient border, opacity / blur / radius sliders), account (auth.js's `#username-form`, email / display name / user id, the four login methods). A live phone preview updates as you type; a floating save bar appears on the first change; leaving with unsaved changes asks first. Uploads are URLs for now (no upload endpoint yet).
- `login`, `signup` — redesigned, on the existing auth contract: `/js/config.js` + `/js/auth.js`, the Turnstile gate (`.auth-lock`), `#login-form` / `#signup-form`, email + password (+ confirm + ToS on signup), Google / Discord / Telegram buttons, `#auth-message`, `.forgot-link`

## New shared assets
- `app/templates/css/v2.css` — the design system used by every page above (the old `style.css` is now unused by any page — keep it around until you've checked)
- `app/templates/js/v2.js` — nav, claim boxes, live preview phone, explore filters, auth field hints, the dashboard editor (`.dash-editor` block; auth.js still owns `/me`, username and logout)
- `app/templates/images/favicon.svg` — the † favicon

## Python changes
- `app/profile_page.py` (new) — `render_public_profile(config)`: the public page at misa.lol/<username>, now a themed profile (avatar, badges, username effects, socials with icons, location, bio, views, audio player, entry screen, background image / video / effects, custom cursor). Every config value is escaped or validated.
- `app/main.py` — imports the renderer from `app.profile_page` (the old inline card is gone); 404 responses now serve `pages/404/index.html` with status 404.
- `app/api/v1/auth.py` — signup accepts an optional `username` (validated with `validate_username`, reserved + taken checks happen before the account is created; the name is set right after).
- `app/core/security.py` — reserved usernames now include the new page slugs (explore, terms, privacy, maintenance, updates, 404, home, …).
- `app/templates/js/auth.js` — signup sends `username` along with the rest.

## v3.2 — polish pass (supersedes v3.1)
- Fix: the dashboard's `.dash` grid rule also matched the “—” cells of the pricing compare table (`.cmp td .dash`) and stretched every row to a full screen — v3.0 and v3.1 shipped that; now scoped to `.dash.dashboard`.
- Background loops (front page hero, log in) start after `load` on an idle callback, skip when the connection has data saver on, and pause while scrolled away or in a background tab. Desktop only, never with reduced motion (as before).
- Share cards: every page has canonical + `og:site_name/url/title/description/image(+alt)` + `twitter:*`; 404, maintenance and dashboard are `noindex`. The image is still `images/mainbg.png` until a real share card exists.
- Pricing: `/pricing#free`, `#lifetime`, `#supporter` scroll to and highlight the plan (`:target`); the compare table's plan names link to them; on phones the feature column stays put while the plan columns scroll. The home pricing strip links to `#lifetime` / `#compare`.
- Accessibility: `aria-label` on plain `div`/`span` (ignored by screen readers) replaced by `role="group"` + label or dropped; all eleven templates pass html-validate (recommended rules). Contrast audit: `--mute` on ink is 4.95:1, `--ash` 8.4:1, crimson on ink 4.7:1 — all AA for text. The one miss is ivory on crimson in primary buttons (3.6:1); that's a brand call, left as is.

## v3.125 — weather where you are, and the dead-links sweep (supersedes v3.124)
- **A weather block** — an eighth block type: `{type:"weather", city:"Berlin", unit:"c"|"f", text}` reads *raining in berlin, 11°* with a small sky icon (sun · moon · cloud · cloud-sun · fog · rain · snow · storm, in the page's inline sprite; WMO codes → words: clear, mostly clear, partly cloudy, overcast, foggy, drizzle, raining, pouring, snowing, showers, storms …; *clear night* / *cloudy night* after dark). `app/core/weather.py` — Open-Meteo's geocoder (a place → lat/lon, cached 7 days) and forecast (current temperature, code, is_day, cached 10 minutes; 3 on a failure), free and keyless; the label the owner typed wins over the geocoder's. Renders never wait on the network: `peek()` reads the cache and starts a background refresh; the page polls `GET /api/v1/weather/{username}` once when the render had nothing, then every ten minutes (30 a minute per address; 404 for pages without a weather block).
- **Check my links** — a button under the links: `POST /api/v1/me/links/check` (`app/api/v1/linkcheck.py`) knocks on every web link on the saved page (at most 20, five at a time, 6 s each, HEAD then GET when a host won't HEAD, redirects followed; email, text-only, disabled rows and private hosts skipped) and answers per link: *fine*, *403 — it answers, but wants a login or blocks robots*, *429 — the host is rate-limiting; probably fine*, *404 — this one's dead*, *timed out — slow or gone*, *can't reach it*. Three sweeps per ten minutes per account. The dashboard lists them, marks dead rows with a crimson edge, and asks you to save first when there are unsaved changes.
- Dashboard: *Weather where you are* in the block types (city, °C/°F, an optional name; the preview says *weather in berlin*).
- `tests/test_features.py` (+3, 76 pass: the words, temperatures and lines; rendering with and without data; the API geocoding once and caching, the render using the cache, a place that isn't one, 404s; the sweep — which rows get checked, the notes, localhost skipped, 401 signed out); `tools/features-test.js` (the block filling in from the poll with its icon; the sweep's list and the dead row; the weather row and preview).
- `app/profile_page.py`, `app/core/weather.py`, `app/api/v1/weather.py`, `app/api/v1/linkcheck.py`, `app/api/v1/router.py`, `app/main.py`, `tests/conftest.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.124 — a page that ages, and milestone cards (supersedes v3.123)
- **Here since** — `settings.since` (everyone, off by default). The footer says *here since 7 sep* (the first month) then *here since jul 2026*, from the account’s own `created_at`. Under a week: a dotted *new here* pill by the location. A month in: a wax seal in the card’s corner — a dagger pressed into the accent, tilted, with a dashed rim. A year in: the seal turns gold and carries the years (*2y*), and the card takes on a patina — a faint diagonal grain, a vignette, a gold breath in two corners — underneath everything (`z-index:-1` in the card’s stacking context, so the words stay crisp). `_age()` reads ISO dates with `Z`, an offset, or just a day; garbage is ignored.
- **Milestone cards** — `GET /<username>/milestone.png?n=100|1000|10000|100000|1000000` (`app/milestone_card.py`): a 1200×630 card with the count in the page’s accent at 200 px, *views on misa.lol/name*, a handwritten line per milestone (*a thousand. it’s a place now.* … *a million. what.*), the name and the date. Only for a count the page has really crossed — anything else is a 404, so it can’t be faked — cached five minutes per (page, milestone), rate-limited with the share card.
- **Dashboard** — Overview gets a *milestone* box once the count passes 100: the biggest milestone crossed, its line, the next one, *Open the card* and *Copy its link*. *What shows* gets the *here since* toggle; the preview phone shows the account’s month.
- `tests/test_features.py` (+2, 73 pass: `_age()` cases, the three ages and the off state, `reached()`/`short()`, a real PNG, the route’s 200 / 404s, the page route passing the age); `tools/features-test.js` (2 / 60 / 800 days rendered and measured — the seal inside the corner and rotated, gold at a year, the patina under the name; the dashboard’s milestone box, copy button and since toggle). The test user is 45 days old.
- `app/profile_page.py`, `app/milestone_card.py`, `app/main.py`, `tests/conftest.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.123 — the chalkboard: visitor doodles (supersedes v3.122)
- **A chalkboard on your page** — `settings.doodles` (everyone). Visitors get a small board (a 200×140 space, drawn at 2× on a canvas) and five chalks (white, the page’s accent, pink, sky, gold); *draw something* opens it, *leave it* sends the strokes, *wipe* clears, *never mind* closes. Nothing hangs on the wall until the owner keeps it; kept drawings hang as slate tiles at slight angles, drawn server-side as inline SVG (`app/core/doodles.py` `svg()` — one path per stroke, a dot for a tap, `currentColor` so the accent can be a variable).
- **Storage and limits** — Dragonfly lists `dd:<uid>:pending` (30) / `dd:<uid>:ok` (24), 12 shown; a drawing is at most 40 strokes × 400 points, 3,000 points in all (integer coordinates, clamped, near-duplicates dropped) — a few KB at the very most; one drawing per visitor per page per day (the salted visitor hash, no address), three an hour per address. Account deletion forgets the board.
- **API** — `POST /api/v1/doodles/{username}` `{strokes, colour}` (400 for nothing drawable, 404 with the board off / unknown / suspended, 429 for a second one today, 503 store down), `GET /api/v1/doodles/{username}`, `GET /api/v1/me/doodles` (entries carry their `svg`, never raw strokes), `POST /api/v1/me/doodles/{id}/approve`, `DELETE /api/v1/me/doodles/{id}`.
- **Dashboard** — a *Chalkboard* part of the Guestbook section: the toggle, *Drawn for you* (Keep / Bin) and *On the wall* (Bin) as thumbnails; SVG from the API is checked before it’s put in the page (`<svg…</svg>` only, no scripts, handlers, images, hrefs or foreignObject — a poisoned one is dropped).
- Fix: a `\d` in the presence script was a Python escape warning.
- `tests/test_features.py` (+2, 71 pass: rendering, `clean()`’s clamping and caps, `svg()`; the full draw → 429 → keep → shown → bin flow, 400 / 422 / 404s, 401 signed out); `tools/features-test.js` (drawing on the canvas with the mouse — a drag is a stroke, a tap a dot; the posted integer points; the empty board refusing; the dashboard’s Keep and Bin; the poisoned SVG never running).
- `app/profile_page.py`, `app/core/doodles.py`, `app/api/v1/doodles.py`, `app/api/v1/router.py`, `app/api/v1/users.py`, `app/main.py`, `tests/conftest.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.122 — now playing (supersedes v3.121)
- **A now-playing block** — a seventh block type: `{type:"nowplaying", text:"track — artist", url, lb}`. Typed, it's a line with a record and a link. With `lb` (a ListenBrainz username — free, public, no API key) the page keeps it live: *now playing · Night Bus — lune* with the record spinning and three bars while something plays, *last played · 4 min ago* when it stops. `app/core/nowplaying.py` reads `/1/user/<name>/playing-now` and, failing that, the last listen; 2.5 s timeout, cached 45 s in Dragonfly (20 s for a dead name), one lookup in flight per name.
- The page never waits on ListenBrainz: the profile route reads the cache and, when it's cold, starts a refresh in the background and shows the typed text meanwhile (or nothing, hidden, when there's only a name); the page polls `GET /api/v1/nowplaying/{username}` (30 a minute per address; 404 for pages without such a block) after 400 ms when the render had nothing, then every 45 s while the tab is visible and on each return to it.
- Dashboard: *Now playing* in the block types — track, link, ListenBrainz name on their own line under the row's controls; the preview draws the record. Blocks copy mentions it.
- `tests/test_features.py` (+2, 69 pass: typed / live / last-played rendering, the hidden-until-known case, the poll timing; the API with a stubbed network — lookup, cache hit, the page reading the cache, last played with an age, no block / unknown / dead name, `ago()`); `tools/features-test.js` (the live block filling in from the poll, stopping on the next one, the dashboard row and preview).
- `app/profile_page.py`, `app/core/nowplaying.py`, `app/api/v1/nowplaying.py`, `app/api/v1/router.py`, `app/main.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.121 — the pages say it (supersedes v3.120)
- **Front page** (`index`): three new spec rows — *Guestbook* (free; two handwritten slips), *Alive* (free + Lifetime; the “3 people here right now” chip with its pulsing dot, “it’s 3:12 am in berlin”, a six-wheel mini odometer), *Secret word* (Lifetime; “night bus” with a caret and the hidden link glitching in). The Effects row no longer promises “layouts” (never built) and now lists pro fonts, five link styles, avatar frames and page moods. Tier columns: Free gets “Unlimited links, five link styles, ten themes” and “Analytics, guestbook, ‘who’s here right now’”; Lifetime gets “Video & living backgrounds, tab title, page moods” and “Typewriter bio, fonts, frames, hit counters, secret word”.
- **Pricing**: the Free card finally has its “more” list — *5 more free features* (guestbook, live presence, five link styles, ten themes, a share card for every link) where the old page promised “7 more” and never listed them; Lifetime’s disclosure grows to *15 more Lifetime perks* (+ retro hit counters, page moods, secret word, avatar frames, a moving tab title, a clock block; “Pro fonts & templates” → “Pro fonts”). The compare table gains *Link styles*, *Avatar frames*, *One-click themes (ten)*, *Tab title that moves*, *Page moods by the visitor’s hour*, an **Alive** group (guestbook, “3 people here right now”, retro hit counters, secret word → a hidden link) and “Content blocks + a clock in your time zone”. 31 rows in six groups.
- Left alone on purpose (Valer’s call): “Private encrypted chats”, “Popup animations”, “galaxy, gold shimmer”, “Unlimited image host” — promises from the old page this repo doesn’t build.
- `tools/pricing-a11y.js` expects 15 perks in the disclosure; home-semantics, home-phone, reflow-test and pricing-a11y pass; the new rows rendered at 1440 and 390.
- `css/v2.css` (the three demos), the `index` and `pricing` templates.

## v3.120 — four more themes: vampire, cathedral, static, lavender (supersedes v3.119)
- **Themes** — four new one-click looks beside the six from the front page: *vampire* (blood on velvet: `#b3001b` on `#0b0004`, UnifrakturMaguntia, outline links, a turning ring, embers, a vinyl player), *cathedral* (stone and candlelight: amber `#d4a24c` on `#0e0c14`, Cormorant, ghost links, a breathing halo, stars, the minimal player), *static* (dead channel: `#e8e8e8` on `#101010`, VT323, brutal links, a pixel frame, rain, square corners, a thin card), *lavender* (`#7c5cff` on `#f3eefc`, Playfair, outline links, a petal ring, petals falling).
- Every preset now also sets `linkStyle`, `avatarFrame`, `font` and `playerStyle` (the six old ones put the defaults back), so switching themes never leaves the last one’s type or links behind; `themeOf()` matches on those too. Paid picks are set as before — the server clears what the plan doesn’t cover and the dashboard says so. Lede: “colours, corners, type and effects”.
- `tools/features-test.js` (vampire sets its five picks and presses its tile; gothic puts Inter, pills and no frame back; ten tiles). Rendered on the real page and looked at; the tiles wrap 9 + 1 at 1440 and 4 / 4 / 2 on a phone.
- `js/v2.js`, the dashboard template (tiles with a `title` each).

## v3.119 — page moods and the secret word (supersedes v3.118)
- **Page moods** — `settings.mood` (Lifetime). The background wash follows the visitor’s own clock: *dawn* (5–8: peach into rose), *day* (9–16: a lift of light), *dusk* (17–20: orange into violet), *night* (otherwise: deeper, the accent breathing behind the card). A fixed `.mood` layer between the background and the card, `data-mood` on `<html>` set by the browser and rechecked each minute; fades in over 1.6 s (at once under reduced motion). The dashboard toggle says which mood it is for you right now, and the preview phone wears it.
- **The secret word** — `settings.secret {word, url, label}` (Lifetime). A link that isn’t on the page until someone types the word anywhere on it (letters and numbers, 3–24, any case, spaces ignored; typing into a form never counts) — or taps the avatar five times and says it in a “say the word” field (Esc closes it; a wrong word shakes). The link then glitches in under *† you said the word* and takes focus. Neither the word nor the link sits in the page’s source: the page carries `sha256("misa-secret|" + word)` to check against and the link XORed with a keystream from `sha256(word)`; the browser decrypts it with what the visitor typed (`crypto.subtle`, so https — misa.lol is). `app/profile_page.py` `_secret()`.
- Fix: a field beside one with a hint used to spread its rows and drop its box (`.field{align-content:start}`).
- `plans.py` GATES (both Lifetime); `tests/test_features.py` (+3, 67 pass: the layer, the secret’s round-trip and the source staying clean, the guards, the gates); `tools/features-test.js` (the mood for this hour and its fade, typing the word, the guestbook form not counting, the five taps, the wrong word, the right one; the dashboard’s mood wash and secret hint).
- `app/profile_page.py`, `app/core/plans.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.118 — the pulse: live presence, retro hit counters, a clock block (supersedes v3.117)
- **“3 people here right now”** — `settings.presence` (everyone). The page counts its visitor on render and beats `POST /api/v1/presence/{username}` every 30 s while the tab is visible (a `leave` beacon on pagehide); anyone quiet for 75 s stops counting. One line above the footer with a pulsing accent dot: *just you here right now* / *N people here right now*. `app/core/presence.py` — one sorted set per page of salted visitor hashes (the analytics marker; no addresses), trimmed on every read, expiring on its own; crawlers are answered, never counted; 40 beats a minute per address.
- **Retro hit counters** — `settings.counterStyle` (Lifetime): *odometer* (dark wheels, the last one in your accent, each digit rolling up from zero on load), *lcd* (ghost eights, glowing in your accent), *flip* (split-flap cards). “you are visitor no. 012412”, padded to six wheels, `role="img"` with the plain count as its label; replaces the “12,412 views” line while views are on. No roll under reduced motion.
- **The clock block** — a sixth block type: `{type:"clock", tz:"Europe/Berlin", text:"berlin"}` reads *it’s 3:12 am in berlin*, rendered server-side from the zone (IANA names only; anything else is skipped) and kept right by the browser every minute, the colon blinking. The dashboard row takes a zone (a datalist of 62 common ones; new clocks start in the owner’s own zone) and a place name, and says what the line will read right now.
- Dashboard: *who’s here right now* toggle and a *hit counter* select under *What shows*; the preview phone shows the counter in each style and the presence line. `tzdata` added to `requirements.txt` (the zone database fallback).
- `plans.py` GATES (`settings.counterStyle` Lifetime; presence free); `tests/test_features.py` (+5, 64 pass: the line, the counters, the clock and its guard, the gate, the API flow — beat, repeat, leave, crawler, off, unknown); `tools/features-test.js` (the roll, the blink, the heartbeat on visibility, reduced motion, the dashboard’s clock row + preview).
- `app/profile_page.py`, `app/core/presence.py`, `app/api/v1/presence.py`, `app/api/v1/router.py`, `app/api/v1/users.py`, `app/core/analytics.py` (`visitor_hash`), `app/core/plans.py`, `app/main.py`, `requirements.txt`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.117 — the guestbook (supersedes v3.116)
- **A guestbook on your page** — `settings.guestbook` (everyone). Visitors leave a name (≤24) and one line (≤120) in handwriting; the slips pin to the card at slight angles under a Caveat "guestbook" heading, and a dotted *sign it* button opens the form (name, one line, *leave it* / *never mind*). Nothing shows until the owner approves it.
- **Moderation from the dashboard** — a *Guestbook* section: the on/off toggle, *Waiting for you* (approve / bin) and *On your page* (bin), with counts. Approving moves the slip onto the page on the next render.
- `app/core/guestbook.py` — Dragonfly lists `gb:<uid>:pending` (50) / `gb:<uid>:ok` (60), one signature per visitor per page per day (`gb:<uid>:seen:<salted hash>`, 24h; no addresses stored). `app/api/v1/guestbook.py` — `POST /api/v1/guestbook/{username}` (3 an hour per address; 404 when the book is off, the name is unknown or the account is suspended; 429 when already signed today; 503 when the store is down), `GET /api/v1/guestbook/{username}`, `GET /api/v1/me/guestbook`, `POST /api/v1/me/guestbook/{id}/approve`, `DELETE /api/v1/me/guestbook/{id}`. Account deletion also forgets the book.
- `app/main.py` passes the approved signatures into `render_public_profile(config, views, signatures)`; the page requests Caveat only when the book is on.
- Fix: a `<select>` with long options widened a `1fr` dashboard grid column past the phone (`minmax(0,1fr)` + selects clipped with an ellipsis).
- `tests/test_features.py` (+2, 59 pass: rendering; the full sign → 429 → moderate → shown flow); `tools/features-test.js` (the page form posts, the dashboard approves and bins).
- `app/profile_page.py`, `app/core/guestbook.py`, `app/api/v1/guestbook.py`, `app/api/v1/router.py`, `app/api/v1/users.py`, `app/main.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.116 — features, batch 5: the beautiful batch (supersedes v3.115)
- **Link styles** — `settings.linkStyle` (everyone): *pill* (as before), *outline* (accent hairline), *ghost* (just words on a rule), *brutal* (ivory blocks with a hard accent shadow, uppercase), *glass* (frosted, a highlight on top). The preview phone mirrors each.
- **Avatar frames** — `settings.avatarFrame` (Lifetime): *ring* (an accent arc that turns), *halo* (a glow that breathes), *pixel* (a stepped 8-bit border on a rounded square), *petals* (a soft pink dotted ring, turning). Preview mirrors each; none move under reduced motion.
- **Four more living backgrounds** — `backgroundEffect` gains *Rain* (streaks in your accent), *Snow* (three depths, drifting), *Embers* (accent and orange sparks rising, flickering), *Petals* (sakura, falling and swaying). Pure CSS, no scripts; the preview phone finally draws background effects at all (all seven).
- **Tab title** — `settings.tabTitle` (Lifetime): *breathe* (two titles trade places), *scroll* (the name walks across the tab), *blink* (a dot pulses). Still under reduced motion.
- `plans.py` GATES (frames + tab title Lifetime; link styles free); `tests/test_features.py` (+2, 57 pass); `tools/features-test.js` extended (the brutal shadow, the ring's turn, petals falling, the title changing and holding still under reduced motion, the preview's classes).
- `app/profile_page.py`, `app/core/plans.py`, `js/v2.js`, `css/v2.css`, the dashboard template.

## v3.115 — features, batch 4: content blocks and a share card you own (supersedes v3.114)
- **Content blocks** — `settings.blocks` (Lifetime): a heading, a paragraph (line breaks kept), a quote (Playfair italic with an accent rule), a † divider, and a *currently:* status line with a pulsing dot — each above or below the links, shown or hidden, up to twelve. Dashboard: a *Blocks* editor under the links (type, text, place, show, move, remove — the same rows as links, announced the same way); the preview phone draws them tiny.
- **The share card you own** — `settings.shareCard` (Lifetime): your own handwritten line in place of *be weird online again.* (the footer then reads your handle), and three styles — *glow* (as before), *poster* (your accent edge to edge, text flips to ink on a light accent), *mono* (ink and ivory with a hairline frame) — plus the bio on or off. Dashboard: the two fields under *What your link looks like when it's posted*.
- Playfair as a page font now scales 1.06 — its hairlines read light at body sizes.
- `plans.py` GATES (blocks fall back to an empty list, the card to none); `tests/test_features.py` (+3, 55 pass); `tools/features-test.js` extended (the blocks' order and escaping on the page, the editor, the card fields).
- `app/profile_page.py`, `app/share_card.py`, `app/core/plans.py`, `js/v2.js`, `css/v2.css`, the dashboard template, `COPY-AUDIT.md` — every one of the audit's twelve "promised but missing" rows is now built (layouts aside).

## v3.114 — features, batch 3: page fonts and player styles (supersedes v3.113)
- **Page fonts** — `settings.font`: Playfair Display, Space Mono, Caveat, VT323, Bebas Neue (Lifetime), Cormorant Garamond and UnifrakturMaguntia (Supporter — the "exclusive fonts"); the name, bio and links take the face (each with its own size scale so a pixel or a handwritten face reads at the same visual size), the handle keeps Playfair italic, and the face is requested from Google Fonts only when chosen. Dashboard: *page font* select under a new *Type* heading; the two Supporter fonts greyed out on Lifetime; the preview phone loads the face on first pick and shows it.
- **Player styles** — `settings.playerStyle` bars (as before) / minimal (a lone round button, the track name on hover or focus) / vinyl (a record with grooves and the accent label that spins while it plays). Dashboard: *player style* select beside the track name.
- **Fixed on the way:** with audio on, a first tap on the play button itself started the track and paused it in the same gesture (the page's "play on first touch" listener fired first) — the button now owns its own tap.
- `plans.py` GATES + `SUPPORTER_FONTS` check; `tests/test_features.py` (+3, 52 pass); `tools/features-test.js` extended (the face and scale on the page, the request to Google Fonts, the vinyl spin, the dashboard's greyed exclusives and the preview font).
- `app/profile_page.py`, `app/core/plans.py`, `js/v2.js`, `css/v2.css`, the dashboard template, `COPY-AUDIT.md` rows updated.

## v3.113 — features, batch 2: the Supporter set (supersedes v3.112)
- **Supporter tag** — `settings.supporterTag`: a small gold *supporter* pill beside the name (dark text on a gold gradient, so it reads next to any username effect). Dashboard: *supporter tag* toggle; the preview phone shows it.
- **Sparkle username trail** — `settings.sparkleTrail`: gold four-point sparks trail the pointer across the page (a fixed canvas, ≤90 sparks, they drift up and fade in ~1s); on touch screens they twinkle around the name instead; nothing under reduced motion. Dashboard: *sparkle trail* toggle; the preview phone twinkles.
- **Animated gold profile border** — `settings.goldBorder`: the card's border becomes a gold gradient that slowly turns (a registered `--ga` angle property animated over 7s; static gold where `@property` is unsupported or motion is reduced) with a soft gold glow. Dashboard: *gold border* toggle; the preview phone gets a gold ring.
- All three Supporter-only in `plans.py` GATES; `tests/test_features.py` (+2, 49 pass); `tools/features-test.js` extended (tag colour beside a shimmer name, sparks appear on pointer move and fade, reduced motion, dashboard locks on Lifetime and the live preview on Supporter).
- `app/profile_page.py`, `app/core/plans.py`, `js/v2.js`, `css/v2.css`, the dashboard template, `COPY-AUDIT.md` rows updated.

## v3.112 — four features the pages promised (supersedes v3.111)
Valer's direction at 21:24Z: *more unique, more different features*. The first batch is the Lifetime set the front page and pricing page have promised all along (see `COPY-AUDIT.md`), built for real — public page, dashboard control, plan gate, tests.
- **Typewriter bio** — `settings.bioTypewriter` (Lifetime): the page types the bio out character by character with an accent-coloured caret (a beat on full stops); the full text stays in the document for screen readers and no-script; reduced motion shows it at once. Dashboard: *typewriter bio* toggle under Effects; the preview phone types it too.
- **Entrance animations** — `settings.entryAnimation` Fade / Rise / Flicker / Glitch (Lifetime): the card arrives with one of them; with the entry screen on, it plays when the screen is dismissed. Dashboard: *entrance animation* select; the preview card replays the pick.
- **Footer badge off** — `settings.hideBrand` (Lifetime): the *made with misa.lol* pill leaves the page (the report button stays). Dashboard: *no misa.lol badge* under What shows.
- **Built-in cursors** — `settings.cursor` gold star / ring / snow (Supporter): 24px gold SVG cursors on a dark outline, inline data URLs, hotspot centred; an uploaded cursor image still wins. Dashboard: *cursor* select beside the cursor image; the preview phone takes the cursor.
- `app/core/plans.py` GATES: the four keys; `tests/test_features.py` (+6, 47 pass); `tools/features-test.js` walks the public page (typing, reduced motion, entry screen) and the dashboard (locks on Free, live preview on Supporter).
- `app/profile_page.py`, `app/core/plans.py`, `js/v2.js`, `css/v2.css`, the dashboard template, `COPY-AUDIT.md` rows updated.

## v3.111 — explore, pricing, login and sign-up at the widths nobody renders (supersedes v3.110)
- The four pages around the front page rendered and looked at at 700, 768, 1024 and 1920. Pricing, login and sign-up hold. Explore's gallery between 641 and 940px sat two full-size cards in ~350px cells — six rows; three columns there now, the phones a touch smaller under 760px, like the front page's wall in v3.109.
- `css/v2.css`.

## v3.110 — the dashboard at the widths nobody renders (supersedes v3.109)
- The dashboard rendered and looked at at 700, 768, 960, 1024 and 1920. The tablet layouts hold (the section strip, the peek sheet, two-up tiles). Two things didn't:
- 821–1100px: the four colour tiles in the sidebar-plus-editor layout ellipsized their labels (“BACKGROU…”). Two-up until 1100px now (was 820).
- 1920px: the editor column ran ~1340px wide — a bio box nine hundred pixels across. The column's content stops at 1080px; the sidebar and the preview rail stay where they are.
- `css/v2.css`.

## v3.109 — the front page at the widths nobody renders (supersedes v3.108)
- The front page rendered and looked at at 700, 768, 960, 1024 and 1920 (`tools/site-render.js` takes `WIDTHS=…`); every check so far ran at 1440 and 390. 1920 holds. The middle didn't:
- 641–940px (tablets): the example-page wall had two columns of full-size phones — six rows, ~3400px of scroll. Three columns there, the phones a touch smaller under 760px so three still fit. The three steps stacked as full-width tall cards; they take the phone's compact row layout (number beside the words) up to 940px now.
- 941–1100px: four full-size phones no longer fit four columns — at 1024 each overlapped its neighbour. A touch smaller there.
- `css/v2.css`, `tools/site-render.js`.

## v3.108 — the dashboard's interactions, with eyes (supersedes v3.107)
- Seventeen interactions rendered on the real template with the real faces at 1440 and 390 and looked at (`tools/dash-states.js`, second half): a theme picked, the accent changed after it (the *Back to y2k* row), a link switched to text mode, moved, switched off, added; the badge switch; the entry screen on; the card ranges dragged; the username field mid-check, taken, free; an upload in progress, locked on Free, too big; the password and delete forms open. All held but one word.
- A link row's switch read *on* whichever way it was set — a switched-off row still said “on”. It reads *show* now, like the badge switch (the title was already *Show on page*).
- `js/v2.js`, `tools/dash-states.js`.

## v3.107 — the front page's interactive states, with eyes (supersedes v3.106)
- Eighteen states of the front page rendered on the real template with the real faces at 1440 and 390 and looked at (`tools/home-states.js`: the hero lab in each theme, the effects off, the claim box answering free / taken / reserved / invalid, a persona tapped, signed in, reduced motion, forced colours, the video blocked, the phone menu open as a visitor and as a member). All held but one.
- Signed in, the nav still offered *Claim username* (→ `/signup`, which the server bounces to the dashboard) — a member has an account. The ivory button now reads *Dashboard* and goes there (`auth.js markLoggedInNav`); the plain Dashboard text link beside it hides on wide screens (phones keep v3.33's text link and hide the button), and the phone menu's *Claim your username* button hides for members (its Login entry already reads Dashboard).
- Noted, not changed: a member typing a name into the page's claim boxes lands on the dashboard without the name (the sign-up redirect) — those boxes could point members at Account instead.
- `js/auth.js`, `css/v2.css`, `tools/home-states.js`.

## v3.106 — the dashboard's states, with eyes (supersedes v3.105)
- Fourteen states of the dashboard rendered on the real template with the real faces at 1440 and 390 and looked at (`tools/dash-states.js`: fresh account in the soft and paper themes, Free / Lifetime / Supporter, analytics unavailable, no views, nine links, a kept draft, an expired session, a failed save, a saved one, a stale tab, the phone peek sheet).
- The live preview on a light theme: the muted text (handle, bio, track, views) and the hairlines stayed tuned for dark pages — on soft, paper or any light background they were nearly invisible. They follow the text colour now, the way the public page mutes with opacity.
- The live preview's username effects: Gradient and Shimmer both drew the front page's gold sparkle, which the public page never shows — Gradient is accent→text, Shimmer text→accent→text, Glow the accent with a halo, and the Supporter halo a soft shadow. The preview draws each the way the page does.
- The top message box on the dashboard used the auth pages' negative bottom margin, so the Overview eyebrow sat against it; it has its own spacing now.
- An expired session mid-save showed the same sentence twice (a message box and the draft bar) with a stale “Saved.” possible beside them, and the save bar offered “Try again”, which only failed again. One box now (the draft bar, which is `role="status"`), any older message cleared, and the save bar's button reads *Log in again* and goes to the login page.
- A 5xx on save showed the server's own words (“Internal Server Error”); it says *Couldn't save — something broke on our side. Your changes are still here; try again in a moment.*
- `css/v2.css`, `js/v2.js`, `tools/dash-states.js`, `tools/save-fail.js` (401 expectation updated).

## v3.105 — a render sweep of every page, with eyes (supersedes v3.104)
- Every public page rendered at 1440 and 390 on the real templates (`tools/site-render.js`, now with a scroll walk so the scroll-revealed sections are on, the real Inter / Playfair / Caveat faces served from the `@fontsource` packages — `tools/brand-fonts.js` — and a `guest` mode) and looked at as screenshots (`tools/render-sheet.py` builds the review sheets and the contact sheet). Three things were wrong that no earlier code-level check had caught.
- Dashboard colour tiles (`.color`): label, swatch and hex sat in one flex row that never fit the tile (≈185px in the four-column grid, ≈170px on phones), so the swatch — the only part allowed to shrink — was a sliver on *accent* and gone on *background*. Same three parts, arranged so nothing shrinks: label over the hex, swatch on the right.
- Pricing compare table on phones: one plan column showed — Free, mostly dashes — with Lifetime and Supporter a sideways swipe away that nothing pointed to. All three plan columns fit the width now (feature column 38%, tighter cells, 9px heads with a 32px tap area, 10.5px notes); the sideways scroll stays only as a safety net.
- Front-page tier row on phones: the Supporter card, off to the right of the swipe row, only revealed once swiped to — a blank card fading in mid-swipe. Cards after a revealed card reveal with it (`html.js .tiers > .tier-col.in ~ .tier-col`).
- Dashboard analytics: the server always sends 14 daily buckets, so the “no views yet — the bars fill in as people visit” placeholder never showed; it shows when the buckets are all zero, and reads *no views in the last 14 days* when the page has had views before.
- `css/v2.css`, `js/v2.js`, `tools/site-render.js`, `tools/brand-fonts.js`, `tools/render-sheet.py`, `tools/pricing-a11y.js` (updated for the fitting table, and now served the real faces so its fit check means something).

## v3.104 — the admin's grant flow, by keyboard and screen reader (supersedes v3.103)
- Where the checks and plans are handed out — walked on the real template with `/api/v1/admin` mocked (`tools/admin-a11y.js`). Held: granting a plan and giving a badge each send one request and are read out (*Granted lifetime to ren.*, *Badge given.*) with focus kept.
- What wasn't: every row's button read *Manage* (now *Manage ren* / *Manage peach*); the tables' column headers had no `scope`; the selected-user panel opened without taking focus and had no name (a region named *Manage ren* now, focused when it opens); the plan and badge selects and the suspension reason had no labels (*Plan to grant*, *Badge to give*, *Reason for suspension*); *Grant / Give / Hide / Suspend / Delete account* said nothing about whom (they name the user now); *View page* opened a new tab without saying so; *Close* dropped focus (it goes back to that row's Manage button).
- `js/v2.js` (the admin section), `tools/admin-a11y.js`.

## v3.103 — what the pages promise vs. what the code does (supersedes v3.102 — no code change)
- Every product claim on the front page and the pricing page checked against the repo (`plans.py` GATES, `profile_page.py`, `uploads.py`, `users.py`, `share_card.py`) and written up in `COPY-AUDIT.md` (in the project). Backed by code: the username page, links without a cap, the music player, analytics on every plan (not gated, so “full analytics” for paid plans is the same thing), one-time entitlements, video and animated backgrounds, username effects, the entry screen, image hosting (200 MB, not unlimited), Supporter-only cursors and the halo. Policy, not code: the verified / gold checks (granted in admin), early access, “live in under a minute”. **Not in the repo at all:** typewriter bio, encrypted chats, removing the footer badge, pro fonts / templates / layouts, content blocks, custom share card, music player styling, supporter tag, sparkle trail, gold border, exclusive fonts.
- Found on the way, not changed: `plan_rank()` returns Lifetime for a plan name it doesn't know (`PLAN_RANK.get(plan, 1)`).
- Nothing on the pages was changed — the list is for Valer: fix the copy (suggested lines are in the audit) or build the features.

## v3.102 — a new account's first run, on a phone (supersedes v3.101 — no code change)
- Walked on the real templates with the real `auth.js` at 390 (`tools/firstrun-phone.js`): landing from sign-up with a theme (*Starting from the "soft" theme you picked — hit save when it looks right*, the theme on the page and the save bar up), the checklist with the name done and three to go, honest empty tiles (*not published · fill in your page and hit save*, 0 views, 0 links), the header knowing who you are; *Say who you are* landing with the section clear of the sticky header and the display-name field one Tab away; the *about* step ticking itself as you type; the Preview sheet showing the new name, bio and the soft accent; a link ticking the third step; *Hit save* from the checklist sending one PUT with the name, the link and the theme's colours, after which the checklist is gone and the status tile says live. The OAuth variant without a username: step 1 open, the status tile saying why, the header saying *username not set*, step 1 landing on the username field, saving a name ticking it and moving the status to *not published*.
- Nothing needed changing. The tool stays as a regression check.

## v3.101 — the explore page on a phone (supersedes v3.100)
- At 390 on the real template (`tools/explore-phone.js`): no overflow, every filter, card link and field thumb-sized, the search box 16px (no zoom), a tapped filter leaving two cards with the count saying *2 of 12 example pages · soft*, and a card's CTA going to sign-up in that theme.
- With the keyboard up the search box slipped under it, taking the result count with it — the v3.81 nudge now covers the search box and keeps the count in view; the keyboard's Enter key is labelled *Search* (`enterkeyhint`), and on a phone it puts the keyboard away so the results show (Enter never reloaded; now it also blurs on touch-only devices).
- `pages/explore/index.html`, `js/v2.js`, `tools/explore-phone.js`.

## v3.100 — when an upgrade lands (supersedes v3.99)
- A Free dashboard checked for where its pricing links point (`tools/upgrade-test.js`): the plan box's *See upgrades* → `/pricing#lifetime`, the locked video field → `#lifetime`, the locked cursor field → `#supporter`, uploads locked, *No badges on this account yet*. All right.
- Then the entitlement lands while the tab is open (an admin grant now; a checkout later). The dashboard read `/api/v1/me` once, at load, so it kept saying Free until a reload — and coming back from the pricing page via the back button can restore the old page from the browser's cache without one. Now coming back to the tab (`visibilitychange`) or to a cached page (`pageshow`) re-reads `/api/v1/me`; a changed plan or a new badge applies without a reload — plan box, CTA, locked fields, uploads, the badge list — with one line said (*Lifetime is on — the perks below are unlocked.* / *A badge was added to your account…*), and any unsaved edits stay exactly as they were. Nothing changed, nothing said.
- `js/v2.js` (`refreshMe`), `tools/upgrade-test.js`.

## v3.99 — the 404 and maintenance pages (supersedes v3.98)
- Both walked on the real templates, on a phone too (`tools/oops-test.js`). The 404: served as a 404 with its title and h1; `/nobody` prefills the claim box, the lede says the name is nobody's yet and the check confirms *is free — claim it*, Enter claims it; a name that isn't free (a page that is gone, or suspended) gets *right now — and that name isn't free either* with the box marked and Enter held; a reserved one says so; `/nobody.png`, `/@nobody` and `/a` get the plain lede and an empty box; nothing overflows and every link is thumb-sized. Maintenance: the claim box is off with an honest hint, the page re-checks every minute, *try again now* works, no dead links (the Discord one is dropped until there's an invite).
- Two things fixed: the 404's offer only ran on the live host (it now uses the same *where the API is* test as the claim boxes, so it can be tested), and `/some/deep/path` offered *some* as a name — only a single-segment path is a username attempt now.
- `js/v2.js`, `tools/oops-test.js`.

## v3.98 — logging out, two tabs, and coming back (supersedes v3.97)
- Three session edges on the real template (`tools/session-edges.js`). Logging out with unsaved changes used to post the logout first and then let the browser's *leave site?* prompt appear on a page whose session was already gone; now the changes are stashed on the device, one plain question is asked first (*They'll be kept on this device for next time — log out anyway?*), Cancel keeps the session, OK leaves with no second prompt, and the next login offers the changes back.
- The dashboard open in two tabs: a save in one silently let the other overwrite it later. A save now leaves a mark for the other tabs (`localStorage`, `storage` event); a tab that is looking at an older page shows *This page was just saved from another tab or device. Reload to see those changes — saving here would overwrite them* with a Reload button (the draft bar's third mode).
- The session expiring while a tab sits open was already covered by v3.86 (the draft is kept, focus lands on *Log in again*).
- `pages/dashboard/index.html` (the Reload button), `js/v2.js`, `css/v2.css`, `tools/session-edges.js`.

## v3.97 — the login page, by keyboard and screen reader (supersedes v3.96)
- The same treatment sign-up got in v3.77 (`tools/login-a11y.js`): the human-check gate (inert fields, a reachable note, unlock that says so and focuses email), Tab order email → *forgot it?* → password → eye → remember → sign in, *forgot it?* saying plainly that password reset isn't enabled yet with focus kept, a wrong password's refusal in the live message with the single-use check re-locking the form and the note asking for it again, a suspended account's reason shown, and a good login landing on the dashboard.
- Three gaps: when the refusal re-locked the form, the Sign in button went with it and focus fell to the page — it now parks on the gate note, right above the check; after passing the check again focus went to the (still filled) email, when it's the password you'll retype — on the login page it lands on the password, selected (sign-up still goes to its first field); and *Signing in…* / *Creating account…* had no busy state, so a second Enter sent a second request (`auth.js` guards both forms and marks the button `aria-busy`).
- Noted, not changed: the login redirect is the API's (`data.redirect`); a `?next=` back to the page you came from isn't wired anywhere yet.
- `js/v2.js` (the gate hooks), `js/auth.js` (`bindLoginForm`, `bindSignupForm`), `tools/login-a11y.js`.

## v3.96 — renaming, under real conditions (supersedes v3.95)
- The dashboard's username change driven through a slow check, a stale answer after a newer one, a rename the server refuses after the check said free, a double Enter while it saves, and a rename that works (`tools/uname-real.js`). Held: *checking misa.lol/lune…* with no green until the answer, a stale answer never re-enabling Save, the server's reason next to the form with focus kept, and after a real rename the your-link box, the Open link and the nav all following.
- Fixed: the check's answer wasn't read out (the hint is only described on focus) — it is now, once; *Saving…* had no busy state and a second Enter sent a second PATCH (`auth.js` guards the form and marks the button `aria-busy`); and after a successful rename the hint kept offering *is free — save to make it yours* for the name that was now yours (it says *that's your name now*).
- `js/v2.js`, `js/auth.js` (`bindUsernameForm`), `tools/uname-real.js`.

## v3.95 — the username check, under real conditions (supersedes v3.94)
- The live *is misa.lol/name free?* check on the front page and on sign-up, driven through a slow answer (2 s), a stale answer arriving after a newer one, an API that errors, no network, a reserved name, and submitting before the answer (`tools/avail-test.js`). The front page held everywhere: the hint says *hit claim to check it's free* until the answer is in, a slower answer for an older name never overwrites the newer one, a failing or missing API leaves the honest hint with no scare and Enter still goes to sign-up (which checks for real), *reserved* is named and blocks, an early Enter goes through.
- Sign-up had two gaps: the username field turned green (*is-valid*) the moment the format was right, before the check answered — it stays neutral now until the answer says free; and a name the check had already refused could still be submitted (the form only re-checked the format) — it is held now with the hint, focus on the field, nothing sent.
- `js/v2.js` (the sign-up username wiring), `tools/avail-test.js`.

## v3.94 — twenty links on a phone (supersedes v3.93)
- The Links section with a real long list — twenty rows, four switched off, one without a link — at 390 on the real template (`tools/links-many.js`). It held: every row's controls thumb-sized, no overflow, typing in row 15 edits it in place (no re-render, caret where it was, the row's name following), Enter on *move down* deep in the list swaps the rows in ~190 ms with focus on the same button and *Moved "link 15" down to 16 of 20* read out, *Add a link* makes a 21st row on screen with its label focused and flagged as empty.
- One thing the long list showed: the preview phone draws the first four links and said nothing about the rest, so an edit to link 15 seemed to do nothing on the phone. It now says *+16 more on the page* under the four.
- `js/v2.js`, `css/v2.css` (`.pf__more`), `tools/links-many.js`.

## v3.93 — the pricing page, by keyboard and screen reader (supersedes v3.92)
- The funnel the front page sends people down for money (`tools/pricing-a11y.js`). Held: three plan cards with distinct CTAs, the paid ones carrying `?plan=` into sign-up, the *9 more Lifetime perks* / *7 more Supporter perks* disclosures working by keyboard, the compare table's column and section headers, four closed FAQ disclosures, no ambiguous link names, no overflow at 390 and the feature column pinned while the table scrolls.
- What it found: the plans sat under the h1 with no h2 (a hidden *The plans* heading now, and each card is a group named by its own heading, like the front page's); the compare table had no caption (one, visually hidden); and every one of its 44 check marks and 22 dashes was a bare icon — a screen reader read nothing for *included* and *em dash* for *not* — each now carries a hidden *yes* / *no*; the plan names in the table head were 30 px to tap on phones (34 now).
- `pages/pricing/index.html`, `css/v2.css`, `tools/pricing-a11y.js`.

## v3.92 — the public page, by keyboard and screen reader (supersedes v3.91)
- The page every dashboard edit is for, rendered by the real `render_public_profile()` and walked (`tools/render-profile.py` + `tools/profile-a11y.js`): one h1 with the name, *ren · misa.lol* as the title, the bio as the description, the user's own card as the share image, two real links with `noopener`, *12,412 views*, the click beacon per link, reduced motion turning the video and every animation off, no overflow at 390.
- What it found: the links open new tabs without saying so (they carry *(opens in a new tab)* for screen readers now); a text-mode entry read *emailren@example.com* (a space between label and value); the music player's button was just *Play* (now *Play graveyard shift* / *Pause graveyard shift*); the *report* button had no open/closed state, the form's details box had no label, its answer wasn't a live region, cancel dropped focus and sending disabled the button under the keyboard (all fixed: `aria-expanded` + `aria-controls`, a label, `role="status"`, focus back on the button on close, Escape closes, `aria-busy` while sending); with an entry screen up, the page behind it — links, the player — was still reachable by Tab (everything is `inert` until you enter, and focus lands on the page afterwards); *made with misa.lol* and *report* were under 32 px to tap; and only the links had a brand focus ring (every control has one now).
- `app/profile_page.py`, `tests/test_pages.py` (report-form test updated, +1 screen-reader test), `tools/render-profile.py`, `tools/profile-a11y.js`.

## v3.91 — the share and search face (supersedes v3.90)
- Every built page checked for what a pasted link and a search result show (`tools/share-check.py`): title, description and its length, canonical = `og:url`, the full Open Graph and Twitter-card set, the 1200×630 share image, `noindex` on internal pages, no two public pages sharing a title. Nearly all of it already held from v3.5x.
- Three gaps: the only icon was an SVG — iOS ignores those for the home screen (you'd get a screenshot) and older tabs show nothing — so there is now a raster set rendered from the same dagger (`favicon-32.png`, `apple-touch-icon.png` 180, `icon-192.png`, `icon-512.png`) plus a `site.webmanifest` (name, theme colour, icons) served by the app; the kept-for-comparison `/home-v2` was indexable and competing with the front page (its canonical already pointed home; it is `noindex` now, until the v2/v3 decision); and the login page's description was too short for a snippet.
- `app/main.py` (`/site.webmanifest`), `tests/test_pages.py` (+1: manifest + icons), `images/*.png`, `site.webmanifest`, every page's `<head>`, `tools/share-check.py`.

## v3.90 — the dashboard on a slow phone (supersedes v3.89)
- Same rig as v3.89 for the dashboard (`tools/slow-dash.js`): 400 kbps / 400 ms RTT, 4× slower CPU, 390 wide, signed in, the profile API answering after 3 s. First contentful paint at ~2.2 s; the page itself is 60 KB over the wire (CSS 25, scripts 34) before the API; the loading state is on from the first frame (fields disabled, tiles *…*, *loading your links…*) and the editor becomes usable the moment the profile lands.
- What moved when the data arrived: the analytics box appeared out of nowhere (it was `hidden` until the stats came) and pushed the page section down, and on phones the overview tiles' note line wraps to two once *31 today · 240 this week* replaces *checking…*. Cumulative layout shift 0.052 → 0.018: the analytics box is on the page from the first frame as a placeholder (*last 14 days · …*) and only hides when analytics can't load or aren't available, and the tiles reserve the second line under 640 px.
- `pages/dashboard/index.html`, `js/v2.js` (`renderStats`, `loadStats`), `css/v2.css`, `tools/slow-dash.js`.

## v3.89 — the front page on a slow phone (supersedes v3.88)
- Measured on the real templates served over a local HTTP server with nginx-style gzip, Chromium throttled to 400 kbps / 400 ms RTT and a 4× slower CPU, 390 wide (`tools/slow-phone.js`): first contentful paint at ~2.8 s, the hero and claim box on screen right after. What the first view fetches is now the HTML, the CSS (24 KB gzipped), two scripts (34 KB gzipped, deferred) and the poster.
- The poster was the fat part: phones pulled the same 134 KB webp as a desktop. The hero's `<picture>` now offers a 960-wide, 53 KB webp under 640 px (`images/mainbg-poster-960.webp`), the hidden hero video no longer carries a poster of its own (it sits at opacity 0 until its loop plays — the poster was pure waste), and the preview phones take a phone-sized poster after `load` (`data-poster`, set by script) instead of the desktop one before it. A phone's first view: 376 KB → 295 KB uncompressed; a desktop's is unchanged.
- Found on the way: the deferred script switches the reveal-on-scroll system on when it runs, and on a slow connection the page has already painted — everything `.reveal` blinked off and faded back in, and the sections below the fold started a visible fade-out. Now whatever is on screen is marked revealed in the same breath, and the hidden state lands in a single frame (`html.js-snap`) with no transition.
- `pages/index/index.html`, the phone partial on every page, `images/mainbg-poster-960.webp`, `js/v2.js`, `css/v2.css`, `tools/slow-phone.js`; `tools/paint-test.js` and `tools/home-phone.js` updated for the phone-sized poster.

## v3.88 — the dashboard in high contrast, with reduced motion, at 200% (supersedes v3.87)
- Three more runs of the real template (`tools/dash-forced.js`). Windows high-contrast (forced colors): every two-state control still shows its state — link-row toggles, badge switches, theme picks, the sidebar's current link, the selected analytics bar (v3.71's work holds), and the status tile says it in words. Reduced motion: nothing on the dashboard keeps animating. 200% zoom (a 720px-wide viewport): no horizontal scroll, the preview column becomes the Preview button, no tile, field or row clips.
- Two gaps: the preview phone lost the page's colours in high contrast (it is a picture of someone's page, not UI — it now opts out with `forced-color-adjust:none`, on the front page's phones too), and the upload button's spinner kept spinning under reduced motion (it holds still now; the field's *uploading…* note and `aria-busy` carry the state).
- `css/v2.css`, `tools/dash-forced.js`.

## v3.87 — the front page without script (supersedes v3.86)
- Three runs of the real template (`tools/nojs-test.js`): JavaScript off, `v2.js` throwing on its first line, and `v2.js` throwing a third of the way in. With script off everything already held — nothing invisible, the poster and Login show, the wall's `<noscript>` note points at explore, and the claim box goes to `/signup?username=…` as a plain GET.
- The third run found the real risk: `v2.js` marked `<html class="js">` on its first line and only revealed `.reveal` sections at its very end, so any error in between left the page blank below the hero (18 sections invisible). The class is now added right before the reveal observer starts — an error anywhere above leaves the page readable.
- The internal updates page was drawn entirely by script; `build.py` now renders the entries, roadmap and to-dos into the HTML (script only draws them when the list shipped empty), and two literal `<new>` / `<old>` in an old entry are escaped. A v3.86 follow-up: the saved toast only waits for focus to leave when that focus is visible (keyboard) — after a mouse click it still goes on its own.
- `js/v2.js`, `tools/nojs-test.js`; the updates page and `build.py` live in the project.

## v3.86 — saving, when it goes wrong (supersedes v3.85)
- The save flow's failure paths by keyboard + screen reader (`tools/save-fail.js`, real template, `PUT /api/v1/profile/me` mocked): a slow save, a 413 with the API's reason, a 500, a dead network, a 401 mid-session. Already right: the reason lands in the live message, the bar turns into *too big to save / couldn't save — try again / couldn't reach the server* with a **Try again** button, the edit stays in the field, the retry goes through, and on a 401 the changes are stashed on the device and the draft bar explains.
- What wasn't: both Save buttons went `disabled` for the duration, so a keyboard user's focus fell to the top of the page on every save — success or failure; nothing said *saving…* while it was in flight; after a successful save the bar's Save button hides (the *Saved — Open page* state) which dropped focus again, and the toast vanished after four seconds even with focus inside it; after a 401 focus stayed nowhere near the way out.
- Now: the buttons are `aria-busy` (a second Enter is ignored) and keep focus; the bar reads *saving…* / *Saving…*; on success, focus that was on the bar's button moves to its *Open page* link, and the toast waits until focus leaves before it hides; on a 401 focus lands on *Log in again*.
- `js/v2.js` (`save`, `showSaved`, `hideToast`), `css/v2.css` (`.btn[aria-busy]`), `tools/save-fail.js`.

## v3.85 — the front page's headings and the pricing strip, by screen reader (supersedes v3.84)
- The semantics walk (`tools/home-semantics.js`): one h1, every section reachable by an h2, no skipped levels, lists that are lists, every image with an alt, no two links sharing a name but going different places, and the pricing strip's three columns as named groups with distinct CTAs.
- What it found: the *how it works* steps had h3s under no h2 (a screen reader jumping by headings went h1 → h3), the three plan names and the six feature names were plain paragraphs — invisible to a headings list — and the footer's column titles were h4s under an h2. Now: `#how` carries a visually-hidden *How it works* h2; *Free / Lifetime / Supporter* are h3s (on the pricing page too) and each column is a `role="group"` named by its h3, so a screen reader says *Lifetime, group* on entering; the feature names (*Soundtrack*, *Video backgrounds*, …) are h3s; the footer titles are h2s. Nothing changed to the eye — every one of these is styled by its class.
- `build.py` learned the new footer heading so the empty *Community* column (no invite links yet) still gets dropped.
- `pages/index/index.html`, `pages/pricing/index.html`, the footer on every page, `css/v2.css` (the footer heading rule re-targeted), `tools/home-semantics.js`.

## v3.84 — the dashboard's bones, by screen reader (supersedes v3.83)
- The structure walk (`tools/dash-structure-a11y.js`): the skip link is the first Tab stop, shows when focused and drops the next Tab into the editor past the 13 header and sidebar stops; one `main`, a labelled nav, an aside; one h1 and no skipped heading level (h1 → h2 → h3); the sidebar marks the section in view with `aria-current`; a 67-stop Tab walk from top to bottom finds every stop with a visible focus ring.
- Two things weren't right: the header's *View my page* link opens a new tab without saying so (the Your-link box's *Open* already did) — it now reads *View my page — opens in a new tab*; and the three login-method links all read *Connect* — they carry the provider now (*Connect Google / Discord / Telegram*), and once connected `auth.js` names the state too (*Connected: Google*).
- `pages/dashboard/index.html`, `js/auth.js` (`setProviderState`), `tools/dash-structure-a11y.js`.

## v3.83 — the front page on small and awkward phones (supersedes v3.82)
- Walked the front page as a 390 phone, a 320-wide one, a landscape one (740×360) with the menu open, and a desktop on data saver (`tools/home-phone.js`). Held up: a phone fetches the webp poster and, after load, only the preview phone's 296 KB loop — the hero background loop and the mp4 are never requested (the hero video element keeps no `src`); with data saver on, a desktop fetches no video at all; at 320 nothing overflows, the nav's three items don't crowd or spill, the headline fits its column, every tappable thing is 32px+ and the claim box stacks its button on its own row; in landscape the menu scrolls to its last line.
- One thing wasn't right: the open menu's first link started under the bottom edge of the floating nav pill (the padding assumed the bar sat at the top; it sits 14px down and is 62px tall). The menu's top padding now clears the pill on every phone.
- `css/v2.css`, `tools/home-phone.js`.

## v3.82 — the dashboard on a phone, keyboard up (supersedes v3.81)
- Walked the editor as a phone with the on-screen keyboard up, and once more on desktop with Tab (`tools/dash-mobile.js`). Found: the link rows' fields were 14px and the explore search box 15px — iOS zooms the whole page when one is focused and leaves it zoomed; with the keyboard up the browser scrolled only the field into view, so a link row's warning line sat behind the keyboard; the editor's fields aren't in a form, so the keyboard's Enter key was a plain *return* that did nothing; and on desktop a field scrolled into view at the bottom edge (Firefox / Safari align focused fields to the edge) lands underneath the floating save bar.
- Now: on touch screens the link-row fields and the search box are 16px (no zoom); the v3.81 keyboard nudge covers every field on every page — claim boxes, dashboard fields, link rows, auth fields — keeping the field's whole box (hint or warning included) above the keyboard, and treating a save bar inside the visible strip as its edge; the editor's single-line fields carry `enterkeyhint="done"` and on a touch-only device Enter puts the keyboard away (blurs) without saving or leaving — on a desktop Enter changes nothing; and while the save bar is showing the page reserves 110px at the bottom for it (`html:has(.dash__savebar:not([hidden])){scroll-padding-bottom}`) so Tab and focus never scroll a field in underneath it.
- `js/v2.js`, `css/v2.css`, `tools/dash-mobile.js`.

## v3.81 — the claim box on a phone (supersedes v3.80)
- The hero claim box walked on a phone (`tools/claim-mobile.js`: iPhone viewport + touch, the real template, the availability API mocked, the keyboard simulated as a 390×450 strip). Held up: 16px input so iOS doesn't zoom on focus, no auto-capitals or spell-check, the hint says *misa.lol/lune — hit claim to check it's free* until the answer is in and then *is free — claim it* (read out once), a taken name is held on the page with the alternatives, Enter on a good name goes straight to sign-up.
- Fixed: `autocorrect="off"` and `enterkeyhint="go"` on every claim box (hero, CTA, 404, maintenance, kit) — iOS was free to "correct" handles and the keyboard's Enter key was a plain return; the *try ren_ / ren2* alternatives were 21px tall — on touch screens they now get a 37px hit area (padding out, margin back in, no layout shift); and when the on-screen keyboard comes up the browser scrolls only the field into view, leaving the answer under it behind the keyboard — a `visualViewport` resize handler now nudges the page so the box and its hint both stay above it.
- The kit's specimen password field gets `autocomplete="new-password"` (html-validate).
- `pages/index/index.html` and the other claim-box pages, `js/v2.js`, `css/v2.css`, `tools/claim-mobile.js`.

## v3.80 — uploads, by keyboard and screen reader (supersedes v3.79)
- The five upload buttons on the dashboard got the walk (`tools/uploads-a11y.js`, real template, `POST /api/v1/uploads` mocked). Found: two buttons were both named *Upload an image*; a locked button (Free, or the cursor one on Lifetime) was `disabled` — skipped by Tab, silent about why beyond a hover tooltip; while a file went up the button was disabled too, which threw focus to the top of the page; and every result — *Uploaded…*, *too large*, *wrong type*, *server unreachable* — landed in the message box at the top of the form, out of sight from the background fields.
- Now: the buttons are *Upload an avatar image / a track / a background image / a background video / a cursor image*. A locked one stays in the Tab order as `aria-disabled`, is described by a plan note (`#lock-uploads`: *Uploading files comes with Lifetime — $5, once. A link works on every plan*; cursors by `#lock-supporter`), and Enter on it writes *uploads come with Lifetime — a link works on every plan* into the field's own note with a pricing link instead of doing nothing. While a file goes up the button is `aria-busy` (spinner as before), keeps focus, and the field's note reads *uploading me.png…* (with a percentage for big files — the request is an `XMLHttpRequest` now for progress events). Afterwards the note says *uploaded me.png — hit save to publish it* with the green mark, or the reason it didn't (`is-invalid`); each is also read out once through the dashboard's live region, and typing a new link clears it.
- Size and type are checked before anything leaves the browser, with the same limits as the API (`UPLOAD_MAX` mirrors `KINDS`): *that’s 9 MB — avatar images can be up to 8 MB*, *that isn’t a png, jpg, webp or gif file*. One hidden file input per button, reused, out of the Tab order and hidden from screen readers.
- `pages/dashboard/index.html` (button names, the `#lock-uploads` note), `js/v2.js`, `css/v2.css` (the `aria-disabled` look and links inside field notes), `tools/uploads-a11y.js`.

## v3.79 — the explore page, by screen reader (supersedes v3.78)
- The front page's wall sends people to `/explore?theme=…`, so it got the walk (`tools/explore-a11y.js`). Most of it already held: the `?theme=` hand-off presses the matching filter and the live count says *2 of 12 example pages · soft*; the seven filters are toggle buttons in a named group; the search box is labelled, Enter in it doesn't reload, and no hits shows the *nothing here (yet)* box with a way out; every card's phone link is named *Start from ren’s page (gothic theme)* with the fake profile hidden; the featured row's four links are named.
- Two things weren't: every card's second link read *start from this theme →* — twelve identical link names — and the opted-in *real pages* row's links read *ren’s page real*. The card links are now *Start from ren’s page — gothic theme* and the real ones *Open ren’s page — misa.lol/ren* (visible text unchanged).
- `js/v2.js` (the explore gallery and real-pages renderers), `tools/explore-a11y.js`; `tools/wall-a11y.js` waits out the smooth scroll instead of sampling once.

## v3.78 — the analytics box, by screen reader (supersedes v3.77)
- Walked the dashboard's analytics box with a screen reader's ears (`tools/analytics-a11y.js`), with traffic and without. Most of it was already right: the fourteen bars are buttons named *Thu, Aug 27: 30 views*, Enter on one puts its day and number into a live caption and Enter again returns the total, the group is named.
- What was missing: the group had no description, so a screen reader entering it heard *Views per day* and fourteen buttons with no total — it now points at the caption (*last 14 days · 423 views*). The referrer and click lists read *tiktok.com 820* — number, no unit, and the column heading isn't tied to the list — so each number now carries a hidden unit (*820 views*, *88 clicks*, *1 click*) with a real word break before it. An empty 14-day chart said nothing at all; it now says *no views yet — the bars fill in as people visit*, centred in the chart area, with the caption reading *last 14 days · 0 views* and the lists *no visits yet* / *no clicks yet* as before.
- `pages/dashboard` (`aria-describedby` on the bars group, `id="ana-cap"`), `js/v2.js` (`renderStats`), `css/v2.css` (`.ana__bars > .ana__empty`), `tools/analytics-a11y.js`.

## v3.77 — the sign-up page, by screen reader (supersedes v3.76)
- Every front-page path ends on `/signup`, so it got the same walk (`tools/signup-a11y.js`). The fields are inert until Cloudflare's human check passes — right, but nothing said so: a screen reader met the title, *lune*, *or continue with* and the fine print, with the whole form simply absent. A hint-sized note now sits above the fields, outside the locked block — *Pass the human check below to unlock the form.* — turns green with *Human check passed — the form is unlocked.* when the widget calls back, says *Pass the human check again…* whenever `auth.js` re-locks (an expired token, or the single-use token spent on a refused submit), and after a pass focus moves to the first empty field if nothing else has focus (an invisible check can pass while someone is still reading). Same on the login page.
- Field hints already described their inputs; a wrong one (a bad email, a short password, a mismatch) now also marks the input `aria-invalid`, so a failed submit — which already puts focus on the first wrong field — lands on something that says it's wrong and why. The top message (`#auth-message`) is a `role="status"` live region on login and sign-up, as it already was on the dashboard, so a server refusal like *That email already has an account* is read out.
- Checked and left alone: Tab runs username → email → password → eye → confirm → eye → terms → submit; the eye buttons say *Show / Hide password* and hand focus back to the field; the plan chip from `?plan=lifetime` reads *lifetime · $5 once*; the submit button names the link (*Claim misa.lol/lune*).
- `pages/signup`, `pages/login` (`[data-lock-note]`, `#auth-message` role), `js/v2.js` (`setField` + the gate hooks around `misaTurnstileSuccess` / `lockAuthActions`), `css/v2.css` (`.auth__gate`), `tools/signup-a11y.js`.

## v3.76 — badges, Copy and the share card, by keyboard (supersedes v3.75)
- Walked the badges box, the *your link* box and the share card on the real template (`tools/badges-a11y.js`). Toggling a badge disabled the switch while its PATCH was in flight — and disabling the focused control throws keyboard focus off the page, so every flip cost a screen-reader user their place. The switch is now `aria-busy` instead (a second flip while it's busy waits), so focus stays put; a failed PATCH flips it back and explains itself right under the badges (*Could not update that badge — it's back the way it was.*, a `role="status"` line, read once) instead of at the top of the page. Each switch is named *Show the Verified badge on your page*.
- *Copy* went silent for a screen reader (a button's label changing to *Copied* isn't read out), assumed the async clipboard (missing on plain http and older browsers) and, if the clipboard refused, said nothing at all. It now falls back to the old `execCommand` copy, is read out as *Copied misa.lol/ren.*, and on refusal the button says *Copy failed* while the link itself is read out so it can still be taken down.
- The *Open* link said only *Open*; it now reads *Open your page in a new tab* (visible text unchanged). The share card already carried a real alt (*Share card for misa.lol/ren*), opens from its summary by keyboard, and is the live card with a cache key that changes on save — nothing to change there.
- `pages/dashboard` (`[data-badges-msg]`, the sr-only suffix on Open), `js/v2.js` (`renderBadges`, `copyText`, `sayDash`), `tools/badges-a11y.js`.

## v3.75 — every link, checked (supersedes v3.74)
- `tools/links-check.py` walks every `href` and form action in the twelve built pages (285 links: 235 same-site, 50 in-page anchors): same-site paths must be a real page, fragments must point at an id that exists on the target page, no empty `#` targets, new-tab links must carry `rel=noopener`. Clean — the v3 rebuild left no dead anchors, `/pricing#lifetime` / `#supporter` / `#compare` all land on their ids (and the deep-linked plan is highlighted, checked at runtime), and the community links come out entirely while `COMMUNITY` in `build.py` is still empty rather than as dead `#`s.
- The one thing it caught was on the login page: *forgot it?* was an `<a href="#">` that `auth.js` intercepts to show *Password reset is not enabled yet…* — a link that goes nowhere, announced as a link. It's a `<button type="button" class="forgot-link">` now, styled exactly like the label links; `auth.js` binds by class, so its message works unchanged (after the human check, as before — the whole field block is inert until then).
- The front page's runtime links were listed after the script runs: `/#themes`, `/#features`, `/explore` (+ `?theme=` once you pick one), `/pricing`, `/pricing#compare`, `/pricing#lifetime`, `/login`, `/signup` (+ `?username=&theme=` from the claim box), `/terms`, `/privacy`. Nothing dead.
- `pages/login`, `css/v2.css` (`.field__label .forgot-link`), `tools/links-check.py`.

## v3.74 — the Account section, by keyboard and screen reader (supersedes v3.73)
- Walked username change, password change and delete on the real template with the API mocked (`tools/account-a11y.js`). The three forms sit at the bottom of the dashboard, and every answer they gave — *Username saved.*, *The two passwords don't match.*, *Current password is wrong.*, *Type delete to confirm.* — went to the message box at the **top** of the page. A sighted user pressing *Save password* saw nothing happen (the fields cleared, or didn't); a screen reader heard it, but from a region nowhere near the form.
- Each form now has its own status line, right above its button (the same `.auth-message` component as the top box, `role="status"` so it's read once), and the answers land there. The username form's save runs through `auth.js`, which reports via the global `showAuthMessage`; for that one save `js/v2.js` routes the report to the form's line and restores the global after.
- A caught mistake also marks its field: the second password field is `aria-invalid` and focused on a mismatch, the *type delete* field on the wrong word; typing clears the mark. The native *cannot be undone* confirm stays as it was.
- `pages/dashboard` (`[data-form-msg]` in the three forms), `js/v2.js` (`formMsg`, `markBad`, the password / delete / username handlers), `css/v2.css` (`.dash form .auth-message`), `tools/account-a11y.js`.

## v3.73 — the claim box and the phone menu, by screen reader (supersedes v3.72)
- The claim box on the real front page (`tools/claim-a11y.js`): the hint is `aria-describedby` on the field, so it's read on focus — but nothing was read as it changed. A bad name pressed with Enter didn't submit (good) but said nothing, wasn't marked invalid, and the browser's own *match the requested format* bubble was doing the stopping. The *fix* button (*no spaces — use* **ren_mix**) was reachable but named only *ren_mix*.
- Now a polite live line says the things worth saying and nothing else: the availability answer (*misa.lol/lune is free — claim it* / *misa.lol/ren is taken — try ren_ or ren2*) and a failed submit's reason; typing itself isn't read out. The field is `aria-invalid` whenever the hint shows a problem, the fix button is *Use ren_mix*, and the script owns validation (`form.noValidate` set by script, so no-JS keeps the browser's pattern check). Same code serves the CTA's claim box and the 404 page's.
- The phone menu opened as a plain overlay: Tab walked through its five links and then on into the page underneath, and Escape left focus wherever it was. While it's open it's now a modal dialog named *Menu*, everything behind it is inert, Tab wraps between the burger and the links, and Escape (or picking a link) puts focus back on the burger.
- `js/v2.js` (`sayClaim`, `setInvalid`, `fixBtn`, the claim submit handler, `setMenu` + a Tab wrap), `tools/claim-a11y.js`.

## v3.72 — the Links section by keyboard (supersedes v3.71)
- Walked the dashboard's Links section with Tab on the real template (`tools/links-a11y.js`). Inside a row the order is platform → label → link → text → on → move up → move down → remove; the first row's *move up* and the last row's *move down* are disabled. What was wrong:
- A row had no name: a screen reader heard *Platform, combo box … Label, edit … Link, edit* for every row with nothing to say which link it was on. Each row is now a group named *Link 2 — the server* (the name follows the label as you type; an unlabelled row falls back to its link or platform).
- Nothing was announced: moving a link, removing one, adding one, and the platform auto-pick (which only flashed the box) were all silent. A live line in the section now says *Moved “the server” down to 3 of 3.*, *Removed “new single” — 2 links left.*, *Added link 2 of 2 — give it a label and a link.* and *Platform set to SoundCloud.*
- Focus fell off the page twice: after a remove (the button you pressed was gone) and after moving a row to the very top or bottom (the same-direction button there is disabled, and focusing a disabled button lands on nothing). A remove hands focus to the next row's remove button (or the previous one's, or *Add a link* when none is left); a move that reaches the end lands on the still-enabled move button.
- Forced colours on the editor: the theme tiles keep their colours (v3.71's rule), and the analytics bars — plain gradients, erased by that mode — are drawn in `CanvasText` there.
- `pages/dashboard` (`[data-links-live]`), `js/v2.js` (`rowName`, `sayLinks`, the move / remove / add handlers, `autoPlatform`), `css/v2.css` (`.ana__bar i` under forced colours), `tools/links-a11y.js`.

## v3.71 — zoomed in, images off, high contrast (supersedes v3.70)
- The front page at 200% and 400% browser zoom on a 1280px screen (640 and 320 CSS px, WCAG 1.4.10 reflow), on the real template: no horizontal scrolling, nothing sticks out of the viewport, the hero stacks copy → phone → lab, no nowrap text is clipped. Nothing to change.
- With images blocked: the poster is gone, no broken-image icons (the page's one `<img>` is decorative, `alt=""`), the hero reads as ivory on ink with its glow; the loops still play, since they're media, not images. Nothing to change.
- Under forced colours (Windows high contrast) the six theme swatches became six identical circles — the mode strips background colours — and a switch's state only showed as knob position. Colour samples now keep their colours (`forced-color-adjust:none` on the swatches, the dashboard's theme tiles and the explore filter dots), the checked swatch and the pressed theme tile get a `Highlight` ring, and an on switch has a `Highlight` track and border with a `CanvasText` knob. `css/v2.css` (`@media (forced-colors:active)`), `tools/reflow-test.js`.

## v3.70 — the editor by keyboard (supersedes v3.69)
- Walked the dashboard's Look section with Tab on the real template (`tools/dash-a11y.js`, free and lifetime). All 31 controls have names, Tab runs themes → colours → behind the card → effects → what shows → the card, the theme tiles are toggle buttons in a named group. What was wrong:
- The four sliders announced raw numbers — *0.5* for card opacity, *14* for blur. They now carry `aria-valuetext` in step with the readout (*50%*, *14px*), updated on every change, arrow keys included.
- A locked perk was just a dimmed, disabled control — a screen reader heard *unavailable* and nothing else, and the two effect selects (username effect, background effect) had no *unlock* link at all, unlike the other perks. Every locked control now points at a hidden note (*Lifetime perk — $5, once. Unlock it on the pricing page.* / the Supporter one at $9.99), the selects have the same *lifetime perk — unlock* row as the rest, and each unlock link's spoken name carries its field (*background video — lifetime perk, unlock*) so four links aren't four of the same.
- The phone's peek sheet opened as a modal dialog but Tab walked straight out of it into the editor behind. While it's open everything else in `.dash` is `inert`, and Tab / Shift+Tab wrap inside the sheet where `inert` isn't supported; Escape still closes it and focus still returns to the peek button.
- `pages/dashboard` (`#lock-lifetime` / `#lock-supporter` notes, label rows on the two selects), `js/v2.js` (`readout`, `applyPlan`, `setPeek`, `peekTrap`), `tools/dash-a11y.js`.

## v3.69 — the wall and the ticker, by keyboard (supersedes v3.68)
- Walked the front page's wall of example pages with Tab on the real template (`tools/wall-a11y.js`). All twelve cards are real buttons, the fake profiles inside them are hidden from screen readers, Tab moves through them in order and on to the rest of the page (on phones: the six cards, then *All twelve on explore*). What was wrong: every card was named *Try the gothic theme* — six names for twelve cards, so a screen reader heard the same button twice. Each is now *ren’s page — try the gothic theme*.
- Activating a card (Enter, Space, a tap) puts the theme on the hero phone and scrolls to it; focus now moves to that theme's swatch by the phone, so the next thing a screen reader says is *Soft theme, radio, checked* — right where the lab is — instead of staying on a card that has scrolled away. (Focus is moved before the smooth scroll starts: moving it after cut the scroll short.)
- The ticker only paused on hover, which a keyboard can't do (WCAG 2.2.2 wants a control). A small pause / play button sits on its right edge (`.ticker__pause`, `aria-pressed`, thumb-sized on touch screens, hidden under reduced motion where the track doesn't move anyway); the scrolling text itself is what's `aria-hidden`, not the whole strip, so the button isn't focusable-inside-hidden. Pausing sticks for the tab (`sessionStorage.misaTicker`).
- `pages/index` (ticker markup), `partials/sprite` (`#i-pause`), `js/v2.js` (`renderWall` names, focus hand-off, `setTick`), `css/v2.css` (`.ticker__pause`, `.ticker.is-paused`), `tools/wall-a11y.js`.

## v3.68 — the dashboard on a slow phone (supersedes v3.67)
- Measured `/dashboard` before `load` on a phone: 277 KB — and the three provider icons in Account (50 KB) loading eagerly from the bottom of the page. They're `loading="lazy"` now: 229 KB.
- Then the part that matters on a slow connection: what the editor shows while `/me` and the profile are still on their way. It painted **0 page views · 0 links · 0 badges** for a page with 12.4k views, the fields were live — a bio typed in those seconds was wiped when the profile landed (`tools/slow-test.js` reproduces it) — and the three requests ran one after the other (`/me` → profile → stats), so a 2.5 s round-trip cost 7.5 s before the last tile filled.
- Now: the tiles hold **…** (muted, a slow pulse unless reduced motion), the whole editor is `aria-busy` and disabled — fields, theme tiles, Add a link, Save — until `/me` and the profile have answered, the Links section says *loading your links…* instead of standing empty, and the three requests go out together (2.5 s round-trip → 2.5 s). Save and Add a link show that they're off (`.dash .btn:disabled`), which they didn't during a save either.
- Live view count wins: once `/me/stats` has answered, the views tile never falls back to the count stored with the profile, whichever request lands first.
- Dead network: the editor stays disabled with *Could not load your page. Refresh to try again.* — no unhandled rejections (the parallel requests carry their own catch), and `auth.js` no longer leaves *loading…* in the nav (`loadDashboard` catches the fetch; nav shows —).
- `pages/dashboard` (`is-loading` + `aria-busy` on `main`, tiles start at …, lazy icons), `js/v2.js` (`setLoading`, parallel `load`, `liveViews`), `js/auth.js` (`loadDashboard` try/catch), `css/v2.css` (`.dash-editor.is-loading`, `.dash .btn:disabled`), `tools/slow-test.js`, `tools/weight-test.js` (now takes a page + signed-in flag).

## v3.67 — first paint (supersedes v3.66)
- Measured what the front page fetches before `load` on the real template: 736 KB in 9 requests — the poster JPEG (223 KB), the preview phone's loop (289 KB, autoplaying from the markup so it raced the poster, the CSS and the fonts for the wire), `css/v2.css`, `js/v2.js`, and `config.js` + `auth.js` loaded synchronously in the head, blocking the first paint until both had arrived. After: 358 KB in 8 requests, no render-blocking scripts.
- The poster is now a WebP (`images/mainbg-poster.webp`, 134 KB, same 1671×941, quality 75 — indistinguishable behind the hero's overlay). The hero uses `<picture>` with the JPEG as fallback, so the old file stays for browsers without WebP; both video posters (hero loop, preview phone) and the login stage point at the WebP as well — one file, cached once.
- The preview phone's loop (`partials/phone.html`, so the front page, sign-up and home-v2) no longer autoplays from the markup: `preload="none"` + `data-autoplay`, and `js/v2.js` starts it on `load`. With `prefers-reduced-motion` or data saver it never starts — the poster frame stays — which the lab's *video background* switch still overrides by hand. Before, the loop played under reduced motion too.
- `config.js` + `auth.js` are `defer` on every page except login and sign-up, where the Turnstile tail reads the site key inline and the auth contract stays exactly as it was. Deferred scripts still run in order before `DOMContentLoaded`, so `markLoggedInNav` / `loadDashboard` behave the same (checked signed-in and guest, front page and dashboard).
- Fonts: every requested weight is used somewhere on the page (Inter 400–800, Playfair regular for the paper theme, italic for the accents, Caveat 500–700 for the handwriting), so nothing to trim there without touching the design. The wall's example pages are drawn in CSS — no thumbnails to lazy-load.
- `tools/weight-test.js` (the before-`load` accounting), `tools/paint-test.js` (loop timing, reduced motion, data saver, the toggle, the WebP, deferred nav marking). `build_site.py` rewrites `srcset` like `src`.

## v3.66 — the returning user, end to end + a save you can see (supersedes v3.65)
- Second walk-through on the real templates, this time as someone coming back: `/login` (Turnstile, remember me) → `/dashboard` with a saved page (status *live*, two links, no first-run checklist, plan box, views) → *Add a link* → save → open the public page — which the test renders with the real `app/profile_page.py` from exactly what the dashboard sent. The new link is on the page with its click id, bare handles get `https://`, the badge and view count show. Holds at 1440, 390 and 320.
- What it showed: after a save the bar at the bottom simply vanished, and the *Saved* message lives at the top of the page — so on the Links section, where you actually pressed save, nothing confirmed it. Now the bar turns green for four seconds — *Saved — your page is up to date* with an **Open page** link in place of the button (just *Saved · Open page* on a 320px phone) — then goes away; an edit in those four seconds flips it straight back to *unsaved changes*. The green toast is muted for screen readers while `#auth-message` announces the same thing, so it isn't said twice.
- The test also caught the toast's timer sharing a name with the status note's timer (`refreshStatus` cleared it, so the toast never went away) — fixed before it shipped.
- `pages/dashboard` (the Open page link in the savebar carries `data-view-page`, so it always points at your link), `js/v2.js` (`showSaved` / `unsaved`, `touch`, `save`), `css/v2.css` (`.dash__savebar.is-saved`, `.dash__saved-more`), `tools/returning-test.js`.

## v3.65 — the whole funnel, end to end (supersedes v3.63)
- Walked the real templates as one person would: front page → pick the *soft* swatch, type *Lune*, hit claim → `/signup?username=Lune&theme=soft` → sign-up with the name filled in and the preview phone already soft → Turnstile, email, password, terms → `POST /api/v1/auth/signup` → `/dashboard` opening on the soft theme, the *Starting from the “soft” theme you picked* note, the save bar up and the first-run checklist showing. All of it holds, at 1440 and 390.
- One thing it caught: the nav's **Claim** button stopped carrying the typed name in v3.37 (the claim-box rewrite replaced the block that held its click handler). It's back — and it now carries the theme too, so nav Claim and the hero box land on the same sign-up. The href stays relative.
- The theme you tried on the hero phone now travels with the claim box itself (a hidden `theme` field is added on submit, only when you actually picked one), not just with the explore link.
- `tools/funnel-test.js` is the walk-through, on the real templates with the API mocked; `js/v2.js` (claim submit, `[data-claim]` handler).

## v3.64 — theme tiles, checked by hand (no code change; v3.63 stays current)
- The six "Aa" tiles put each theme's own text colour on that theme's own base colour (the accent only shows at the tile's far edge): ivory on ink, plum on pink, white on black, ink on ivory, cream on deep purple, mint on near-black — every pair well over 4.5:1. The pressed ring is the brand crimson on the panel and reads on all six, paper included. Nothing to change.

## v3.63 — the 404 tells the truth about the name (supersedes v3.62)
- misa.lol/rne (a typo, a moved page) already fills the claim box with *rne* and says *nobody has that name yet*. But a 404 isn't always a free name — reserved words 404 too, and so does an account that's been suspended. The lede now follows the same availability check the claim box runs: *…right now — that name is reserved* / *…and that name isn't free either*, while the box itself says taken / reserved and offers alternatives.
- Under it, a small fix in the availability helper: two askers for the same name (the lede and the claim box) used to cancel each other — only the last one got the answer. Now one request answers everyone who asked.
- Checked after v3.51: the 404 page has no placeholder links and the three-column footer.
- `js/v2.js` (`checkAvail`, the 404 block).

## v3.62 — the dashboard without JavaScript (supersedes v3.61)
- The dashboard and the admin page are scripts; with JavaScript off they showed a page of empty tiles and "loading…". Now a `<noscript>` strip at the top says so plainly — *The dashboard is a script — with JavaScript off it can only show you empty tiles. Turn it on for misa.lol and reload.*
- Checked, already right: a logged-out visitor to `/dashboard` or `/admin` is redirected to `/login` by the server before any HTML is sent (no flash of an empty dashboard), and a logged-in visitor to `/login` or `/signup` goes to `/dashboard`.
- `dashboard/index.html`, `admin/index.html`.

## v3.61 — without JavaScript (supersedes v3.60)
- Rendered the front page with scripts off. Everything shows — the entrance and reveal animations only run when `html.js` is set, so nothing is left invisible; the ticker and the caret are CSS; the claim box submits as a plain form. The one hole was the wall: it's drawn by script, so the neighbourhood was a heading over nothing. Now a `<noscript>` line explains it and the *All twelve on explore* button shows whenever the script hasn't run.
- `index/index.html`, `css/v2.css`.

## v3.60 — the live phone shows your background (supersedes v3.59)
- Paste a background image link and the live phone shows it (cover, centred, at your background opacity); paste a direct video link (`.mp4` / `.webm`) and the phone plays it muted on a loop — created on demand, paused under reduced motion, removed when the field is cleared. Only links the page itself would use count (the v3.44 checks): a YouTube page does nothing, as on the page.
- `js/v2.js` (`preview()`).

## v3.59 — half the video (supersedes v3.58)
- The hero loop and the phone mock's video were one 607 KB MP4 that carried an audio track nobody hears (everything is muted). Now: `images/mainbg.webm` (VP9, 296 KB — visually identical behind the tint) is offered first, and `images/mainbg.mp4` is the same H.264 stream without the audio (523 KB) as the fallback. The loops loader picks WebM when the browser can play it (`data-src-webm`); the phone mock lists `<source>` WebM then MP4. Chromium and Firefox fetch one 296 KB file for the whole page; Safari without VP9 gets the 523 KB MP4. Phones still don't load the hero loop at all.
- Checked and left as is: `preload="none"` holds until the loader runs after `load` (idle), and the loader already bows out under reduced motion and the Save-Data hint.
- `images/mainbg.webm` (new), `images/mainbg.mp4` (re-muxed), `index/index.html`, `login/index.html`, the phone partial in every page that has it, `js/v2.js`; `src/build.py` / `build_site.py` know the new attribute.

## v3.58 — the share card, cached properly (supersedes v3.57)
- The overview's "what your link looks like when it's posted" image was requested as `/<name>/card.png?t=<now>` — a fresh URL on every load and every save, so the browser could never keep it even though the server says `max-age=300`. The URL now carries a short key derived from what's saved (`?v=<hash of the editable config>`): same page → same URL → cached; a save changes the key, and the server drops its own copy on save anyway.
- `js/v2.js` (`cardKey`, `applyShare`).

## v3.57 — the ticker rests (supersedes v3.56 / v3.55)
- The ticker was the one thing on the front page that never stopped: a 48-second loop that kept animating below the fold and in a background tab. It now pauses whenever it isn't on screen and whenever the tab is hidden, and resumes where it was (hover still pauses it; reduced motion still stops it entirely). Same on the log-in page's ticker, since it's the same component.
- `js/v2.js`, `css/v2.css` (`.ticker.is-off`).

## v3.56 — dashboard contrast sweep (no code change; v3.55 stays current)
- Every visible text run on the dashboard measured against its real background. Everything passes AA except two brand elements: the crimson eyebrow labels on panel backgrounds (4.4:1 at 11.5px — 4.7:1 on the page ground, so it's only the panels), and white on the crimson buttons (4.4:1). Both are the brand palette, not bugs — a slightly darker crimson (`--crimson-2`) for text-on-panel and button grounds would clear both; your call.
- Muted labels (`--mute` on `--panel`) are 4.8:1, the gold "won't show" note 7:1, the green "live" status 6:1, the crimson "not published" status is large text (38px) and fine.

## v3.55 — the manifesto, legible (supersedes v3.54)
- The two paragraphs on the crimson manifesto were 85% ink on crimson — 4.3:1, just under the 4.5:1 that body text needs; the eyebrow was 70% ink, 3.6:1. Both are solid ink now (4.7:1). The headline and the hand-written sign-off are large text and were already fine (3.6:1 for ivory on crimson, over the 3:1 large-text bar). Reading width checked: ~47 characters a line at 18.7px, two columns — comfortable.
- Not changed, for you to decide: white on the crimson buttons is 4.4:1 — a hair under AA for 15px text. The brand's darker crimson (`--crimson-2`, #d4053d) as the button ground would be 7.6:1, but that's a brand call, not a bug fix.
- `css/v2.css` only.

## v3.54 — view my page, honestly (supersedes v3.53)
- "View my page" (top bar) and "Open" (your-link row) opened misa.lol/<name> in the same tab — on top of unsaved edits, and to a 404 if nothing had been saved yet. Both open a new tab now (`rel="noopener"`); with no username the click sends you to Account; with nothing saved yet it says *Your page isn't live yet — hit save first* instead of opening; with unsaved edits it opens and notes *Opened what's saved — your unsaved changes aren't on it yet*.
- `dashboard/index.html`, `js/v2.js`.

## v3.53 — explore, already filtered (supersedes v3.52)
- The wall's button read *All twelve on explore* whatever you'd just tried. Once you pick a theme (a swatch, an arrow key, a page on the wall) it becomes *More soft pages on explore* and points at `/explore?theme=soft`, which the explore page already understands — it opens with that filter pressed. Before any pick it stays *All twelve on explore* → `/explore`.
- `index/index.html` (one span), `js/v2.js` (`syncMore`).

## v3.52 — the save bar is the retry (supersedes v3.51)
- A save that fails for any reason other than an expired session (storage down → 502, a body too large → 413, no network) used to leave a red line at the top of the page and a save bar that still said "unsaved changes". Now the bar turns red with a short reason — *couldn't save — try again* / *too big to save* / *couldn't reach the server* — its button reads **Try again**, it shakes once (not under reduced motion), and the full server detail still goes to the message strip. The next attempt resets it; the edits stay exactly where they were.
- Fixed on the way: the save bar is a fixed, centred pill, and a fixed element anchored at `left:50%` only gets half the viewport to size itself — so on phones its label had been wrapping ("unsaved / changes") since it was born. `width:max-content` with a viewport cap, and a slightly tighter pill under 420px.
- `dashboard/index.html`, `js/v2.js` (`saveState`), `css/v2.css`.

## v3.51 — no links to nowhere (supersedes v3.50)
- The Discord and Telegram links in the closing CTA, the footer's Community column and the maintenance page have been `href="#"` since v2 — a TODO that read as dead links. The build now has one place for the invites (`COMMUNITY` at the top of `src/build.py`): paste a URL and every link lights up with `rel="noopener"`; leave it empty and that link is dropped. With both empty, the "or come hang out first" row and the whole Community column go, and the footer becomes three columns so nothing sits in an empty track. Every page rebuilt this way (index, pricing, explore, terms, privacy, 404, maintenance, home-v2).
- `src/build.py` (`COMMUNITY`, `community()`), `css/v2.css` (`.footer__grid--3`).

## v3.50 — the badges empty state, by plan (supersedes v3.49)
- Under Links → Badges, everyone without a badge saw *no badges on this account yet.* — no idea how one is earned. Now it depends on the plan: on **Free**, *Badges are granted, not toggled — the verified check comes with Lifetime, the gold one with Supporter* (both linked to the pricing page); on **Lifetime** / **Supporter**, the same sentence says the badge is granted by the team rather than switched on here, so an empty list means it hasn't been applied yet.
- Why that wording: badges are `user_badges` rows the admin grants (v3.13); nothing in the repo grants the verified check automatically when a plan is bought. That's a real gap between the pricing page's promise and the mechanism — worth wiring to whatever checkout ends up doing (grant plan → grant badge), or a one-off admin habit until then.
- `js/v2.js` (`badgesEmptyCopy`), `css/v2.css`.

## v3.49 — the wall says what a hover does (supersedes v3.48)
- Desktop: hovering an example page on the wall lifts it, but nothing said it was clickable. Now an ivory **try this look** chip rises onto the phone's bottom edge on hover and on keyboard focus; it's hidden on touch devices (a tap already just works) and doesn't animate under reduced motion.
- Keyboard focus on a wall item used to draw a rectangle around the whole tilted card, caption included. The ring now follows the phone (rounded, offset), as on explore.
- `js/v2.js` (chip in `renderWall`), `css/v2.css`.

## v3.48 — phone-sized targets (supersedes v3.47)
- Dashboard → Links on phones: the move up / down arrows were 30×38 and the remove button 38×38 — now 38×40 and 40×40 under 640px. The chart's day letters go from 9.5px to 11px there.
- Every page: the logo in the nav bar is a 44px-tall target (it was 26px); the bar is 60px, so nothing moves.
- Left as is: the 14 chart bars are 17px wide on a phone — they're buttons with a caption since v3.40, and there's no honest way to make 14 days wider than the screen allows. The audit is otherwise clean on both pages.
- `css/v2.css` only.

## v3.47 — the sizes nobody tests (supersedes v3.46)
- Looked at the hero at 1024×768 (iPad landscape), 1920×1080 and 2560×1440. All three hold: the copy column caps at 680px, the phone at 352px, the headline at 148px, the ticker lands on the fold at 1080. One fix: between 941 and 1100px the three effect toggles wrapped by four pixels — tighter gap and padding on that band so they sit on one line at 1024.
- `css/v2.css` only.

## v3.46 — one status, one voice (supersedes v3.45 / v3.44)
- The status tile is driven by one small state machine now: *no username → pick one under Account to publish* · *not published → fill in your page and hit save* · *live → unsaved changes — hit save* (new: it used to keep saying "your page is published" while the save bar said otherwise) · *live → saved just now* (reverts to *your page is published* after 8 s; it used to stay forever) · *live → your page is published*. If the dashboard can't load at all, the tile says *couldn't load — refresh to try again* instead of sitting on "checking…".
- The views tile on a page that isn't live yet reads *once your page is live* instead of *since your page went live*.
- `js/v2.js` (`refreshStatus`).

## v3.45 — the claims, traced (no code change; v3.44 stays current)
- Every claim on the v3 front page, traced to a source: **free forever** and **not a subscription / no subscription** — the live site's own meta description; **one payment, yours for life** — the pricing model (Lifetime / Supporter are one-time entitlements; the admin *can* grant a dated trial, which the dashboard then shows as "until <date>", so the copy is true of purchases); **video backgrounds, custom cursors, typewriter bios, gold sparkles, verified check, image host, encrypted chats, analytics** — each is a gated feature in `app/core/plans.py` or a dashboard field; **"the card looks like your page, not ours"** — `share_card.py` renders from the profile config.
- The one claim the repo can't prove: **live in under a minute** (claim box hint, step 1). It came from the original page's "Live in under a minute" heading; sign-up → name → save is a short path, but a minute is a promise. Kept, flagged — say the word and it becomes "live tonight" or goes.
- Not on v3 at all: 200K+ / 40M+ / 100+ (still on the v2 page, already a TODO).

## v3.44 — links that can't work, said early (supersedes v3.43)
- The five asset fields (avatar, audio, background image, background video, cursor) accepted any link, the server kept it, and the page used it as-is — a YouTube page as an avatar, a Spotify page as the track. Now, as you type: a page on YouTube / Spotify / SoundCloud / TikTok / Instagram / X / Facebook / Vimeo / Google Drive / Pinterest / Threads gets *that's a page, not a file — the page needs a direct link to the audio (or an upload)*; a file of the wrong kind gets *that looks like a video file, not an image*; anything that isn't http(s) gets *needs to start with https:// — the page will ignore this one* (which is exactly what the renderer does). Direct links and uploads (`/u/…`) pass silently. A note, not a block — the server still decides.
- `dashboard/index.html` (`data-asset` + a hint line per field), `js/v2.js` (`assetDoubt`, `assetCheck`).

## v3.43 — lighter on phones (supersedes v3.42)
- The front page built all twelve example phones and hid six with CSS under 640px. It now builds six on phones — 883 DOM nodes instead of 1,159 — and builds the other six the moment the viewport grows past 640px (rotate, resize), with the CSS rule still there as a backstop. Desktop unchanged (1,159 nodes, well under the usual 1,500 warning line).
- `js/v2.js` (`renderWall`).

## v3.42 — the dashboard for keyboards and screen readers (supersedes v3.41)
- The section nav sets `aria-current` on the section you're in (it only had a visual state). The first-run checklist reads "done:" before a step that's done. The unsaved-changes bar and the message strip are live regions, so a screen reader hears "unsaved changes" and "Saved." without hunting for them. The phone-preview sheet is a `dialog` (`aria-modal`) while it's open and an ordinary aside otherwise.
- Checked and left alone: every field has a label (colours, sliders with their readouts, the link-row inputs, the toggles), the move / remove / upload buttons have names, the skip link is first in the page, and Esc / backdrop / focus return on the sheet work from the keyboard.
- `dashboard/index.html`, `js/v2.js`.

## v3.41 — the hero controls, for keyboards and screen readers (supersedes v3.40)
- Theme swatches are a real `radiogroup`: one tab stop (the chosen theme), ← → ↑ ↓ move and pick, Home / End jump, wraps at the ends; each swatch is `role="radio"` with `aria-checked`, and picking a page on the wall updates the radios too. Same on the v2 front page.
- The three effect toggles are `role="switch"` with `aria-checked` — a screen reader says "video background, switch, on" instead of "button, pressed". Space / Enter toggle as before.
- The phone mock already reads as a labelled group ("Live preview of your misa.lol page"); the ticker and the hand-written notes stay hidden from assistive tech; the dashboard's phone is `aria-hidden` (its fields are the accessible version).
- `index/index.html`, `home-v2/index.html`, `js/v2.js`, `css/v2.css`.

## v3.40 — analytics you can tap (supersedes v3.39)
- Dashboard → Overview: the 14-day bars are buttons now. A tap (or focus + Enter) puts the day and its number in a caption under the chart — *Fri, Sep 4 · 14 views* — tap again to go back to *last 14 days · 94 views*. Each bar carries the same text as its accessible name; the old hover title never worked on phones.
- "Where from" now starts with **direct or from apps** — the views the server saw with no referrer host (total minus everything attributed, both all-time) — so the list adds up instead of silently missing most visits. The empty state reads *no visits yet*.
- `dashboard/index.html` (caption element, `role="group"`), `js/v2.js` (`renderStats`), `css/v2.css`.

## v3.39 — rhythm on phones (supersedes v3.38)
- The three "how it works" steps were tall cards on phones (number on top, ~190px each). Under 640px each is a row — number beside the words — so the strip is 374px instead of 572px and the page gets to the neighbourhood sooner. Desktop unchanged.
- Looked at the rest of the phone rhythm (steps → wall → manifesto → features → pricing → CTA): the crimson manifesto already breaks the two text runs, the features section is long because it has six real demos, not padding. No second ticker — more motion isn't what the page needs.
- `css/v2.css` only.

## v3.38 — a link that isn't one (supersedes v3.37)
- The public page has always skipped a link row with no link in it; the dashboard didn't say so — the live phone showed the row, the "links" tile counted it, and the first-run checklist ticked "add a link" for a label alone. Now a row that's on but has no link or handle gets a gold outline on the link field and a one-line note under the row (*won't show on your page until it has a link or handle*); the phone, the tile and the checklist leave it out, exactly like the page does. Turning the row off clears the note.
- Badges needed no change: only badges you own are listed, so there's nothing unowned to toggle.
- `js/v2.js`, `css/v2.css` (`.social-row.is-empty`, `.social-row__warn`).

## v3.37 — the claim box explains itself (supersedes v3.36)
- Every claim box (hero, pricing, 404, the closing CTA) now copes with what people actually paste: `https://misa.lol/lune`, `misa.lol/lune` and `@peach` are cleaned to the name; `my name` gets *no spaces — use my_name* with **my_name** as a button; `ren!!` offers **ren**; `9lives` → *has to start with a letter*; `re` → *at least 3 characters*; `rené` / emoji → *letters, numbers and underscores only — no emoji or accents*. `Ren` is shown as misa.lol/**ren** with a "(links are lowercase)" note, which is what the server does.
- A taken name offers two real buttons — *is taken — try **ren_** or **ren2*** — and each click re-checks. Submitting a name we already know is taken or reserved is blocked (it used to bounce off the sign-up page instead).
- `js/v2.js` (`cleanName`, `nameProblem`, `fixBtn`), `css/v2.css` (`.claim__fix`). Eleven inputs + both submits covered by `src/tools/claim-test.js`.

## v3.36 — the username form, and a rename bug (supersedes v3.35)
- Dashboard → Account: the username field now checks availability as you type, like the claim boxes — *misa.lol/lune is free — save to make it yours* / *taken* / *reserved* / *that's your name already* — and the Save button only lights up for a real, free, valid change. The hint says plainly that changing it changes your link and the old one stops working (it does — there's no redirect).
- Bug: `PATCH /api/v1/me/username` renamed the account but not the saved profile config, and the public page and the share card read the name from there — so misa.lol/<new> kept saying "misa.lol/<old>" (and og:url pointed at the dead link) until the next dashboard save. The rename now follows into the config, and both names' share cards plus the explore cache are dropped. Test added (39 pass).
- `dashboard/index.html`, `js/v2.js`, `app/api/v1/users.py`, `tests/test_profile_api.py`.

## v3.35 — honesty pass on the front page (supersedes v3.34)
- Audited every number and name on the front page. The twelve example pages are invented personas (the lede says so, on phones too); the hero phone's "12.4k views", the analytics widget's "1,204 this week" and the wall's view counts are mock-ups inside mock phones, never presented as site statistics; no "200K+ / 40M+"-style claims remain on v3. Nothing needed rewording.
- Two names are now reserved in `app/core/security.py`: **yourname** — the placeholder on every claim box, the hero, the share card — and **u**, the uploads mount. Test added (38 pass).
- Left for you: the twelve persona handles (ren, peach, void, n0t_found, lune, kuro, mortis, mochi, hex, gl1tch, nova, ivy) are *not* reserved — a real member can own misa.lol/ren while the front page shows a fictional "ren". Reserving them costs real people twelve nice names; the admin page's *Reserved names* form does it in a minute if you'd rather.

## v3.34 — drafts that survive (supersedes v3.33)
- Every dashboard edit is stashed on the device (`localStorage`, per account, 400 ms after the last keystroke): an expired session, a crash, a closed tab or a refresh no longer loses the work. On load, a draft that differs from what the server has shows a bar — *You have unsaved changes from today at 12:58 on this device* — with **Restore** / **Discard**; a successful save clears the draft.
- Saving into an expired session (PUT → 401) used to say "Not authenticated." and leave you stuck. Now the bar switches to *Your session expired — your changes are kept on this device* with a **Log in again** button; log in, land back on the dashboard, restore.
- Only the editable parts are stashed (display name, bio, location, settings, assets, links) — never badges, views or the username.
- `dashboard/index.html` (the bar), `js/v2.js` (`stash` / `readDraft` / `restoreDraft`, 401 branch in `save`), `css/v2.css` (`.draftbar`). Also: the top-bar Save button's label had a stray double space.

## v3.33 — the nav on phones (supersedes v3.32)
- **Login** stays in the bar on phones (it was two taps away, inside the menu); once signed in it reads Dashboard as before, and the phone bar drops the "Claim" button for members so it still fits (`auth.js` adds `is-signed-in` to `<html>`). Under 340px the link steps back into the menu.
- The menu scrolls on short screens instead of clipping, with smaller type under 640px tall.
- Tiny phones (≤360px): the tilted wall's captions could poke past the edge and give the whole page a sideways scroll — captions wrap and the wall clips horizontally.
- Validator: `autocapitalize` dropped from the two e-mail inputs (login, sign up) — browsers never autocapitalize e-mail fields anyway, and html-validate flagged it. Every template now validates clean.
- `css/v2.css`, `js/auth.js` (one line), `login/index.html`, `signup/index.html`.

## v3.32 — Look & effects, in groups (supersedes v3.31)
- The Look section was one long column of fifteen controls after the theme tiles. It's five labelled groups now — **Colours** (four pickers in a row), **Behind the card** (background image / video, cursor), **Effects** (username + background effect, entry screen, the four effect toggles), **What shows** (views, badges, links, list on explore), **The card** (the four sliders). Same fields, same `data-cfg` paths, nothing renamed.
- Sliders show their value (72%, 16px …). The two opacity sliders step by 0.01 instead of 0.05 — the gothic preset's 0.72 wasn't representable before, so the slider snapped to 0.70 while the saved value stayed 0.72.
- The theme tile of the theme you're on is pressed on load too (detected from the settings), and once you drift from it a **Back to <theme>** button appears under the tiles; it re-applies the preset (colours, corners, effects — never links or words).
- `dashboard/index.html`, `js/v2.js` (`themeOf`, `syncTheme`, `readout`), `css/v2.css` (`.look__*`).

## v3.31 — the pricing strip on phones (supersedes v3.30)
- Front page, under 640px: the three stacked plan cards were ~1,500px of scrolling. They're a swipe row now — scroll-snap, one card at a time with the next one peeking, Lifetime first (as the pricing page already does on phones), a hand-written "swipe for the other two →" under it. Cards keep every line they had; the section is 790px instead of 1,550px. Desktop and tablet unchanged. Keyboard users still reach every button (focus scrolls the row).
- Checked every claim on the strip against the pricing page — prices, "once", and all twelve bullet lines match (nothing was changed).
- `index/index.html` (one hint line), `css/v2.css`.

## v3.30 — the live preview on phones and tablets (supersedes v3.29)
- Under 1240px the dashboard's live-preview column was simply gone — on a tablet or phone you edited blind until you saved and opened the page. Now a **Preview** button in the top bar (eye icon only under 640px) opens the same phone as a full-screen sheet; it's the live one, so whatever you just typed is on it. Close with the ×, the backdrop, or Esc; focus moves into the sheet and back. Under 640px "Save changes" reads "Save" so the bar fits.
- Link rows between 821 and 1200px: the label and link inputs kept their ~200px intrinsic width and overlapped the next cells (a real overlap, not just tight). Fixed with `minmax(0,…)` columns and `min-width:0`; on that band the row is two lines — platform · label · link · arrows · × over text · on.
- `dashboard/index.html` (Preview button, sheet close button, Save label), `css/v2.css`, `js/v2.js` (`setPeek`).

## v3.29 — tap a page, see it land (supersedes v3.28)
- Front page wall: tapping an example page now scrolls the **hero phone** itself into the middle of the screen (it used to go to the hero's top edge, which on a phone left the preview below the fold) and pulses a ring around it once so the eye lands where the theme just changed. Off under reduced motion (instant jump, no pulse).
- Phone partial bug, everywhere it's used (hero, wall, explore, share card): the player's progress bar is a `<span>`, so its `height:3px` never applied — the bar was a 35px block, obvious as a solid pink slab on the light themes and a too-tall player row on all of them. `display:block` fixes it; `images/share.png` / `share@2x.png` re-rendered with the fix.
- `js/v2.js` (`showPhone`), `css/v2.css` (`.pf__bar`, `hit` pulse), `images/share*.png`.

## v3.28 — paste a link, the platform picks itself (supersedes v3.27)
- Dashboard → Links: typing or pasting a link into a row that still says **Custom URL** sets the platform from the host — youtube.com / youtu.be → YouTube, discord.gg → Discord, x.com / twitter.com → X, t.me → Telegram, open.spotify.com → Spotify, an e-mail address → Email, and so on for every platform in the list (subdomains match, look-alikes like `notyoutube.com` don't). A platform you picked by hand is never overridden; a row the auto-pick set follows the link if you paste a different one, and goes back to Custom URL for a host it doesn't know. The select flashes once so you see what changed (not under reduced motion). The auto state lives only in the page — nothing new is saved.
- `js/v2.js` (`guessPlatform`, `autoPlatform`), `css/v2.css` (`autopick` flash).

## v3.27 — the front page on phones (supersedes v3.26)
- Hero: the theme swatches and effect toggles are their own grid child (`.hero3__lab`) — on desktop nothing moves (copy over controls on the left, phone on the right, the pair centred against the phone); on phones the order is copy → phone → controls, so the switches sit right under the thing they change instead of above a phone that's off-screen. Controls are centred under the phone; the hero starts 36px higher under 640px.
- The steps strip (`#how`) is a bridge, not a section: `.section--bridge` gives it 40–64px above and below (it had 72–124px below, which read as a hole between the steps and the neighbourhood).
- Claim hint: when it wraps on a phone, the green dot sits on the first line instead of floating between two. CTA: "or come hang out first" takes its own line under 640px so the Discord and Telegram buttons stay together.
- No copy or product facts changed. `index/index.html`, `css/v2.css`, `js/v2.js` (unchanged JS, re-minified with the new asset version).

## v3.26 — first-run checklist (supersedes v3.25)
- Dashboard overview: a four-step strip for accounts whose page isn't live yet — **pick your name → say who you are → add a link → hit save**. Each step jumps to its section; the marks turn green as you type (name from `/me`, display name + bio, at least one enabled link with a value or label, saved with nothing pending). The save step is a real save button. The strip appears / goes away only on load and after a save, so it never flickers mid-edit, and it stays out of the way once all four are done.
- Pure front-end: `dashboard-main.html` (markup), `js/v2.js` (`checklist()`, `published`), `css/v2.css` (`.checklist*`). No API changes.

## v3.25 — the first two seconds (supersedes v3.24)
- The hero's poster was `images/mainbg.png` — 2.2 MB — so the first paint waited on it. New `images/mainbg-poster.jpg` (222 KB, progressive) sits behind the video as a `fetchpriority="high"` image and is the `poster` of every loop (hero, log in, the preview phone). The PNG stays for anything else that references it.
- Entrance: eyebrow → headline → lede → claim box → controls fade up in a 0.6 s stagger, the phone settles in from the right; off under reduced motion. A left-to-right darkening keeps the copy column clean over the artwork.
- The claim box's placeholder types example names (yourname, ren, peach, …) until you focus or type; off under reduced motion.

## v3.24 — front page pass (supersedes v3.23)
- "How it works" — three plain steps between the hero and the wall (claim your name · make it yours · post the link). No new facts, no numbers.
- Phones: the wall shows six of the twelve example pages under 640px with an "All twelve on explore" button (the mobile page is ~500px shorter); the steps stack.
- Desktop: the hero phone leans toward the cursor (fine pointer, no reduced motion) and settles back on leave.

## v3.23 — admin delete + share preview (supersedes v3.22)
- `DELETE /api/v1/admin/users/{id}` — delete an account outright (spam, impersonation; suspension stays the reversible option). Refuses your own id; deletes through the data API first, then runs the same cleanup as self-deletion (uploads, analytics, card, explore cache); writes `user.delete` to the audit log. Admin page → Manage → "Delete account" (type the name to confirm). Test added (37 pass).
- Dashboard overview: a closed "What your link looks like when it's posted" panel showing the page's own share card (`/<name>/card.png`), refreshed after every save.

## v3.22 — real pages on explore (supersedes v3.21)
- Opt-in discovery. Dashboard → Your page → **list on explore** (`settings.listed`); the explore page grows a "People who opted in" row above the examples (newest first, the page's own colours, badge, first three link labels, views), each card linking to the page. Hidden entirely when nobody has opted in. Off by default; suspended accounts never appear.
- `GET /api/v1/explore` (`app/api/v1/explore.py`) returns card fields only — never a full config — cached 60 s in Dragonfly and busted on any profile save. **Rust change:** `GET /v1/profiles?listed=true&limit=N` in `tools/prostgres_db` (`cargo check` passes) — rebuild that container. Test added (36 pass).

## v3.21 — live username check (supersedes v3.20)
- `GET /api/v1/auth/available?username=x` → `{available, reason: invalid | reserved | taken | null}` (30 per IP per minute; reserved list + data API; says nothing a signup attempt wouldn't).
- Every claim box (front pages, pricing, explore, 404) and the sign-up username field now say "misa.lol/name is free — claim it" / "is taken — try another" / "is reserved" as you type (350 ms debounce, only on misa.lol hosts — the hosted previews keep the plain hint). Tested on the real template (35 tests pass).

## v3.20 — passwords + caching (supersedes v3.19)
- `PATCH /api/v1/me/password` `{current_password?, new_password}` — change it, or set one on an account that signed up with Google / Discord / Telegram (then email login works too). Current password required when one exists; 8+ chars; 10 per user per hour. Dashboard → Account → "Change password" / "Set a password" panel. Tests added (34 pass).
- `build_site.py` minifies `css/v2.css` + `js/v2.js` (rcssmin / rjsmin — `pip install rcssmin rjsmin` on the build box; falls back to unminified) and links them with `?v=<content hash>`; a middleware in `app/main.py` sends `Cache-Control: public, max-age=31536000, immutable` for versioned static files and content-hashed uploads, `public, no-cache` (revalidate) for the rest. nginx already gzips css/js/svg/json.

## v3.19 — themes in the dashboard (supersedes v3.18)
- The six looks the front page and explore page sell (gothic, soft, mono, paper, sunset, y2k) are now one-click presets at the top of Look & effects — colours, corners, opacity/blur and effects only; links and words stay. Paid-only effects in a preset are set too: the server clears what the plan doesn't cover and the locked fields say why.
- The marketing → product loop closes: `/signup?theme=y2k` (from explore's "start from this theme") stashes the pick, and a fresh dashboard starts from it (unsaved, with a note); `/dashboard?theme=x` does the same.

## v3.18 — delete my account (supersedes v3.17)
- `DELETE /api/v1/me` `{confirm: "delete", password?}` — the password is required for accounts that have one (OAuth-only accounts just type the word). Order: the account is deleted through the data API first (profile, badges, grants and reports' user links cascade in Postgres); only then the uploads folder, the analytics keys and the cached card are dropped, and the session is destroyed. If the data API fails, nothing has been removed.
- **Rust change** (`tools/prostgres_db`): `DELETE /v1/users/{id}` → `db::delete_user` (204 / 404). `cargo check` passes; rebuild that container too: `docker compose build prostgres_db app01 app02 && docker compose up -d`.
- Dashboard → Account → a closed "† Delete my account" panel at the bottom: password (shown only for email accounts), type *delete*, a browser confirm, then home. Tests added (32 pass).

## v3.17 — one more (supersedes v3.16)
- **Fix:** the v3.14 report form was always visible — its `display:grid` beat the browser's default for the `hidden` attribute. The page now has a `[hidden]{display:none!important}` reset like the rest of the site. Test added (30 pass).

## v3.16 — public profile fixes (supersedes v3.15)
- **Fix:** the background image never applied — the inline style was `url("…")` inside a double-quoted attribute, so the browser cut it off at the first quote. Single quotes now (the URL validator already rejects quotes and spaces, so nothing can break out).
- **Fix:** a bio with a long unbroken word (or URL) stretched the card off-screen on phones: the card's grid track is now `minmax(0,1fr)` so text wraps inside it.
- Cursor URLs are written into the stylesheet without HTML-escaping (`&quot;` isn't valid CSS); the value is validated and stripped of quotes and angle brackets instead. Tests added (29 pass).

## v3.15 — hardening (supersedes v3.14)
- **Fix:** a suspended account's public page and share card still rendered (login and sessions were checked, the page wasn't). Both are 404 now while the suspension lasts. Test added.
- Rate limits on the new public / heavy endpoints, with the existing limiter: uploads 60 per user per hour, click beacons 120 per IP per minute, share-card renders 60 per IP per minute. 28 tests pass.

## v3.14 — "report this page" (supersedes v3.13)
- The `reports` table the admin page reviews had no way in. Public pages now carry a small **report** link in the footer that opens an inline form (reason from a fixed list, optional details); `POST /api/v1/reports` (`app/api/v1/reports.py`) stores it with the reporter's id when they're signed in. Five per visitor per hour (the existing rate limiter); an unknown name gets the same "thanks" as a real one; 422 for made-up reasons. `admin_db.add_report` added. Test added (27 pass).

## v3.13 — the admin page (supersedes v3.12)
- The Next `dashboard-ui/` (which had the admin view) isn't deployed, so there was no way to grant Lifetime / Supporter or give a badge. `/admin` now exists in the same design system, on top of the admin API that was already there (`app/api/v1/admin.py`, untouched): users (search, manage → grant a plan with optional expiry, give / hide a badge, suspend with a reason / lift), entitlements list, badges (create, list), reserved usernames (add, release), reports (status), feature flags (toggle), audit log (latest 100). Every action writes to the audit log via the existing endpoints.
- Access: `/admin` is a private page (login required) and returns the designed 404 for anyone who isn't `is_admin` or in `MISA_ADMIN_USER_IDS`; the page's own JS also checks `/me`. Test added (26 pass).
- Template: `app/templates/pages/admin/index.html`; `admin` was already a reserved username.

## v3.12 — review pass (supersedes v3.11)
- Click table capped at 64 ids per page (random ids from a beacon spammer can no longer grow it); test added (25 pass).
- Re-verified the auth.js contract across signup / login / dashboard (field names, Turnstile box, provider buttons, `#auth-message`, `#username-form`, `#logout-btn`, `#nav-*`) and that nginx only fronts the FastAPI app (the Next `dashboard-ui/` folder is not deployed — the new `/dashboard` is the real one).

## v3.11 — tests (supersedes v3.10)
- `tests/` — 24 pytest cases that boot the real FastAPI app with every external service stubbed (no Postgres, no data API; Dragonfly is `fakeredis`): site pages + redirects + the designed 404 + sitemap, the public profile page (escaping, server-owned views, click beacons, og:image) and its card, `PUT /profile/me` (wire shape, server-side badges, plan gating per plan, admin-DB-down behaviour, badge toggles, `/me`), uploads (plan gate, sniffing, cursor rules, traversal), analytics (dedupe, bots, referrers, clicks, Dragonfly down) and the gating table.
- `requirements-dev.txt` + `pytest.ini`. Run: `pip install -r requirements-dev.txt && python -m pytest` — under a second.

## v3.10 — honest analytics (supersedes v3.9)
- Until now `profile.views` was whatever the dashboard sent — anyone could type 12,412. Views are now counted on the server (`app/core/analytics.py`, Dragonfly): one per visitor (salted hash of address + user agent) per 30 minutes, crawlers and link-preview bots skipped, referrer host recorded (own domain excluded, table capped at 64 hosts), daily buckets kept 100 days. The public page shows the server's number; `PUT /profile/me` overwrites whatever `views` the client sent.
- Link clicks: public pages send `navigator.sendBeacon('/api/v1/hit/<name>/<social id>')` on click (never blocks the navigation); `POST /api/v1/hit/{username}/{social_id}` is public, answers 204 whatever happens, and never reveals whether a name exists.
- `GET /api/v1/me/stats` → `{views, today, week, daily: [[date, n] × 14], referrers: [[host, n]], clicks: [[id, label, n]]}` (labels joined from the current links). Degrades to zeros with `unavailable: true` if Dragonfly is down.
- Dashboard overview: the views tile reads "N today · M this week", plus a block with a 14-day bar chart, top referrers and top links. Settings: `MISA_ANALYTICS_SALT` (optional; falls back to the data-API key) salts the visitor hash.
- Tested with a fake Redis: three refreshes from one visitor = 1 view, a second visitor = 2, a Discordbot UA = not counted, referrers `t.co` / `discord.com` recorded, clicks labelled, a save with `views: 999999` comes back as 2.

## v3.9 — uploads (supersedes v3.8)
- `POST /api/v1/uploads` (multipart `file` + `kind` = avatar | background | video | audio | cursor), `GET /api/v1/uploads`, `DELETE /api/v1/uploads/{name}` — `app/api/v1/uploads.py`. Hosting is a Lifetime / Supporter perk on the pricing table, so free accounts get a 403 that says so and keep pasting links; cursors need Supporter. Types are sniffed from the bytes (PNG / JPEG / WebP / GIF, MP4 / WebM, MP3 / OGG / WAV / M4A), images are opened with Pillow (≤ 40 MP; cursors ≤ 128 px PNG), caps 8 / 32 / 12 MB / 256 KB, 200 MB per user in total. Files are named by content hash under `<upload_dir>/<user_id>/` and served at `/u/<user_id>/<name>`.
- `docker-compose.yml`: a shared `uploads` volume mounted at `/data/uploads` in app01 **and** app02 (both instances must see the same files); `MISA_UPLOAD_DIR` overrides the path. `nginx/nginx.conf`: `client_max_body_size` 16m → 40m for the video cap. `python-multipart` added to requirements.
- Dashboard: an upload button inside each file field (avatar, background image, background video, audio, cursor) — locked below the plan with a tooltip, spinner while uploading, the URL lands in the field, the live phone and the save bar react. Tested: free → 403, lifetime avatar → 201 and served, an .exe renamed .png → 400, cursor on lifetime → 403, 300 px cursor → 400, mp3 / mp4 → 201, list + delete, path traversal on delete and on `/u/` → 404.

## v3.8 — per-profile share cards (supersedes v3.7)
- `GET /<username>/card.png` — a 1200×630 card for that page, drawn server-side with Pillow (`app/share_card.py`): the page's accent colour as the glow, the initial on an accent disc, display name + badge, handle, bio (Playfair italic, wrapped to three lines), the † and "be weird online again." Nothing is fetched at render time (remote avatars are untrusted); unsupported glyphs are dropped rather than drawn as boxes; ~90 KB, ~300 ms cold, cached 5 minutes in memory (500 entries) and `Cache-Control: public, max-age=300`; the cache is dropped when the profile is saved. Unknown or invalid names → 404.
- Profile pages now carry full Open Graph + Twitter meta pointing at their card, so a misa.lol/name link previews as that person's page on Discord, X, iMessage, Telegram.
- New: `Pillow` + `fonttools` in `requirements.txt`; `app/assets/fonts/` ships Inter 500/600/800, Playfair Display italic and Caveat 600 as TTF (SIL OFL, licences beside them). The Dockerfile already copies `app/`.
- Smoke-tested: `/ren/card.png` 200 image/png (same bytes on the second hit), `/nobody/card.png` 404, `/pricing/card.png` 404, `/ren` carries `og:image` → its card.

## v3.7 — routing + sitemap (supersedes v3.6)
- `app/main.py`: site pages are served before the username lookup (their slugs are reserved anyway), so `/pricing`, `/explore` etc. no longer cost a data-API round trip per view; profile pages get `Cache-Control: no-store`; unknown paths raise the designed 404.
- `GET /sitemap.xml` (robots.txt already pointed at it): the seven public pages, cached an hour. Profile pages aren't listed — that would be a user scan on every crawl.
- Smoke-tested with FastAPI's TestClient and stubbed backends: `/`, `/pricing`, `/explore`, `/login`, `/dashboard` (302 for guests), `/sitemap.xml`, `/robots.txt`, `/images/share.png`, a missing page (designed 404), and `/ren` with a stubbed profile (rendered, escaped, badge + link present, title `ren · misa.lol`).

## v3.6 — share card (supersedes v3.5)
- `app/templates/images/share.png` (1200×630, + `share@2x.png`): the real share card — headline, one line, the gothic phone — rendered from the design system by `gen_share.py`. Every page's `og:image` / `twitter:image` now points at `/images/share.png` with width/height meta. Regenerate after a brand change; per-profile cards (misa.lol/<name> with that page's look) would need a renderer on the server — noted, not built.

## v3.5 — plans, badges, link order (supersedes v3.4)
- **Fix (contract):** the v3.1 dashboard sent `{profile: <config>}` to `PUT /api/v1/profile/me`; the API (and the old Next dashboard) use the bare `ProfileConfig` as the body. Saves would have failed with "Profile username does not match". Now correct.
- **Security:** `badges` in a saved profile were whatever the client sent, so anyone could give themselves a Verified badge on their public page. `PUT /api/v1/profile/me` now rebuilds `badges` from `user_badges` (the admin-granted table), keeping only the user's show/hide choice for badges they own. If the admin database is unreachable it keeps the previously stored list instead of stripping it.
- **Plan gating:** `app/core/plans.py` — paid-only cosmetics are cleared server-side on save when the plan doesn't cover them (video background, animated background, username effects and entry screen need Lifetime; cursor and the gold halo need Supporter — straight from the pricing compare table; edit `GATES` to change it). The reply carries `cleared: [paths]` so the dashboard can say so. Plan = best active, unexpired row in `premium_entitlements` (`supporter` > `lifetime` > anything else counts as lifetime-level).
- `GET /api/v1/me` now includes `plan`, `plan_expires_at` and `badges` (owned, with `enabled`); new `PATCH /api/v1/me/badges/{id}` `{enabled}` to show/hide an owned badge. Both degrade (free / none / 503) if the admin database is down.
- Dashboard: the plan box shows the real plan (Free → "See upgrades", Lifetime → "Get Supporter", Supporter → nothing to sell); paid-only fields lock below their plan with an "— unlock" link; a Badges list under Links with show/hide toggles; links can be reordered with arrows; the live phone shows the badge (gold on Supporter).

## v3.4 — mobile pass (supersedes v3.2)
- Tap targets on small screens: footer links, auth-page inline links (log in / claim one / forgot it? / terms), explore card links, the compare table's plan links, checkboxes and the dashboard's per-link "text" checkbox all get ≥ 32px hit areas under 640px; the password eye is wider on touch devices.
- Label sizes on phones: plan picks, "not a subscription", gold tags, tier chips and filmstrip captions go from 10.5px to 11px under 640px.
- Copy reviewed page by page; no product facts changed. The TODOs that only you can close: Discord + Telegram invite links (currently `#` in the CTA, footer and maintenance page), the checkout the plan buttons should point at (they go to `/signup?plan=` for now), the "7 more free features" the old page promised, and the 200K+ / 40M+ numbers carried over from the old front page.

## Notes
- Every page still loads fonts from Google Fonts; nothing else external except Turnstile on the auth pages.
- Claim boxes on every page go to `/signup?username=<name>`; the sign up page prefills it and the API claims it at signup. `?plan=lifetime|supporter` from the pricing page is carried as a hidden field (the API ignores it for now).
- Dashboard follow-ups: real file uploads (avatar / background / audio / cursor), plan + billing state (the plan box is hard-coded to Free until the API exposes the plan), badge management, link reordering.

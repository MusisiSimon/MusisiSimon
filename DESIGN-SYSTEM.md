# Design System — Intellora Tech

Everything lives in `assets/styles.css`, organised in numbered sections. Change tokens at the top; components inherit.

---

## 1. Palette

The identity was evolved rather than replaced, as the brief required.

| Token | Value | Use |
|---|---|---|
| `--paper` | `#F5F3EE` | Page background |
| `--paper-2` | `#FFFFFF` | Cards, raised surfaces |
| `--paper-3` | `#EBE8E0` | Alternating section bands, table headers |
| `--ink` | `#0D1B2A` | Dark sections, footer, logo mark |
| `--brand` | `#12574E` | Primary actions, links, emphasis |
| `--signal` | `#CBEF4A` | Accent. Used sparingly — roughly a dozen places total |
| `--copper` | `#C1653A` | Warnings, placeholders, "before" states only |

### Pillar accents — wayfinding only

Six muted accents identify which capability you are inside. They appear as a 4px left spine on pillar cards, a top border on capability sections, and in the badge. **They are never decoration.**

| Pillar | Token | Value |
|---|---|---|
| Analytics | `--p-analytics` | `#12574E` |
| Governance | `--p-governance` | `#5C4A8A` |
| Security | `--p-security` | `#9C3B3F` |
| AI & ML | `--p-ai` | `#1F6486` |
| Database | `--p-database` | `#9A6B1C` |
| Cloud | `--p-cloud` | `#2F6B45` |

Apply with `data-p="ai"` on any ancestor. Descendants read `var(--pc)`.

```html
<article class="pil" data-p="security">…</article>
<section data-p="cloud" style="border-top:4px solid var(--pc)">…</section>
```

### Dark mode

Built on the same token names, overridden in two places: a `prefers-color-scheme` block and a `[data-theme="dark"]` attribute set by the toggle and stored in `localStorage`. Pillar accents lighten so they hold contrast on dark backgrounds. **Never hard-code a hex value in a component** — it will break dark mode silently.

---

## 2. Typography

| Family | Role |
|---|---|
| Fraunces | `h1`–`h4`, statistic values, price figures |
| Instrument Sans | Body, buttons, labels |
| IBM Plex Mono | Metadata, eyebrows, dates, tags, technical labels |

Scale is a 1.25 major third from `--t-xs` (12px) to `--t-3xl` (fluid, up to 60px). Body copy is capped at `--max-txt` (68ch).

### Restraint rules applied

Three corrections were made against the previous site, following the frontend-design guidance on generated-page tells:

- Eyebrows appear on **section openers only**, never above every heading.
- Reveal animation is **one orchestrated moment per section**, not a fade-up on every card.
- Arrows (`→`) appear on **primary CTAs only**, never on inline links.

Keep these. They are the difference between "engineering practice" and "designer portfolio", which matters for this audience.

---

## 3. Spacing and layout

4px base scale, `--s1` through `--s9`. `--s9` is fluid and used for section padding. `--gut` is the responsive page gutter, `--max` is 1200px.

Never use raw pixel margins in a component — use the scale so vertical rhythm holds.

---

## 4. Components

| Class | Purpose |
|---|---|
| `.wrap` | Max-width container with gutter |
| `.sec` / `.sec-tight` | Standard / reduced section padding |
| `.sec-alt` / `.sec-3` / `.sec-ink` | Background variants. `.sec-ink` recolours headings and leads automatically |
| `.hd` | Section header block, capped at 760px |
| `.g` + `.g2`/`.g3`/`.g4` | Responsive grids |
| `.g-rule` + `.c2`/`.c3`/`.c4` | Hairline-ruled grid; children read as one table rather than floating tiles |
| `.card` | Standard bordered card |
| `.pil` | Pillar card with coloured spine. Requires `data-p` |
| `.pbadge` / `.pbanner` | Pillar page badge and top border |
| `.chip` / `.chips` | Tags, technology lists, tier three sectors |
| `.tier` + `.t1`/`.t2`/`.t3` | Sector tiers. Tag colour encodes depth |
| `.tw` + `table.t` | Scrollable table, sticky first column, `.us` marks your column |
| `.faq` + `<details>` | Accordion. Native element, works without JavaScript |
| `.note` | Copper-bordered caveat block |
| `.ph-slot` | Dashed placeholder. **Every one must be filled or removed before launch** |
| `.cred` / `.cred-i` | Credential rows with status pills |
| `.opt` | Selectable option button. Uses `aria-pressed` |
| `.scta` | Sticky bottom CTA |
| `.rv` | Scroll reveal |

### Status pills

`.st-cur` (current, teal), `.st-perm` (no expiry, grey), `.st-trn` (training, amber). Also used for technology proficiency: primary / working / familiar.

---

## 5. Component states

Every interactive element defines default, hover, focus-visible and disabled. Focus is a 2px `--brand` outline at 3px offset — **never remove it**. Selected state uses `aria-pressed="true"`, not a class, so assistive technology hears it.

---

## 6. Motion

Standard easing `--e: cubic-bezier(.2,.7,.3,1)`, duration `--d: .24s`. Nothing exceeds 400ms except the hero pipeline loop (9s) and the orbit rotation (54s / 84s), which are ambient.

`prefers-reduced-motion: reduce` disables all animation globally and freezes the hero graphic on its resolved end state, so the message survives without movement.

---

## 7. Accessibility baseline

- Skip link on every page.
- One `h1` per page; heading order never skips a level.
- Semantic landmarks: `nav`, `main`, `header`, `footer`, `section`.
- Every decorative SVG carries `aria-hidden="true"`; every meaningful graphic has a descriptive `aria-label`.
- The hero graphic's `aria-label` describes the whole diagram and states that its figures are illustrative.
- Tables have a caption (visually hidden) and `scope` on all headers.
- Colour never carries meaning alone — tiers, proficiency and status all carry text.

---

## 8. Adding a page

Copy any existing spoke page and replace: `<title>`, description, canonical, Open Graph tags, breadcrumb, `aria-current` in the nav, and the JSON-LD block. Asset paths are `assets/` from root and `../assets/` from a subdirectory.

To add a pillar: add a `--p-{name}` token, add the `[data-p="{name}"]` selector next to the others, then use `data-p` on the section and its cards.

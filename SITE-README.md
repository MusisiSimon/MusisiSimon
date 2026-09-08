# Intellora Tech — Website

A seven-page static site covering six engineering capabilities, targeted globally. No frameworks, no build step, no dependencies beyond Google Fonts. Open `index.html` in a browser and it works.

---

## File map

```
/
├── index.html                              Home
├── capabilities/
│   ├── index.html                          Hub — all six pillars + technology universe
│   ├── ai-machine-learning.html            Full spoke page
│   └── aws-cloud-architecture.html         Full spoke page
├── industries/index.html                   Three-tier sector taxonomy + buyer personas
├── about/index.html                        Credentials, delivery model, conflict disclosure
├── contact/index.html                      Scoping call, engagement lifecycle
├── assets/
│   ├── styles.css                          All styling, tokenised
│   ├── main.js                             All behaviour, progressive enhancement
│   └── img/                                Portrait, WebP + JPEG at 360 and 720px
├── DESIGN-SYSTEM.md
├── EVIDENCE-REGISTER.md                    ← read this before publishing
└── README.md
```

---

## ⚠️ Read before publishing

Three items in `EVIDENCE-REGISTER.md` are marked **Action required**. Briefly:

1. **The principal is unresolved.** The brief supplied Anita Tashobya's LinkedIn, named Musisi Simon Peter as partner, and attached certificates belonging only to Simon. Decide who is principal and who is partner before launch.
2. **The employment conflict needs legal clearance.** The site markets revenue-administration services while the principal is employed by a revenue authority. Get a Ugandan lawyer's view and speak to your employer's HR before the site is indexed.
3. **Every `.ph-slot` must be filled or removed.** They are visibly marked and will look deliberate to a visitor, but they are not a launch state.

---

## Hosting options

All four are free at this scale, support custom domains with automatic HTTPS, and need no build step. Ranked for this specific site.

### 1. Cloudflare Pages — recommended

The fastest global network, which matters when your visitors are in seven regions and you are serving from one origin.

1. Create a free account at `cloudflare.com`.
2. **Workers & Pages → Create → Pages → Upload assets**.
3. Drag the whole folder in. Project name: `intellora-tech`.
4. **Custom domains** → add `intelloratech.com`. If you also register the domain with Cloudflare, DNS configures itself.

Why this one: unlimited bandwidth on the free tier, ~300 edge locations including Africa and the Gulf, and Cloudflare Registrar sells domains at wholesale cost with no upsells. It is also the natural home if you later add a serverless function for a contact form.

### 2. Netlify

Simplest possible deploy. Go to `app.netlify.com/drop` and drag the folder onto the page — it publishes immediately to a `*.netlify.app` URL. Add your domain under **Site settings → Domain management**.

Best if you want it live in ninety seconds. Free tier caps bandwidth at 100GB/month, far above what this site will use.

### 3. GitHub Pages

Best if you want version history from day one, which is worth having for a site with legally sensitive disclosure text.

1. Create a public repository, e.g. `intellora-site`.
2. Upload all files preserving the folder structure.
3. **Settings → Pages** → source `main`, folder `/ (root)`.
4. Add a `CNAME` file containing `intelloratech.com`.

Slower to propagate changes and no edge network as broad as Cloudflare's, but the free custom-domain support is solid.

### 4. Vercel

Comparable to Netlify. Import from Git or drag-and-drop, framework preset **Other**. Strongest if you later move to a framework, but that is not planned here.

### Domain registration

Register `intelloratech.com` **and** `intelloratech.io` on the same day — squatters watch new LinkedIn and company-name activity.

| Registrar | Note |
|---|---|
| Cloudflare Registrar | At-cost pricing, no upsells, no first-year discount that triples on renewal. Best choice. |
| Porkbun | Cheap, reliable, good interface. |
| Namecheap | Fine, but check renewal pricing. |

Avoid registrars that bundle "privacy protection" as a paid add-on — WHOIS privacy should be free.

### After deploying

- Submit to Google Search Console and Bing Webmaster Tools.
- Add a `robots.txt` and `sitemap.xml` (seven URLs — write it by hand in five minutes).
- **Do not index the site until the conflict-of-interest wording has been legally cleared.** If you deploy early, add `<meta name="robots" content="noindex">` to every page in the interim.

---

## Placeholders to replace

| File | Placeholder | Replace with |
|---|---|---|
| All | `hello@intelloratech.com` | Real monitored address |
| All footers | "Registration pending" | URSB number |
| `about/` | Second principal slot | Name, role, background |
| `contact/` | Booking link slot | Calendly / Cal.com URL |
| `contact/` | LinkedIn slot | Company page + correct personal profile |
| `index.html` | Testimonial, case study, logos | Real attributed content only |
| `index.html` | Insurance card | PI cover and any ISO/SOC 2 alignment, or delete the card |
| `capabilities/*.html` | Case study slots | Delivered engagements |

---

## Changing prices

All pricing lives in one place: `assets/main.js`, the `BASE`, `PILLAR` and `M` objects near the top of the estimator block.

```js
var BASE = {
  assess:   { p: 4200,  w: 3,  l: '…' },   // p = USD base, w = base weeks
  optimise: { p: 6800,  w: 4,  l: '…' },
  build:    { p: 15000, w: 9,  l: '…' },
  migrate:  { p: 20000, w: 12, l: '…' }
};
```

Displayed range is −16% / +18% around the computed midpoint. Currency conversion rates are in the `CUR` object — **these are static and will drift.** Either update them periodically or switch the selector to display-only labels.

### The capacity cap — do not remove

Above a computed midpoint of **USD 58,000**, the result panel shows an additional note explaining that a programme that size is phased or partnered rather than quoted as one contract.

At the top of the input range the model returns figures approaching USD 230,000. A senior-led practice cannot deliver that as a single engagement, and quoting it would invite an enquiry you have to walk back — the most expensive possible moment to lose credibility. That threshold is the one number tied to delivery capacity rather than the rate card. Raise it only when capacity genuinely rises.

---

## Adding content

**A new capability spoke:** copy `capabilities/ai-machine-learning.html`, change the `data-p` on `<body>`, the badge, title, meta, canonical, breadcrumb and JSON-LD. Link it from the hub and both footers.

**A new sector:** decide the tier honestly first. Tier 1 requires production history — not adjacent experience, not a similar project. If in doubt it is Tier 2.

**A new region:** add a row to the timezone table in `index.html#reach` and a card to the four-card grid below it.

**An insights section:** not built, since an empty blog is worse than none. Add `/insights/` once three articles exist.

---

## Technical notes

- **Progressive enhancement.** Every page is readable and navigable with JavaScript disabled. The estimator and maturity check show `<noscript>` fallbacks with indicative starting prices.
- **Theme.** Respects `prefers-color-scheme`; the toggle overrides and persists to `localStorage`.
- **Accessibility.** Skip links, one `h1` per page, visible focus, `aria-pressed` on toggles, descriptive labels on both graphics, sticky table headers with `scope`.
- **Reduced motion.** All animation disabled; the hero graphic freezes on its resolved state.
- **Performance.** Two external requests (fonts and CSS) plus one deferred script. The only images are the portrait, served as WebP with a JPEG fallback, lazy-loaded, with explicit dimensions to prevent layout shift. Should score 95+ on Lighthouse across all four categories.
- **Fonts.** Loaded from Google Fonts with `display=swap`. To eliminate the third-party request, self-host the three families in `assets/fonts/` and swap the `<link>` for `@font-face` rules.

---

## What was deliberately not built

- **Insights/blog system** — an empty blog is worse than none.
- **Contact form** — `mailto:` needs no backend. Add Formspree or a Cloudflare Pages Function when you want one.
- **Regional and persona sub-pages** — the structures exist on the home and industries pages. Split them out when there is enough regional content to justify separate URLs.
- **Localisation** — `hreflang` scaffolding was omitted rather than stubbed, because a language switcher pointing at pages that do not exist is worse than no switcher. Add it when translations are commissioned.
- **Client logo marquee** — not until real logos with written permission exist.

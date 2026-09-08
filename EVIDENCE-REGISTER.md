# Evidence Register — Intellora Tech website

Required by section 8 of the brief. Every substantive claim on the site is listed with its status.

**Status meanings**
- **Verified** — evidenced by a document supplied, or a structural fact about the site or the practice's own policy.
- **Needs evidence** — plausible and probably true, but nothing supplied to support it. Confirm before launch.
- **Placeholder** — a component exists with visibly marked placeholder content. Must be filled or removed before launch.
- **Action required** — carries legal, employment or reputational risk. Resolve before the site is indexed.

---

## 1. Credentials — all Verified

Extracted directly from the eight PDFs in `Certs.zip`. All are in the name **Simon Peter Musisi Ntege** (name order varies by issuer).

| Claim on site | Status | Evidence |
|---|---|---|
| AWS Certified Solutions Architect – Associate, issued Oct 2024, valid to Oct 2027 | Verified | Certificate; validation number `df0efd1a285c44eaa06f2415817edd46` |
| ITIL 4 Foundation, IT Service Management, Jul 2022, no expiry | Verified | PeopleCert certificate `GR671415551SM` |
| COBIT 5 Foundation, Apr 2020, no expiry | Verified | PeopleCert / ISACA certificate `GR692009471SM` |
| PRINCE2 Foundation, Project Management, Jan 2020, no expiry | Verified | PeopleCert certificate `GR656131015SM` |
| EXIN Agile Scrum Master, Jun 2020 | Verified | EXIN certificate `6336083.20793133` |
| Oracle Data Integrator 12c — listed as **training**, 40 hours, Dec 2024 | Verified | Oracle University completion certificate, event 236924 |
| Data Scientist Masters Program — listed as **training**, Jan 2019 | Verified | Simplilearn certificate, graduated summa cum laude |

### Deliberately excluded

| Item | Reason |
|---|---|
| PRINCE2 Practitioner (`GR657061784SM`) | **Expired 23 January 2023.** Listing a lapsed certification without marking it is the kind of small overstatement that destroys credibility when checked. It is noted in the About page prose as previously held. Renew it or leave it off. |
| "Oracle certified" phrasing anywhere | The ODI document is an Oracle University *training completion*, not an Oracle certification. The site says "training programmes completed" and keeps it in a separate block. Do not merge these two lists. |

---

## 2. Experience claims

| Claim | Status | Note |
|---|---|---|
| ~10 years production data engineering | Needs evidence | Consistent across prior briefs; no CV supplied with this build. Confirm the exact figure. |
| Core banking experience | Needs evidence | Stated in prior briefs (GTBank, FINCA Uganda). No employer is named on the site — correct, since permission has not been confirmed. |
| United Nations / WFP humanitarian operations | Needs evidence | Stated in prior briefs (2018–2021). Site refers to "United Nations country programmes" without naming WFP. Confirm you may name it. |
| National revenue administration experience | Needs evidence | Basis of the conflict-of-interest disclosure. Employer deliberately unnamed. |
| MBA, Uganda Management Institute | Needs evidence | No certificate supplied. |
| BSc Computer Engineering, Makerere University | Needs evidence | No certificate supplied. |
| Technology proficiency grades (primary / working / familiar) | Needs evidence | Self-assessed. Review each line yourself before launch — you will be asked about them on calls. |

---

## 3. Numeric and pricing claims

| Claim | Status | Note |
|---|---|---|
| Hero graphic: 12 min freshness, 99.6% reliability, 1 agreed metric | Verified as labelled | Panel header reads "representative engagement"; the `aria-label` states the figures are illustrative and not a client result. **Do not relabel these as achieved outcomes.** |
| Estimator base prices and multipliers | Verified as policy | Your own rate card. Located in `assets/main.js` under `BASE`, `PILLAR` and `M`. |
| AI readiness $6,000–8,400; AI production from ~$15,000 | Verified | Cross-checked against the estimator model. |
| Comparison table: $18,000–35,000 for a three-month build | Verified | Matches estimator output for a medium-scope build. |
| Comparison table: agency $45,000–90,000, freelancer $12,000–30,000 | Needs evidence | Market-rate estimates, not sourced. Defensible as ranges but be ready to say they are indicative. |
| Statistics band: 10+ years, 6 pillars, 3 sectors, 100% fixed-price | Verified / Needs evidence | Pillars and pricing policy are structural facts. Years and sectors depend on section 2 above. |
| **No AWS savings percentage anywhere** | Verified by removal | The previous site claimed "25–45% typical AWS spend reduction" with no delivered engagement behind it. The cloud page now explains why no headline percentage is published. **Do not reinstate this without a real engagement.** |

---

## 3b. Imagery

| Item | Status | Note |
|---|---|---|
| Portrait of Musisi Ntege Simon Peter | Verified | Supplied by the client 7 Sep 2026. Served as WebP with JPEG fallback at 360px and 720px, with descriptive alt text. Appears on `about/` and `contact/`. |

---

## 4. Placeholders — must be filled or removed

| Location | What belongs there |
|---|---|
| `about/` — second principal | Name, role, background. See section 5 below. |
| `contact/` — booking link | Calendly or Cal.com URL. Removes an email round-trip. |
| `contact/` — LinkedIn | Company page plus the correct personal profile. See section 5. |
| `index.html` — testimonial | Two to three sentences, attributed with name, role and organisation. |
| `index.html` — case study | Context, problem, constraints, approach, architecture, outcome, technologies, duration. |
| `index.html` — client logos | Only with written permission. |
| `index.html` — insurance and certification card | Professional indemnity cover and any ISO or SOC 2 alignment, stated accurately or removed. |
| `capabilities/ai-machine-learning.html` — case study | A delivered ML engagement. |
| `capabilities/aws-cloud-architecture.html` — case study | A delivered cloud engagement with measured savings. |
| Footer, all pages — "Registration pending" | URSB registration number once obtained. |
| All pages — `hello@intelloratech.com` | Confirm this address exists and is monitored. |

---

## 5. Action required — resolve before launch

### 5.1 Identity of the principal is unresolved

The brief supplied **Anita Tashobya's LinkedIn profile** as the site's LinkedIn, listed **Musisi Simon Peter under "partner or consortium arrangements"**, and attached eight certificates all belonging to **Simon Peter Musisi Ntege**.

These three inputs are mutually inconsistent and I have not guessed between them. The About page names Simon as principal because that is the only person with supplied evidence, and carries a visible note plus a placeholder for the second person.

Before launch, decide and state plainly: who is the principal, who is the partner, and whose LinkedIn appears. If this is a two-person practice, say so — it honestly doubles apparent capacity and strengthens the offer.

### 5.2 Employment conflict of interest

The principal is employed by a national revenue authority. The site markets revenue and tax administration services as a Tier 1 sector.

The `about/#conflicts` section states the position in full and lists the specific controls. It also carries a visible action note. That note is not decoration:

- Confirm the disclosure wording with a **qualified Ugandan lawyer**.
- Hold the conversation with your employer's **HR or legal function** before the site is indexed.
- A public commercial website marketing revenue-administration services is materially different from private consulting work, and the Leadership Code Act obligations attach to the public-facing version far more clearly.

Per the brief, no existing exclusion was silently removed. The narrowed position ("step back from procurements where a declarable conflict exists") was already present in the supplied `firm.html`; it has been retained and made more explicit rather than diluted further.

### 5.3 Business name

"Intellora Tech" appears to carry no obvious trademark conflict, unlike the previous name. Still run a URSB register search and a EUIPO TMview check in classes 9, 35 and 42 before registering.

---

## 6. What was removed from the previous site

| Removed | Reason |
|---|---|
| "25–45% typical AWS spend reduction" | No delivered cost engagement to support it. |
| "Around 70% of new clients start with an Audit" | Invented operational statistic; no client base to derive it from. |
| Four "recent project examples" with prices | Read as delivered engagements. Replaced with placeholder case-study slots. |
| Undifferentiated 38-industry chip list | Replaced with the three-tier taxonomy required by section 3.3. |

---

## 7. Prioritised list — what most improves conversion

Ordered by expected impact per unit of effort. The first four are worth more than any further design work.

1. ~~Photograph of the principal.~~ **Done.** Portrait supplied and placed on the About page and the Contact page.
2. **Two attributed testimonials.** LinkedIn recommendations from former colleagues are acceptable if labelled as such.
3. **One real case study.** Problem, approach, result. Worth more than the remaining placeholder slots combined.
4. **Booking link.** Every email round-trip loses a meaningful share of interested visitors.
5. **Resolve the principal question** (5.1). Ambiguity about who runs the firm is fatal at enterprise procurement.
6. **Legal clearance on the conflict disclosure** (5.2). Not a conversion item — a prerequisite for publishing at all.
7. **Company registration number.** "Registration pending" is honest but weakens enterprise credibility.
8. **Professional indemnity insurance.** Frequently a hard requirement in enterprise and donor procurement.
9. **First technical article.** Compounds slowly; start once the four items above are done.
10. **Named partner arrangement.** Converts the capacity ceiling from a weakness into a governance answer.

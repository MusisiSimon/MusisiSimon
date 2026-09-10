#!/usr/bin/env python3
"""
Intellora Tech — static page generator.

Writes every page of the site from one shared layout so the header, footer and
metadata stay identical across pages. The output is plain HTML with no runtime
dependency: deploy the generated files directly (Cloudflare Pages, any static
host). Run `python3 build.py` after editing content here.
"""

import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://intelloratech.net"
EMAIL = "hello@intelloratech.net"

# Logo — a lineage graph: scattered sources converge through one governed
# transform into a single served truth. The shape data engineers draw on
# whiteboards every week, and the shape of what the practice sells.
LOGO_PATHS = (
    '<path d="M8 8.5 L17 16 M8 23.5 L17 16 M17 16 L24.5 16" stroke="{fg}" '
    'stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity=".85"/>'
    '<circle cx="8" cy="8.5" r="2.5" fill="{fg}"/>'
    '<circle cx="8" cy="23.5" r="2.5" fill="{fg}"/>'
    '<circle cx="17" cy="16" r="2.1" fill="{fg}"/>'
    '<circle cx="25" cy="16" r="3.3" fill="{accent}"/>'
)

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='7' fill='%230E6E5E'/%3E"
    + LOGO_PATHS.format(fg="%23FBF9F5", accent="%23F0C05A").replace('"', "'").replace("<", "%3C").replace(">", "%3E")
    + "%3C/svg%3E"
)

FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Plus+Jakarta+Sans:wght@400;500;600;700&"
    "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&"
    "family=JetBrains+Mono:wght@400;500&display=swap"
)

MARK = (
    '<span class="brand-mark" aria-hidden="true">'
    '<svg width="17" height="17" viewBox="0 0 32 32">'
    + LOGO_PATHS.format(fg="#FBF9F5", accent="#F0C05A") +
    '</svg></span>'
)

NAV = [
    ("Products", "/products/"),
    ("Projects", "/projects/"),
    ("Tools", "/tools/"),
    ("Blog", "/blog/"),
    ("About", "/about/"),
    ("Payments", "/payment/"),
]

# What a 60-minute technical consultation costs, and the free intro that
# precedes it. Senior data-architecture consulting sits at roughly
# USD 150-350 an hour; 250 is mid-range and credited back on signing.
CONSULT_FEE = 250
INTRO_MINS = 15

PRODUCTS = [
    ("analytics-bi", "Analytics &amp; BI", "emerald",
     "Numbers your board can act on without arguing about them first."),
    ("data-governance", "Data Governance", "indigo",
     "Evidence you can produce in minutes, not weeks."),
    ("security", "Security &amp; Data Protection", "deep",
     "Security designed into the platform, not bolted on after the finding."),
    ("ai-machine-learning", "AI &amp; Machine Learning", "plum",
     "Models that reach production, on data you can defend."),
    ("database-engineering", "Database Engineering", "coral",
     "The deepest part of our practice."),
    ("aws-cloud", "AWS Cloud Architecture", "gold",
     "Architecture you can defend, and a bill you can predict."),
]

POSTS = [
    {
        "slug": "why-two-dashboards-disagree",
        "title": "Why your two dashboards disagree",
        "date": "2026-02-18",
        "date_h": "18 February 2026",
        "cat": "Analytics",
        "mins": 6,
        "excerpt": "Nearly every reporting dispute is a definition dispute wearing a "
                   "technical costume. Here is how to find the real disagreement and end it.",
    },
    {
        "slug": "database-cost-audit",
        "title": "The database bill nobody audits",
        "date": "2026-01-27",
        "date_h": "27 January 2026",
        "cat": "Databases",
        "mins": 7,
        "excerpt": "Most cloud database overspend is not a pricing problem. It is five "
                   "specific query patterns, and each one is cheaper to fix than to host.",
    },
    {
        "slug": "ml-production-readiness",
        "title": "What has to be true before a model ships",
        "date": "2025-12-09",
        "date_h": "9 December 2025",
        "cat": "AI & ML",
        "mins": 8,
        "excerpt": "Models rarely fail in the notebook. They fail at the boundary between "
                   "training data and the real world — a data engineering problem, not a modelling one.",
    },
]


def layout(path, title, desc, body, accent="emerald", nav_key=None, crumbs=None, noindex=False):
    canonical = SITE + path
    nav_html = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' aria-current="page"' if label == nav_key else "", label)
        for label, href in NAV
    )
    mobile_html = "".join('<a href="%s">%s</a>' % (href, label) for label, href in NAV)

    crumb_html = ""
    if crumbs:
        parts = ['<a href="/">Home</a>']
        for label, href in crumbs:
            parts.append('<span aria-hidden="true">/</span>')
            parts.append('<a href="%s">%s</a>' % (href, label) if href else "<span>%s</span>" % label)
        crumb_html = '<div class="wrap"><nav class="crumb" aria-label="Breadcrumb">%s</nav></div>' % "".join(parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{'<meta name="robots" content="noindex">' if noindex else ''}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/theme.js"></script>
</head>
<body data-accent="{accent}">
<a class="skip" href="#main">Skip to content</a>

<header class="hdr">
  <div class="wrap hdr-in">
    <a href="/" class="brand">{MARK}Intellora Tech</a>
    <nav class="nav" aria-label="Primary">{nav_html}</nav>
    <div class="hdr-act">
      <button class="icon-btn" id="theme" type="button" aria-label="Switch theme">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      </button>
      <a href="/contact/" class="btn btn-p">Book a call</a>
      <button class="burger" id="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mobile"><i></i><i></i><i></i></button>
    </div>
  </div>
  <div class="mobile" id="mobile">
    {mobile_html}
    <a href="/tools/estimator/">Price estimator</a>
    <a href="/contact/" class="btn btn-p">Book a call</a>
  </div>
</header>
{crumb_html}
<main id="main">
{body}
</main>

<footer class="ft">
  <div class="wrap">
    <div class="ft-g">
      <div>
        <p class="brand">{MARK}Intellora Tech</p>
        <p class="ft-about">A practice of specialists across data engineering, cloud architecture, governance, security, machine learning and databases — led by a principal engineer.</p>
        <p class="mt4"><a href="mailto:{EMAIL}">{EMAIL}</a><br>Distributed team · delivery worldwide</p>
      </div>
      <div>
        <h2>Products</h2>
        <ul>{"".join('<li><a href="/products/%s/">%s</a></li>' % (s, n) for s, n, _, _ in PRODUCTS)}</ul>
      </div>
      <div>
        <h2>Explore</h2>
        <ul>
          <li><a href="/projects/">Projects</a></li>
          <li><a href="/blog/">Blog</a></li>
          <li><a href="/tools/estimator/">Price estimator</a></li>
          <li><a href="/tools/maturity/">Data health check</a></li>
        </ul>
      </div>
      <div>
        <h2>Company</h2>
        <ul>
          <li><a href="/about/">About</a></li>
          <li><a href="/contact/">Contact</a></li>
          <li><a href="/payment/">Payments</a></li>
        </ul>
      </div>
    </div>
    <div class="ft-b"><span>© 2026 Intellora Tech</span><span>A distributed practice · delivered worldwide</span></div>
  </div>
</footer>

<script src="/assets/site.js" defer></script>
</body>
</html>
"""


def write(path, html):
    rel = path.strip("/")
    out = os.path.join(ROOT, rel, "index.html") if rel else os.path.join(ROOT, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", os.path.relpath(out, ROOT))


def cta(title, text, primary=("Book a call", "/contact/"), secondary=None):
    sec = ('<a href="%s" class="btn btn-s">%s</a>' % (secondary[1], secondary[0])) if secondary else ""
    return f"""
<section class="wrap section">
  <div class="section-tint ctr rv">
    <h2 style="max-width:22ch;margin-inline:auto">{title}</h2>
    <p class="lead" style="margin-inline:auto">{text}</p>
    <div class="row ctr mt5" style="justify-content:center">
      <a href="{primary[1]}" class="btn btn-p">{primary[0]} <span class="ar" aria-hidden="true">→</span></a>
      {sec}
    </div>
  </div>
</section>"""


# ----------------------------------------------------------------- home
home = f"""
<section class="wrap page-head">
  <div class="hero">
    <div>
      <p class="eyebrow">A practice of specialists</p>
      <h1>Data platforms that hold up when someone checks the numbers.</h1>
      <p class="lead">We build and fix the systems underneath your reports — databases, data pipelines, cloud setups, and the rules that keep the numbers trustworthy. You speak to a hands-on engineer from the team that will do the work.</p>
      <div class="row mt6">
        <a href="/contact/" class="btn btn-p">Book a call <span class="ar" aria-hidden="true">→</span></a>
        <a href="/tools/estimator/" class="btn btn-s">Estimate the cost</a>
      </div>
    </div>
    <aside class="panel">
      <p class="mono mb4">At a glance</p>
      <div class="rows">
        <div><div><p class="n">Structure</p></div><p class="d">Distributed specialists</p></div>
        <div><div><p class="n">Delivery</p></div><p class="d">Remote, worldwide</p></div>
        <div><div><p class="n">First reply</p></div><p class="d">One working day</p></div>
        <div><div><p class="n">Pricing</p></div><p class="d">Fixed on signature</p></div>
        <div><div><p class="n">Intro call</p></div><p class="d">Free · 15 minutes</p></div>
        <div><div><p class="n">Deep-dive session</p></div><p class="d">USD 250 · 60 minutes</p></div>
      </div>
    </aside>
  </div>
</section>

<section class="wrap mb6">
  <div class="pgfx rv" role="img" aria-label="Animated diagram. Four fragmented data sources — a stale CRM export, a payments ledger with three conflicting schemas, a manual operations spreadsheet and an unindexed object store — flow through a four-stage pipeline of ingest, validate, model and serve. They emerge as a single source of truth with twelve-minute data freshness, ninety-nine point six per cent pipeline reliability and one agreed metric definition. Figures illustrate a representative project.">
    <div class="pgfx-hd">
      <span>pipeline_view — representative project</span>
      <span class="lv"><span class="dot-live"></span>running</span>
      <span class="sweep"></span>
    </div>
    <div class="pgfx-bd">
      <div class="flow" aria-hidden="true">
        <span style="--y0:31%;--y1:26%;animation-delay:0s"></span>
        <span style="--y0:44%;--y1:41%;animation-delay:-1.1s"></span>
        <span style="--y0:57%;--y1:56%;animation-delay:-2.2s"></span>
        <span style="--y0:70%;--y1:72%;animation-delay:-3.3s"></span>
        <span style="--y0:38%;--y1:66%;animation-delay:-4.4s"></span>
        <span style="--y0:63%;--y1:33%;animation-delay:-5.5s"></span>
      </div>
      <div>
        <div class="pcol-l">Before <em>· 4 sources, 0 contracts</em></div>
        <div class="src"><span class="sd"></span><span class="sn">CRM export</span><span class="sm">stale 6d</span></div>
        <div class="src"><span class="sd"></span><span class="sn">Payments ledger</span><span class="sm">3 schemas</span></div>
        <div class="src"><span class="sd"></span><span class="sn">Ops spreadsheet</span><span class="sm">manual</span></div>
        <div class="src"><span class="sd"></span><span class="sn">Object store</span><span class="sm">unindexed</span></div>
      </div>
      <div>
        <div class="pipe">
          <div class="pipe-n">Intellora pipeline</div>
          <div class="pipe-rail"><u></u><i></i><i></i><i></i></div>
          <div class="pipe-st"><b>INGEST</b><b>VALIDATE</b><b>MODEL</b><b>SERVE</b></div>
          <div class="pipe-tag">governed · tested · traced</div>
        </div>
      </div>
      <div>
        <div class="pcol-l">After <em class="ok">· 1 source of truth</em></div>
        <div class="out"><span class="ol">Data freshness</span><span class="ov">12 min</span></div>
        <div class="out"><span class="ol">Pipeline reliability</span><span class="ov">99.6%</span></div>
        <div class="out"><span class="ol">Metric definitions</span><span class="ov">1 agreed</span></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="grid c3">
    <a href="/products/" class="card card-accent k-emerald rv">
      <p class="mono">Start here</p>
      <h3>Six products</h3>
      <p>Reporting, governance, security, AI, databases and AWS — buy one or several.</p>
      <span class="go">See the products →</span>
    </a>
    <a href="/tools/estimator/" class="card card-accent k-gold rv">
      <p class="mono">Two minutes</p>
      <h3>Estimate the cost</h3>
      <p>Six questions gives you a price range, a timeline and a breakdown you can forward.</p>
      <span class="go">Open the estimator →</span>
    </a>
    <a href="/blog/" class="card card-accent k-coral rv">
      <p class="mono">Blog</p>
      <h3>Field notes</h3>
      <p>What actually goes wrong with company data, written from real jobs rather than theory.</p>
      <span class="go">Read the blog →</span>
    </a>
  </div>
</section>

<section class="wrap section">
  <div class="grid c4">
    <div class="stat rv"><p class="v">10+</p><p class="k">Years of production data engineering</p></div>
    <div class="stat rv"><p class="v">3</p><p class="k">Most projects we run at once</p></div>
    <div class="stat rv"><p class="v">6</p><p class="k">Products, sold separately or together</p></div>
    <div class="stat rv"><p class="v">0</p><p class="k">Account managers between you and the engineers</p></div>
  </div>
</section>

<section class="wrap section">
  <div class="capacity rv">
    <div class="grid c2" style="align-items:center">
      <div>
        <p class="eyebrow">Deliberately limited</p>
        <h2 style="max-width:18ch">Three projects at a time. Never four.</h2>
        <p class="lead">What we sell is undivided specialist attention, and attention does not scale by taking on more work. So we cap the book, decline what we cannot do excellently, and finish what we start before opening the next slot.</p>
        <p class="mono mt6">Projects we can take right now</p>
        <div class="slots" role="img" aria-label="Two of three project slots currently committed, one open.">
          <i></i><i></i><i class="open"></i>
        </div>
        <p class="mono mt4">2 committed · 1 open</p>
      </div>
      <div class="grid" style="gap:var(--s4)">
        <div class="card card-accent k-emerald"><h3>Specialists, not generalists</h3><p>Each project is staffed with the people whose depth matches the work, and the principal reviews everything that ships. No junior learning on your budget.</p></div>
        <div class="card card-accent k-gold"><h3>We say no more than yes</h3><p>Work outside our depth, undefined scope, or a timeline that would force shortcuts — declined, with a suggestion of who is better placed.</p></div>
        <div class="card card-accent k-indigo"><h3>Narrow scope, finished properly</h3><p>A tightly drawn project delivered completely beats a broad one delivered to eighty per cent. Scope is fixed at signature and changes are quoted before work starts.</p></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="orbit-w rv">
    <div class="orbit" role="img" aria-label="Diagram showing Intellora Tech at the centre of two rotating rings. The inner ring holds the six products: analytics and business intelligence, governance, security, artificial intelligence and machine learning, database engineering, and AWS cloud architecture. The outer ring holds representative services including ETL and ELT pipelines, lineage tracing, feature pipelines, access control design, Oracle Analytics, Oracle Data Integrator, cost optimisation, semantic modelling, MLOps and performance tuning.">
      <div class="orb-halo" aria-hidden="true"></div>
      <div class="orb-core"><b>Intellora<br>Tech</b><i>6 products</i></div>
      <div class="ring ring1">
        <div class="onode p-analytics" style="--a:0deg"><div class="ospin"><div class="opill">Analytics &amp; BI</div></div></div>
        <div class="onode p-governance" style="--a:60deg"><div class="ospin"><div class="opill">Governance</div></div></div>
        <div class="onode p-security" style="--a:120deg"><div class="ospin"><div class="opill">Security</div></div></div>
        <div class="onode p-ai" style="--a:180deg"><div class="ospin"><div class="opill">AI &amp; ML</div></div></div>
        <div class="onode p-database" style="--a:240deg"><div class="ospin"><div class="opill">Databases</div></div></div>
        <div class="onode p-cloud" style="--a:300deg"><div class="ospin"><div class="opill">AWS Cloud</div></div></div>
      </div>
      <div class="ring ring2">
        <div class="onode" style="--a:0deg"><div class="ospin"><div class="opill">ETL &amp; ELT</div></div></div>
        <div class="onode" style="--a:36deg"><div class="ospin"><div class="opill">Lineage tracing</div></div></div>
        <div class="onode" style="--a:72deg"><div class="ospin"><div class="opill">Access control</div></div></div>
        <div class="onode" style="--a:108deg"><div class="ospin"><div class="opill">Feature pipelines</div></div></div>
        <div class="onode" style="--a:144deg"><div class="ospin"><div class="opill">MLOps</div></div></div>
        <div class="onode" style="--a:180deg"><div class="ospin"><div class="opill">Oracle Data Integrator</div></div></div>
        <div class="onode" style="--a:216deg"><div class="ospin"><div class="opill">Performance tuning</div></div></div>
        <div class="onode" style="--a:252deg"><div class="ospin"><div class="opill">Cost optimisation</div></div></div>
        <div class="onode" style="--a:288deg"><div class="ospin"><div class="opill">Oracle Analytics</div></div></div>
        <div class="onode" style="--a:324deg"><div class="ospin"><div class="opill">Semantic modelling</div></div></div>
      </div>
    </div>
    <p class="orb-cap">Six products · one team · you speak to the engineers who build it</p>
  </div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <h2>What we are best at</h2>
      <p class="lead">A decade inside core banking, United Nations humanitarian work, and national tax and customs systems. That is what we are fast at: regulated data, matching numbers that must agree, audit trails, and moves that cannot afford a bad switch-over.</p>
      <div class="row mt5">
        <a href="/projects/" class="btn btn-s">See our projects</a>
        <a href="/about/" class="btn btn-g">About the practice →</a>
      </div>
    </div>
    <div class="rv">
      <h2>How a project runs</h2>
      <div class="rows mt4">
        <div><div><p class="n">Written proposal</p><p class="m">One page: the problem, the work, the price, the dates</p></div><p class="d">48 hours</p></div>
        <div><div><p class="n">Fixed price on signature</p><p class="m">Any change is priced before work starts</p></div><p class="d">Always</p></div>
        <div><div><p class="n">Written update</p><p class="m">What is done, what is next, what is stuck</p></div><p class="d">Every Friday</p></div>
        <div><div><p class="n">Handover</p><p class="m">Guides, decisions written down, a live session</p></div><p class="d">Final week</p></div>
      </div>
    </div>
  </div>
</section>
""" + cta(
    "Tell us what is broken.",
    "One paragraph is enough. You will hear back within one working day.",
    secondary=("Run the health check", "/tools/maturity/"),
)

write("", layout("/", "Intellora Tech — Data, Cloud &amp; AI Engineering",
                 "A practice of specialists in data engineering, cloud architecture, governance, security and "
                 "machine learning, led by a principal engineer. You speak to hands-on engineers.",
                 home, accent="emerald"))

# ----------------------------------------------------------- capabilities hub
prod_cards = "".join(f"""
    <a href="/products/{slug}/" class="card card-accent k-{colour} rv">
      <p class="mono">{i:02d}</p>
      <h3>{name}</h3>
      <p>{line}</p>
      <span class="go">Read more →</span>
    </a>""" for i, (slug, name, colour, line) in enumerate(PRODUCTS, 1))

prod_hub = f"""
<section class="wrap page-head">
  <p class="eyebrow">Products</p>
  <h1>Six products, bought separately or together.</h1>
  <p class="lead">Each one is a complete piece of work on its own. Most clients buy one, see it land, then buy the next.</p>
</section>

<section class="wrap">
  <div class="grid c3">{prod_cards}</div>
</section>
""" + cta("Not sure which one you need?",
          "The health check takes two minutes and points at what is most likely holding you back.",
          primary=("Run the health check", "/tools/maturity/"),
          secondary=("Book a call", "/contact/"))

write("products", layout("/products/", "Products — Intellora Tech",
                            "Six products: reporting and BI, data governance, security, AI and machine "
                            "learning, database engineering and AWS cloud work.",
                            prod_hub, accent="emerald", nav_key="Products",
                            crumbs=[("Products", None)]))


# --------------------------------------------------------------- pillar pages
def product_page(slug, name, colour, accent, headline, intro, services, tech, budget, triggers):
    svc = "".join('<li><b>%s</b><span>%s</span></li>' % (t, d) for t, d in services)
    chips = "".join('<span class="chip">%s</span>' % t for t in tech)
    trg = "".join('<li><b>%s</b></li>' % t for t in triggers)
    body = f"""
<section class="wrap page-head">
  <p class="eyebrow">{name}</p>
  <h1>{headline}</h1>
  <p class="lead">{intro}</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <div class="rv">
      <h2 class="mb5">What we do</h2>
      <ul class="svc">{svc}</ul>
    </div>
    <div class="rv">
      <h2 class="mb5">Technologies</h2>
      <div class="chips">{chips}</div>

      <h2 class="mt7 mb4">Who usually owns the budget</h2>
      <p class="soft">{budget}</p>

      <h2 class="mt7 mb4">What triggers the purchase</h2>
      <ul class="svc">{trg}</ul>
    </div>
  </div>
</section>
""" + cta("Is this the piece you need?",
          "Twenty minutes on a call is usually enough to know whether this is the right starting point.",
          secondary=("Estimate the cost", "/tools/estimator/"))
    write("products/" + slug,
          layout("/products/%s/" % slug, "%s — Intellora Tech" % re.sub("&amp;", "&", name),
                 intro[:155], body, accent=accent, nav_key="Products",
                 crumbs=[("Products", "/products/"), (name, None)]))


product_page(
    "analytics-bi", "Analytics &amp; BI", "emerald", "emerald",
    "Numbers your board can act on without arguing about them first.",
    "Most reporting problems are definition problems wearing a technical costume. We model each metric once, govern the definition, and build the reporting layer on top of it — so the argument moves from whose number is right to what to do about it.",
    [("Semantic modelling &amp; metric governance", "One agreed definition per metric, versioned and consumed everywhere."),
     ("Oracle Analytics Server design &amp; installation", "Architecture, sizing, installation, RPD modelling, subject areas, security and high availability, including migration from legacy OBIEE."),
     ("Power BI &amp; embedded analytics", "Dashboards built around decisions people actually make, and analytics embedded into your own product where that is the requirement."),
     ("Regulatory &amp; management reporting", "Reporting pipelines with audit trails, reconciliation controls and defensible lineage for regulators, auditors and boards."),
     ("Self-service enablement", "Curated datasets, documentation and training so analysts answer their own questions without filing tickets.")],
    ["Oracle Analytics Server", "Oracle Analytics Cloud", "Power BI", "dbt", "SQL", "Redshift", "Snowflake", "Athena"],
    "Head of Data, CDO, or a Finance Director who has lost patience with reconciliation.",
    ["Two dashboards disagree and nobody can say which is right",
     "A regulator or auditor has asked how a reported figure was derived",
     "Analysts spend more time assembling data than analysing it"])

product_page(
    "data-governance", "Data Governance", "indigo", "indigo",
    "Evidence you can produce in minutes, not weeks.",
    "Governance fails when it is written as policy and never wired into the pipeline. We implement it as running infrastructure: lineage captured automatically, quality enforced at the boundary, ownership recorded where the data lives.",
    [("Governance frameworks", "Ownership models, stewardship roles, decision rights and policy grounded in DAMA-DMBOK practice."),
     ("Lineage &amp; governance tracing", "Column-level tracing from source system through every transformation to the final report field, with impact analysis before changes ship."),
     ("Metadata management &amp; cataloguing", "OpenMetadata and equivalents wired into pipelines so ownership, glossary, freshness and lineage stay current automatically."),
     ("Data quality &amp; observability", "Automated validation, schema enforcement, anomaly detection and alerting on data correctness rather than job status alone."),
     ("Master data management", "Entity resolution, golden record design and survivorship rules for customers, counterparties, products and locations."),
     ("Privacy impact assessment &amp; DPIA", "Processing registers, risk scoring, high-risk flagging and retention schedules aligned to GDPR and equivalent regimes.")],
    ["OpenMetadata", "OpenLineage", "Great Expectations", "dbt tests", "DAMA-DMBOK", "ISO/IEC/IEEE 29148"],
    "CDO, Chief Risk &amp; Compliance Officer, or a Head of Data preparing for an audit or a funding round.",
    ["An audit, regulator or investor has asked for evidence you cannot assemble quickly",
     "A schema change broke a downstream report nobody knew existed",
     "New privacy obligations require a defensible processing record"])

product_page(
    "security", "Security &amp; Data Protection", "deep", "emerald",
    "Security designed into the platform, not bolted on after the finding.",
    "This is data-platform security specifically — how your warehouse, pipelines and analytics layer are protected, segmented, encrypted and evidenced.",
    [("Data security architecture", "Security design for the data platform: trust boundaries, segmentation, data classification and control placement."),
     ("Encryption &amp; key management", "Encryption at rest and in transit, KMS key hierarchy, rotation policy, envelope encryption and field-level protection for sensitive attributes."),
     ("Access control design", "Role-based and attribute-based access control, row and column-level security, least-privilege review and joiner-mover-leaver process for data access."),
     ("Secrets management", "Removing credentials from code and configuration, centralised secrets storage, rotation and short-lived credential patterns."),
     ("Audit logging &amp; evidence", "Tamper-evident logging of data access and change, retention aligned to your obligations, and query interfaces auditors can actually use."),
     ("Threat modelling &amp; posture review", "Structured threat modelling of the data estate and a prioritised remediation plan, plus incident response runbooks for data exposure scenarios.")],
    ["AWS KMS", "AWS IAM", "Secrets Manager", "CloudTrail", "VPC design", "Lake Formation", "Database-native RLS"],
    "CISO, Head of Security, or a CTO responding to a customer security questionnaire.",
    ["An enterprise customer sent a security questionnaire you cannot pass",
     "Credentials are sitting in code and nobody is sure where else they are",
     "You cannot evidence who accessed which data, when"])

product_page(
    "ai-machine-learning", "AI &amp; Machine Learning", "plum", "plum",
    "Models that reach production, on data you can defend.",
    "We approach machine learning from the data side first. Most organisations asking for models actually need the layer underneath fixed — and we will tell you that rather than build something impressive on unreliable inputs.",
    [("Feature pipelines &amp; feature stores", "Reproducible feature engineering with consistent definitions between training and serving."),
     ("Model training workflows", "Versioned, reproducible training with experiment tracking and a registry that records what shipped and why."),
     ("MLOps &amp; deployment", "Deployment pipelines, rollback paths, monitoring for drift and degradation, and retraining schedules."),
     ("Retrieval-augmented generation", "Document ingestion, chunking, embedding and retrieval over your own corpus, with evaluation and citation of sources."),
     ("AI governance &amp; model risk", "Model documentation, lineage from training data to prediction, bias assessment, and the record a regulator will eventually ask for.")],
    ["Python", "scikit-learn", "XGBoost", "MLflow", "Amazon SageMaker", "Amazon Bedrock", "Vector stores", "Airflow"],
    "CTO, Head of Data Science, or a product owner with a use case and no path to production.",
    ["Models work in notebooks and never ship",
     "A deployed model has quietly degraded and nobody noticed",
     "An AI initiative was announced before the data layer was ready"])

product_page(
    "database-engineering", "Database Engineering", "coral", "coral",
    "The deepest part of our practice.",
    "A decade of production database work across core banking, humanitarian operations and revenue administration. This is where our experience is longest and where the fastest wins usually are — tuning a query is almost always cheaper than buying more hardware.",
    [("Logical &amp; physical data modelling", "Conceptual through physical models, normalisation and deliberate denormalisation, dimensional and Data Vault approaches where they fit."),
     ("Database design &amp; development", "Schema design, constraints and referential integrity, stored procedures and packages, across Oracle, PostgreSQL, MySQL and SQL Server."),
     ("Performance tuning", "Execution plan analysis, index strategy, statistics management, partitioning and query rewrites."),
     ("High availability &amp; recovery", "Replication topology, failover design, backup strategy and tested recovery procedures with real recovery time objectives."),
     ("Migration &amp; upgrade", "Version upgrades and cross-platform migration with parallel validation and reconciliation before cutover."),
     ("Oracle Data Integrator development", "ODI mappings, packages, load plans and knowledge module customisation, including remediation of inherited estates.")],
    ["Oracle 19c &amp; 23ai", "PostgreSQL", "MySQL", "SQL Server", "MongoDB", "Redis", "Oracle Data Integrator", "Data Vault"],
    "CTO, VP Engineering, or a Head of Platform whose database has become the bottleneck.",
    ["Queries that used to take seconds now take minutes",
     "An unsupported database version is becoming an audit finding",
     "Nobody has tested whether the backups actually restore"])

product_page(
    "aws-cloud", "AWS Cloud Architecture", "gold", "gold",
    "Architecture you can defend, and a bill you can predict.",
    "Certified on AWS and opinionated about it, while staying vendor-neutral above the platform layer. Most cloud cost problems are architecture problems, which is why the review and the savings work are the same project.",
    [("Well-Architected review", "Structured review across operational excellence, security, reliability, performance, cost and sustainability, with a prioritised remediation plan."),
     ("Landing zone &amp; multi-account design", "Account structure, organisational units, guardrails, network topology and centralised logging built for growth."),
     ("Cloud migration", "On-premise to AWS planning and execution, including hybrid cutover with shadow validation for low-downtime moves."),
     ("FinOps &amp; cost optimisation", "Line-by-line spend audit, quick wins implemented during the project, and structural recommendations with quantified savings."),
     ("Infrastructure as code", "Terraform and CloudFormation provisioning, environment parity, CI/CD for data infrastructure and automated testing."),
     ("Resilience &amp; disaster recovery", "Recovery objectives agreed with the business, failover design and tested restore procedures.")],
    ["AWS", "Terraform", "CloudFormation", "S3", "Glue", "Redshift", "Lambda", "EKS"],
    "CTO, Head of Platform, or a Finance lead who has seen the cloud bill trend line.",
    ["The monthly bill grows faster than usage does",
     "A migration has stalled halfway and both estates now need running",
     "Nobody can say what happens if the primary region goes down"])

# -------------------------------------------------------------------- projects
PROJECTS = [
    {
        "name": "National tax administration system rebuild",
        "colour": "indigo",
        "body": "Set the data quality rules across every old and new system, decided who owns which data, "
                "put lineage and access controls in place, and wrote the plan for moving the data — a move "
                "spanning several years.",
        "tags": ["Data governance", "Migration planning", "Data quality"],
    },
    {
        "name": "Data lake house — pipeline architecture",
        "colour": "emerald",
        "body": "Built the pipelines that fill a central data store: Apache Airflow to schedule the work, Kafka "
                "for live data, PySpark for the heavy lifting. Data from several separate systems now lands in "
                "one place that the reports read from.",
        "tags": ["Airflow", "Kafka", "PySpark", "Power BI"],
    },
    {
        "name": "Data warehouse rebuild",
        "colour": "gold",
        "body": "Rebuilt the loading pipelines so they process far more data in the same window, and added "
                "automatic quality checks, alerting and schema enforcement — so a broken load is caught before "
                "it reaches a report rather than after someone queries it.",
        "tags": ["ELT redesign", "Data quality", "Alerting"],
    },
    {
        "name": "Core banking upgrade — Oracle 12c to 19c",
        "colour": "coral",
        "body": "Moved core banking and mobile banking databases onto a new Oracle version with no downtime and "
                "no data lost. Performance tuning and stress testing were done on the new setup before anyone "
                "was switched over to it.",
        "tags": ["Oracle 19c", "Zero downtime", "Performance tuning"],
    },
    {
        "name": "Disaster recovery and emergency failover",
        "colour": "deep",
        "body": "Designed an Oracle Data Guard cascading standby setup across several recovery sites, then led "
                "the emergency failover that brought a bank back up after a critical infrastructure failure — "
                "with no data lost.",
        "tags": ["Data Guard", "Disaster recovery", "Failover"],
    },
    {
        "name": "Biometric records for two million people",
        "colour": "plum",
        "body": "Kept the databases holding more than two million biometric records accurate, secure and "
                "available across field sites with limited infrastructure — the records behind food and cash "
                "distribution — including checking and correcting a national register.",
        "tags": ["Data integrity", "Access security", "Field operations"],
    },
    {
        "name": "Core banking databases and reporting",
        "colour": "emerald",
        "body": "Kept core banking databases fast and available, managed who could reach what, and built the "
                "ETL processes feeding reporting across several business units.",
        "tags": ["Core banking", "ETL", "Access control"],
    },
]

# Organisations where the work above was delivered.
#
# `logo` names a file in assets/img/logos/. Drop the file in with that exact
# name and re-run this script — the tile switches from a wordmark to the image
# automatically. A missing file is not an error: the tile just falls back to the
# wordmark, so the page never shows a broken image.
#
# Format: SVG if you have it, otherwise PNG with a transparent background,
# roughly 400px on the long edge. Logos are third-party trademarks — use them
# only with the owner's permission.
ORGS = [
    {"name": "Uganda Revenue Authority", "short": "URA", "logo": "ura.png"},
    {"name": "FINCA", "short": "FINCA", "logo": "finca.jpg"},
    {"name": "UN World Food Programme", "short": "WFP", "logo": "wfp.png"},
]

LOGO_DIR = os.path.join(ROOT, "assets", "img", "logos")


def org_tile(o):
    """One organisation tile: a square badge plus the name.

    Badges sit on a white plate because the supplied marks are a mix — some are
    free-standing with transparent backgrounds, others are solid-colour blocks —
    and the plate is what makes them line up and stay legible in dark mode. A
    missing file falls back to initials on the same plate, so the row keeps its
    shape whether or not every logo has arrived.
    """
    have_file = o["logo"] and os.path.exists(os.path.join(LOGO_DIR, o["logo"]))
    if have_file:
        badge = ('<span class="logo-badge">'
                 '<img src="/assets/img/logos/%s" alt="" loading="lazy" decoding="async"></span>' % o["logo"])
    else:
        badge = '<span class="logo-badge is-empty">%s</span>' % o["short"]
    return ('<div class="logo-tile">%s<span class="logo-name">%s</span></div>') % (badge, o["name"])


proj_cards = "".join("""
      <div class="card card-accent k-{colour} rv">
        <h3>{name}</h3>
        <p>{body}</p>
        <div class="chips mt4">{chips}</div>
      </div>""".format(
        colour=p["colour"], name=p["name"], body=p["body"],
        chips="".join('<span class="chip">%s</span>' % t for t in p["tags"]))
    for p in PROJECTS)

projects = f"""
<section class="wrap page-head">
  <p class="eyebrow">Projects</p>
  <h1>Work we have actually done.</h1>
  <p class="lead">Real work, described plainly. Each of these was delivered by our people in the roles they held at the time.</p>
</section>

<section class="wrap">
  <div class="grid c2">{proj_cards}</div>
</section>

<section class="wrap section">
  <div class="logo-band rv">
    <p class="mono ctr mb5">Where our people have delivered this work</p>
    <div class="logo-wall">{"".join(org_tile(o) for o in ORGS)}</div>
  </div>
</section>

<section class="wrap section">
  <div class="rv narrow">
    <h2 class="mb4">What this adds up to</h2>
    <p class="lead">Tax and customs systems, core banking, and humanitarian operations — places where a wrong number has consequences and someone eventually checks. That is the kind of work we are quick at: regulated data, matching numbers that must agree, audit trails, and moves that cannot afford a bad switch-over.</p>
    <p class="mono mt6 mb3">We also work in</p>
    <div class="chips">{"".join('<span class="chip">%s</span>' % t for t in [
      "Lending &amp; credit", "Insurance", "Payments &amp; fintech", "Capital markets",
      "Logistics &amp; supply chain", "Telecoms", "Public sector", "Energy &amp; utilities",
      "Healthcare administration", "Retail &amp; e-commerce"])}</div>
  </div>
</section>
""" + cta("Have a project like one of these?",
          "Tell us what is broken in a paragraph. We will tell you honestly whether we are the right people.",
          secondary=("See what we sell", "/products/"))

write("projects", layout("/projects/", "Projects — Intellora Tech",
                         "Real project work: a national tax administration system rebuild, data lake pipelines, "
                         "a data warehouse rebuild, core banking upgrades, disaster recovery and large-scale "
                         "biometric data operations.",
                         projects, accent="indigo", nav_key="Projects",
                         crumbs=[("Projects", None)]))


# ------------------------------------------------------------------ tools hub
tools_hub = """
<section class="wrap page-head">
  <p class="eyebrow">Tools</p>
  <h1>Two free tools, two minutes each.</h1>
  <p class="lead">Both are free, need no sign-up, and give you something you can act on — or forward to whoever holds the budget.</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <a href="/tools/estimator/" class="card card-accent k-gold rv">
      <p class="mono">Six questions</p>
      <h3>Price estimator</h3>
      <p>Answer six questions about the job and get a price range, how long it should take, and how the work splits into stages. Built from our own rate card.</p>
      <span class="go">Open the estimator →</span>
    </a>
    <a href="/tools/maturity/" class="card card-accent k-emerald rv">
      <p class="mono">Six questions</p>
      <h3>Data health check</h3>
      <p>Answer six questions about your setup and get a plain description of where you stand, plus the two things worth fixing first.</p>
      <span class="go">Start the check →</span>
    </a>
  </div>
</section>
""" + cta("Want a real number instead of an estimate?",
          "A short call and a look at your systems turns an estimate into a fixed price.")

write("tools", layout("/tools/", "Tools — Intellora Tech",
                      "Two free tools: a price estimator for data, cloud and AI work, and a data health check.",
                      tools_hub, accent="gold", nav_key="Tools", crumbs=[("Tools", None)]))

# ------------------------------------------------------------------- estimator
def opts(group, items, cols="g2"):
    return '<div class="opt-grid %s" data-grp="%s">%s</div>' % (
        cols, group,
        "".join('<button class="opt" type="button" data-v="%s" aria-pressed="false"><b>%s</b><span>%s</span></button>' % (v, t, d)
                for v, t, d in items))


estimator = f"""
<section class="wrap page-head">
  <p class="eyebrow">Price estimator</p>
  <h1>Six questions, one price range.</h1>
  <p class="lead">Built from our own rate card and past work. You get a price range, how long it should take, and how the work splits into stages — all of it copyable into an email.</p>
</section>

<section class="wrap" id="est">
  <div class="steps">
    <span data-stepname="1" aria-current="step">1 · Objective</span>
    <span data-stepname="2" aria-current="false">2 · Shape</span>
    <span data-stepname="3" aria-current="false">3 · Estimate</span>
  </div>
  <div class="track"><i id="estBar"></i></div>

  <div data-pane="1">
    <p class="q-h">What are you trying to do?</p>
    {opts("type", [
        ("assess", "Assess or prove", "An assessment, audit or proof of concept before committing."),
        ("optimise", "Optimise", "Something exists and underperforms — cost, speed or reliability."),
        ("build", "Build", "A new platform, pipeline or product capability."),
        ("migrate", "Migrate", "Move or modernise an existing estate."),
    ])}
    <p class="q-h mt6">Which product is the main one?</p>
    {opts("pillar", [
        ("analytics", "Analytics &amp; BI", "Reporting, semantic models, dashboards."),
        ("governance", "Governance", "Lineage, quality, catalogue, privacy."),
        ("security", "Security", "Access control, encryption, evidence."),
        ("ai", "AI &amp; ML", "Feature pipelines, training, deployment."),
        ("database", "Databases", "Modelling, tuning, HA, migration."),
        ("cloud", "AWS cloud", "Architecture, landing zone, FinOps."),
    ], "g3")}
    <div class="row mt6"><button class="btn btn-p" id="estN1" type="button" disabled>Continue <span class="ar" aria-hidden="true">→</span></button></div>
  </div>

  <div data-pane="2" hidden>
    <p class="q-h">Complexity</p>
    {opts("cx", [
        ("std", "Standard", "Clean sources, familiar patterns."),
        ("mod", "Moderate", "Several systems, some unknowns."),
        ("adv", "Advanced", "Legacy estate, heavy integration, unclear lineage."),
    ], "g3")}
    <p class="q-h mt6">Scope</p>
    {opts("sz", [
        ("s", "Small", "One system or one reporting domain."),
        ("m", "Medium", "Several systems or a department."),
        ("l", "Large", "Enterprise-wide or multi-entity."),
    ], "g3")}
    <p class="q-h mt6">Governance load</p>
    {opts("gv", [
        ("light", "Light", "Internal use, limited external obligation."),
        ("standard", "Standard", "Audit trail and documented controls expected."),
        ("regulated", "Regulated", "Supervised entity, formal evidence required."),
    ], "g3")}
    <p class="q-h mt6">Timeline</p>
    {opts("tl", [
        ("relaxed", "Relaxed", "No hard deadline, cheaper to deliver."),
        ("standard", "Standard", "Normal pace."),
        ("rush", "Compressed", "Fixed external deadline."),
    ], "g3")}
    <div class="row mt6">
      <button class="btn btn-p" id="estN2" type="button" disabled>See the estimate <span class="ar" aria-hidden="true">→</span></button>
      <button class="btn btn-g" id="estB2" type="button">← Back</button>
    </div>
  </div>

  <div data-pane="3" hidden>
    <div class="grid c2">
      <div>
        <div class="row mb4" style="justify-content:space-between">
          <p class="mono">Estimated range</p>
          <label class="mono" for="cur" style="display:flex;gap:.5rem;align-items:center">Currency
            <select id="cur" style="width:auto"><option>USD</option><option>EUR</option><option>GBP</option><option>AED</option></select>
          </label>
        </div>
        <p class="result-price" id="resRange">—</p>
        <p class="soft mt4" id="resDur"></p>
        <div class="chips mt5" id="resTags"></div>
        <div class="row mt6">
          <a class="btn btn-p" id="resMail" href="mailto:{EMAIL}">Send this to us <span class="ar" aria-hidden="true">→</span></a>
          <button class="btn btn-s" id="resCopy" type="button">Copy summary</button>
          <span class="mono" id="resCopied" hidden>Copied</span>
        </div>
        <div class="row mt5"><button class="btn btn-g" id="estB3" type="button">← Change answers</button></div>
      </div>
      <div>
        <p class="mono mb4">How the work splits</p>
        <div id="resPhases"></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap">
  <noscript><div class="callout">The estimator needs JavaScript. Projects typically start at $4,200 for an assessment and $15,000 for a platform build — <a href="/contact/">email us</a> and we will price your case properly.</div></noscript>
</section>
""" + cta("Does the number work?",
          "After one call and a look at your systems, the estimate becomes a fixed price.",
          secondary=("Run the health check", "/tools/maturity/"))

write("tools/estimator", layout("/tools/estimator/", "Price estimator — Intellora Tech",
                               "Six questions gives a price range, a timeline and a stage-by-stage breakdown for data, cloud or AI work.",
                               estimator, accent="gold", nav_key="Tools",
                               crumbs=[("Tools", "/tools/"), ("Price estimator", None)]))

# -------------------------------------------------------------------- maturity
QUESTIONS = [
    ("Where does reporting data come from today?",
     [("", "Choose one"), ("1", "Spreadsheets and direct queries on production"),
      ("2", "A reporting database refreshed on a schedule"),
      ("3", "A modelled warehouse with defined layers"),
      ("4", "A governed platform with contracts between layers")]),
    ("If a number looks wrong, how long to trace it to source?",
     [("", "Choose one"), ("1", "Days, and often inconclusive"), ("2", "Hours, by asking the right person"),
      ("3", "Minutes, with documentation"), ("4", "Immediately, lineage is captured automatically")]),
    ("How are pipeline failures detected?",
     [("", "Choose one"), ("1", "Someone notices a stale dashboard"), ("2", "Job failure alerts"),
      ("3", "Job and freshness alerts"), ("4", "Data quality tests fail before consumers see it")]),
    ("Who can access sensitive data?",
     [("", "Choose one"), ("1", "Broad access, unclear boundaries"), ("2", "Role-based, reviewed occasionally"),
      ("3", "Least privilege with periodic review"), ("4", "Least privilege, row/column controls, full access logs")]),
    ("How is infrastructure provisioned?",
     [("", "Choose one"), ("1", "Manually, by hand"), ("2", "Scripted in places"),
      ("3", "Infrastructure as code for most of it"), ("4", "Fully declarative with environment parity")]),
    ("Where is machine learning today?",
     [("", "Choose one"), ("1", "Not started or exploratory only"), ("2", "Notebooks, nothing in production"),
      ("3", "One or two models deployed"), ("4", "Models in production with monitoring and retraining")]),
]

q_html = "".join(f"""
  <div class="field" data-q>
    <label for="q{i}">{q}</label>
    <select id="q{i}">{''.join('<option value="%s">%s</option>' % (v, t) for v, t in choices)}</select>
  </div>""" for i, (q, choices) in enumerate(QUESTIONS, 1))

maturity = f"""
<section class="wrap page-head">
  <p class="eyebrow">Data health check</p>
  <h1>Six questions about your data setup.</h1>
  <p class="lead">Answer honestly and you get a plain description of where you stand, what usually holds companies back at that point, and the two things we would fix first.</p>
</section>

<section class="wrap" id="mat">
  <div class="grid c2">
    <div class="rv">{q_html}
      <button class="btn btn-p" id="matGo" type="button">Show my result <span class="ar" aria-hidden="true">→</span></button>
    </div>
    <div class="rv"><div id="matOut" hidden></div></div>
  </div>
  <noscript><div class="callout mt6">This check needs JavaScript. <a href="/contact/">Book a call</a> and we will walk through the same questions with you.</div></noscript>
</section>
""" + cta("Want the proper version?",
          "A call replaces this with a real look at your systems.",
          secondary=("Estimate the cost", "/tools/estimator/"))

write("tools/maturity", layout("/tools/maturity/", "Data data health check — Intellora Tech",
                              "Six questions that show where your data setup stands and what is worth fixing first.",
                              maturity, accent="gold", nav_key="Tools",
                              crumbs=[("Tools", "/tools/"), ("Data health check", None)]))

# ------------------------------------------------------------------------ blog
post_cards = "".join(f"""
    <a href="/blog/{p['slug']}/" class="card card-accent k-coral rv">
      <p class="mono">{p['cat']} · {p['mins']} min read</p>
      <div class="post-card">
        <span class="t">{p['title']}</span>
        <span class="x">{p['excerpt']}</span>
      </div>
      <span class="go">Read →</span>
    </a>""" for p in POSTS)

blog_index = f"""
<section class="wrap page-head">
  <p class="eyebrow">Blog</p>
  <h1>Field notes from production systems.</h1>
  <p class="lead">Written from real jobs and things that went wrong, not vendor material. Short, specific, and useful whether or not you ever hire us.</p>
</section>

<section class="wrap">
  <div class="grid c3">{post_cards}</div>
</section>
""" + cta("Have a version of this problem?",
          "If one of these sounds like your platform, a twenty-minute call will tell you how deep it goes.")

write("blog", layout("/blog/", "Blog — Intellora Tech",
                     "Field notes on data platforms: reporting definitions, database cost, and what has to be "
                     "true before a machine learning model ships.",
                     blog_index, accent="coral", nav_key="Blog", crumbs=[("Blog", None)]))


def post_page(p, body_html):
    others = [o for o in POSTS if o["slug"] != p["slug"]][:2]
    more = "".join(f"""
    <a href="/blog/{o['slug']}/" class="card card-accent k-coral">
      <p class="mono">{o['cat']} · {o['mins']} min read</p>
      <div class="post-card"><span class="t">{o['title']}</span><span class="x">{o['excerpt']}</span></div>
      <span class="go">Read →</span>
    </a>""" for o in others)

    body = f"""
<article class="wrap page-head article">
  <p class="eyebrow">{p['cat']}</p>
  <h1 style="max-width:24ch">{p['title']}</h1>
  <div class="post-meta">
    <time datetime="{p['date']}">{p['date_h']}</time>
    <span>·</span><span>{p['mins']} minute read</span>
    <span>·</span><span>Intellora Tech engineering team</span>
  </div>
  <div class="prose mt7">{body_html}</div>
</article>

<section class="wrap section article">
  <h2 class="mb5">More from the blog</h2>
  <div class="grid c2">{more}</div>
</section>
""" + cta("Recognise this in your own platform?",
          "Twenty minutes is usually enough to tell you whether it is a small fix or a structural one.")

    write("blog/" + p["slug"], layout("/blog/%s/" % p["slug"], "%s — Intellora Tech" % p["title"],
                                      p["excerpt"], body, accent="coral", nav_key="Blog",
                                      crumbs=[("Blog", "/blog/"), (p["title"], None)]))


post_page(POSTS[0], """
<p>Two people open two dashboards, both labelled <em>active customers</em>, and get different numbers. The meeting stops. Someone is asked to "check the data", and three days later the answer is that both dashboards are correct.</p>

<p>They are correct because they are answering different questions. One counts a customer active if they transacted in the last 30 days. The other counts them active if their account is not closed. Nobody wrote either rule down, so nobody noticed they had diverged.</p>

<h2>The disagreement is almost never technical</h2>

<p>It is tempting to treat this as a pipeline problem — a join gone wrong, a filter applied in one place and not the other. Occasionally it is. Far more often the pipelines are both doing exactly what they were told, and what they were told was decided separately, months apart, by people solving different immediate problems.</p>

<p>The tell is simple: ask each dashboard's owner to state the definition out loud. If they hesitate, or reach for the SQL to answer, the definition does not exist as a governed object. It exists as an implementation detail, and implementation details drift.</p>

<blockquote>A metric that lives only in a query is not a definition. It is a copy of one, and copies diverge.</blockquote>

<h2>What actually fixes it</h2>

<p>The durable fix is to define each metric once, in one place, and have every consumer read from that place. In practice that means a semantic layer — <code>dbt</code> metrics, a warehouse view layer, an Oracle Analytics RPD, whatever fits your stack — that owns the calculation, and reporting tools that are forbidden from recalculating it themselves.</p>

<p>Three properties make it stick:</p>

<ul>
  <li><strong>One definition per metric, versioned.</strong> If the rule changes, that is a commit with a date and an author, not a silent edit in a dashboard.</li>
  <li><strong>Consumers cannot override it.</strong> The moment a report can redefine <em>active customer</em> locally, you are back where you started — only now with the appearance of governance.</li>
  <li><strong>The definition is readable by non-engineers.</strong> If the CFO cannot read the rule and agree with it, the rule has not actually been agreed.</li>
</ul>

<h2>The part people skip</h2>

<p>The technical work is the easy half. The hard half is getting the finance lead, the operations lead and the product lead into one room to agree what <em>active</em> means — because it turns out they each need it to mean something slightly different, and that disagreement is real, not a data problem.</p>

<p>When that happens, the answer is usually not one metric. It is two or three, each named precisely — <em>transacting customers (30d)</em>, <em>open accounts</em>, <em>billable accounts</em> — so that nobody has to guess which one a chart is showing. Precision in the name does more work than any amount of pipeline engineering.</p>

<h2>How to tell if you have this problem</h2>

<p>You do, if any of these are true: a recurring meeting spends time reconciling figures rather than acting on them; the answer to "which number is right" depends on who you ask; or a regulator has asked how a reported figure was derived and the answer took more than an hour to assemble.</p>

<p>None of those are reporting problems. They are all the same definition problem, showing up at different altitudes.</p>
""")

post_page(POSTS[1], """
<p>Cloud database spend has a peculiar property: it grows smoothly, so nobody ever has the moment where they look at it and flinch. Each month is a little more than the last, each increase is individually defensible, and eighteen months later the line item is four times what it was with no single decision to point at.</p>

<p>When we audit these bills, the overspend is rarely in the pricing model. It is in a handful of query patterns that were reasonable at small volumes and became expensive at large ones.</p>

<h2>1. The query that scans everything to return almost nothing</h2>

<p>A report filters on a date range and returns 400 rows. The execution plan shows a full scan of 90 million. Usually the filter is applied to a derived column — <code>WHERE YEAR(created_at) = 2026</code> — which makes the index unusable. Rewriting to a range predicate on the raw column changes the plan and, on managed platforms billed by data scanned, changes the bill directly.</p>

<h2>2. Statistics nobody has refreshed</h2>

<p>The optimiser makes its decisions from statistics. When those statistics describe a table as it was two years and forty million rows ago, it will confidently choose a nested loop where a hash join belongs. This is the cheapest fix on this list and the most commonly skipped: a stale-stats problem looks exactly like a hardware problem right up until someone checks.</p>

<h2>3. Indexes that exist for queries nobody runs</h2>

<p>Every index is paid for twice: once in storage, and again on every write. Estates that have been through several teams accumulate indexes added for a report that was retired long ago. Most engines expose usage counters. Anything unused across a full business cycle — including month-end and year-end, which is why you wait a full cycle — is a candidate for removal.</p>

<blockquote>Adding an index is a five-minute decision that you pay for on every insert, for years.</blockquote>

<h2>4. Partitions that are not aligned to how data is queried</h2>

<p>Partitioning helps only when the predicate lets the engine skip partitions. A table partitioned by ingest date, queried almost exclusively by transaction date, gets all of the maintenance cost and none of the pruning benefit. This one requires actually reading the query log rather than reasoning about how the table <em>should</em> be used.</p>

<h2>5. The pipeline that reprocesses history every night</h2>

<p>Full reloads survive because they are simple and correct. They stop being cheap the moment the table is large: reprocessing five years of history nightly to capture one day of change is a cost that grows with your success. Incremental processing with a watermark, plus a scheduled reconciliation to catch drift, keeps the correctness and drops most of the cost.</p>

<h2>Where to start</h2>

<p>Pull the ten most expensive queries by total cost — not by average runtime, which hides frequently-run cheap-looking queries — and read their plans. In most estates, those ten account for a large majority of the spend, and two or three of them are fixable in an afternoon.</p>

<p>The reason this work is undersold is that it produces no new capability. It just makes the bill smaller and the reports faster, which is a difficult thing to put in a launch announcement and an easy thing to justify to a finance director.</p>
""")

post_page(POSTS[2], """
<p>A model that scores well in a notebook and never reaches production is not a modelling failure. It is nearly always a data engineering failure that surfaced late, and the specific failures repeat across organisations with striking consistency.</p>

<h2>The features have to be reproducible at serving time</h2>

<p>The most common blocker: a feature computed from a table that only exists in the analytics warehouse, refreshed nightly, using a window that includes data not available at prediction time. The model works in training because it can see the future. In production it cannot, and accuracy collapses in a way that looks mysterious unless you go looking for leakage.</p>

<p>The fix is structural, not clever. Features get computed by one pipeline that serves both training and inference, or by two pipelines with a test that asserts they produce identical values for the same input. Anything less and the two drift, quietly.</p>

<h2>Training data has to be reconstructible</h2>

<p>Six months after deployment someone asks why the model made a particular decision. Answering means reconstructing the exact training set — which means the raw inputs, the transformation code and the feature definitions all have to be versioned together, not just the model weights.</p>

<blockquote>If you cannot rebuild the training set from scratch, you do not have a reproducible model. You have an artefact.</blockquote>

<p>In regulated settings this is not a nice-to-have. It is the thing a supervisor will ask for, and "we retrained since then" is not an answer.</p>

<h2>Someone has to own degradation</h2>

<p>Models decay. Input distributions shift, an upstream system changes a code list, a business process changes and the historical relationship stops holding. None of this raises an error — the model keeps returning confident predictions that are progressively less useful.</p>

<p>Production readiness means monitoring the inputs, not just the outputs: distribution checks on incoming features, alerts on null-rate and cardinality changes, and a scheduled review of prediction quality against outcomes once outcomes are known. And a named person who receives those alerts.</p>

<h2>There has to be a rollback</h2>

<p>The question "what do we do if this model starts behaving badly on a Friday afternoon" should have a boring answer: route traffic to the previous version, or to the deterministic rule the model replaced. If the answer involves a retraining run, the model is not deployed — it is merely running.</p>

<h2>The honest sequencing</h2>

<p>When an organisation asks for machine learning and the data layer underneath is not ready, the useful response is to say so and fix the layer first. The model built on unreliable inputs will be impressive in a demo and unusable in operations, and the credibility spent getting it approved does not come back.</p>

<p>Fixing the layer first is a slower announcement and a much faster route to something that survives contact with production.</p>
""")

# ----------------------------------------------------------------------- about
about = f"""
<section class="wrap page-head">
  <p class="eyebrow">About</p>
  <h1>A senior-led practice, deliberately small.</h1>
  <p class="lead">Intellora Tech is an engineering consultancy working across data, cloud, AI and security. A collective of specialists — database, cloud, analytics, machine learning, governance and security — led by a principal engineer who staffs each project and reviews what ships. You speak to hands-on engineers throughout, never an account manager.</p>
</section>

<section class="wrap section">
  <div class="capacity rv">
    <p class="eyebrow">How we stay small on purpose</p>
    <h2 style="max-width:24ch">A capped book is the quality control.</h2>
    <p class="lead">We run at most three projects concurrently. Not as a scarcity tactic — as the only honest way to promise that the specialists on your platform are genuinely thinking about it, and that the principal can review every piece of work rather than signing off work nobody senior has read.</p>
    <div class="grid c3 mt6">
      <div><p class="mono mb3">We decline</p><p class="soft">Work outside our depth, scope that is genuinely undefined at contracting, and deadlines that would force us to cut the testing or the documentation.</p></div>
      <div><p class="mono mb3">We finish</p><p class="soft">A project is done when it is documented, handed over and running — not when the hours are used up. Overrun on a fixed price is our problem, not yours.</p></div>
      <div><p class="mono mb3">We go narrow</p><p class="soft">One capability, delivered completely, beats a broad project delivered to eighty per cent. If the right answer is a smaller project, we will propose the smaller one.</p></div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <picture>
        <source type="image/webp" srcset="/assets/img/simon-720.webp">
        <img src="/assets/img/simon-720.jpg" width="720" height="720" alt="Portrait of Musisi Ntege Simon Peter, principal engineer at Intellora Tech." loading="lazy" decoding="async" style="border-radius:var(--r-lg);max-width:22rem">
      </picture>
    </div>
    <div class="rv">
      <p class="mono mb3">Principal engineer · practice lead</p>
      <h2>Musisi Ntege Simon Peter</h2>
      <p class="soft mt4">Leads the practice: sets the engineering standards, staffs each project, and reviews what goes out the door. Roughly a decade of production data engineering across core banking, United Nations humanitarian operations, and revenue and customs administration.</p>
      <p class="soft mt4">Deepest personally in Oracle database internals, enterprise data warehouse architecture and ETL and ELT engineering. Holds an MBA and a BSc in Computer Engineering.</p>
      <p class="mono mt6 mb3">Certified in</p>
      <div class="chips"><span class="chip">AWS Solutions Architect</span><span class="chip">Oracle Data Integrator</span><span class="chip">ITIL 4 Foundation</span><span class="chip">PRINCE2 Practitioner</span><span class="chip">Agile Scrum Master</span><span class="chip">COBIT 5 Foundation</span></div>
      <div class="row mt5">
        <a href="/contact/" class="btn btn-p">Book a call</a>
        <a href="/products/" class="btn btn-s">See the products</a>
      </div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="rv">
    <h2 class="mb4">Specialists, matched to your stack</h2>
    <p class="lead mb6">No single engineer is deepest at everything, and we do not pretend otherwise. The practice is organised around distinct specialisms, and a project is staffed with the people whose depth matches the work rather than whoever is free.</p>
    <div class="grid c3">
      <div class="card card-accent k-coral"><h3>Database engineering</h3><p>Oracle internals, PostgreSQL, SQL Server and MySQL. Modelling, tuning, high availability, migration and Oracle Data Integrator.</p></div>
      <div class="card card-accent k-gold"><h3>Cloud &amp; platform</h3><p>AWS architecture, landing zones, infrastructure as code, CI/CD for data infrastructure, and cost engineering.</p></div>
      <div class="card card-accent k-emerald"><h3>Analytics engineering</h3><p>Semantic modelling, dbt, Oracle Analytics and Power BI, and the metric governance that stops dashboards disagreeing.</p></div>
      <div class="card card-accent k-plum"><h3>Machine learning</h3><p>Feature pipelines, training workflows, MLOps and retrieval systems — built by people who ship models, not only notebooks.</p></div>
      <div class="card card-accent k-indigo"><h3>Governance &amp; data quality</h3><p>Lineage, cataloguing, quality enforcement and the evidence trail an auditor or regulator will eventually ask for.</p></div>
      <div class="card card-accent k-deep"><h3>Platform security</h3><p>Access control design, encryption and key management, secrets, and audit logging for the data estate.</p></div>
    </div>
    <div class="callout mt6"><b>Who you actually speak to.</b> Every call is with a hands-on engineer from the team that would do the work — someone who reads execution plans and writes the code, not an account manager relaying questions back to a delivery team. The principal reviews every project regardless of who leads it.</div>
  </div>
</section>

<section class="wrap section">
  <div class="rv">
    <h2 class="mb5">How a distributed practice works</h2>
    <div class="grid c2">
      <div class="card card-accent k-emerald"><h3>Weekly written update</h3><p>Every Friday from the engineer leading your work: what shipped, what is next, what is blocked, and any change to the estimate — in writing, so it survives being forwarded to your board.</p></div>
      <div class="card card-accent k-indigo"><h3>Working sessions, not status calls</h3><p>Calls are for decisions and joint work. Status arrives in writing beforehand so the call is not spent reading it aloud.</p></div>
      <div class="card card-accent k-gold"><h3>Your tools</h3><p>The team works in your Slack, your Jira, your repository and your cloud account, with access provisioned at least privilege and revoked on handover.</p></div>
      <div class="card card-accent k-coral"><h3>Handover as a piece of work</h3><p>Documentation, runbooks and decision records, plus a live session between your engineers and ours — so the work outlives the project.</p></div>
    </div>
  </div>
</section>
""" + cta("Work with the engineers, not the org chart.",
          "One paragraph about what is broken is enough to start.",
          secondary=("Read the insights", "/blog/"))

write("about", layout("/about/", "About — Intellora Tech",
                      "A distributed engineering practice of specialists across data, cloud, AI and "
                      "security, led by a principal engineer and delivering worldwide.",
                      about, accent="emerald", nav_key="About", crumbs=[("About", None)]))

# --------------------------------------------------------------------- contact
contact = f"""
<section class="wrap page-head">
  <p class="eyebrow">Book a call</p>
  <h1>Two ways to start.</h1>
  <p class="lead">Both are with a hands-on engineer — someone who writes the code, not a salesperson. Pick whichever fits where you are.</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <div class="card card-accent k-emerald rv" style="padding:var(--s6)">
      <p class="mono">Free · {INTRO_MINS} minutes</p>
      <h3>Intro call</h3>
      <p style="font-size:var(--t-bd)">Tell us what is broken. We tell you whether we are the right people, roughly what it would cost, and what we would do first. If we are not right for it, we say so and point you somewhere better.</p>
      <p class="mt4"><b class="ui">Good for:</b> <span class="soft">working out whether to take this further at all.</span></p>
      <div class="row mt5">
        <a href="mailto:{EMAIL}?subject=Intro%20call%20request" class="btn btn-p">Book the free call <span class="ar" aria-hidden="true">→</span></a>
      </div>
    </div>

    <div class="card card-accent k-gold rv" style="padding:var(--s6)">
      <p class="mono">USD {CONSULT_FEE} · 60 minutes</p>
      <h3>Technical consultation</h3>
      <p style="font-size:var(--t-bd)">A working session, not a sales call. We look at your actual setup — schemas, pipelines, cloud bill, whatever is relevant — and you leave with specific answers and a written summary of what we found and what we would do about it.</p>
      <p class="mt4"><b class="ui">Free if you hire us:</b> <span class="soft">the full fee comes off your first invoice.</span></p>
      <div class="row mt5">
        <a href="/payment/?amount={CONSULT_FEE}&amp;for=Technical+consultation+%2860+minutes%29" class="btn btn-p">Book and pay <span class="ar" aria-hidden="true">→</span></a>
        <a href="mailto:{EMAIL}?subject=Technical%20consultation" class="btn btn-s">Ask first</a>
      </div>
    </div>
  </div>
  <div class="callout mt6"><b>Why the paid session has a price at all.</b> An hour of senior engineering time spent reading your systems properly is worth more to you than a free chat, and charging for it means we prepare for it. Independent senior data engineers typically charge USD 150–350 an hour; we sit in the middle of that, and give it back if you go ahead.</div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <h2 class="mb5">How to reach us</h2>
      <div class="rows">
        <div><div><p class="n">Email</p><p class="m">Replies within one business day</p></div><p class="d"><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
        <div><div><p class="n">Structure</p><p class="m">Specialists matched to your stack</p></div><p class="d">Distributed team</p></div>
        <div><div><p class="n">Working hours</p><p class="m">Calls scheduled in your timezone</p></div><p class="d">Your business hours</p></div>
        <div><div><p class="n">Languages</p><p class="m">Delivery and documentation</p></div><p class="d">English</p></div>
        <div><div><p class="n">Payments</p><p class="m">Card, or bank transfer</p></div><p class="d"><a href="/payment/">Payments</a></p></div>
      </div>
    </div>
    <div class="rv">
      <h2 class="mb5">What happens on the free call</h2>
      <ul class="svc">
        <li><b>First few minutes · What is broken</b><span>You describe the problem. We ask who it hurts and what it costs every month it continues.</span></li>
        <li><b>Middle · What you already have</b><span>What data exists, how it is organised, and what state the systems are in. This is what moves the price most, so we ask early.</span></li>
        <li><b>Then · Money and order of work</b><span>Whether your budget and our price are in the same range, and what should be done first.</span></li>
        <li><b>Last few minutes · A straight answer</b><span>Whether we can help, who would lead it, what we would suggest, and when you would get it in writing.</span></li>
      </ul>
      <div class="callout mt6"><b>Bring nothing prepared.</b> An architecture diagram or a recent cloud bill speeds things up, but the call works fine without either.</div>
      <div class="callout mt5"><b>We run three projects at a time.</b> If they are all full when you write, we will say so on the call and give you a real start date rather than taking the work and spreading ourselves thin.</div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="rv narrow">
    <h2 class="mb5">Before you write</h2>
    <div class="rows">
      <div><div><p class="n">What should a first email say?</p><p class="m">One paragraph on the problem, roughly what you run it on, and any deadline. Nothing formal.</p></div></div>
      <div><div><p class="n">Will you sign an NDA before we talk?</p><p class="m">Yes — standard mutual NDAs usually within a day.</p></div></div>
      <div><div><p class="n">Do you charge for the call?</p><p class="m">The 15-minute intro call is free. The 60-minute technical session is USD 250, and it comes off your first invoice if you hire us.</p></div></div>
      <div><div><p class="n">How do payments work?</p><p class="m">Invoices in USD, EUR, GBP or AED, paid by card or bank transfer. Usually half up front on a first project.</p></div></div>
    </div>
  </div>
</section>
""" + cta("Tell us what is broken.",
          "One paragraph is enough. You will hear back within one business day.",
          primary=("Email us", "mailto:%s?subject=Discovery%%20call%%20request" % EMAIL),
          secondary=("Pay an invoice", "/payment/"))

write("contact", layout("/contact/", "Contact — Intellora Tech",
                        "Two ways to start: a free 15-minute intro call, or a paid 60-minute technical session with a "
                        "senior engineer, refunded against your first invoice.",
                        contact, accent="emerald", crumbs=[("Contact", None)]))

# --------------------------------------------------------------------- payment
payment = f"""
<section class="wrap page-head">
  <p class="eyebrow">Secure payment</p>
  <h1>Pay securely by card.</h1>
  <p class="lead">For paying an invoice, a deposit, or a booked technical session. Payment happens on Stripe's own page — your card number is typed there, never here.</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <div class="rv">
      <div class="card" style="padding:var(--s6)">
        <form id="pay-form" novalidate>
          <div id="pay-err" class="alert" role="alert" hidden></div>

          <div class="field">
            <label for="pay-amount">Amount (USD)</label>
            <input type="number" id="pay-amount" name="amount" min="1" max="250000" step="0.01" inputmode="decimal" placeholder="1500.00" required>
            <span class="hint">The figure on your invoice, proposal, or USD 250 for a technical session.</span>
          </div>

          <div class="field">
            <label for="pay-reference">Invoice or reference number</label>
            <input type="text" id="pay-reference" name="reference" maxlength="100" placeholder="INV-0042">
          </div>

          <div class="field">
            <label for="pay-description">What this payment is for</label>
            <input type="text" id="pay-description" name="description" maxlength="200" placeholder="Deposit — data platform build">
          </div>

          <button type="submit" id="pay-btn" class="btn btn-p" style="width:100%;justify-content:center">Pay with Visa / Mastercard <span class="ar" aria-hidden="true">→</span></button>

          <noscript><div class="callout mt5">This page needs JavaScript to open a secure checkout session. Email <a href="mailto:{EMAIL}">{EMAIL}</a> to arrange payment another way.</div></noscript>

          <div class="trust">
            <span>🔒 TLS encrypted</span>
            <span>Processed by Stripe · PCI DSS Level 1</span>
            <span>Visa · Mastercard · Amex</span>
          </div>
        </form>
      </div>
    </div>

    <div class="rv">
      <h2 class="mb5">How this works</h2>
      <ul class="svc">
        <li><b>1 · Enter the amount</b><span>Use the figure from your invoice or written proposal, and add the reference so we can match the payment.</span></li>
        <li><b>2 · You are redirected to Stripe</b><span>Card number, expiry and CVC are entered on Stripe's own page, over a connection Stripe controls end to end.</span></li>
        <li><b>3 · Instant confirmation</b><span>You return here with an on-screen confirmation, and Stripe emails your receipt automatically.</span></li>
      </ul>
      <div class="callout mt6"><b>Why we never take card numbers directly.</b> Routing payment through Stripe's hosted checkout keeps Intellora Tech out of PCI-DSS scope entirely — the same standard used by companies far larger than us.</div>
    </div>
  </div>
</section>
"""

write("payment", layout("/payment/", "Pay an invoice — Intellora Tech",
                        "Pay an invoice, deposit or booked technical session securely by Visa or Mastercard.",
                        payment, accent="emerald", nav_key="Payments", crumbs=[("Payments", None)]))

success = """
<section class="wrap page-head ctr">
  <p class="eyebrow" style="margin-inline:auto">Payment received</p>
  <h1 style="max-width:20ch;margin-inline:auto">Thank you — that is settled.</h1>
  <p class="lead" style="margin-inline:auto">Stripe has processed your card payment and emailed your receipt. We will be in touch shortly to confirm next steps.</p>
  <p id="confirm-box" class="mono mt5" hidden style="color:var(--accent)"></p>
  <div class="row mt6" style="justify-content:center">
    <a href="/" class="btn btn-p">Back to home</a>
    <a href="/contact/" class="btn btn-s">Contact us</a>
  </div>
</section>
"""
write("payment/success", layout("/payment/success/", "Payment received — Intellora Tech",
                                "Your payment to Intellora Tech has been received.",
                                success, accent="emerald", noindex=True))

cancel = """
<section class="wrap page-head ctr">
  <p class="eyebrow" style="margin-inline:auto">Payment cancelled</p>
  <h1 style="max-width:20ch;margin-inline:auto">No charge was made.</h1>
  <p class="lead" style="margin-inline:auto">You can try again whenever you are ready, or email us if something went wrong along the way.</p>
  <div class="row mt6" style="justify-content:center">
    <a href="/payment/" class="btn btn-p">Try again</a>
    <a href="/contact/" class="btn btn-s">Contact us</a>
  </div>
</section>
"""
write("payment/cancel", layout("/payment/cancel/", "Payment cancelled — Intellora Tech",
                               "Your payment was cancelled and no charge was made.",
                               cancel, accent="emerald", noindex=True))

# ------------------------------------------------------------- sitemap & robots
urls = ["/", "/products/", "/projects/", "/blog/", "/about/", "/contact/", "/payment/",
        "/tools/", "/tools/estimator/", "/tools/maturity/"]
urls += ["/products/%s/" % s for s, _, _, _ in PRODUCTS]
urls += ["/blog/%s/" % p["slug"] for p in POSTS]

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += "".join("  <url><loc>%s%s</loc></url>\n" % (SITE, u) for u in urls)
sitemap += "</urlset>\n"
with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
    fh.write(sitemap)
print("wrote sitemap.xml")

with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as fh:
    fh.write("User-agent: *\nAllow: /\nDisallow: /payment/success/\nDisallow: /payment/cancel/\n\nSitemap: %s/sitemap.xml\n" % SITE)
print("wrote robots.txt")

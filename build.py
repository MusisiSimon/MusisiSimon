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
EMAIL = "support@intelloratech.net"

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
    ("Products", "Produits", "/products/"),
    ("Projects", "Projets", "/projects/"),
    ("Tools", "Outils", "/tools/"),
    ("Blog", "Blog", "/blog/"),
    ("About", "À propos", "/about/"),
    ("Payments", "Paiements", "/payment/"),
]

# What a 60-minute technical consultation costs, and the free intro that
# precedes it. Senior data-architecture consulting sits at roughly
# USD 150-350 an hour; 250 is mid-range and credited back on signing.
CONSULT_FEE = 250
INTRO_MINS = 15


# ------------------------------------------------------------------- i18n
# Bilingual helpers. A plain string is English-only (falls back to itself
# in French); an (en, fr) tuple carries a real translation. `bi()` renders
# a leaf text node (no nested tags) that site.js swaps via data-en/data-fr.
# `blocks()` wraps two fully-built HTML fragments so JS can toggle whichever
# one matches the active language; used for larger, structurally-mirrored
# page content where tagging every leaf node would be impractical.
def esc(s):
    return s.replace('"', "&quot;")


def pair(t):
    return t if isinstance(t, tuple) else (t, t)


def bi(t, tag="span", cls=None, extra=""):
    en, fr = pair(t)
    c = ' class="%s"' % cls if cls else ""
    return '<%s%s data-en="%s" data-fr="%s"%s>%s</%s>' % (tag, c, esc(en), esc(fr), extra, en, tag)


def blocks(html_en, html_fr):
    return ('<div class="i18n" lang="en">%s</div>'
            '<div class="i18n" lang="fr" hidden>%s</div>') % (html_en, html_fr)


BTN_FR = {
    "Book a call": "Réserver un appel",
    "Estimate the cost": "Estimer le coût",
    "Run the health check": "Lancer le diagnostic",
    "See what we sell": "Voir nos offres",
    "Read the insights": "Lire les articles",
    "Pay an invoice": "Payer une facture",
    "Email us": "Nous écrire",
    "See our projects": "Voir nos projets",
    "About the practice →": "La pratique →",
    "See the products": "Voir les produits",
}


def a_btn(href, label, cls="btn btn-p", arrow=False):
    en, fr = pair(label)
    fr = BTN_FR.get(en, fr) if fr == en else fr
    ar = ' <span class="ar" aria-hidden="true">→</span>' if arrow else ""
    return '<a href="%s" class="%s"><span data-en="%s" data-fr="%s">%s</span>%s</a>' % (
        href, cls, esc(en), esc(fr), en, ar)

PRODUCTS = [
    ("analytics-bi", "Analytics &amp; BI", "Analytique &amp; BI", "emerald",
     "Numbers your board can act on without arguing about them first.",
     "Des chiffres que votre comité de direction peut exploiter sans d'abord se disputer à leur sujet."),
    ("data-governance", "Data Governance", "Gouvernance des données", "indigo",
     "Evidence you can produce in minutes, not weeks.",
     "Des preuves que vous pouvez produire en quelques minutes, et non en semaines."),
    ("security", "Security &amp; Data Protection", "Sécurité &amp; Protection des données", "deep",
     "Security designed into the platform, not bolted on after the finding.",
     "Une sécurité conçue dans la plateforme, et non ajoutée après le constat d'audit."),
    ("ai-machine-learning", "AI &amp; Machine Learning", "IA &amp; Machine Learning", "plum",
     "Models that reach production, on data you can defend.",
     "Des modèles qui atteignent la production, sur des données que vous pouvez défendre."),
    ("database-engineering", "Database Engineering", "Ingénierie des bases de données", "coral",
     "The deepest part of our practice.",
     "Le socle historique de notre pratique."),
    ("aws-cloud", "AWS Cloud Architecture", "Architecture cloud AWS", "gold",
     "Architecture you can defend, and a bill you can predict.",
     "Une architecture que vous pouvez défendre, et une facture que vous pouvez prévoir."),
    ("project-delivery", "Project &amp; Delivery Management", "Gestion de projet &amp; de livraison", "slate",
     "The discipline that makes the other six land on time and on budget.",
     "La discipline qui permet aux six autres d'être livrés à temps et dans le budget."),
]

POSTS = [
    {
        "slug": "why-two-dashboards-disagree",
        "title": "Why your two dashboards disagree",
        "title_fr": "Pourquoi vos deux tableaux de bord se contredisent",
        "date": "2026-02-18",
        "date_h": "18 February 2026",
        "date_h_fr": "18 février 2026",
        "cat": "Analytics",
        "cat_fr": "Analytique",
        "mins": 6,
        "excerpt": "Nearly every reporting dispute is a definition dispute wearing a "
                   "technical costume. Here is how to find the real disagreement and end it.",
        "excerpt_fr": "Presque tous les désaccords de reporting sont des désaccords de définition déguisés en "
                      "problème technique. Voici comment trouver le vrai désaccord et y mettre fin.",
    },
    {
        "slug": "database-cost-audit",
        "title": "The database bill nobody audits",
        "title_fr": "La facture de base de données que personne n'audite",
        "date": "2026-01-27",
        "date_h": "27 January 2026",
        "date_h_fr": "27 janvier 2026",
        "cat": "Databases",
        "cat_fr": "Bases de données",
        "mins": 7,
        "excerpt": "Most cloud database overspend is not a pricing problem. It is five "
                   "specific query patterns, and each one is cheaper to fix than to host.",
        "excerpt_fr": "La plupart des dépassements de coûts des bases de données cloud ne sont pas un problème "
                      "de tarification. Ce sont cinq schémas de requêtes précis, chacun moins coûteux à corriger qu'à héberger.",
    },
    {
        "slug": "ml-production-readiness",
        "title": "What has to be true before a model ships",
        "title_fr": "Ce qui doit être vrai avant qu'un modèle parte en production",
        "date": "2025-12-09",
        "date_h": "9 December 2025",
        "date_h_fr": "9 décembre 2025",
        "cat": "AI & ML",
        "cat_fr": "IA & ML",
        "mins": 8,
        "excerpt": "Models rarely fail in the notebook. They fail at the boundary between "
                   "training data and the real world: a data engineering problem, not a modelling one.",
        "excerpt_fr": "Les modèles échouent rarement dans le notebook. Ils échouent à la frontière entre les "
                      "données d'entraînement et le monde réel : un problème d'ingénierie des données, pas de modélisation.",
    },
    {
        "slug": "sprint-board-vs-steering-pack",
        "title": "Why the sprint board and the steering pack never agree",
        "title_fr": "Pourquoi le tableau de sprint et le rapport de pilotage ne s'accordent jamais",
        "date": "2026-03-10",
        "date_h": "10 March 2026",
        "date_h_fr": "10 mars 2026",
        "cat": "Delivery",
        "cat_fr": "Livraison",
        "mins": 7,
        "excerpt": "A sprint board and a steering pack can both be accurate and still describe two "
                   "different projects. The gap between them is a methodology choice, not a communication problem.",
        "excerpt_fr": "Un tableau de sprint et un rapport de pilotage peuvent tous deux être exacts et pourtant "
                      "décrire deux projets différents. L'écart entre les deux est un choix de méthodologie, pas un problème de communication.",
    },
]


def layout(path, title, desc, body, accent="emerald", nav_key=None, crumbs=None, noindex=False):
    canonical = SITE + path
    nav_html = "".join(
        '<a href="%s"%s><span data-en="%s" data-fr="%s">%s</span></a>' % (
            href, ' aria-current="page"' if label_en == nav_key else "", esc(label_en), esc(label_fr), label_en)
        for label_en, label_fr, href in NAV
    )
    mobile_html = "".join(
        '<a href="%s"><span data-en="%s" data-fr="%s">%s</span></a>' % (href, esc(label_en), esc(label_fr), label_en)
        for label_en, label_fr, href in NAV
    )

    crumb_html = ""
    if crumbs:
        parts = ['<a href="/">%s</a>' % bi(("Home", "Accueil"))]
        for label, href in crumbs:
            label_en, label_fr = pair(label)
            parts.append('<span aria-hidden="true">/</span>')
            inner = bi((label_en, label_fr))
            parts.append('<a href="%s">%s</a>' % (href, inner) if href else "<span>%s</span>" % inner)
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
<script src="/assets/lang.js"></script>
</head>
<body data-accent="{accent}">
<a class="skip" href="#main">Skip to content</a>

<header class="hdr">
  <div class="wrap hdr-in">
    <a href="/" class="brand">{MARK}Intellora Tech</a>
    <nav class="nav" aria-label="Primary">{nav_html}</nav>
    <div class="hdr-act">
      <button class="icon-btn lang-btn" id="langBtn" type="button" data-aria-en="Switch to French" data-aria-fr="Passer à l'anglais" aria-label="Switch to French">
        <span data-en="FR" data-fr="EN">FR</span>
      </button>
      <button class="icon-btn" id="theme" type="button" aria-label="Switch theme">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      </button>
      {a_btn("/contact/", "Book a call")}
      <button class="burger" id="burger" type="button" data-aria-en="Open menu" data-aria-fr="Ouvrir le menu" aria-label="Open menu" aria-expanded="false" aria-controls="mobile"><i></i><i></i><i></i></button>
    </div>
  </div>
  <div class="mobile" id="mobile">
    {mobile_html}
    <a href="/tools/estimator/">{bi(("Price estimator", "Estimateur de prix"))}</a>
    {a_btn("/contact/", "Book a call")}
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
        <p class="ft-about">{bi(("A practice of specialists across data engineering, cloud architecture, governance, security, machine learning and databases, led by a principal engineer.",
                                  "Une pratique de spécialistes en ingénierie des données, architecture cloud, gouvernance, sécurité, machine learning et bases de données, dirigée par un ingénieur principal."))}</p>
        <p class="mt4"><a href="mailto:{EMAIL}">{EMAIL}</a><br>{bi(("Distributed team · delivery worldwide", "Équipe distribuée · livraison dans le monde entier"))}</p>
      </div>
      <div>
        <h2>{bi(("Products", "Produits"))}</h2>
        <ul>{"".join('<li><a href="/products/%s/">%s</a></li>' % (s, bi((n, nf))) for s, n, nf, _, _, _ in PRODUCTS)}</ul>
      </div>
      <div>
        <h2>{bi(("Explore", "Explorer"))}</h2>
        <ul>
          <li><a href="/projects/">{bi(("Projects", "Projets"))}</a></li>
          <li><a href="/blog/">Blog</a></li>
          <li><a href="/tools/estimator/">{bi(("Price estimator", "Estimateur de prix"))}</a></li>
          <li><a href="/tools/maturity/">{bi(("Data health check", "Diagnostic des données"))}</a></li>
        </ul>
      </div>
      <div>
        <h2>{bi(("Company", "Entreprise"))}</h2>
        <ul>
          <li><a href="/about/">{bi(("About", "À propos"))}</a></li>
          <li><a href="/contact/">{bi(("Contact", "Contact"))}</a></li>
          <li><a href="/payment/">{bi(("Payments", "Paiements"))}</a></li>
        </ul>
      </div>
    </div>
    <div class="ft-b"><span>© 2026 Intellora Tech</span><span>{bi(("A distributed practice · delivered worldwide", "Une pratique distribuée · livrée dans le monde entier"))}</span></div>
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
    sec = a_btn(secondary[1], secondary[0], cls="btn btn-s") if secondary else ""
    return f"""
<section class="wrap section">
  <div class="section-tint ctr rv">
    <h2 style="max-width:22ch;margin-inline:auto">{bi(title)}</h2>
    <p class="lead" style="margin-inline:auto">{bi(text)}</p>
    <div class="row ctr mt5" style="justify-content:center">
      {a_btn(primary[1], primary[0], cls="btn btn-p", arrow=True)}
      {sec}
    </div>
  </div>
</section>"""


# ----------------------------------------------------------------- home
home_en = """
<section class="wrap page-head">
  <div class="hero">
    <div>
      <p class="eyebrow">A practice of specialists</p>
      <h1>Data platforms that hold up when someone checks the numbers.</h1>
      <p class="lead">We build and fix the systems underneath your reports: databases, data pipelines, cloud setups, and the rules that keep the numbers trustworthy. You speak to a hands-on engineer from the team that will do the work.</p>
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
  <div class="pgfx rv" role="img" aria-label="Animated diagram. Four fragmented data sources (a stale CRM export, a payments ledger with three conflicting schemas, a manual operations spreadsheet and an unindexed object store) flow through a four-stage pipeline of ingest, validate, model and serve. They emerge as a single source of truth with twelve-minute data freshness, ninety-nine point six per cent pipeline reliability and one agreed metric definition. Figures illustrate a representative project.">
    <div class="pgfx-hd">
      <span>pipeline_view: representative project</span>
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
      <h3>Seven products</h3>
      <p>Reporting, governance, security, AI, databases, AWS and delivery. Buy one or several.</p>
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
    <div class="stat rv"><p class="v">7</p><p class="k">Products, sold separately or together</p></div>
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
        <div class="card card-accent k-gold"><h3>We say no more than yes</h3><p>Work outside our depth, undefined scope, or a timeline that would force shortcuts: declined, with a suggestion of who is better placed.</p></div>
        <div class="card card-accent k-indigo"><h3>Narrow scope, finished properly</h3><p>A tightly drawn project delivered completely beats a broad one delivered to eighty per cent. Scope is fixed at signature and changes are quoted before work starts.</p></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="orbit-w rv">
    <div class="orbit" role="img" aria-label="Diagram showing Intellora Tech at the centre of two rotating rings. The inner ring holds the seven products: analytics and business intelligence, governance, security, artificial intelligence and machine learning, database engineering, AWS cloud architecture, and project and delivery management. The outer ring holds representative services including ETL and ELT pipelines, lineage tracing, feature pipelines, access control design, Oracle Analytics, Oracle Data Integrator, cost optimisation, semantic modelling, MLOps, performance tuning and PRINCE2/Agile/PMBOK delivery frameworks.">
      <div class="orb-halo" aria-hidden="true"></div>
      <div class="orb-core"><b>Intellora<br>Tech</b><i>7 products</i></div>
      <div class="ring ring1">
        <div class="onode p-analytics" style="--a:0deg"><div class="ospin"><div class="opill">Analytics &amp; BI</div></div></div>
        <div class="onode p-governance" style="--a:51.4deg"><div class="ospin"><div class="opill">Governance</div></div></div>
        <div class="onode p-security" style="--a:102.9deg"><div class="ospin"><div class="opill">Security</div></div></div>
        <div class="onode p-ai" style="--a:154.3deg"><div class="ospin"><div class="opill">AI &amp; ML</div></div></div>
        <div class="onode p-database" style="--a:205.7deg"><div class="ospin"><div class="opill">Databases</div></div></div>
        <div class="onode p-cloud" style="--a:257.1deg"><div class="ospin"><div class="opill">AWS Cloud</div></div></div>
        <div class="onode p-delivery" style="--a:308.6deg"><div class="ospin"><div class="opill">Delivery &amp; PM</div></div></div>
      </div>
      <div class="ring ring2">
        <div class="onode" style="--a:0deg"><div class="ospin"><div class="opill">ETL &amp; ELT</div></div></div>
        <div class="onode" style="--a:32.7deg"><div class="ospin"><div class="opill">Lineage tracing</div></div></div>
        <div class="onode" style="--a:65.5deg"><div class="ospin"><div class="opill">Access control</div></div></div>
        <div class="onode" style="--a:98.2deg"><div class="ospin"><div class="opill">Feature pipelines</div></div></div>
        <div class="onode" style="--a:130.9deg"><div class="ospin"><div class="opill">MLOps</div></div></div>
        <div class="onode" style="--a:163.6deg"><div class="ospin"><div class="opill">Oracle Data Integrator</div></div></div>
        <div class="onode" style="--a:196.4deg"><div class="ospin"><div class="opill">Performance tuning</div></div></div>
        <div class="onode" style="--a:229.1deg"><div class="ospin"><div class="opill">Cost optimisation</div></div></div>
        <div class="onode" style="--a:261.8deg"><div class="ospin"><div class="opill">Oracle Analytics</div></div></div>
        <div class="onode" style="--a:294.5deg"><div class="ospin"><div class="opill">Semantic modelling</div></div></div>
        <div class="onode" style="--a:327.3deg"><div class="ospin"><div class="opill">PRINCE2 / Agile / PMBOK</div></div></div>
      </div>
    </div>
    <p class="orb-cap">Seven products · one team · you speak to the engineers who build it</p>
  </div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <h2>What we are best at</h2>
      <p class="lead">Full-stack data engineering: Oracle and cloud-native databases, AWS architecture, the pipelines that move data and the dashboards that turn it into something a board can act on. The toolset flexes to whatever your platform already runs on; the standard does not.</p>
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
"""

home_fr = """
<section class="wrap page-head">
  <div class="hero">
    <div>
      <p class="eyebrow">Une pratique de spécialistes</p>
      <h1>Des plateformes de données qui tiennent la route quand quelqu'un vérifie les chiffres.</h1>
      <p class="lead">Nous construisons et réparons les systèmes derrière vos rapports : bases de données, pipelines de données, configurations cloud, et les règles qui rendent les chiffres fiables. Vous parlez à un ingénieur opérationnel de l'équipe qui fera le travail.</p>
      <div class="row mt6">
        <a href="/contact/" class="btn btn-p">Réserver un appel <span class="ar" aria-hidden="true">→</span></a>
        <a href="/tools/estimator/" class="btn btn-s">Estimer le coût</a>
      </div>
    </div>
    <aside class="panel">
      <p class="mono mb4">En un coup d'œil</p>
      <div class="rows">
        <div><div><p class="n">Structure</p></div><p class="d">Spécialistes distribués</p></div>
        <div><div><p class="n">Livraison</p></div><p class="d">À distance, dans le monde entier</p></div>
        <div><div><p class="n">Première réponse</p></div><p class="d">Un jour ouvré</p></div>
        <div><div><p class="n">Tarification</p></div><p class="d">Fixée à la signature</p></div>
        <div><div><p class="n">Appel d'introduction</p></div><p class="d">Gratuit · 15 minutes</p></div>
        <div><div><p class="n">Session approfondie</p></div><p class="d">250 USD · 60 minutes</p></div>
      </div>
    </aside>
  </div>
</section>

<section class="wrap mb6">
  <div class="pgfx rv" role="img" aria-label="Diagramme animé. Quatre sources de données fragmentées (un export CRM obsolète, un registre de paiements avec trois schémas contradictoires, une feuille de calcul opérationnelle manuelle et un stockage d'objets non indexé) traversent un pipeline en quatre étapes : ingestion, validation, modélisation et mise à disposition. Elles ressortent comme une source unique de vérité avec une fraîcheur des données de douze minutes, une fiabilité de pipeline de quatre-vingt-dix-neuf virgule six pour cent et une définition d'indicateur convenue. Les chiffres illustrent un projet représentatif.">
    <div class="pgfx-hd">
      <span>pipeline_view : projet représentatif</span>
      <span class="lv"><span class="dot-live"></span>en cours</span>
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
        <div class="pcol-l">Avant <em>· 4 sources, 0 contrats</em></div>
        <div class="src"><span class="sd"></span><span class="sn">Export CRM</span><span class="sm">6 j. obsolète</span></div>
        <div class="src"><span class="sd"></span><span class="sn">Registre de paiements</span><span class="sm">3 schémas</span></div>
        <div class="src"><span class="sd"></span><span class="sn">Feuille de calcul</span><span class="sm">manuel</span></div>
        <div class="src"><span class="sd"></span><span class="sn">Stockage d'objets</span><span class="sm">non indexé</span></div>
      </div>
      <div>
        <div class="pipe">
          <div class="pipe-n">Pipeline Intellora</div>
          <div class="pipe-rail"><u></u><i></i><i></i><i></i></div>
          <div class="pipe-st"><b>INGESTION</b><b>VALIDATION</b><b>MODÈLE</b><b>SERVICE</b></div>
          <div class="pipe-tag">gouverné · testé · traçé</div>
        </div>
      </div>
      <div>
        <div class="pcol-l">Après <em class="ok">· 1 source de vérité</em></div>
        <div class="out"><span class="ol">Fraîcheur des données</span><span class="ov">12 min</span></div>
        <div class="out"><span class="ol">Fiabilité du pipeline</span><span class="ov">99,6 %</span></div>
        <div class="out"><span class="ol">Définitions d'indicateurs</span><span class="ov">1 convenue</span></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="grid c3">
    <a href="/products/" class="card card-accent k-emerald rv">
      <p class="mono">Commencer ici</p>
      <h3>Sept produits</h3>
      <p>Reporting, gouvernance, sécurité, IA, bases de données, AWS et gestion de projet. Achetez-en un ou plusieurs.</p>
      <span class="go">Voir les produits →</span>
    </a>
    <a href="/tools/estimator/" class="card card-accent k-gold rv">
      <p class="mono">Deux minutes</p>
      <h3>Estimer le coût</h3>
      <p>Six questions vous donnent une fourchette de prix, un calendrier et une répartition que vous pouvez transmettre.</p>
      <span class="go">Ouvrir l'estimateur →</span>
    </a>
    <a href="/blog/" class="card card-accent k-coral rv">
      <p class="mono">Blog</p>
      <h3>Notes de terrain</h3>
      <p>Ce qui va réellement mal avec les données d'entreprise, écrit à partir de vrais projets plutôt que de théorie.</p>
      <span class="go">Lire le blog →</span>
    </a>
  </div>
</section>

<section class="wrap section">
  <div class="grid c4">
    <div class="stat rv"><p class="v">10+</p><p class="k">Années d'ingénierie des données en production</p></div>
    <div class="stat rv"><p class="v">3</p><p class="k">Projets menés en même temps, au maximum</p></div>
    <div class="stat rv"><p class="v">7</p><p class="k">Produits, vendus séparément ou ensemble</p></div>
    <div class="stat rv"><p class="v">0</p><p class="k">Chargé de compte entre vous et les ingénieurs</p></div>
  </div>
</section>

<section class="wrap section">
  <div class="capacity rv">
    <div class="grid c2" style="align-items:center">
      <div>
        <p class="eyebrow">Délibérément limité</p>
        <h2 style="max-width:18ch">Trois projets à la fois. Jamais quatre.</h2>
        <p class="lead">Ce que nous vendons, c'est une attention de spécialiste indivise, et l'attention ne s'étend pas en acceptant plus de travail. Nous limitons donc le carnet, refusons ce que nous ne pouvons pas faire excellemment, et terminons ce que nous commençons avant d'ouvrir le prochain créneau.</p>
        <p class="mono mt6">Projets que nous pouvons prendre dès maintenant</p>
        <div class="slots" role="img" aria-label="Deux créneaux de projet sur trois actuellement engagés, un disponible.">
          <i></i><i></i><i class="open"></i>
        </div>
        <p class="mono mt4">2 engagés · 1 disponible</p>
      </div>
      <div class="grid" style="gap:var(--s4)">
        <div class="card card-accent k-emerald"><h3>Des spécialistes, pas des généralistes</h3><p>Chaque projet est confié aux personnes dont la profondeur correspond au travail, et le principal relit tout ce qui est livré. Pas d'apprentissage junior sur votre budget.</p></div>
        <div class="card card-accent k-gold"><h3>Nous disons non plus souvent que oui</h3><p>Un travail hors de notre domaine, un périmètre réellement indéfini, ou un calendrier qui forcerait des raccourcis : refusé, avec une suggestion de qui serait mieux placé.</p></div>
        <div class="card card-accent k-indigo"><h3>Périmètre restreint, terminé proprement</h3><p>Un projet étroitement défini et livré complètement vaut mieux qu'un projet large livré à quatre-vingts pour cent. Le périmètre est fixé à la signature et les changements sont chiffrés avant le début du travail.</p></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="orbit-w rv">
    <div class="orbit" role="img" aria-label="Diagramme montrant Intellora Tech au centre de deux anneaux rotatifs. L'anneau intérieur contient les sept produits : analytique et intelligence d'affaires, gouvernance, sécurité, intelligence artificielle et machine learning, ingénierie des bases de données, architecture cloud AWS, et gestion de projet et de livraison. L'anneau extérieur contient des services représentatifs : pipelines ETL et ELT, traçabilité, pipelines de features, conception du contrôle d'accès, Oracle Analytics, Oracle Data Integrator, optimisation des coûts, modélisation sémantique, MLOps, optimisation des performances et cadres de livraison PRINCE2/Agile/PMBOK.">
      <div class="orb-halo" aria-hidden="true"></div>
      <div class="orb-core"><b>Intellora<br>Tech</b><i>7 produits</i></div>
      <div class="ring ring1">
        <div class="onode p-analytics" style="--a:0deg"><div class="ospin"><div class="opill">Analytique &amp; BI</div></div></div>
        <div class="onode p-governance" style="--a:51.4deg"><div class="ospin"><div class="opill">Gouvernance</div></div></div>
        <div class="onode p-security" style="--a:102.9deg"><div class="ospin"><div class="opill">Sécurité</div></div></div>
        <div class="onode p-ai" style="--a:154.3deg"><div class="ospin"><div class="opill">IA &amp; ML</div></div></div>
        <div class="onode p-database" style="--a:205.7deg"><div class="ospin"><div class="opill">Bases de données</div></div></div>
        <div class="onode p-cloud" style="--a:257.1deg"><div class="ospin"><div class="opill">AWS Cloud</div></div></div>
        <div class="onode p-delivery" style="--a:308.6deg"><div class="ospin"><div class="opill">Livraison &amp; PM</div></div></div>
      </div>
      <div class="ring ring2">
        <div class="onode" style="--a:0deg"><div class="ospin"><div class="opill">ETL &amp; ELT</div></div></div>
        <div class="onode" style="--a:32.7deg"><div class="ospin"><div class="opill">Traçabilité</div></div></div>
        <div class="onode" style="--a:65.5deg"><div class="ospin"><div class="opill">Contrôle d'accès</div></div></div>
        <div class="onode" style="--a:98.2deg"><div class="ospin"><div class="opill">Pipelines de features</div></div></div>
        <div class="onode" style="--a:130.9deg"><div class="ospin"><div class="opill">MLOps</div></div></div>
        <div class="onode" style="--a:163.6deg"><div class="ospin"><div class="opill">Oracle Data Integrator</div></div></div>
        <div class="onode" style="--a:196.4deg"><div class="ospin"><div class="opill">Optimisation des performances</div></div></div>
        <div class="onode" style="--a:229.1deg"><div class="ospin"><div class="opill">Optimisation des coûts</div></div></div>
        <div class="onode" style="--a:261.8deg"><div class="ospin"><div class="opill">Oracle Analytics</div></div></div>
        <div class="onode" style="--a:294.5deg"><div class="ospin"><div class="opill">Modélisation sémantique</div></div></div>
        <div class="onode" style="--a:327.3deg"><div class="ospin"><div class="opill">PRINCE2 / Agile / PMBOK</div></div></div>
      </div>
    </div>
    <p class="orb-cap">Sept produits · une équipe · vous parlez aux ingénieurs qui les construisent</p>
  </div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <h2>Ce dans quoi nous excellons</h2>
      <p class="lead">Ingénierie des données de bout en bout : bases de données Oracle et cloud-natives, architecture AWS, les pipelines qui déplacent les données et les tableaux de bord qui les transforment en décisions pour un conseil d'administration. L'outillage s'adapte à votre plateforme existante ; le niveau d'exigence, non.</p>
      <div class="row mt5">
        <a href="/projects/" class="btn btn-s">Voir nos projets</a>
        <a href="/about/" class="btn btn-g">La pratique →</a>
      </div>
    </div>
    <div class="rv">
      <h2>Comment se déroule un projet</h2>
      <div class="rows mt4">
        <div><div><p class="n">Proposition écrite</p><p class="m">Une page : le problème, le travail, le prix, les dates</p></div><p class="d">48 heures</p></div>
        <div><div><p class="n">Prix fixé à la signature</p><p class="m">Tout changement est chiffré avant le début du travail</p></div><p class="d">Toujours</p></div>
        <div><div><p class="n">Mise à jour écrite</p><p class="m">Ce qui est fait, ce qui vient, ce qui est bloqué</p></div><p class="d">Chaque vendredi</p></div>
        <div><div><p class="n">Transfert</p><p class="m">Guides, décisions écrites, une session en direct</p></div><p class="d">Dernière semaine</p></div>
      </div>
    </div>
  </div>
</section>
"""

home = blocks(home_en, home_fr) + cta(
    ("Tell us what is broken.", "Dites-nous ce qui ne va pas."),
    ("One paragraph is enough. You will hear back within one working day.",
     "Un paragraphe suffit. Vous aurez une réponse dans un jour ouvré."),
    secondary=("Run the health check", "/tools/maturity/"),
)

write("", layout("/", "Intellora Tech · Data, Cloud &amp; AI Engineering",
                 "A practice of specialists in data engineering, cloud architecture, governance, security and "
                 "machine learning, led by a principal engineer. You speak to hands-on engineers.",
                 home, accent="emerald"))

# ----------------------------------------------------------- capabilities hub
prod_cards = "".join(f"""
    <a href="/products/{slug}/" class="card card-accent k-{colour} rv">
      <p class="mono">{i:02d}</p>
      <h3>{bi((name, name_fr))}</h3>
      <p>{bi((line, line_fr))}</p>
      {bi(("Read more →", "En savoir plus →"), cls="go")}
    </a>""" for i, (slug, name, name_fr, colour, line, line_fr) in enumerate(PRODUCTS, 1))

prod_hub_en = f"""
<section class="wrap page-head">
  <p class="eyebrow">Products</p>
  <h1>Seven products, bought separately or together.</h1>
  <p class="lead">Each one is a complete piece of work on its own. Most clients buy one, see it land, then buy the next.</p>
</section>

<section class="wrap">
  <div class="grid c3">{prod_cards}</div>
</section>"""

prod_hub_fr = f"""
<section class="wrap page-head">
  <p class="eyebrow">Produits</p>
  <h1>Sept produits, achetés séparément ou ensemble.</h1>
  <p class="lead">Chacun est un projet complet en soi. La plupart des clients en achètent un, le voient aboutir, puis achètent le suivant.</p>
</section>

<section class="wrap">
  <div class="grid c3">{prod_cards}</div>
</section>"""

prod_hub = blocks(prod_hub_en, prod_hub_fr) + cta(
    ("Not sure which one you need?", "Vous ne savez pas lequel vous choisir ?"),
    ("The health check takes two minutes and points at what is most likely holding you back.",
     "Le diagnostic prend deux minutes et indique ce qui vous freine le plus probablement."),
    primary=("Run the health check", "/tools/maturity/"),
    secondary=("Book a call", "/contact/"))

write("products", layout("/products/", "Products · Intellora Tech",
                            "Seven products: reporting and BI, data governance, security, AI and machine "
                            "learning, database engineering, AWS cloud work, and project delivery management.",
                            prod_hub, accent="emerald", nav_key="Products",
                            crumbs=[(("Products", "Produits"), None)]))


# --------------------------------------------------------------- pillar pages
HEAD_FR = {
    "What we do": "Ce que nous faisons",
    "Who usually owns the budget": "Qui détient généralement le budget",
    "What triggers the purchase": "Ce qui déclenche l'achat",
}


def product_page(slug, name, colour, accent, headline, intro, services, tech, budget, triggers, tech_label="Technologies"):
    name_en, name_fr = pair(name)
    headline_en, headline_fr = pair(headline)
    intro_en, intro_fr = pair(intro)
    budget_en, budget_fr = pair(budget)
    tech_label_en, tech_label_fr = pair(tech_label)
    chips = "".join('<span class="chip">%s</span>' % t for t in tech)

    def build(name_, headline_, intro_, tech_label_, budget_, i):
        svc = "".join('<li><b>%s</b><span>%s</span></li>' % (pair(t)[i], pair(d)[i]) for t, d in services)
        trg = "".join('<li><b>%s</b></li>' % pair(t)[i] for t in triggers)
        h1, h2, h3 = (HEAD_FR[k] if i else k for k in
                      ("What we do", "Who usually owns the budget", "What triggers the purchase"))
        return f"""
<section class="wrap page-head">
  <p class="eyebrow">{name_}</p>
  <h1>{headline_}</h1>
  <p class="lead">{intro_}</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <div class="rv">
      <h2 class="mb5">{h1}</h2>
      <ul class="svc">{svc}</ul>
    </div>
    <div class="rv">
      <h2 class="mb5">{tech_label_}</h2>
      <div class="chips">{chips}</div>

      <h2 class="mt7 mb4">{h2}</h2>
      <p class="soft">{budget_}</p>

      <h2 class="mt7 mb4">{h3}</h2>
      <ul class="svc">{trg}</ul>
    </div>
  </div>
</section>"""

    body = blocks(build(name_en, headline_en, intro_en, tech_label_en, budget_en, 0),
                  build(name_fr, headline_fr, intro_fr, tech_label_fr, budget_fr, 1)) + cta(
        ("Is this the piece you need?", "Est-ce la pièce qu'il vous faut ?"),
        ("Twenty minutes on a call is usually enough to know whether this is the right starting point.",
         "Vingt minutes au téléphone suffisent généralement à savoir si c'est le bon point de départ."),
        secondary=("Estimate the cost", "/tools/estimator/"))
    write("products/" + slug,
          layout("/products/%s/" % slug, "%s · Intellora Tech" % re.sub("&amp;", "&", name_en),
                 intro_en[:155], body, accent=accent, nav_key="Products",
                 crumbs=[(("Products", "Produits"), "/products/"), ((name_en, name_fr), None)]))


product_page(
    "analytics-bi", ("Analytics &amp; BI", "Analytique &amp; BI"), "emerald", "emerald",
    ("Numbers your board can act on without arguing about them first.",
     "Des chiffres que votre comité de direction peut exploiter sans d'abord s'en disputer."),
    ("Most reporting problems are definition problems wearing a technical costume. We model each metric once, govern the definition, and build the reporting layer on top of it, so the argument moves from whose number is right to what to do about it.",
     "La plupart des problèmes de reporting sont des problèmes de définition déguisés en problème technique. Nous modélisons chaque indicateur une seule fois, en gouvernons la définition, et construisons la couche de reporting par-dessus, afin que le débat porte sur quoi faire plutôt que sur quel chiffre a raison."),
    [(("Semantic modelling &amp; metric governance", "Modélisation sémantique &amp; gouvernance des indicateurs"),
      ("One agreed definition per metric, versioned and consumed everywhere.", "Une définition unique et convenue par indicateur, versionnée et utilisée partout.")),
     (("Oracle Analytics Server design &amp; installation", "Conception &amp; installation d'Oracle Analytics Server"),
      ("Architecture, sizing, installation, RPD modelling, subject areas, security and high availability, including migration from legacy OBIEE.",
       "Architecture, dimensionnement, installation, modélisation RPD, domaines de sujets, sécurité et haute disponibilité, y compris la migration depuis un ancien OBIEE.")),
     (("Power BI &amp; embedded analytics", "Power BI &amp; analytique embarquée"),
      ("Dashboards built around decisions people actually make, and analytics embedded into your own product where that is the requirement.",
       "Des tableaux de bord construits autour des décisions réellement prises, et une analytique embarquée dans votre propre produit lorsque c'est le besoin.")),
     (("Regulatory &amp; management reporting", "Reporting réglementaire &amp; de gestion"),
      ("Reporting pipelines with audit trails, reconciliation controls and defensible lineage for regulators, auditors and boards.",
       "Des pipelines de reporting avec pistes d'audit, contrôles de rapprochement et traçabilité défendable pour les régulateurs, auditeurs et conseils d'administration.")),
     (("Self-service enablement", "Autonomie des utilisateurs"),
      ("Curated datasets, documentation and training so analysts answer their own questions without filing tickets.",
       "Des jeux de données préparés, une documentation et une formation pour que les analystes répondent eux-mêmes à leurs questions sans ouvrir de ticket."))],
    ["Oracle Analytics Server", "Oracle Analytics Cloud", "Power BI", "Tableau", "dbt", "SQL", "Redshift", "Snowflake"],
    ("Head of Data, CDO, or a Finance Director who has lost patience with reconciliation.",
     "Le responsable data, le CDO, ou un directeur financier qui n'a plus la patience pour les rapprochements."),
    [("Two dashboards disagree and nobody can say which is right",
      "Deux tableaux de bord se contredisent et personne ne peut dire lequel a raison"),
     ("A regulator or auditor has asked how a reported figure was derived",
      "Un régulateur ou un auditeur a demandé comment un chiffre publié a été calculé"),
     ("Analysts spend more time assembling data than analysing it",
      "Les analystes passent plus de temps à assembler les données qu'à les analyser")])

product_page(
    "data-governance", ("Data Governance", "Gouvernance des données"), "indigo", "indigo",
    ("Evidence you can produce in minutes, not weeks.",
     "Des preuves que vous pouvez produire en quelques minutes, et non en semaines."),
    ("Governance fails when it is written as policy and never wired into the pipeline. We implement it as running infrastructure: lineage captured automatically, quality enforced at the boundary, ownership recorded where the data lives.",
     "La gouvernance échoue quand elle n'est qu'une politique écrite jamais intégrée au pipeline. Nous l'implémentons comme une infrastructure vivante : la traçabilité est captée automatiquement, la qualité est appliquée à la frontière, et la propriété des données est enregistrée là où elles vivent."),
    [(("Governance frameworks", "Cadres de gouvernance"),
      ("Ownership models, stewardship roles, decision rights and policy grounded in DAMA-DMBOK practice.",
       "Modèles de propriété, rôles de gestionnaire de données, droits de décision et politiques fondés sur la pratique DAMA-DMBOK.")),
     (("Lineage &amp; governance tracing", "Traçabilité &amp; lignage de gouvernance"),
      ("Column-level tracing from source system through every transformation to the final report field, with impact analysis before changes ship.",
       "Traçabilité au niveau colonne depuis le système source jusqu'au champ final du rapport à travers chaque transformation, avec analyse d'impact avant chaque changement.")),
     (("Metadata management &amp; cataloguing", "Gestion des métadonnées &amp; catalogage"),
      ("OpenMetadata and equivalents wired into pipelines so ownership, glossary, freshness and lineage stay current automatically.",
       "OpenMetadata et équivalents intégrés aux pipelines pour que propriété, glossaire, fraîcheur et lignage restent à jour automatiquement.")),
     (("Data quality &amp; observability", "Qualité &amp; observabilité des données"),
      ("Automated validation, schema enforcement, anomaly detection and alerting on data correctness rather than job status alone.",
       "Validation automatisée, application de schéma, détection d'anomalies et alertes sur l'exactitude des données, au-delà du simple statut des jobs.")),
     (("Master data management", "Gestion des données de référence"),
      ("Entity resolution, golden record design and survivorship rules for customers, counterparties, products and locations.",
       "Résolution d'entités, conception du golden record et règles de survivance pour les clients, contreparties, produits et sites.")),
     (("Privacy impact assessment &amp; DPIA", "Analyse d'impact sur la vie privée &amp; AIPD"),
      ("Processing registers, risk scoring, high-risk flagging and retention schedules aligned to GDPR and equivalent regimes.",
       "Registres de traitement, notation du risque, signalement des traitements à haut risque et calendriers de conservation alignés sur le RGPD et régimes équivalents."))],
    ["OpenMetadata", "OpenLineage", "Great Expectations", "dbt tests", "DAMA-DMBOK", "ISO/IEC/IEEE 29148"],
    ("CDO, Chief Risk &amp; Compliance Officer, or a Head of Data preparing for an audit or a funding round.",
     "Le CDO, le directeur des risques et de la conformité, ou un responsable data qui se prépare à un audit ou une levée de fonds."),
    [("An audit, regulator or investor has asked for evidence you cannot assemble quickly",
      "Un audit, un régulateur ou un investisseur a demandé des preuves que vous ne pouvez pas réunir rapidement"),
     ("A schema change broke a downstream report nobody knew existed",
      "Un changement de schéma a cassé un rapport en aval dont personne ne connaissait l'existence"),
     ("New privacy obligations require a defensible processing record",
      "De nouvelles obligations en matière de vie privée exigent un registre de traitement défendable")])

product_page(
    "security", ("Security &amp; Data Protection", "Sécurité &amp; Protection des données"), "deep", "emerald",
    ("Security designed into the platform, not bolted on after the finding.",
     "Une sécurité conçue dans la plateforme, et non ajoutée après le constat d'audit."),
    ("This is data-platform security specifically: how your warehouse, pipelines and analytics layer are protected, segmented, encrypted and evidenced.",
     "Il s'agit ici spécifiquement de la sécurité de la plateforme de données : comment votre entrepôt, vos pipelines et votre couche analytique sont protégés, segmentés, chiffrés et documentés."),
    [(("Data security architecture", "Architecture de sécurité des données"),
      ("Security design for the data platform: trust boundaries, segmentation, data classification and control placement.",
       "Conception de la sécurité pour la plateforme de données : frontières de confiance, segmentation, classification des données et placement des contrôles.")),
     (("Encryption &amp; key management", "Chiffrement &amp; gestion des clés"),
      ("Encryption at rest and in transit, KMS key hierarchy, rotation policy, envelope encryption and field-level protection for sensitive attributes.",
       "Chiffrement au repos et en transit, hiérarchie de clés KMS, politique de rotation, chiffrement enveloppé et protection au niveau champ pour les attributs sensibles.")),
     (("Access control design", "Conception du contrôle d'accès"),
      ("Role-based and attribute-based access control, row and column-level security, least-privilege review and joiner-mover-leaver process for data access.",
       "Contrôle d'accès basé sur les rôles et les attributs, sécurité au niveau ligne et colonne, revue du moindre privilège et processus d'arrivée-mutation-départ pour l'accès aux données.")),
     (("Secrets management", "Gestion des secrets"),
      ("Removing credentials from code and configuration, centralised secrets storage, rotation and short-lived credential patterns.",
       "Suppression des identifiants du code et de la configuration, stockage centralisé des secrets, rotation et schémas d'identifiants de courte durée.")),
     (("Audit logging &amp; evidence", "Journalisation d'audit &amp; preuves"),
      ("Tamper-evident logging of data access and change, retention aligned to your obligations, and query interfaces auditors can actually use.",
       "Journalisation infalsifiable des accès et modifications de données, conservation alignée sur vos obligations, et interfaces de requête réellement utilisables par les auditeurs.")),
     (("Threat modelling &amp; posture review", "Modélisation des menaces &amp; revue de posture"),
      ("Structured threat modelling of the data estate and a prioritised remediation plan, plus incident response runbooks for data exposure scenarios.",
       "Modélisation structurée des menaces du patrimoine de données et un plan de remédiation prioritisé, ainsi que des procédures de réponse aux incidents pour les scénarios d'exposition de données."))],
    ["AWS KMS", "AWS IAM", "Secrets Manager", "CloudTrail", "VPC design", "Lake Formation", "Database-native RLS"],
    ("CISO, Head of Security, or a CTO responding to a customer security questionnaire.",
     "Le RSSI, le responsable sécurité, ou un CTO qui répond à un questionnaire de sécurité client."),
    [("An enterprise customer sent a security questionnaire you cannot pass",
      "Un client grand compte a envoyé un questionnaire de sécurité que vous ne pouvez pas réussir"),
     ("Credentials are sitting in code and nobody is sure where else they are",
      "Des identifiants sont exposés dans le code et personne n'est certain d'où se trouvent les autres"),
     ("You cannot evidence who accessed which data, when",
      "Vous ne pouvez pas prouver qui a accédé à quelles données, et quand")])

product_page(
    "ai-machine-learning", ("AI &amp; Machine Learning", "IA &amp; Machine Learning"), "plum", "plum",
    ("Models that reach production, on data you can defend.",
     "Des modèles qui atteignent la production, sur des données que vous pouvez défendre."),
    ("We approach machine learning from the data side first. Most organisations asking for models actually need the layer underneath fixed, and we will tell you that rather than build something impressive on unreliable inputs.",
     "Nous abordons le machine learning d'abord par les données. La plupart des organisations qui demandent des modèles ont en réalité besoin de réparer la couche sous-jacente, et nous vous le dirons plutôt que de construire quelque chose d'impressionnant sur des données peu fiables."),
    [(("Feature pipelines &amp; feature stores", "Pipelines de features &amp; feature stores"),
      ("Reproducible feature engineering with consistent definitions between training and serving.",
       "Ingénierie de features reproductible avec des définitions cohérentes entre l'entraînement et la mise en service.")),
     (("Model training workflows", "Flux d'entraînement des modèles"),
      ("Versioned, reproducible training with experiment tracking and a registry that records what shipped and why.",
       "Entraînement versionné et reproductible avec suivi des expériences et un registre qui documente ce qui a été mis en production, et pourquoi.")),
     (("MLOps &amp; deployment", "MLOps &amp; déploiement"),
      ("Deployment pipelines, rollback paths, monitoring for drift and degradation, and retraining schedules.",
       "Pipelines de déploiement, chemins de retour en arrière, surveillance de la dérive et de la dégradation, et calendriers de réentraînement.")),
     (("Retrieval-augmented generation", "Génération augmentée par récupération (RAG)"),
      ("Document ingestion, chunking, embedding and retrieval over your own corpus, with evaluation and citation of sources.",
       "Ingestion de documents, découpage, vectorisation et récupération sur votre propre corpus, avec évaluation et citation des sources.")),
     (("AI governance &amp; model risk", "Gouvernance de l'IA &amp; risque modèle"),
      ("Model documentation, lineage from training data to prediction, bias assessment, and the record a regulator will eventually ask for.",
       "Documentation des modèles, traçabilité des données d'entraînement jusqu'à la prédiction, évaluation des biais, et le dossier qu'un régulateur finira par demander."))],
    ["Python", "scikit-learn", "XGBoost", "MLflow", "Amazon SageMaker", "Amazon Bedrock", "Vector stores", "Airflow"],
    ("CTO, Head of Data Science, or a product owner with a use case and no path to production.",
     "Le CTO, le responsable data science, ou un product owner avec un cas d'usage et aucune voie vers la production."),
    [("Models work in notebooks and never ship",
      "Les modèles fonctionnent dans les notebooks et ne partent jamais en production"),
     ("A deployed model has quietly degraded and nobody noticed",
      "Un modèle en production s'est dégradé silencieusement sans que personne ne le remarque"),
     ("An AI initiative was announced before the data layer was ready",
      "Une initiative IA a été annoncée avant que la couche de données ne soit prête")])

product_page(
    "database-engineering", ("Database Engineering", "Ingénierie des bases de données"), "coral", "coral",
    ("The deepest part of our practice.", "Le socle historique de notre pratique."),
    ("Deep production database work across Oracle, PostgreSQL, SQL Server and the cloud-native platforms that have largely replaced them. This is where the fastest wins usually are: tuning a query is almost always cheaper than buying more hardware.",
     "Un travail approfondi sur les bases de données en production, sur Oracle, PostgreSQL, SQL Server et les plateformes cloud-natives qui les ont largement remplacées. C'est souvent là que se trouvent les gains les plus rapides : ajuster une requête coûte presque toujours moins cher qu'acheter du matériel supplémentaire."),
    [(("Logical &amp; physical data modelling", "Modélisation logique &amp; physique des données"),
      ("Conceptual through physical models, normalisation and deliberate denormalisation, dimensional and Data Vault approaches where they fit.",
       "Des modèles conceptuels aux modèles physiques, normalisation et dénormalisation délibérée, approches dimensionnelles et Data Vault lorsqu'elles s'appliquent.")),
     (("Database design &amp; development", "Conception &amp; développement de bases de données"),
      ("Schema design, constraints and referential integrity, stored procedures and packages, across Oracle, PostgreSQL, MySQL and SQL Server.",
       "Conception de schémas, contraintes et intégrité référentielle, procédures stockées et packages, sur Oracle, PostgreSQL, MySQL et SQL Server.")),
     (("Performance tuning", "Optimisation des performances"),
      ("Execution plan analysis, index strategy, statistics management, partitioning and query rewrites.",
       "Analyse des plans d'exécution, stratégie d'indexation, gestion des statistiques, partitionnement et réécriture de requêtes.")),
     (("High availability &amp; recovery", "Haute disponibilité &amp; reprise"),
      ("Replication topology, failover design, backup strategy and tested recovery procedures with real recovery time objectives.",
       "Topologie de réplication, conception du basculement, stratégie de sauvegarde et procédures de reprise testées avec de vrais objectifs de délai de reprise.")),
     (("Migration &amp; upgrade", "Migration &amp; mise à niveau"),
      ("Version upgrades and cross-platform migration with parallel validation and reconciliation before cutover.",
       "Montées de version et migration inter-plateformes avec validation en parallèle et rapprochement avant la bascule.")),
     (("Oracle Data Integrator development", "Développement Oracle Data Integrator"),
      ("ODI mappings, packages, load plans and knowledge module customisation, including remediation of inherited estates.",
       "Mappings ODI, packages, plans de chargement et personnalisation de knowledge modules, y compris la remédiation de patrimoines hérités."))],
    ["Oracle 19c &amp; 23ai", "PostgreSQL", "MySQL", "SQL Server", "MongoDB", "Redis", "Oracle Data Integrator", "Data Vault"],
    ("CTO, VP Engineering, or a Head of Platform whose database has become the bottleneck.",
     "Le CTO, le VP Engineering, ou un responsable plateforme dont la base de données est devenue le goulot d'étranglement."),
    [("Queries that used to take seconds now take minutes",
      "Des requêtes qui prenaient quelques secondes en prennent maintenant plusieurs minutes"),
     ("An unsupported database version is becoming an audit finding",
      "Une version de base de données non supportée devient un constat d'audit"),
     ("Nobody has tested whether the backups actually restore",
      "Personne n'a testé si les sauvegardes se restaurent réellement")])

product_page(
    "aws-cloud", ("AWS Cloud Architecture", "Architecture cloud AWS"), "gold", "gold",
    ("Architecture you can defend, and a bill you can predict.",
     "Une architecture que vous pouvez défendre, et une facture que vous pouvez prévoir."),
    ("Certified on AWS and opinionated about it, while staying vendor-neutral above the platform layer. Most cloud cost problems are architecture problems, which is why the review and the savings work are the same project.",
     "Certifiés sur AWS et convaincus de nos choix, tout en restant neutres au-dessus de la couche plateforme. La plupart des problèmes de coût cloud sont des problèmes d'architecture, c'est pourquoi la revue et le travail d'économies ne font qu'un seul projet."),
    [(("Well-Architected review", "Revue Well-Architected"),
      ("Structured review across operational excellence, security, reliability, performance, cost and sustainability, with a prioritised remediation plan.",
       "Revue structurée couvrant l'excellence opérationnelle, la sécurité, la fiabilité, la performance, le coût et la durabilité, avec un plan de remédiation prioritisé.")),
     (("Landing zone &amp; multi-account design", "Landing zone &amp; conception multi-comptes"),
      ("Account structure, organisational units, guardrails, network topology and centralised logging built for growth.",
       "Structure de comptes, unités organisationnelles, garde-fous, topologie réseau et journalisation centralisée conçus pour la croissance.")),
     (("Cloud migration", "Migration cloud"),
      ("On-premise to AWS planning and execution, including hybrid cutover with shadow validation for low-downtime moves.",
       "Planification et exécution de la migration on-premise vers AWS, y compris une bascule hybride avec validation en miroir pour des transitions à faible interruption.")),
     (("FinOps &amp; cost optimisation", "FinOps &amp; optimisation des coûts"),
      ("Line-by-line spend audit, quick wins implemented during the project, and structural recommendations with quantified savings.",
       "Audit des dépenses ligne par ligne, gains rapides mis en œuvre pendant le projet, et recommandations structurelles avec économies chiffrées.")),
     (("Infrastructure as code", "Infrastructure as code"),
      ("Terraform and CloudFormation provisioning, environment parity, CI/CD for data infrastructure and automated testing.",
       "Provisionnement Terraform et CloudFormation, parité des environnements, CI/CD pour l'infrastructure de données et tests automatisés.")),
     (("Resilience &amp; disaster recovery", "Résilience &amp; reprise après sinistre"),
      ("Recovery objectives agreed with the business, failover design and tested restore procedures.",
       "Objectifs de reprise convenus avec le métier, conception du basculement et procédures de restauration testées."))],
    ["AWS", "Terraform", "CloudFormation", "S3", "Glue", "Redshift", "Lambda", "EKS"],
    ("CTO, Head of Platform, or a Finance lead who has seen the cloud bill trend line.",
     "Le CTO, le responsable plateforme, ou un responsable financier qui a vu la courbe de la facture cloud."),
    [("The monthly bill grows faster than usage does",
      "La facture mensuelle croît plus vite que l'usage"),
     ("A migration has stalled halfway and both estates now need running",
      "Une migration s'est arrêtée à mi-chemin et les deux environnements doivent désormais fonctionner en parallèle"),
     ("Nobody can say what happens if the primary region goes down",
      "Personne ne peut dire ce qui se passe si la région principale tombe en panne")])

product_page(
    "project-delivery", ("Project &amp; Delivery Management", "Gestion de projet &amp; de livraison"), "slate", "slate",
    ("The discipline that makes the other six land on time and on budget.",
     "La discipline qui permet aux six autres d'être livrés à temps et dans le budget."),
    ("Good engineering does not survive bad delivery. We run every project against a named methodology chosen for the shape of the work: PRINCE2 where governance and stage gates matter, Agile and Scrum where the requirement will keep moving, or a PMBOK-aligned blend where part of the programme is fixed and part is exploratory. The method is picked to fit the work, not applied by default.",
     "Une bonne ingénierie ne survit pas à une mauvaise gestion de projet. Nous menons chaque projet selon une méthodologie nommée, choisie pour la nature du travail : PRINCE2 lorsque la gouvernance et les jalons comptent, Agile et Scrum lorsque le besoin va continuer d'évoluer, ou un mélange aligné sur le PMBOK lorsqu'une partie du programme est fixe et une autre exploratoire. La méthode est choisie pour s'adapter au travail, jamais appliquée par défaut."),
    [(("Methodology selection &amp; governance design", "Sélection de la méthodologie &amp; conception de la gouvernance"),
      ("PRINCE2, Agile/Scrum, a PMBOK-aligned waterfall, or a deliberate hybrid, chosen for the project's risk profile and how settled the requirements actually are.",
       "PRINCE2, Agile/Scrum, un cycle en cascade aligné sur le PMBOK, ou un hybride délibéré, choisi selon le profil de risque du projet et le degré de stabilité réel des besoins.")),
     (("Programme &amp; project management office (PMO)", "Bureau de gestion de programme &amp; de projet (PMO)"),
      ("Schedule, budget, RAID log, change control and stage-gate reporting run as a discipline, not bolted onto the engineering work after the fact.",
       "Planning, budget, registre RAID, contrôle des changements et reporting aux jalons gérés comme une discipline à part entière, et non ajoutés après coup au travail d'ingénierie.")),
     (("Agile delivery &amp; Scrum facilitation", "Livraison Agile &amp; facilitation Scrum"),
      ("Sprint planning, backlog ownership, ceremonies and velocity tracking for teams where the requirement is expected to change as the work proceeds.",
       "Planification de sprint, gestion du backlog, cérémonies et suivi de la vélocité pour les équipes où le besoin est appelé à évoluer au fil du travail.")),
     (("Business case &amp; benefits realisation", "Argumentaire économique &amp; réalisation des bénéfices"),
      ("The case for the spend, built to a PMBOK-aligned standard, and the tracking that proves the benefit was actually realised once delivery is over.",
       "La justification de la dépense, construite selon une norme alignée sur le PMBOK, et le suivi qui prouve que le bénéfice a réellement été réalisé une fois la livraison terminée.")),
     (("Stakeholder &amp; steering committee reporting", "Reporting aux parties prenantes &amp; au comité de pilotage"),
      ("The written weekly update and the steering pack, built so a non-technical sponsor or board can follow progress without a translator.",
       "Le point hebdomadaire écrit et le rapport de pilotage, conçus pour qu'un sponsor ou un conseil non technique puisse suivre l'avancement sans traducteur.")),
     (("Risk, issue &amp; change management", "Gestion des risques, des problèmes &amp; des changements"),
      ("A structured RAID log and change-control process, so scope drifts on paper before it drifts in the codebase.",
       "Un registre RAID structuré et un processus de contrôle des changements, pour que la dérive de périmètre apparaisse sur le papier avant d'apparaître dans le code."))],
    ["PRINCE2", "Agile / Scrum", "PMBOK-aligned waterfall", "Hybrid / bimodal delivery", "RAID logs", "Stage-gate governance"],
    ("Programme Director, PMO Lead, or a sponsor who has been burned by a delivery with no paper trail.",
     "Le directeur de programme, le responsable PMO, ou un sponsor qui a déjà souffert d'une livraison sans trace écrite."),
    [("A programme has no single named methodology and everyone is improvising their own",
      "Un programme n'a aucune méthodologie nommée et chacun improvise la sienne"),
     ("The board wants a steering pack and the current update is a Slack thread",
      "Le conseil veut un rapport de pilotage et la mise à jour actuelle est un fil de discussion Slack"),
     ("Requirements are fixed in some areas and volatile in others, and one methodology does not fit both",
      "Les besoins sont figés dans certains domaines et volatils dans d'autres, et une seule méthodologie ne convient pas aux deux")],
    tech_label=("Methodologies", "Méthodologies"))

# -------------------------------------------------------------------- projects
PROJECTS = [
    {
        "name": "National tax administration system rebuild",
        "name_fr": "Refonte du système national d'administration fiscale",
        "colour": "indigo",
        "body": "Set the data quality rules across every old and new system, decided who owns which data, "
                "put lineage and access controls in place, and wrote the plan for moving the data: a "
                "multi-year programme run to a named governance framework rather than by instinct.",
        "body_fr": "Défini les règles de qualité des données sur chaque système, ancien et nouveau, décidé qui "
                   "possède quelles données, mis en place la traçabilité et les contrôles d'accès, et rédigé le "
                   "plan de migration des données : un programme pluriannuel mené selon un cadre de gouvernance "
                   "nommé plutôt qu'à l'instinct.",
        "tags": ["Data governance", "Migration planning", "Programme governance"],
        "tags_fr": ["Gouvernance des données", "Planification de la migration", "Gouvernance de programme"],
    },
    {
        "name": "Data lake house build",
        "name_fr": "Construction d'un data lakehouse",
        "colour": "emerald",
        "body": "Built the pipelines that fill a central data store: Apache Airflow to schedule the work, Kafka "
                "for live data, PySpark for the heavy lifting. Data from several separate systems now lands in "
                "one place that the reports read from.",
        "body_fr": "Construit les pipelines qui alimentent un entrepôt de données central : Apache Airflow pour "
                   "planifier le travail, Kafka pour les données en temps réel, PySpark pour le traitement lourd. "
                   "Les données de plusieurs systèmes distincts arrivent désormais dans un seul endroit que "
                   "lisent les rapports.",
        "tags": ["Airflow", "Kafka", "PySpark", "Power BI"],
        "tags_fr": ["Airflow", "Kafka", "PySpark", "Power BI"],
    },
    {
        "name": "Data warehouse rebuild",
        "name_fr": "Refonte de l'entrepôt de données",
        "colour": "gold",
        "body": "Rebuilt the loading pipelines so they process far more data in the same window, and added "
                "automatic quality checks, alerting and schema enforcement, so a broken load is caught before "
                "it reaches a report rather than after someone queries it.",
        "body_fr": "Reconstruit les pipelines de chargement pour qu'ils traitent bien plus de données dans la "
                   "même fenêtre, et ajouté des contrôles de qualité automatiques, des alertes et l'application "
                   "de schéma, pour qu'un chargement défaillant soit détecté avant d'atteindre un rapport plutôt "
                   "qu'après qu'une requête l'interroge.",
        "tags": ["ELT redesign", "Data quality", "Alerting"],
        "tags_fr": ["Refonte ELT", "Qualité des données", "Alertes"],
    },
    {
        "name": "Core banking database upgrade",
        "name_fr": "Mise à niveau de la base de données bancaire centrale",
        "colour": "coral",
        "body": "Moved core banking and mobile banking databases onto a new Oracle version with no downtime and "
                "no data lost. Performance tuning and stress testing were done on the new setup before anyone "
                "was switched over to it.",
        "body_fr": "Migré les bases de données de banque centrale et de banque mobile vers une nouvelle version "
                   "d'Oracle sans interruption de service et sans perte de données. L'optimisation des "
                   "performances et les tests de charge ont été réalisés sur la nouvelle configuration avant "
                   "toute bascule.",
        "tags": ["Oracle 19c", "Zero downtime", "Performance tuning"],
        "tags_fr": ["Oracle 19c", "Zéro interruption", "Optimisation des performances"],
    },
    {
        "name": "Disaster recovery and emergency failover",
        "name_fr": "Reprise après sinistre et basculement d'urgence",
        "colour": "deep",
        "body": "Designed an Oracle Data Guard cascading standby setup across several recovery sites, then led "
                "the emergency failover that brought a bank back up after a critical infrastructure failure, "
                "with no data lost.",
        "body_fr": "Conçu une configuration de secours en cascade Oracle Data Guard sur plusieurs sites de "
                   "reprise, puis dirigé le basculement d'urgence qui a remis une banque en service après une "
                   "défaillance critique de l'infrastructure, sans perte de données.",
        "tags": ["Data Guard", "Disaster recovery", "Failover"],
        "tags_fr": ["Data Guard", "Reprise après sinistre", "Basculement"],
    },
    {
        "name": "Core banking databases and reporting",
        "name_fr": "Bases de données bancaires centrales et reporting",
        "colour": "emerald",
        "body": "Kept core banking databases fast and available, managed who could reach what, and built the "
                "ETL processes feeding reporting across several business units.",
        "body_fr": "Maintenu les bases de données de banque centrale rapides et disponibles, géré les droits "
                   "d'accès, et construit les processus ETL alimentant le reporting de plusieurs unités métier.",
        "tags": ["Core banking", "ETL", "Access control"],
        "tags_fr": ["Banque centrale", "ETL", "Contrôle d'accès"],
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


def proj_cards_html(i):
    return "".join("""
      <div class="card card-accent k-{colour} rv">
        <h3>{name}</h3>
        <p>{body}</p>
        <div class="chips mt4">{chips}</div>
      </div>""".format(
        colour=p["colour"], name=p["name"] if not i else p["name_fr"], body=p["body"] if not i else p["body_fr"],
        chips="".join('<span class="chip">%s</span>' % t for t in (p["tags"] if not i else p["tags_fr"])))
    for p in PROJECTS)


INDUSTRIES = [
    ("Lending &amp; credit", "Crédit &amp; prêts"), ("Insurance", "Assurance"),
    ("Payments &amp; fintech", "Paiements &amp; fintech"), ("Capital markets", "Marchés de capitaux"),
    ("Logistics &amp; supply chain", "Logistique &amp; chaîne d'approvisionnement"), ("Telecoms", "Télécoms"),
    ("Public sector", "Secteur public"), ("Energy &amp; utilities", "Énergie &amp; services publics"),
    ("Healthcare administration", "Administration de la santé"),
    ("Retail &amp; e-commerce", "Commerce de détail &amp; e-commerce"),
]

projects_en = f"""
<section class="wrap page-head">
  <p class="eyebrow">Projects</p>
  <h1>Work we have actually done.</h1>
  <p class="lead">Real work, described plainly. Each of these was delivered by our people in the roles they held at the time.</p>
</section>

<section class="wrap">
  <div class="grid c2">{proj_cards_html(0)}</div>
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
    <p class="lead">Tax and customs systems, core banking, and humanitarian operations: places where a wrong number has consequences and someone eventually checks. That is the kind of work we are quick at, regulated data, matching numbers that must agree, audit trails, and moves that cannot afford a bad switch-over.</p>
    <p class="mono mt6 mb3">We also work in</p>
    <div class="chips">{"".join('<span class="chip">%s</span>' % t for t, _ in INDUSTRIES)}</div>
  </div>
</section>"""

projects_fr = f"""
<section class="wrap page-head">
  <p class="eyebrow">Projets</p>
  <h1>Le travail que nous avons réellement effectué.</h1>
  <p class="lead">Du travail réel, décrit simplement. Chacun de ces projets a été livré par nos équipes, dans les fonctions qu'elles occupaient à l'époque.</p>
</section>

<section class="wrap">
  <div class="grid c2">{proj_cards_html(1)}</div>
</section>

<section class="wrap section">
  <div class="logo-band rv">
    <p class="mono ctr mb5">Où nos équipes ont livré ce travail</p>
    <div class="logo-wall">{"".join(org_tile(o) for o in ORGS)}</div>
  </div>
</section>

<section class="wrap section">
  <div class="rv narrow">
    <h2 class="mb4">Ce que cela représente</h2>
    <p class="lead">Systèmes fiscaux et douaniers, banque centrale, et opérations humanitaires : des domaines où un chiffre erroné a des conséquences et où quelqu'un finit toujours par vérifier. C'est le type de travail où nous sommes rapides : données réglementées, chiffres qui doivent se recouper, pistes d'audit, et bascules qui ne peuvent pas se permettre d'échouer.</p>
    <p class="mono mt6 mb3">Nous travaillons aussi dans</p>
    <div class="chips">{"".join('<span class="chip">%s</span>' % t for _, t in INDUSTRIES)}</div>
  </div>
</section>"""

projects = blocks(projects_en, projects_fr) + cta(
    ("Have a project like one of these?", "Vous avez un projet comme l'un de ceux-ci ?"),
    ("Tell us what is broken in a paragraph. We will tell you honestly whether we are the right people.",
     "Décrivez-nous en un paragraphe ce qui ne va pas. Nous vous dirons honnêtement si nous sommes les bonnes personnes."),
    secondary=("See what we sell", "/products/"))

write("projects", layout("/projects/", "Projects · Intellora Tech",
                         "Real project work: a national tax administration system rebuild, data lake pipelines, "
                         "a data warehouse rebuild, core banking upgrades, disaster recovery and large-scale "
                         "biometric data operations.",
                         projects, accent="indigo", nav_key="Projects",
                         crumbs=[(("Projects", "Projets"), None)]))


# ------------------------------------------------------------------ tools hub
tools_hub_en = """
<section class="wrap page-head">
  <p class="eyebrow">Tools</p>
  <h1>Two free tools, two minutes each.</h1>
  <p class="lead">Both are free, need no sign-up, and give you something you can act on, or forward to whoever holds the budget.</p>
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
</section>"""

tools_hub_fr = """
<section class="wrap page-head">
  <p class="eyebrow">Outils</p>
  <h1>Deux outils gratuits, deux minutes chacun.</h1>
  <p class="lead">Les deux sont gratuits, ne demandent aucune inscription, et vous donnent quelque chose sur quoi agir, ou à transmettre à qui détient le budget.</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <a href="/tools/estimator/" class="card card-accent k-gold rv">
      <p class="mono">Six questions</p>
      <h3>Estimateur de prix</h3>
      <p>Répondez à six questions sur le projet et obtenez une fourchette de prix, une durée estimée, et la répartition du travail en étapes. Construit à partir de notre propre grille tarifaire.</p>
      <span class="go">Ouvrir l'estimateur →</span>
    </a>
    <a href="/tools/maturity/" class="card card-accent k-emerald rv">
      <p class="mono">Six questions</p>
      <h3>Diagnostic des données</h3>
      <p>Répondez à six questions sur votre configuration et obtenez une description simple de votre situation, ainsi que les deux points à corriger en priorité.</p>
      <span class="go">Démarrer le diagnostic →</span>
    </a>
  </div>
</section>"""

tools_hub = blocks(tools_hub_en, tools_hub_fr) + cta(
    ("Want a real number instead of an estimate?", "Vous voulez un vrai chiffre plutôt qu'une estimation ?"),
    ("A short call and a look at your systems turns an estimate into a fixed price.",
     "Un court appel et un coup d'œil à vos systèmes transforment une estimation en prix fixe."))

write("tools", layout("/tools/", "Tools · Intellora Tech",
                      "Two free tools: a price estimator for data, cloud and AI work, and a data health check.",
                      tools_hub, accent="gold", nav_key="Tools", crumbs=[(("Tools", "Outils"), None)]))

# ------------------------------------------------------------------- estimator
def opts(group, items, cols="g2"):
    return '<div class="opt-grid %s" data-grp="%s">%s</div>' % (
        cols, group,
        "".join('<button class="opt" type="button" data-v="%s" aria-pressed="false">%s%s</button>' % (
            v, bi(t, tag="b"), bi(d, tag="span"))
                for v, t, d in items))


estimator = f"""
<section class="wrap page-head">
  <p class="eyebrow">{bi(("Price estimator", "Estimateur de prix"))}</p>
  <h1>{bi(("Six questions, one price range.", "Six questions, une fourchette de prix."))}</h1>
  <p class="lead">{bi(("Built from our own rate card and past work. You get a price range, how long it should take, and how the work splits into stages, all copyable into an email.",
                        "Construit à partir de notre propre grille tarifaire et de nos projets passés. Vous obtenez une fourchette de prix, une durée estimée, et la répartition du travail en étapes, tout copiable dans un e-mail."))}</p>
</section>

<section class="wrap" id="est">
  <div class="steps">
    <span data-stepname="1" aria-current="step">{bi(("1 · Objective", "1 · Objectif"))}</span>
    <span data-stepname="2" aria-current="false">{bi(("2 · Shape", "2 · Contexte"))}</span>
    <span data-stepname="3" aria-current="false">{bi(("3 · Estimate", "3 · Estimation"))}</span>
  </div>
  <div class="track"><i id="estBar"></i></div>

  <div data-pane="1">
    <p class="q-h">{bi(("What are you trying to do?", "Que cherchez-vous à faire ?"))}</p>
    {opts("type", [
        ("assess", ("Assess or prove", "Évaluer ou tester"), ("An assessment, audit or proof of concept before committing.", "Un audit, une évaluation ou un test de concept avant de s'engager.")),
        ("optimise", ("Optimise", "Optimiser"), ("Something exists and underperforms: cost, speed or reliability.", "Quelque chose existe et sous-performe : coût, vitesse ou fiabilité.")),
        ("build", ("Build", "Construire"), ("A new platform, pipeline or product capability.", "Une nouvelle plateforme, un nouveau pipeline ou une nouvelle capacité produit.")),
        ("migrate", ("Migrate", "Migrer"), ("Move or modernise an existing estate.", "Déplacer ou moderniser un patrimoine existant.")),
    ])}
    <p class="q-h mt6">{bi(("Which product is the main one?", "Quel est le produit principal concerné ?"))}</p>
    {opts("pillar", [
        ("analytics", ("Analytics &amp; BI", "Analytique &amp; BI"), ("Reporting, semantic models, dashboards.", "Reporting, modèles sémantiques, tableaux de bord.")),
        ("governance", ("Governance", "Gouvernance"), ("Lineage, quality, catalogue, privacy.", "Traçabilité, qualité, catalogue, vie privée.")),
        ("security", ("Security", "Sécurité"), ("Access control, encryption, evidence.", "Contrôle d'accès, chiffrement, preuves.")),
        ("ai", ("AI &amp; ML", "IA &amp; ML"), ("Feature pipelines, training, deployment.", "Pipelines de features, entraînement, déploiement.")),
        ("database", ("Databases", "Bases de données"), ("Modelling, tuning, HA, migration.", "Modélisation, optimisation, haute disponibilité, migration.")),
        ("cloud", ("AWS cloud", "Cloud AWS"), ("Architecture, landing zone, FinOps.", "Architecture, landing zone, FinOps.")),
        ("delivery", ("Delivery &amp; PM", "Livraison &amp; PM"), ("PRINCE2, Agile/Scrum, PMBOK, PMO setup.", "PRINCE2, Agile/Scrum, PMBOK, mise en place d'un PMO.")),
    ], "g3")}
    <div class="row mt6"><button class="btn btn-p" id="estN1" type="button" disabled>{bi(("Continue", "Continuer"))} <span class="ar" aria-hidden="true">→</span></button></div>
  </div>

  <div data-pane="2" hidden>
    <p class="q-h">{bi(("Complexity", "Complexité"))}</p>
    {opts("cx", [
        ("std", ("Standard", "Standard"), ("Clean sources, familiar patterns.", "Sources propres, schémas familiers.")),
        ("mod", ("Moderate", "Modérée"), ("Several systems, some unknowns.", "Plusieurs systèmes, quelques inconnues.")),
        ("adv", ("Advanced", "Avancée"), ("Legacy estate, heavy integration, unclear lineage.", "Patrimoine ancien, forte intégration, traçabilité floue.")),
    ], "g3")}
    <p class="q-h mt6">{bi(("Scope", "Périmètre"))}</p>
    {opts("sz", [
        ("s", ("Small", "Petit"), ("One system or one reporting domain.", "Un seul système ou un seul domaine de reporting.")),
        ("m", ("Medium", "Moyen"), ("Several systems or a department.", "Plusieurs systèmes ou un département.")),
        ("l", ("Large", "Grand"), ("Enterprise-wide or multi-entity.", "À l'échelle de l'entreprise ou multi-entités.")),
    ], "g3")}
    <p class="q-h mt6">{bi(("Governance load", "Niveau de gouvernance"))}</p>
    {opts("gv", [
        ("light", ("Light", "Léger"), ("Internal use, limited external obligation.", "Usage interne, peu d'obligations externes.")),
        ("standard", ("Standard", "Standard"), ("Audit trail and documented controls expected.", "Piste d'audit et contrôles documentés attendus.")),
        ("regulated", ("Regulated", "Réglementé"), ("Supervised entity, formal evidence required.", "Entité supervisée, preuves formelles exigées.")),
    ], "g3")}
    <p class="q-h mt6">{bi(("Timeline", "Calendrier"))}</p>
    {opts("tl", [
        ("relaxed", ("Relaxed", "Détendu"), ("No hard deadline, cheaper to deliver.", "Aucune échéance stricte, livraison moins coûteuse.")),
        ("standard", ("Standard", "Standard"), ("Normal pace.", "Rythme normal.")),
        ("rush", ("Compressed", "Comprimé"), ("Fixed external deadline.", "Échéance externe fixe.")),
    ], "g3")}
    <div class="row mt6">
      <button class="btn btn-p" id="estN2" type="button" disabled>{bi(("See the estimate", "Voir l'estimation"))} <span class="ar" aria-hidden="true">→</span></button>
      <button class="btn btn-g" id="estB2" type="button">{bi(("← Back", "← Retour"))}</button>
    </div>
  </div>

  <div data-pane="3" hidden>
    <div class="grid c2">
      <div>
        <div class="row mb4" style="justify-content:space-between">
          <p class="mono">{bi(("Estimated range", "Fourchette estimée"))}</p>
          <label class="mono" for="cur" style="display:flex;gap:.5rem;align-items:center">{bi(("Currency", "Devise"))}
            <select id="cur" style="width:auto"><option>USD</option><option>EUR</option><option>GBP</option><option>AED</option></select>
          </label>
        </div>
        <p class="result-price" id="resRange">—</p>
        <p class="soft mt4" id="resDur"></p>
        <div class="chips mt5" id="resTags"></div>
        <div class="row mt6">
          <a class="btn btn-p" id="resMail" href="mailto:{EMAIL}">{bi(("Send this to us", "Nous l'envoyer"))} <span class="ar" aria-hidden="true">→</span></a>
          <button class="btn btn-s" id="resCopy" type="button">{bi(("Copy summary", "Copier le résumé"))}</button>
          <span class="mono" id="resCopied" hidden>{bi(("Copied", "Copié"))}</span>
        </div>
        <div class="row mt5"><button class="btn btn-g" id="estB3" type="button">{bi(("← Change answers", "← Modifier les réponses"))}</button></div>
      </div>
      <div>
        <p class="mono mb4">{bi(("How the work splits", "Répartition du travail"))}</p>
        <div id="resPhases"></div>
      </div>
    </div>
  </div>
</section>

<section class="wrap">
  <noscript><div class="callout">The estimator needs JavaScript. Projects typically start at $4,200 for an assessment and $15,000 for a platform build. <a href="/contact/">Email us</a> and we will price your case properly.</div></noscript>
</section>
""" + cta(
    ("Does the number work?", "Ce chiffre vous convient-il ?"),
    ("After one call and a look at your systems, the estimate becomes a fixed price.",
     "Après un appel et un coup d'œil à vos systèmes, l'estimation devient un prix fixe."),
    secondary=("Run the health check", "/tools/maturity/"))

write("tools/estimator", layout("/tools/estimator/", "Price estimator · Intellora Tech",
                               "Six questions gives a price range, a timeline and a stage-by-stage breakdown for data, cloud or AI work.",
                               estimator, accent="gold", nav_key="Tools",
                               crumbs=[(("Tools", "Outils"), "/tools/"), (("Price estimator", "Estimateur de prix"), None)]))

# -------------------------------------------------------------------- maturity
QUESTIONS = [
    (("Where does reporting data come from today?", "D'où proviennent aujourd'hui les données de reporting ?"),
     [("", ("Choose one", "Choisissez une réponse")),
      ("1", ("Spreadsheets and direct queries on production", "Feuilles de calcul et requêtes directes en production")),
      ("2", ("A reporting database refreshed on a schedule", "Une base de reporting actualisée selon un calendrier")),
      ("3", ("A modelled warehouse with defined layers", "Un entrepôt modélisé avec des couches définies")),
      ("4", ("A governed platform with contracts between layers", "Une plateforme gouvernée avec des contrats entre les couches"))]),
    (("If a number looks wrong, how long to trace it to source?", "Si un chiffre semble erroné, combien de temps pour en retrouver la source ?"),
     [("", ("Choose one", "Choisissez une réponse")),
      ("1", ("Days, and often inconclusive", "Des jours, et souvent sans résultat concluant")),
      ("2", ("Hours, by asking the right person", "Des heures, en demandant à la bonne personne")),
      ("3", ("Minutes, with documentation", "Des minutes, grâce à la documentation")),
      ("4", ("Immediately, lineage is captured automatically", "Immédiatement, la traçabilité est captée automatiquement"))]),
    (("How are pipeline failures detected?", "Comment les échecs de pipeline sont-ils détectés ?"),
     [("", ("Choose one", "Choisissez une réponse")),
      ("1", ("Someone notices a stale dashboard", "Quelqu'un remarque un tableau de bord obsolète")),
      ("2", ("Job failure alerts", "Alertes d'échec de job")),
      ("3", ("Job and freshness alerts", "Alertes de job et de fraîcheur des données")),
      ("4", ("Data quality tests fail before consumers see it", "Les tests de qualité échouent avant que les utilisateurs ne le voient"))]),
    (("Who can access sensitive data?", "Qui peut accéder aux données sensibles ?"),
     [("", ("Choose one", "Choisissez une réponse")),
      ("1", ("Broad access, unclear boundaries", "Accès large, limites floues")),
      ("2", ("Role-based, reviewed occasionally", "Basé sur les rôles, revu occasionnellement")),
      ("3", ("Least privilege with periodic review", "Moindre privilège avec revue périodique")),
      ("4", ("Least privilege, row/column controls, full access logs", "Moindre privilège, contrôles ligne/colonne, journaux d'accès complets"))]),
    (("How is infrastructure provisioned?", "Comment l'infrastructure est-elle provisionnée ?"),
     [("", ("Choose one", "Choisissez une réponse")),
      ("1", ("Manually, by hand", "Manuellement, à la main")),
      ("2", ("Scripted in places", "Scriptée par endroits")),
      ("3", ("Infrastructure as code for most of it", "Infrastructure as code pour l'essentiel")),
      ("4", ("Fully declarative with environment parity", "Entièrement déclarative avec parité des environnements"))]),
    (("Where is machine learning today?", "Où en est le machine learning aujourd'hui ?"),
     [("", ("Choose one", "Choisissez une réponse")),
      ("1", ("Not started or exploratory only", "Pas commencé, ou seulement exploratoire")),
      ("2", ("Notebooks, nothing in production", "Des notebooks, rien en production")),
      ("3", ("One or two models deployed", "Un ou deux modèles déployés")),
      ("4", ("Models in production with monitoring and retraining", "Des modèles en production, avec surveillance et réentraînement"))]),
]

q_html = "".join(f"""
  <div class="field" data-q>
    <label for="q{i}">{bi(q)}</label>
    <select id="q{i}">{''.join('<option value="%s" data-en="%s" data-fr="%s">%s</option>' % (v, esc(pair(t)[0]), esc(pair(t)[1]), pair(t)[0]) for v, t in choices)}</select>
  </div>""" for i, (q, choices) in enumerate(QUESTIONS, 1))

maturity = f"""
<section class="wrap page-head">
  <p class="eyebrow">{bi(("Data health check", "Diagnostic des données"))}</p>
  <h1>{bi(("Six questions about your data setup.", "Six questions sur votre configuration de données."))}</h1>
  <p class="lead">{bi(("Answer honestly and you get a plain description of where you stand, what usually holds companies back at that point, and the two things we would fix first.",
                        "Répondez honnêtement et vous obtenez une description simple de votre situation, de ce qui freine généralement les entreprises à ce stade, et des deux points que nous corrigerions en premier."))}</p>
</section>

<section class="wrap" id="mat">
  <div class="grid c2">
    <div class="rv">{q_html}
      <button class="btn btn-p" id="matGo" type="button">{bi(("Show my result", "Afficher mon résultat"))} <span class="ar" aria-hidden="true">→</span></button>
    </div>
    <div class="rv"><div id="matOut" hidden></div></div>
  </div>
  <noscript><div class="callout mt6">This check needs JavaScript. <a href="/contact/">Book a call</a> and we will walk through the same questions with you.</div></noscript>
</section>
""" + cta(
    ("Want the proper version?", "Vous voulez la version complète ?"),
    ("A call replaces this with a real look at your systems.",
     "Un appel remplace ceci par un vrai regard sur vos systèmes."),
    secondary=("Estimate the cost", "/tools/estimator/"))

write("tools/maturity", layout("/tools/maturity/", "Data health check · Intellora Tech",
                              "Six questions that show where your data setup stands and what is worth fixing first.",
                              maturity, accent="gold", nav_key="Tools",
                              crumbs=[(("Tools", "Outils"), "/tools/"), (("Data health check", "Diagnostic des données"), None)]))

# ------------------------------------------------------------------------ blog
def post_cards_html(i):
    return "".join(f"""
    <a href="/blog/{p['slug']}/" class="card card-accent k-coral rv">
      <p class="mono">{p['cat'] if not i else p['cat_fr']} · {p['mins']} {"min read" if not i else "min de lecture"}</p>
      <div class="post-card">
        <span class="t">{p['title'] if not i else p['title_fr']}</span>
        <span class="x">{p['excerpt'] if not i else p['excerpt_fr']}</span>
      </div>
      <span class="go">{"Read →" if not i else "Lire →"}</span>
    </a>""" for p in POSTS)


blog_index_en = f"""
<section class="wrap page-head">
  <p class="eyebrow">Blog</p>
  <h1>Field notes from production systems.</h1>
  <p class="lead">Written from real jobs and things that went wrong, not vendor material. Short, specific, and useful whether or not you ever hire us.</p>
</section>

<section class="wrap">
  <div class="grid c3">{post_cards_html(0)}</div>
</section>"""

blog_index_fr = f"""
<section class="wrap page-head">
  <p class="eyebrow">Blog</p>
  <h1>Notes de terrain depuis des systèmes en production.</h1>
  <p class="lead">Écrit à partir de vrais projets et de vraies erreurs, pas de contenu commercial. Court, précis, et utile que vous nous engagiez ou non.</p>
</section>

<section class="wrap">
  <div class="grid c3">{post_cards_html(1)}</div>
</section>"""

blog_index = blocks(blog_index_en, blog_index_fr) + cta(
    ("Have a version of this problem?", "Vous reconnaissez une version de ce problème ?"),
    ("If one of these sounds like your platform, a twenty-minute call will tell you how deep it goes.",
     "Si l'un de ces cas ressemble à votre plateforme, vingt minutes au téléphone suffisent à en mesurer l'ampleur."))

write("blog", layout("/blog/", "Blog · Intellora Tech",
                     "Field notes on data platforms: reporting definitions, database cost, and what has to be "
                     "true before a machine learning model ships.",
                     blog_index, accent="coral", nav_key="Blog", crumbs=[(("Blog", "Blog"), None)]))


def post_page(p, body_html, body_html_fr=None):
    body_html_fr = body_html_fr or body_html
    others = [o for o in POSTS if o["slug"] != p["slug"]][:2]

    def more_html(i):
        return "".join(f"""
    <a href="/blog/{o['slug']}/" class="card card-accent k-coral">
      <p class="mono">{o['cat'] if not i else o['cat_fr']} · {o['mins']} {"min read" if not i else "min de lecture"}</p>
      <div class="post-card"><span class="t">{o['title'] if not i else o['title_fr']}</span><span class="x">{o['excerpt'] if not i else o['excerpt_fr']}</span></div>
      <span class="go">{"Read →" if not i else "Lire →"}</span>
    </a>""" for o in others)

    def article(cat, title, date_h, mins_label, team, more_label, body_h, more_h):
        return f"""
<article class="wrap page-head article">
  <p class="eyebrow">{cat}</p>
  <h1 style="max-width:24ch">{title}</h1>
  <div class="post-meta">
    <time datetime="{p['date']}">{date_h}</time>
    <span>·</span><span>{mins_label}</span>
    <span>·</span><span>{team}</span>
  </div>
  <div class="prose mt7">{body_h}</div>
</article>

<section class="wrap section article">
  <h2 class="mb5">{more_label}</h2>
  <div class="grid c2">{more_h}</div>
</section>"""

    body_en = article(p['cat'], p['title'], p['date_h'], "%d minute read" % p['mins'],
                       "Intellora Tech engineering team", "More from the blog", body_html, more_html(0))
    body_fr = article(p['cat_fr'], p['title_fr'], p['date_h_fr'], "%d minutes de lecture" % p['mins'],
                       "Équipe d'ingénierie Intellora Tech", "Plus sur le blog", body_html_fr, more_html(1))

    body = blocks(body_en, body_fr) + cta(
        ("Recognise this in your own platform?", "Cela vous rappelle votre propre plateforme ?"),
        ("Twenty minutes is usually enough to tell you whether it is a small fix or a structural one.",
         "Vingt minutes suffisent généralement à dire s'il s'agit d'une petite correction ou d'un problème structurel."))

    write("blog/" + p["slug"], layout("/blog/%s/" % p["slug"], "%s · Intellora Tech" % p["title"],
                                      p["excerpt"], body, accent="coral", nav_key="Blog",
                                      crumbs=[("Blog", "/blog/"), ((p["title"], p["title_fr"]), None)]))


post_page(POSTS[0], """
<p>Two people open two dashboards, both labelled <em>active customers</em>, and get different numbers. The meeting stops. Someone is asked to "check the data", and three days later the answer is that both dashboards are correct.</p>

<p>They are correct because they are answering different questions. One counts a customer active if they transacted in the last 30 days. The other counts them active if their account is not closed. Nobody wrote either rule down, so nobody noticed they had diverged.</p>

<h2>The disagreement is almost never technical</h2>

<p>It is tempting to treat this as a pipeline problem: a join gone wrong, a filter applied in one place and not the other. Occasionally it is. Far more often the pipelines are both doing exactly what they were told, and what they were told was decided separately, months apart, by people solving different immediate problems.</p>

<p>The tell is simple: ask each dashboard's owner to state the definition out loud. If they hesitate, or reach for the SQL to answer, the definition does not exist as a governed object. It exists as an implementation detail, and implementation details drift.</p>

<blockquote>A metric that lives only in a query is not a definition. It is a copy of one, and copies diverge.</blockquote>

<h2>What actually fixes it</h2>

<p>The durable fix is to define each metric once, in one place, and have every consumer read from that place. In practice that means a semantic layer (<code>dbt</code> metrics, a warehouse view layer, an Oracle Analytics RPD, whatever fits your stack) that owns the calculation, and reporting tools that are forbidden from recalculating it themselves.</p>

<p>Three properties make it stick:</p>

<ul>
  <li><strong>One definition per metric, versioned.</strong> If the rule changes, that is a commit with a date and an author, not a silent edit in a dashboard.</li>
  <li><strong>Consumers cannot override it.</strong> The moment a report can redefine <em>active customer</em> locally, you are back where you started, only now with the appearance of governance.</li>
  <li><strong>The definition is readable by non-engineers.</strong> If the CFO cannot read the rule and agree with it, the rule has not actually been agreed.</li>
</ul>

<h2>The part people skip</h2>

<p>The technical work is the easy half. The hard half is getting the finance lead, the operations lead and the product lead into one room to agree what <em>active</em> means, because it turns out they each need it to mean something slightly different, and that disagreement is real, not a data problem.</p>

<p>When that happens, the answer is usually not one metric. It is two or three, each named precisely: <em>transacting customers (30d)</em>, <em>open accounts</em>, <em>billable accounts</em>, so that nobody has to guess which one a chart is showing. Precision in the name does more work than any amount of pipeline engineering.</p>

<h2>How to tell if you have this problem</h2>

<p>You do, if any of these are true: a recurring meeting spends time reconciling figures rather than acting on them; the answer to "which number is right" depends on who you ask; or a regulator has asked how a reported figure was derived and the answer took more than an hour to assemble.</p>

<p>None of those are reporting problems. They are all the same definition problem, showing up at different altitudes.</p>
""", """
<p>Deux personnes ouvrent deux tableaux de bord, tous deux intitulés <em>clients actifs</em>, et obtiennent des chiffres différents. La réunion s'arrête. On demande à quelqu'un de « vérifier les données », et trois jours plus tard, la réponse est que les deux tableaux de bord sont corrects.</p>

<p>Ils sont corrects parce qu'ils répondent à des questions différentes. L'un compte un client comme actif s'il a transigé au cours des 30 derniers jours. L'autre le compte comme actif si son compte n'est pas fermé. Personne n'a écrit l'une ou l'autre règle, donc personne n'a remarqué qu'elles avaient dérivé.</p>

<h2>Le désaccord n'est presque jamais technique</h2>

<p>Il est tentant de traiter cela comme un problème de pipeline : une jointure mal faite, un filtre appliqué à un endroit et pas à un autre. C'est parfois le cas. Bien plus souvent, les deux pipelines font exactement ce qu'on leur a demandé, et ce qu'on leur a demandé a été décidé séparément, à des mois d'intervalle, par des personnes qui résolvaient des problèmes immédiats différents.</p>

<p>Le signe est simple : demandez au responsable de chaque tableau de bord d'énoncer la définition à voix haute. S'il hésite, ou s'il va chercher le SQL pour répondre, la définition n'existe pas comme un objet gouverné. Elle existe comme un détail d'implémentation, et les détails d'implémentation dérivent.</p>

<blockquote>Un indicateur qui ne vit que dans une requête n'est pas une définition. C'est la copie d'une définition, et les copies dérivent.</blockquote>

<h2>Ce qui règle vraiment le problème</h2>

<p>La solution durable consiste à définir chaque indicateur une seule fois, à un seul endroit, et à faire en sorte que chaque consommateur le lise depuis cet endroit. En pratique, cela signifie une couche sémantique (des métriques <code>dbt</code>, une couche de vues d'entrepôt, un RPD Oracle Analytics, ce qui convient à votre pile) qui possède le calcul, et des outils de reporting auxquels il est interdit de le recalculer eux-mêmes.</p>

<p>Trois propriétés permettent que cela tienne :</p>

<ul>
  <li><strong>Une définition par indicateur, versionnée.</strong> Si la règle change, c'est un commit avec une date et un auteur, pas une modification silencieuse dans un tableau de bord.</li>
  <li><strong>Les consommateurs ne peuvent pas la modifier.</strong> Dès qu'un rapport peut redéfinir <em>client actif</em> localement, vous revenez à la case départ, mais avec cette fois l'apparence de la gouvernance.</li>
  <li><strong>La définition est lisible par des non-ingénieurs.</strong> Si le directeur financier ne peut pas lire la règle et l'approuver, la règle n'a pas vraiment été convenue.</li>
</ul>

<h2>La partie que tout le monde évite</h2>

<p>Le travail technique est la moitié facile. La moitié difficile consiste à réunir le responsable financier, le responsable des opérations et le responsable produit dans une même salle pour se mettre d'accord sur ce que signifie <em>actif</em>, car il s'avère que chacun a besoin que cela signifie quelque chose de légèrement différent, et ce désaccord est réel, pas un problème de données.</p>

<p>Quand cela arrive, la réponse n'est généralement pas un seul indicateur. Ce sont deux ou trois, chacun nommé précisément : <em>clients transactionnels (30j)</em>, <em>comptes ouverts</em>, <em>comptes facturables</em>, afin que personne n'ait à deviner ce qu'un graphique montre. La précision du nom fait plus de travail que n'importe quelle quantité d'ingénierie de pipeline.</p>

<h2>Comment savoir si vous avez ce problème</h2>

<p>C'est le cas si l'une de ces situations est vraie : une réunion récurrente passe du temps à rapprocher des chiffres plutôt qu'à agir sur eux ; la réponse à « quel chiffre est correct » dépend de qui vous demandez ; ou un régulateur a demandé comment un chiffre publié a été calculé et la réponse a pris plus d'une heure à assembler.</p>

<p>Aucun de ces cas n'est un problème de reporting. Ce sont tous le même problème de définition, qui se manifeste à des altitudes différentes.</p>
""")

post_page(POSTS[1], """
<p>Cloud database spend has a peculiar property: it grows smoothly, so nobody ever has the moment where they look at it and flinch. Each month is a little more than the last, each increase is individually defensible, and eighteen months later the line item is four times what it was with no single decision to point at.</p>

<p>When we audit these bills, the overspend is rarely in the pricing model. It is in a handful of query patterns that were reasonable at small volumes and became expensive at large ones.</p>

<h2>1. The query that scans everything to return almost nothing</h2>

<p>A report filters on a date range and returns 400 rows. The execution plan shows a full scan of 90 million. Usually the filter is applied to a derived column, such as <code>WHERE YEAR(created_at) = 2026</code>, which makes the index unusable. Rewriting to a range predicate on the raw column changes the plan and, on managed platforms billed by data scanned, changes the bill directly.</p>

<h2>2. Statistics nobody has refreshed</h2>

<p>The optimiser makes its decisions from statistics. When those statistics describe a table as it was two years and forty million rows ago, it will confidently choose a nested loop where a hash join belongs. This is the cheapest fix on this list and the most commonly skipped: a stale-stats problem looks exactly like a hardware problem right up until someone checks.</p>

<h2>3. Indexes that exist for queries nobody runs</h2>

<p>Every index is paid for twice: once in storage, and again on every write. Estates that have been through several teams accumulate indexes added for a report that was retired long ago. Most engines expose usage counters. Anything unused across a full business cycle, including month-end and year-end, which is why you wait a full cycle, is a candidate for removal.</p>

<blockquote>Adding an index is a five-minute decision that you pay for on every insert, for years.</blockquote>

<h2>4. Partitions that are not aligned to how data is queried</h2>

<p>Partitioning helps only when the predicate lets the engine skip partitions. A table partitioned by ingest date, queried almost exclusively by transaction date, gets all of the maintenance cost and none of the pruning benefit. This one requires actually reading the query log rather than reasoning about how the table <em>should</em> be used.</p>

<h2>5. The pipeline that reprocesses history every night</h2>

<p>Full reloads survive because they are simple and correct. They stop being cheap the moment the table is large: reprocessing five years of history nightly to capture one day of change is a cost that grows with your success. Incremental processing with a watermark, plus a scheduled reconciliation to catch drift, keeps the correctness and drops most of the cost.</p>

<h2>Where to start</h2>

<p>Pull the ten most expensive queries by total cost, not by average runtime, which hides frequently-run cheap-looking queries, and read their plans. In most estates, those ten account for a large majority of the spend, and two or three of them are fixable in an afternoon.</p>

<p>The reason this work is undersold is that it produces no new capability. It just makes the bill smaller and the reports faster, which is a difficult thing to put in a launch announcement and an easy thing to justify to a finance director.</p>
""", """
<p>Les dépenses de bases de données cloud ont une particularité : elles augmentent en douceur, si bien que personne n'a jamais ce moment où on les regarde et sursaute. Chaque mois est un peu plus élevé que le précédent, chaque hausse est individuellement défendable, et dix-huit mois plus tard, la ligne de dépense est quatre fois plus élevée qu'avant, sans qu'aucune décision unique n'en soit la cause.</p>

<p>Quand nous auditons ces factures, le dépassement se trouve rarement dans le modèle tarifaire. Il se trouve dans une poignée de schémas de requêtes qui étaient raisonnables à faible volume et sont devenus coûteux à grande échelle.</p>

<h2>1. La requête qui parcourt tout pour ne retourner presque rien</h2>

<p>Un rapport filtre sur une plage de dates et retourne 400 lignes. Le plan d'exécution montre un scan complet de 90 millions de lignes. En général, le filtre est appliqué à une colonne dérivée, comme <code>WHERE YEAR(created_at) = 2026</code>, ce qui rend l'index inutilisable. Réécrire le filtre en un prédicat de plage sur la colonne brute change le plan et, sur les plateformes managées facturées au volume de données scannées, change directement la facture.</p>

<h2>2. Des statistiques que personne n'a rafraîchies</h2>

<p>L'optimiseur prend ses décisions à partir des statistiques. Quand ces statistiques décrivent une table telle qu'elle était il y a deux ans et quarante millions de lignes, il choisira avec assurance une boucle imbriquée là où une jointure par hachage s'impose. C'est la correction la moins chère de cette liste et la plus souvent négligée : un problème de statistiques obsolètes ressemble exactement à un problème matériel, jusqu'à ce que quelqu'un vérifie.</p>

<h2>3. Des index qui existent pour des requêtes que personne n'exécute</h2>

<p>Chaque index est payé deux fois : une fois en stockage, et à nouveau à chaque écriture. Les patrimoines qui ont vu passer plusieurs équipes accumulent des index ajoutés pour un rapport retiré depuis longtemps. La plupart des moteurs exposent des compteurs d'utilisation. Tout ce qui reste inutilisé sur un cycle métier complet, incluant la fin de mois et la fin d'année, ce qui explique qu'il faille attendre un cycle complet, est un candidat à la suppression.</p>

<blockquote>Ajouter un index est une décision de cinq minutes que vous payez à chaque insertion, pendant des années.</blockquote>

<h2>4. Des partitions qui ne sont pas alignées sur la façon dont les données sont interrogées</h2>

<p>Le partitionnement n'aide que lorsque le prédicat permet au moteur de sauter des partitions. Une table partitionnée par date d'ingestion, interrogée presque exclusivement par date de transaction, subit tout le coût de maintenance sans aucun des bénéfices d'élagage. Ce cas exige de véritablement lire le journal des requêtes plutôt que de raisonner sur la façon dont la table <em>devrait</em> être utilisée.</p>

<h2>5. Le pipeline qui retraite l'historique chaque nuit</h2>

<p>Les rechargements complets survivent parce qu'ils sont simples et corrects. Ils cessent d'être bon marché dès que la table devient grande : retraiter cinq ans d'historique chaque nuit pour capturer un jour de changement est un coût qui croît avec votre succès. Un traitement incrémental avec un point de contrôle, plus un rapprochement programmé pour détecter la dérive, préserve l'exactitude tout en réduisant l'essentiel du coût.</p>

<h2>Par où commencer</h2>

<p>Extrayez les dix requêtes les plus coûteuses par coût total, et non par durée moyenne d'exécution, qui masque les requêtes fréquentes à l'apparence bon marché, et lisez leurs plans. Dans la plupart des patrimoines, ces dix requêtes représentent une large majorité de la dépense, et deux ou trois d'entre elles se corrigent en une après-midi.</p>

<p>La raison pour laquelle ce travail est sous-évalué est qu'il ne produit aucune nouvelle capacité. Il rend simplement la facture plus petite et les rapports plus rapides, ce qui est difficile à mettre dans une annonce de lancement mais facile à justifier auprès d'un directeur financier.</p>
""")

post_page(POSTS[3], """
<p>The sponsor asks for a one-line status and gets two contradictory answers in the same afternoon. The steering pack says the programme is on track: milestone three signed off, budget on plan, risk register green. The sprint board says something rougher: the backlog has grown by forty stories since kickoff and nobody is quite sure when it stops growing.</p>

<p>Both are correct. They are not measuring the same thing.</p>

<h2>A stage gate and a burndown chart answer different questions</h2>

<p>A steering pack exists to answer "are we still doing the thing we agreed to do, for the money we agreed to spend." It assumes the thing was defined well enough at the start to be trackable against, and that assumption is exactly what a stage-gate, PRINCE2-style structure is built to enforce: a business case, a defined scope, a set of stage boundaries, and a formal decision to continue or stop at each one.</p>

<p>A sprint board exists to answer a different question: "given what we now know, what is the most valuable thing to build next." It assumes the requirement will keep sharpening as the team learns, and that trying to freeze it early would produce the wrong thing built precisely on schedule.</p>

<p>Neither assumption is wrong in general. One of them is wrong for a given piece of work, and the disagreement between the two reports is usually the first visible symptom that the wrong one got picked.</p>

<blockquote>A programme with no named methodology is not neutral. It is running an unplanned hybrid, and nobody chose its rules on purpose.</blockquote>

<h2>The tell: what changed between the plan and the board</h2>

<p>When we are asked to look at a stalled programme, the fastest diagnostic is not the risk register. It is comparing the original business case to the current backlog. If they still describe the same thing in the same terms, the stage-gate structure is probably still earning its keep. If the backlog has drifted a long way from what the business case funded, and nobody formally re-baselined the case, the programme has quietly gone agile without anyone deciding to run it that way, and the steering pack is now reporting against a target that stopped being the real target months ago.</p>

<p>The reverse failure is just as common and less talked about: a genuinely exploratory piece of work, forced into stage gates because that is the only reporting format the organisation knows how to run. Each gate review becomes a fiction where the team pretends the next stage is well-defined enough to commit to, because saying "we do not know yet" is not an acceptable answer in that room.</p>

<h2>Choosing the method is a risk decision, not a preference</h2>

<p>The honest version of this choice rests on two questions, asked at the start and revisited at each stage boundary: how much of the requirement is actually fixed, and how much does getting it wrong cost. High governance load and a genuinely fixed scope point toward PRINCE2 or a PMBOK-aligned waterfall, because the cost of an ungoverned change is high and the requirement is stable enough to govern against. Low governance load and a requirement that will keep moving point toward Scrum, because the cost of a rigid plan is discovering, three stage gates later, that you built the wrong thing precisely as specified.</p>

<p>Most real programmes are neither. A migration, for instance, usually has a hard, fixed constraint (the cutover date, the data that must reconcile) wrapped around genuinely exploratory work (exactly how the new platform's edge cases should behave). The honest answer there is a named hybrid: stage gates around the fixed commitments, sprints inside them, with an explicit statement of which parts of the plan are fixed and which are expected to move. Calling it a hybrid on purpose, in writing, is what separates a deliberate blend from an accidental one.</p>

<h2>What a RAID log is actually for</h2>

<p>Underneath both reporting styles sits the same unglamorous document: a risk, assumption, issue and dependency log, kept current and reviewed on a schedule. Agile teams sometimes drop it because a backlog feels like enough; PRINCE2 programmes sometimes let it become a compliance exercise nobody reads until an auditor asks for it. Either failure mode produces the same result: the sponsor finds out about a risk on the day it becomes an issue, rather than three weeks earlier when it was still cheap to manage.</p>

<p>A RAID log that is actually used is boring in exactly the right way. It has a small number of live entries, each with a named owner and a next review date, and it gets ten minutes at the start of every steering meeting whether or not there is anything dramatic to report.</p>

<h2>How to tell if you have this problem</h2>

<p>The symptoms travel together: status meetings spend more time reconciling two versions of reality than deciding anything; a milestone gets marked "on track" the week before it visibly is not; and nobody can point to the moment the methodology was chosen, because it never was, it just accumulated.</p>

<p>None of that is a team performance problem. It is a structural one, and it is fixed by naming the method on purpose rather than discovering which one you were running after the fact.</p>
""", """
<p>Le sponsor demande un statut en une ligne et reçoit deux réponses contradictoires le même après-midi. Le rapport de pilotage dit que le programme est sur la bonne voie : jalon trois validé, budget conforme au plan, registre des risques au vert. Le tableau de sprint dit quelque chose de plus rugueux : le backlog a grossi de quarante user stories depuis le lancement et personne n'est vraiment sûr de quand cela s'arrêtera.</p>

<p>Les deux sont exacts. Ils ne mesurent pas la même chose.</p>

<h2>Un jalon et un burndown répondent à des questions différentes</h2>

<p>Un rapport de pilotage existe pour répondre à « faisons-nous toujours ce que nous avons convenu de faire, pour l'argent que nous avons convenu de dépenser ». Il suppose que la chose a été définie assez précisément au départ pour être suivie, et cette hypothèse est exactement ce qu'une structure à jalons, de type PRINCE2, est conçue pour imposer : un argumentaire économique, un périmètre défini, un ensemble de limites d'étapes, et une décision formelle de continuer ou d'arrêter à chacune d'elles.</p>

<p>Un tableau de sprint existe pour répondre à une question différente : « étant donné ce que nous savons maintenant, quelle est la chose la plus utile à construire ensuite ». Il suppose que le besoin va continuer à s'affiner à mesure que l'équipe apprend, et que tenter de le figer tôt produirait la mauvaise chose, construite précisément dans les délais.</p>

<p>Aucune des deux hypothèses n'est fausse en général. L'une d'elles est fausse pour un travail donné, et le désaccord entre les deux rapports est généralement le premier symptôme visible que la mauvaise a été choisie.</p>

<blockquote>Un programme sans méthodologie nommée n'est pas neutre. Il fonctionne selon un hybride non planifié, et personne n'en a choisi les règles délibérément.</blockquote>

<h2>Le signe révélateur : ce qui a changé entre le plan et le tableau</h2>

<p>Quand on nous demande d'examiner un programme bloqué, le diagnostic le plus rapide n'est pas le registre des risques. C'est de comparer l'argumentaire économique original au backlog actuel. S'ils décrivent toujours la même chose dans les mêmes termes, la structure à jalons mérite probablement encore sa place. Si le backlog a dérivé loin de ce que l'argumentaire économique finançait, et que personne n'a formellement rebasé le dossier, le programme est passé discrètement en mode agile sans que personne ne décide de le gérer ainsi, et le rapport de pilotage rapporte désormais par rapport à une cible qui a cessé d'être la vraie cible depuis des mois.</p>

<p>L'échec inverse est tout aussi fréquent et moins souvent évoqué : un travail réellement exploratoire, forcé dans des jalons parce que c'est le seul format de reporting que l'organisation sait gérer. Chaque revue de jalon devient une fiction où l'équipe prétend que l'étape suivante est suffisamment définie pour s'y engager, parce que dire « nous ne savons pas encore » n'est pas une réponse acceptable dans cette salle.</p>

<h2>Choisir la méthode est une décision de risque, pas une préférence</h2>

<p>La version honnête de ce choix repose sur deux questions, posées au départ et revisitées à chaque limite d'étape : quelle part du besoin est réellement figée, et combien coûte une erreur. Une charge de gouvernance élevée et un périmètre réellement figé orientent vers PRINCE2 ou un cycle en cascade aligné sur le PMBOK, car le coût d'un changement non gouverné est élevé et le besoin est assez stable pour être gouverné. Une charge de gouvernance faible et un besoin qui va continuer d'évoluer orientent vers Scrum, car le coût d'un plan rigide est de découvrir, trois jalons plus tard, que vous avez construit la mauvaise chose, précisément comme spécifié.</p>

<p>La plupart des programmes réels ne sont ni l'un ni l'autre. Une migration, par exemple, a généralement une contrainte dure et fixe (la date de bascule, les données qui doivent se recouper) enveloppant un travail réellement exploratoire (exactement comment les cas limites de la nouvelle plateforme doivent se comporter). La réponse honnête ici est un hybride nommé : des jalons autour des engagements fixes, des sprints à l'intérieur, avec une déclaration explicite de quelles parties du plan sont fixes et lesquelles sont censées évoluer. L'appeler un hybride délibérément, par écrit, est ce qui distingue un mélange voulu d'un mélange accidentel.</p>

<h2>À quoi sert vraiment un registre RAID</h2>

<p>Sous les deux styles de reporting se trouve le même document peu glamour : un registre des risques, hypothèses, problèmes et dépendances, tenu à jour et revu selon un calendrier. Les équipes agiles l'abandonnent parfois parce qu'un backlog semble suffire ; les programmes PRINCE2 le laissent parfois devenir un exercice de conformité que personne ne lit jusqu'à ce qu'un auditeur le demande. Les deux modes d'échec produisent le même résultat : le sponsor découvre un risque le jour où il devient un problème, plutôt que trois semaines plus tôt, quand il était encore bon marché à gérer.</p>

<p>Un registre RAID réellement utilisé est ennuyeux exactement de la bonne façon. Il contient un petit nombre d'entrées actives, chacune avec un responsable nommé et une prochaine date de revue, et il reçoit dix minutes au début de chaque réunion de pilotage, qu'il y ait ou non quelque chose de dramatique à signaler.</p>

<h2>Comment savoir si vous avez ce problème</h2>

<p>Les symptômes voyagent ensemble : les réunions de statut passent plus de temps à rapprocher deux versions de la réalité qu'à décider quoi que ce soit ; un jalon est marqué « sur la bonne voie » la semaine avant qu'il ne le soit visiblement plus ; et personne ne peut désigner le moment où la méthodologie a été choisie, parce qu'elle ne l'a jamais été, elle s'est simplement accumulée.</p>

<p>Rien de tout cela n'est un problème de performance d'équipe. C'est un problème structurel, et il se corrige en nommant la méthode délibérément plutôt qu'en découvrant après coup laquelle vous étiez en train d'exécuter.</p>
""")

post_page(POSTS[2], """
<p>A model that scores well in a notebook and never reaches production is not a modelling failure. It is nearly always a data engineering failure that surfaced late, and the specific failures repeat across organisations with striking consistency.</p>

<h2>The features have to be reproducible at serving time</h2>

<p>The most common blocker: a feature computed from a table that only exists in the analytics warehouse, refreshed nightly, using a window that includes data not available at prediction time. The model works in training because it can see the future. In production it cannot, and accuracy collapses in a way that looks mysterious unless you go looking for leakage.</p>

<p>The fix is structural, not clever. Features get computed by one pipeline that serves both training and inference, or by two pipelines with a test that asserts they produce identical values for the same input. Anything less and the two drift, quietly.</p>

<h2>Training data has to be reconstructible</h2>

<p>Six months after deployment someone asks why the model made a particular decision. Answering means reconstructing the exact training set, which means the raw inputs, the transformation code and the feature definitions all have to be versioned together, not just the model weights.</p>

<blockquote>If you cannot rebuild the training set from scratch, you do not have a reproducible model. You have an artefact.</blockquote>

<p>In regulated settings this is not a nice-to-have. It is the thing a supervisor will ask for, and "we retrained since then" is not an answer.</p>

<h2>Someone has to own degradation</h2>

<p>Models decay. Input distributions shift, an upstream system changes a code list, a business process changes and the historical relationship stops holding. None of this raises an error; the model keeps returning confident predictions that are progressively less useful.</p>

<p>Production readiness means monitoring the inputs, not just the outputs: distribution checks on incoming features, alerts on null-rate and cardinality changes, and a scheduled review of prediction quality against outcomes once outcomes are known. And a named person who receives those alerts.</p>

<h2>There has to be a rollback</h2>

<p>The question "what do we do if this model starts behaving badly on a Friday afternoon" should have a boring answer: route traffic to the previous version, or to the deterministic rule the model replaced. If the answer involves a retraining run, the model is not deployed; it is merely running.</p>

<h2>The honest sequencing</h2>

<p>When an organisation asks for machine learning and the data layer underneath is not ready, the useful response is to say so and fix the layer first. The model built on unreliable inputs will be impressive in a demo and unusable in operations, and the credibility spent getting it approved does not come back.</p>

<p>Fixing the layer first is a slower announcement and a much faster route to something that survives contact with production.</p>
""", """
<p>Un modèle qui obtient de bons scores dans un notebook et n'atteint jamais la production n'est pas un échec de modélisation. C'est presque toujours un échec d'ingénierie des données qui a émergé tardivement, et les échecs spécifiques se répètent d'une organisation à l'autre avec une constance frappante.</p>

<h2>Les features doivent être reproductibles au moment de la mise en service</h2>

<p>Le blocage le plus courant : une feature calculée à partir d'une table qui n'existe que dans l'entrepôt analytique, rafraîchie chaque nuit, utilisant une fenêtre qui inclut des données non disponibles au moment de la prédiction. Le modèle fonctionne à l'entraînement parce qu'il peut voir le futur. En production, il ne le peut pas, et la précision s'effondre d'une manière qui semble mystérieuse à moins de chercher activement une fuite de données.</p>

<p>La correction est structurelle, pas astucieuse. Les features doivent être calculées par un seul pipeline qui alimente à la fois l'entraînement et l'inférence, ou par deux pipelines avec un test qui vérifie qu'ils produisent des valeurs identiques pour la même entrée. Tout le reste, et les deux dérivent, silencieusement.</p>

<h2>Les données d'entraînement doivent être reconstructibles</h2>

<p>Six mois après le déploiement, quelqu'un demande pourquoi le modèle a pris une décision particulière. Y répondre signifie reconstruire l'ensemble d'entraînement exact, ce qui signifie que les données brutes, le code de transformation et les définitions de features doivent tous être versionnés ensemble, pas seulement les poids du modèle.</p>

<blockquote>Si vous ne pouvez pas reconstruire l'ensemble d'entraînement à partir de zéro, vous n'avez pas un modèle reproductible. Vous avez un artefact.</blockquote>

<p>Dans les environnements réglementés, ce n'est pas un luxe. C'est ce qu'un superviseur demandera, et « nous avons réentraîné depuis » n'est pas une réponse.</p>

<h2>Quelqu'un doit être responsable de la dégradation</h2>

<p>Les modèles se dégradent. Les distributions d'entrée évoluent, un système amont change une liste de codes, un processus métier change et la relation historique cesse de tenir. Rien de tout cela ne déclenche d'erreur ; le modèle continue de renvoyer des prédictions confiantes qui sont progressivement moins utiles.</p>

<p>Être prêt pour la production signifie surveiller les entrées, pas seulement les sorties : des contrôles de distribution sur les features entrantes, des alertes sur les changements de taux de nulls et de cardinalité, et une revue programmée de la qualité des prédictions par rapport aux résultats une fois ces résultats connus. Et une personne nommée qui reçoit ces alertes.</p>

<h2>Il doit y avoir un retour en arrière possible</h2>

<p>La question « que faisons-nous si ce modèle commence à mal se comporter un vendredi après-midi » devrait avoir une réponse ennuyeuse : rediriger le trafic vers la version précédente, ou vers la règle déterministe que le modèle a remplacée. Si la réponse implique un réentraînement, le modèle n'est pas déployé ; il ne fait que fonctionner.</p>

<h2>Le séquencement honnête</h2>

<p>Quand une organisation demande du machine learning et que la couche de données sous-jacente n'est pas prête, la réponse utile est de le dire et de réparer la couche en premier. Le modèle construit sur des entrées peu fiables sera impressionnant en démo et inutilisable en exploitation, et la crédibilité dépensée pour le faire approuver ne revient pas.</p>

<p>Réparer la couche en premier fait une annonce plus lente, et un chemin bien plus rapide vers quelque chose qui survit au contact avec la production.</p>
""")

# ----------------------------------------------------------------------- about
about_en = """
<section class="wrap page-head">
  <p class="eyebrow">About</p>
  <h1>A senior-led practice, deliberately small.</h1>
  <p class="lead">Intellora Tech is an engineering consultancy working across data, cloud, AI and security. A collective of specialists (database, cloud, analytics, machine learning, governance and security) led by a principal engineer who staffs each project and reviews what ships. You speak to hands-on engineers throughout, never an account manager.</p>
</section>

<section class="wrap section">
  <div class="capacity rv">
    <p class="eyebrow">How we stay small on purpose</p>
    <h2 style="max-width:24ch">A capped book is the quality control.</h2>
    <p class="lead">We run at most three projects concurrently, not as a scarcity tactic but as the only honest way to promise that the specialists on your platform are genuinely thinking about it, and that the principal can review every piece of work rather than signing off work nobody senior has read.</p>
    <div class="grid c3 mt6">
      <div><p class="mono mb3">We decline</p><p class="soft">Work outside our depth, scope that is genuinely undefined at contracting, and deadlines that would force us to cut the testing or the documentation.</p></div>
      <div><p class="mono mb3">We finish</p><p class="soft">A project is done when it is documented, handed over and running, not when the hours are used up. Overrun on a fixed price is our problem, not yours.</p></div>
      <div><p class="mono mb3">We go narrow</p><p class="soft">One capability, delivered completely, beats a broad project delivered to eighty per cent. If the right answer is a smaller project, we will propose the smaller one.</p></div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <picture>
        <source type="image/webp" srcset="/assets/img/simon-720.webp">
        <img src="/assets/img/simon-720.jpg" width="720" height="720" alt="Portrait of Musisi Simon Peter, principal engineer at Intellora Tech." loading="lazy" decoding="async" style="border-radius:var(--r-lg);max-width:22rem">
      </picture>
    </div>
    <div class="rv">
      <p class="mono mb3">Principal engineer · practice lead</p>
      <h2>Musisi Simon Peter</h2>
      <p class="soft mt4">Leads the practice: sets the engineering standards, staffs each project, and reviews what goes out the door. Roughly a decade of production data engineering across regulated financial services, public-sector systems and international-development programmes.</p>
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
      <div class="card card-accent k-plum"><h3>Machine learning</h3><p>Feature pipelines, training workflows, MLOps and retrieval systems, built by people who ship models, not only notebooks.</p></div>
      <div class="card card-accent k-indigo"><h3>Governance &amp; data quality</h3><p>Lineage, cataloguing, quality enforcement and the evidence trail an auditor or regulator will eventually ask for.</p></div>
      <div class="card card-accent k-deep"><h3>Platform security</h3><p>Access control design, encryption and key management, secrets, and audit logging for the data estate.</p></div>
      <div class="card card-accent k-slate"><h3>Project &amp; delivery management</h3><p>PRINCE2, Agile/Scrum or a PMBOK-aligned blend, chosen to fit the project rather than applied by default, plus the PMO discipline that keeps a programme reportable to a board.</p></div>
    </div>
    <div class="callout mt6"><b>Who you actually speak to.</b> Every call is with a hands-on engineer from the team that would do the work: someone who reads execution plans and writes the code, not an account manager relaying questions back to a delivery team. The principal reviews every project regardless of who leads it.</div>
  </div>
</section>

<section class="wrap section">
  <div class="rv">
    <h2 class="mb5">How a distributed practice works</h2>
    <div class="grid c2">
      <div class="card card-accent k-emerald"><h3>Weekly written update</h3><p>Every Friday from the engineer leading your work: what shipped, what is next, what is blocked, and any change to the estimate, in writing, so it survives being forwarded to your board.</p></div>
      <div class="card card-accent k-indigo"><h3>Working sessions, not status calls</h3><p>Calls are for decisions and joint work. Status arrives in writing beforehand so the call is not spent reading it aloud.</p></div>
      <div class="card card-accent k-gold"><h3>Your tools</h3><p>The team works in your Slack, your Jira, your repository and your cloud account, with access provisioned at least privilege and revoked on handover.</p></div>
      <div class="card card-accent k-coral"><h3>Handover as a piece of work</h3><p>Documentation, runbooks and decision records, plus a live session between your engineers and ours, so the work outlives the project.</p></div>
    </div>
  </div>
</section>"""

about_fr = """
<section class="wrap page-head">
  <p class="eyebrow">À propos</p>
  <h1>Une pratique dirigée par un senior, délibérément restreinte.</h1>
  <p class="lead">Intellora Tech est un cabinet d'ingénierie qui intervient sur les données, le cloud, l'IA et la sécurité. Un collectif de spécialistes (bases de données, cloud, analytique, machine learning, gouvernance et sécurité) dirigé par un ingénieur principal qui compose chaque équipe et relit ce qui est livré. Vous parlez à des ingénieurs opérationnels du début à la fin, jamais à un chargé de compte.</p>
</section>

<section class="wrap section">
  <div class="capacity rv">
    <p class="eyebrow">Comment nous restons volontairement restreints</p>
    <h2 style="max-width:24ch">Un carnet de commandes limité, c'est notre contrôle qualité.</h2>
    <p class="lead">Nous menons au maximum trois projets en même temps, non par tactique de rareté, mais parce que c'est la seule façon honnête de garantir que les spécialistes affectés à votre plateforme y réfléchissent réellement, et que le principal peut relire chaque livrable plutôt que d'approuver un travail que personne de senior n'a lu.</p>
    <div class="grid c3 mt6">
      <div><p class="mono mb3">Nous refusons</p><p class="soft">Un travail hors de notre domaine, un périmètre réellement indéfini à la contractualisation, et des délais qui nous forceraient à réduire les tests ou la documentation.</p></div>
      <div><p class="mono mb3">Nous terminons</p><p class="soft">Un projet est terminé quand il est documenté, transféré et opérationnel, pas quand les heures sont épuisées. Un dépassement sur un prix fixe est notre problème, pas le vôtre.</p></div>
      <div><p class="mono mb3">Nous restons ciblés</p><p class="soft">Une seule capacité livrée entièrement vaut mieux qu'un projet large livré à quatre-vingts pour cent. Si la bonne réponse est un projet plus petit, c'est celui-là que nous proposerons.</p></div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <picture>
        <source type="image/webp" srcset="/assets/img/simon-720.webp">
        <img src="/assets/img/simon-720.jpg" width="720" height="720" alt="Portrait de Musisi Simon Peter, ingénieur principal chez Intellora Tech." loading="lazy" decoding="async" style="border-radius:var(--r-lg);max-width:22rem">
      </picture>
    </div>
    <div class="rv">
      <p class="mono mb3">Ingénieur principal · responsable de la pratique</p>
      <h2>Musisi Simon Peter</h2>
      <p class="soft mt4">Dirige la pratique : fixe les standards d'ingénierie, compose chaque équipe de projet, et relit tout ce qui sort. Environ une décennie d'ingénierie des données en production dans les services financiers réglementés, les systèmes du secteur public et les programmes de développement international.</p>
      <p class="soft mt4">Personnellement le plus expert sur l'interne des bases Oracle, l'architecture d'entrepôts de données d'entreprise et l'ingénierie ETL et ELT. Titulaire d'un MBA et d'une licence en génie informatique.</p>
      <p class="mono mt6 mb3">Certifié en</p>
      <div class="chips"><span class="chip">AWS Solutions Architect</span><span class="chip">Oracle Data Integrator</span><span class="chip">ITIL 4 Foundation</span><span class="chip">PRINCE2 Practitioner</span><span class="chip">Agile Scrum Master</span><span class="chip">COBIT 5 Foundation</span></div>
      <div class="row mt5">
        <a href="/contact/" class="btn btn-p">Réserver un appel</a>
        <a href="/products/" class="btn btn-s">Voir les produits</a>
      </div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="rv">
    <h2 class="mb4">Des spécialistes, adaptés à votre pile technique</h2>
    <p class="lead mb6">Aucun ingénieur seul n'est le plus expert en tout, et nous ne prétendons pas le contraire. La pratique est organisée autour de spécialisations distinctes, et un projet est confié aux personnes dont l'expertise correspond au travail, plutôt qu'à qui est disponible.</p>
    <div class="grid c3">
      <div class="card card-accent k-coral"><h3>Ingénierie des bases de données</h3><p>Interne Oracle, PostgreSQL, SQL Server et MySQL. Modélisation, optimisation, haute disponibilité, migration et Oracle Data Integrator.</p></div>
      <div class="card card-accent k-gold"><h3>Cloud &amp; plateforme</h3><p>Architecture AWS, landing zones, infrastructure as code, CI/CD pour l'infrastructure de données, et ingénierie des coûts.</p></div>
      <div class="card card-accent k-emerald"><h3>Ingénierie analytique</h3><p>Modélisation sémantique, dbt, Oracle Analytics et Power BI, et la gouvernance des indicateurs qui empêche les tableaux de bord de se contredire.</p></div>
      <div class="card card-accent k-plum"><h3>Machine learning</h3><p>Pipelines de features, flux d'entraînement, MLOps et systèmes de récupération, construits par des personnes qui mettent des modèles en production, pas seulement des notebooks.</p></div>
      <div class="card card-accent k-indigo"><h3>Gouvernance &amp; qualité des données</h3><p>Traçabilité, catalogage, application de la qualité et la piste de preuves qu'un auditeur ou un régulateur finira par demander.</p></div>
      <div class="card card-accent k-deep"><h3>Sécurité de la plateforme</h3><p>Conception du contrôle d'accès, chiffrement et gestion des clés, secrets, et journalisation d'audit pour le patrimoine de données.</p></div>
      <div class="card card-accent k-slate"><h3>Gestion de projet &amp; de livraison</h3><p>PRINCE2, Agile/Scrum ou un mélange aligné sur le PMBOK, choisi pour s'adapter au projet plutôt qu'appliqué par défaut, ainsi que la discipline PMO qui garde un programme reportable à un conseil.</p></div>
    </div>
    <div class="callout mt6"><b>À qui vous parlez réellement.</b> Chaque appel se fait avec un ingénieur opérationnel de l'équipe qui ferait le travail : quelqu'un qui lit les plans d'exécution et écrit le code, pas un chargé de compte qui relaie des questions à une équipe de livraison. Le principal relit chaque projet, quel que soit qui le dirige.</div>
  </div>
</section>

<section class="wrap section">
  <div class="rv">
    <h2 class="mb5">Comment fonctionne une pratique distribuée</h2>
    <div class="grid c2">
      <div class="card card-accent k-emerald"><h3>Mise à jour hebdomadaire écrite</h3><p>Chaque vendredi, de la part de l'ingénieur qui dirige votre projet : ce qui a été livré, ce qui vient, ce qui est bloqué, et tout changement à l'estimation, par écrit, pour que cela survive une fois transmis à votre conseil.</p></div>
      <div class="card card-accent k-indigo"><h3>Des sessions de travail, pas des points de statut</h3><p>Les appels servent aux décisions et au travail commun. Le statut arrive par écrit au préalable, pour que l'appel ne soit pas consacré à le lire à voix haute.</p></div>
      <div class="card card-accent k-gold"><h3>Vos outils</h3><p>L'équipe travaille dans votre Slack, votre Jira, votre dépôt de code et votre compte cloud, avec un accès provisionné au moindre privilège et révoqué au transfert.</p></div>
      <div class="card card-accent k-coral"><h3>Le transfert, comme un livrable à part entière</h3><p>Documentation, procédures opérationnelles et comptes-rendus de décisions, plus une session en direct entre vos ingénieurs et les nôtres, pour que le travail survive au projet.</p></div>
    </div>
  </div>
</section>"""

about = blocks(about_en, about_fr) + cta(
    ("Work with the engineers, not the org chart.", "Travaillez avec les ingénieurs, pas avec l'organigramme."),
    ("One paragraph about what is broken is enough to start.",
     "Un paragraphe sur ce qui ne va pas suffit pour démarrer."),
    secondary=("Read the insights", "/blog/"))

write("about", layout("/about/", "About · Intellora Tech",
                      "A distributed engineering practice of specialists across data, cloud, AI and "
                      "security, led by a principal engineer and delivering worldwide.",
                      about, accent="emerald", nav_key="About", crumbs=[(("About", "À propos"), None)]))

# --------------------------------------------------------------------- contact
contact_en = f"""
<section class="wrap page-head">
  <p class="eyebrow">Book a call</p>
  <h1>Two ways to start.</h1>
  <p class="lead">Both are with a hands-on engineer, someone who writes the code, not a salesperson. Pick whichever fits where you are.</p>
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
      <p style="font-size:var(--t-bd)">A working session, not a sales call. We look at your actual setup (schemas, pipelines, cloud bill, whatever is relevant) and you leave with specific answers and a written summary of what we found and what we would do about it.</p>
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
      <div><div><p class="n">Will you sign an NDA before we talk?</p><p class="m">Yes, standard mutual NDAs, usually within a day.</p></div></div>
      <div><div><p class="n">Do you charge for the call?</p><p class="m">The 15-minute intro call is free. The 60-minute technical session is USD 250, and it comes off your first invoice if you hire us.</p></div></div>
      <div><div><p class="n">How do payments work?</p><p class="m">Invoices in USD, EUR, GBP or AED, paid by card or bank transfer. Usually half up front on a first project.</p></div></div>
    </div>
  </div>
</section>"""

contact_fr = f"""
<section class="wrap page-head">
  <p class="eyebrow">Réserver un appel</p>
  <h1>Deux façons de démarrer.</h1>
  <p class="lead">Les deux se font avec un ingénieur opérationnel, quelqu'un qui écrit le code, pas un commercial. Choisissez celle qui correspond à votre situation.</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <div class="card card-accent k-emerald rv" style="padding:var(--s6)">
      <p class="mono">Gratuit · {INTRO_MINS} minutes</p>
      <h3>Appel d'introduction</h3>
      <p style="font-size:var(--t-bd)">Dites-nous ce qui ne va pas. Nous vous disons si nous sommes les bonnes personnes, à peu près ce que cela coûterait, et ce que nous ferions en premier. Si nous ne sommes pas les bons pour ce projet, nous le disons et vous orientons ailleurs.</p>
      <p class="mt4"><b class="ui">Utile pour :</b> <span class="soft">déterminer si cela vaut la peine d'aller plus loin.</span></p>
      <div class="row mt5">
        <a href="mailto:{EMAIL}?subject=Intro%20call%20request" class="btn btn-p">Réserver l'appel gratuit <span class="ar" aria-hidden="true">→</span></a>
      </div>
    </div>

    <div class="card card-accent k-gold rv" style="padding:var(--s6)">
      <p class="mono">250 USD · 60 minutes</p>
      <h3>Consultation technique</h3>
      <p style="font-size:var(--t-bd)">Une session de travail, pas un appel commercial. Nous examinons votre configuration réelle (schémas, pipelines, facture cloud, ce qui est pertinent) et vous partez avec des réponses précises et un résumé écrit de ce que nous avons trouvé et de ce que nous ferions.</p>
      <p class="mt4"><b class="ui">Gratuit si vous nous engagez :</b> <span class="soft">le montant total est déduit de votre première facture.</span></p>
      <div class="row mt5">
        <a href="/payment/?amount={CONSULT_FEE}&amp;for=Technical+consultation+%2860+minutes%29" class="btn btn-p">Réserver et payer <span class="ar" aria-hidden="true">→</span></a>
        <a href="mailto:{EMAIL}?subject=Technical%20consultation" class="btn btn-s">Demander d'abord</a>
      </div>
    </div>
  </div>
  <div class="callout mt6"><b>Pourquoi la session payante a un prix.</b> Une heure de temps d'ingénierie senior consacrée à examiner correctement vos systèmes vous vaut plus qu'une discussion gratuite, et la facturer signifie que nous nous y préparons. Les ingénieurs data seniors indépendants facturent généralement entre 150 et 350 USD de l'heure ; nous nous situons au milieu de cette fourchette, et la remboursons si vous allez de l'avant.</div>
</section>

<section class="wrap section">
  <div class="grid c2">
    <div class="rv">
      <h2 class="mb5">Comment nous contacter</h2>
      <div class="rows">
        <div><div><p class="n">E-mail</p><p class="m">Réponse dans un jour ouvré</p></div><p class="d"><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
        <div><div><p class="n">Structure</p><p class="m">Des spécialistes adaptés à votre pile technique</p></div><p class="d">Équipe distribuée</p></div>
        <div><div><p class="n">Horaires de travail</p><p class="m">Appels programmés dans votre fuseau horaire</p></div><p class="d">Vos heures de bureau</p></div>
        <div><div><p class="n">Langues</p><p class="m">Livraison et documentation</p></div><p class="d">Anglais</p></div>
        <div><div><p class="n">Paiements</p><p class="m">Carte, ou virement bancaire</p></div><p class="d"><a href="/payment/">Paiements</a></p></div>
      </div>
    </div>
    <div class="rv">
      <h2 class="mb5">Ce qui se passe pendant l'appel gratuit</h2>
      <ul class="svc">
        <li><b>Premières minutes · Ce qui ne va pas</b><span>Vous décrivez le problème. Nous demandons qui cela affecte et ce que cela coûte chaque mois que cela continue.</span></li>
        <li><b>Au milieu · Ce que vous avez déjà</b><span>Quelles données existent, comment elles sont organisées, et dans quel état sont les systèmes. C'est ce qui influence le plus le prix, donc nous le demandons tôt.</span></li>
        <li><b>Ensuite · Budget et ordre des travaux</b><span>Si votre budget et notre prix sont dans la même fourchette, et ce qui doit être fait en premier.</span></li>
        <li><b>Dernières minutes · Une réponse franche</b><span>Si nous pouvons aider, qui dirigerait le projet, ce que nous suggérerions, et quand vous l'obtiendrez par écrit.</span></li>
      </ul>
      <div class="callout mt6"><b>N'apportez rien de préparé.</b> Un schéma d'architecture ou une facture cloud récente accélèrent les choses, mais l'appel fonctionne très bien sans l'un ou l'autre.</div>
      <div class="callout mt5"><b>Nous menons trois projets à la fois.</b> S'ils sont tous complets au moment où vous nous écrivez, nous le dirons pendant l'appel et vous donnerons une vraie date de début plutôt que d'accepter le travail en nous dispersant.</div>
    </div>
  </div>
</section>

<section class="wrap section">
  <div class="rv narrow">
    <h2 class="mb5">Avant de nous écrire</h2>
    <div class="rows">
      <div><div><p class="n">Que doit dire un premier e-mail ?</p><p class="m">Un paragraphe sur le problème, à peu près sur quoi cela tourne, et une éventuelle échéance. Rien de formel.</p></div></div>
      <div><div><p class="n">Signerez-vous un accord de confidentialité avant que nous parlions ?</p><p class="m">Oui, des accords de confidentialité mutuels standards, généralement dans la journée.</p></div></div>
      <div><div><p class="n">Facturez-vous l'appel ?</p><p class="m">L'appel d'introduction de 15 minutes est gratuit. La session technique de 60 minutes coûte 250 USD, déduits de votre première facture si vous nous engagez.</p></div></div>
      <div><div><p class="n">Comment fonctionnent les paiements ?</p><p class="m">Factures en USD, EUR, GBP ou AED, payées par carte ou virement bancaire. Généralement la moitié à l'avance pour un premier projet.</p></div></div>
    </div>
  </div>
</section>"""

contact = blocks(contact_en, contact_fr) + cta(
    ("Tell us what is broken.", "Dites-nous ce qui ne va pas."),
    ("One paragraph is enough. You will hear back within one business day.",
     "Un paragraphe suffit. Vous aurez une réponse dans un jour ouvré."),
    primary=("Email us", "mailto:%s?subject=Discovery%%20call%%20request" % EMAIL),
    secondary=("Pay an invoice", "/payment/"))

write("contact", layout("/contact/", "Contact · Intellora Tech",
                        "Two ways to start: a free 15-minute intro call, or a paid 60-minute technical session with a "
                        "senior engineer, refunded against your first invoice.",
                        contact, accent="emerald", crumbs=[("Contact", None)]))

# --------------------------------------------------------------------- payment
payment = f"""
<section class="wrap page-head">
  <p class="eyebrow">{bi(("Secure payment", "Paiement sécurisé"))}</p>
  <h1>{bi(("Pay securely by card.", "Payez en toute sécurité par carte."))}</h1>
  <p class="lead">{bi(("For paying an invoice, a deposit, or a booked technical session. Payment happens on Stripe's own page: your card number is typed there, never here.",
                        "Pour régler une facture, un acompte, ou une session technique réservée. Le paiement se fait sur la page de Stripe : votre numéro de carte y est saisi, jamais ici."))}</p>
</section>

<section class="wrap">
  <div class="grid c2">
    <div class="rv">
      <div class="card" style="padding:var(--s6)">
        <form id="pay-form" novalidate>
          <div id="pay-err" class="alert" role="alert" hidden></div>

          <div class="field">
            <label for="pay-amount">{bi(("Amount (USD)", "Montant (USD)"))}</label>
            <input type="number" id="pay-amount" name="amount" min="1" max="250000" step="0.01" inputmode="decimal" placeholder="1500.00" data-ph-en="1500.00" data-ph-fr="1500.00" required>
            <span class="hint">{bi(("The figure on your invoice, proposal, or USD 250 for a technical session.",
                                     "Le montant indiqué sur votre facture, votre proposition, ou 250 USD pour une session technique."))}</span>
          </div>

          <div class="field">
            <label for="pay-reference">{bi(("Invoice or reference number", "Numéro de facture ou de référence"))}</label>
            <input type="text" id="pay-reference" name="reference" maxlength="100" placeholder="INV-0042">
          </div>

          <div class="field">
            <label for="pay-description">{bi(("What this payment is for", "Objet de ce paiement"))}</label>
            <input type="text" id="pay-description" name="description" maxlength="200" placeholder="Deposit for data platform build" data-ph-en="Deposit for data platform build" data-ph-fr="Acompte pour la construction d'une plateforme de données">
          </div>

          <button type="submit" id="pay-btn" class="btn btn-p" style="width:100%;justify-content:center">{bi(("Pay with Visa / Mastercard", "Payer avec Visa / Mastercard"))} <span class="ar" aria-hidden="true">→</span></button>

          <noscript><div class="callout mt5">This page needs JavaScript to open a secure checkout session. Email <a href="mailto:{EMAIL}">{EMAIL}</a> to arrange payment another way.</div></noscript>

          <div class="trust">
            <span>🔒 {bi(("TLS encrypted", "Chiffré en TLS"))}</span>
            <span>{bi(("Processed by Stripe · PCI DSS Level 1", "Traité par Stripe · PCI DSS niveau 1"))}</span>
            <span>Visa · Mastercard · Amex</span>
          </div>
        </form>
      </div>
    </div>

    <div class="rv">
      <h2 class="mb5">{bi(("How this works", "Comment cela fonctionne"))}</h2>
      <ul class="svc">
        <li><b>{bi(("1 · Enter the amount", "1 · Indiquez le montant"))}</b><span>{bi(("Use the figure from your invoice or written proposal, and add the reference so we can match the payment.",
                                                                                       "Utilisez le montant de votre facture ou de votre proposition écrite, et ajoutez la référence pour que nous puissions rapprocher le paiement."))}</span></li>
        <li><b>{bi(("2 · You are redirected to Stripe", "2 · Vous êtes redirigé vers Stripe"))}</b><span>{bi(("Card number, expiry and CVC are entered on Stripe's own page, over a connection Stripe controls end to end.",
                                                                                                              "Le numéro de carte, la date d'expiration et le CVC sont saisis sur la page de Stripe, via une connexion que Stripe contrôle de bout en bout."))}</span></li>
        <li><b>{bi(("3 · Instant confirmation", "3 · Confirmation instantanée"))}</b><span>{bi(("You return here with an on-screen confirmation, and Stripe emails your receipt automatically.",
                                                                                                  "Vous revenez ici avec une confirmation à l'écran, et Stripe vous envoie automatiquement votre reçu par e-mail."))}</span></li>
      </ul>
      <div class="callout mt6"><b>{bi(("Why we never take card numbers directly.", "Pourquoi nous ne prenons jamais les numéros de carte directement."))}</b> {bi(("Routing payment through Stripe's hosted checkout keeps Intellora Tech out of PCI-DSS scope entirely, the same standard used by companies far larger than us.",
                                                                                                                                                                              "Faire passer le paiement par le checkout hébergé de Stripe maintient Intellora Tech entièrement hors du périmètre PCI-DSS, la même norme utilisée par des entreprises bien plus grandes que nous."))}</div>
    </div>
  </div>
</section>
"""

write("payment", layout("/payment/", "Pay an invoice · Intellora Tech",
                        "Pay an invoice, deposit or booked technical session securely by Visa or Mastercard.",
                        payment, accent="emerald", nav_key="Payments", crumbs=[(("Payments", "Paiements"), None)]))

success = f"""
<section class="wrap page-head ctr">
  <p class="eyebrow" style="margin-inline:auto">{bi(("Payment received", "Paiement reçu"))}</p>
  <h1 style="max-width:20ch;margin-inline:auto">{bi(("Thank you. That is settled.", "Merci. C'est réglé."))}</h1>
  <p class="lead" style="margin-inline:auto">{bi(("Stripe has processed your card payment and emailed your receipt. We will be in touch shortly to confirm next steps.",
                                                   "Stripe a traité votre paiement par carte et vous a envoyé votre reçu par e-mail. Nous vous recontacterons prochainement pour confirmer les prochaines étapes."))}</p>
  <p id="confirm-box" class="mono mt5" hidden style="color:var(--accent)"></p>
  <div class="row mt6" style="justify-content:center">
    <a href="/" class="btn btn-p">{bi(("Back to home", "Retour à l'accueil"))}</a>
    <a href="/contact/" class="btn btn-s">{bi(("Contact us", "Nous contacter"))}</a>
  </div>
</section>
"""
write("payment/success", layout("/payment/success/", "Payment received · Intellora Tech",
                                "Your payment to Intellora Tech has been received.",
                                success, accent="emerald", noindex=True))

cancel = f"""
<section class="wrap page-head ctr">
  <p class="eyebrow" style="margin-inline:auto">{bi(("Payment cancelled", "Paiement annulé"))}</p>
  <h1 style="max-width:20ch;margin-inline:auto">{bi(("No charge was made.", "Aucun montant n'a été débité."))}</h1>
  <p class="lead" style="margin-inline:auto">{bi(("You can try again whenever you are ready, or email us if something went wrong along the way.",
                                                   "Vous pouvez réessayer quand vous le souhaitez, ou nous écrire si quelque chose s'est mal passé."))}</p>
  <div class="row mt6" style="justify-content:center">
    <a href="/payment/" class="btn btn-p">{bi(("Try again", "Réessayer"))}</a>
    <a href="/contact/" class="btn btn-s">{bi(("Contact us", "Nous contacter"))}</a>
  </div>
</section>
"""
write("payment/cancel", layout("/payment/cancel/", "Payment cancelled · Intellora Tech",
                               "Your payment was cancelled and no charge was made.",
                               cancel, accent="emerald", noindex=True))

# ------------------------------------------------------------- sitemap & robots
urls = ["/", "/products/", "/projects/", "/blog/", "/about/", "/contact/", "/payment/",
        "/tools/", "/tools/estimator/", "/tools/maturity/"]
urls += ["/products/%s/" % s for s, _, _, _, _, _ in PRODUCTS]
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

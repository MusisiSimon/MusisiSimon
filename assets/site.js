/* ==========================================================
   INTELLORA TECH: SHARED BEHAVIOUR
   Progressive enhancement. Every page reads without JS.
   ========================================================== */
(function () {
  'use strict';
  var RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- theme ---------- */
  (function () {
    var btn = $('#theme');
    if (!btn) return;
    var KEY = 'intellora-theme';
    function isDark() {
      var cur = document.documentElement.getAttribute('data-theme');
      return cur === 'dark' || (!cur && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
    function label() {
      btn.setAttribute('aria-label', isDark() ? 'Switch to light theme' : 'Switch to dark theme');
    }
    label();
    btn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem(KEY, next); } catch (e) {}
      label();
    });
  })();

  /* ---------- language ---------- */
  var LANG_KEY = 'intellora-lang';
  function getLang() {
    return document.documentElement.getAttribute('data-lang') === 'fr' ? 'fr' : 'en';
  }
  function applyLang(lang) {
    document.documentElement.lang = lang;
    document.documentElement.setAttribute('data-lang', lang);
    $$('.i18n').forEach(function (el) { el.hidden = el.getAttribute('lang') !== lang; });
    $$('[data-en]').forEach(function (el) {
      var v = lang === 'fr' ? el.getAttribute('data-fr') : el.getAttribute('data-en');
      if (v !== null) el.textContent = v;
    });
    $$('[data-aria-en]').forEach(function (el) {
      var v = lang === 'fr' ? el.getAttribute('data-aria-fr') : el.getAttribute('data-aria-en');
      if (v !== null) el.setAttribute('aria-label', v);
    });
    $$('[data-ph-en]').forEach(function (el) {
      var v = lang === 'fr' ? el.getAttribute('data-ph-fr') : el.getAttribute('data-ph-en');
      if (v !== null) el.setAttribute('placeholder', v);
    });
    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: lang } }));
  }
  (function () {
    var btn = $('#langBtn');
    applyLang(getLang());
    if (!btn) return;
    btn.addEventListener('click', function () {
      var next = getLang() === 'fr' ? 'en' : 'fr';
      try { localStorage.setItem(LANG_KEY, next); } catch (e) {}
      applyLang(next);
    });
  })();

  /* ---------- mobile nav ---------- */
  (function () {
    var b = $('#burger'), m = $('#mobile');
    if (!b || !m) return;
    function shut() { m.classList.remove('open'); b.classList.remove('on'); b.setAttribute('aria-expanded', 'false'); }
    b.addEventListener('click', function () {
      var open = m.classList.toggle('open');
      b.classList.toggle('on', open);
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    m.addEventListener('click', function (e) { if (e.target.tagName === 'A') shut(); });
    window.addEventListener('resize', function () { if (window.innerWidth > 1140) shut(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') shut(); });
  })();

  /* ---------- reveals ---------- */
  (function () {
    var els = $$('.rv');
    if (!els.length) return;
    if (RM || !('IntersectionObserver' in window)) { els.forEach(function (e) { e.classList.add('on'); }); return; }
    var io = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('on'); io.unobserve(e.target); } });
    }, { threshold: 0.06, rootMargin: '0px 0px -30px 0px' });
    els.forEach(function (e) { io.observe(e); });
  })();

  /* ---------- currency ---------- */
  var CUR = { USD: { s: '$', r: 1 }, EUR: { s: '€', r: 0.92 }, GBP: { s: '£', r: 0.79 }, AED: { s: 'AED ', r: 3.67 } };
  var curCode = 'USD';
  function fmt(usd) {
    var c = CUR[curCode], v = Math.round(usd * c.r / 100) * 100;
    return c.s + v.toLocaleString('en-US');
  }

  /* ---------- programme estimator ---------- */
  (function () {
    var root = $('#est');
    if (!root) return;

    var BASE = {
      assess:   { p: 4200,  w: 3,  l: 'Assessment or proof of concept', lFr: 'Évaluation ou preuve de concept' },
      optimise: { p: 6800,  w: 4,  l: 'Optimise an existing platform', lFr: 'Optimiser une plateforme existante' },
      build:    { p: 15000, w: 9,  l: 'New platform or product build', lFr: "Construction d'une nouvelle plateforme ou d'un produit" },
      migrate:  { p: 20000, w: 12, l: 'Migration or modernisation', lFr: 'Migration ou modernisation' }
    };
    var PILLAR = {
      analytics:  { p: 1.00, w: 1.00, l: 'Analytics & BI', lFr: 'Analytique & BI' },
      governance: { p: 1.10, w: 1.12, l: 'Governance & compliance', lFr: 'Gouvernance & conformité' },
      security:   { p: 1.15, w: 1.08, l: 'Security & data protection', lFr: 'Sécurité & protection des données' },
      ai:         { p: 1.30, w: 1.22, l: 'AI & machine learning', lFr: 'IA & machine learning' },
      database:   { p: 1.05, w: 1.00, l: 'Database engineering', lFr: 'Ingénierie des bases de données' },
      cloud:      { p: 1.12, w: 1.05, l: 'AWS cloud architecture', lFr: 'Architecture cloud AWS' },
      delivery:   { p: 0.92, w: 1.10, l: 'Project & delivery management', lFr: 'Gestion de projet & de livraison' }
    };
    var M = {
      cx: { std: { p: 1.00, w: 1.00, l: 'Standard complexity', lFr: 'Complexité standard' }, mod: { p: 1.45, w: 1.30, l: 'Moderate complexity', lFr: 'Complexité modérée' }, adv: { p: 2.05, w: 1.60, l: 'Advanced complexity', lFr: 'Complexité avancée' } },
      sz: { s: { p: 0.80, w: 0.80, l: 'Small scope', lFr: 'Petit périmètre' }, m: { p: 1.30, w: 1.25, l: 'Medium scope', lFr: 'Périmètre moyen' }, l: { p: 2.00, w: 1.75, l: 'Large scope', lFr: 'Grand périmètre' } },
      gv: { light: { p: 1.00, w: 1.00, l: 'Light governance', lFr: 'Gouvernance légère' }, standard: { p: 1.12, w: 1.08, l: 'Standard governance', lFr: 'Gouvernance standard' }, regulated: { p: 1.38, w: 1.22, l: 'Regulated governance', lFr: 'Gouvernance réglementée' } },
      tl: { relaxed: { p: 0.94, w: 1.30, l: 'Relaxed timeline', lFr: 'Calendrier détendu' }, standard: { p: 1.00, w: 1.00, l: 'Standard timeline', lFr: 'Calendrier standard' }, rush: { p: 1.32, w: 0.70, l: 'Compressed timeline', lFr: 'Calendrier comprimé' } }
    };
    var PH = {
      assess:   [['Discovery and analysis', 'Découverte et analyse', 45], ['Assessment work', "Travail d'évaluation", 33], ['Findings and roadmap', 'Conclusions et feuille de route', 22]],
      optimise: [['Audit and analysis', 'Audit et analyse', 38], ['Implementation', 'Mise en œuvre', 37], ['Validation', 'Validation', 15], ['Report and handover', 'Rapport et transfert', 10]],
      build:    [['Discovery and design', 'Découverte et conception', 20], ['Build', 'Construction', 45], ['Validation and testing', 'Validation et tests', 20], ['Documentation and handover', 'Documentation et transfert', 15]],
      migrate:  [['Discovery and mapping', 'Découverte et cartographie', 25], ['Build and migrate', 'Construction et migration', 38], ['Parallel validation', 'Validation en parallèle', 24], ['Cutover and handover', 'Bascule et transfert', 13]]
    };

    var st = { type: null, pillar: null, cx: null, sz: null, gv: null, tl: null };
    var step = 1;

    function calc() {
      var b = BASE[st.type], pl = PILLAR[st.pillar];
      var p = b.p * pl.p * M.cx[st.cx].p * M.sz[st.sz].p * M.gv[st.gv].p * M.tl[st.tl].p;
      var w = b.w * pl.w * M.cx[st.cx].w * M.sz[st.sz].w * M.gv[st.gv].w * M.tl[st.tl].w;
      return { lo: p * 0.84, hi: p * 1.18, wLo: Math.max(2, Math.round(w * 0.85)), wHi: Math.round(w * 1.15) };
    }

    function paint() {
      if (!st.type || !st.pillar || !st.cx || !st.sz || !st.gv || !st.tl) return;
      var fr = getLang() === 'fr';
      var lab = function (o) { return fr ? o.lFr : o.l; };
      var r = calc(), b = BASE[st.type];
      $('#resRange').textContent = fmt(r.lo) + ' – ' + fmt(r.hi);
      $('#resDur').textContent = fr
        ? r.wLo + '–' + r.wHi + ' semaines · réalisé à distance · prix fixe une fois signé'
        : r.wLo + '–' + r.wHi + ' weeks · done remotely · fixed price once signed';
      $('#resTags').innerHTML = [lab(b), lab(PILLAR[st.pillar]), lab(M.cx[st.cx]), lab(M.sz[st.sz]), lab(M.gv[st.gv]), lab(M.tl[st.tl])]
        .map(function (t) { return '<span class="chip">' + t + '</span>'; }).join('');
      $('#resPhases').innerHTML = PH[st.type].map(function (p) {
        return '<div class="mb4"><div style="display:flex;justify-content:space-between;gap:.625rem;font-size:.875rem;margin-bottom:.375rem" class="ui">' +
          '<b style="font-weight:600">' + (fr ? p[1] : p[0]) + '</b><span class="mono">' + p[2] + '% · ' + fmt(r.lo * p[2] / 100) + '–' + fmt(r.hi * p[2] / 100) + '</span></div>' +
          '<div class="bar"><i style="width:' + p[2] + '%"></i></div></div>';
      }).join('');

      var sum = fr
        ? 'Estimation de prix, intelloratech.net\n\n' +
          'Ce que nous voulons : ' + lab(b) + '\nProduit principal : ' + lab(PILLAR[st.pillar]) + '\n' +
          'Complexité : ' + lab(M.cx[st.cx]) + '\nTaille : ' + lab(M.sz[st.sz]) + '\n' +
          'Règles à respecter : ' + lab(M.gv[st.gv]) + '\nCalendrier : ' + lab(M.tl[st.tl]) + '\n\n' +
          'Prix estimé : ' + fmt(r.lo) + ' – ' + fmt(r.hi) + ' (' + curCode + ')\n' +
          'Durée estimée : ' + r.wLo + '–' + r.wHi + ' semaines\n\nNotre situation :\n'
        : 'Price estimate, intelloratech.net\n\n' +
          'What we want: ' + lab(b) + '\nMain product: ' + lab(PILLAR[st.pillar]) + '\n' +
          'How complex: ' + lab(M.cx[st.cx]) + '\nHow big: ' + lab(M.sz[st.sz]) + '\n' +
          'Rules to satisfy: ' + lab(M.gv[st.gv]) + '\nTiming: ' + lab(M.tl[st.tl]) + '\n\n' +
          'Estimated price: ' + fmt(r.lo) + ' – ' + fmt(r.hi) + ' (' + curCode + ')\n' +
          'Estimated time: ' + r.wLo + '–' + r.wHi + ' weeks\n\nOur situation:\n';
      window.__estSum = sum;
      var ml = $('#resMail');
      if (ml) ml.href = 'mailto:support@intelloratech.net?subject=' + encodeURIComponent((fr ? 'Demande d\'appel : ' : 'Call request: ') + lab(b)) + '&body=' + encodeURIComponent(sum);
    }
    document.addEventListener('langchange', function () { if (step === 3) paint(); });

    var sel = $('#cur');
    if (sel) sel.addEventListener('change', function () {
      curCode = sel.value;
      if (step === 3) paint();
    });

    function go(n) {
      step = n;
      $$('[data-pane]', root).forEach(function (p) { p.hidden = (+p.dataset.pane !== n); });
      $$('[data-stepname]', root).forEach(function (s) {
        s.setAttribute('aria-current', +s.dataset.stepname === n ? 'step' : 'false');
      });
      var bar = $('#estBar');
      if (bar) bar.style.width = (n * 33.34) + '%';
      if (n === 3) paint();
      var y = root.getBoundingClientRect().top + window.pageYOffset - 90;
      window.scrollTo({ top: y, behavior: RM ? 'auto' : 'smooth' });
    }

    function gate() {
      var n1 = $('#estN1'), n2 = $('#estN2');
      if (n1) n1.disabled = !(st.type && st.pillar);
      if (n2) n2.disabled = !(st.cx && st.sz && st.gv && st.tl);
    }

    $$('[data-grp]', root).forEach(function (g) {
      g.addEventListener('click', function (e) {
        var c = e.target.closest('.opt');
        if (!c) return;
        $$('.opt', g).forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
        c.setAttribute('aria-pressed', 'true');
        st[g.dataset.grp] = c.dataset.v;
        gate();
      });
    });

    var n1 = $('#estN1'), n2 = $('#estN2'), b2 = $('#estB2'), b3 = $('#estB3');
    if (n1) n1.addEventListener('click', function () { if (st.type && st.pillar) go(2); });
    if (n2) n2.addEventListener('click', function () { if (st.cx && st.sz && st.gv && st.tl) go(3); });
    if (b2) b2.addEventListener('click', function () { go(1); });
    if (b3) b3.addEventListener('click', function () { go(2); });

    var cp = $('#resCopy');
    if (cp) cp.addEventListener('click', function () {
      var t = window.__estSum || '';
      var done = function () {
        var c = $('#resCopied');
        if (!c) return;
        c.hidden = false;
        setTimeout(function () { c.hidden = true; }, 2600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, done);
      else {
        var ta = document.createElement('textarea');
        ta.value = t;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        ta.remove();
        done();
      }
    });
    gate();
  })();

  /* ---------- maturity check ---------- */
  (function () {
    var root = $('#mat');
    if (!root) return;
    var qs = $$('[data-q]', root), out = $('#matOut'), btn = $('#matGo');
    var STAGE = [
      { max: 11, n: 'Ad hoc', nFr: 'Improvisé',
        d: 'Data lives in operational systems and spreadsheets. Reporting is manual and answers disagree depending on who produced them. The first win is a single reliable pipeline and one agreed set of definitions.',
        dFr: 'Les données vivent dans les systèmes opérationnels et les feuilles de calcul. Le reporting est manuel et les réponses diffèrent selon qui les a produites. Le premier gain est un pipeline fiable unique et un ensemble de définitions convenu.',
        p: ['database', 'analytics'] },
      { max: 17, n: 'Repeatable', nFr: 'Reproductible',
        d: 'Pipelines exist but break quietly, and nobody can trace a number back to its source. The priority is orchestration you can trust and lineage you can show an auditor.',
        dFr: 'Des pipelines existent mais se cassent silencieusement, et personne ne peut retracer un chiffre jusqu\'à sa source. La priorité est une orchestration fiable et une traçabilité que vous pouvez montrer à un auditeur.',
        p: ['analytics', 'governance'] },
      { max: 23, n: 'Governed', nFr: 'Gouverné',
        d: 'The platform is reliable and documented. The next constraints are cost efficiency, access control, and preparing the data layer to support models rather than dashboards alone.',
        dFr: 'La plateforme est fiable et documentée. Les contraintes suivantes sont l\'efficacité des coûts, le contrôle d\'accès, et la préparation de la couche de données pour supporter des modèles plutôt que seulement des tableaux de bord.',
        p: ['cloud', 'security'] },
      { max: 99, n: 'Optimising', nFr: 'En optimisation',
        d: 'Strong foundations already in place. Value now comes from advanced workloads: machine learning in production, real-time decisioning, and formal model governance.',
        dFr: 'Des fondations solides sont déjà en place. La valeur vient désormais des charges de travail avancées : machine learning en production, prise de décision en temps réel, et gouvernance formelle des modèles.',
        p: ['ai', 'governance'] }
    ];
    var NAMES = {
      analytics: 'Analytics & BI', governance: 'Governance & compliance', security: 'Security & data protection',
      ai: 'AI & machine learning', database: 'Database engineering', cloud: 'AWS cloud architecture'
    };
    var NAMES_FR = {
      analytics: 'Analytique & BI', governance: 'Gouvernance & conformité', security: 'Sécurité & protection des données',
      ai: 'IA & machine learning', database: 'Ingénierie des bases de données', cloud: 'Architecture cloud AWS'
    };
    var LINKS = {
      analytics: '/products/analytics-bi/', governance: '/products/data-governance/',
      security: '/products/security/', ai: '/products/ai-machine-learning/',
      cloud: '/products/aws-cloud/', database: '/products/database-engineering/'
    };

    function render() {
      if (out.hidden) return;
      var fr = getLang() === 'fr';
      var total = 0, answered = 0;
      qs.forEach(function (q) {
        var sel = $('select', q);
        if (sel && sel.value !== '') { total += parseInt(sel.value, 10); answered++; }
      });
      if (answered < qs.length) {
        out.innerHTML = '<div class="alert">' + (fr
          ? 'Répondez aux ' + qs.length + ' questions pour voir votre résultat.'
          : 'Answer all ' + qs.length + ' questions to see your result.') + '</div>';
        return;
      }
      var s = STAGE.filter(function (x) { return total <= x.max; })[0];
      var names = fr ? NAMES_FR : NAMES;
      out.innerHTML =
        '<div class="card" style="border-color:var(--accent)">' +
        '<p class="mono mb4">' + (fr ? 'Résultat · score ' + total + ' sur ' + (qs.length * 4) : 'Result · score ' + total + ' of ' + (qs.length * 4)) + '</p>' +
        '<h3 style="color:var(--accent)">' + (fr ? s.nFr : s.n) + '</h3>' +
        '<p class="mb5">' + (fr ? s.dFr : s.d) + '</p>' +
        '<p class="mono mb4">' + (fr ? 'Par où nous commencerions' : 'Where we would start') + '</p>' +
        '<div class="chips">' + s.p.map(function (k) {
          return '<a class="chip" href="' + LINKS[k] + '">' + names[k] + '</a>';
        }).join('') + '</div>' +
        '</div>';
    }

    if (btn) btn.addEventListener('click', function () {
      out.hidden = false;
      render();
      out.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'nearest' });
    });
    document.addEventListener('langchange', render);
  })();

  /* ---------- payment form ---------- */
  (function () {
    var form = $('#pay-form');
    if (!form) return;
    var btn = $('#pay-btn'), errBox = $('#pay-err'), btnLabel = btn.innerHTML;

    /* let a link prefill the form, e.g. /payment/?amount=250&for=Consultation */
    (function () {
      var q = new URLSearchParams(window.location.search);
      var amount = parseFloat(q.get('amount'));
      if (isFinite(amount) && amount > 0 && amount <= 250000) $('#pay-amount').value = amount.toFixed(2);
      var what = q.get('for');
      if (what) $('#pay-description').value = what.slice(0, 200);
      var ref = q.get('ref');
      if (ref) $('#pay-reference').value = ref.slice(0, 100);
    })();

    function showError(msg) { errBox.textContent = msg; errBox.hidden = false; }
    function clearError() { errBox.hidden = true; errBox.textContent = ''; }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      clearError();
      var fr = getLang() === 'fr';

      var amount = parseFloat($('#pay-amount').value);
      if (!isFinite(amount) || amount <= 0) {
        showError(fr ? 'Indiquez un montant valide supérieur à zéro.' : 'Enter a valid amount greater than zero.');
        return;
      }
      if (amount > 250000) {
        showError(fr
          ? 'Pour les montants supérieurs à 250 000 USD, merci d\'écrire à support@intelloratech.net pour organiser le paiement.'
          : 'For amounts above USD 250,000 please email support@intelloratech.net to arrange payment.');
        return;
      }

      var reference = $('#pay-reference').value.trim();
      var description = $('#pay-description').value.trim();

      btn.disabled = true;
      btn.textContent = fr ? 'Redirection vers le paiement sécurisé…' : 'Redirecting to secure checkout…';

      fetch('/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount, reference: reference, description: description })
      })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (result) {
          if (!result.ok || !result.data || !result.data.url) {
            throw new Error((result.data && result.data.error) ||
              (fr ? 'Impossible de démarrer le paiement. Merci de réessayer.' : 'Unable to start checkout. Please try again.'));
          }
          window.location.href = result.data.url;
        })
        .catch(function (err) {
          showError(err.message || (fr
            ? 'Une erreur est survenue. Merci de réessayer ou d\'écrire à support@intelloratech.net.'
            : 'Something went wrong. Please try again or email support@intelloratech.net.'));
          btn.disabled = false;
          btn.innerHTML = btnLabel;
        });
    });
  })();

  /* ---------- payment confirmation ---------- */
  (function () {
    var box = $('#confirm-box');
    if (!box) return;
    var sessionId = new URLSearchParams(window.location.search).get('session_id');
    if (!sessionId) return;
    fetch('/verify-payment?session_id=' + encodeURIComponent(sessionId))
      .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
      .then(function (result) {
        if (!result.ok) return;
        var d = result.data;
        if (d.status !== 'paid' && d.status !== 'no_payment_required') return;
        var amount = (d.amount_total / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        var fr = getLang() === 'fr';
        var text = (fr ? 'Confirmé : ' : 'Confirmed: ') + (d.currency || 'usd').toUpperCase() + ' ' + amount;
        if (d.reference) text += (fr ? ' · Réf ' : ' · Ref ') + d.reference;
        box.textContent = text;
        box.hidden = false;
      })
      .catch(function () {});
  })();
})();

/* ==========================================================
   INTELLORA TECH — SHARED BEHAVIOUR
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
    window.addEventListener('resize', function () { if (window.innerWidth > 1000) shut(); });
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
      assess:   { p: 4200,  w: 3,  l: 'Assessment or proof of concept' },
      optimise: { p: 6800,  w: 4,  l: 'Optimise an existing platform' },
      build:    { p: 15000, w: 9,  l: 'New platform or product build' },
      migrate:  { p: 20000, w: 12, l: 'Migration or modernisation' }
    };
    var PILLAR = {
      analytics:  { p: 1.00, w: 1.00, l: 'Analytics & BI' },
      governance: { p: 1.10, w: 1.12, l: 'Governance & compliance' },
      security:   { p: 1.15, w: 1.08, l: 'Security & data protection' },
      ai:         { p: 1.30, w: 1.22, l: 'AI & machine learning' },
      database:   { p: 1.05, w: 1.00, l: 'Database engineering' },
      cloud:      { p: 1.12, w: 1.05, l: 'AWS cloud architecture' }
    };
    var M = {
      cx: { std: { p: 1.00, w: 1.00, l: 'Standard complexity' }, mod: { p: 1.45, w: 1.30, l: 'Moderate complexity' }, adv: { p: 2.05, w: 1.60, l: 'Advanced complexity' } },
      sz: { s: { p: 0.80, w: 0.80, l: 'Small scope' }, m: { p: 1.30, w: 1.25, l: 'Medium scope' }, l: { p: 2.00, w: 1.75, l: 'Large scope' } },
      gv: { light: { p: 1.00, w: 1.00, l: 'Light governance' }, standard: { p: 1.12, w: 1.08, l: 'Standard governance' }, regulated: { p: 1.38, w: 1.22, l: 'Regulated governance' } },
      tl: { relaxed: { p: 0.94, w: 1.30, l: 'Relaxed timeline' }, standard: { p: 1.00, w: 1.00, l: 'Standard timeline' }, rush: { p: 1.32, w: 0.70, l: 'Compressed timeline' } }
    };
    var PH = {
      assess:   [['Discovery and analysis', 45], ['Assessment work', 33], ['Findings and roadmap', 22]],
      optimise: [['Audit and analysis', 38], ['Implementation', 37], ['Validation', 15], ['Report and handover', 10]],
      build:    [['Discovery and design', 20], ['Build', 45], ['Validation and testing', 20], ['Documentation and handover', 15]],
      migrate:  [['Discovery and mapping', 25], ['Build and migrate', 38], ['Parallel validation', 24], ['Cutover and handover', 13]]
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
      var r = calc(), b = BASE[st.type];
      $('#resRange').textContent = fmt(r.lo) + ' – ' + fmt(r.hi);
      $('#resDur').textContent = r.wLo + '–' + r.wHi + ' weeks · delivered remotely · fixed price on signature';
      $('#resTags').innerHTML = [b.l, PILLAR[st.pillar].l, M.cx[st.cx].l, M.sz[st.sz].l, M.gv[st.gv].l, M.tl[st.tl].l]
        .map(function (t) { return '<span class="chip">' + t + '</span>'; }).join('');
      $('#resPhases').innerHTML = PH[st.type].map(function (p) {
        return '<div class="mb4"><div style="display:flex;justify-content:space-between;gap:.625rem;font-size:.875rem;margin-bottom:.375rem" class="ui">' +
          '<b style="font-weight:600">' + p[0] + '</b><span class="mono">' + p[1] + '% · ' + fmt(r.lo * p[1] / 100) + '–' + fmt(r.hi * p[1] / 100) + '</span></div>' +
          '<div class="bar"><i style="width:' + p[1] + '%"></i></div></div>';
      }).join('');

      var sum = 'Programme estimate — intelloratech.com\n\n' +
        'Objective: ' + b.l + '\nPrimary capability: ' + PILLAR[st.pillar].l + '\n' +
        'Complexity: ' + M.cx[st.cx].l + '\nScope: ' + M.sz[st.sz].l + '\n' +
        'Governance: ' + M.gv[st.gv].l + '\nTimeline: ' + M.tl[st.tl].l + '\n\n' +
        'Indicative range: ' + fmt(r.lo) + ' – ' + fmt(r.hi) + ' (' + curCode + ')\n' +
        'Indicative duration: ' + r.wLo + '–' + r.wHi + ' weeks\n\nOur situation:\n';
      window.__estSum = sum;
      var ml = $('#resMail');
      if (ml) ml.href = 'mailto:hello@intelloratech.com?subject=' + encodeURIComponent('Scoping call — ' + b.l) + '&body=' + encodeURIComponent(sum);
    }

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
      { max: 11, n: 'Ad hoc', d: 'Data lives in operational systems and spreadsheets. Reporting is manual and answers disagree depending on who produced them. The first win is a single reliable pipeline and one agreed set of definitions.', p: ['database', 'analytics'] },
      { max: 17, n: 'Repeatable', d: 'Pipelines exist but break quietly, and nobody can trace a number back to its source. The priority is orchestration you can trust and lineage you can show an auditor.', p: ['analytics', 'governance'] },
      { max: 23, n: 'Governed', d: 'The platform is reliable and documented. The next constraints are cost efficiency, access control, and preparing the data layer to support models rather than dashboards alone.', p: ['cloud', 'security'] },
      { max: 99, n: 'Optimising', d: 'Strong foundations already in place. Value now comes from advanced workloads — machine learning in production, real-time decisioning, and formal model governance.', p: ['ai', 'governance'] }
    ];
    var NAMES = {
      analytics: 'Analytics & BI', governance: 'Governance & compliance', security: 'Security & data protection',
      ai: 'AI & machine learning', database: 'Database engineering', cloud: 'AWS cloud architecture'
    };
    var LINKS = {
      analytics: '/capabilities/analytics-bi/', governance: '/capabilities/data-governance/',
      security: '/capabilities/security/', ai: '/capabilities/ai-machine-learning/',
      cloud: '/capabilities/aws-cloud/', database: '/capabilities/database-engineering/'
    };

    if (btn) btn.addEventListener('click', function () {
      var total = 0, answered = 0;
      qs.forEach(function (q) {
        var sel = $('select', q);
        if (sel && sel.value !== '') { total += parseInt(sel.value, 10); answered++; }
      });
      out.hidden = false;
      if (answered < qs.length) {
        out.innerHTML = '<div class="alert">Answer all ' + qs.length + ' questions to see your result.</div>';
        return;
      }
      var s = STAGE.filter(function (x) { return total <= x.max; })[0];
      out.innerHTML =
        '<div class="card" style="border-color:var(--accent)">' +
        '<p class="mono mb4">Result · score ' + total + ' of ' + (qs.length * 4) + '</p>' +
        '<h3 style="color:var(--accent)">' + s.n + '</h3>' +
        '<p class="mb5">' + s.d + '</p>' +
        '<p class="mono mb4">Where we would start</p>' +
        '<div class="chips">' + s.p.map(function (k) {
          return '<a class="chip" href="' + LINKS[k] + '">' + NAMES[k] + '</a>';
        }).join('') + '</div>' +
        '</div>';
      out.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'nearest' });
    });
  })();

  /* ---------- payment form ---------- */
  (function () {
    var form = $('#pay-form');
    if (!form) return;
    var btn = $('#pay-btn'), errBox = $('#pay-err'), btnLabel = btn.innerHTML;

    function showError(msg) { errBox.textContent = msg; errBox.hidden = false; }
    function clearError() { errBox.hidden = true; errBox.textContent = ''; }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      clearError();

      var amount = parseFloat($('#pay-amount').value);
      if (!isFinite(amount) || amount <= 0) { showError('Enter a valid amount greater than zero.'); return; }
      if (amount > 250000) { showError('For amounts above USD 250,000 please email hello@intelloratech.com to arrange payment.'); return; }

      var reference = $('#pay-reference').value.trim();
      var description = $('#pay-description').value.trim();

      btn.disabled = true;
      btn.textContent = 'Redirecting to secure checkout…';

      fetch('/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount, reference: reference, description: description })
      })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (result) {
          if (!result.ok || !result.data || !result.data.url) {
            throw new Error((result.data && result.data.error) || 'Unable to start checkout. Please try again.');
          }
          window.location.href = result.data.url;
        })
        .catch(function (err) {
          showError(err.message || 'Something went wrong. Please try again or email hello@intelloratech.com.');
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
        var text = 'Confirmed: ' + (d.currency || 'usd').toUpperCase() + ' ' + amount;
        if (d.reference) text += ' · Ref ' + d.reference;
        box.textContent = text;
        box.hidden = false;
      })
      .catch(function () {});
  })();
})();

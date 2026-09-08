/* ============================================================
   INTELLORA TECH — SHARED BEHAVIOUR
   Progressive enhancement only. Every feature degrades to
   readable static content when JS is unavailable.
   ============================================================ */
(function () {
  'use strict';
  var RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- theme ---------- */
  (function () {
    var btn = $('#thm'); if (!btn) return;
    var KEY = 'intellora-theme';
    var stored = null;
    try { stored = localStorage.getItem(KEY); } catch (e) {}
    if (stored) document.documentElement.setAttribute('data-theme', stored);
    function label() {
      var cur = document.documentElement.getAttribute('data-theme');
      var dark = cur === 'dark' || (!cur && window.matchMedia('(prefers-color-scheme: dark)').matches);
      btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    }
    label();
    btn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme');
      var dark = cur === 'dark' || (!cur && window.matchMedia('(prefers-color-scheme: dark)').matches);
      var next = dark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem(KEY, next); } catch (e) {}
      label();
    });
  })();

  /* ---------- mobile nav ---------- */
  (function () {
    var b = $('#burger'), m = $('#mnav'); if (!b || !m) return;
    function shut() { m.classList.remove('open'); b.classList.remove('on'); b.setAttribute('aria-expanded', 'false'); }
    b.addEventListener('click', function () {
      var open = m.classList.toggle('open');
      b.classList.toggle('on', open);
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    m.addEventListener('click', function (e) { if (e.target.tagName === 'A') shut(); });
    window.addEventListener('resize', function () { if (window.innerWidth > 1080) shut(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') shut(); });
  })();

  /* ---------- scroll: progress + sticky CTA ---------- */
  (function () {
    var sp = $('#sprog'), sc = $('#scta'), hero = $('[data-hero]'), end = $('#contact') || $('[data-cta-end]');
    var tick = false;
    function run() {
      var d = document.documentElement;
      if (sp) {
        var max = d.scrollHeight - d.clientHeight;
        sp.style.width = (max > 0 ? (d.scrollTop || document.body.scrollTop) / max * 100 : 0) + '%';
      }
      if (sc && hero) {
        var past = (window.pageYOffset || d.scrollTop) > (hero.offsetTop + hero.offsetHeight);
        var near = false;
        if (end) near = end.getBoundingClientRect().top < window.innerHeight * 0.9;
        sc.classList.toggle('on', past && !near);
      }
      tick = false;
    }
    function onScroll() { if (tick) return; tick = true; window.requestAnimationFrame(run); }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    run();
  })();

  /* ---------- reveals (one orchestrated moment per section) ---------- */
  (function () {
    var els = $$('.rv');
    if (!els.length) return;
    if (RM || !('IntersectionObserver' in window)) { els.forEach(function (e) { e.classList.add('on'); }); return; }
    var io = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('on'); io.unobserve(e.target); } });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (e) { io.observe(e); });
  })();

  /* ---------- count-up ---------- */
  (function () {
    var els = $$('[data-to]');
    if (!els.length) return;
    function up(el) {
      var to = parseFloat(el.dataset.to),
          to2 = el.dataset.to2 ? parseFloat(el.dataset.to2) : null,
          suf = el.dataset.suf || '', t0 = null, dur = 1200;
      if (RM) { el.textContent = (to2 !== null ? to + '–' + to2 : to) + suf; return; }
      function frame(ts) {
        if (!t0) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
        el.textContent = (to2 !== null ? Math.round(to * e) + '–' + Math.round(to2 * e) : Math.round(to * e)) + suf;
        if (p < 1) requestAnimationFrame(frame);
        else el.textContent = (to2 !== null ? to + '–' + to2 : to) + suf;
      }
      requestAnimationFrame(frame);
    }
    if (!('IntersectionObserver' in window)) { els.forEach(up); return; }
    var io = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { up(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.5 });
    els.forEach(function (e) { io.observe(e); });
  })();

  /* ---------- currency toggle ---------- */
  var CUR = { USD: { s: '$', r: 1 }, EUR: { s: '€', r: 0.92 }, GBP: { s: '£', r: 0.79 }, AED: { s: 'AED ', r: 3.67 } };
  var curCode = 'USD';
  function fmt(usd) {
    var c = CUR[curCode], v = Math.round(usd * c.r / 100) * 100;
    return c.s + v.toLocaleString('en-US');
  }
  (function () {
    var sel = $('#cur'); if (!sel) return;
    function apply() {
      curCode = sel.value;
      $$('[data-usd]').forEach(function (el) { el.textContent = fmt(parseFloat(el.dataset.usd)); });
      if (window.__reprice) window.__reprice();
    }
    sel.addEventListener('change', apply);
    apply();
  })();

  /* ---------- programme estimator ---------- */
  (function () {
    var root = $('#est'); if (!root) return;

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

    var st = { type: null, pillar: null, cx: null, sz: null, gv: null, tl: null }, step = 1;

    function calc() {
      var b = BASE[st.type], pl = PILLAR[st.pillar];
      var p = b.p * pl.p * M.cx[st.cx].p * M.sz[st.sz].p * M.gv[st.gv].p * M.tl[st.tl].p;
      var w = b.w * pl.w * M.cx[st.cx].w * M.sz[st.sz].w * M.gv[st.gv].w * M.tl[st.tl].w;
      return { lo: p * 0.84, hi: p * 1.18, mid: p, wLo: Math.max(2, Math.round(w * 0.85)), wHi: Math.round(w * 1.15) };
    }

    function paint() {
      if (!st.type || !st.pillar || !st.cx || !st.sz || !st.gv || !st.tl) return;
      var r = calc(), b = BASE[st.type];
      $('#resRange').textContent = fmt(r.lo) + ' – ' + fmt(r.hi);
      $('#resDur').textContent = r.wLo + '–' + r.wHi + ' weeks · delivered remotely · fixed price on signature';
      $('#resTags').innerHTML = [b.l, PILLAR[st.pillar].l, M.cx[st.cx].l, M.sz[st.sz].l, M.gv[st.gv].l, M.tl[st.tl].l]
        .map(function (t) { return '<span class="chip">' + t + '</span>'; }).join('');
      $('#resPhases').innerHTML = PH[st.type].map(function (p) {
        return '<div class="mb4"><div style="display:flex;justify-content:space-between;gap:.625rem;font-size:var(--t-sm);margin-bottom:.375rem">' +
          '<b style="font-weight:500">' + p[0] + '</b><span class="mono dim">' + p[1] + '% · ' + fmt(r.lo * p[1] / 100) + '–' + fmt(r.hi * p[1] / 100) + '</span></div>' +
          '<div style="height:7px;background:var(--paper-3);border-radius:4px;overflow:hidden"><i style="display:block;height:100%;width:' + p[1] + '%;background:var(--brand);border-radius:4px"></i></div></div>';
      }).join('');

      var cap = $('#resCap');
      if (r.mid > 58000) {
        cap.hidden = false;
        cap.innerHTML = '<b>A programme this size needs a conversation before a number.</b> At this scale the work is either phased into sequenced engagements with their own fixed prices, or delivered with a partner team for capacity. We would rather say that now than quote a figure we cannot staff. Treat the range above as a total across phases, not a single contract.';
      } else { cap.hidden = true; }

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
    window.__reprice = function () { if (step === 3) paint(); };

    function go(n) {
      step = n;
      $$('[data-pane]', root).forEach(function (p) { p.hidden = (+p.dataset.pane !== n); });
      $$('[data-stepname]', root).forEach(function (s) {
        var on = +s.dataset.stepname === n;
        s.style.color = on ? 'var(--brand)' : 'var(--tx-dim)';
        s.setAttribute('aria-current', on ? 'step' : 'false');
      });
      var bar = $('#estBar'); if (bar) bar.style.width = (n * 33.34) + '%';
      if (n === 3) paint();
      var y = root.getBoundingClientRect().top + window.pageYOffset - 88;
      window.scrollTo({ top: y, behavior: RM ? 'auto' : 'smooth' });
    }

    function gate() {
      var n1 = $('#estN1'), n2 = $('#estN2');
      if (n1) n1.disabled = !(st.type && st.pillar);
      if (n2) n2.disabled = !(st.cx && st.sz && st.gv && st.tl);
    }

    $$('[data-grp]', root).forEach(function (g) {
      g.addEventListener('click', function (e) {
        var c = e.target.closest('.opt'); if (!c) return;
        $$('.opt', g).forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
        c.setAttribute('aria-pressed', 'true');
        st[g.dataset.grp] = c.dataset.v;
        gate();
      });
    });

    var n1 = $('#estN1'), n2 = $('#estN2');
    if (n1) n1.addEventListener('click', function () { if (st.type && st.pillar) go(2); });
    if (n2) n2.addEventListener('click', function () { if (st.cx && st.sz && st.gv && st.tl) go(3); });
    var b2 = $('#estB2'), b3 = $('#estB3');
    if (b2) b2.addEventListener('click', function () { go(1); });
    if (b3) b3.addEventListener('click', function () { go(2); });

    var cp = $('#resCopy');
    if (cp) cp.addEventListener('click', function () {
      var t = window.__estSum || '', done = function () {
        var c = $('#resCopied'); if (!c) return;
        c.hidden = false; setTimeout(function () { c.hidden = true; }, 2600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, done);
      else {
        var ta = document.createElement('textarea');
        ta.value = t; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        ta.remove(); done();
      }
    });
    gate();
  })();

  /* ---------- maturity self-assessment ---------- */
  (function () {
    var root = $('#mat'); if (!root) return;
    var qs = $$('[data-q]', root), out = $('#matOut'), btn = $('#matGo');
    var STAGE = [
      { max: 11, n: 'Ad hoc', d: 'Data lives in operational systems and spreadsheets. Reporting is manual and answers disagree depending on who produced them. The first win is a single reliable pipeline and one agreed set of definitions.', p: ['database', 'analytics'] },
      { max: 17, n: 'Repeatable', d: 'Pipelines exist but break quietly, and nobody can trace a number back to its source. The priority is orchestration you can trust and lineage you can show an auditor.', p: ['analytics', 'governance'] },
      { max: 23, n: 'Governed', d: 'The platform is reliable and documented. The next constraints are cost efficiency, access control, and preparing the data layer to support models rather than dashboards alone.', p: ['cloud', 'security'] },
      { max: 99, n: 'Optimising', d: 'Strong foundations already in place. Value now comes from advanced workloads — machine learning in production, real-time decisioning, and formal model governance.', p: ['ai', 'governance'] }
    ];
    var NAMES = { analytics: 'Analytics & BI', governance: 'Governance & compliance', security: 'Security & data protection', ai: 'AI & machine learning', database: 'Database engineering', cloud: 'AWS cloud architecture' };
    var LINKS = { analytics: '../capabilities/', governance: '../capabilities/', security: '../capabilities/', ai: '../capabilities/ai-machine-learning.html', cloud: '../capabilities/aws-cloud-architecture.html', database: '../capabilities/' };

    if (btn) btn.addEventListener('click', function () {
      var total = 0, answered = 0;
      qs.forEach(function (q) {
        var sel = $('select', q);
        if (sel && sel.value !== '') { total += parseInt(sel.value, 10); answered++; }
      });
      if (answered < qs.length) {
        out.hidden = false;
        out.innerHTML = '<div class="note">Answer all ' + qs.length + ' questions to see your result.</div>';
        return;
      }
      var s = STAGE.filter(function (x) { return total <= x.max; })[0];
      out.hidden = false;
      out.innerHTML =
        '<div class="card" style="border-color:var(--brand)">' +
        '<div class="mono dim mb4">Result · score ' + total + ' of ' + (qs.length * 4) + '</div>' +
        '<h3 style="color:var(--brand);margin-bottom:.5rem">' + s.n + '</h3>' +
        '<p class="mb5">' + s.d + '</p>' +
        '<div class="mono dim mb4">Where we would start</div>' +
        '<div class="row">' + s.p.map(function (k) {
          return '<a class="chip" href="' + LINKS[k] + '" style="border-color:var(--p-' + k + ');color:var(--p-' + k + ')">' + NAMES[k] + '</a>';
        }).join('') + '</div>' +
        '<p class="mono dim mt5" style="font-size:var(--t-xs)">Indicative only. A scoping call replaces this with an assessment of your actual systems.</p>' +
        '</div>';
      out.scrollIntoView({ behavior: RM ? 'auto' : 'smooth', block: 'nearest' });
    });
  })();

  /* ---------- technology filter ---------- */
  (function () {
    var root = $('#techf'); if (!root) return;
    var btns = $$('[data-tf]', root), items = $$('[data-tgroup]');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.tf;
        btns.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        items.forEach(function (it) { it.hidden = !(k === 'all' || it.dataset.tgroup === k); });
      });
    });
  })();
})();

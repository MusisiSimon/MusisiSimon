(function () {
  'use strict';
  var box = document.getElementById('confirm-box');
  if (!box) return;

  var params = new URLSearchParams(window.location.search);
  var sessionId = params.get('session_id');
  if (!sessionId) return;

  fetch('/verify-payment?session_id=' + encodeURIComponent(sessionId))
    .then(function (res) {
      return res.json().then(function (data) { return { ok: res.ok, data: data }; });
    })
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

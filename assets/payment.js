/* ============================================================
   INTELLORA TECH — PAYMENT PAGE
   Creates a Stripe Checkout session server-side and redirects.
   Card details are never handled by this script or this origin.
   ============================================================ */
(function () {
  'use strict';
  var form = document.getElementById('pay-form');
  if (!form) return;

  var btn = document.getElementById('pay-btn');
  var errBox = document.getElementById('pay-err');
  var btnLabel = btn.innerHTML;

  function showError(msg) {
    errBox.textContent = msg;
    errBox.hidden = false;
  }
  function clearError() {
    errBox.hidden = true;
    errBox.textContent = '';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    clearError();

    var amount = parseFloat(document.getElementById('pay-amount').value);
    if (!isFinite(amount) || amount <= 0) {
      showError('Enter a valid amount greater than zero.');
      return;
    }
    if (amount > 250000) {
      showError('For amounts above USD 250,000 please email hello@intelloratech.com to arrange payment.');
      return;
    }

    var reference = document.getElementById('pay-reference').value.trim();
    var description = document.getElementById('pay-description').value.trim();

    btn.disabled = true;
    btn.textContent = 'Redirecting to secure checkout…';

    fetch('/create-checkout-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: amount, reference: reference, description: description })
    })
      .then(function (res) {
        return res.json().then(function (data) { return { ok: res.ok, data: data }; });
      })
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

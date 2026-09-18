function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function onRequestGet(context) {
  const { request, env } = context;

  if (!env.STRIPE_SECRET_KEY) {
    return json({ error: 'Payment processing is not configured yet.' }, 500);
  }

  const url = new URL(request.url);
  const sessionId = url.searchParams.get('session_id') || '';
  if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId)) {
    return json({ error: 'Invalid session id.' }, 400);
  }

  let stripeRes;
  try {
    stripeRes = await fetch('https://api.stripe.com/v1/checkout/sessions/' + encodeURIComponent(sessionId), {
      headers: { Authorization: 'Basic ' + btoa(env.STRIPE_SECRET_KEY + ':') },
    });
  } catch (e) {
    return json({ error: 'Unable to reach the payment processor.' }, 502);
  }

  const data = await stripeRes.json();
  if (!stripeRes.ok) {
    return json({ error: (data.error && data.error.message) || 'Lookup failed.' }, 502);
  }

  return json({
    status: data.payment_status,
    amount_total: data.amount_total,
    currency: data.currency,
    reference: data.client_reference_id,
  });
}

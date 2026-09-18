const MIN_CENTS = 100;
const MAX_CENTS = 25000000;

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.STRIPE_SECRET_KEY) {
    return json({ error: 'Payment processing is not configured yet. Please email hello@intelloratech.com.' }, 500);
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json({ error: 'Invalid request.' }, 400);
  }

  const amount = Number(body.amount);
  if (!Number.isFinite(amount) || amount <= 0) {
    return json({ error: 'Enter a valid amount greater than zero.' }, 400);
  }

  const amountCents = Math.round(amount * 100);
  if (amountCents < MIN_CENTS || amountCents > MAX_CENTS) {
    return json({ error: 'Amount must be between USD 1.00 and USD 250,000.00.' }, 400);
  }

  const description = typeof body.description === 'string' && body.description.trim()
    ? body.description.trim().slice(0, 200)
    : 'Intellora Tech — invoice payment';
  const reference = typeof body.reference === 'string' ? body.reference.trim().slice(0, 100) : '';

  const origin = new URL(request.url).origin;

  const params = new URLSearchParams();
  params.set('mode', 'payment');
  params.append('payment_method_types[]', 'card');
  params.set('line_items[0][price_data][currency]', 'usd');
  params.set('line_items[0][price_data][unit_amount]', String(amountCents));
  params.set('line_items[0][price_data][product_data][name]', description);
  params.set('line_items[0][quantity]', '1');
  params.set('success_url', origin + '/payment/success/?session_id={CHECKOUT_SESSION_ID}');
  params.set('cancel_url', origin + '/payment/cancel/');
  params.set('submit_type', 'pay');
  if (reference) params.set('client_reference_id', reference);

  let stripeRes;
  try {
    stripeRes = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        Authorization: 'Basic ' + btoa(env.STRIPE_SECRET_KEY + ':'),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });
  } catch (e) {
    return json({ error: 'Unable to reach the payment processor. Please try again shortly.' }, 502);
  }

  const data = await stripeRes.json();
  if (!stripeRes.ok) {
    return json({ error: (data.error && data.error.message) || 'Unable to start checkout.' }, 502);
  }

  return json({ url: data.url });
}

export async function onRequestGet() {
  return json({ error: 'Method not allowed.' }, 405);
}

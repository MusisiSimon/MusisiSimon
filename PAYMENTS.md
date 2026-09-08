# Card payments — setup

The site accepts Visa, Mastercard and Amex through **Stripe Checkout**. Card numbers are entered on Stripe's own hosted page and never reach this site's server or codebase — the site stays out of PCI-DSS scope entirely.

## How it works

1. `/payment/` — a form for amount, an optional invoice reference, and a description.
2. `assets/payment.js` posts that to `/create-checkout-session` (a Cloudflare Pages Function).
3. `functions/create-checkout-session.js` calls the Stripe API with the site's **secret key** and creates a Checkout Session, returning Stripe's hosted checkout URL.
4. The browser is redirected to `checkout.stripe.com` to enter card details.
5. Stripe redirects back to `/payment/success/` (or `/payment/cancel/` if abandoned). The success page calls `/verify-payment` to display a confirmation, but the payment itself already happened on Stripe's side by that point.

No card data, PAN, CVC or expiry ever touches this repository's code or this site's origin.

## Required setup before this works

This is a static site — the `functions/` folder only works once deployed to a platform that runs them (Cloudflare Pages is what the rest of this site's `README` recommends; the code here assumes that platform).

1. Create a [Stripe account](https://dashboard.stripe.com/register) if you don't have one.
2. In the Stripe Dashboard, grab your **secret key** (`sk_live_...` for real payments, `sk_test_...` while testing).
3. In Cloudflare Pages: **your project → Settings → Environment variables** → add
   - `STRIPE_SECRET_KEY` = your secret key
   Set it for both "Production" and "Preview" if you want the payment page to work on preview deploys too. **Never commit this key to git.**
4. Redeploy. The `functions/` folder is picked up automatically by Cloudflare Pages — no build step or `package.json` needed, since the functions only use `fetch`.

## Testing before going live

Use a Stripe **test** secret key (`sk_test_...`) and Stripe's test card `4242 4242 4242 4242`, any future expiry, any CVC, any postcode. Test payments appear in the Stripe Dashboard's test mode and never touch real money. Switch to the live key only once you're ready to accept real cards.

## Where money actually lands

Stripe deposits to whatever bank account you connect in the Dashboard, on Stripe's normal payout schedule. This site has no bookkeeping of its own — the Stripe Dashboard (and the receipt Stripe emails automatically) is the source of truth for every payment. If you later want automatic email notifications or CRM/accounting sync beyond Stripe's own emails and dashboard, that's a Stripe webhook (`checkout.session.completed`) calling a new function — not built here since nothing today needs to consume it.

## Limits

- Amounts are capped server-side between USD 1.00 and USD 250,000.00 (`functions/create-checkout-session.js`). Adjust `MIN_CENTS` / `MAX_CENTS` there if needed.
- Currency is fixed at USD. To offer more currencies, change `line_items[0][price_data][currency]` in the same file (and decide how the amount field should convert).

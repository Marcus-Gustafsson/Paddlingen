# Stripe Development

Last updated: 2026-03-25

## Purpose

This document explains the manual Stripe setup steps for this project.

Use it when you need to:

- create a Stripe account,
- collect the correct test keys,
- install and log in to the Stripe CLI,
- prepare local `.env` values,
- understand which commands are useful during Stripe development.

This document is written for the current project shape:

- Flask backend,
- Stripe-hosted Checkout planned as the first real payment UI,
- webhook-first payment confirmation,
- WSL with a Linux shell such as `bash`.

## Important beginner idea

Before the Stripe-specific values, remember one important app setting:

- `SECRET_KEY`
  This is the Flask app's own secret key. It is not a Stripe key, but the app
  still needs it so sessions and CSRF-protected forms work correctly.

Then there are three different kinds of Stripe values you need to care about:

1. `STRIPE_SECRET_KEY`
   This lets your Flask backend call Stripe's API.
2. `STRIPE_WEBHOOK_SECRET`
   This lets your backend verify that an incoming webhook really came from
   Stripe.
3. `STRIPE_PUBLIC_BASE_URL`
   This tells Stripe where your site lives publicly so Checkout can return the
   visitor to `/payment-success` or `/payment-cancel`.

Do not mix them up.

The Flask `SECRET_KEY`, the Stripe secret key, and the Stripe webhook secret
are all different values with different jobs.

### Why the Flask `SECRET_KEY` is still needed

Even when you are working on Stripe, the Flask app still needs `SECRET_KEY` in
`.env`.

Why:

- Flask uses it to sign session cookies,
- Flask-WTF uses it to generate CSRF tokens,
- pages such as the public lock screen and login page can fail without it.

Generate one with:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then save it in the project root `.env` file:

```env
SECRET_KEY=your-generated-value-here
```

Important:

- this is not your Stripe key,
- do not replace it with `STRIPE_SECRET_KEY`,
- you need both values in `.env`.

## What you need to do manually

These are the manual steps you should do yourself in the Stripe Dashboard.

### Step 1: create a Stripe account

1. Go to `https://dashboard.stripe.com/register`
2. Create an account.
3. Finish the basic setup Stripe asks for.

For development, you should stay in Stripe's sandbox or test mode.

Do not start with live mode.

## Step 2: find your test API keys

1. Open the Stripe Dashboard.
2. Open the API keys page:

```text
Developers / Workbench -> API keys
```

3. Make sure you are looking at sandbox or test mode keys.
4. Reveal the secret test key that starts with `sk_test_`.
5. Copy it into your local `.env` file as `STRIPE_SECRET_KEY`.

Important:

- test secret keys start with `sk_test_`
- live secret keys start with `sk_live_`
- use `sk_test_` while building and testing
- when you use `sk_test_...` together with Stripe test cards, Stripe does not
  create real charges

## Step 3: decide your public base URL

Stripe Checkout needs a base URL it can send the browser back to after:

- a completed Checkout flow,
- or a canceled Checkout flow.

In this project that base URL is stored in:

```env
STRIPE_PUBLIC_BASE_URL=...
```

Use only the site root in this variable.

Correct examples:

```env
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
STRIPE_PUBLIC_BASE_URL=https://abc123.ngrok-free.app
STRIPE_PUBLIC_BASE_URL=https://paddlingen.se
```

Wrong examples:

```env
STRIPE_PUBLIC_BASE_URL=https://abc123.ngrok-free.app/payment-success
STRIPE_PUBLIC_BASE_URL=abc123.ngrok-free.app
```

### When `localhost` works

`localhost` or `127.0.0.1` works when you are the one testing in your own
browser on the same machine that is running Flask.

Example:

```env
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
```

Why this works:

- your browser can open Stripe Checkout,
- Stripe can redirect that same browser back to
  `http://127.0.0.1:5000/payment-success`,
- because that browser is running on the same computer as your Flask app.

This is enough for your own local Step 5 and Step 7 testing later.

### When `localhost` does not work

`localhost` does not work for other people.

Why:

- on your friend's computer, `localhost` means their own computer,
- not your WSL machine.

That means your friend cannot complete a Stripe flow that tries to return to
your `http://127.0.0.1:5000/...` URL.

### When you should use ngrok

Use an ngrok URL when:

- another person needs to test the site from their own home or device,
- you want Stripe Checkout to return to a public URL,
- or you want a temporary public web address without deploying the app.

Example:

```env
STRIPE_PUBLIC_BASE_URL=https://your-current-ngrok-url.ngrok-free.app
```

Important:

- the free ngrok tier is fine for occasional testing,
- but the URL can change each time you start a new tunnel,
- so update `.env` when the ngrok URL changes.

### `localhost` and webhooks are different

Browser redirects and webhooks are not the same thing.

`STRIPE_PUBLIC_BASE_URL` controls browser return URLs.

Webhook delivery can still work locally later through the Stripe CLI even when
your base URL is still `http://127.0.0.1:5000`.

That later command looks like this:

```bash
stripe listen --forward-to localhost:5000/stripe/webhook
```

Why this matters:

- Stripe itself cannot call your localhost over the public internet,
- but the Stripe CLI can receive Stripe events and forward them into your local
  Flask app.

## Step 4: prepare your local `.env`

Add these values to your local `.env` file:

```env
SECRET_KEY=replace-with-a-long-random-secret
STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me_before_webhook_testing
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
```

Notes:

- If you are testing only in your own browser on the same machine, use
  `http://127.0.0.1:5000`.
- If you later test with your friend through ngrok, temporarily change
  `STRIPE_PUBLIC_BASE_URL` to the current ngrok root URL instead.
- `STRIPE_WEBHOOK_SECRET` is required by the project configuration, but you
  only get the real value after you create a webhook listener later.
- Until webhook testing is connected, you can leave a placeholder value in
  local development.
- In production, use the real values from the Stripe Dashboard and webhook
  setup.
- Restart Flask after changing `.env`, otherwise the app may still use the old
  values.

## How to confirm you are still in Stripe test mode

Use these checks:

1. Your local `.env` uses `STRIPE_SECRET_KEY=sk_test_...`
2. The Stripe Dashboard test-mode toggle is enabled
3. You pay with Stripe test card numbers, not a real card

If those three are true, you are still in sandbox or test mode and should not
create real charges.

## Important hosted Checkout limitation

Stripe-hosted Checkout is not a normal project template that you can control
pixel by pixel.

For this project that means:

- Stripe can translate its own built-in Checkout text when we set the locale to
  Swedish.
- Stripe can be limited to card only by creating the Checkout Session with
  `payment_method_types=["card"]`.
- Stripe does not let us place a fully custom project-owned countdown timer or
  a custom-positioned `Avbryt order` button inside the hosted Checkout page.

Because of that limitation, the project now uses two steps:

1. A new Step 3 inside the booking modal on our own site
2. Stripe-hosted Checkout after the visitor clicks `Fortsätt till betalning`

The booking-modal Step 3 is where we show:

- the 15-minute reservation countdown,
- the clear `Avbryt order` button,
- the local booking reference and amount.

Then Stripe-hosted Checkout is used only for the actual card entry.

Important:

- Stripe's own back or cancel control inside hosted Checkout still sends the
  visitor to our `/payment-cancel` return route.
- The project now treats that route as a real cancellation path that releases
  the unpaid reservation.

### Why the visible timer is on our page instead of inside Stripe

Stripe does let Checkout Sessions expire, but Stripe's own `expires_at` rule
has a minimum lifetime that is longer than this project's local 15-minute hold.

So the project now uses:

- a local 15-minute reservation timer inside booking-modal Step 3,
- and a Stripe-managed Checkout Session lifetime behind the scenes.

Entering Stripe does not reset or extend that local 15-minute timer. If the
visitor returns after the local hold has already expired, the app redirects
home with a toast and releases the stale unpaid reservation.

That gives us the clear timer the visitor asked for without pretending we can
fully control Stripe's hosted page.

## Step 5: install the Stripe CLI in WSL

Stripe recommends the Stripe CLI for local development and webhook testing.

For Ubuntu or Debian inside WSL, run these commands:

```bash
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg > /dev/null
```

```bash
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
```

```bash
sudo apt update
```

```bash
sudo apt install stripe
```

After installation, check that the command exists:

```bash
stripe --version
```

## Step 6: log in to the Stripe CLI

Run:

```bash
stripe login
```

What happens:

- Stripe prints a short pairing code,
- opens or asks you to open a browser page,
- you approve the CLI login for your Stripe account.

Then check who the CLI is using:

```bash
stripe whoami
```

Important note:

- `stripe login` creates CLI-specific restricted keys for your account.
- That is good for CLI usage.
- It does not replace the `STRIPE_SECRET_KEY` that your Flask app reads from
  `.env`.

## Step 7: install the Python dependency used by this project

This repository now includes Stripe in `pyproject.toml`.

From the project root, run:

```bash
uv sync
```

This installs the Stripe Python SDK into the local project environment.

## Good commands to know

These commands are useful during development.

### Check the project environment

```bash
uv sync
```

```bash
uv run -m pytest tests/test_stripe_helpers.py
```

```bash
make all-basic
```

### Check the Stripe CLI

```bash
stripe --version
```

```bash
stripe whoami
```

```bash
stripe logs tail
```

### Optional CLI smoke test

This sends a harmless test request to Stripe and confirms the CLI works:

```bash
stripe products create \
  --name="CLI setup check" \
  --description="Created during local Stripe setup"
```

This creates test data in your Stripe sandbox, not a real charge.

## Local webhook setup

The project now has a real local Stripe webhook route at:

```text
http://127.0.0.1:5000/stripe/webhook
```

### Step 7: start Flask first

Run your normal local app command:

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

Leave that terminal running.

### Step 8: start Stripe CLI forwarding

Open a second terminal in the project root and run:

```bash
stripe listen --forward-to localhost:5000/stripe/webhook
```

What this does:

- listens for Stripe sandbox webhook events,
- forwards them to your local Flask webhook route,
- prints a webhook signing secret that starts with `whsec_`.

Stripe's CLI prints a line similar to:

```text
Ready! Your webhook signing secret is whsec_...
```

### Step 9: save the printed webhook secret into `.env`

Copy the printed `whsec_...` value and save it in your project root `.env`:

```env
STRIPE_WEBHOOK_SECRET=whsec_replace_me_with_the_value_from_stripe_listen
```

Important:

- `SECRET_KEY` is Flask's secret.
- `STRIPE_SECRET_KEY` is Stripe's API key.
- `STRIPE_WEBHOOK_SECRET` is only for verifying incoming webhook requests.

### Step 10: restart Flask after changing `.env`

After updating `.env`, restart Flask so the app loads the new webhook secret:

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

### Step 11: keep `stripe listen` running while testing

Do not close the `stripe listen` terminal while you are testing webhooks. If
you stop it and later start it again, Stripe CLI can print a new `whsec_...`
value. If that happens, update `.env` again and restart Flask.

### Step 12: trigger a test event manually when needed

Example:

```bash
stripe trigger checkout.session.completed
```

Use this when you want to confirm that the webhook route receives and processes
an event without going through the full booking flow first.

Important:

- `stripe trigger checkout.session.completed` is useful for route-level testing.
- It does not create one of this project's real booking orders.
- That means it should not be used as the final proof that a real local booking
  becomes paid.
- To test real booking finalization, complete the normal booking flow in the
  app and pay with a Stripe test card while `stripe listen` is running.

## Manual test flow for the current Checkout step

After the current booking-modal Step 3 plus Stripe Checkout flow has been
added,
use this manual test flow.

### Local setup to use first

Keep these values in `.env` while testing on your own machine:

```env
SECRET_KEY=your-generated-flask-secret
STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me_before_webhook_testing
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
```

Then restart Flask:

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

### What to do manually

1. Open `http://127.0.0.1:5000`
2. Unlock the public page if the shared password gate is enabled
3. Start a canoe booking
4. Submit the booking form
5. Confirm that the site moves the booking modal into Step 3 without reloading
   the whole page
6. Confirm that Step 3 shows:
   - `Reservation och betalning`
   - a visible countdown
   - `Fortsätt till betalning`
   - `Avbryt order`
7. Click `Fortsätt till betalning`
8. Confirm that Stripe Checkout opens in Swedish and only shows card payment
   for now
9. Use a Stripe test card such as:
   - for a successful payment
   ```bash
   4242 4242 4242 4242 
   ``` 
   - for a 3D Secure flow
   ```bash
   4000 0000 0000 3220 
   ``` 
   - for a declined card
   ```bash
   4000 0000 0000 9995 
   ``` 
10. Use any future expiration date, any three-digit CVC, and any postal code
11. Complete or cancel the flow

### What you should expect right now

If the payment succeeds in Stripe Checkout:

- the browser returns to a local completion page,
- that page first tries to reconcile the Stripe Checkout Session directly,
- if Stripe already reports the session as paid, the booking is confirmed
  locally right away even if your webhook listener is temporarily off,
- otherwise the page waits briefly for the webhook-backed booking update,
- and only then switches to the final confirmed success page automatically.

If the payment is canceled:

- pressing `Avbryt order` in booking-modal Step 3 should send you back home and
  remove the unpaid temporary booking,
- canceling inside Stripe Checkout should send you back home with a toast that
  explains the reservation was released.

If the local countdown reaches zero while you stay in Step 3:

- the order should be canceled automatically,
- and your browser should be sent back to the homepage.

### Helpful command while testing

Keep this running in another terminal if you want to see Stripe API activity:

```bash
stripe logs tail
```

## Recommended local development order

Use this order:

1. Create your Stripe account.
2. Stay in test mode.
3. Reveal and save your `sk_test_...` key.
4. Add the Stripe values to `.env`.
5. Install the Stripe CLI.
6. Run `stripe login`.
7. Run `uv sync`.
8. Confirm the app still starts normally.
9. Start `stripe listen --forward-to localhost:5000/stripe/webhook`.
10. Copy the printed `whsec_...` value into `.env`.
11. Restart Flask.
12. Move on to the next Stripe implementation step in the roadmap.

## Step-by-step summary for `STRIPE_WEBHOOK_SECRET`

If you only want the short version, do this:

1. Start Flask:

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

2. In another terminal, run:

```bash
stripe listen --forward-to localhost:5000/stripe/webhook
```

3. Copy the printed `whsec_...` secret.
4. Save it in your project root `.env`:

```env
STRIPE_WEBHOOK_SECRET=whsec_the_value_printed_by_stripe_listen
```

5. Restart Flask.
6. Keep `stripe listen` running.
7. Complete a Stripe test payment or run:

```bash
stripe trigger checkout.session.completed
```

8. Confirm the booking becomes paid after either the webhook is received or,
   when the browser has already returned from Stripe, after the app reconciles
   the paid Checkout Session directly.

For clarity:

- using a real booking plus a Stripe test card checks full payment
  finalization,
- using `stripe trigger checkout.session.completed` only checks that the
  webhook route can receive and parse a Stripe event.

## What to change right now

If you are currently running Flask like this:

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

and testing in your own browser on the same machine, set this in `.env`:

```env
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
```

Keep `STRIPE_SECRET_KEY` as your real `sk_test_...` value.

You can keep `STRIPE_WEBHOOK_SECRET` as a placeholder for now, for example:

```env
STRIPE_WEBHOOK_SECRET=whsec_replace_me_before_webhook_testing
```

Later, when you test with your friend through ngrok, temporarily change:

```env
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
```

to:

```env
STRIPE_PUBLIC_BASE_URL=https://your-current-ngrok-url.ngrok-free.app
```

Then restart the Flask app so the new value is loaded.

## Common mistakes

### Mistake 1: using the live key too early

Do not start with `sk_live_...`.

Use test mode first so you cannot accidentally create real charges.

### Mistake 2: using the secret key in browser code

Never expose `STRIPE_SECRET_KEY` in JavaScript or HTML templates.

It must stay server-side only.

### Mistake 3: confusing the API key with the webhook secret

These values look different and have different jobs:

- `sk_test_...` or `sk_live_...` = API secret key
- `whsec_...` = webhook signing secret

### Mistake 4: putting a full path into `STRIPE_PUBLIC_BASE_URL`

Use only the root URL:

```env
STRIPE_PUBLIC_BASE_URL=https://abc123.ngrok-free.app
```

Not:

```env
STRIPE_PUBLIC_BASE_URL=https://abc123.ngrok-free.app/payment-success
```

### Mistake 5: forgetting that `localhost` only works for your own browser

If you use:

```env
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
```

that is good for your own machine.

It is not good for your friend, because their browser would treat `localhost`
or `127.0.0.1` as their own computer.

## Related project documents

- `docs/roadmaps/backend_roadmap.md`
- `docs/dev/dev_ngrok.md`
- `docs/dev/dev_overview.md`

## Useful official Stripe pages

- Stripe development environment:
  `https://docs.stripe.com/get-started/development-environment?lang=python`
- Stripe API keys:
  `https://docs.stripe.com/keys`
- Stripe CLI usage:
  `https://docs.stripe.com/stripe-cli/use-cli`
- Stripe CLI keys:
  `https://docs.stripe.com/stripe-cli/keys`
- Stripe testing:
  `https://docs.stripe.com/testing`

### Mistake 4: stopping the webhook listener and expecting full automation

The return page can now recover many successful test payments by checking the
Stripe Checkout Session directly, but the webhook listener is still important.
Keep it running because it is the only fully automatic path when the visitor
closes the browser before returning, and it is the right place for later side
effects such as confirmation emails.

# Stripe Development

Last updated: 2026-03-24

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

There are three different kinds of Stripe values you need to care about:

1. `STRIPE_SECRET_KEY`
   This lets your Flask backend call Stripe's API.
2. `STRIPE_WEBHOOK_SECRET`
   This lets your backend verify that an incoming webhook really came from
   Stripe.
3. `STRIPE_PUBLIC_BASE_URL`
   This tells Stripe where your site lives publicly so Checkout can return the
   visitor to `/payment-success` or `/payment-cancel`.

Do not mix them up.

The secret key and webhook secret are not the same thing.

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

## Commands you will use later

The commands below are useful later, but they are not fully usable in this
project until the webhook route has been implemented.

### Forward Stripe events to your local app

Example command:

```bash
stripe listen --forward-to localhost:5000/stripe/webhook
```

What this does:

- listens for Stripe events in your sandbox,
- forwards them to your local Flask route,
- prints a webhook signing secret that starts with `whsec_`.

When you eventually run this command for the real local webhook route, copy the
printed signing secret into:

```env
STRIPE_WEBHOOK_SECRET=whsec_replace_me
```

### Trigger a test event

Example:

```bash
stripe trigger checkout.session.completed
```

This is useful later when the webhook endpoint exists and you want to confirm
that the route receives and processes the event.

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
9. Move on to the next Stripe implementation step in the roadmap.

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

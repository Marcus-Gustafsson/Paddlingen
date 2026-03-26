# Stripe Development

Last updated: 2026-03-26

## Purpose

This document explains how Stripe is currently wired into this project, which
manual Stripe settings still matter, and which local commands are useful during
development.

Use it when you need to:

- understand the current booking and payment flow,
- set up local Stripe test mode,
- start webhook forwarding in WSL,
- test payment success, cancellation, and delayed confirmation cases,
- enable and test Stripe's automatic success receipt email,
- or finish the remaining manual Stripe Dashboard branding settings.

This document assumes:

- Flask backend,
- Stripe-hosted Checkout,
- WSL with `bash`,
- commands run from the project root.

## The important Stripe values

The project uses four required Stripe-related values and one optional Checkout
value during payment work:

1. `SECRET_KEY`
   Flask's own secret key for sessions and CSRF. This is not a Stripe value.
2. `STRIPE_SECRET_KEY`
   The backend's Stripe API key.
3. `STRIPE_WEBHOOK_SECRET`
   The signing secret used to verify incoming Stripe webhooks.
4. `STRIPE_PUBLIC_BASE_URL`
   The public site root used for Stripe return URLs such as `/payment-success`
   and `/payment-cancel`.
5. `STRIPE_CHECKOUT_PRODUCT_ID` (optional)
   A Stripe Product ID from the Dashboard catalog. When set, the backend loads
   that product's uploaded image and reuses it on hosted Checkout while still
   keeping the app's dynamic canoe-count title and price note.

Do not mix them up. Each one has a different job.

## Local `.env` example

Use values like these during local development:

```env
SECRET_KEY=replace-with-a-long-random-secret
STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me_before_webhook_testing
STRIPE_PUBLIC_BASE_URL=http://127.0.0.1:5000
STRIPE_CHECKOUT_PRODUCT_ID=prod_replace_me_if_you_want_dashboard_product_images
```

Good to know:

- `sk_test_...` means Stripe test mode.
- `sk_live_...` means live mode.
- `STRIPE_PUBLIC_BASE_URL` must be only the site root, not a nested path.
- `STRIPE_CHECKOUT_PRODUCT_ID` is optional. Leave it empty if you want to use
  only the repo's fallback PNG image in environments where Stripe can reach it.
- restart Flask after changing `.env`.

## Useful local commands

Start the Flask app:

```bash
uv run flask --app app:create_app run --debug
```

Install the Stripe CLI in WSL if needed:

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

Check that Stripe CLI is installed:

```bash
stripe --version
```

Log in to the Stripe CLI:

```bash
stripe login
```

Forward Stripe webhooks into your local Flask app:

```bash
stripe listen --forward-to localhost:5000/stripe/webhook
```

That command prints a `whsec_...` signing secret. Save that value into your
local `.env` as `STRIPE_WEBHOOK_SECRET` and restart Flask.

## How the current payment flow works

This is the current step-by-step behavior.

1. The visitor fills in the booking modal on the site.
2. Flask validates the request and creates a local pending `BookingOrder`.
3. Flask creates matching reserved `BookedCanoe` rows.
4. Flask creates a real Stripe Checkout Session.
5. The browser moves into booking-modal Step 3 and then redirects to
   Stripe-hosted Checkout.
6. Stripe handles the real card form on its own page.
7. Stripe tries to send a webhook to `/stripe/webhook`.
8. Stripe also redirects the visitor back to `/payment-success` or
   `/payment-cancel`.
9. The app finalizes the booking only after the backend has verified Stripe's
   state.

## Why both the webhook and the browser return matter

The webhook is still important because it is the normal background
confirmation path. It works even if the visitor closes the browser after
paying.

The browser return path is now also robust. When the visitor returns to
`/payment-success`, the backend can check the Checkout Session directly with
Stripe and confirm the booking if Stripe already reports the session as paid.

That means the current project uses a hybrid confirmation model:

- webhook first as the normal background path,
- direct Stripe session reconciliation as a safe fallback when the browser
  returns before the webhook has updated the local order.

Both paths end up using the same local paid-booking finalization behavior.

## What happens in the main return cases

### Successful payment with webhook running

1. Stripe marks the Checkout Session as paid.
2. Stripe sends the webhook.
3. The webhook marks the local booking `paid`.
4. The visitor returns to `/payment-success`.
5. The site shows the final confirmation page and booking overview.

### Successful payment with webhook delayed or not running

1. Stripe marks the Checkout Session as paid.
2. The visitor returns to `/payment-success`.
3. The backend checks Stripe directly.
4. If Stripe already says `paid`, the app finalizes the booking locally anyway.
5. The confirmation page still works without waiting forever for the webhook.

### Visitor cancels or never finishes payment

1. Stripe sends the visitor back to `/payment-cancel` or the local hold expires.
2. The app releases the unpaid reservation.
3. The visitor is sent back to the homepage and can start over.

## Hosted Checkout customization: what the app controls

The app now uses Stripe-supported API customization for the hosted Checkout
product section.

It currently sends:

- a short product title such as `2 kanoter`,
- a short per-canoe note such as `(1 200 kr per kanot)`, while Stripe still
  shows the total line amount in the large price,
- a hosted Checkout product image from one of these sources:
  - first choice: the Stripe Dashboard product configured in
    `STRIPE_CHECKOUT_PRODUCT_ID`,
  - fallback: `static/images/canoe_checkout_icon_png.png`, but only when
    `STRIPE_PUBLIC_BASE_URL` points to a URL that Stripe can actually reach,
- `submit_type="book"`,
- and short helper text around the payment action.

Good to know:

- Stripe branding settings such as logo, accent color, and business name can
  show up locally even on `http://127.0.0.1:5000`, because they are hosted by
  Stripe.
- Product images are different. If the app sends an image URL based on
  `localhost` or `127.0.0.1`, Stripe cannot fetch that file from its own
  servers, so the image will not appear.
- `STRIPE_CHECKOUT_PRODUCT_ID` avoids that problem by letting the backend load
  the already-uploaded Dashboard product image and attach it to the dynamic
  Checkout line item.
- PNG is used for the hosted Checkout image because it is the safer supported
  format here.
- The repo also contains an SVG version, but the PNG is the safer Checkout
  choice for broad compatibility.
- Hosted Checkout is still Stripe's page, so the app cannot fully redesign its
  layout.

## Hosted Checkout customization: what is still manual in Stripe Dashboard

Some branding still has to be configured in Stripe Dashboard instead of this
repo. That includes:

- business or organizer name,
- logo or icon,
- brand colors,
- font and shape preset,
- support contact details,
- privacy policy link,
- terms link,
- refund or return policy details if you want them shown there.

## Stripe receipt emails: recommended first step

For this project, the recommended first email-confirmation step is to use
Stripe's built-in receipt for successful payments.

Why this is the recommended first step:

- the payer already enters an email address in hosted Checkout,
- Stripe can send the receipt automatically after a successful card payment,
- this avoids building and maintaining a second email system right away,
- and this project does not need Stripe's paid one-time invoice feature for the
  first booking launch.

Good to know:

- enable only the normal successful-payment receipt for now,
- do not enable `invoice_creation` in code for this use case,
- Stripe receipts are best for payment confirmation,
- a future app-sent email can still be added later if you want a richer custom
  booking summary with all participant names and local event instructions.

## What the app now sends into Stripe receipts

When the Checkout Session is created, the backend now adds
`payment_intent_data.description`.

That description is what Stripe can show in the successful payment receipt.

Current format:

- `Paddlingen - 2 kanoter - 20 mars 2026 - Bokningsreferens PAD-2026-00001`

This keeps the receipt short and useful:

- event title,
- canoe count,
- event date in Swedish format,
- and the booking reference.

## What you can customize in the Stripe receipt

### In code

The project currently customizes:

- `payment_intent_data.description`

That value is built in the backend when the Checkout Session is created.

If you want to adjust the wording later, update the helper in:

- `app/util/checkout_preparation.py`

Example styles that fit this project:

- `Paddlingen - 2 kanoter - 20 mars 2026 - Bokningsreferens PAD-2026-00001`
- `Bokning för Paddlingen - 2 kanoter - 20 mars 2026 - Ref PAD-2026-00001`
- `Paddlingen 2026 - 2 kanoter - Havsjömossen - Bokningsreferens PAD-2026-00001`

Keep this description short. Stripe receipts are not the best place for a long
participant list or detailed arrival instructions.

### In Stripe Dashboard

You can customize:

- logo,
- brand colors,
- business name,
- public phone number,
- website address,
- and similar public business details shown in the receipt.

Update those in:

- `Settings -> Business -> Branding`
- `Settings -> Business -> Public details`

## Exact Dashboard checklist for automatic success receipts

Do these steps in Stripe Dashboard:

1. Open Stripe Dashboard in the correct mode:
   - use test mode while testing,
   - use live mode only when you are ready for production.
2. Go to `Settings -> Customer emails`.
3. Under customer emails, enable:
   - `Successful payments`
4. Leave invoice-related features out of scope for now.
5. Go to `Settings -> Business -> Branding`.
6. Check:
   - logo,
   - icon,
   - accent color,
   - brand color.
7. Use the receipt preview there and click `Send test receipt`.
8. Go to `Settings -> Business -> Public details`.
9. Check:
   - public business or organizer name,
   - website,
   - support phone number or other public contact details.

What to expect after this:

- Stripe sends a receipt only after a successful payment,
- failed or declined payments do not send a receipt,
- the receipt uses your Stripe branding and public details,
- the receipt includes the short booking description sent by the app.

## How to use a Dashboard product image in this project

If you want the Product Catalog image to appear in hosted Checkout, do this:

1. Open Stripe Dashboard.
2. Go to Product Catalog.
3. Open the canoe booking product.
4. Confirm that the product has the image you want.
5. Copy the product ID. It looks like `prod_...`.
6. Add that value to `.env`:

```env
STRIPE_CHECKOUT_PRODUCT_ID=prod_...
```

7. Restart Flask.
8. Start a new booking and open hosted Checkout again.

What to expect:

- the app still controls the short title such as `2 kanoter`,
- the app still controls the short note such as `(1 200 kr per kanot)`,
- but the image now comes from the Dashboard product instead of a local file.

## Beginner-friendly local testing checklist

### Test 1: normal paid booking

1. Start Flask locally.
2. Start `stripe listen --forward-to localhost:5000/stripe/webhook`.
3. Open the site and create a booking.
4. Go through Stripe Checkout with a Stripe test card.
5. Confirm that the final confirmation page appears and the booking becomes
   `paid` locally.
6. Confirm that Stripe shows a successful payment in the Dashboard.
7. Confirm that the receipt preview and real receipt content look correct.

### Test 2: webhook listener off, but payment succeeds

1. Stop the Stripe CLI listener.
2. Create a new booking.
3. Complete Stripe Checkout with a test card.
4. Confirm that `/payment-success` still reaches the final confirmation page
   through direct Stripe reconciliation.

### Test 3: cancel from Stripe

1. Start a booking.
2. Enter Stripe Checkout.
3. cancel from Stripe's page.
4. Confirm that the reservation is released and the homepage becomes bookable
   again.

### Test 4: local hold expires

1. Start a booking.
2. Wait until the local reservation time expires before finishing payment.
3. Confirm that the app does not keep the canoes blocked forever.
4. Confirm that the visitor is told to start a new booking.

## What to check when something looks wrong

If payment works in Stripe Dashboard but the local booking does not update:

1. Check whether `stripe listen --forward-to localhost:5000/stripe/webhook` is
   running.
2. Check that the printed `whsec_...` value matches `STRIPE_WEBHOOK_SECRET` in
   `.env`.
3. Check that Flask was restarted after `.env` changed.
4. Check that `STRIPE_PUBLIC_BASE_URL` matches the URL used in the browser.
5. Reload the confirmation page once and confirm whether the backend fallback
   now reconciles the session directly.

If the hosted Checkout page looks too generic:

1. Confirm the app-driven product title, per-canoe note, and image are present.
2. Then finish the remaining brand settings in Stripe Dashboard.

If the hosted Checkout image is missing:

1. Check whether `STRIPE_CHECKOUT_PRODUCT_ID` is set in `.env`.
2. If it is set, confirm the Product Catalog entry still has an uploaded image.
3. Restart Flask after changing `.env`.
4. If `STRIPE_CHECKOUT_PRODUCT_ID` is not set, remember that a local
   `127.0.0.1` image URL is not public to Stripe, so the fallback image will
   not show there.

If the successful payment receipt does not arrive:

1. Check that `Settings -> Customer emails -> Successful payments` is enabled.
2. Check that the payer email really was entered in hosted Checkout.
3. In test mode, remember that Stripe limits automatic test receipts to your
   own verified test-environment email addresses.
4. Open the payment in Stripe Dashboard and use `Send receipt` manually if
   needed while testing.

## Production reminder

Before production, replace all local test values with the real live values and
verify:

- live `STRIPE_SECRET_KEY`,
- live `STRIPE_WEBHOOK_SECRET`,
- live `STRIPE_PUBLIC_BASE_URL`,
- live webhook delivery,
- and one controlled end-to-end payment test.

## Later guide: create a dedicated Stripe account for the event

Use this later, after you have decided which dedicated event email address you
want to own the Stripe account.

Recommended order:

1. First decide the dedicated mailbox for the event, for example
   `paddlingen@...`.
2. Make sure more than one organizer can access or recover that mailbox if
   needed.
3. Only then create the Stripe account with that email address.

Why:

- it keeps ownership of the payment account tied to the event rather than one
  person's private email,
- it makes password recovery and staff handover easier,
- and it reduces the chance of needing to migrate the Stripe account later.

## How to think about business type during Stripe onboarding

This part matters because Stripe's official guidance separates a legally
registered non-profit from activity that is simply non-profit in practice.

For this project, you have already clarified the important fact:

- there is no registered association or business behind the event,
- the event is run by you and a few admins as individuals,
- the booking money is collected only to pay the canoe rental company,
- and the event is not being run for profit.

That means the Stripe setup should follow the real legal structure, not the
spirit of the event.

Stripe's support guidance says:

- if you registered your organization with a government agency and it is a
  registered non-profit or charity, the business type is likely
  `Non-profit organisation`,
- if you did not file paperwork to register as a business entity, the business
  type is likely `Individual`.

Practical interpretation for this project:

- do not choose `Non-profit organisation` only because the event is volunteer
  run,
- do not invent a company or association that does not exist,
- and do not enter a business or organization number unless it truly belongs to
  the real legal owner of the Stripe account.

For your case, the later production setup should be based on the individual
path unless the legal structure changes before launch.

Good to know:

- Stripe's exact labels can vary slightly by country or interface language.
- If the form does not literally say `Individual`, choose the option that means
  no registered company or association exists and one real person is operating
  the account.

## What Stripe is likely to ask for

Exact requirements vary by country and business type, but Stripe's official
documentation and support pages make a few things clear.

Expect to provide some or all of the following:

- legal entity or personal name,
- date of birth for the representative or individual,
- address,
- bank account for payouts,
- website or public web presence,
- phone and public contact details,
- tax or registration number when the entity type requires it,
- and possibly verification documents.

Good to know:

- Stripe checks the business profile and website details.
- If the website or public page is incomplete, verification can fail.
- If you do not have a website or public web presence that explains what you
  are charging for, Stripe says you should contact support for alternative
  verification options.

For this project, the public website is a strong advantage because it already
shows:

- what the event is,
- what the payment is for,
- contact information,
- and the booking flow.

## What to do if Stripe asks for a business number

For this project, the safest assumption is:

- if there is no registered entity, you should not enter a made-up business
  number.

Examples:

- registered non-profit or association:
  use that entity's official registration or tax number if Stripe asks for it
- registered company:
  use the company's number
- no registered entity:
  do not guess or borrow someone else's organization number just to get through
  onboarding

Stripe also notes that for some unincorporated entities, partnerships, or
non-profits, additional verification documentation might be required, and in
some countries onboarding as a non-profit through the normal form is not always
available. In those cases Stripe says the account might need to onboard using a
different entity path that matches the real legal setup.

## Recommended decision rule for this project

Use this simple rule:

- because this event currently has no registered legal entity behind it,
  onboard Stripe using the real individual who will legally receive and manage
  the payouts,
- use that same person's real identity and payout information during
  verification,
- and only change away from that model later if the event gets a formally
  registered legal entity.

Because this site is for event booking fees, not tax-deductible donation
collection, do not assume Stripe's non-profit pages automatically change the
required legal setup. Those pages mostly explain how Stripe can be used by
non-profits, not that Stripe will let an unregistered organizer skip identity
and entity verification.

## Suggested later setup checklist

When you are ready to create the dedicated production account:

1. Decide the dedicated event email address.
2. Decide which one real person will legally own and verify the Stripe account.
   This person should be the one whose identity and bank payout information can
   honestly be used during onboarding.
3. Gather:
   - that person's full legal name,
   - date of birth if Stripe asks for it,
   - address,
   - phone number,
   - bank account details for payouts,
   - the public website URL,
   - and any identification or verification documents Stripe later asks for.
4. Create the Stripe account with the dedicated event email.
5. During onboarding, choose the option that matches an individual-operated
   setup with no registered company or association.
6. When Stripe asks what you sell or charge for, describe the real activity in
   plain language, for example:
   - event canoe booking for a yearly paddling event,
   - card payments collected through the event website,
   - money used to cover canoe rental costs for the event.
7. Add the website URL so Stripe can see the public booking flow and contact
   details.
8. Complete identity and payout verification honestly and exactly.
9. If Stripe asks for documents, upload the real supporting documents through
   Stripe Dashboard.
10. Only after that, switch the app from the current temporary/testing setup to
   the new dedicated Stripe account keys.

## Suggested answers during onboarding for this project

These are not official fixed field values, because Stripe can change the
questions slightly, but they show the direction you should follow.

Who owns the account:

- the real individual who will receive payouts and handle verification

What type of organization is this:

- choose the individual / no registered business path

What is the website used for:

- booking canoes for the yearly paddling event

What are customers paying for:

- canoe booking fee for the event

Why is there no business number:

- because there is no registered company or association behind the event

Which bank account should receive payouts:

- the bank account belonging to the same real person who owns the Stripe
  account and passes verification

Important:

- do not use one person's identity with another person's bank account unless
  Stripe explicitly allows and verifies that structure,
- and do not say the account belongs to a non-profit organisation if no such
  legal entity exists.

## When to stop and double-check before continuing

Pause and verify before continuing if:

- you are unsure which real person should legally own the Stripe account,
- you are unsure whose bank account should receive payouts,
- you are unsure what Stripe means by a tax, registration, or business number,
- or the onboarding form seems to force a company or organization path that
  does not match your real setup.

In those cases, stop before submitting incorrect details. Confirm the real legal
owner first, and if needed ask Stripe support which onboarding option matches a
community-run event with no registered legal entity.

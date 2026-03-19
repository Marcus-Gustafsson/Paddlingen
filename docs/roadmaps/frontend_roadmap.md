# Frontend Roadmap

Last updated: 2026-03-19

## Goal

Make the public and admin interfaces clear, modern, and easy to use.

This roadmap covers:

- public page layout,
- booking UX,
- admin page design,
- responsive testing.

## Completed Foundation Work

These frontend milestones are already done:

- The public homepage has been redesigned around a single hero section.
- The old previous-years sidebar and stacked archive sections are gone.
- The rolling previous-years ribbon is in place.
- The booking modal has been redesigned into a two-step flow.
- The FAQ and contact popups now match the newer visual direction.
- Desktop, tablet, and phone layouts have had an initial responsive pass.

## Phase 1: Keep The Public Homepage Consistent

### Step 1. Review the current hero spacing and responsive balance (Completed 2026-03-19)

Completed work:

- Tuned desktop, tablet, and phone hero spacing.
- Moved weather and utility buttons into clearer responsive positions.
- Tightened the first-screen vertical layout.

### Step 2. Keep the ribbon and gallery experience working (Completed 2026-03-19)

Completed work:

- Replaced the stuttering ribbon loop with a smoother animation.
- Added fading ribbon edges.
- Kept the gallery modal connected to the ribbon.

### Step 3. Keep the booking modal aligned with the public design (Completed 2026-03-19)

Completed work:

- Introduced the two-step booking flow.
- Limited one booking to five canoes.
- Improved the booking summary and quantity selector behavior.

## Phase 2: Redesign The Admin Login Page

Goal:

- Make the admin login page feel intentional and consistent with the rest of
  the site.

### Step 1. Redesign the login layout

What to do:

- Replace the current page with one centered login card.
- Keep one clear title, clear labels, and one obvious submit action.

Why:

- The current login page works, but it still looks much older than the public
  page.

How to test:

- Open `/login` and confirm the page is visually cleaner and still easy to use.

### Step 2. Improve validation and feedback visibility on the login page

What to do:

- Make error and success messages easier to notice.
- Confirm keyboard focus stays sensible after a failed login.

Why:

- A polished login page should still behave clearly when something goes wrong.

How to test:

- Try an invalid login and confirm the message is easy to see.

## Phase 3: Redesign The Admin Dashboard

Goal:

- Make the admin page easier to read and safer to use for booking changes.

### Step 1. Redesign the booking list layout

What to do:

- Replace the current plain layout with clearer rows or cards.
- Improve spacing, headings, and scanability.

Why:

- The admin dashboard should feel like a small internal tool, not a rough form
  page.

How to test:

- Log in as admin and confirm the booking list is easier to read.

### Step 2. Make add, edit, and delete actions visually clearer

What to do:

- Improve the placement and visual distinction of the CRUD actions.

Why:

- Admin actions should be obvious and hard to confuse.

How to test:

- Add, edit, and delete a booking and confirm the actions are easy to follow.

### Step 3. Add room for future booking metadata

What to do:

- Reserve space for future fields such as:
  - booking reference,
  - payment state,
  - event link.

Why:

- The admin UI will need more booking context once Stripe is added.

How to test:

- Review the new layout and confirm it can grow without another redesign.

## Phase 4: Re-test The Full Frontend On Real Layouts

Goal:

- Confirm the redesigned public and admin pages stay usable across screen sizes.

### Step 1. Re-test desktop, phone, and tablet layouts

What to do:

- Re-run manual checks on:
  - homepage,
  - booking modal,
  - FAQ/contact popups,
  - admin login,
  - admin dashboard.

Why:

- Layout regressions are common after design changes.

How to test:

- Check desktop and browser device emulation for phone and tablet widths.

### Step 2. Test the homepage on a real phone later through ngrok

What to do:

- Open the public page on a real phone through the ngrok workflow.

Why:

- Browser emulation is helpful, but it does not replace a real device.

How to test:

- Load the site on a phone and confirm the public page feels correct.

## Current Recommended Next Step

The next frontend step is:

1. Wait until the backend event-settings work is started.
2. Then redesign the admin login page.
3. After that, redesign the admin dashboard.

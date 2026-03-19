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

- Make the admin page easier to read and safe for non-technical admins to use.

### Step 1. Redesign the dashboard around two primary admin actions

Status:

- Initial draft implemented on 2026-03-19.
- Further visual refinement is still expected after manual review.

What to do:

- Replace the current plain page with a clearer dashboard layout.
- Add two obvious primary action buttons or cards:
  - `Hantera bokningar`
  - `Hantera event`
- Make these the first things an admin sees after logging in.

Why:

- Most admins should not need to understand the whole page structure before
  making a simple change.
- Clear top-level actions reduce mistakes and make the page easier to learn.

How to test:

- Log in as admin and confirm the two primary actions are immediately obvious
  and easy to understand without technical context.

### Step 2. Add a booking-management modal or panel

Status:

- Initial draft implemented on 2026-03-19.
- The panel now supports:
  - manual booking creation,
  - booking name edits,
  - booking deletion,
  - manual payment-method selection for admin-added bookings.

What to do:

- Add one focused booking-management modal or panel that opens from
  `Hantera bokningar`.
- Let admins:
  - add canoe bookings
  - edit existing bookings
  - delete bookings
- Keep the booking controls grouped together instead of scattered across the
  page.
- Keep the workflow simple enough that a new admin can make a change without
  understanding the database tables behind it.

Why:

- Booking edits are the most common admin action right now.
- A focused booking-management view should be faster and less confusing.

How to test:

- Add, edit, and delete a booking and confirm the workflow feels clear from one
  place.

### Step 3. Add an event-settings modal or panel

Status:

- Initial draft implemented on 2026-03-19.
- The panel now supports:
  - selecting an existing event,
  - editing event fields,
  - creating a new event by copying an existing one,
  - activating the selected event.

What to do:

- Add one focused event-management modal or panel that opens from
  `Hantera event`.
- Let admins:
  - select an existing event row
  - update all editable event fields for that row
  - create a new event for an upcoming year
  - switch which event is active
- Make the editable fields cover the event data now stored in the database,
  including:
  - title
  - subtitle
  - event date
  - start time
  - start and end locations
  - available canoes
  - price per canoe
  - max canoes per booking
  - weather settings
  - FAQ card content
  - rules card content
  - contact details

Why:

- Event changes should not require source-code edits.
- Some future admins will not have programming experience, so the event changes
  must feel like editing content, not editing configuration.

How to test:

- Create a new event row.
- Switch the active event.
- Update one visible field and confirm the public homepage reflects the saved
  value.
- Confirm a non-technical admin can understand which values affect the public
  page without needing developer help.

### Step 4. Add room for future booking metadata

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

1. Redesign the admin login page so it matches the newer public-site styling.
2. Then redesign the admin dashboard around two primary actions:
   - `Hantera bokningar`
   - `Hantera event`
3. After that, implement the event-management modal so admins can edit active
   event values and create upcoming event rows without changing source code.

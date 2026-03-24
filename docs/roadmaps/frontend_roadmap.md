# Frontend Roadmap

Last updated: 2026-03-20

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

### Step 1. Redesign the login layout (Completed 2026-03-20)

Completed work:

- Replace the current page with one centered login card.
- Keep one clear title, clear labels, and one obvious submit action.
- Align the visual direction with the public site.
- Keep the page responsive on desktop, tablet, and phone.

Why:

- The current login page works, but it still looks much older than the public
  page.

How to test:

- Open `/login` and confirm the page is visually cleaner and still easy to use.

### Step 2. Improve validation and feedback visibility on the login page (Completed 2026-03-20)

Completed work:

- Make error and success messages easier to notice.
- Replace the older banner-style feedback with clearer toast-style feedback.
- Keep login validation and messages understandable for non-technical admins.

Why:

- A polished login page should still behave clearly when something goes wrong.

How to test:

- Try an invalid login and confirm the message is easy to see.

## Phase 3: Redesign The Admin Dashboard

Goal:

- Make the admin page easier to read and safe for non-technical admins to use.

### Step 1. Redesign the dashboard around two primary admin actions (Completed 2026-03-20)

Completed work:

- Replace the current plain page with a clearer dashboard layout.
- Add two obvious primary action buttons or cards:
  - `Hantera bokningar`
  - `Hantera event`
- Make these the first things an admin sees after logging in.
- Refine the top-row utility layout and responsive behavior.

Why:

- Most admins should not need to understand the whole page structure before
  making a simple change.
- Clear top-level actions reduce mistakes and make the page easier to learn.

How to test:

- Log in as admin and confirm the two primary actions are immediately obvious
  and easy to understand without technical context.

### Step 2. Add a booking-management modal or panel (Completed 2026-03-20)

Completed work:

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
- Support manual payment methods, including Stripe fallback cases.
- Split participant names into first-name and last-name fields.
- Improve mobile rendering by switching to stacked booking cards on smaller
  screens.

Why:

- Booking edits are the most common admin action right now.
- A focused booking-management view should be faster and less confusing.

How to test:

- Add, edit, and delete a booking and confirm the workflow feels clear from one
  place.

### Step 3. Add an event-settings modal or panel (Completed 2026-03-20)

Completed work:

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
- Simplify the create flow so new events only require a new date and copy the
  rest from the selected event.
- Keep the admin-facing date and time fields aligned with Swedish formats.
- Move low-change technical fields out of the admin form to keep the UI simpler
  for non-technical admins.

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

### Step 5. Prepare the public booking flow for Stripe-hosted Checkout

Implementation note:

- Backend Phase 4 Step 1 has already chosen Stripe-hosted Checkout as the
  first real payment UI.
- The remaining frontend work in this step is to make the public return states
  clear and consistent once the real Stripe redirect is connected.
- Backend Phase 4 Step 2 has also chosen the meaning of those return states:
  - `/payment-success` should confirm only that the visitor returned from
    Stripe,
  - `/payment-cancel` should explain that payment was not completed and the
    unpaid reservation was released,
  - neither page should claim the booking is fully paid until webhook
    verification has happened.

What to do:

- Keep the public booking modal focused on booking review and participant
  details, not card entry.
- Redirect the user from the booking summary step to Stripe-hosted Checkout
  instead of trying to collect payment details in the site itself.
- Add clear return states for:
  - successful payment return,
  - canceled payment return,
  - declined or otherwise failed payment attempts.

Why:

- Stripe-hosted Checkout keeps the public payment UI simpler and safer for the
  first real payment release.
- The user should still understand what happened when they return to the site.

How to test:

- Start a booking and confirm:
  - the site redirects cleanly to Stripe Checkout,
  - the success return is clear,
  - the cancel return is clear,
  - the site does not claim payment success before the backend has verified it.

### Step 6. Add secondary admin utility actions

What to do:

- Add smaller secondary admin actions below the main booking and event cards.
- Start with:
  - shared public-password rotation,
  - one reserved checklist action slot for later.

Why:

- Some admin workflows are important but should not compete visually with the
  two primary actions.

How to test:

- Confirm the new utility actions are easy to find without overpowering the
  main booking and event actions.

### Step 7. Add an event-day checklist tool later

What to do:

- Turn the reserved checklist action into a real admin tool.
- Support both on-screen check-off and printable export (.pdf to start with).
- The on-screen checklist is now implemented with grouped names on the left and
  one checkbox per canoe on the right.
- Printable export is still pending.

Why:

- The event staff still need a practical replacement for the older paper-based
  check-off workflow.

How to test:

- Open the checklist tool from the admin page and confirm it works both on
  screen and for print/PDF use.

### Step 8. Refine the public participant overview for grouped canoe counts

What to do:

- Show the participant name on the left and the canoe count on the right once
  grouped multi-canoe bookings are supported.

Why:

- The current overview is still built around one row per canoe.

How to test:

- Confirm the overview stays readable when one person holds multiple canoes.

### Step 9. Extend the booking modal for named riders inside each canoe (Completed 2026-03-24)

Completed work:

- Kept the current canoe-card layout in the public booking modal.
- Updated each canoe card to collect:
  - one required pickup person,
  - one optional second rider field pair shown by a small add/remove button,
  - one optional third rider field pair shown by a small add/remove button.
- Kept rider two and rider three optional, but now require complete first- and
  last-name pairs when either optional rider is used.
- Updated the booking summary so it shows the pickup person first and the
  optional riders below.

### Step 10. Keep grouped overview and checklist rows expandable (Completed 2026-03-24)

Completed work:

- Kept the grouped row summary in both:
  - the public participant overview,
  - the admin event-day checklist.
- Added expandable canoe-detail rows under each grouped pickup person.
- Made the public grouped overview row a full-width button.
- Made the checklist summary area a button while keeping the per-canoe
  checkboxes separate and clickable.
- Added the canoe-detail text to the rendered HTML so later UI styling and
  interaction work stays simpler.

### Step 11. Extend manual admin booking and editing to match the canoe layout (Completed 2026-03-24)

Completed work:

- Updated the admin manual-booking form to use the same canoe-based shape as
  the public booking flow.
- Added support for:
  - pickup person,
  - optional second rider shown by a small add/remove button,
  - optional third rider behind a small add/remove button.
- Updated the admin edit form so the same canoe row can be corrected later
  without leaving the dashboard.

## Phase 4: Re-test The Full Frontend On Real Layouts

Goal:

- Confirm the redesigned public and admin pages stay usable across screen sizes.

### Step 1. Re-test desktop, phone, and tablet layouts (Completed 2026-03-20)

Completed work:

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

## Phase 5: Improve The Gallery And Public Image Handling

Goal:

- Keep the previous-years images easier to load, easier to manage, and easier
  to identify when someone asks about a specific photo.

### Step 1. Add optimized image variants for ribbon and gallery (Completed 2026-03-20)

Completed work:

- Stop using the same image files for every gallery-related surface.
- Add:
  - smaller ribbon thumbnails,
  - medium-sized gallery images,
  - and keep originals archived separately if needed later.
- Generate those variants together with the image metadata sync workflow.

Why:

- The homepage ribbon should not need to download the same heavier files that
  the full gallery uses.
- Smaller image variants reduce bandwidth and improve the page feel.

How to test:

- Open the homepage and confirm the ribbon still looks correct.
- Open the gallery and confirm the modal still looks sharp enough.
- Compare page load size before and after the change.

### Step 2. Add image metadata with stable public IDs (Completed 2026-03-20)

Completed work:

- Add one metadata file for the previous-years images.
- Give each image a stable public ID such as:
  - `IMG-0001`
  - `IMG-0002`
- Keep the first version simple with:
  - image ID,
  - filename.
- Add a sync script so new or removed files can update the metadata file
  without changing older image IDs.

Why:

- The current `1 / 100` gallery counter is not stable enough to use as a
  support identifier.
- Stable image IDs let users report one specific picture even if the gallery
  order changes later.

How to test:

- Open the gallery and confirm each image has one stable ID.
- Reorder or add one image and confirm the older image IDs do not change.

### Step 3. Show image support information inside the gallery modal (Completed 2026-03-20)

Completed work:

- Add a small information button or help area inside the gallery modal.
- Show:
  - the stable image ID,
  - and short text explaining how someone can contact the organizer by email
    if they want to ask a question or request removal.
- Keep that information inside a separate `?` popup instead of showing it on
  every image all the time.

Why:

- This gives users a clear and consistent way to identify the correct photo.

How to test:

- Open the gallery modal.
- Confirm the image help/info area is easy to find but does not get in the way
  of the image itself.

### Step 4. Reduce homepage image loading further (Completed 2026-03-20)

Completed work:

- Review how many ribbon images are loaded immediately.
- Avoid downloading more image data than the homepage really needs.
- Switch the ribbon from CSS background images to lazy-loaded `<img>` elements
  so the browser can defer offscreen image work more effectively.
- Add next/previous image preloading in the gallery lightbox so browsing
  remains smooth without loading the whole gallery at once.

Why:

- Even with local hosting or a VPS, smaller homepage payloads improve user
  experience and make hosting simpler.

How to test:

- Reload the homepage with the browser network panel open.
- Confirm fewer or smaller image files are loaded on first view.

## Current Recommended Next Step

The next frontend step is:

1. Keep refining the admin and public responsive layout based on real-device
   testing.
2. Move to the next roadmap area outside `Phase 5`, since the gallery image
   handling work is now in place.

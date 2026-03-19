# Temporary Refactor Checklist

Last updated: 2026-03-19

## Purpose

This is a temporary working document for the upcoming refactor work.

It is meant to help us:

- break the refactor into smaller steps,
- check off each step one by one,
- avoid changing too many things at the same time,
- keep the project understandable while we restructure it.

This file is intentionally temporary.

When the refactor is finished, the final structure should instead be reflected
in the normal project documentation.

## Current State Summary

The main files that are now large enough to justify splitting are:

- `static/js/main.js` at about 72 lines
- `docs/Roadmap.md` at about 955 lines
- `docs/dev_doc.md` at about 589 lines
- `docs/TechnicalOverview.md` at about 855 lines
- `templates/index.html` at about 386 lines

This means the refactor goal is reasonable and justified.

## Recommended Order

This is the safest order to do the refactor in:

1. Decide the target structure before moving files.
2. Split CSS.
3. Split JavaScript.
4. Flatten the previous-years images into one folder and update image lookup.
5. Split roadmap documents.
6. Split development documentation.
7. Do a final cleanup pass and update all references.

Why this order:

- CSS and JavaScript splitting have the clearest value and lowest framework
  risk.
- The image refactor is also useful, but it should happen after the frontend
  file split direction is clear.
- Renaming Flask `templates/` is possible, but it is lower value and more
  likely to create confusion than the other changes.
- The documentation split should happen after the code/file structure is more
  settled, otherwise we risk rewriting the docs twice.

## Refactor Checklist

### Phase 1: Decide the target structure

- [ ] Decide the final CSS file structure.
- [ ] Decide the final JavaScript file structure.
- [ ] Decide whether image filenames need to be renamed before flattening into
      one folder.

Recommended decisions:

- Keep `static/css/admin.css` as its own file.
- Split public CSS into a few larger files, not many tiny ones.
- Split JavaScript by feature, then use one small entry file to initialize the
  page.
- Keep `templates/` as the Flask-standard folder name.

### Phase 2: Split the public CSS (DONE)

- [x] Audit `static/css/styles.css` and group rules into major sections.
- [x] Decide the new CSS file names.
- [x] Move the reset/base styles into a shared file.
- [x] Move homepage hero and ribbon styles into a public homepage file.
- [x] Move modal styles into a modal-focused file.
- [x] Move booking modal styles into a booking-focused file.
- [x] Move gallery ribbon and gallery modal styles into a gallery-focused file.
- [ ] Keep admin styles separate in `static/css/admin.css`.
- [x] Remove `static/css/styles.css` after the remaining useful rules were
      moved elsewhere.
- [x] Update the template `<link>` tags to load the new files in the correct
      order.
- [x] Test desktop, tablet, and mobile again after the split.

Suggested CSS structure:

- `static/css/base.css`
- `static/css/home.css`
- `static/css/modals.css`
- `static/css/booking.css`
- `static/css/gallery.css`
- `static/css/admin.css`

Why this structure:

- It keeps the number of files reasonable.
- It separates the biggest public UI areas cleanly.
- It avoids over-splitting into many tiny component files.

How to test after this phase:

- Homepage loads correctly.
- Booking modal still opens and looks correct.
- FAQ and contact popups still open and look correct.
- Gallery ribbon and gallery modal still work.

### Phase 3: Split the public JavaScript (DONE)

- [x] Audit `static/js/script.js` and group logic by feature.
- [x] Decide the new JavaScript file names.
- [x] Create one small entry file that initializes the page.
- [x] Move booking logic into its own file.
- [x] Move modal logic into its own file.
- [x] Move gallery logic into its own file.
- [x] Move weather logic into its own file.
- [x] Move booking-progress logic into its own file.
- [x] Update `index.html` to load the scripts in a safe order.
- [x] Test all homepage interactions again.

Suggested JavaScript structure:

- `static/js/main.js`
- `static/js/booking_progress.js`
- `static/js/weather.js`
- `static/js/modals.js`
- `static/js/gallery.js`
- `static/js/booking.js`

Why this structure:

- It matches how the page already works logically.
- Each file gets one main responsibility.
- It stays understandable without introducing a frontend framework or bundler.

Implementation note:

- The simplest path is likely to keep plain browser scripts and load them with
  `defer`.
- We should avoid introducing a build step unless it solves a real problem.

How to test after this phase:

- Weather still loads or shows the countdown correctly.
- Booking progress still updates.
- Booking modal still works end to end.
- FAQ/contact popups still work.
- Previous-years gallery still works.

Audit findings:

- The old `script.js` used to mix six responsibilities in one file:
  - event settings,
  - booking progress,
  - weather,
  - FAQ/contact/overview modal behavior,
  - gallery ribbon and lightbox,
  - booking modal logic.
- The booking modal block is the largest and most stateful part of the file.
- `updateBookingProgress()` currently uses `innerHTML`, which is workable but
  should be treated carefully and kept scoped to known text-only markup.
- Multiple features attach separate global `keydown` listeners. This works, but
  splitting the file will make those listeners easier to reason about.
- The safest split order is:
  1. `booking_progress.js`
  2. `weather.js`
  3. `modals.js`
  4. `gallery.js`
  5. `booking.js`
  6. `main.js`

Current progress note:

- `static/js/booking_progress.js` now handles the homepage booking-progress
  updates.
- `static/js/weather.js` now handles the weather countdown and forecast widget.
- `static/js/modals.js` now handles the FAQ, contact, and participant
  overview popup behavior.
- `static/js/gallery.js` now handles the previous-years ribbon animation and
  gallery lightbox behavior.
- `static/js/booking.js` now handles the two-step booking modal, participant
  field generation, and booking summary.
- `static/js/main.js` now contains the final shared page initialization
  sequence and the scroll animation helper.

### Architecture Note: Move Event Settings Into The Database

- [ ] Add an `events` table so the current event can be edited from the admin
      panel instead of from `config.py`.
- [ ] Add an `is_active` flag or another clear way to mark which event is the
      current live event.
- [ ] Move editable values such as year, date, start time, location, location
      URL, available canoes, rules text, FAQ text, contact email, and contact
      phone into that table.
- [ ] Decide whether weather cache fields should live in the `events` table or
      in a separate weather-cache table.
- [ ] Add an admin form for updating the active event settings safely.

Recommended setup:

- Use one `events` table with one row per event year or event instance.
- Keep booking rows linked to the relevant event row instead of assuming there
  is only one global event forever.
- Store admin-editable content in normal columns so non-technical admins do
  not need to change source code.
- For weather, use cached data rather than calling the weather API on every
  page load.

Recommended event columns:

- `id`
- `year`
- `event_date`
- `start_time`
- `starting_location_name`
- `starting_location_url`
- `end_location_name` (end_location name and url, as it will be usefull information to have under e.g. FAQ/information, as the end location/where the canoes are picked up is at a different location compared to the starting location, thus having navigation (e.g. google maps link) and location name is good information)
- `end_location_url`
- `available_canoes`
- `rules_text`
- `faq_text` or structured FAQ fields
- `contact_email`
- `contact_phone`
- `is_active`
- `weather_cached_summary`
- `weather_cached_temperature`
- `weather_cached_rain_mm`
- `weather_cached_icon`
- `weather_cached_at`

Important note:

- Once event settings move into the database, the weather widget can handle
  past events more cleanly by showing either:
  - a saved weather snapshot from event day,
  - or a simple message that the event has already passed.

### Phase 4: Flatten previous-years images into one folder

- [x] Review all image folders currently used by the homepage and gallery.
- [x] Confirm which files should move into `static/images/previous_years/`.
- [x] Check for duplicate filenames before moving images.
- [x] Rename files if needed so no files overwrite each other.
- [x] Update image lookup logic in the backend helper functions.
- [x] Update any hardcoded image paths still used by the homepage or gallery.
- [x] Remove old year-based gallery folder usage once the new folder works.

Important note:

- Duplicate filenames were found across the old year folders.
- Those files were kept by renaming them with a year prefix inside
  `static/images/previous_years/` instead of overwriting them.
- The current homepage background image was kept out of that folder and now
  lives at `static/images/nitten.png`.

How to test after this phase:

- The homepage hero still loads its background image.
- The ribbon still shows images.
- The gallery modal still opens and cycles through the previous-years images.

### Phase 5: Split the roadmap documents

- [ ] Decide the final roadmap categories.
- [ ] Move frontend work into a frontend roadmap.
- [ ] Move backend/database/payment work into a backend roadmap.
- [ ] Move deployment/monitoring/project-structure tasks into a misc or ops
      roadmap.
- [ ] Add a short index document that explains which roadmap to read first.
- [ ] Remove duplicated items during the split.

Suggested roadmap structure:

- `docs/roadmaps/frontend_roadmap.md`
- `docs/roadmaps/backend_roadmap.md`
- `docs/roadmaps/misc_roadmap.md`
- `docs/roadmaps/README.md`

Why this structure:

- It separates concerns clearly.
- It keeps each roadmap shorter and easier to scan.
- It still keeps the number of documents limited.

### Phase 6: Split the development documentation

- [ ] Decide the final development document categories.
- [ ] Move Docker-specific content into a Docker document.
- [ ] Move Supabase/database-specific content into a database document.
- [ ] Move testing and local commands into a general development document.
- [ ] Add one small index document for the development docs.
- [ ] Remove duplicated commands or notes that appear in multiple files.

Suggested development-document structure:

- `docs/dev/dev_overview.md`
- `docs/dev/dev_docker.md`
- `docs/dev/dev_database.md`
- `docs/dev/dev_testing.md`

Why this structure:

- It keeps related commands together.
- It avoids one very long development document.
- It still stays within a manageable number of files.

### Phase 7: Final cleanup and verification

- [ ] Remove dead CSS selectors, dead JavaScript functions, and outdated file
      references.
- [ ] Update `README.md`.
- [ ] Update `docs/TechnicalOverview.md`.
- [ ] Update the roadmap files after the split.
- [ ] Update `AGENTS.md` so the documentation rules point to the new roadmap
      and development-document locations.
- [ ] Run the relevant tests.
- [ ] Manually test the homepage, booking flow, and admin pages.

## Decision Notes

These are the most important architectural recommendations before starting:

### Recommendation 1: Split CSS and JavaScript first

This gives the clearest improvement with the lowest risk.

### Recommendation 2: Flatten the gallery images, but do it carefully

The main technical risk is filename collisions.

### Recommendation 3: Split docs after the code structure is settled

Otherwise the documentation will be rewritten twice.

## First Recommended Implementation Step

When we start the actual refactor, the first step should be:

- split `static/css/styles.css` into a few larger focused files

Why:

- It is currently the largest file.
- It directly affects readability.
- It can be tested visually right away.

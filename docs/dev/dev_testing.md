# Development Testing

Last updated: 2026-03-19

## Purpose

This document contains the practical test and verification commands used during
normal development.

## Common Commands

### Install dependencies

```bash
make install
```

Alternative:

```bash
uv sync
```

### Run the full test suite

```bash
make test
```

Alternative:

```bash
uv run -m pytest -q
```

### Run linting

```bash
make lint
```

### Check formatting

```bash
make format-check
```

### Apply formatting

```bash
make format
```

### Run type checking

```bash
make type-check
```

## Current Manual Homepage Check

Start the app:

```bash
uv run flask --app wsgi --debug run
```

Then open:

```text
http://127.0.0.1:5000
```

Check:

- homepage hero loads,
- weather widget loads,
- info and contact popups open,
- progress bar updates,
- participant list popup opens,
- booking modal opens,
- ribbon scrolls,
- gallery modal opens.

## Development Booking Seed Commands

These commands are useful when you want to test near-full or sold-out states
without creating many bookings manually.

### Seed test bookings

```bash
uv run flask --app wsgi seed-test-bookings --count 39
```

What it does:

- removes older seeded test bookings first,
- creates the requested number of confirmed test bookings,
- marks them with `payment_provider = "dev_seed"`.

### Clear test bookings

```bash
uv run flask --app wsgi clear-test-bookings
```

What it does:

- removes the seeded test bookings without touching normal bookings.

### Suggested testing workflow

1. Seed a near-full state:

```bash
uv run flask --app wsgi seed-test-bookings --count 39
```

2. Open the homepage and test the booking UI.

3. Clear the seeded data:

```bash
uv run flask --app wsgi clear-test-bookings
```

## Notes About Warnings

You may still see warnings in some test runs, for example:

- Flask-Limiter using in-memory rate-limit storage,
- SQLAlchemy legacy query warnings in older code paths.

These warnings do not always mean the feature is broken, but they should still
be reviewed when the related code is touched.

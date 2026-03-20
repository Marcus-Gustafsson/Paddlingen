# Development Testing

Last updated: 2026-03-20

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

What it checks:

- runs `ruff`
- looks for common code issues such as unused imports, simple mistakes, and
  style problems that the project wants to keep consistent

### Check formatting

```bash
make format-check
```

What it checks:

- runs `black --check`
- confirms that the Python files already match the project's formatting rules
- does not change any files

If this fails, the usual fix is:

```bash
make format
```

Then run `make format-check` again.

### Apply formatting

```bash
make format
```

What it does:

- runs `black`
- rewrites Python files into the expected project format automatically

### Run type checking

```bash
make type-check
```

What it checks:

- runs `mypy`
- checks whether type hints and function calls are consistent
- helps catch mistakes before runtime, especially when values can be `None` or
  have the wrong type

### Run the normal full local verification

```bash
make all-basic
```

What it does:

- runs `make install`
- runs `make lint`
- runs `make format-check`
- runs `make type-check`
- runs `make test`

This is the main command to use after a normal implementation step when you
want to check that the project still works as expected.

### Run the broader local verification

```bash
make all-advanced
```

What it does:

- runs everything in `make all-basic`
- also runs the security checks:
  - `bandit` on the source code
  - `pip-audit` on installed dependencies

When to use it:

- before a larger handoff
- before release or deployment work
- after dependency changes

Important note:

- `pip-audit` may depend on network access and can be slower or noisier than the
  normal development checks
- because of that, `make all-advanced` is useful, but it does not need to be
  run after every tiny CSS or documentation change
- `bandit` should be run against the project code, not against the whole repo
  root including `.venv`, otherwise you may see noisy warnings from third-party
  files that are not part of this application

### Run only the code security scan

```bash
make security-code
```

What it checks:

- runs `bandit`
- scans the project's Python code for common security mistakes
- example findings can include missing request timeouts or risky subprocess use

### Run only the dependency security scan

```bash
make security-deps
```

What it checks:

- runs `pip-audit`
- audits the project's locked dependencies, exported from `uv.lock`
- checks project dependencies for known published vulnerabilities
- this may require network access

## Recommended Workflow

For most normal code changes:

1. Make the code change.
2. Run the most relevant targeted tests while working.
3. Before considering the step finished, run:

```bash
make all-basic
```

If `make all-basic` fails only because of formatting, run:

```bash
make format
make all-basic
```

For bigger changes, dependency updates, or pre-release checks, also run:

```bash
make all-advanced
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

## Previous-Years Image Asset Sync

Run this whenever you add, remove, or rename files in:

```text
static/images/previous_years/
```

Command:

```bash
uv run python scripts/sync_previous_year_image_metadata.py
```

What it does:

- reads the current image files,
- loads `data/previous_year_images.json`,
- keeps existing `IMG-000x` IDs for filenames that already exist,
- assigns new IDs only to new filenames,
- removes metadata rows for files that no longer exist.
- writes optimized ribbon variants to `static/images/previous_years/ribbon/`,
- writes optimized gallery variants to `static/images/previous_years/gallery/`.

Best practice:

- run this script explicitly when the image folder changes
- do not try to update the metadata automatically on app startup

Why:

- explicit updates are easier to reason about
- automatic rewrites during app startup can hide mistakes and make image-ID
  changes harder to track
- generating the optimized image variants at the same time keeps the public
  image paths in sync with the metadata

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

## Notes About Security Tool Output

If `bandit` prints many strange warnings about comments or test names, that
usually means it scanned files outside the real application source, for example
inside `.venv`. The normal project command avoids that by scanning only the
project's Python files.

If `pip-audit` fails, separate these cases:

- `No module named pip_audit`
  - the command is being called incorrectly or the tool is not installed in the
    environment
- network or registry errors
  - the tool is installed, but it could not reach the vulnerability data source
- vulnerability findings
  - the command is working correctly, but one or more pinned dependency
    versions should be upgraded

# AGENTS.md

## Scope

This file applies to the entire repository.

Its purpose is to tell coding agents and collaborators how to work in this
project so the codebase stays understandable, beginner friendly, and easy to
maintain over time.

## Project Context

- This is a small Flask web application for a canoe event booking website.
- The project should stay simple, understandable, and practical.
- The main goals are:
  - public event website,
  - booking flow,
  - database-backed booking storage,
  - safe payment flow through Stripe,
  - previous-years image display,
  - logging and monitoring,
  - deployment that is easy to reason about.
- The UI that the admin and user interact with should all be in correct Swedish grammar, as the users of the website are only Swedish people.
- All dates, currency, time, should use Swedish format.
- The code, comments, dev documents, commands, explanations, roadmaps, etc should be in English
- All explanations should be beginner friendly, and all commands should be fully documented.
- Always respond in English in the codex session, do not switch to Swedish.

## Development Environment

- The project is developed on WSL on a Windows 11 machine.
- Default command examples, guides, and local development notes should assume:
  - Ubuntu or similar Linux shell inside WSL,
  - `bash`,
  - commands run from the project root.
- If Windows-specific commands are needed, label them clearly as Windows-only.
- Do not assume PowerShell unless the task is specifically Windows-side.

## Documentation Rules

- Keep documentation in sync with the code.
- If behavior, architecture, workflow, or tooling changes, update:
  - the relevant file in `docs/roadmaps/`
  - `docs/TechnicalOverview.md`
  - the relevant file in `docs/dev/`
- Do not leave newly implemented features undocumented.
- Prefer clear, beginner-friendly explanations over dense technical
  language.

## Code Style Expectations

- Write code for clarity first.
- Prefer simple, explicit code over clever shortcuts.
- Keep functions focused on one responsibility.
- Keep files reasonably organized by responsibility.
- If a file starts handling too many unrelated concerns, split it into smaller
  units.

## Naming Rules

- Use full, clear function names.
- Avoid cryptic abbreviations unless they are standard and obvious.
- Names should explain what the value or function represents without needing
  extra guesswork.

Good examples:

- `pending_booking`
- `available_canoes`
- `create_checkout_session`
- `is_payment_confirmed`

Avoid:

- `pb`
- `val`
- `tmp`
- `do_stuff`

## Python Standards

- Use type hints on function parameters and return values.
- Add docstrings to functions that explain:
  - what the function does,
  - the important inputs,
  - the return value,
  - any important side effects when relevant.
- Docstrings should be beginner friendly.
- Keep comments useful and explanatory, not noisy.

## Flask And Project Structure Guidelines

- Keep route handlers thin where possible.
- Put reusable business logic into helper functions or dedicated modules instead
  of growing route files endlessly.
- Keep configuration in `config.py` or environment variables, not hardcoded into
  route logic.
- Database schema changes should go through migrations.
- Avoid adding new global state unless there is a strong reason.
- Focus on modular programming, keeping each file and function more modular.

## Database Guidelines

- Treat PostgreSQL as the long-term target database.
- Prefer designs that will work correctly under concurrent access.
- Be explicit about booking rules, availability checks, and payment state.
- If database behavior changes, document the reason in the technical overview.

## Frontend Guidelines

- Preserve the simple server-rendered approach unless there is a clear reason to
  introduce more complexity.
- Keep HTML, CSS, and JavaScript understandable to a beginner.
- Avoid unnecessary framework adoption.
- If frontend files grow too large, 500 or more lines, split them into smaller pieces with clear names and objectives.

## Testing Expectations

- Prefer adding or updating tests when changing behavior.
- Run the most relevant checks after code changes.
- At minimum, run targeted tests for the area changed when practical.
- If a change affects core behavior, run the broader test suite if possible.
- After each meaningful implementation step, prefer running:
  - `make all-basic`
- Before a larger handoff, release step, or dependency-related change, prefer
  running:
  - `make all-advanced`
- If `make all-basic` fails on formatting, run:
  - `make format`
  - then rerun `make all-basic`

Current useful commands:

```bash
make test
make lint
make format-check
make type-check
make all-basic
make all-advanced
uv run -m pytest
```

## Dependency And Tooling Rules

- Prefer existing project tools before adding new ones.
- Do not add a new framework, service, or dependency unless it solves a real
  project problem.
- Keep the stack as small as practical.

## Change Management

- Make small, testable changes.
- Prefer one clear step at a time over large mixed refactors.
- If a change is part of the roadmap, keep the roadmap updated so it reflects
  what remains to be done.
- If something is still a placeholder, say so clearly in code or docs.

## Communication Style In Docs And Code

- Assume the reader may be new to programming or web development.
- Explain important architectural choices in simple language.
- When documenting commands, show the exact command to run.
- When documenting workflows, present them in a logical order.

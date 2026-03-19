# Docker Development

Last updated: 2026-03-19

## Purpose

This document explains the current Docker workflow.

It is written for someone who may be new to Docker.

## Beginner-Friendly Terms

- A Docker image is the built application package.
- A Docker container is one running instance created from that image.
- `docker run` starts a container directly.
- `docker compose` starts services defined in `compose.yaml`.

## Current Docker Scope

Right now, Docker only runs the Flask app container.

The database is not running inside Docker for this project.
The app connects to Supabase instead.

## Build the Flask app image

```bash
docker build -t paddlingen-web .
```

Why:

- Builds the current Flask application image from the root `Dockerfile`.

## Run the Flask app container directly

```bash
docker run --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
```

Why:

- Starts one container directly with a clear project-specific name.
- `--rm` removes the container automatically when it stops.

What to expect:

- The container stays attached to your terminal.
- Flask logs will appear in the terminal while it runs.
- Docker Desktop will show the same logs because it is reading the same output.

Stop it with:

```bash
Ctrl+C
```

## Run the container in the background

```bash
docker run -d --rm --name paddlingen-web -p 8080:8080 --env-file .env paddlingen-web
```

Useful follow-up commands:

```bash
docker logs -f paddlingen-web
docker stop paddlingen-web
```

## Run through Docker Compose

```bash
docker compose up --build
```

Why:

- Uses `compose.yaml`.
- Gives the project a stable Docker Desktop grouping.
- Makes it easier to add more services later if needed.

## Run Docker Compose in the background

```bash
docker compose up --build -d
```

Useful follow-up commands:

```bash
docker compose logs -f web
docker compose ps
docker compose down
```

## What To Test After Docker Changes

1. Build the image successfully.
2. Start the container.
3. Open:

```text
http://127.0.0.1:8080
```

4. Confirm:
- homepage loads,
- booking modal opens,
- FAQ and contact popups open,
- ribbon and gallery still work.

# ngrok Development

Last updated: 2026-03-20

## Purpose

This document explains how to expose the local Paddlingen site through ngrok
 so other people can open it while you are developing in WSL.

Use this when:

- you want a friend or another admin to test the site,
- you want to open the local site from a real phone,
- you later need a public URL for webhook testing.

## What ngrok does

ngrok does not run the website by itself.

It does one specific job:

- it creates a public internet URL,
- and forwards incoming traffic from that public URL to one local port on your
  computer.

That means you need two things running:

1. the local web application
2. ngrok

If the app is not running, ngrok has nothing to forward traffic to.

## What the local server command does

Example:

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

What this does:

- starts the Flask development server,
- binds it to port `5000`,
- allows the app to listen on all local network interfaces inside WSL.

In simple terms:

- this command makes the website run locally on your machine.

## What the ngrok command does

Example:

```bash
ngrok http 5000
```

What this does:

- opens a public ngrok URL,
- forwards requests from that public URL to `http://127.0.0.1:5000`.

In simple terms:

- this command makes the already-running local website reachable from the
  internet.

## Important rule about ports

The ngrok port must match the port used by the local app.

Examples:

- if Flask runs on `5000`, use:

```bash
ngrok http 5000
```

- if Docker Compose serves the app on `8080`, use:

```bash
ngrok http 8080
```

If you point ngrok to the wrong port, the public URL will exist, but it will
fail to load the site because nothing useful is listening there.

## Recommended WSL workflow with Flask

Open two terminals in WSL.

### Terminal 1: run the app

```bash
uv run flask --app wsgi --debug run --host 0.0.0.0 --port 5000
```

### Terminal 2: confirm the app works locally

```bash
curl -I http://127.0.0.1:5000
```

What to expect:

- you should get an HTTP response such as `200 OK` or `302 FOUND`

If this fails, fix the local app first before starting ngrok.

### Terminal 2: start ngrok

```bash
ngrok http 5000
```

What to expect:

- ngrok will show:
  - `Session Status`
  - `Forwarding`
  - a public `https://...ngrok-free.dev` URL

### Open the public URL

Copy the `Forwarding` URL and open it in a browser.

If the homepage loads there, you can send that URL to another person.

## Recommended workflow with Docker Compose

If you run the app with Docker instead, use the Docker port.

### Terminal 1: start Docker Compose

```bash
docker compose up --build
```

### Terminal 2: confirm the app works locally

```bash
curl -I http://127.0.0.1:8080
```

### Terminal 2: start ngrok

```bash
ngrok http 8080
```

## Step-by-step checklist for sharing the site

1. Start the local app.
2. Confirm the site works locally in your own browser first.
3. Start ngrok on the same port as the local app.
4. Copy the public ngrok URL.
5. Open the URL yourself once.
6. Send the same URL to your testers.

## Common mistake

This is the most common error:

```bash
ngrok http 80
```

Why it fails in this project:

- the Flask dev server normally uses `5000`
- the Docker setup normally uses `8080`
- port `80` is usually not where this app is running locally

That produces a public ngrok URL, but the tunnel has no correct upstream web
service behind it.

## If the ngrok URL shows an upstream connection error

Check these in order:

1. Is the app actually running?
2. Can you open the site locally first?
3. Did you give ngrok the correct port?
4. Is something listening on that port?

Useful command:

```bash
ss -ltn
```

Look for:

- `:5000`
- or `:8080`

## Security note

Do not share your ngrok authtoken.

If you accidentally paste or expose it anywhere, rotate it in the ngrok
dashboard and add the new one again:

```bash
ngrok config add-authtoken YOUR_NEW_TOKEN
```

## What to test after starting ngrok

1. Open the ngrok URL on your own computer.
2. Open the admin login page through the ngrok URL.
3. Open the booking modal and FAQ/contact popups.
4. Ask another person to open the same URL from another device.
5. Confirm the site loads the same way for them.

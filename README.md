<!--

File: README.md

What it does:
  - Gives a quick project overview.
  - Explains how to install dependencies and start the server.

Why it’s here:
  - New contributors can read this first to get the site running.
-->


# requirements.txt — project dependencies
# -------------------------------------------------------
# This file lists all Python packages (and pinned versions)
# that your app needs to run.
#
# To update this list after adding/removing a package:
#  1. Activate your virtual environment:
#       source .venv/bin/activate
#  2. Run:
#       pip freeze > requirements.txt
#
# Why we use .venv:
#  - Isolates this project’s packages from other projects/system.
#  - Prevents version conflicts.
#
# In production (on e.g. Render, Heroku), the deploy process
# reads this file and does:
#     pip install -r requirements.txt
# to recreate your environment remotely.




# Paddlingen — Local Development Setup

## 📥 1. Clone the repository

# Replace with your friend’s Git URL if different

```bash
git clone https://github.com/yourusername/paddlingen.git
cd paddlingen
```

## 🐍 2. Create & activate a virtual environment
Why? Keeps project packages isolated from your system Python.

1. Create a .venv folder in the project root
```bash
python3 -m venv .venv
```

2. Activate it on WSL/macOS/Linux:
```bash
source .venv/bin/activate
```

- …or on Windows PowerShell:
```bash
.venv\Scripts\Activate.ps1
```
- You should now see (.venv) in your prompt.

## 📦 3. Install Python dependencies

```bash
pip install -r requirements.txt   # install Flask, SQLAlchemy, etc.
```

- If you add a new library later, update requirements.txt with:
```bash
pip freeze > requirements.txt
```

## 🔑 4. Configure environment variables
1. Create a file called .env in the project root (next to run.py).
2. Copy this template into it:
```bash
# .env — Private settings (never commit!)
SECRET_KEY=your-secret-key
PAYMENT_API_KEY=sk_test_XXXXXXXXXXXXXXXX
FLASK_DEBUG=True
```
#### Make sure *.env* is listed in *.gitignore* so your secrets stay private.

## 🚀 6. Start the Flask server
With the venv active and from the project root, run:

```bash
python run.py
```

- The app will launch at: http://127.0.0.1:5000
- Debug mode is on by default (auto-reloads on code changes).

## 💡 7. Tips & tricks
- Stopping the server: Press Ctrl+C in your terminal.

- Auto-reload templates: No extra setup—Flask’s debug mode reloads HTML/CSS/JS.

- Check logs: Watch your terminal for error messages or 404s.

- Clearing caches: If CSS or JS don’t update, do a hard refresh (Ctrl+F5).

- Database reset: Delete instance/paddlingen.sqlite to start fresh.

- VSCode integration:

## Git workflow:

1. git status to see changes

2. git add . && git commit -m "Your message" to save work

3. git push to upload to GitHub


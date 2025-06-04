<!--

File: README.md

What it does:
  - Gives a quick project overview.
  - Explains how to install dependencies and start the server.

Why it’s here:
  - New contributors can read this first to get the site running.
-->


## requirements.txt — project dependencies
-------------------------------------------------------
This file lists all Python packages (and pinned versions)
that your app needs to run.

To update this list after adding/removing a package:
 1. Activate your virtual environment:
```bash
      source .venv/bin/activate
```
2. Run:
```bash
      pip freeze > requirements.txt
```

 Why we use .venv:
 - Isolates this project’s packages from other projects/system.
 - Prevents version conflicts.

 In production (on e.g. Render, Heroku), the deploy process
reads this file and does:
```bash
    pip install -r requirements.txt
```
 to recreate your environment remotely.




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



## Viewing website on phone via Flask on WSL.
• (WSL) → run in the Ubuntu /bash shell  
• (WIN) → run in Windows PowerShell or Windows CMD  
(when the line also says “Admin”, open PowerShell **as Administrator**)

If a command is entered in the wrong place it simply will not work, so use the labels as your guard-rails.

────────────────────────────────

1. Close anything already using port 5000  
    ────────────────────────────────  
    (WSL) CTRL-C in any existing Flask window  
    (WSL) `sudo fuser -k 5000/tcp` ← optional, makes sure the port is free

────────────────────────────────  
2. Find out which IP your WSL instance received  
────────────────────────────────  
(WSL) `hostname -I` # ← notice: NO “wsl” in front  
Example output: `172.23.115.255`  
Write that number down – we call it WSL_IP from now on.

Tip: If it prints nothing, just carry on to step 3, start Flask once, then run `hostname -I` again; WSL occasionally waits for a socket before it asks DHCP for an address.

────────────────────────────────  
3. Start Flask inside WSL  
────────────────────────────────  
(WSL) `flask run --host=0.0.0.0 --port=5000`

Leave that window open.

────────────────────────────────  
4. Create the Windows → WSL port-forward  
────────────────────────────────  
(WIN – Admin) Open an **administrator** PowerShell (Start menu → type “powershell” → right-click → Run as administrator)

(WIN – Admin)

``1netsh interface portproxy add v4tov4 ` 2   listenaddress=0.0.0.0 listenport=5000 ` 3   connectaddress=WSL_IP connectport=5000``

Replace `WSL_IP` with the number from step 2.  
(If you mistype it, delete with the command shown at the end and add it again.)

You can check the rule with:

(WIN – Admin) `netsh interface portproxy show all`

────────────────────────────────  
5. Allow that port through the Windows firewall  
────────────────────────────────  
You said you already disabled the firewall once; doing it the precise way is safer:

(WIN – Admin)

``1New-NetFirewallRule -DisplayName "Flask-WSL-5000" ` 2    -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow``

────────────────────────────────  
6. Find the Windows LAN address you will give to the phone  
────────────────────────────────  
(WIN) `ipconfig`

Under “Wireless LAN adapter Wi-Fi” read the line  
IPv4 Address . . . : 192.168.10.122 ← example, call it WINDOWS_IP

────────────────────────────────  
7. Test locally first  
────────────────────────────────  
(WIN) Open a browser on the laptop and go to  
`http://WINDOWS_IP:5000`

You must see your Flask app.  
If you do **not** see it:

• Port-forward wrong? `netsh interface portproxy show all`  
• Firewall rule wrong? `Get-NetFirewallRule -DisplayName "Flask-WSL-5000"`  
• Flask not running? look at the WSL window

Fix whatever is wrong, then reload the page until it works on the laptop.

────────────────────────────────  
8. Open the same URL on the phone  
────────────────────────────────  
Make sure the phone is on the **same Wi-Fi** and that any phone-VPN is off.

Browser on the phone → `http://WINDOWS_IP:5000`

You should now see the page.

────────────────────────────────  
Common hiccups table  
────────────────────────────────  
• Using the 172.23.x.x address on the phone – always use the **192.168 / 10.x** address from step 6.  
• WSL got a new IP after a reboot – redo steps 2 and 4 with the fresh WSL_IP.  
• Another program already listens on Windows:5000 – pick a free port everywhere, e.g. 8000 (change steps 3-5 accordingly).  
• Corporate security/VPN – some suites still block LAN even with the firewall rule; pause them briefly to test.

────────────────────────────────  
When you are done testing  
────────────────────────────────  
(WIN – Admin)

`1netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=5000 2Remove-NetFirewallRule -DisplayName "Flask-WSL-5000"`

That returns the machine to its previous state.

Follow the labels—WSL commands in the Ubuntu shell, Windows commands in PowerShell—and the Flask site will appear on your phone.

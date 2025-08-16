# Paddlingen

A small Flask application for managing canoe rentals. The app lets visitors book canoes and provides a simple admin interface to review and edit bookings.

## Prerequisites

- Python 3.10 or newer
- `git` for cloning the repository

## Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/paddlingen.git
   cd paddlingen
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   On Windows use `.venv\Scripts\activate` instead.

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root and add your secrets:

   ```
   SECRET_KEY=replace-me
   PAYMENT_API_KEY=replace-me
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=changeme
   FLASK_DEBUG=True
   SESSION_COOKIE_SECURE=False
   # Optional: use PostgreSQL instead of the default SQLite database
   # DATABASE_URL=postgresql+psycopg://paddlingen:password@localhost:5432/paddlingen
   ```

   `DATABASE_URL` controls which database is used. Leave it unset to store data in `instance/paddlingen.db` (SQLite). To develop against a local PostgreSQL server, set it to a connection string like the example above.

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Start the development server**
   ```bash
   flask --app wsgi --debug run
   ```
   The application will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

7. **Run tests**
   ```bash
   pytest
   ```

## Database migrations

Paddlingen uses [Alembic](https://alembic.sqlalchemy.org/) to keep the database schema in sync with your models.

1. **Create a migration** – whenever you change a model, ask Alembic to generate a migration script:
   ```bash
   alembic revision --autogenerate -m "describe your change"
   ```
   The command inspects the `db` models and stores a new migration file in `migrations/versions`.

2. **Apply migrations** – run pending migrations to update the database to the latest schema:
   ```bash
   alembic upgrade head
   ```

3. **Roll back** – undo the last migration if something went wrong:
   ```bash
   alembic downgrade -1
   ```
   Replace `-1` with a specific revision identifier to roll back to an exact point in history.

For more background see the [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Deployment (Production)

In production set configuration values directly with your hosting provider instead of using a `.env` file. Typical values are:

```
SECRET_KEY=generate-a-long-random-value
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
DATABASE_URL=postgresql+psycopg://user:password@dbhost:5432/paddlingen
```

For PythonAnywhere the `DATABASE_URL` looks like:

```
postgresql+psycopg://yourusername:password@yourusername-123.postgres.pythonanywhere-services.com/yourusername$paddlingen
```

### Running migrations during deployment

After deploying new code, make sure the production database schema is up to date:

```bash
alembic upgrade head
```

Run this command on the server each time you deploy changes that modify the database models.

### Deploying to PythonAnywhere

PythonAnywhere offers a beginner‑friendly free tier that is perfect for hosting this project. The basic steps are:

1. **Upload your code** using the PythonAnywhere dashboard or by cloning the repository with `git`.

2. **Create a virtual environment** in the *Consoles* tab and install the dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create the database.** In the *Databases* tab create a new PostgreSQL database. Copy the connection string that PythonAnywhere displays and save it for the `DATABASE_URL` environment variable.  
   ![Creating the database on PythonAnywhere](docs/pythonanywhere-create-db.svg)

4. **Initialize the database and run migrations** in a Bash console:
   ```bash
   python init_db.py
   alembic upgrade head
   ```

5. **Configure the WSGI file.** On the *Web* tab click the link to the WSGI configuration file. Ensure it adds your project to the path and imports the Flask application from `wsgi.py`:  
   ```python
   import sys
   sys.path.insert(0, '/home/yourusername/path-to-project')

   from wsgi import application
   ```
   ![WSGI configuration on PythonAnywhere](docs/pythonanywhere-wsgi.svg)

6. **Set environment variables** such as `SECRET_KEY`, `DATABASE_URL`, `FLASK_DEBUG`, and `SESSION_COOKIE_SECURE` in the *Web* tab under "Environment Variables":  
   ![Setting environment variables on PythonAnywhere](docs/pythonanywhere-env-vars.svg)

7. **Reload the web app** from the dashboard. PythonAnywhere serves your site over HTTPS, so keep `SESSION_COOKIE_SECURE=True` in your environment to protect sessions.

# Development Notes

# Viewing website on phone via Flask on WSL.
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

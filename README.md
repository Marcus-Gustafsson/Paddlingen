# Paddlingen

A small Flask application for managing canoe rentals. The app lets visitors book canoes and provides a simple admin interface to review and edit bookings.

## Prerequisites

- Python 3.10 or newer
- `git` for cloning the repository

## Setup

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
   On Windows use `.venv\Scripts\activate` instead of the last command above.

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root and add your secrets:
   ```bash
   SECRET_KEY=replace-me
   PAYMENT_API_KEY=replace-me
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=changeme
   FLASK_DEBUG=True
   ```
   The `.env` file is ignored by Git.

5. **Initialize the database**
   Run the helper script once to create `instance/paddlingen.db` and seed the administrator account specified above:
   ```bash
   python init_db.py
   ```

6. **Start the development server**
   ```bash
   python main.py
   ```
   The application will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

7. **Run tests (optional)**
   ```bash
   pytest -q
   ```

Log in to `/login` with the credentials from your `.env` file to access the admin dashboard.

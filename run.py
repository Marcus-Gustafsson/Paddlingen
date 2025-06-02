"""
File: run.py

What it does:
  - The “entry point” of your app.
  - When you run “python run.py”, this file creates and starts the server.

Why it’s here:
  - It lives at the project root so it’s easy to find and run.

"""


"""
The ‘entry point’ to start your site.
Run with: python run.py
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)   # Starts Flask on http://127.0.0.1:5000


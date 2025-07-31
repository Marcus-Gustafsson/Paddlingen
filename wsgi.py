"""A tiny WSGI wrapper so hosting services can launch the app.

This file exposes a module-level variable named ``application`` that
WSGI servers like Gunicorn, uWSGI, or platforms such as PythonAnywhere
look for by default.  By importing the Flask ``app`` object from
``main.py`` and assigning it to ``application`` we give these servers
what they expect without requiring any special configuration.
"""

from main import app

# Many WSGI servers expect the variable name ``application``.  We simply
# re-export our Flask ``app`` under that name so ``gunicorn wsgi:application``
# just works.
application = app


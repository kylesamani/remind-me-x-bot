"""WSGI entry point for Gunicorn."""

# Python 3.13 compatibility: imghdr was removed, provide a shim
import sys
import imghdr_shim
sys.modules['imghdr'] = imghdr_shim

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()


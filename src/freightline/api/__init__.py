"""HTTP API.

Importing this package requires the ``api`` extra (``pip install -e ".[api]"``).
The domain packages never import from here.
"""

from .app import create_app

__all__ = ["create_app"]

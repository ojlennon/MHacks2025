"""My FastAPI Application Package."""

__version__ = "0.1.0"
__author__ = "Coppas Team"

# Optionally expose main components at package level
from .main import app

import coppa.model

__all__ = ["app"]
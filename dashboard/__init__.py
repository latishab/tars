"""TARS Dashboard - Web interface for robot control."""

from .backend.server import app, get_app

__all__ = ["app", "get_app"]

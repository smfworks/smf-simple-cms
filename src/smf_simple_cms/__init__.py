"""SMF Simple CMS - Lightweight CRM for small businesses."""

__version__ = "0.1.0"
__author__ = "SMF Works"

from .database import Database
from .models import Lead, Contact, Note, Task
from .app import create_app

__all__ = ['Database', 'Lead', 'Contact', 'Note', 'Task', 'create_app']
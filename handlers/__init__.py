"""Handlers module - exports all routers for bot registration.

Routers:
- user_router: User-facing handlers (/start, events, registrations, settings)
- admin_router: Admin handlers (/admin, event management)
"""

from handlers.admin import router as admin_router
from handlers.user import router as user_router

__all__ = ["user_router", "admin_router"]

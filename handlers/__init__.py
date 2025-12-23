"""Handlers module - exports all routers for bot registration.

Routers:
- user_router: User-facing handlers (/start, events, registrations, settings)
"""

from handlers.user import router as user_router

__all__ = ["user_router"]

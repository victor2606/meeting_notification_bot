"""Scheduler module for background reminder tasks.

Exports:
- setup_scheduler: Initialize and start APScheduler (line 6 in reminders.py)
- shutdown_scheduler: Graceful shutdown (line 25 in reminders.py)
"""

from scheduler.reminders import setup_scheduler, shutdown_scheduler

__all__ = ["setup_scheduler", "shutdown_scheduler"]

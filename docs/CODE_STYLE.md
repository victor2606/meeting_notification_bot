# Code Style Guide

## Overview

| Aspect | Standard |
|--------|----------|
| Language | Python 3.11+ |
| Type Hints | Required |
| Docstrings | Required for modules/functions |
| Line Length | 100 characters |
| Formatter | ruff |
| Linter | ruff |

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `queries.py`, `inline.py` |
| Functions | snake_case | `get_user`, `create_event` |
| Variables | snake_case | `event_id`, `user_data` |
| Constants | SCREAMING_SNAKE_CASE | `BOT_TOKEN`, `DATABASE_URL` |
| Classes | PascalCase | `EventCallback`, `SettingsCallback` |
| Type Aliases | PascalCase | `UserDict`, `EventList` |
| Private | Leading underscore | `_pool`, `_cache` |
| SQL Constants | SCREAMING_SNAKE_CASE | `INIT_TABLES_SQL` |

## Import Organization

Order imports in three groups separated by blank lines:

```python
# 1. Standard library
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Any

# 2. Third-party packages
import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

# 3. Local modules
from config import BOT_TOKEN, DATABASE_URL
from database.models import INIT_TABLES_SQL
```

### Import Rules

| Rule | Correct | Incorrect |
|------|---------|-----------|
| Specific imports | `from typing import Optional` | `from typing import *` |
| Group related | `from aiogram.types import Message, CallbackQuery` | Multiple lines for same module |
| Alphabetical within groups | `import asyncio` before `import logging` | Random order |

## Type Hints

### Required Annotations

```python
# Function parameters and return types
async def get_user(telegram_id: int) -> Optional[dict]:
    ...

# Variables with non-obvious types
_pool: Optional[asyncpg.Pool] = None

# Class attributes
class EventCallback(CallbackData, prefix="event"):
    action: str
    event_id: int | None = None
```

### Type Hint Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| `Optional[T]` | Nullable values | `Optional[str] = None` |
| `T \| None` | Python 3.10+ nullable | `int \| None = None` |
| `list[T]` | Typed lists | `list[dict]` |
| `dict[K, V]` | Typed dicts | `dict[str, Any]` |
| Return `None` | Void functions | `-> None` |
| Return `Optional` | May return None | `-> Optional[dict]` |

### Generic Container Types

```python
# Use lowercase built-in generics (Python 3.9+)
def get_events() -> list[dict]:  # Not List[dict]
    ...

def get_user_data() -> dict[str, Any]:  # Not Dict[str, Any]
    ...
```

## Docstrings

### Module Docstrings

```python
"""Database queries and CRUD operations."""
```

### Function Docstrings

```python
async def create_user(
    telegram_id: int,
    first_name: str,
    username: Optional[str] = None
) -> dict:
    """Create a new user or return existing one."""
    ...
```

### Docstring Rules

| Rule | Description |
|------|-------------|
| First line | Brief description ending with period |
| Imperative mood | "Create user" not "Creates user" |
| No redundancy | Don't repeat type hints in docstring |
| When to add params | Only if behavior non-obvious from types |

## Function Signatures

### Parameter Ordering

```python
async def create_event(
    # 1. Required positional parameters
    title: str,
    category: str,
    format: str,
    event_datetime: datetime,
    location: str,
    organizer_contact: str,
    # 2. Optional parameters with defaults
    description: Optional[str] = None
) -> dict:
```

### Multi-line Formatting

```python
# Parameters on separate lines when > 2 or line too long
async def update_user_notifications(
    telegram_id: int,
    notify_it: Optional[bool] = None,
    notify_sport: Optional[bool] = None,
    notify_books: Optional[bool] = None
) -> Optional[dict]:
```

## Async Patterns

### Database Connection Pattern

```python
# Global pool with lazy initialization
_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool
```

### Context Manager for Connections

```python
async def get_user(telegram_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            telegram_id
        )
        return dict(row) if row else None
```

### Async Function Rules

| Rule | Description |
|------|-------------|
| Naming | No `async_` prefix, same as sync |
| Return | Always use `return`, never implicit None for Optional |
| Context managers | Use `async with` for connections |
| Awaiting | Always await coroutines immediately |

## SQL Style

### Query Formatting

```python
# Multi-line SQL in triple quotes
row = await conn.fetchrow(
    """
    SELECT * FROM events
    WHERE event_datetime > NOW()
        AND is_cancelled = FALSE
        AND category = $1
    ORDER BY event_datetime ASC
    LIMIT $2
    """,
    category, limit
)
```

### SQL Rules

| Rule | Example |
|------|---------|
| Keywords uppercase | `SELECT`, `WHERE`, `INSERT` |
| Identifiers lowercase | `users`, `telegram_id` |
| Parameterized queries | `$1`, `$2` (never f-strings) |
| Indentation | 4 spaces for continuation |
| Trailing comma | After last parameter |

### Schema Definitions

```python
INIT_TABLES_SQL = """
-- Table comment
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index comment
CREATE INDEX IF NOT EXISTS idx_name ON table(column);
"""
```

## Class Definitions

### CallbackData Classes

```python
class EventCallback(CallbackData, prefix="event"):
    """Callback data for event actions."""
    action: str  # Inline comment for field
    event_id: int | None = None
```

### Class Rules

| Rule | Description |
|------|-------------|
| Docstring | Required, describes purpose |
| Field comments | Inline, list valid values |
| Defaults | At end of field list |
| Prefix | Lowercase, short identifier |

## Keyboard Builders

### Function Pattern

```python
def event_list_kb(events: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    """Create keyboard with event list buttons."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"📌 {event['title']}",
                callback_data=EventCallback(action="detail", event_id=event["id"]).pack()
            )
        ]
        for event in events
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

### Keyboard Rules

| Rule | Description |
|------|-------------|
| Return type | Always `InlineKeyboardMarkup` or `ReplyKeyboardMarkup` |
| Naming | `*_kb` suffix |
| Button text | Emoji prefix for visual distinction |
| List comprehension | For dynamic button lists |

## Module Exports

### __init__.py Pattern

```python
"""Module description."""

from module.submodule import (
    # Group 1: Category name
    function_a,
    function_b,
    # Group 2: Another category
    function_c,
)

__all__ = [
    # Group 1
    "function_a",
    "function_b",
    # Group 2
    "function_c",
]
```

### Export Rules

| Rule | Description |
|------|-------------|
| Explicit imports | List all public symbols |
| `__all__` | Must match imports |
| Comments | Group related exports |
| Order | Match import order |

## Code Sections

### Section Separators

```python
# ============== User Functions ==============

async def create_user(...):
    ...

async def get_user(...):
    ...


# ============== Event Functions ==============

async def create_event(...):
    ...
```

### Section Rules

| Rule | Description |
|------|-------------|
| Format | `# ============== Name ==============` |
| Spacing | Blank line before and after |
| When to use | 3+ related functions |
| Naming | PascalCase, plural |

## Error Handling

### Fail Fast Pattern

```python
# Config validation - fail immediately
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")
```

### Database Error Pattern

```python
# Let database errors propagate - no silent failures
async def get_user(telegram_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(...)
        return dict(row) if row else None  # None is valid, errors propagate
```

### Error Rules

| Rule | Description |
|------|-------------|
| No empty catch | Never `except: pass` |
| Specific exceptions | Catch only expected types |
| Fail fast | Validate early, raise immediately |
| No default fallbacks | Missing required data = error |

## Logging

### Setup Pattern

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
```

### Usage

```python
logger.info("Starting bot...")
logger.error("Failed to process: %s", error_message)
```

## Configuration

### Environment Loading

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Required - fail if missing
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

# Optional - empty default
ADMIN_IDS: list[int] = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip()
]
```

## File Organization

### Standard Module Structure

```python
"""Module docstring."""

# Imports (3 groups)
import stdlib
import thirdparty
from local import module

# Constants
CONSTANT_VALUE = "value"

# Global state (if needed)
_private_state: Optional[Type] = None


# ============== Section 1 ==============

def public_function() -> ReturnType:
    """Docstring."""
    ...


# ============== Section 2 ==============

def another_function() -> ReturnType:
    """Docstring."""
    ...
```

## Quick Reference

### Do

- Type hint all function signatures
- Use `async with` for database connections
- Parameterize all SQL queries
- Export explicitly in `__init__.py`
- Fail fast on invalid input
- Use section separators for large files

### Don't

- Use `from module import *`
- Catch generic `Exception`
- Use f-strings in SQL
- Return `dict()` on error (return `None` or raise)
- Mix sync and async in same module
- Use global state without getters

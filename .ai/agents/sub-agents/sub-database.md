# Sub-Agent: Database

**ID:** `sub-database`
**Parent:** `agent-3-execution`

---

## Purpose

SQLite database operations.

---

## Pattern

```python
import sqlite3
from pathlib import Path

DB_PATH = Path("data/vdo_content.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def save_project(project: dict):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (title, content) VALUES (?, ?)",
            (project['title'], project['content'])
        )
        conn.commit()
```

---

**Status:** Active

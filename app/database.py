import sqlite3
from pathlib import Path
from app.paths import db_path as _db_path


def get_connection():
    p = _db_path()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        # Persistent task definitions (created once)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                client_name TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                assigned_by TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                timer_status TEXT DEFAULT 'inactive',
                eod_status TEXT DEFAULT 'In Progress',
                start_time TEXT,
                end_time TEXT,
                duration TEXT,
                what_done TEXT DEFAULT '',
                last_session_date TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Bookmark tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmark_clients (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                is_pinned  INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmark_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id  INTEGER NOT NULL,
                data_name  TEXT NOT NULL,
                data_type  TEXT NOT NULL DEFAULT 'Link',
                content    TEXT NOT NULL DEFAULT '',
                is_pinned  INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES bookmark_clients(id) ON DELETE CASCADE
            )
        """)
        conn.execute("PRAGMA foreign_keys = ON")

        # Migrate existing schema
        _migrate(conn)

        # All modules off by default for new installs
        defaults = {
            'gorilla_enabled':          'false',
            'gorilla_interval_type':    'fixed',
            'gorilla_interval_seconds': '120',
            'gorilla_random_min':       '120',
            'gorilla_random_max':       '300',
            'gorilla_message':          'What are you doing?',
            'bookmarks_enabled':        'false',
            'theme':                    'dark',
        }
        for key, value in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        conn.commit()


def _migrate(conn):
    """Add new columns to existing databases without breaking them."""
    existing = {
        row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }
    migrations = [
        ("is_active",          "ALTER TABLE tasks ADD COLUMN is_active INTEGER DEFAULT 1"),
        ("last_session_date",  "ALTER TABLE tasks ADD COLUMN last_session_date TEXT"),
    ]
    for col, sql in migrations:
        if col not in existing:
            conn.execute(sql)

    # Migrate old 'date' column rows: set last_session_date from date if present
    if 'date' in existing and 'last_session_date' in {
        row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }:
        conn.execute(
            "UPDATE tasks SET last_session_date = date WHERE last_session_date IS NULL AND date IS NOT NULL"
        )
    conn.commit()


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key, default=None):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row['value'] if row else default


def set_setting(key, value):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )
        conn.commit()


# ── Task queries ───────────────────────────────────────────────────────────────

def get_active_tasks():
    """Tasks shown in the timer list (active only)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE is_active = 1 ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_tasks():
    """All tasks — used in Manage mode."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY is_active DESC, id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_task(task_name, client_name, assigned_to, assigned_by):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO tasks (task_name, client_name, assigned_to, assigned_by, is_active)
               VALUES (?, ?, ?, ?, 1)""",
            (task_name, client_name, assigned_to, assigned_by)
        )
        conn.commit()


def update_task(task_id, **kwargs):
    if not kwargs:
        return
    sets   = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [task_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {sets} WHERE id = ?", values)
        conn.commit()


def delete_task(task_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()


def toggle_active(task_id, currently_active):
    new_val = 0 if currently_active else 1
    update_task(task_id, is_active=new_val)


def reset_timers():
    """Clear all timer data — call at start of a fresh day."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE tasks SET
                timer_status = 'inactive',
                eod_status   = 'In Progress',
                start_time   = NULL,
                end_time     = NULL,
                duration     = NULL,
                what_done    = '',
                last_session_date = NULL
            WHERE is_active = 1
        """)
        conn.commit()


def get_tasks_for_export():
    """Active tasks that have been worked on today."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT task_name, eod_status, client_name, start_time, end_time,
                   duration, assigned_to, assigned_by, what_done
            FROM tasks
            WHERE is_active = 1
              AND last_session_date = date('now')
              AND start_time IS NOT NULL
            ORDER BY id ASC
        """).fetchall()
        return [dict(r) for r in rows]


def get_running_task():
    """Return the single currently running task, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE timer_status = 'running' AND is_active = 1 LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_unfinished_tasks_today():
    """Tasks started today that are not yet finished — used in gorilla dropdown."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, task_name, timer_status
            FROM tasks
            WHERE is_active = 1
              AND last_session_date = date('now')
              AND start_time IS NOT NULL
              AND timer_status != 'finished'
            ORDER BY id ASC
        """).fetchall()
        return [dict(r) for r in rows]


# ── Bookmark clients ───────────────────────────────────────────────────────────

def get_bookmark_clients():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM bookmark_clients
            ORDER BY is_pinned DESC, sort_order ASC, id ASC
        """).fetchall()
        return [dict(r) for r in rows]


def add_bookmark_client(name):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO bookmark_clients (name) VALUES (?)", (name,)
        )
        conn.commit()


def update_bookmark_client(client_id, **kwargs):
    if not kwargs:
        return
    sets   = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [client_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE bookmark_clients SET {sets} WHERE id = ?", values)
        conn.commit()


def delete_bookmark_client(client_id):
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM bookmark_clients WHERE id = ?", (client_id,))
        conn.execute("DELETE FROM bookmark_items WHERE client_id = ?", (client_id,))
        conn.commit()


# ── Bookmark items ─────────────────────────────────────────────────────────────

def get_bookmark_items(client_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM bookmark_items WHERE client_id = ?
            ORDER BY is_pinned DESC, sort_order ASC, id ASC
        """, (client_id,)).fetchall()
        return [dict(r) for r in rows]


def add_bookmark_item(client_id, data_name, data_type, content):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO bookmark_items (client_id, data_name, data_type, content)
               VALUES (?, ?, ?, ?)""",
            (client_id, data_name, data_type, content)
        )
        conn.commit()


def update_bookmark_item(item_id, **kwargs):
    if not kwargs:
        return
    sets   = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [item_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE bookmark_items SET {sets} WHERE id = ?", values)
        conn.commit()


def delete_bookmark_item(item_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM bookmark_items WHERE id = ?", (item_id,))
        conn.commit()

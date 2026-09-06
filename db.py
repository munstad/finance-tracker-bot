"""
db.py — вся работа с базой данных (SQLite).

Храним одну таблицу expenses:
    id        — уникальный номер записи
    user_id   — telegram id пользователя (бот может обслуживать нескольких людей)
    amount    — сумма траты
    category  — категория (еда, транспорт, и т.д.)
    raw_text  — исходное сообщение (на всякий случай, для отладки)
    created_at — дата и время добавления записи
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "expenses.db"


def get_connection():
    """Открывает соединение с базой. Создаёт файл, если его ещё нет."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # чтобы обращаться к колонкам по имени
    return conn


def init_db():
    """Создаёт таблицу, если она ещё не существует. Вызывается один раз при старте бота."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            raw_text TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_expense(user_id: int, amount: float, category: str, raw_text: str):
    """Добавляет одну трату в базу."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, raw_text, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, raw_text, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_expenses(user_id: int, days: int = 30):
    """
    Возвращает все траты пользователя за последние `days` дней.
    Результат — список словарей (удобно передавать в pandas.DataFrame).
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT amount, category, created_at
        FROM expenses
        WHERE user_id = ?
          AND datetime(created_at) >= datetime('now', ?)
        ORDER BY created_at
        """,
        (user_id, f"-{days} days"),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_last_expense(user_id: int):
    """Удаляет последнюю добавленную трату пользователя (команда /undo)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, amount, category FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None:
        conn.close()
        return None
    conn.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return dict(row)

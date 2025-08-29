"""Simple SQLite database for saving items and printer settings."""
import sqlite3
import json
import os
from typing import List, Dict, Optional


class LabelDatabase:
    def __init__(self, db_path: str = "data/labels.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_number TEXT NOT NULL,
                    upc TEXT,
                    title TEXT,
                    casepack TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS printer_settings (
                    id INTEGER PRIMARY KEY,
                    printer_name TEXT,
                    language TEXT,
                    size TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_item(self, item_number: str, upc: str = "", title: str = "", casepack: str = "") -> bool:
        """Save an item to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO saved_items (item_number, upc, title, casepack)
                    VALUES (?, ?, ?, ?)
                """, (item_number, upc, title, casepack))
                conn.commit()
            return True
        except Exception:
            return False

    def get_saved_items(self) -> List[Dict]:
        """Get all saved items."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT item_number, upc, title, casepack, created_at
                    FROM saved_items
                    ORDER BY created_at DESC
                """)
                return [
                    {
                        "item_number": row[0],
                        "upc": row[1] or "",
                        "title": row[2] or "",
                        "casepack": row[3] or "",
                        "created_at": row[4]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception:
            return []

    def delete_item(self, item_number: str) -> bool:
        """Delete an item from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM saved_items WHERE item_number = ?", (item_number,))
                conn.commit()
            return True
        except Exception:
            return False

    def save_printer_settings(self, printer_name: str, language: str, size: str) -> bool:
        """Save printer settings."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO printer_settings (id, printer_name, language, size, updated_at)
                    VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (printer_name, language, size))
                conn.commit()
            return True
        except Exception:
            return False

    def get_printer_settings(self) -> Optional[Dict]:
        """Get saved printer settings."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT printer_name, language, size
                    FROM printer_settings
                    WHERE id = 1
                """)
                row = cursor.fetchone()
                if row:
                    return {
                        "printer_name": row[0],
                        "language": row[1],
                        "size": row[2]
                    }
        except Exception:
            pass
        return None

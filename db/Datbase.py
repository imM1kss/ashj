import sqlite3
from typing import List, Tuple, Optional

class Database:
    def __init__(self, path: str = "data.db"):
        self.path = path
        self._init_db()
    
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                telegram_id INTEGER UNIQUE,
                vk_id INTEGER UNIQUE
            );
            
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                full_name TEXT NOT NULL,
                telegram_id INTEGER UNIQUE,
                vk_id INTEGER UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('user','admin')),
                               
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                UNIQUE(full_name, group_id)
            );
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                group_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 2),
                
                UNIQUE (group_id, name, year, semester),
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                lesson_num INTEGER NOT NULL,
                classroom TEXT NOT  NULL,
                               
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                               
                UNIQUE(group_id, lesson_num)
            );
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
                grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 5),
                               
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                description TEXT,
                attachments TEXT,
                lessons_left INTEGER NOT NULL DEFAULT 1 CHECK(lessons_left >= 0)
                               
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );
            """)

            def ensure_user(self,
                            full_name: str,
                            role: str,
                            telegram_id: Optional[int] = None,
                            vk_id: Optional[int] = None,
                            group_id: Optional[int] = None,
                            ) -> int:
                if not telegram_id and not vk_id:
                    raise ValueError("Нужно хотя-бы ВК или ТГ")
                
                with self._connect() as conn:
                    cur = conn.cursor()

                    cur.execute("""
                        SELECT id, telegram_id, vk_id FROM users
                        WHERE telegram_id = ? OR vk_id = ? OR group_id = ?
                    """, (telegram_id, vk_id, group_id))
                    row = cur.fetchone()

                    if row:
                        user_id = row["id"]

                        if telegram_id and not row["telegram_id"]:
                            cur.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, user_id))
                        elif vk_id and not row["vk_id"]:
                            cur.execute("UPDATE users SET vk_id = ? WHERE id = ?", (vk_id, user_id))
                        elif group_id and not row["group_id"]:
                            cur.execute("UPDATE users SET group_id = ? WHERE id = ?", (group_id, user_id))
                        
                        else:
                            cur.execute("""
                                INSERT INTO users (telegram_id, vk_id, group_id, full_name. role) VALUES (?,?,?,?,?),
                            """, (telegram_id, vk_id, group_id, full_name, role))
                        return user_id

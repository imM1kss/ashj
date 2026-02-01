import sqlite3
from typing import List, Tuple, Optional


class Database:
    def __init__(self, path: str = "diary.db"):
        self.path = path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                vk_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 5),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            );
            """)

    # ---------- USERS ----------

    def ensure_user(
        self,
        telegram_id: Optional[int] = None,
        vk_id: Optional[int] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> int:
        """Создает пользователя или обновляет существующий профиль с новым ID"""
        if not telegram_id and not vk_id:
            raise ValueError("Нужен хотя бы telegram_id или vk_id")

        with self._connect() as conn:
            cur = conn.cursor()

            # 1. Найти существующего пользователя по любому ID
            cur.execute("""
                SELECT id, telegram_id, vk_id FROM users
                WHERE telegram_id = ? OR vk_id = ?
            """, (telegram_id, vk_id))
            row = cur.fetchone()

            if row:
                user_id = row["id"]
                # Обновляем отсутствующий ID, если он ещё пуст
                if telegram_id and not row["telegram_id"]:
                    cur.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, user_id))
                if vk_id and not row["vk_id"]:
                    cur.execute("UPDATE users SET vk_id = ? WHERE id = ?", (vk_id, user_id))
            else:
                # Создаем новый профиль
                cur.execute("""
                    INSERT INTO users (telegram_id, vk_id, username, first_name)
                    VALUES (?, ?, ?, ?)
                """, (telegram_id, vk_id, username, first_name))
                user_id = cur.lastrowid

            return user_id

    def get_user_id(
        self,
        telegram_id: Optional[int] = None,
        vk_id: Optional[int] = None
    ) -> int:
        if not telegram_id and not vk_id:
            raise ValueError("Нужен хотя бы telegram_id или vk_id")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM users
                WHERE telegram_id = ? OR vk_id = ?
            """, (telegram_id, vk_id))
            row = cur.fetchone()
            if not row:
                raise ValueError("User not found")
            return row["id"]

    # ---------- SUBJECTS ----------

    def ensure_subject(self, name: str) -> int:
        with self._connect() as conn:
            conn.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (name,))
            cur = conn.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            return cur.fetchone()["id"]

    def get_subjects(self) -> List[Tuple[int, str]]:
        with self._connect() as conn:
            cur = conn.execute("SELECT id, name FROM subjects ORDER BY name")
            return [(row["id"], row["name"]) for row in cur.fetchall()]

    def delete_subject(self, id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM subjects WHERE id = ?", (id,))
            return cur.rowcount > 0  # True если что-то удалилось

    # ---------- GRADES ----------

    def add_grade(
        self,
        telegram_id: Optional[int] = None,
        vk_id: Optional[int] = None,
        subject: str = "",
        grade: int = 0
    ) -> None:
        if not 1 <= grade <= 5:
            raise ValueError("Grade must be between 1 и 5")

        user_id = self.get_user_id(telegram_id=telegram_id, vk_id=vk_id)
        subject_id = self.ensure_subject(subject)

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO grades (user_id, subject_id, grade)
                VALUES (?, ?, ?)
            """, (user_id, subject_id, grade))

    def get_user_grades(
        self,
        telegram_id: Optional[int] = None,
        vk_id: Optional[int] = None
    ) -> List[Tuple[str, int, str]]:
        user_id = self.get_user_id(telegram_id=telegram_id, vk_id=vk_id)
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT s.name, g.grade, g.created_at
                FROM grades g
                JOIN subjects s ON s.id = g.subject_id
                WHERE g.user_id = ?
                ORDER BY g.created_at DESC
            """, (user_id,))
            return [(row["name"], row["grade"], row["created_at"]) for row in cur.fetchall()]

    def get_average_grade(
        self,
        telegram_id: Optional[int] = None,
        vk_id: Optional[int] = None
    ) -> Optional[float]:
        user_id = self.get_user_id(telegram_id=telegram_id, vk_id=vk_id)
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT AVG(grade) AS avg_grade
                FROM grades
                WHERE user_id = ?
            """, (user_id,))
            result = cur.fetchone()["avg_grade"]
            return round(result, 2) if result is not None else None

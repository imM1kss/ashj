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
            
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                full_name TEXT NOT NULL,
                telegram_id INTEGER UNIQUE,
                vk_id INTEGER UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('user','admin')),
                               
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
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
                date TEXT NOT NULL,
                               
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                               
                UNIQUE(group_id, lesson_num, date)
            );
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                schedule_id INTEGER NOT NULL,
                grade INTEGER NOT NULL CHECK (grade BETWEEN 1 AND 5),
                               
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (schedule_id) REFERENCES schedule(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                description TEXT,
                attachments TEXT,
                lessons_left INTEGER NOT NULL DEFAULT 1 CHECK(lessons_left >= 0),
                               
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );
            """)

    #--------------------------------------USERS---------------------------------
    def ensure_user(self,
                    full_name: str,
                    role: str,
                    telegram_id: Optional[int] = None,
                    vk_id: Optional[int] = None,
                    group_id: Optional[int] = None,
                    ) -> int:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ")
        
        if role not in ("user", "admin"):
            raise ValueError("Неверная роль")
        
        if full_name is None:
            raise ValueError("full_name is None")
        if role is None:
            raise ValueError("role is None")
        
        with self._connect() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT id, telegram_id, vk_id, group_id FROM users
                WHERE telegram_id = ? OR vk_id = ?
            """, (telegram_id, vk_id))
            row = cur.fetchone()

            if row:
                user_id = row["id"]

                if telegram_id and not row["telegram_id"]:
                    cur.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, user_id))
                if vk_id and not row["vk_id"]:
                    cur.execute("UPDATE users SET vk_id = ? WHERE id = ?", (vk_id, user_id))
                if group_id is not None and not row["group_id"] is None:
                    cur.execute("UPDATE users SET group_id = ? WHERE id = ?", (group_id, user_id))
                
            else:
                cur.execute("""
                    INSERT INTO users (telegram_id, vk_id, group_id, full_name, role) VALUES (?,?,?,?,?)
                """, (telegram_id, vk_id, group_id, full_name, role))
                user_id = cur.lastrowid
            return user_id
    
    def get_user_id(self,
                    telegram_id: Optional[int] = None,
                    vk_id: Optional[int] = None,
                    ) -> int:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM users
                WHERE telegram_id = ? OR vk_id = ?
                """, (telegram_id, vk_id))
            row = cur.fetchone()
            if not row:
                raise ValueError("Пользователь не найден")
            return row["id"]
    
    def delete_user(self, user_id:int):
        if user_id is None:
            raise ValueError("user_id is None")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    def is_admin(self,
                telegram_id:Optional[int] = None,
                vk_id:Optional[int] = None,
                user_id: Optional[int] = None):
        if telegram_id is None and vk_id is None and user_id is None:
            raise ValueError("Укажите хотя-бы какое-то id")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT role FROM users WHERE telegram_id = ? OR vk_id = ? OR user_id = ?",
                        (telegram_id, vk_id, user_id))
            row = cur.fetchone()
            if row:
                if row['role'] == "admin":
                    return True
                else: 
                    return False

    
    #------------------------------GROUPS----------------------------------
    def ensure_group(self,
                     name: str,
                     telegram_id: Optional[int] = None,
                     vk_id: Optional[int] = None
                     ) -> int:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id,telegram_id,vk_id FROM groups
                WHERE telegram_id = ? OR vk_id = ?
            """, (telegram_id, vk_id))
            row = cur.fetchone()

            if row:
                group_id = row["id"]

                if telegram_id and not row["telegram_id"]:
                    cur.execute("UPDATE groups SET telegram_id = ? WHERE id = ?", (telegram_id, group_id))
                elif vk_id and not row["vk_id"]:
                    cur.execute("UPDATE groups SET vk_id = ? WHERE id = ?", (vk_id, group_id))
            else:
                cur.execute("""
                    INSERT INTO groups (name, telegram_id, vk_id)
                    VALUES (?,?,?)
                """, (name, telegram_id, vk_id))
                group_id = cur.lastrowid
            return group_id
    
    def get_group_id(self, telegram_id: Optional[int] = None, vk_id: Optional[int] = None) -> int:

        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM groups
                WHERE telegram_id = ? OR vk_id = ?
                """, (telegram_id, vk_id))
            row = cur.fetchone()
            if not row:
                raise ValueError("Группа не найдена")
            return row["id"]
    
    def get_group_names(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM groups ORDER BY name")
            return [row["name"] for row in cur.fetchall()]
    
    #------------------------------SUBJECTS--------------------------------
    def ensure_subject(self,
                       name: str,
                       group_id:int,
                       year:int,
                       semester: int) -> int:
        if name is None:
            raise ValueError("Name not specified")
        if group_id is None:
            raise ValueError("Group not specified")
        if year is None:
            raise ValueError("Year not specified")
        if semester is None:
            raise ValueError("Semester not specified")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM subjects WHERE group_id = ? AND name = ? AND year = ? AND semester = ?", (group_id,name,year,semester))
            row = cur.fetchone()

            if row:
                return row["id"]
            else:
                cur.execute("INSERT INTO subjects (name,group_id,year,semester) VALUES (?,?,?,?)", (name, group_id, year, semester))
                return cur.lastrowid
    
    def get_subjects(self, group_id:int):
        if group_id is None:
            raise ValueError("Group not specified")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id,name FROM subjects WHERE group_id = ?", (group_id,))
            return [(row["id"],row["name"]) for row in cur.fetchall()]
    
    def delete_subject(self, id_sub: int) -> bool:
        if id_sub is None:
            raise ValueError("Укажите хотя-бы что-то (id or name)")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM subjects WHERE id = ?", (id_sub,))
            return cur.rowcount > 0
    
    def get_subject_id(self, group_id: int, name: str) -> int:
        if group_id is None or name is None:
            raise ValueError("group or name not specified")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM subjects WHERE group_id = ? AND name = ?",(group_id,name))
            row = cur.fetchone()
            if row:
                return row["id"]
            else:
                raise ValueError("Subject is not founded")
    
    def get_subject_name(self, sub_id:int) -> int:
        if id is None:
            raise ValueError("id not specified")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM subjects WHERE id=?",(sub_id,))
            row = cur.fetchone()
            return row["name"]
    
    #--------------------------SCHEDULE----------------------
    def ensure_schedule(self, group_id:int, subject_id:int, lesson_num:int, classroom:str, date:str):
        if group_id is None:
            raise ValueError("Group_id not specified")
        if subject_id is None:
            raise ValueError("Subject_id is None")
        if lesson_num is None:
            raise ValueError("lesson_num is None")
        if classroom is None:
            raise ValueError("Classroom is None")
        if date is None:
            raise ValueError("date is None")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO schedule (group_id,subject_id,lesson_num,classroom) VALUES (?,?,?,?)",
                        (group_id,subject_id,lesson_num,classroom))
    
    def delete_schedule(self, date:str, group_id:int):
        if date is None or group_id is None:
            raise ValueError("Надо указать все парамметры для удаления рассписания")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM schedule WHERE group_id = ? AND date = ?",
                        (group_id,date))
            
            if cur.rowcount == 0:
                raise ValueError("Расписание на эту дату не найдено")
    
    def get_schedule(self,
                     group_id:int,
                     date:str):
        if group_id is None or date is None:
            raise ValueError("Нужно указать все парраметры для получения рассписания")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT subject_id,classroom,lesson_num FROM schedule WHERE group_id = ? AND date = ? ORDER BY lesson_num",
                        (group_id, date))
            rows = cur.fetchall()
            if not rows:
                raise ValueError("Рассписание на этот день не найдено")
            
            return [(row["subject_id"],row["lesson_num"],row["classroom"]) for row in rows]
    
    def get_schedule_id(self,
                        subject_id:int,
                        date:str) -> int:
        if subject_id is None:
            raise ValueError("Subject id is None")
        if date is None:
            raise ValueError("Date is None")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM schedule WHERE subject_id = ? AND date = ?",
                        (subject_id,date))
    
    #-------------------------GRADES----------------------------------

    def ensure_grade(self,
                     user_id:int,
                     schedule_id:int,
                     grade:int):
        if user_id is None:
            raise ValueError("User id is none")
        if schedule_id is None:
            raise ValueError("Schedule id is none")
        if grade is None:
            raise ValueError("Grade is None")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO grades (user_id,schedule_id,grade) VALUES (?,?,?)",
                        (user_id,schedule_id,grade))
    def delete_grade(self,
                     user_id:int,
                     schedule_id:int):
        if user_id is None:
            raise ValueError("user id is None")
        if schedule_id is None:
            raise ValueError("Schedule id is None")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM grades WHERE user_id = ? AND schedule_id = ?",
                        (user_id, schedule_id)) 
            if cur.rowcount == 0:
                raise ValueError("Оценка не найдена")
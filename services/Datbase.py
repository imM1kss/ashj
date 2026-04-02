import sqlite3
from typing import List, Tuple, Optional
import json
import random
import datetime
from datetime import timedelta
import secrets
import string

class Database:
    def __init__(self, path: str = "database.db"):
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
                
                UNIQUE (group_id, name, year),
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
            CREATE TABLE IF NOT EXISTS group_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL UNIQUE,
                code TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                               
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );
            """)

    #--------------------------------------USERS---------------------------------
    def ensure_user(self,
                    full_name:Optional[str] = None,
                    role: Optional[str] = "user",
                    telegram_id: Optional[int] = None,
                    vk_id: Optional[int] = None,
                    group_id: Optional[int] = None,
                    ) -> int:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ")
    
        
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
                if full_name is not None and not row["full_name"]:
                    cur.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name, user_id))
                if role == "admin" and row["role"] == "user":
                    cur.execute("UPDATE users SET role = ? WHERE id = ?", (role,user_id))
                
            else:
                cur.execute("""
                    INSERT INTO users (telegram_id, vk_id, group_id, full_name, role) VALUES (?,?,?,?,?)
                """, (telegram_id, vk_id, group_id, full_name, role))
                user_id = cur.lastrowid
            return user_id
    
    def delete_user(self, 
                    user_id:Optional[int] = None,
                    telegram_id: Optional[int] = None,
                    vk_id: Optional[int] = None) -> None:
        if user_id is None and telegram_id is None and vk_id is None:
            raise ValueError("user_id is None")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = ? OR telegram_id = ? OR vk_id = ?",
                        (user_id,telegram_id, vk_id))
    
    def is_admin(self,
                telegram_id:Optional[int] = None,
                vk_id:Optional[int] = None,) -> bool:
        if telegram_id is None and vk_id is None:
            raise ValueError("Укажите хотя-бы какое-то id")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT role FROM users WHERE telegram_id = ? OR vk_id = ?",
                        (telegram_id, vk_id))
            row = cur.fetchone()
            if row:
                if row['role'] == "admin":
                    return True 
            return False
    
    def get_admins(self) -> List[int]:

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE role = ?",("admin",))
            return [row['id'] for row in cur.fetchall()]

    
    #------------------------------GROUPS----------------------------------
    def ensure_group(self,
                     name: Optional[str] = None,
                     telegram_id: Optional[int] = None,
                     vk_id: Optional[int] = None
                     ) -> int:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id,telegram_id,vk_id,name FROM groups
                WHERE telegram_id = ? OR vk_id = ? OR name = ?
            """, (telegram_id, vk_id,name))
            row = cur.fetchone()

            if row:
                group_id = row["id"]

                if vk_id is not None and row["vk_id"] is not None:
                    return None
                if telegram_id is not None and row["telegram_id"] is not None:
                    return None
                if name is not None and row["name"] is not None:
                    return None

                if telegram_id is not None and not row["telegram_id"]:
                    cur.execute("UPDATE groups SET telegram_id = ? WHERE id = ?", (telegram_id, group_id))
                if vk_id is not None and not row["vk_id"]:
                    cur.execute("UPDATE groups SET vk_id = ? WHERE id = ?", (vk_id, group_id))
            else:
                if name is None:
                    raise ValueError("Группа не найдена и не может быть создана, так как нет нужнх парраметров")
                cur.execute("""
                    INSERT INTO groups (name, telegram_id, vk_id)
                    VALUES (?,?,?)
                """, (name, telegram_id, vk_id))
                group_id = cur.lastrowid
            return group_id
    
    def get_group_id(self, 
                     telegram_id: Optional[int] = None, 
                     vk_id: Optional[int] = None,
                     name: Optional[str] = None) -> int:

        if telegram_id is None and vk_id is None and name is None:
            raise ValueError("Нужно хотя-бы ВК или ТГ или название")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM groups
                WHERE telegram_id = ? OR vk_id = ? OR name = ?
                """, (telegram_id, vk_id, name))
            row = cur.fetchone()
            if not row:
                raise ValueError("Группа не найдена")
            return row["id"]
    
    def get_group_names(self) -> List[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM groups ORDER BY name")
            return [row["name"] for row in cur.fetchall()]
    
    #------------------------------SUBJECTS--------------------------------
    def ensure_subject(self,
                       name: str = None,
                       year:int = None,
                       telegram_id: Optional[int] = None,
                       vk_id:Optional[int] = None) -> int:
        if name is None:
            raise ValueError("Name not specified")
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужно зотя-бы вк или тг")
        if year is None:
            raise ValueError("Year not specified")

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""SELECT id 
                        FROM subjects
                        JOIN groups ON subjects.group_id = groups.id 
                        WHERE (groups.telegram_id = ? OR groups.vk_id = ?)
                        AND subjects.name = ? 
                        AND year = ? """,
                        (telegram_id,vk_id,name,year))
            row = cur.fetchone()

            if row:
                return row["id"]
            else:
                group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
                cur.execute("INSERT INTO subjects (name,group_id,year) VALUES (?,?,?,)", (name, group_id, year))
                return cur.lastrowid
    
    def get_subjects(self,
                     telegram_id: Optional[int] = None,
                     vk_id: Optional[int] = None) -> List[Tuple[int,str]]:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""SELECT id,name 
                        FROM subjects 
                        JOIN groups ON subjects.group_id = groups.id 
                        WHERE groups.telegram_id = ? OR groups.vk_id = ?""",
                        (telegram_id, vk_id))
            return [(row["id"],row["name"]) for row in cur.fetchall()]
    
    def delete_subject(self,
                       telegram_id: Optional[int] = None,
                       vk_id: Optional[int] = None,
                       name:str = None,
                       year:int = None) -> bool:
        if telegram_id is None and vk_id is None:
            raise ValueError("Укажите хотя-бы ВК или ТГ")
        if name is None or year is None:
            raise ValueError("Name or Year is None")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            cur.execute("DELETE FROM subjects WHERE group_id = ? AND name = ? AND year = ?", (group_id,name,year))
            return cur.rowcount > 0
    
    def get_subject_id(self,
                       telegram_id:Optional[int] = None,
                       vk_id:Optional[int] = None, 
                       group_id:Optional[int] = None,
                       name: str = None,
                       year: int = None) -> int:
        if telegram_id is None and vk_id is None and group_id is None:
            raise ValueError("Нужен хотя-бы вк или тг или id")
        if name is None or year is None:
            raise ValueError("Наименование или Год не указаны")
        
        with self._connect() as conn:
            cur = conn.cursor()
            if group_id is None:
                group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            cur.execute("""SELECT id FROM subjects
                        WHERE group_id = ? 
                        AND name = ?
                        AND year = ?""",(group_id,name, year))
            row = cur.fetchone()
            if row:
                return row["id"]
            else:
                raise ValueError("Subject is not founded")
    
    def get_subject_name(self,
                         telegram_id:Optional[int] = None,
                         vk_id:Optional[int] = None,
                         name:str = None,
                         year:int = None) -> str:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if name is None or year is None:
            raise ValueError("Наименование или Год не указаны")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            cur.execute("SELECT name FROM subjects WHERE group_id = ? AND year = ? AND name = ?",(group_id,year,name))
            row = cur.fetchone()
            if row:
                return row["name"]
            else:
                raise ValueError("Предмет не был найден")
    
    #--------------------------SCHEDULE----------------------
    def ensure_lesson(self,
                      telegram_id: Optional[int] = None,
                      vk_id:Optional[int] = None,
                      year:int = None,
                      name:str = None,
                      lesson_num:int = None,
                      classroom:str = None,
                      date:str = None) -> None:
        
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if year is None or name is None or lesson_num is None or classroom is None or date is None:
            raise ValueError("Один из параметров не указан(год,наименование,номер пары,кабинет или дата)")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            subject_id = self.get_subject_id(telegram_id=telegram_id, vk_id=vk_id, name=name, year=year)
            cur.execute("INSERT INTO schedule (group_id,subject_id,lesson_num,classroom) VALUES (?,?,?,?)",
                        (group_id,subject_id,lesson_num,classroom))
    
    def delete_schedule(self, 
                        date:str = None, 
                        telegram_id: Optional[int] = None, 
                        vk_id:Optional[int] = None):
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if date is None:
            raise ValueError("Дата не указана")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            cur.execute("DELETE FROM schedule WHERE group_id = ? AND date = ?",
                        (group_id,date))
            if cur.rowcount == 0:
                raise ValueError("Расписание на эту дату не найдено")
    
    def get_schedule(self,
                    telegram_id: Optional[int] = None, 
                    vk_id:Optional[int] = None,
                    date:str = None) -> List[Tuple[int,str,str]]:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if date is None:
            raise ValueError("Дата не указана")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            cur.execute("""SELECT subjects.name,classroom,lesson_num 
                        FROM schedule
                        JOIN subjects ON schedule.subject_id = subjects.id
                        WHERE schedule.group_id = ? 
                        AND date = ? 
                        ORDER BY lesson_num""",
                        (group_id, date))
            rows = cur.fetchall()
            if not rows:
                raise ValueError("Рассписание на этот день не найдено")
            
            return [(row["lesson_num"],row["name"],row["classroom"]) for row in rows]
    
    def get_schedule_id(self,
                        telegram_id:Optional[int] = None,
                        vk_id:Optional[int] = None,
                        name:str = None,
                        year:int = None,
                        date:str = None) -> int:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if date is None or name is None or year is None:
            raise ValueError("Один из параметров не указан(дата,наименование или год)")
        
        with self._connect() as conn:
            cur = conn.cursor()
            subject_id = self.get_subject_id(telegram_id=telegram_id,vk_id=vk_id,
                                             year=year,name=name)
            cur.execute("SELECT id FROM schedule WHERE subject_id = ? AND date = ?",
                        (subject_id,date))
            row = cur.fetchone()
            return row['id']
    
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
    def get_grades(self,
                   subject_name:str = None,
                   start_date:str = None,
                   end_date:str = None,
                   telegram_id:Optional[int] = None,
                   vk_id:Optional[int]=None) -> List[Tuple[str,int,str]]:
        
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if start_date is None or end_date is None or subject_name is None:
            raise ValueError("Один из парраметров не указан, оценки не могут быть получены.")
        
        
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT subjects.name, schedule.date, grades.grade
                FROM grades
                JOIN schedule ON grades.schedule_id = schedule.id
                JOIN subjects ON schedule.subject_id = subjects.id
                JOIN users ON grades.user_id = users.id
                WHERE (users.telegram_id = ? OR users.vk_id = ?) 
                        AND subjects.name = ? 
                        AND schedule.date >= ? 
                        AND schedule.date <= ?
                ORDER BY schedule.date
            """,(telegram_id,vk_id,subject_name,start_date,end_date))
            rows = cur.fetchall()
            return [(row["name"],row["grade"],row["date"]) for row in rows]
    #---------------------------------HOMEWORK------------------------------------------

    def ensure_homework(self,
                        telegram_id:Optional[int] = None,
                        vk_id:Optional[int] = None,
                        name:str = None,
                        year:int = None,
                        description:str = None,
                        attachments:Optional[List[str]] = None,
                        lessons_left:int = 1) -> None:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if name is None or year is None:
            raise ValueError("Один из параметров (наименование, год, описание или вложения) не указан")
        
        description = description or ""
        attachments = attachments or []

        if not description and not attachments:
            raise ValueError("Нужно хотя-бы описание или вложения")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
            subject_id = self.get_subject_id(group_id=group_id,name=name,year=year)
            attachments_json = json.dumps(attachments)
            cur.execute("""
            INSERT INTO homework (group_id,subject_id,description,attachments,lessons_left)
            VALUES (?,?,?,?,?)
            """,(group_id,subject_id,description,attachments_json,lessons_left))
    
    def delete_homework(self, homework_id:Optional[int] = None) -> None:
        if homework_id is None:
            raise ValueError("Укажите id")
        
        with self._connect() as conn:
            conn.execute("DELETE FROM homework WHERE id = ?", (homework_id,))
    
    def get_homework(self,
                     telegram_id:Optional[int] = None,
                     vk_id: Optional[int] = None,
                     name:Optional[str] = None,
                     year:Optional[int] = None) -> List[Tuple[int,str,str,List[str],int]]:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        if name is None or year is None:
            raise ValueError("Не указаны наименование или год")
        
        with self._connect() as conn:
            cur = conn.cursor()
            group_id = self.get_group_id(telegram_id=telegram_id,vk_id=vk_id)
            subject_id = self.get_subject_id(group_id=group_id,name=name,year=year)
            cur.execute("""
            SELECT homework.id,subjects.name,homework.description,homework.attachments,homework.lessons_left
            FROM homework
            JOIN subjects ON homework.subject_id = subjects.id
            WHERE homework.group_id = ? AND subjects.id = ?
            """,(group_id,subject_id))

            rows = cur.fetchall()
            return [
                (
                    row['id'],
                    row['name'],
                    row['description'],
                    json.loads(row['attachments']) if row['attachments'] else [],
                    row['lessons_left']
                )
                for row in rows
            ]

 #----------------------GROUP_LINK--------------------------

    def ensure_link(self,
                    vk_id: Optional[int] = None,
                    telegram_id: Optional[int] = None,
                    ) -> str:
        if telegram_id is None and vk_id is None:
            raise ValueError("Нужен хотя-бы вк или тг")
        
        group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
        now = datetime.now()
        ATTEMPTS = 3


        with self._connect() as conn:
            cur = conn.cursor()
            

            cur.execute("SELECT created_at FROM group_link WHERE group_id = ?",
                        (group_id,))
            if cur.fetchone() is not None:
                created_at = cur.fetchone()
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                if now - dt >= timedelta(minutes=10):
                    alphabet = string.ascii_letters + string.digits
                    code = ''.join(secrets.choice(alphabet) for _ in range(6))
                    time = now.strftime("%Y-%m-%d %H:%M:%S")
                    cur.execute("INSERT INTO group_link (group_id,code,created_at) VALUES (?,?,?)",
                                (group_id,code,time,ATTEMPTS))
                    return code
                else:
                    return None
            else:
                alphabet = string.ascii_letters + string.digits
                code = ''.join(secrets.choice(alphabet) for _ in range(6))
                time = now.strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("INSERT INTO group_link (group_id,code,created_at,attempts) VALUES (?,?,?,?)",
                            (group_id,code,time,ATTEMPTS))
                return code
    
    def chech_code(self,
                   vk_id:Optional[int] = None,
                   telegram_id:Optional[int] = None,
                   code:Optional[str] = None) -> bool:
        if (telegram_id is None and vk_id is None) or (code is None):
            raise ValueError("code is not definded or (tg and vk) is None")
        
        group_id = self.get_group_id(telegram_id=telegram_id, vk_id=vk_id)
        now = datetime.now()

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, code, created_at, attempts FROM group_link WHERE group_id = ?",
                        (group_id,))
            row = cur.fetchone()
            if row is not None:
                dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
                if now - dt >= timedelta(minutes=10):
                    cur.execute("DELETE FROM group_link WHERE id = ?", (row["id"],))
                    return False
                else:
                    if code == row["code"]:
                        return True
                    else:
                        attempts = row["attempts"] - 1
                        if attempts <= 0:
                            cur.execute("DELETE FROM group_link WHERE id = ?", (row["id"],))
                        else:
                            cur.execute("UPDATE group_link SET attempts = ? WHERE id = ?", (row["id"],))
                        return False
            else:
                return False
        
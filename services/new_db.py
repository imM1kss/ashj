#imports
import asyncio
import asyncpg
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, SmallInteger, Date, func, CheckConstraint, Sequence, ForeignKey, UniqueConstraint, ARRAY, String
from dotenv import load_dotenv
from os import getenv
from enum import IntEnum
from datetime import date
from typing import Optional, List, TypeVar, Generic, Sequence

load_dotenv()


DB_URL = f"postgresql+asyncpg://{getenv('DB_USER')}:{getenv('DB_PASS')}@127.0.0.1:{getenv('DB_PORT')}/test_db"
engine = create_async_engine(DB_URL, echo=True)


async_session = async_sessionmaker(engine, expire_on_commit=False)

#-----------------TABLES--------------------

class BaseModel(DeclarativeBase):
    pass

class AcademicRole(IntEnum):
    USER = 0
    STUDENT = 1
    PRAEPOSITOR = 2
    TEACHER = 3
    DEPUTY = 4

class AdminRole(IntEnum):
    NONE = 0
    HELPER = 1
    ADMIN = 2

class UserModel(BaseModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    group_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=False,
        nullable=True
    )
    full_name: Mapped[str] = mapped_column(
        nullable=True,
        unique=False
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True
    )
    vk_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True
    )
    max_id: Mapped[int] = mapped_column(
        BigInteger,
        unique= True,
        nullable=True
    )
    academic_role: Mapped[int] = mapped_column(
        SmallInteger,
        CheckConstraint(
            "academic_role BETWEEN 0 AND 4",
            name="academic_role_range"
        ),
        nullable=False,
        unique=False,
        default=AcademicRole.USER
    )
    admin_role:Mapped[int] = mapped_column(
        SmallInteger,
        CheckConstraint(
            "admin_role BETWEEN 0 AND 2",
            name="admin_role_range"
        ),
        default=AdminRole.NONE,
        nullable=False,
        unique=False
    )

    __table_args__ = (
        CheckConstraint(
            "tg_id IS NOT NULL OR vk_id IS NOT NULL OR max_id IS NOT NULL",
            name="check_user_tg_vk_max"
        )
    )

class GroupModel(BaseModel):
    __tablename__="groups"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True
    )
    designation: Mapped[str] = mapped_column(
        unique=True,
        nullable=False
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True
    )
    vk_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True
    )
    max_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "tg_id IS NOT NULL OR vk_id IS NOT NULL OR max_id IS NOT NULL",
            name="check_group_tg_vk_max"
        )
    )

class SubjectModel(BaseModel):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True
    )
    title: Mapped[str] = mapped_column(
        nullable=False,
        unique=False
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey(
            "groups.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "group_id","title", 
            name="uniq_subj_groupid_title"
        )
    )

class ScheduleModel(BaseModel):
    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey(
            "groups.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    subj_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    period: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        unique=False
    )
    classroom:Mapped[str] = mapped_column(
        nullable=True,
        unique=False
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=False
    )

    __table_args__ = (
        UniqueConstraint(
            "group_id","period","date",
            name="uniq_schedule_groupid_period_date"
        )
    )

class GradeModel(BaseModel):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey(
            "schedule.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    grade: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        unique=False
    )

    __table_args__ = (
        CheckConstraint(
            "grade BETWEEN 1 AND 5",
            name="check_grade"
        )
    )

class HomeworkModel(BaseModel):
    __tablename__ = "homework"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subjects.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )
    task: Mapped[str] = mapped_column(
        unique=False,
        nullable=False
    )
    attachment: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False
    )


#----------REPOS-----------

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure(self,
        group_id:Optional[int] = None,
        full_name:Optional[str] = None,
        tg_id:Optional[int] = None,
        vk_id:Optional[int] = None,
        max_id:Optional[int] = None,
        academic_role:Optional[int] = AcademicRole.USER,
        admin_role:Optional[int] = AdminRole.NONE
    ) -> UserModel:
        
        if (tg_id is None) and (vk_id is None) and (max_id is None):
            raise ValueError("Нужно указать хотя-бы одно из полей: tg_id, vk_id, max_id в user.ensure()")

T = TypeVar('T')
        
class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by(self, **kwargs) -> T | None:
        filters = [getattr(self.model, k) == v for k,v in kwargs.items() if v is not None]
        stmt = select(self.model).where(and_(*filters))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by(self, **kwargs) -> Sequence[T]:
        stmt = select(self.model)
        filters = [getattr(self.model,k) == v for k,v in kwargs.items() if v is not None]
        if not filters:
            return []
        stmt.where(and_(*filters))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by(self, **kwargs) -> bool:
        filters = [getattr(self.model,k) == v for k,v in kwargs.items() if v is not None]
        if not filters:
            return False
        stmt = delete(self.model).where(and_(*filters))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def add(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        return obj

    async def update_by(self, filters:dict, values:dict) -> int:
        filters_stand = [getattr(self.model, k) == v for k,v in filters.items() if v is not None]
        if not filters_stand:
            return 0

    

class GroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class SubjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class ScheduleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class GradeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class HomeworkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

        self.user = UserRepository(session=self.session)
        self.group = GroupRepository(session=self.session)
        self.subject = SubjectRepository(session=self.session)
        self.schedule = ScheduleRepository(session=self.session)
        self.grade = GradeRepository(session=self.session)
        self.homework = HomeworkRepository(session=self.session)
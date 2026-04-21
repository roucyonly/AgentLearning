"""
SQLAlchemy 数据库表定义
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    role = Column(String(20), nullable=False)  # TEACHER / STUDENT
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    student_classes = relationship("StudentClassMapping", back_populates="student")


class TeacherProfile(Base):
    """教师分身配置表"""
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    avatar_prompt = Column(Text, nullable=False)
    name = Column(String(100), nullable=False)
    personality = Column(Text, nullable=False)
    catchphrase = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="teacher_profile")
    classes = relationship("Class", back_populates="teacher")


class Class(Base):
    """班级表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_name = Column(String(100), nullable=False)
    invite_code = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    teacher = relationship("TeacherProfile", back_populates="classes")
    student_mappings = relationship("StudentClassMapping", back_populates="class_obj")


class StudentClassMapping(Base):
    """学生-班级映射表"""
    __tablename__ = "student_class_mappings"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("User", back_populates="student_classes")
    class_obj = relationship("Class", back_populates="student_mappings")


class Document(Base):
    """文档表"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf / pptx / txt
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)


class ChatHistory(Base):
    """对话历史表"""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string
    trace_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

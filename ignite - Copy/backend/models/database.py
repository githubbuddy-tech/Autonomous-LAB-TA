"""SQLAlchemy database models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, LargeBinary, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Interaction(Base):
    """Student interaction logging"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), index=True)
    language = Column(String(20), index=True)
    error_type = Column(String(50))
    hint_level = Column(Integer)
    successful = Column(Boolean)
    student_id_hash = Column(String(64))
    hint_used = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sandbox_used = Column(Boolean, default=False)

class LabTask(Base):
    """Lab task definitions"""
    __tablename__ = "lab_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    language = Column(String(20))
    difficulty = Column(String(20))
    starter_code = Column(Text)
    tests = Column(Text)
    expected_output = Column(Text)

class ReferenceSolution(Base):
    """Reference solutions for tasks"""
    __tablename__ = "reference_solutions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), index=True)
    language = Column(String(20))
    solution = Column(Text)
    embedding = Column(LargeBinary)  # For RAG vector search
    created_at = Column(DateTime, default=datetime.utcnow)

class CodeAnalysis(Base):
    """Code analysis results"""
    __tablename__ = "code_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    student_code_hash = Column(String(64))
    syntax_similarity = Column(Float)
    logic_similarity = Column(Float)
    error_count = Column(Integer)
    quality_score = Column(Integer)
    analysis_result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
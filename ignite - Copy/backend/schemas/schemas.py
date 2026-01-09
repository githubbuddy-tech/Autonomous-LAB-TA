"""Pydantic schemas for API requests/responses"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request schemas
class CodeSubmission(BaseModel):
    code: str
    language: str = "python"
    task_id: str = "python_sum_list"
    student_id: str = "anonymous"
    hint_level: int = Field(1, ge=1, le=5)

class CodeAnalysisRequest(BaseModel):
    student_code: str
    reference_code: Optional[str] = None
    language: str = "python"
    task_id: str

class RAGHintRequest(BaseModel):
    code: str
    error: Optional[str] = None
    language: str = "python"
    hint_level: int = Field(1, ge=1, le=5)
    task_id: Optional[str] = None

class SandboxExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = Field(10, ge=1, le=30)
    use_docker: bool = True

class CompareCodeRequest(BaseModel):
    student_code: str
    reference_code: str
    language: str = "python"

# Response schemas
class HintResponse(BaseModel):
    hint: str
    hint_level: int
    error_type: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    suggestions: List[str] = []
    execution_time: Optional[float] = None
    sandboxed: bool = False

class AnalysisResponse(BaseModel):
    student_code: str
    reference_code: Optional[str] = None
    language: str
    error_type: str
    success: bool
    quality_score: int = Field(0, ge=0, le=10)
    issues: List[str] = []
    suggestions: List[str] = []
    comparison_results: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ComparisonResponse(BaseModel):
    syntax_similarity: float = Field(0.0, ge=0.0, le=1.0)
    logic_similarity: float = Field(0.0, ge=0.0, le=1.0)
    embedding_similarity: float = Field(0.0, ge=0.0, le=1.0)
    overall_similarity: float = Field(0.0, ge=0.0, le=1.0)
    match_percentage: float = Field(0.0, ge=0.0, le=100.0)
    grade: str
    differences: List[Dict[str, Any]] = []
    error: Optional[str] = None

class RAGHintResponse(BaseModel):
    hint: str
    similarity_score: float = Field(0.0, ge=0.0, le=1.0)
    similar_solutions: List[Dict[str, Any]] = []
    rag_used: bool = True
    error: Optional[str] = None

class SandboxExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    sandboxed: bool
    execution_time: Optional[float] = None

# Database models schemas
class LabTaskSchema(BaseModel):
    task_id: str
    title: str
    description: str
    language: str
    difficulty: str
    starter_code: Optional[str] = None
    tests: Optional[str] = None
    expected_output: Optional[str] = None

class ReferenceSolutionSchema(BaseModel):
    task_id: str
    language: str
    solution: str

class AnalyticsResponse(BaseModel):
    period_days: int
    total_interactions: int
    success_rate: float
    language_distribution: List[Dict[str, Any]]
    error_distribution: List[Dict[str, Any]]
    common_errors: List[str]
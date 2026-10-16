from typing import List
from pydantic import BaseModel, Field

# --- Shared Models ---
class Achievement(BaseModel):
    id: str
    title: str
    description: str
    icon: str # e.g., 'bi-trophy'
    requirement_type: str # e.g., 'total_quizzes' or 'avg_score'
    requirement_value: int
    color: str # e.g., 'primary', 'warning', 'success'

class VideoItem(BaseModel):
    title: str
    url: str
    duration: str # e.g., '12:45'

class QuizItem(BaseModel):
    question: str
    option1: str
    option2: str
    option3: str
    option4: str
    # Refined: Added pattern to prevent AI from returning 'A', '1', or 'option_1'
    answer: str = Field(pattern="^option[1-4]$") 
    difficulty: str # 'easy', 'medium', 'hard'

# --- Nested Structure ---
class Chapter(BaseModel):
    chapter_id: str
    title: str
    overview: str = Field(description="500-word comprehensive academic summary")
    video_stack: List[VideoItem]
    # Refined: Enforced your rule of at least 30 questions per chapter
    quiz_data: List[QuizItem] = Field(min_length=30)

class Subject(BaseModel):
    subject_id: str
    subject_name: str
    subject_overview: str
    icon: str # e.g., 'bi-diagram-3'
    achievement: List[Achievement]
    # Refined: Enforced your rule of at least 5 chapters per subject
    chapters: List[Chapter] = Field(min_length=5)

class Course(BaseModel):
    course_id: str
    course_level: str
    course_context: str
    branch: str
    grade_level: str
    # Refined: Enforced your rule of at least 5 subjects per course
    subjects: List[Subject] = Field(min_length=5)

# --- Skeleton Models for Phases ---
class ChapterTitleList(BaseModel):
    """Used in Model 2 to establish the 5 chapter names for a subject."""
    titles: List[str] = Field(min_length=5, max_length=5)
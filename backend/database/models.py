from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    student_id: str
    student_name: str
    class_id: Optional[int] = None
    face_registered: bool = False


@dataclass
class Class:
    class_id: Optional[int]
    class_name: str
    department: Optional[str] = None
    semester: Optional[int] = None


@dataclass
class Exam:
    exam_id: Optional[int]
    exam_name: str
    class_id: Optional[int]
    exam_date: str
    start_time: Optional[str] = None


@dataclass
class Attendance:
    student_id: str
    student_name: str
    attendance_date: str
    attendance_time: str
    status: str
    session_id: Optional[int] = None
    verification_score: Optional[float] = None


@dataclass
class VerificationAttempt:
    student_id: Optional[str]
    result: str
    similarity: Optional[float] = None
    liveness_result: Optional[str] = None
    reason: Optional[str] = None
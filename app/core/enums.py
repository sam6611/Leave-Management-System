from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"


class DecisionSource(str, Enum):
    RULE_ENGINE = "rule_engine"
    AI = "ai"
    ADMIN = "admin"


class RuleDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"

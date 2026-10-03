"""Schemas Pydantic: o que entra e o que sai em cada rota."""

from .auth import LoginRequest, TokenResponse
from .course import CourseCreate, CourseRead
from .dashboard import DashboardRead
from .event import EventCreate, EventRead, EventUpdate
from .registration import (
    AttendanceUpdate,
    CertificateRead,
    RegistrationCreate,
    RegistrationRead,
)
from .user import UserCreate, UserRead

__all__ = [
    "AttendanceUpdate",
    "CertificateRead",
    "CourseCreate",
    "CourseRead",
    "DashboardRead",
    "EventCreate",
    "EventRead",
    "EventUpdate",
    "LoginRequest",
    "RegistrationCreate",
    "RegistrationRead",
    "TokenResponse",
    "UserCreate",
    "UserRead",
]

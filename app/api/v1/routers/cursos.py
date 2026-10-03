"""Rotas de cursos."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from ....core.config import settings
from ....core.deps import get_current_user_id
from ....schemas.course import CourseCreate, CourseRead
from ....services import course_service

router = APIRouter(prefix="/cursos", tags=["Cursos"])


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um curso (Administrador ou Professor)",
)
def cadastrar_curso(
    payload: CourseCreate, actor_id: int = Depends(get_current_user_id)
) -> CourseRead:
    return course_service.create_course(
        actor_id=actor_id,
        name=payload.name,
        code=payload.code,
        coordinator_id=payload.coordinator_id,
    )


@router.get("", response_model=list[CourseRead], summary="Lista os cursos")
def consultar_cursos(
    limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(default=0, ge=0),
) -> list[CourseRead]:
    """Consulta aberta: a lista de cursos é informação pública do evento."""
    return course_service.list_courses(limit=limit, offset=offset)


@router.get("/{course_id}", response_model=CourseRead, summary="Consulta um curso")
def consultar_curso(course_id: int) -> CourseRead:
    return course_service.get_course(course_id)
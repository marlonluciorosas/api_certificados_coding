"""Dados de exemplo para o banco (usuários, senhas, cursos, eventos e inscrições).

Para que serve: quando o professor (ou eu) abrir o /docs, já existem dados para
testar sem precisar cadastrar tudo na mão.

Como rodar:
    python popular_banco.py              # completa o que faltar
    python popular_banco.py --recriar    # apaga tudo e cria novamente
    python -m app.database.seed          # a mesma coisa, pelo módulo

As datas dos eventos são calculadas a partir de hoje (alguns já terminaram e
outros ainda vão acontecer), então o exemplo nunca "envelhece".
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from ..core.config import settings
from ..core.security import hash_password
from ..models.entities import RegistrationStatus, UserRole
from ..repositories import (
    course_repository,
    event_repository,
    registration_repository,
    user_repository,
)
from .converters import now_utc
from .session import clear_database, get_connection, init_db, transaction

# ---------------------------------------------------------------------------
# Usuários (a senha é gravada como hash, nunca em texto puro)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedUser:
    name: str
    email: str
    password: str
    role: str
    course_code: Optional[str] = None


SEED_USERS: tuple[SeedUser, ...] = (
    SeedUser(
        "Victor Ricardo Batista de Araújo",
        "victor.araujo@faculdade.edu",
        "admin123",
        UserRole.ADMIN.value,
    ),
    SeedUser(
        "Carla Mendes",
        "carla.mendes@faculdade.edu",
        "prof123",
        UserRole.PROFESSOR.value,
        "ADS",
    ),
    SeedUser(
        "Rafael Souza",
        "rafael.souza@faculdade.edu",
        "prof123",
        UserRole.PROFESSOR.value,
        "ADS",
    ),
    SeedUser(
        "Juliana Lima",
        "juliana.lima@faculdade.edu",
        "prof123",
        UserRole.PROFESSOR.value,
        "CC",
    ),
    SeedUser(
        "Marcos Vinícius Prado",
        "marcos.prado@faculdade.edu",
        "prof123",
        UserRole.PROFESSOR.value,
        "REDES",
    ),
    SeedUser(
        "Patrícia Andrade",
        "patricia.andrade@faculdade.edu",
        "prof123",
        UserRole.PROFESSOR.value,
        "SI",
    ),
    SeedUser("Ana Paula Ribeiro", "ana.ribeiro@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "ADS"),
    SeedUser("Bruno Ferreira", "bruno.ferreira@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "ADS"),
    SeedUser("Camila Rocha", "camila.rocha@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "ADS"),
    SeedUser("Diego Santos", "diego.santos@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "ADS"),
    SeedUser("Eduarda Alves", "eduarda.alves@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "CC"),
    SeedUser("Felipe Gomes", "felipe.gomes@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "CC"),
    SeedUser("Gabriela Nunes", "gabriela.nunes@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "CC"),
    SeedUser("Henrique Dias", "henrique.dias@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "SI"),
    SeedUser("Isabela Moraes", "isabela.moraes@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "SI"),
    SeedUser("João Pedro Martins", "joao.martins@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "REDES"),
    SeedUser("Karina Lopes", "karina.lopes@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "REDES"),
    SeedUser("Lucas Barbosa", "lucas.barbosa@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "ADS"),
    SeedUser("Mariana Teixeira", "mariana.teixeira@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "ADS"),
    SeedUser("Nathália Campos", "nathalia.campos@aluno.faculdade.edu", "aluno123", UserRole.PARTICIPANTE.value, "CC"),
)

# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedCourse:
    name: str
    code: str
    coordinator_email: str


SEED_COURSES: tuple[SeedCourse, ...] = (
    SeedCourse("Análise e Desenvolvimento de Sistemas", "ADS", "carla.mendes@faculdade.edu"),
    SeedCourse("Ciência da Computação", "CC", "juliana.lima@faculdade.edu"),
    SeedCourse("Sistemas de Informação", "SI", "patricia.andrade@faculdade.edu"),
    SeedCourse("Redes de Computadores", "REDES", "marcos.prado@faculdade.edu"),
)

# ---------------------------------------------------------------------------
# Eventos (days_from_now: negativo = já aconteceu)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedEvent:
    key: str
    title: str
    description: str
    course_code: Optional[str]
    responsible_email: str
    days_from_now: float
    duration_hours: float
    capacity: int
    location: str


SEED_EVENTS: tuple[SeedEvent, ...] = (
    SeedEvent(
        "semtec",
        "Semana Acadêmica de Tecnologia 2026",
        "Cinco dias de palestras, minicursos e apresentação dos trabalhos dos alunos.",
        "ADS",
        "carla.mendes@faculdade.edu",
        -45,
        20.0,
        200,
        "Auditório Principal",
    ),
    SeedEvent(
        "fastapi",
        "Workshop de FastAPI e APIs REST",
        "Construção de uma API completa com validação de dados e banco SQLite.",
        "ADS",
        "rafael.souza@faculdade.edu",
        -20,
        8.0,
        30,
        "Laboratório 03",
    ),
    SeedEvent(
        "maratona",
        "Maratona de Programação Interna",
        "Competição em equipes com problemas de lógica e estruturas de dados.",
        "CC",
        "juliana.lima@faculdade.edu",
        -10,
        5.0,
        20,
        "Laboratório 05",
    ),
    SeedEvent(
        "lgpd",
        "Oficina de LGPD e Proteção de Dados",
        "Como tratar dados pessoais em projetos acadêmicos e profissionais.",
        "SI",
        "patricia.andrade@faculdade.edu",
        -4,
        3.0,
        30,
        "Sala 204",
    ),
    SeedEvent(
        "git",
        "Minicurso de Git e GitHub",
        "Versionamento de código, ramos e revisão de código em equipe.",
        "ADS",
        "rafael.souza@faculdade.edu",
        7,
        4.0,
        25,
        "Laboratório 02",
    ),
    SeedEvent(
        "ml",
        "Introdução ao Machine Learning",
        "Primeiros passos com Python, dados e treinamento de modelos simples.",
        "CC",
        "juliana.lima@faculdade.edu",
        12,
        6.0,
        40,
        "Laboratório de Inteligência Artificial",
    ),
    SeedEvent(
        "seginfo",
        "Segurança da Informação na Prática",
        "Testes de invasão em ambiente controlado e boas práticas de proteção.",
        "REDES",
        "marcos.prado@faculdade.edu",
        18,
        8.0,
        35,
        "Laboratório de Redes",
    ),
    SeedEvent(
        "carreira",
        "Palestra: Carreira em Tecnologia",
        "Conversa com profissionais sobre mercado de trabalho e primeiras vagas.",
        "SI",
        "patricia.andrade@faculdade.edu",
        21,
        2.0,
        100,
        "Auditório B",
    ),
    SeedEvent(
        "docker",
        "Curso de Docker para Iniciantes",
        "Containers, imagens e publicação de aplicações.",
        "ADS",
        "rafael.souza@faculdade.edu",
        25,
        6.0,
        20,
        "Laboratório 01",
    ),
    SeedEvent(
        "hackathon",
        "Hackathon Faculdade 2026",
        "Trinta horas de desenvolvimento em equipe com desafio real proposto por empresa parceira.",
        "CC",
        "juliana.lima@faculdade.edu",
        40,
        30.0,
        60,
        "Espaço Maker",
    ),
)


def _ensure_users(connection, course_by_code: dict[str, int]) -> dict[str, int]:
    """Cadastra os usuários que ainda não existem e devolve e-mail -> id."""
    users_by_email: dict[str, int] = {}

    for seed in SEED_USERS:
        existing = user_repository.get_user_by_email(connection, seed.email)
        if existing is not None:
            users_by_email[seed.email] = existing.id
            continue

        course_id = course_by_code.get(seed.course_code or "")
        user_id = user_repository.insert_user(
            connection,
            name=seed.name,
            email=seed.email,
            password_hash=hash_password(seed.password),
            role=seed.role,
            course_id=course_id,
            created_at=now_utc(),
        )
        users_by_email[seed.email] = user_id

    return users_by_email


def _ensure_courses(connection, users_by_email: dict[str, int]) -> dict[str, int]:
    """Cadastra os cursos que ainda não existem e devolve sigla -> id."""
    courses_by_code: dict[str, int] = {}

    for seed in SEED_COURSES:
        existing = course_repository.get_course_by_code(connection, seed.code)
        if existing is not None:
            courses_by_code[seed.code] = existing.id
            continue

        course_id = course_repository.insert_course(
            connection,
            name=seed.name,
            code=seed.code,
            coordinator_id=users_by_email.get(seed.coordinator_email),
            created_at=now_utc(),
        )
        courses_by_code[seed.code] = course_id

    return courses_by_code


def _ensure_events(
    connection, users_by_email: dict[str, int], courses_by_code: dict[str, int]
) -> dict[str, int]:
    """Cadastra os eventos que ainda não existem e devolve chave -> id."""
    events_by_key: dict[str, int] = {}
    existing_titles = {
        event.title: event.id
        for event in event_repository.list_events(connection, limit=1000, offset=0)
    }

    for seed in SEED_EVENTS:
        if seed.title in existing_titles:
            events_by_key[seed.key] = existing_titles[seed.title]
            continue

        start_at = now_utc() + timedelta(days=seed.days_from_now)
        event_id = event_repository.insert_event(
            connection,
            title=seed.title,
            description=seed.description,
            start_at=start_at,
            location=seed.location,
            capacity=seed.capacity,
            duration_hours=seed.duration_hours,
            responsible_id=users_by_email[seed.responsible_email],
            course_id=courses_by_code.get(seed.course_code or ""),
            created_at=now_utc(),
        )
        events_by_key[seed.key] = event_id

    return events_by_key


def _create_registrations(
    connection,
    users_by_email: dict[str, int],
    events_by_key: dict[str, int],
    users_by_course: dict[str, list[int]],
) -> tuple[int, int]:
    """Sorteia inscrições de forma reprodutível (sempre o mesmo resultado).

    Usamos random.Random(7) para que o resultado seja igual em toda máquina:
    é um exemplo de dados, não um sorteio de verdade.
    """
    sorter = random.Random(7)
    created = 0
    attended_marked = 0

    for seed in SEED_EVENTS:
        event_id = events_by_key[seed.key]
        event_finished = seed.days_from_now < 0

        # 1) alunos do próprio curso entram primeiro (mais realista)
        candidates = list(users_by_course.get(seed.course_code or "", []))
        # 2) depois alunos dos outros cursos
        others = [
            user_id
            for code, ids in users_by_course.items()
            if code != seed.course_code
            for user_id in ids
        ]
        candidates = candidates + others

        total = min(sorter.randint(4, 9), len(candidates), seed.capacity)
        for user_id in sorter.sample(candidates, total):
            if registration_repository.find_by_user_and_event(connection, user_id, event_id):
                continue
            registration_id = registration_repository.insert_registration(
                connection, user_id=user_id, event_id=event_id, created_at=now_utc()
            )
            created += 1

            if event_finished and sorter.random() < 0.85:
                # Nos eventos que já aconteceram quase todos compareceram.
                registration_repository.set_attendance(connection, registration_id, True)
                attended_marked += 1
            elif not event_finished and sorter.random() < 0.15:
                # Um ou outro cancelamento nos eventos futuros (respeitando 24h).
                registration_repository.cancel_registration(
                    connection, registration_id, now_utc()
                )

    return created, attended_marked


def populate_database(*, force: bool = False) -> dict[str, int]:
    """Cria as tabelas e insere os dados de exemplo.

    A operação pode ser repetida: o que já existe é mantido e só o que falta é
    inserido. Com force=True o banco é limpo antes.
    """
    init_db()

    with transaction(immediate=True) as connection:
        if force:
            connection.execute("DELETE FROM registrations")
            connection.execute("DELETE FROM events")
            connection.execute("DELETE FROM users")
            connection.execute("UPDATE courses SET coordinator_id = NULL")
            connection.execute("DELETE FROM courses")
            # Zera os contadores para os ids começarem em 1 novamente.
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name IN "
                "('registrations', 'events', 'courses', 'users')"
            )

        users_by_email = _ensure_users(connection, {})
        courses_by_code = _ensure_courses(connection, users_by_email)

        # Segunda passada: agora os cursos existem, então vinculamos os alunos.
        for seed in SEED_USERS:
            course_id = courses_by_code.get(seed.course_code or "")
            if seed.course_code and course_id is not None:
                connection.execute(
                    "UPDATE users SET course_id = ? WHERE id = ? AND course_id IS NULL",
                    (course_id, users_by_email[seed.email]),
                )

        users_by_course: dict[str, list[int]] = {}
        for seed in SEED_USERS:
            if seed.course_code:
                users_by_course.setdefault(seed.course_code, []).append(
                    users_by_email[seed.email]
                )

        events_by_key = _ensure_events(connection, users_by_email, courses_by_code)
        created, attended_marked = _create_registrations(
            connection, users_by_email, events_by_key, users_by_course
        )

        summary = {
            "usuarios": user_repository.count_users(connection),
            "cursos": course_repository.count_courses(connection),
            "eventos": event_repository.count_events(connection),
            "inscricoes_criadas_agora": created,
            "presencas_confirmadas_agora": attended_marked,
        }

    return summary


def show_credentials() -> None:
    """Imprime a lista de logins para facilitar o teste no Swagger."""
    print("\nUsuários criados (e-mail / senha / perfil):")
    print("-" * 74)
    for seed in SEED_USERS:
        print(f"  {seed.email:<44} {seed.password:<10} {seed.role}")
    print("-" * 74)
    print("Dica: no Swagger, faça POST /api/v1/auth/login e use o token em Authorize.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula o banco com dados de exemplo.")
    parser.add_argument(
        "--recriar",
        action="store_true",
        help="apaga os dados atuais antes de popular novamente",
    )
    parser.add_argument(
        "--silencioso", action="store_true", help="não mostra a lista de usuários"
    )
    args = parser.parse_args()

    print(f"Banco: {settings.database_path}")
    summary = populate_database(force=args.recriar)
    print("Dados de exemplo prontos:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    if not args.silencioso:
        show_credentials()


if __name__ == "__main__":
    main()

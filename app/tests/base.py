"""Classe base com os atalhos usados pelos testes.

O nome do arquivo começa com "base" (e não com "test") de propósito: assim o
unittest não tenta executá-lo como se fosse uma suíte de testes.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.testclient import TestClient

from ..database.session import get_connection, init_db
from ..main import app

UTC = timezone.utc


class ApiTestCase(unittest.TestCase):
    """Sobe a aplicação com o banco de teste e oferece métodos de apoio."""

    client: TestClient
    admin: dict
    professor: dict
    outro_professor: dict
    alice: dict
    bob: dict
    curso: dict

    @classmethod
    def setUpClass(cls) -> None:
        init_db()
        cls.client = TestClient(app)
        cls.client.__enter__()  # dispara o lifespan (cria as tabelas)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def setUp(self) -> None:
        """Limpa as tabelas e cria o cenário básico de cada teste."""
        self.clear_tables()
        # A ordem importa: o curso é cadastrado por um administrador.
        self.admin = self.create_user("Administração", "admin@faculdade.edu", "admin", "senha123")
        self.professor = self.create_user(
            "Professora Responsável", "prof@faculdade.edu", "professor", "senha123"
        )
        self.outro_professor = self.create_user(
            "Outro Professor", "outro@faculdade.edu", "professor", "senha123"
        )
        self.curso = self.create_course("Análise e Desenvolvimento de Sistemas", "ADS")
        self.alice = self.create_user("Alice Participante", "alice@faculdade.edu")
        self.bob = self.create_user("Bob Participante", "bob@faculdade.edu")

    # ------------------------------------------------------------------ apoio

    @staticmethod
    def clear_tables() -> None:
        connection = get_connection()
        try:
            for table in ("registrations", "events", "courses", "users"):
                connection.execute(f"DELETE FROM {table}")
            connection.execute(
                "DELETE FROM sqlite_sequence WHERE name IN "
                "('registrations', 'events', 'courses', 'users')"
            )
            connection.commit()
        finally:
            connection.close()

    def create_user(
        self,
        name: str,
        email: str,
        role: str = "participante",
        password: str = "aluno123",
        course_id: Optional[int] = None,
    ) -> dict:
        response = self.client.post(
            "/api/v1/usuarios",
            json={
                "name": name,
                "email": email,
                "password": password,
                "role": role,
                "course_id": course_id,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def create_course(self, name: str, code: str, coordinator_id: Optional[int] = None) -> dict:
        response = self.client.post(
            "/api/v1/cursos",
            headers=self.headers(self.admin["id"]),
            json={"name": name, "code": code, "coordinator_id": coordinator_id},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, email: str, password: str = "senha123") -> dict:
        """Faz login e devolve os cabeçalhos já com o token."""
        response = self.client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        self.assertEqual(response.status_code, 200, response.text)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def headers(user_id: int) -> dict:
        """Forma antiga de identificação, mantida para compatibilidade."""
        return {"X-User-Id": str(user_id)}

    def create_event(
        self,
        *,
        start: Optional[datetime] = None,
        capacity: int = 10,
        duration_hours: float = 4,
        actor: Optional[dict] = None,
        responsible_id: Optional[int] = None,
        course_id: Optional[int] = None,
    ) -> dict:
        actor = actor or self.professor
        responsible_id = responsible_id or self.professor["id"]
        start = start or (datetime.now(UTC) + timedelta(days=3))
        response = self.client.post(
            "/api/v1/eventos",
            headers=self.headers(actor["id"]),
            json={
                "title": "Workshop de Desenvolvimento",
                "description": "Atividade técnica de integração.",
                "start_at": start.isoformat(),
                "location": "Laboratório 01",
                "capacity": capacity,
                "duration_hours": duration_hours,
                "responsible_id": responsible_id,
                "course_id": course_id or self.curso["id"],
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def register(self, event: dict, user: dict, actor: Optional[dict] = None) -> dict:
        actor = actor or user
        response = self.client.post(
            "/api/v1/inscricoes",
            headers=self.headers(actor["id"]),
            json={"user_id": user["id"], "event_id": event["id"]},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

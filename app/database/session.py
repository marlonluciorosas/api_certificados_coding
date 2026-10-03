"""Conexão com o banco SQLite.

Responsabilidades desta camada:
- abrir a conexão com as configurações certas (chaves estrangeiras ligadas);
- oferecer o bloco `transaction()`, que faz commit no final e rollback se der erro;
- criar as tabelas (`init_db`) e limpar os dados quando for preciso (`clear_database`).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ..core.config import settings
from .schema import SCHEMA_SQL

# Ordem usada para limpar as tabelas sem quebrar as chaves estrangeiras.
TABLES_IN_ORDER = ("registrations", "events", "courses", "users")


def get_connection() -> sqlite3.Connection:
    """Abre uma conexão nova, já configurada para a API."""
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        settings.database_path,
        timeout=10,
        isolation_level=None,  # controlamos as transações na mão
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def transaction(immediate: bool = False) -> Iterator[sqlite3.Connection]:
    """Executa um bloco dentro de uma transação.

    Usamos BEGIN IMMEDIATE nas operações que contam registros antes de gravar
    (inscrição, cancelamento, presença). Assim dois pedidos simultâneos não
    conseguem passar pela mesma verificação de vagas.
    """
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    """Cria as tabelas e os índices sem apagar dados existentes."""
    connection = get_connection()
    try:
        connection.executescript(SCHEMA_SQL)
    finally:
        connection.close()


def clear_database() -> None:
    """Apaga todos os registros (usado pelo popular_banco.py --recriar)."""
    with transaction() as connection:
        for table in TABLES_IN_ORDER:
            connection.execute(f"DELETE FROM {table}")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name IN "
            "('registrations', 'events', 'courses', 'users')"
        )


def database_is_empty() -> bool:
    """Diz se ainda não existe nenhum usuário cadastrado."""
    connection = get_connection()
    try:
        total = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        return int(total) == 0
    finally:
        connection.close()
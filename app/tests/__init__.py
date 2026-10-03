"""Configuração dos testes.

Este arquivo é executado ANTES de qualquer teste ser importado, então dá tempo
de apontar o sistema para um banco separado. Assim os testes nunca tocam o
`eventos.db` real do projeto.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "eventos_api_testes.sqlite3"

os.environ["EVENTOS_DB_PATH"] = str(TEST_DATABASE_PATH)
os.environ["EVENTOS_SEED_ON_STARTUP"] = "false"
os.environ["EVENTOS_PASSWORD_ITERATIONS"] = "1000"  # testes mais rápidos

__all__ = ["TEST_DATABASE_PATH"]
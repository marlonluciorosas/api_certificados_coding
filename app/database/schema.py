"""Leitura do arquivo SQL que cria as tabelas."""
from __future__ import annotations

from pathlib import Path

SCHEMA_FILE = Path(__file__).with_name("schema.sql")

# O SQL fica no arquivo schema.sql para ficar mais fácil de ler e de alterar.
SCHEMA_SQL = SCHEMA_FILE.read_text(encoding="utf-8")
"""Configurações do sistema.

Deixei todas as configurações em um lugar só: se for preciso trocar o nome do
arquivo do banco, o tempo de validade do token ou a dificuldade do hash da
senha, basta mexer aqui ou definir a variável de ambiente correspondente.

Variáveis de ambiente aceitas:
    EVENTOS_DB_PATH              caminho do arquivo SQLite
    EVENTOS_SECRET_KEY           chave usada para assinar o token
    EVENTOS_TOKEN_MINUTES        tempo de validade do token (minutos)
    EVENTOS_PASSWORD_ITERATIONS  repetições do PBKDF2
    EVENTOS_SEED_ON_STARTUP      true para popular o banco ao iniciar a API
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Raiz do projeto: .../atividade_fastapi_eventos_organizado
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "eventos.db"


def _env_int(name: str, default: int) -> int:
    """Lê um número inteiro do ambiente; se estiver inválido, usa o padrão."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    """Aceita 1/true/sim/yes/on como verdadeiro."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "sim", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Objeto imutável com as configurações já lidas do ambiente."""

    project_name: str = "Atividade de Victor lalala"
    version: str = "2.0.0"
    author: str = "Victor Ricardo Batista de Araújo"
    course: str = "Análise e Desenvolvimento de Sistemas (ADS)"
    api_prefix: str = "/api/v1"

    database_path: Path = DEFAULT_DATABASE_PATH
    secret_key: str = "chave-de-estudo-trocar-em-producao"
    token_expire_minutes: int = 120
    password_iterations: int = 120_000
    password_min_length: int = 6

    seed_on_startup: bool = False
    default_page_size: int = 50
    max_page_size: int = 200

    @classmethod
    def from_environment(cls) -> "Settings":
        """Monta as configurações misturando os valores padrão com o ambiente."""
        return cls(
            version=os.getenv("EVENTOS_VERSION", cls.version),
            api_prefix=os.getenv("EVENTOS_API_PREFIX", cls.api_prefix),
            database_path=Path(os.getenv("EVENTOS_DB_PATH", str(DEFAULT_DATABASE_PATH))),
            secret_key=os.getenv("EVENTOS_SECRET_KEY", cls.secret_key),
            token_expire_minutes=_env_int(
                "EVENTOS_TOKEN_MINUTES", cls.token_expire_minutes
            ),
            password_iterations=_env_int(
                "EVENTOS_PASSWORD_ITERATIONS", cls.password_iterations
            ),
            seed_on_startup=_env_bool(
                "EVENTOS_SEED_ON_STARTUP", cls.seed_on_startup
            ),
        )


# Objeto pronto para ser importado pelas outras camadas.
settings = Settings.from_environment()
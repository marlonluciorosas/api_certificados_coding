"""Inicializador oficial do trabalho V2 Unifacil.

Uso recomendado:
    python executar.py

Na primeira execução este arquivo cria o ambiente virtual, instala as
bibliotecas, gera uma chave local para o JWT, prepara o banco de demonstração e
inicia o servidor. Nas próximas execuções ele reaproveita o que já existe.
"""
from __future__ import annotations

import os
import platform
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
ENV_FILE = ROOT / ".env"


def venv_python() -> Path:
    """Retorna o executável Python dentro do ambiente virtual."""
    if platform.system().lower().startswith("win"):
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def run(command: list[str], description: str, step: str) -> None:
    """Executa uma etapa e mostra uma mensagem compreensível em caso de erro."""
    print(f"\n[{step}] {description}...", flush=True)
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except FileNotFoundError as error:
        print(f"\nPrograma não encontrado: {command[0]}")
        print("Instale o Python 3.10 ou mais recente e tente novamente.")
        raise SystemExit(1) from error
    except subprocess.CalledProcessError as error:
        print(f"\nNão foi possível concluir: {description} (código {error.returncode}).")
        print("Confira a conexão com a internet e as mensagens acima.")
        raise SystemExit(error.returncode) from error


def ensure_environment_file() -> None:
    """Cria uma configuração local somente se o usuário ainda não tiver uma."""
    if ENV_FILE.exists():
        return
    jwt_key = secrets.token_urlsafe(32)
    ENV_FILE.write_text(
        "# Configuração local criada automaticamente pelo executar.py\n"
        f"EVENTOS_SECRET_KEY={jwt_key}\n"
        "EVENTOS_TOKEN_MINUTES=120\n",
        encoding="utf-8",
    )
    print("      configuração local criada em .env", flush=True)


def main() -> None:
    os.chdir(ROOT)
    print("=" * 68)
    print(" TRABALHO V2 UNIFACIL")
    print(" Inicialização automática para apresentação e entrega")
    print("=" * 68)

    if not venv_python().exists():
        run(
            [sys.executable, "-m", "venv", str(VENV)],
            "criando o ambiente virtual local",
            "1/5",
        )
    else:
        print("\n[1/5] ambiente virtual já existe.", flush=True)

    python = str(venv_python())
    run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-q",
            "-r",
            str(REQUIREMENTS),
        ],
        "instalando ou conferindo as dependências",
        "2/5",
    )

    ensure_environment_file()
    run(
        [python, "-m", "app.database.seed", "--silencioso"],
        "preparando o banco com os cadastros de demonstração",
        "3/5",
    )

    port = os.getenv("EVENTOS_PORT", "8000")
    print("\n[4/5] banco pronto e configurações carregadas.", flush=True)
    print(f"      porta selecionada: {port}", flush=True)
    print("\n[5/5] iniciando o servidor...", flush=True)
    print(f"      Swagger: http://127.0.0.1:{port}/docs", flush=True)
    print(f"      Redoc:   http://127.0.0.1:{port}/redoc", flush=True)
    print("      Para encerrar, pressione Ctrl+C.", flush=True)

    subprocess.run(
        [
            python,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            port,
        ],
        cwd=ROOT,
        check=False,
    )


if __name__ == "__main__":
    main()

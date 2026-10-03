"""Inicializador do Atividade de Victor lalala.

Uso: python executar.py

O script faz tudo sozinho:
1. cria o ambiente virtual (.venv) se ainda não existir;
2. instala/atualiza as dependências do requirements.txt;
3. cria o banco e coloca os dados de exemplo na primeira execução;
4. sobe o servidor em http://127.0.0.1:8000.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
DATABASE = ROOT / "eventos.db"


def venv_python() -> Path:
    if platform.system().lower().startswith("win"):
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def run(command: list[str], description: str, step: str) -> None:
    print(f"\n[{step}] {description}...", flush=True)
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as error:
        print(f"\nNão foi possível concluir: {description} (código {error.returncode}).")
        print("Verifique sua conexão com a internet e tente novamente.")
        raise SystemExit(error.returncode) from error


def main() -> None:
    os.chdir(ROOT)

    if not venv_python().exists():
        run(
            [sys.executable, "-m", "venv", str(VENV)],
            "criando o ambiente virtual local",
            "1/4",
        )

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
        "instalando ou atualizando as dependências",
        "2/4",
    )

    if not DATABASE.exists():
        run(
            [python, "-m", "app.database.seed"],
            "criando o banco com usuários, cursos e eventos de exemplo",
            "3/4",
        )
    else:
        print("\n[3/4] banco de dados já existe (eventos.db).", flush=True)
        print("      Para recriar os exemplos: python popular_banco.py --recriar")

    print("\n[4/4] iniciando o sistema...", flush=True)
    print("Documentação: http://127.0.0.1:8000/docs")
    print("Para encerrar, pressione Ctrl+C.", flush=True)
    subprocess.run(
        [python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT,
        check=False,
    )


if __name__ == "__main__":
    main()
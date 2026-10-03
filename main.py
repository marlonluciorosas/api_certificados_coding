"""Ponto de entrada do projeto.

A aplicação de verdade mora em `app/main.py`, junto do resto do código. Este
arquivo existe apenas para o comando continuar simples:

    uvicorn main:app --reload
"""
from __future__ import annotations

from app.main import app

__all__ = ["app"]


if __name__ == "__main__":  # permite rodar com "python main.py"
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
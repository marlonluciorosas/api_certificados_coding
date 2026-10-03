"""Preenche o banco com usuários, senhas, cursos, eventos e inscrições.

Uso:
    python popular_banco.py             # completa o que estiver faltando
    python popular_banco.py --recriar   # apaga tudo e cria de novo

O código de verdade está em `app/database/seed.py`; este arquivo só facilita a
execução a partir da raiz do projeto.
"""
from __future__ import annotations

from app.database.seed import main

if __name__ == "__main__":
    main()
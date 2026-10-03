"""Atividade de Victor lalala.

Organização das pastas:

    app/api       -> rotas HTTP (v1)
    app/core      -> configurações, segurança e dependências
    app/models    -> modelos de domínio (User, Course, Event, Registration)
    app/schemas   -> validação de entrada/saída (Pydantic)
    app/services  -> regras de negócio
    app/repositories -> consultas SQL
    app/database  -> conexão, tabelas e dados de exemplo
    app/tests     -> testes automatizados
"""

__version__ = "2.0.0"
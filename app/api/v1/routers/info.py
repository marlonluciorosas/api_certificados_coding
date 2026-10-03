"""Rotas de apresentação do sistema (ficam na raiz, sem versão).

São as rotas originais da atividade (`/`, `/sobre`, `/saudacao/{nome}`) mais o
`/health` e a lista de regras implementadas.
"""
from __future__ import annotations

from fastapi import APIRouter

from ....core.config import settings

router = APIRouter(tags=["Informações"])

BUSINESS_RULES = [
    {"codigo": "RN01", "descricao": "Impede inscrição dupla do mesmo usuário no mesmo evento."},
    {"codigo": "RN02", "descricao": "Bloqueia novas inscrições quando a capacidade máxima é atingida."},
    {"codigo": "RN03", "descricao": "Restringe exclusões/edições a Administrador e Professor responsável."},
    {"codigo": "RN04", "descricao": "Permite ao participante agir somente nas próprias inscrições."},
    {"codigo": "RN05", "descricao": "Bloqueia cadastro e edição de eventos com data passada."},
    {"codigo": "RN06", "descricao": "Emite certificado somente com inscrição ativa e presença confirmada."},
    {"codigo": "RN07", "descricao": "Protege dados estruturais de eventos finalizados."},
    {"codigo": "RN08", "descricao": "Mantém e-mail único, sem diferenciar maiúsculas e minúsculas."},
    {"codigo": "RN09", "descricao": "Exige carga horária estritamente maior que zero."},
    {"codigo": "RN10", "descricao": "Exige antecedência mínima de 24 horas para cancelamento."},
]

SECURITY_RULES = [
    {"codigo": "RS01", "descricao": "Login por e-mail e senha; a senha é guardada apenas como hash PBKDF2."},
    {"codigo": "RS02", "descricao": "Token de acesso assinado (HMAC-SHA256) com prazo de validade."},
    {"codigo": "RS03", "descricao": "Senha com no mínimo 6 caracteres, contendo letra e número."},
    {"codigo": "RS04", "descricao": "Participante consulta somente as próprias inscrições."},
    {"codigo": "RS05", "descricao": "O hash da senha nunca aparece nas respostas da API."},
]

EXTRA_RULES = [
    {"codigo": "RC01", "descricao": "Não permite excluir evento que ainda tem inscrições ativas."},
    {"codigo": "RC02", "descricao": "Toda data é gravada em UTC, evitando erro de fuso horário."},
    {"codigo": "RC03", "descricao": "Listagens usam paginação (limit/offset) para não devolver tudo de uma vez."},
]


@router.get("/", tags=["Informações"])
def inicio() -> dict[str, str]:
    """Rota original preservada para compatibilidade com a atividade inicial."""
    return {
        "mensagem": "API do Atividade de Victor lalala funcionando!",
        "aluno": settings.author,
        "documentacao": "/docs",
    }


@router.get("/sobre", tags=["Informações"])
def sobre() -> dict[str, str]:
    return {
        "nome": settings.author,
        "atividade": settings.project_name,
        "curso": settings.course,
        "versao": settings.version,
        "api": settings.api_prefix,
    }


@router.get("/saudacao/{nome}", tags=["Informações"])
def saudacao(nome: str) -> dict[str, str]:
    return {"mensagem": f"Olá, {nome}!"}


@router.get("/health", tags=["Informações"])
def health() -> dict[str, object]:
    """Informa que a API está no ar e mostra um resumo do banco."""
    from ....services import course_service, event_service, registration_service, user_service

    return {
        "status": "ok",
        "versao": settings.version,
        "banco": str(settings.database_path.name),
        "resumo": {
            "usuarios": user_service.count_users(),
            "cursos": course_service.count_courses(),
            "eventos": event_service.count_events(),
            "inscricoes": registration_service.count_registrations(),
        },
    }


@router.get("/regras-negocio", tags=["Informações"])
def regras_negocio() -> dict[str, object]:
    """Lista as regras para facilitar a conferência da atividade."""
    return {
        "total": len(BUSINESS_RULES),
        "regras": BUSINESS_RULES,
        "regras_seguranca": SECURITY_RULES,
        "regras_complementares": EXTRA_RULES,
    }
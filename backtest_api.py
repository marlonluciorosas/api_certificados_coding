"""Backtest da API: testa o sistema de ponta a ponta, com o servidor rodando.

Diferente dos testes automatizados (que usam o TestClient, sem abrir porta),
este script conversa com a API de verdade por HTTP, do mesmo jeito que o
Swagger ou um aplicativo faria. É uma forma de conferir se está tudo de pé
depois de subir o servidor.

Como usar (em dois terminais):

    # terminal 1 - inicia a API
    python executar.py          # ou: uvicorn main:app --reload

    # terminal 2 - roda o backtest
    python backtest_api.py

Também aceita outro endereço:
    EVENTOS_BASE_URL=http://127.0.0.1:9000 python backtest_api.py

O script não depende de ids fixos: ele descobre os usuários pelo login. Assim
pode rodar várias vezes seguidas, porque cria dados com um sufixo de tempo.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx

BASE_URL = os.getenv("EVENTOS_BASE_URL", "http://127.0.0.1:8000")
PREFIX = os.getenv("EVENTOS_API_PREFIX", "/api/v1")
UTC = timezone.utc

# Contas criadas pelo popular_banco.py
ADMIN = ("victor.araujo@faculdade.edu", "admin123")
PROFESSOR = ("rafael.souza@faculdade.edu", "prof123")
PROFESSOR_DE_OUTRO_CURSO = ("juliana.lima@faculdade.edu", "prof123")
ALUNO = ("ana.ribeiro@aluno.faculdade.edu", "aluno123")
OUTRO_ALUNO = ("bruno.ferreira@aluno.faculdade.edu", "aluno123")


class Backtest:
    """Guarda o resultado de cada verificação e no final mostra o resumo."""

    def __init__(self, base_url: str) -> None:
        self.client = httpx.Client(base_url=base_url, timeout=20.0)
        self.passou = 0
        self.falhou = 0
        self.falhas: list[str] = []

    def conferir(self, descricao: str, obtido: object, esperado: object) -> bool:
        """Compara o resultado obtido com o esperado e registra o placar."""
        ok = obtido == esperado
        if ok:
            self.passou += 1
            print(f"  [OK]    {descricao}")
        else:
            self.falhou += 1
            self.falhas.append(descricao)
            print(f"  [FALHA] {descricao} (esperado: {esperado!r} | obtido: {obtido!r})")
        return ok

    def titulo(self, texto: str) -> None:
        print(f"\n== {texto} ==")

    def encerrar(self) -> int:
        total = self.passou + self.falhou
        print("\n" + "=" * 66)
        print(f"BACKTEST CONCLUÍDO: {self.passou}/{total} verificações aprovadas")
        if self.falhas:
            print("\nFalhas encontradas:")
            for descricao in self.falhas:
                print(f"  - {descricao}")
        print("=" * 66)
        return 1 if self.falhou else 0


def fazer_login(backtest: Backtest, conta: tuple[str, str]) -> dict[str, str]:
    """Faz login e devolve os cabeçalhos com o token (ou vazio se falhar)."""
    email, senha = conta
    resposta = backtest.client.post(
        f"{PREFIX}/auth/login", json={"email": email, "password": senha}
    )
    if resposta.status_code != 200:
        return {}
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def descobrir_id(backtest: Backtest, cabecalhos: dict[str, str]) -> int:
    """Pega o id de quem está logado (sem chutar números fixos)."""
    resposta = backtest.client.get(f"{PREFIX}/auth/me", headers=cabecalhos)
    return int(resposta.json()["id"]) if resposta.status_code == 200 else 0


def rodar_backtest() -> int:
    backtest = Backtest(BASE_URL)
    sufixo = int(time.time())  # deixa os dados deste teste sempre únicos
    agora = datetime.now(UTC)

    print(f"Backtest da API em {BASE_URL}")

    # ---------------------------------------------------------------- 1. saúde
    backtest.titulo("1. Rotas de apresentação e saúde do sistema")
    saude = backtest.client.get("/health")
    backtest.conferir("GET /health responde 200", saude.status_code, 200)
    backtest.conferir("status é 'ok'", saude.json().get("status"), "ok")
    backtest.conferir("GET / responde 200", backtest.client.get("/").status_code, 200)
    backtest.conferir("GET /sobre responde 200", backtest.client.get("/sobre").status_code, 200)
    regras = backtest.client.get("/regras-negocio").json()
    backtest.conferir("catálogo tem as 10 regras de negócio", regras["total"], 10)
    backtest.conferir("catálogo lista as regras de segurança", bool(regras["regras_seguranca"]), True)

    # -------------------------------------------------------------- 2. login
    backtest.titulo("2. Login com e-mail e senha")
    admin = fazer_login(backtest, ADMIN)
    professor = fazer_login(backtest, PROFESSOR)
    outro_professor = fazer_login(backtest, PROFESSOR_DE_OUTRO_CURSO)
    aluno = fazer_login(backtest, ALUNO)
    outro_aluno = fazer_login(backtest, OUTRO_ALUNO)
    backtest.conferir("login do administrador devolve token", bool(admin), True)
    backtest.conferir("login do professor devolve token", bool(professor), True)
    backtest.conferir("login do aluno devolve token", bool(aluno), True)
    if not (admin and professor and aluno):
        print("\nSem login não dá para continuar. Rode: python popular_banco.py")
        return backtest.encerrar()

    admin_id = descobrir_id(backtest, admin)
    professor_id = descobrir_id(backtest, professor)
    aluno_id = descobrir_id(backtest, aluno)

    senha_errada = backtest.client.post(
        f"{PREFIX}/auth/login",
        json={"email": ADMIN[0], "password": "senha-errada"},
    )
    backtest.conferir("senha errada responde 401", senha_errada.status_code, 401)

    eu = backtest.client.get(f"{PREFIX}/auth/me", headers=aluno)
    backtest.conferir("GET /auth/me responde 200", eu.status_code, 200)
    backtest.conferir("o token identifica o perfil do aluno", eu.json().get("role"), "participante")
    backtest.conferir("a senha não aparece na resposta", "password" in eu.text, False)

    # --------------------------------------------------------- 3. dados do seed
    backtest.titulo("3. Dados de exemplo no banco")
    usuarios = backtest.client.get(f"{PREFIX}/usuarios?limit=200", headers=admin).json()
    cursos = backtest.client.get(f"{PREFIX}/cursos").json()
    eventos = backtest.client.get(f"{PREFIX}/eventos?limit=200").json()
    backtest.conferir("existem pelo menos 20 usuários", len(usuarios) >= 20, True)
    backtest.conferir("existem pelo menos 4 cursos", len(cursos) >= 4, True)
    backtest.conferir("existem pelo menos 10 eventos", len(eventos) >= 10, True)
    backtest.conferir(
        "algum evento já terminou (histórico para o certificado)",
        any(evento["finished"] for evento in eventos),
        True,
    )
    backtest.conferir(
        "algum evento ainda vai acontecer",
        any(not evento["finished"] for evento in eventos),
        True,
    )
    backtest.conferir("o evento traz o nome do curso", bool(eventos[0]["course_name"]), True)
    backtest.conferir(
        "a listagem de eventos é paginada",
        len(backtest.client.get(f"{PREFIX}/eventos?limit=3").json()),
        3,
    )
    busca_workshop = backtest.client.get(f"{PREFIX}/eventos?busca=Workshop").json()
    backtest.conferir(
        "a busca encontra eventos pelo título",
        any("Workshop" in evento["title"] for evento in busca_workshop),
        True,
    )
    eventos_futuros = backtest.client.get(f"{PREFIX}/eventos?futuros=true").json()
    backtest.conferir(
        "o filtro de futuros não traz evento finalizado",
        all(not evento["finished"] for evento in eventos_futuros),
        True,
    )
    painel = backtest.client.get(f"{PREFIX}/dashboard", headers=aluno)
    backtest.conferir("o dashboard do aluno responde 200", painel.status_code, 200)
    backtest.conferir(
        "o dashboard identifica o usuário logado",
        painel.json().get("user_id") if painel.status_code == 200 else None,
        descobrir_id(backtest, aluno),
    )
    backtest.conferir(
        "listar usuários sem login responde 401",
        backtest.client.get(f"{PREFIX}/usuarios").status_code,
        401,
    )

    # ---------------------------------------------------------------- 4. cursos
    backtest.titulo("4. Cadastro de cursos")
    sigla = f"T{sufixo % 10000}"
    novo_curso = backtest.client.post(
        f"{PREFIX}/cursos",
        headers=professor,
        json={
            "name": f"Curso de Teste {sufixo}",
            "code": sigla,
            "coordinator_id": professor_id,
        },
    )
    backtest.conferir("professor cadastra curso", novo_curso.status_code, 201)
    curso_id = novo_curso.json().get("id") if novo_curso.status_code == 201 else None
    backtest.conferir(
        "a sigla é gravada em maiúsculas",
        novo_curso.json().get("code") if curso_id else None,
        sigla.upper(),
    )
    repetido = backtest.client.post(
        f"{PREFIX}/cursos",
        headers=admin,
        json={"name": "Curso repetido", "code": sigla.lower()},
    )
    backtest.conferir("sigla repetida responde 409", repetido.status_code, 409)
    backtest.conferir(
        "aluno não cadastra curso (403)",
        backtest.client.post(
            f"{PREFIX}/cursos",
            headers=aluno,
            json={"name": "Curso do aluno", "code": f"A{sufixo % 10000}"},
        ).status_code,
        403,
    )

    # -------------------------------------------------------------- 5. usuários
    backtest.titulo("5. Cadastro de usuários e validações de senha")
    email_novo = f"teste.{sufixo}@aluno.faculdade.edu"
    criado = backtest.client.post(
        f"{PREFIX}/usuarios",
        json={
            "name": "Aluno do Backtest",
            "email": email_novo,
            "password": "backtest123",
            "role": "participante",
            "course_id": curso_id,
        },
    )
    backtest.conferir("cadastro de usuário responde 201", criado.status_code, 201)
    aluno_novo_id = criado.json().get("id", 0) if criado.status_code == 201 else 0
    backtest.conferir(
        "o curso do usuário vem na resposta",
        criado.json().get("course_id") if aluno_novo_id else None,
        curso_id,
    )
    token_novo = fazer_login(backtest, (email_novo, "backtest123"))
    backtest.conferir("o usuário novo consegue fazer login", bool(token_novo), True)

    backtest.conferir(
        "e-mail repetido responde 409 (RN08)",
        backtest.client.post(
            f"{PREFIX}/usuarios",
            json={"name": "E-mail repetido", "email": email_novo, "password": "backtest123"},
        ).status_code,
        409,
    )
    backtest.conferir(
        "senha sem número responde 422",
        backtest.client.post(
            f"{PREFIX}/usuarios",
            json={"name": "Senha fraca", "email": f"fraca.{sufixo}@aluno.edu", "password": "abcdef"},
        ).status_code,
        422,
    )

    # --------------------------------------------------------------- 6. eventos
    backtest.titulo("6. Cadastro de eventos")
    evento = backtest.client.post(
        f"{PREFIX}/eventos",
        headers=professor,
        json={
            "title": f"Evento do Backtest {sufixo}",
            "description": "Evento criado automaticamente pelo backtest.",
            "start_at": (agora + timedelta(days=10)).isoformat(),
            "location": "Laboratório 09",
            "capacity": 5,
            "duration_hours": 4,
            "responsible_id": professor_id,
            "course_id": curso_id,
        },
    )
    backtest.conferir("professor cadastra evento", evento.status_code, 201)
    evento_id = evento.json().get("id", 0) if evento.status_code == 201 else 0
    backtest.conferir(
        "o evento calcula as vagas disponíveis",
        evento.json().get("available_spots") if evento_id else None,
        5,
    )

    passado = backtest.client.post(
        f"{PREFIX}/eventos",
        headers=professor,
        json={
            "title": "Evento com data passada",
            "start_at": (agora - timedelta(days=1)).isoformat(),
            "location": "Sala 1",
            "capacity": 10,
            "duration_hours": 2,
            "responsible_id": professor_id,
        },
    )
    backtest.conferir("evento com data passada responde 400 (RN05)", passado.status_code, 400)
    backtest.conferir(
        "carga horária zero responde 422 (RN09)",
        backtest.client.post(
            f"{PREFIX}/eventos",
            headers=professor,
            json={
                "title": "Evento sem carga horária",
                "start_at": (agora + timedelta(days=5)).isoformat(),
                "location": "Sala 2",
                "capacity": 10,
                "duration_hours": 0,
                "responsible_id": professor_id,
            },
        ).status_code,
        422,
    )
    backtest.conferir(
        "curso inexistente responde 400",
        backtest.client.post(
            f"{PREFIX}/eventos",
            headers=professor,
            json={
                "title": "Evento com curso inexistente",
                "start_at": (agora + timedelta(days=5)).isoformat(),
                "location": "Sala 2",
                "capacity": 10,
                "duration_hours": 2,
                "responsible_id": professor_id,
                "course_id": 987654,
            },
        ).status_code,
        400,
    )
    backtest.conferir(
        "aluno não cadastra evento (403)",
        backtest.client.post(
            f"{PREFIX}/eventos",
            headers=aluno,
            json={
                "title": "Evento do aluno",
                "start_at": (agora + timedelta(days=5)).isoformat(),
                "location": "Sala 2",
                "capacity": 10,
                "duration_hours": 2,
                "responsible_id": aluno_id,
            },
        ).status_code,
        403,
    )

    # ----------------------------------------------------------- 7. inscrições
    backtest.titulo("7. Inscrições (RN01 e RN02)")
    inscricao = backtest.client.post(
        f"{PREFIX}/inscricoes",
        headers=token_novo,
        json={"user_id": aluno_novo_id, "event_id": evento_id},
    )
    backtest.conferir("aluno se inscreve no evento", inscricao.status_code, 201)
    inscricao_id = inscricao.json().get("id", 0) if inscricao.status_code == 201 else 0
    backtest.conferir(
        "inscrição duplicada responde 409 (RN01)",
        backtest.client.post(
            f"{PREFIX}/inscricoes",
            headers=token_novo,
            json={"user_id": aluno_novo_id, "event_id": evento_id},
        ).status_code,
        409,
    )
    backtest.conferir(
        "aluno não inscreve outra pessoa (403 - RN04)",
        backtest.client.post(
            f"{PREFIX}/inscricoes",
            headers=token_novo,
            json={"user_id": aluno_id, "event_id": evento_id},
        ).status_code,
        403,
    )

    evento_cheio = backtest.client.post(
        f"{PREFIX}/eventos",
        headers=professor,
        json={
            "title": f"Evento de uma vaga {sufixo}",
            "start_at": (agora + timedelta(days=15)).isoformat(),
            "location": "Sala 7",
            "capacity": 1,
            "duration_hours": 2,
            "responsible_id": professor_id,
        },
    )
    cheio_id = evento_cheio.json()["id"]
    primeira = backtest.client.post(
        f"{PREFIX}/inscricoes",
        headers=token_novo,
        json={"user_id": aluno_novo_id, "event_id": cheio_id},
    )
    segunda = backtest.client.post(
        f"{PREFIX}/inscricoes",
        headers=aluno,
        json={"user_id": aluno_id, "event_id": cheio_id},
    )
    backtest.conferir("primeira inscrição na última vaga é aceita", primeira.status_code, 201)
    backtest.conferir("inscrição sem vaga responde 409 (RN02)", segunda.status_code, 409)

    # --------------------------------------------------------- 8. cancelamentos
    backtest.titulo("8. Cancelamento (RN04 e RN10)")
    evento_curto = backtest.client.post(
        f"{PREFIX}/eventos",
        headers=professor,
        json={
            "title": f"Evento em 5 horas {sufixo}",
            "start_at": (agora + timedelta(hours=5)).isoformat(),
            "location": "Sala 8",
            "capacity": 10,
            "duration_hours": 2,
            "responsible_id": professor_id,
        },
    )
    curto_id = evento_curto.json()["id"]
    inscricao_curta = backtest.client.post(
        f"{PREFIX}/inscricoes",
        headers=token_novo,
        json={"user_id": aluno_novo_id, "event_id": curto_id},
    ).json()

    backtest.conferir(
        "cancelar com menos de 24h responde 400 (RN10)",
        backtest.client.post(
            f"{PREFIX}/inscricoes/{inscricao_curta['id']}/cancelar", headers=token_novo
        ).status_code,
        400,
    )

    com_prazo = backtest.client.post(
        f"{PREFIX}/inscricoes/{inscricao_id}/cancelar", headers=token_novo
    )
    backtest.conferir("cancelar com antecedência responde 200", com_prazo.status_code, 200)
    backtest.conferir(
        "situação da inscrição vira 'cancelada'",
        com_prazo.json().get("status") if com_prazo.status_code == 200 else None,
        "cancelada",
    )
    backtest.conferir(
        "cancelar duas vezes responde 409",
        backtest.client.post(
            f"{PREFIX}/inscricoes/{inscricao_id}/cancelar", headers=token_novo
        ).status_code,
        409,
    )
    backtest.conferir(
        "cancelar inscrição de outro aluno responde 403 (RN04)",
        backtest.client.post(
            f"{PREFIX}/inscricoes/{inscricao_curta['id']}/cancelar", headers=outro_aluno
        ).status_code,
        403,
    )
    backtest.conferir(
        "a vaga volta a ficar disponível depois do cancelamento",
        backtest.client.get(f"{PREFIX}/eventos/{evento_id}").json()["available_spots"],
        5,
    )

    # ------------------------------------------------- 9. presença e certificado
    backtest.titulo("9. Presença e certificado (RN06)")
    evento_antigo = next(
        (item for item in eventos if item["finished"] and item["registrations_count"] > 0),
        None,
    )
    backtest.conferir("existe evento finalizado com inscritos", evento_antigo is not None, True)
    if evento_antigo is not None:
        inscritos = backtest.client.get(
            f"{PREFIX}/inscricoes?event_id={evento_antigo['id']}&status=inscrita&limit=200",
            headers=admin,
        ).json()
        com_presenca = [item for item in inscritos if item["attended"]]
        sem_presenca = [item for item in inscritos if not item["attended"]]
        backtest.conferir("evento finalizado tem presenças confirmadas", len(com_presenca) > 0, True)

        if com_presenca:
            certificado = backtest.client.get(
                f"{PREFIX}/inscricoes/{com_presenca[0]['id']}/certificado", headers=admin
            )
            backtest.conferir("administrador emite o certificado", certificado.status_code, 200)
            backtest.conferir(
                "o certificado traz a carga horária do evento",
                certificado.json().get("workload_hours"),
                evento_antigo["duration_hours"],
            )
            backtest.conferir(
                "o certificado tem identificador CERT-",
                str(certificado.json().get("certificate_id", "")).startswith("CERT-"),
                True,
            )
        if sem_presenca:
            backtest.conferir(
                "certificado sem presença responde 400 (RN06)",
                backtest.client.get(
                    f"{PREFIX}/inscricoes/{sem_presenca[0]['id']}/certificado", headers=admin
                ).status_code,
                400,
            )

        # O próprio aluno dono da inscrição também pode emitir o certificado.
        dono = com_presenca[0] if com_presenca else None
        if dono is not None:
            backtest.conferir(
                "o dono da inscrição também consegue emitir",
                backtest.client.get(
                    f"{PREFIX}/inscricoes/{dono['id']}/certificado",
                    headers=aluno if dono["user_id"] == aluno_id else admin,
                ).status_code,
                200,
            )

    # -------------------------------------------------- 10. permissões finais
    backtest.titulo("10. Permissões e exclusões (RN03, RN07 e RC01)")
    backtest.conferir(
        "professor de outro evento não edita (403)",
        backtest.client.patch(
            f"{PREFIX}/eventos/{cheio_id}", headers=outro_professor, json={"title": "Alterado"}
        ).status_code,
        403,
    )
    backtest.conferir(
        "aluno não exclui evento (403)",
        backtest.client.delete(f"{PREFIX}/eventos/{cheio_id}", headers=aluno).status_code,
        403,
    )
    backtest.conferir(
        "excluir evento com inscrição ativa responde 409 (RC01)",
        backtest.client.delete(f"{PREFIX}/eventos/{cheio_id}", headers=professor).status_code,
        409,
    )
    backtest.conferir(
        "responsável exclui a inscrição (204)",
        backtest.client.delete(
            f"{PREFIX}/inscricoes/{primeira.json()['id']}", headers=professor
        ).status_code,
        204,
    )
    backtest.conferir(
        "depois disso o evento é excluído (204)",
        backtest.client.delete(f"{PREFIX}/eventos/{cheio_id}", headers=professor).status_code,
        204,
    )
    backtest.conferir(
        "o evento excluído não é mais encontrado (404)",
        backtest.client.get(f"{PREFIX}/eventos/{cheio_id}").status_code,
        404,
    )

    evento_finalizado = next((item for item in eventos if item["finished"]), None)
    if evento_finalizado is not None:
        backtest.conferir(
            "evento finalizado não muda local (409 - RN07)",
            backtest.client.patch(
                f"{PREFIX}/eventos/{evento_finalizado['id']}",
                headers=admin,
                json={"location": "Outro lugar"},
            ).status_code,
            409,
        )
        backtest.conferir(
            "evento finalizado aceita ajuste de descrição",
            backtest.client.patch(
                f"{PREFIX}/eventos/{evento_finalizado['id']}",
                headers=admin,
                json={"description": "Descrição ajustada depois do evento."},
            ).status_code,
            200,
        )

    # ------------------------------------------------------ 11. privacidade
    backtest.titulo("11. Privacidade das inscrições (RS04)")
    minhas = backtest.client.get(f"{PREFIX}/inscricoes?limit=200", headers=outro_aluno).json()
    backtest.conferir(
        "aluno vê apenas as próprias inscrições",
        all(item["user_id"] == descobrir_id(backtest, outro_aluno) for item in minhas),
        True,
    )
    backtest.conferir(
        "aluno não consulta inscrição de outro (403)",
        backtest.client.get(
            f"{PREFIX}/inscricoes?user_id={admin_id}", headers=outro_aluno
        ).status_code,
        403,
    )
    backtest.conferir(
        "administrador vê todas as inscrições",
        len(backtest.client.get(f"{PREFIX}/inscricoes?limit=200", headers=admin).json()) > 5,
        True,
    )
    backtest.conferir(
        "token adulterado responde 401",
        backtest.client.get(
            f"{PREFIX}/inscricoes", headers={"Authorization": "Bearer token.adulterado"}
        ).status_code,
        401,
    )
    backtest.conferir(
        "inscrição sem identificação responde 401",
        backtest.client.post(
            f"{PREFIX}/inscricoes", json={"user_id": aluno_id, "event_id": evento_id}
        ).status_code,
        401,
    )

    return backtest.encerrar()


if __name__ == "__main__":
    try:
        sys.exit(rodar_backtest())
    except httpx.ConnectError:
        print(f"\nNão consegui falar com a API em {BASE_URL}.")
        print("Suba o servidor primeiro: python executar.py")
        sys.exit(2)

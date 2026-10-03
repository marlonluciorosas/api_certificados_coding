"""Testes das rotas e das regras de negócio.

Execute com:
    python -m unittest discover -s app/tests -t . -v
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .base import UTC, ApiTestCase
from ..database.session import get_connection


class InformacoesTests(ApiTestCase):
    """Testes das rotas de apresentação."""

    def test_rotas_originais_continuam_funcionando(self) -> None:
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/sobre").status_code, 200)
        self.assertEqual(
            self.client.get("/saudacao/Victor").json()["mensagem"], "Olá, Victor!"
        )
        self.assertEqual(self.client.get("/health").json()["status"], "ok")

    def test_catalogo_de_regras(self) -> None:
        regras = self.client.get("/regras-negocio").json()
        self.assertEqual(regras["total"], 10)
        self.assertEqual(
            {item["codigo"] for item in regras["regras"]},
            {f"RN{numero:02d}" for numero in range(1, 11)},
        )
        self.assertTrue(regras["regras_seguranca"])
        self.assertTrue(regras["regras_complementares"])


class AutenticacaoTests(ApiTestCase):
    """Testes das regras de segurança."""

    def test_login_devolve_token_e_usuario_sem_senha(self) -> None:
        resposta = self.client.post(
            "/api/v1/auth/login",
            json={"email": "alice@faculdade.edu", "password": "aluno123"},
        )
        self.assertEqual(resposta.status_code, 200, resposta.text)
        corpo = resposta.json()
        self.assertTrue(corpo["access_token"])
        self.assertEqual(corpo["user"]["email"], "alice@faculdade.edu")
        self.assertNotIn("password", corpo["user"])
        self.assertNotIn("password_hash", corpo["user"])

    def test_login_com_senha_errada_retorna_401(self) -> None:
        resposta = self.client.post(
            "/api/v1/auth/login",
            json={"email": "alice@faculdade.edu", "password": "errada999"},
        )
        self.assertEqual(resposta.status_code, 401)

    def test_token_da_acesso_as_rotas_protegidas(self) -> None:
        cabecalhos = self.login("alice@faculdade.edu", "aluno123")
        resposta = self.client.get("/api/v1/auth/me", headers=cabecalhos)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()["name"], "Alice Participante")

    def test_token_adulterado_retorna_401(self) -> None:
        cabecalhos = {"Authorization": "Bearer token.invalido"}
        resposta = self.client.get("/api/v1/inscricoes", headers=cabecalhos)
        self.assertEqual(resposta.status_code, 401)

    def test_x_user_id_continua_valendo(self) -> None:
        """Compatibilidade com os primeiros testes da atividade."""
        resposta = self.client.get("/api/v1/usuarios", headers=self.headers(self.alice["id"]))
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(len(resposta.json()), 5)

    def test_senha_fraca_e_recusada_no_cadastro(self) -> None:
        sem_numero = self.client.post(
            "/api/v1/usuarios",
            json={"name": "Teste Senha", "email": "senha@faculdade.edu", "password": "abcdef"},
        )
        curta = self.client.post(
            "/api/v1/usuarios",
            json={"name": "Teste Curta", "email": "curta@faculdade.edu", "password": "ab1"},
        )
        self.assertEqual(sem_numero.status_code, 422)
        self.assertEqual(curta.status_code, 422)


class RegrasDeNegocioTests(ApiTestCase):
    """Um teste para cada regra numerada (RN01 a RN10)."""

    def test_rn01_impede_inscricao_dupla(self) -> None:
        evento = self.create_event()
        primeiro = self.register(evento, self.alice)
        repetido = self.client.post(
            "/api/v1/inscricoes",
            headers=self.headers(self.alice["id"]),
            json={"user_id": self.alice["id"], "event_id": evento["id"]},
        )
        self.assertEqual(primeiro["status"], "inscrita")
        self.assertEqual(repetido.status_code, 409)

    def test_rn02_bloqueia_lotacao_maxima(self) -> None:
        evento = self.create_event(capacity=1)
        self.register(evento, self.alice)
        resposta = self.client.post(
            "/api/v1/inscricoes",
            headers=self.headers(self.bob["id"]),
            json={"user_id": self.bob["id"], "event_id": evento["id"]},
        )
        self.assertEqual(resposta.status_code, 409)
        self.assertIn("capacidade", resposta.json()["detail"])

    def test_rn03_restringe_exclusao_a_gestores(self) -> None:
        evento = self.create_event()
        inscricao = self.register(evento, self.alice)

        proibido_evento = self.client.delete(
            f"/api/v1/eventos/{evento['id']}", headers=self.headers(self.alice["id"])
        )
        proibido_inscricao = self.client.delete(
            f"/api/v1/inscricoes/{inscricao['id']}", headers=self.headers(self.alice["id"])
        )
        self.assertEqual(proibido_evento.status_code, 403)
        self.assertEqual(proibido_inscricao.status_code, 403)

        # Com inscrição ativa a exclusão do evento é bloqueada pela RC01.
        evento_com_inscricao = self.client.delete(
            f"/api/v1/eventos/{evento['id']}", headers=self.headers(self.professor["id"])
        )
        self.assertEqual(evento_com_inscricao.status_code, 409)

        # O professor responsável exclui a inscrição e depois o evento.
        self.assertEqual(
            self.client.delete(
                f"/api/v1/inscricoes/{inscricao['id']}",
                headers=self.headers(self.professor["id"]),
            ).status_code,
            204,
        )
        self.assertEqual(
            self.client.delete(
                f"/api/v1/eventos/{evento['id']}", headers=self.headers(self.professor["id"])
            ).status_code,
            204,
        )

    def test_rn04_participante_cancela_somente_propria_inscricao(self) -> None:
        evento = self.create_event()
        inscricao_alice = self.register(evento, self.alice)
        inscricao_bob = self.register(evento, self.bob)

        sem_permissao = self.client.post(
            f"/api/v1/inscricoes/{inscricao_bob['id']}/cancelar",
            headers=self.headers(self.alice["id"]),
        )
        propria = self.client.post(
            f"/api/v1/inscricoes/{inscricao_alice['id']}/cancelar",
            headers=self.headers(self.alice["id"]),
        )
        self.assertEqual(sem_permissao.status_code, 403)
        self.assertEqual(propria.status_code, 200, propria.text)
        self.assertEqual(propria.json()["status"], "cancelada")

    def test_rn05_bloqueia_evento_com_data_passada_no_cadastro_e_edicao(self) -> None:
        passado = datetime.now(UTC) - timedelta(hours=1)
        criacao = self.client.post(
            "/api/v1/eventos",
            headers=self.headers(self.professor["id"]),
            json={
                "title": "Evento Inválido",
                "description": "Não deve ser criado.",
                "start_at": passado.isoformat(),
                "location": "Sala 1",
                "capacity": 10,
                "duration_hours": 2,
                "responsible_id": self.professor["id"],
            },
        )
        self.assertEqual(criacao.status_code, 400)

        evento = self.create_event()
        edicao = self.client.patch(
            f"/api/v1/eventos/{evento['id']}",
            headers=self.headers(self.professor["id"]),
            json={"start_at": passado.isoformat()},
        )
        self.assertEqual(edicao.status_code, 400)

    def test_rn06_certificado_exige_inscricao_e_presenca(self) -> None:
        evento = self.create_event()
        inscricao = self.register(evento, self.alice)

        sem_presenca = self.client.get(
            f"/api/v1/inscricoes/{inscricao['id']}/certificado",
            headers=self.headers(self.alice["id"]),
        )
        self.assertEqual(sem_presenca.status_code, 400)

        presenca = self.client.patch(
            f"/api/v1/inscricoes/{inscricao['id']}/presenca",
            headers=self.headers(self.professor["id"]),
            json={"attended": True},
        )
        certificado = self.client.get(
            f"/api/v1/inscricoes/{inscricao['id']}/certificado",
            headers=self.headers(self.alice["id"]),
        )
        self.assertEqual(presenca.status_code, 200, presenca.text)
        self.assertEqual(certificado.status_code, 200, certificado.text)
        self.assertEqual(certificado.json()["workload_hours"], 4.0)
        self.assertTrue(certificado.json()["certificate_id"].startswith("CERT-"))

    def test_rn07_evento_finalizado_nao_altera_dados_estruturais(self) -> None:
        evento = self.create_event()
        connection = get_connection()
        try:
            connection.execute(
                "UPDATE events SET start_at = ? WHERE id = ?",
                ((datetime.now(UTC) - timedelta(hours=5)).isoformat(), evento["id"]),
            )
            connection.commit()
        finally:
            connection.close()

        resposta = self.client.patch(
            f"/api/v1/eventos/{evento['id']}",
            headers=self.headers(self.professor["id"]),
            json={"location": "Novo laboratório"},
        )
        self.assertEqual(resposta.status_code, 409)
        self.assertIn("finalizado", resposta.json()["detail"])

        # Campo não estrutural continua editável.
        titulo = self.client.patch(
            f"/api/v1/eventos/{evento['id']}",
            headers=self.headers(self.professor["id"]),
            json={"title": "Workshop Encerrado"},
        )
        self.assertEqual(titulo.status_code, 200, titulo.text)

    def test_rn08_email_e_unico_e_ignora_maiusculas(self) -> None:
        resposta = self.client.post(
            "/api/v1/usuarios",
            json={
                "name": "Duplicado",
                "email": "ADMIN@FACULDADE.EDU",
                "password": "senha123",
                "role": "participante",
            },
        )
        self.assertEqual(resposta.status_code, 409)

    def test_rn09_carga_horaria_deve_ser_maior_que_zero(self) -> None:
        for duracao_invalida in (0, -1):
            resposta = self.client.post(
                "/api/v1/eventos",
                headers=self.headers(self.professor["id"]),
                json={
                    "title": "Carga Horária Inválida",
                    "description": "Teste de validação.",
                    "start_at": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
                    "location": "Sala 1",
                    "capacity": 10,
                    "duration_hours": duracao_invalida,
                    "responsible_id": self.professor["id"],
                },
            )
            self.assertEqual(resposta.status_code, 422)

    def test_rn10_cancelamento_exige_24_horas(self) -> None:
        evento = self.create_event(start=datetime.now(UTC) + timedelta(hours=23))
        inscricao = self.register(evento, self.alice)
        resposta = self.client.post(
            f"/api/v1/inscricoes/{inscricao['id']}/cancelar",
            headers=self.headers(self.alice["id"]),
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("24 horas", resposta.json()["detail"])

    def test_validacoes_de_permissao_e_capacidade_na_edicao(self) -> None:
        evento = self.create_event(capacity=2)
        self.register(evento, self.alice)

        outro_professor = self.client.patch(
            f"/api/v1/eventos/{evento['id']}",
            headers=self.headers(self.outro_professor["id"]),
            json={"title": "Alteração indevida"},
        )
        capacidade_menor = self.client.patch(
            f"/api/v1/eventos/{evento['id']}",
            headers=self.headers(self.professor["id"]),
            json={"capacity": 0},
        )
        self.assertEqual(outro_professor.status_code, 403)
        self.assertEqual(capacidade_menor.status_code, 422)


class CursosTests(ApiTestCase):
    """Testes das rotas novas de curso."""

    def test_cadastro_e_listagem_de_cursos(self) -> None:
        criado = self.client.post(
            "/api/v1/cursos",
            headers=self.headers(self.professor["id"]),
            json={
                "name": "Ciência da Computação",
                "code": "cc",
                "coordinator_id": self.professor["id"],
            },
        )
        self.assertEqual(criado.status_code, 201, criado.text)
        self.assertEqual(criado.json()["code"], "CC")
        self.assertEqual(criado.json()["coordinator_name"], "Professora Responsável")

        lista = self.client.get("/api/v1/cursos").json()
        self.assertEqual(len(lista), 2)

    def test_sigla_repetida_retorna_409(self) -> None:
        resposta = self.client.post(
            "/api/v1/cursos",
            headers=self.headers(self.admin["id"]),
            json={"name": "Outro nome", "code": "ads"},
        )
        self.assertEqual(resposta.status_code, 409)

    def test_participante_nao_cadastra_curso(self) -> None:
        resposta = self.client.post(
            "/api/v1/cursos",
            headers=self.headers(self.alice["id"]),
            json={"name": "Curso do Aluno", "code": "XYZ"},
        )
        self.assertEqual(resposta.status_code, 403)

    def test_evento_com_curso_inexistente_retorna_400(self) -> None:
        resposta = self.client.post(
            "/api/v1/eventos",
            headers=self.headers(self.professor["id"]),
            json={
                "title": "Evento com curso errado",
                "start_at": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
                "location": "Sala 3",
                "capacity": 10,
                "duration_hours": 2,
                "responsible_id": self.professor["id"],
                "course_id": 9999,
            },
        )
        self.assertEqual(resposta.status_code, 400)


class ConsultasTests(ApiTestCase):
    """Testes de listagem, paginação e privacidade."""

    def test_participante_ve_somente_as_proprias_inscricoes(self) -> None:
        evento = self.create_event()
        self.register(evento, self.alice)
        self.register(evento, self.bob)

        do_alice = self.client.get(
            "/api/v1/inscricoes", headers=self.headers(self.alice["id"])
        ).json()
        do_professor = self.client.get(
            "/api/v1/inscricoes", headers=self.headers(self.professor["id"])
        ).json()

        self.assertEqual(len(do_alice), 1)
        self.assertEqual(do_alice[0]["user_id"], self.alice["id"])
        self.assertEqual(len(do_professor), 2)

    def test_participante_nao_espia_inscricoes_de_outro(self) -> None:
        resposta = self.client.get(
            f"/api/v1/inscricoes?user_id={self.bob['id']}",
            headers=self.headers(self.alice["id"]),
        )
        self.assertEqual(resposta.status_code, 403)

    def test_filtros_e_paginacao_das_inscricoes(self) -> None:
        evento = self.create_event()
        self.register(evento, self.alice)
        self.register(evento, self.bob)

        por_evento = self.client.get(
            f"/api/v1/inscricoes?event_id={evento['id']}",
            headers=self.headers(self.admin["id"]),
        ).json()
        self.assertEqual(len(por_evento), 2)

        primeira = self.client.get(
            "/api/v1/inscricoes?limit=1&offset=0",
            headers=self.headers(self.admin["id"]),
        ).json()
        self.assertEqual(len(primeira), 1)

        ativas = self.client.get(
            "/api/v1/inscricoes?status=inscrita",
            headers=self.headers(self.admin["id"]),
        ).json()
        self.assertEqual(len(ativas), 2)

    def test_operacoes_protegidas_exigem_identidade(self) -> None:
        evento = self.create_event()
        resposta = self.client.post(
            "/api/v1/inscricoes",
            json={"user_id": self.alice["id"], "event_id": evento["id"]},
        )
        self.assertEqual(resposta.status_code, 401)

        sem_token = self.client.get("/api/v1/usuarios")
        self.assertEqual(sem_token.status_code, 401)

    def test_evento_traz_nome_do_curso_e_vagas(self) -> None:
        evento = self.create_event(capacity=3)
        self.register(evento, self.alice)
        consultado = self.client.get(f"/api/v1/eventos/{evento['id']}").json()

        self.assertEqual(consultado["course_name"], "Análise e Desenvolvimento de Sistemas")
        self.assertEqual(consultado["registrations_count"], 1)
        self.assertEqual(consultado["available_spots"], 2)
        self.assertFalse(consultado["finished"])
        self.assertIn("end_at", consultado)

    def test_busca_eventos_por_texto_e_filtra_futuros(self) -> None:
        evento = self.create_event()

        encontrados = self.client.get("/api/v1/eventos?busca=Workshop").json()
        self.assertTrue(any(item["id"] == evento["id"] for item in encontrados))

        futuros = self.client.get("/api/v1/eventos?futuros=true").json()
        self.assertTrue(futuros)
        self.assertTrue(all(not item["finished"] for item in futuros))

    def test_dashboard_mostra_a_situacao_do_participante(self) -> None:
        evento = self.create_event()
        self.register(evento, self.alice)

        dashboard = self.client.get(
            "/api/v1/dashboard", headers=self.headers(self.alice["id"])
        )
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        dados = dashboard.json()
        self.assertEqual(dados["user_id"], self.alice["id"])
        self.assertEqual(dados["total_inscricoes"], 1)
        self.assertEqual(dados["inscricoes_ativas"], 1)
        self.assertEqual(dados["certificados_disponiveis"], 0)
        self.assertEqual(len(dados["proximos_eventos"]), 1)

    def test_dashboard_exige_login(self) -> None:
        resposta = self.client.get("/api/v1/dashboard")
        self.assertEqual(resposta.status_code, 401)

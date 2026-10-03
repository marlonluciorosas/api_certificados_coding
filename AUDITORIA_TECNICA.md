# Anotações da atividade (v2 - projeto reorganizado)

**Aluno:** Victor Ricardo Batista de Araújo
**Curso:** Análise e Desenvolvimento de Sistemas (ADS)
**Projeto:** Atividade de Victor lalala

---

## 1. O que tinha no arquivo original

O ZIP recebido tinha uma aplicação FastAPI simples, com as rotas `/`, `/sobre` e
`/saudacao/{nome}`, sem banco de dados, sem usuários e sem eventos.

## 2. O que foi feito na versão anterior (v1)

- banco SQLite criado automaticamente;
- cadastro de usuários com perfil (participante, professor, admin);
- cadastro, consulta, edição e exclusão de eventos;
- inscrições, cancelamentos, presença e certificado;
- validações de data, e-mail, capacidade e carga horária;
- dez regras de negócio (RN01 a RN10) e testes automatizados;
- arquivos `executar.py`, `executar.bat` e `executar.sh`.

## 3. O que mudou nesta versão (v2)

### 3.1 Organização em pastas

O código saiu de quatro arquivos soltos (`api.py`, `services.py`, `schemas.py`,
`database.py`) e passou a ficar separado por responsabilidade:

```text
app/api/v1/routers  -> rotas HTTP (um arquivo por assunto)
app/core            -> config.py, security.py, deps.py
app/models          -> modelos de domínio (User, Course, Event, Registration)
app/schemas         -> validação de entrada e saída (Pydantic)
app/services        -> regras de negócio
app/repositories    -> apenas SQL
app/database        -> conexão, schema.sql, seed.py, conversão de datas
app/tests           -> testes automatizados
app/main.py         -> criação da aplicação FastAPI
```

As rotas agora são versionadas em **`/api/v1`** (as rotas de apresentação
continuam na raiz). O `main.py` da raiz ficou só como atalho para
`uvicorn main:app`.

### 3.2 Funcionalidades novas

| Novidade | Detalhe |
|---|---|
| **Senhas** | Hash PBKDF2-SHA256 com "sal" aleatório; a senha em texto puro nunca é gravada nem devolvida |
| **Login** | `POST /api/v1/auth/login` devolve um token assinado (HMAC-SHA256) com validade de 120 minutos |
| **Token** | Rotas protegidas aceitam `Authorization: Bearer <token>` (e o antigo `X-User-Id` continua valendo) |
| **Cursos** | Tabela `courses` com sigla única e coordenador; eventos e alunos pertencem a um curso |
| **Dados de exemplo** | `popular_banco.py` cria 20 usuários, 4 cursos, 10 eventos e 68 inscrições |
| **Paginação** | Listagens aceitam `limit` e `offset` |
| **Filtros** | Eventos por curso; inscrições por usuário, evento e situação |
| **Backtest** | `backtest_api.py` testa a API rodando, por HTTP (71 verificações) |

### 3.3 Coisas que foram corrigidas

| Problema na v1 | Como ficou na v2 |
|---|---|
| `@app.on_event("startup")` (descontinuado no FastAPI) | `lifespan` (forma recomendada) |
| `init_db()` era executado no momento do `import` do módulo | a criação das tabelas acontece na subida do servidor |
| `PermissionError` (nome igual a um erro embutido do Python) | renomeado para `ForbiddenError`, sem sombra de dúvida |
| Nenhuma senha: qualquer um usava qualquer `X-User-Id` | login com senha + token assinado (o `X-User-Id` ficou só por compatibilidade) |
| `GET /inscricoes` devolvia as inscrições de todos para qualquer pessoa | participante recebe apenas as próprias (RS04) |
| Erro de e-mail duplicado era detectado comparando o texto do erro do SQLite | checagem explícita antes do INSERT + `IntegrityError` como garantia final |
| Exclusão de evento apagava as inscrições junto (CASCADE) sem avisar | RC01: evento com inscrições ativas não é excluído (409) |
| Datas espalhadas em vários formatos | todas as conversões ficaram em `database/converters.py`, sempre em UTC |
| Nomes de tabelas em inglês, rotas em português, misturados sem padrão | o padrão foi documentado: tabelas/campos em inglês, rotas e mensagens em português |
| Nada dizia quantos registros existiam no banco | `/health` mostra o resumo (usuários, cursos, eventos, inscrições) |

### 3.4 Onde ficou cada regra

| Regra | Local no código |
|---|---|
| RN01 | `services/registration_service.py` + `UNIQUE (user_id, event_id)` |
| RN02 | `services/registration_service.py` (transação `BEGIN IMMEDIATE`) |
| RN03 | `services/permissions.py` |
| RN04 | `services/registration_service.py` |
| RN05 | `services/event_service.py` |
| RN06 | `services/registration_service.py` |
| RN07 | `services/event_service.py` (`STRUCTURAL_FIELDS`) |
| RN08 | `services/user_service.py` + `COLLATE NOCASE` na tabela |
| RN09 | `schemas/event.py` + `CHECK (duration_hours > 0)` |
| RN10 | `services/registration_service.py` (`MIN_HOURS_TO_CANCEL = 24`) |
| RS01 a RS05 | `core/security.py`, `core/deps.py`, `services/auth_service.py` |
| RC01 a RC03 | `services/event_service.py`, `database/converters.py`, rotas com `limit`/`offset` |

---

## 4. Testes e backtest

### Testes automatizados

```bash
python -m unittest discover -s app/tests -t . -v
```

**39 testes aprovados.** Eles rodam contra um banco temporário
(`/tmp/eventos_api_testes.sqlite3`), apontado pelo `app/tests/__init__.py`, então
o banco real do projeto não é alterado.

O que é testado: rotas de apresentação, as dez regras de negócio, permissões,
cadastro de curso, curso inexistente, exclusão de evento com inscrições ativas,
privacidade das inscrições, paginação, filtros, senha fraca, senha com hash,
token válido, token expirado e token adulterado.

### Backtest com o servidor rodando

```bash
python executar.py        # terminal 1
python backtest_api.py    # terminal 2
```

**71 de 71 verificações aprovadas.** O resultado completo está em
`backtest_resultado.txt`. O backtest cobre:

1. rotas de apresentação e `/health`;
2. login dos três perfis, senha errada e `/auth/me`;
3. dados de exemplo no banco e bloqueio sem login;
4. cadastro de curso, sigla repetida e permissão do aluno;
5. cadastro de usuário, e-mail repetido e senha fraca;
6. cadastro de evento, data passada, carga horária zero e curso inexistente;
7. inscrição, duplicidade (RN01), terceiros (RN04) e lotação (RN02);
8. cancelamento com e sem prazo (RN10), cancelamento duplo e vaga liberada;
9. presença e certificado com e sem presença (RN06);
10. permissões de edição/exclusão (RN03), evento finalizado (RN07) e RC01;
11. privacidade das inscrições (RS04) e token adulterado;
12. busca de eventos, filtro de eventos futuros e dashboard do usuário.

Como o backtest cria dados com um sufixo de tempo, ele pode rodar várias vezes.
Para voltar ao banco de exemplo "limpo":

```bash
python popular_banco.py --recriar
```

---

## 5. Observação sobre o `X-User-Id`

O `X-User-Id` nasceu como forma simples de identificar o usuário nos primeiros
testes da atividade. Ele **continua funcionando** (as rotas aceitam as duas
formas), mas agora existe login de verdade: senha com hash, token assinado e
prazo de validade. Em um sistema real, o `X-User-Id` seria removido, porque
permitiria que qualquer pessoa se passasse por outro usuário.

## 6. Próximos passos possíveis

- trocar o SQLite por PostgreSQL (basta ajustar `database/session.py`);
- enviar o certificado em PDF (biblioteca `reportlab` ou `fpdf2`);
- criar uma tela em HTML para o aluno se inscrever sem usar o Swagger;
- registrar o e-mail de confirmação da inscrição;
- colocar perfis e permissões mais finos (ex.: coordenador de curso).

# Projeto - Sistema de Gestão de Eventos Acadêmicos 

**Aluno:** Victor Ricardo, Júlio César Ferreira, Marlon Lúcio, Lucas Gabriel, Rhyan Albuquerque, Rayanne França

**Curso:** Análise e Desenvolvimento de Sistemas (ADS)
**Versão:** 2.0.0 (projeto reorganizado em camadas, com login e cursos)

---

## Sobre o projeto

API em FastAPI para gerenciar **usuários**, **cursos**, **eventos**, **inscrições**,
**presença** e **certificados**. O banco é o SQLite (arquivo `eventos.db`, criado
automaticamente) e não precisa instalar servidor de banco.

Nesta versão o projeto foi reorganizado em camadas, ganhou **login com senha**
(hash PBKDF2) e **token de acesso**, além do cadastro de **cursos** ligados aos
eventos e aos alunos. Também foram adicionados uma busca simples de eventos,
filtro de eventos futuros e um painel-resumo para o usuário.

---

## Como iniciar (jeito mais fácil)

### Windows

1. Extraia o ZIP.
2. Abra a pasta do projeto.
3. Dê dois cliques em **`executar.bat`**.
4. Abra <http://127.0.0.1:8000/docs>.

### Linux ou macOS

```bash
chmod +x executar.sh
./executar.sh
```

O `executar.py` cria o ambiente virtual (`.venv`), instala as dependências e, na
primeira execução, **já cria o banco com os dados de exemplo**. Para parar o
servidor, pressione `Ctrl+C`. Na primeira vez é preciso estar com internet.

### Execução manual 

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python popular_banco.py            # cria as tabelas e os dados de exemplo
uvicorn main:app --reload
```

---

## Estrutura de pastas

```text
app/
├── api/
│   └── v1/
│       ├── routers/          # um arquivo de rotas por assunto
│       │   ├── auth.py
│       │   ├── cursos.py
│       │   ├── dashboard.py       # resumo do usuário logado
│       │   ├── eventos.py
│       │   ├── info.py
│       │   ├── inscricoes.py
│       │   └── usuarios.py
│       └── api.py            # junta todos os routers da v1
├── core/
│   ├── config.py             # configurações (banco, token, paginação...)
│   ├── security.py           # hash de senha e token de acesso
│   └── deps.py               # descobre quem está fazendo a requisição
├── models/
│   └── entities.py           # User, Course, Event, Registration
├── schemas/                  # validação de entrada/saída (Pydantic)
│   ├── auth.py
│   ├── course.py
│   ├── event.py
│   ├── registration.py
│   └── user.py
├── services/                 # REGRAS DE NEGÓCIO
│   ├── auth_service.py
│   ├── course_service.py
│   ├── errors.py
│   ├── event_service.py
│   ├── permissions.py
│   ├── registration_service.py
│   └── user_service.py
├── repositories/             # somente SQL
│   ├── course_repository.py
│   ├── event_repository.py
│   ├── registration_repository.py
│   └── user_repository.py
├── database/
│   ├── converters.py         # conversão de datas (UTC)
│   ├── schema.py
│   ├── schema.sql            # criação das tabelas
│   ├── seed.py               # dados de exemplo
│   └── session.py            # conexão e transações
├── tests/                    # testes automatizados
│   ├── base.py
│   ├── test_api.py
│   └── test_security.py
└── main.py                   # cria a aplicação FastAPI

main.py                       # atalho para "uvicorn main:app"
popular_banco.py              # popula o banco pela linha de comando
backtest_api.py               # testa a API rodando, por HTTP
```

**O caminho de um pedido:** `router` → `service` (regra de negócio) → `repository`
(SQL) → `database`. Cada camada só conversa com a de baixo, o que deixa o código
fácil de achar e de corrigir.

---

## Autenticação

1. Faça o cadastro em `POST /api/v1/usuarios` (nome, e-mail, senha, perfil e,
   se quiser, o curso).
2. Faça login em `POST /api/v1/auth/login` e copie o `access_token`.
3. No Swagger, clique em **Authorize** e informe o token.
4. `GET /api/v1/auth/me` mostra quem está logado.

Exemplo com `curl`:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"victor.araujo@faculdade.edu","password":"admin123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/api/v1/eventos -H "Authorization: Bearer $TOKEN"
```

> **Observação:** por ser um projeto de estudo, as rotas também aceitam o
> cabeçalho `X-User-Id: 1` (a forma usada nos primeiros testes da atividade).
> Em um sistema de verdade isso sairia do código, porque qualquer pessoa poderia
> "dizer" que é outro usuário.

---

## Usuários e senhas do banco de exemplo

Criados pelo `popular_banco.py`. Todos já podem ser usados no login:

| Perfil | E-mail | Senha |
|---|---|---|
| admin | `victor.araujo@faculdade.edu` | `admin123` |
| professor (coordenadora ADS) | `carla.mendes@faculdade.edu` | `prof123` |
| professor (ADS) | `rafael.souza@faculdade.edu` | `prof123` |
| professor (CC) | `juliana.lima@faculdade.edu` | `prof123` |
| professor (REDES) | `marcos.prado@faculdade.edu` | `prof123` |
| professor (SI) | `patricia.andrade@faculdade.edu` | `prof123` |
| participante | `ana.ribeiro@aluno.faculdade.edu` | `aluno123` |
| participante | `bruno.ferreira@aluno.faculdade.edu` | `aluno123` |
| participante | `camila.rocha@aluno.faculdade.edu` | `aluno123` |
| participante | `diego.santos@aluno.faculdade.edu` | `aluno123` |
| participante | `eduarda.alves@aluno.faculdade.edu` | `aluno123` |
| participante | `felipe.gomes@aluno.faculdade.edu` | `aluno123` |
| participante | `gabriela.nunes@aluno.faculdade.edu` | `aluno123` |
| participante | `henrique.dias@aluno.faculdade.edu` | `aluno123` |
| participante | `isabela.moraes@aluno.faculdade.edu` | `aluno123` |
| participante | `joao.martins@aluno.faculdade.edu` | `aluno123` |
| participante | `karina.lopes@aluno.faculdade.edu` | `aluno123` |
| participante | `lucas.barbosa@aluno.faculdade.edu` | `aluno123` |
| participante | `mariana.teixeira@aluno.faculdade.edu` | `aluno123` |
| participante | `nathalia.campos@aluno.faculdade.edu` | `aluno123` |

Com o `X-User-Id`, os ids são: **1** = admin, **2 a 6** = professores,
**7 a 20** = participantes.

### O que já existe no banco

- **20 usuários** (1 admin, 5 professores e 14 alunos);
- **4 cursos:** ADS, CC, SI e REDES (cada um com coordenador);
- **10 eventos:** 4 já finalizados e 6 que ainda vão acontecer;
- **68 inscrições:** 62 ativas e 6 canceladas;
- **21 presenças confirmadas** nos eventos que já aconteceram (prontas para
  emitir certificado).

Os eventos que já terminaram servem justamente para testar presença e
certificado; os futuros servem para testar inscrição e cancelamento.

---

## Rotas

Rotas de apresentação (continuam na raiz, sem versão):

| Método | Rota | O que faz |
|---|---|---|
| GET | `/` | Mensagem de boas-vindas |
| GET | `/sobre` | Dados do projeto |
| GET | `/saudacao/{nome}` | Saudação simples |
| GET | `/health` | Estado da API + resumo do banco |
| GET | `/regras-negocio` | Lista as regras implementadas |

Rotas do sistema (prefixo `/api/v1`):

| Método | Rota | Quem pode |
|---|---|---|
| POST | `/auth/login` | Todos |
| GET | `/auth/me` | Usuário logado |
| GET | `/dashboard` | Usuário logado (resumo pessoal) |
| POST | `/usuarios` | Todos (é o cadastro) |
| GET | `/usuarios` | Usuário logado |
| GET | `/usuarios/{id}` | Usuário logado |
| POST | `/cursos` | Admin / Professor |
| GET | `/cursos` | Todos |
| GET | `/cursos/{id}` | Todos |
| POST | `/eventos` | Admin / Professor |
| GET | `/eventos` | Todos (aceita `course_id`, `busca`, `futuros`, `limit`, `offset`) |
| GET | `/eventos/{id}` | Todos |
| PATCH | `/eventos/{id}` | Admin / Professor responsável |
| DELETE | `/eventos/{id}` | Admin / Professor responsável |
| POST | `/inscricoes` | Usuário logado (participante só por si) |
| GET | `/inscricoes` | Logado (participante vê só as suas) |
| POST | `/inscricoes/{id}/cancelar` | Dono da inscrição ou equipe |
| DELETE | `/inscricoes/{id}` | Admin / Professor responsável |
| PATCH | `/inscricoes/{id}/presenca` | Admin / Professor responsável |
| GET | `/inscricoes/{id}/certificado` | Dono, responsável ou admin |

---

## Regras implementadas

### Regras de negócio (as 10 da atividade)

| Código | Regra | Onde está |
|---|---|---|
| RN01 | Sem inscrição duplicada no mesmo evento | `registration_service.create_registration` + `UNIQUE` na tabela |
| RN02 | Bloqueia inscrição sem vagas | `registration_service.create_registration` |
| RN03 | Só admin/responsável edita e exclui | `services/permissions.py` |
| RN04 | Participante só age nas próprias inscrições | `create_registration`, `cancel_registration` |
| RN05 | Sem evento com data passada | `event_service.create_event` e `update_event` |
| RN06 | Certificado exige inscrição ativa + presença | `registration_service.issue_certificate` |
| RN07 | Evento finalizado não muda dados estruturais | `event_service.update_event` |
| RN08 | E-mail único (ignorando maiúsculas) | `user_service.create_user` + `COLLATE NOCASE` |
| RN09 | Carga horária maior que zero | `schemas/event.py` + `CHECK` na tabela |
| RN10 | Cancelamento com 24h de antecedência | `registration_service.cancel_registration` |

### Regras de segurança (novas)

| Código | Regra |
|---|---|
| RS01 | Login por e-mail e senha; senha gravada só como hash PBKDF2 |
| RS02 | Token de acesso assinado (HMAC-SHA256) com prazo de validade |
| RS03 | Senha com no mínimo 6 caracteres, contendo letra e número |
| RS04 | Participante consulta somente as próprias inscrições |
| RS05 | O hash da senha nunca aparece nas respostas da API |

### Regras complementares

| Código | Regra |
|---|---|
| RC01 | Não excluir evento que ainda tem inscrições ativas |
| RC02 | Toda data é gravada em UTC (evita erro de fuso horário) |
| RC03 | Listagens paginadas (`limit`/`offset`) |

---

## Testes

Testes automatizados (usam um banco separado, não mexem no `eventos.db`):

```bash
python -m unittest discover -s app/tests -t . -v
```

Resultado atual: **39 testes aprovados** (rotas, as 10 regras, permissões,
senhas, tokens, cursos, busca, dashboard, paginação e privacidade).

Backtest com o servidor rodando (conversa por HTTP, como o Swagger faria):

```bash
# terminal 1
python executar.py

# terminal 2
python backtest_api.py
```

Resultado atual: **71/71 verificações aprovadas** (o log fica em
`backtest_resultado.txt`). O backtest cria dados de teste com um sufixo de
tempo, então pode ser executado várias vezes seguidas. Para deixar o banco
limpo de novo:

```bash
python popular_banco.py --recriar
```

---

## Problemas comuns

| Situação | O que fazer |
|---|---|
| `ModuleNotFoundError: fastapi` | Ative o ambiente: `source .venv/bin/activate` |
| Porta 8000 ocupada | `uvicorn main:app --port 8001` |
| Quero o banco limpo de novo | `python popular_banco.py --recriar` |
| Esqueci de logar e recebi 401 | Faça `POST /api/v1/auth/login` e use o token |
| Quero ver os dados | `sqlite3 eventos.db "SELECT * FROM users;"` |

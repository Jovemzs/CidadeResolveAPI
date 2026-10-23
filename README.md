# CidadeResolve

> Nunca usou FastAPI, Docker ou Postman? Comece pelo [guia passo a passo](docs/05-guia-passo-a-passo.md).

Web Service REST, com site próprio, para registrar e acompanhar problemas urbanos (buracos, iluminação pública, descarte irregular de lixo) e consultar indicadores de atendimento.

Protótipo acadêmico do Projeto Integrador Web Services. Não há integração oficial com nenhuma prefeitura.

## O que a API faz

- Cadastro e login com dois papéis: **cidadão** e **gestor**.
- Categorias e ocorrências com endereço, bairro e localização opcional.
- Upload de até 5 fotos por ocorrência (JPEG, PNG ou WebP, até 5 MB).
- Fluxo de status com histórico: `ABERTA → EM_ANALISE → EM_ATENDIMENTO → RESOLVIDA`, ou `REJEITADA` a partir de `ABERTA` e `EM_ANALISE`.
- Consulta pública com filtros por bairro, categoria e status.
- Indicadores para o gestor: totais, taxa de resolução e tempo médio de resolução.

O site, servido pela própria API, traz lista de ocorrências com mapa e filtros, registro com ponto no mapa e fotos, acompanhamento do andamento e, para o gestor, mudança de status, categorias e painel de indicadores.

Stack: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, PostgreSQL 16, JWT, pytest, Locust e Docker. Site em HTML, CSS e JavaScript, com mapa Leaflet e OpenStreetMap.

## Rodar localmente

Requisito: Docker com Docker Compose.

```bash
docker compose up --build
```

O comando sobe o PostgreSQL e a API, aplica as migrações e executa a carga inicial (um gestor e três categorias).

| O quê | Onde |
|---|---|
| Site | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| API | http://localhost:8000/api/v1 |
| Verificação | http://localhost:8000/saude |
| PostgreSQL (acesso pelo host) | `localhost:5440`, usuário, senha e banco `cidaderesolve` |

Gestor da carga inicial: `gestor@cidaderesolve.com` / `gestor12345`.

Para ter dados de exemplo (uma cidadã e 7 ocorrências em situações diferentes), com a API ligada:

```bash
docker compose exec api python -m app.demo
```

Cidadã de exemplo: `maria.demo@cidaderesolve.com` / `demo12345`.

Para mudar segredo, credenciais do gestor ou portas, copie `.env.example` para `.env` e ajuste. O compose também aceita `API_PORT` e `DB_PORT` se as portas 8000 ou 5440 estiverem ocupadas.

Para parar: `docker compose down`. Para apagar também o banco e as fotos: `docker compose down -v`.

### Usar o Swagger com login

1. Em `POST /api/v1/auth/login`, envie e-mail e senha e copie o `access_token`.
2. Clique em **Authorize**, cole o token e confirme.

### Rodar a API fora do Docker

```bash
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # Linux/macOS: cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Testes

Os testes usam um banco PostgreSQL separado (`cidaderesolve_test`), recriado a cada execução, e uma pasta temporária para as fotos. O banco de desenvolvimento não é tocado.

```bash
docker compose up -d db
pip install -r requirements-dev.txt
pytest
```

Para usar outro servidor PostgreSQL, defina `TEST_DATABASE_URL`.

Teste de performance (com a API ligada), simulando 200 usuários por 90 segundos:

```bash
locust -f tests/performance/locustfile.py --host http://localhost:8000 --headless -u 200 -r 20 -t 90s --html docs/performance/relatorio.html
```

Resultados e análise em [docs/06-testes.md](docs/06-testes.md).

## Postman

Arquivos em `postman/`:

- `CidadeResolve.postman_collection.json`: todos os endpoints e a pasta **Fluxo de demonstração**.
- `CidadeResolve-Local.postman_environment.json`: ambiente local.
- `CidadeResolve-Render.postman_environment.json`: ambiente público (troque `base_url` pela URL do seu serviço).

Como usar:

1. No Postman, clique em **Import** e selecione os três arquivos.
2. Escolha o ambiente **CidadeResolve - Local**.
3. Rode a pasta **Fluxo de demonstração** em ordem: registro, login, criar ocorrência, enviar foto, gestor muda o status, indicadores. Os tokens e ids são salvos sozinhos nas variáveis do ambiente.
4. Na requisição **Enviar foto**, selecione um arquivo de imagem no campo `arquivo` (há um exemplo em `postman/exemplo.png`).

Pela linha de comando, a partir da raiz do projeto:

```bash
npx newman run postman/CidadeResolve.postman_collection.json -e postman/CidadeResolve-Local.postman_environment.json --folder "Fluxo de demonstração"
```

## Endpoints

Prefixo `/api/v1`.

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/auth/registro` | Cria usuário cidadão | público |
| POST | `/auth/login` | Devolve token JWT | público |
| GET | `/auth/eu` | Dados do usuário logado | logado |
| GET | `/categorias` | Lista categorias (`incluir_inativas` opcional) | público |
| GET | `/categorias/{id}` | Detalha categoria | público |
| POST | `/categorias` | Cria categoria | gestor |
| PUT | `/categorias/{id}` | Altera categoria | gestor |
| DELETE | `/categorias/{id}` | Exclui categoria sem ocorrências | gestor |
| GET | `/ocorrencias` | Lista com filtros e paginação | público |
| GET | `/ocorrencias/{id}` | Detalha, com fotos | público |
| POST | `/ocorrencias` | Cria ocorrência | logado |
| PUT | `/ocorrencias/{id}` | Altera ocorrência | dono ou gestor |
| DELETE | `/ocorrencias/{id}` | Exclui ocorrência | dono ou gestor |
| PATCH | `/ocorrencias/{id}/status` | Muda status | gestor |
| GET | `/ocorrencias/{id}/historico` | Histórico de status | público |
| POST | `/ocorrencias/{id}/fotos` | Envia foto (multipart, campo `arquivo`) | dono ou gestor |
| DELETE | `/fotos/{id}` | Exclui foto | dono ou gestor |
| GET | `/indicadores` | Indicadores (`data_inicio` e `data_fim` opcionais) | gestor |

Filtros de `GET /ocorrencias`: `bairro`, `categoria_id`, `status`, `minhas` (exige login), `pagina` (padrão 1) e `tamanho` (padrão 20, máximo 100).

Erros seguem um formato único:

```json
{ "erro": { "codigo": "TRANSICAO_INVALIDA", "mensagem": "Não é possível ir de RESOLVIDA para ABERTA." } }
```

| Situação | HTTP |
|---|---|
| Arquivo inválido (tipo ou tamanho) | 400 |
| Sem token ou token inválido | 401 |
| Sem permissão | 403 |
| Recurso não encontrado | 404 |
| E-mail já cadastrado, transição inválida, limite de fotos, categoria em uso | 409 |
| Dados inválidos | 422 |

## Configuração

| Variável | Uso | Padrão |
|---|---|---|
| `DATABASE_URL` | Conexão com o PostgreSQL | obrigatória |
| `JWT_SECRET` | Chave de assinatura do token | obrigatória |
| `JWT_EXPIRA_MINUTOS` | Validade do token | 60 |
| `UPLOAD_DIR` | Pasta das fotos | `uploads` |
| `GESTOR_EMAIL`, `GESTOR_SENHA` | Credenciais do gestor da carga inicial | sem gestor se ausentes |
| `CORS_ORIGENS` | Outros endereços autorizados a chamar a API pelo navegador, separados por vírgula. O site da própria API não precisa disso | `http://localhost:5173,http://localhost:3000` |

## Estrutura

```
app/
  main.py          cria a aplicação e registra rotas e handlers de erro
  core/            config, segurança (JWT, hash), dependências, exceções
  db/              sessão e base do SQLAlchemy
  models/          entidades ORM
  schemas/         contratos de entrada e saída (Pydantic)
  repositories/    acesso ao banco, sem regra de negócio
  services/        regras de negócio (permissões, status, fotos, indicadores)
  routers/         HTTP, sem regra de negócio
  seed.py          carga inicial
  demo.py          dados de demonstração
frontend/          site (HTML, CSS e JavaScript), servido na raiz
alembic/           migrações
tests/             testes automatizados (performance/ com o teste de carga)
docs/              documentação do projeto
postman/           coleção e ambientes
```

Cada camada só conhece a imediatamente abaixo: rotas → serviços → repositórios → modelos. Os serviços não conhecem HTTP; as exceções de negócio viram respostas nos handlers de `app/main.py`.

## Deploy no Render

O repositório traz um `render.yaml` que descreve o serviço web (Docker) e o PostgreSQL, ambos no plano gratuito.

1. Envie o repositório para o GitHub.
2. No Render, escolha **New > Blueprint** e selecione o repositório.
3. Informe `GESTOR_EMAIL` e `GESTOR_SENHA` quando solicitado. `DATABASE_URL` e `JWT_SECRET` são preenchidos sozinhos.
4. Aguarde o deploy. A cada início, o contêiner aplica as migrações e a carga inicial.
5. Acesse `https://SEU-SERVICO.onrender.com` (site) e `/docs` (Swagger), e atualize `base_url` no ambiente **CidadeResolve - Render** do Postman.

Sem o Blueprint: crie um PostgreSQL e um Web Service com runtime Docker, e configure as variáveis da tabela acima no painel.

## Limitações

- **Fotos em produção.** O disco do plano gratuito do Render é apagado a cada deploy ou reinício, então as fotos enviadas no ambiente público se perdem. No Docker local elas persistem em volume. Melhoria futura: outra implementação de `ArmazenamentoFotos` usando armazenamento de objetos (S3, Cloudinary).
- Sem notificações ao cidadão e sem detecção de ocorrências duplicadas. Lista completa de limitações e melhorias em [docs/07-resultados-e-impacto.md](docs/07-resultados-e-impacto.md).

## Documentação do projeto

- [Problema](docs/01-problema.md)
- [Requisitos](docs/02-requisitos.md)
- [Modelo de dados](docs/03-modelo-de-dados.md)
- [Cronograma](docs/04-cronograma.md)
- [Guia passo a passo para iniciantes](docs/05-guia-passo-a-passo.md)
- [Testes (funcionais, performance e usabilidade)](docs/06-testes.md)
- [Resultados, impacto e melhorias](docs/07-resultados-e-impacto.md)
- [Boas práticas (camadas, SOLID, segurança, Git)](docs/08-boas-praticas.md)
- [Roteiro de apresentação e vídeo](docs/09-apresentacao.md)
- [Especificação de design](docs/superpowers/specs/2026-10-13-cidaderesolve-api-design.md)

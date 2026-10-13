# CidadeResolve API — Especificação de design

Data: 2026-10-13

## 1. Contexto e objetivo

Moradores têm dificuldade para registrar e acompanhar problemas urbanos como buracos, iluminação pública defeituosa e descarte irregular de lixo. A CidadeResolve API é um Web Service REST que permite cadastrar ocorrências, acompanhar o atendimento e consultar indicadores.

O projeto é um protótipo acadêmico (Projeto Integrador Web Services). Não pressupõe integração oficial com nenhuma prefeitura.

## 2. Escopo

Dentro do escopo:

- Cadastro e login de usuários com dois papéis: cidadão e gestor.
- CRUD de categorias.
- CRUD de ocorrências com categoria e localização.
- Upload de fotos das ocorrências, armazenadas em disco.
- Mudança de status com histórico.
- Consulta de ocorrências com filtros por bairro, categoria e status.
- Indicadores de atendimento.
- Documentação Swagger, coleção Postman, testes automatizados com pytest.
- Docker para desenvolvimento e deploy em serviço gratuito (Render).
- Documentação do projeto: problema, requisitos, modelo de dados e cronograma.

Fora do escopo:

- Interface web ou aplicativo.
- Integração com sistemas de prefeitura.
- Notificações por e-mail ou push.
- Teste de performance (carga).
- Armazenamento de fotos em serviço externo (ver seção 11).

## 3. Stack

| Item | Escolha |
|---|---|
| Linguagem | Python 3.12 |
| Framework | FastAPI |
| ORM e migrações | SQLAlchemy 2 e Alembic |
| Banco de dados | PostgreSQL 16 |
| Validação | Pydantic 2 |
| Autenticação | JWT (PyJWT), senhas com bcrypt |
| Testes | pytest e httpx (TestClient) |
| Containers | Docker e docker-compose |
| Deploy | Render (serviço web + PostgreSQL gratuitos) |

## 4. Arquitetura

Arquitetura em camadas. Cada camada só conhece a camada imediatamente abaixo.

| Camada | Responsabilidade |
|---|---|
| Rotas (`routers`) | HTTP: recebe a requisição, valida com schemas, chama o serviço, devolve a resposta. Sem regra de negócio. |
| Serviços (`services`) | Regras de negócio: permissões, transições de status, limites de fotos, cálculo de indicadores. |
| Repositórios (`repositories`) | Acesso ao banco via SQLAlchemy. Sem regra de negócio. |
| Modelos (`models`) | Entidades ORM. |
| Schemas (`schemas`) | Contratos de entrada e saída (Pydantic). |

Estrutura de pastas:

```
app/
  main.py              # cria a aplicação e registra rotas e handlers de erro
  core/                # config, segurança (JWT, hash), dependências, exceções
  db/                  # sessão e base do SQLAlchemy
  models/
  schemas/
  repositories/
  services/
  routers/
  seed.py              # carga inicial
alembic/
tests/
docs/
postman/
uploads/               # fotos (volume Docker, fora do git)
Dockerfile
docker-compose.yml
```

O armazenamento de fotos fica atrás de uma interface (`ArmazenamentoFotos`) com uma implementação em disco. Isso permite trocar por armazenamento externo no futuro sem alterar os serviços.

## 5. Modelo de dados

### usuario

| Campo | Tipo | Regras |
|---|---|---|
| id | inteiro | chave primária |
| nome | texto (120) | obrigatório |
| email | texto (255) | obrigatório, único |
| senha_hash | texto | obrigatório |
| papel | enum | `CIDADAO` ou `GESTOR`; padrão `CIDADAO` |
| criado_em | data e hora | automático |

### categoria

| Campo | Tipo | Regras |
|---|---|---|
| id | inteiro | chave primária |
| nome | texto (80) | obrigatório, único |
| descricao | texto (255) | opcional |
| ativa | booleano | padrão verdadeiro |

### ocorrencia

| Campo | Tipo | Regras |
|---|---|---|
| id | inteiro | chave primária |
| titulo | texto (120) | obrigatório, mínimo 5 caracteres |
| descricao | texto | obrigatório, mínimo 10 caracteres |
| categoria_id | FK categoria | obrigatório; categoria deve estar ativa |
| autor_id | FK usuario | preenchido com o usuário logado |
| status | enum | padrão `ABERTA` |
| endereco | texto (255) | obrigatório |
| bairro | texto (80) | obrigatório, indexado |
| latitude | decimal | opcional, entre -90 e 90 |
| longitude | decimal | opcional, entre -180 e 180 |
| criado_em | data e hora | automático |
| atualizado_em | data e hora | automático |
| resolvido_em | data e hora | preenchido ao entrar em `RESOLVIDA` |

Latitude e longitude devem ser informadas juntas ou nenhuma das duas.

### foto

| Campo | Tipo | Regras |
|---|---|---|
| id | inteiro | chave primária |
| ocorrencia_id | FK ocorrencia | exclusão em cascata |
| nome_arquivo | texto | nome gerado (UUID + extensão) |
| tipo_conteudo | texto | `image/jpeg`, `image/png` ou `image/webp` |
| tamanho_bytes | inteiro | máximo 5 MB |
| criado_em | data e hora | automático |

### historico_status

| Campo | Tipo | Regras |
|---|---|---|
| id | inteiro | chave primária |
| ocorrencia_id | FK ocorrencia | exclusão em cascata |
| status_anterior | enum | nulo no registro de criação |
| status_novo | enum | obrigatório |
| alterado_por_id | FK usuario | obrigatório |
| comentario | texto (500) | opcional; obrigatório ao rejeitar |
| criado_em | data e hora | automático |

## 6. Regras de negócio

### Fluxo de status

```
ABERTA -> EM_ANALISE -> EM_ATENDIMENTO -> RESOLVIDA
ABERTA -> REJEITADA
EM_ANALISE -> REJEITADA
```

- `RESOLVIDA` e `REJEITADA` são estados finais.
- Qualquer transição fora do fluxo retorna 409.
- Toda mudança de status grava um registro em `historico_status`. A criação da ocorrência grava o registro inicial (`status_anterior` nulo, `status_novo` `ABERTA`).
- Rejeitar exige comentário.

### Permissões

| Ação | Público | Cidadão | Gestor |
|---|---|---|---|
| Listar e ver ocorrências, categorias e histórico | sim | sim | sim |
| Criar ocorrência | não | sim | sim |
| Editar ou excluir ocorrência | não | só as próprias e só em `ABERTA` | sim |
| Enviar ou excluir foto | não | só das próprias e só em `ABERTA` | sim |
| Mudar status | não | não | sim |
| Criar, editar e excluir categoria | não | não | sim |
| Ver indicadores | não | não | sim |

- O cadastro público sempre cria usuário `CIDADAO`. O gestor inicial vem da carga inicial.
- Categoria com ocorrências vinculadas não é excluída: a exclusão retorna 409 e o gestor deve desativá-la (`ativa = false`).

### Fotos

- Tipos aceitos: JPEG, PNG e WebP, validados pelo conteúdo do arquivo e não só pela extensão.
- Tamanho máximo: 5 MB por arquivo.
- Máximo de 5 fotos por ocorrência.
- O arquivo é salvo com nome gerado (UUID), nunca com o nome enviado pelo cliente.
- As fotos são servidas em `/uploads/{nome_arquivo}`; as respostas da API trazem a URL completa.
- Excluir a foto ou a ocorrência remove o arquivo do disco.

## 7. Endpoints

Prefixo: `/api/v1`. Swagger em `/docs`.

### Autenticação

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/auth/registro` | Cria usuário cidadão | público |
| POST | `/auth/login` | Devolve token JWT | público |
| GET | `/auth/eu` | Dados do usuário logado | logado |

### Categorias

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| GET | `/categorias` | Lista categorias (por padrão só ativas) | público |
| GET | `/categorias/{id}` | Detalha categoria | público |
| POST | `/categorias` | Cria categoria | gestor |
| PUT | `/categorias/{id}` | Altera categoria | gestor |
| DELETE | `/categorias/{id}` | Exclui categoria sem ocorrências | gestor |

### Ocorrências

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| GET | `/ocorrencias` | Lista com filtros e paginação | público |
| GET | `/ocorrencias/{id}` | Detalha, com fotos | público |
| POST | `/ocorrencias` | Cria ocorrência | logado |
| PUT | `/ocorrencias/{id}` | Altera ocorrência | dono ou gestor |
| DELETE | `/ocorrencias/{id}` | Exclui ocorrência | dono ou gestor |
| PATCH | `/ocorrencias/{id}/status` | Muda status | gestor |
| GET | `/ocorrencias/{id}/historico` | Histórico de status | público |
| POST | `/ocorrencias/{id}/fotos` | Envia foto (multipart) | dono ou gestor |
| DELETE | `/fotos/{id}` | Exclui foto | dono ou gestor |

Filtros de `GET /ocorrencias`: `bairro` (sem diferenciar maiúsculas), `categoria_id`, `status`, `minhas` (exige login). Paginação: `pagina` (padrão 1) e `tamanho` (padrão 20, máximo 100). Ordenação: mais recentes primeiro. A resposta traz `itens`, `total`, `pagina` e `tamanho`.

As respostas públicas de ocorrência mostram apenas o nome do autor, nunca o e-mail.

### Indicadores

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| GET | `/indicadores` | Indicadores de atendimento | gestor |

Resposta:

- `total_ocorrencias`
- `por_status`: quantidade por status
- `por_categoria`: quantidade por categoria
- `por_bairro`: quantidade por bairro
- `taxa_resolucao`: resolvidas dividido pelo total, em percentual
- `tempo_medio_resolucao_horas`: média entre `criado_em` e `resolvido_em` das resolvidas; nulo se não houver resolvidas

Filtros opcionais: `data_inicio` e `data_fim` (pela data de criação).

## 8. Tratamento de erros

Formato único de resposta de erro:

```json
{ "erro": { "codigo": "TRANSICAO_INVALIDA", "mensagem": "Não é possível ir de RESOLVIDA para ABERTA." } }
```

| Situação | Código HTTP |
|---|---|
| Dados inválidos | 422 |
| Arquivo inválido (tipo ou tamanho) | 400 |
| Sem token ou token inválido | 401 |
| Sem permissão | 403 |
| Recurso não encontrado | 404 |
| E-mail já cadastrado, transição inválida, limite de fotos, categoria em uso | 409 |

As exceções de negócio são definidas em `core` e convertidas em resposta por handlers registrados em `main.py`. Os serviços não conhecem HTTP.

## 9. Testes

Testes automatizados com pytest, usando o TestClient do FastAPI contra um banco PostgreSQL de teste isolado, recriado a cada execução. O armazenamento de fotos usa um diretório temporário.

Cobertura mínima:

- Autenticação: registro, e-mail duplicado, login válido e inválido, rota protegida sem token.
- Categorias: CRUD e bloqueio para não gestores.
- Ocorrências: CRUD, validações, filtros, paginação, regra de dono e de status `ABERTA`.
- Status: cada transição válida, transições inválidas, comentário obrigatório ao rejeitar, gravação do histórico, preenchimento de `resolvido_em`.
- Fotos: upload válido, tipo inválido, tamanho excedido, limite de 5, exclusão.
- Indicadores: valores calculados sobre um conjunto conhecido de ocorrências e acesso restrito.

Testes manuais: coleção Postman com todos os endpoints e um fluxo de demonstração (registro, login, criar ocorrência, enviar foto, gestor muda status, indicadores), com variáveis de ambiente para a URL base e os tokens.

## 10. Ambientes e configuração

Configuração por variáveis de ambiente, com `.env.example` no repositório:

| Variável | Uso |
|---|---|
| `DATABASE_URL` | Conexão com o PostgreSQL |
| `JWT_SECRET` | Chave de assinatura do token |
| `JWT_EXPIRA_MINUTOS` | Validade do token (padrão 60) |
| `UPLOAD_DIR` | Pasta das fotos (padrão `uploads`) |
| `GESTOR_EMAIL`, `GESTOR_SENHA` | Credenciais do gestor da carga inicial |

- Local: `docker compose up` sobe a API e o PostgreSQL, aplica as migrações e executa a carga inicial. As fotos ficam em um volume.
- Produção: a mesma imagem Docker publicada no Render, com PostgreSQL gerenciado e as variáveis configuradas no painel.
- Carga inicial (idempotente): um usuário gestor e as categorias Buraco na via, Iluminação pública e Descarte irregular de lixo.

## 11. Limitações e melhorias futuras

- **Persistência das fotos em produção.** O disco do plano gratuito do Render é apagado a cada novo deploy ou reinício, então as fotos enviadas no ambiente público são perdidas. No Docker local elas persistem em volume. Melhoria futura: nova implementação de `ArmazenamentoFotos` usando armazenamento de objetos (por exemplo S3 ou Cloudinary).
- **Teste de performance.** Não há teste de carga. Melhoria futura: script com Locust ou k6 e relatório de resultados.
- Notificações ao cidadão a cada mudança de status.
- Detecção de ocorrências duplicadas por proximidade geográfica.
- Interface web ou aplicativo consumindo a API.

## 12. Documentação do projeto

Arquivos em `docs/`:

- `01-problema.md`: definição do problema, dor do público-alvo, causas e efeitos.
- `02-requisitos.md`: requisitos funcionais e não funcionais.
- `03-modelo-de-dados.md`: entidades, relacionamentos e diagrama.
- `04-cronograma.md`: planejamento e cronograma de trabalho.

O `README.md` traz a visão geral, como rodar localmente, como executar os testes, como importar a coleção Postman e como fazer o deploy.

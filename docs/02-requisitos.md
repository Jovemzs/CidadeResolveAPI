# 2. Requisitos

Papéis: **público** (sem login), **cidadão** e **gestor**.

## Requisitos funcionais

### Usuários e autenticação

| Id | Requisito |
|---|---|
| RF01 | O sistema deve permitir o cadastro de usuários com nome, e-mail e senha. O cadastro público sempre cria um usuário com papel cidadão. |
| RF02 | O sistema não deve permitir dois usuários com o mesmo e-mail. |
| RF03 | O sistema deve autenticar o usuário por e-mail e senha e devolver um token JWT. |
| RF04 | O sistema deve permitir que o usuário logado consulte os próprios dados. |
| RF05 | O gestor inicial deve ser criado pela carga inicial, a partir de variáveis de ambiente. |

### Categorias

| Id | Requisito |
|---|---|
| RF06 | Qualquer pessoa pode listar e detalhar categorias. A listagem traz, por padrão, só as ativas. |
| RF07 | O gestor pode criar, alterar e excluir categorias. |
| RF08 | Uma categoria com ocorrências vinculadas não pode ser excluída; o gestor deve desativá-la. |

### Ocorrências

| Id | Requisito |
|---|---|
| RF09 | O usuário logado pode criar uma ocorrência com título, descrição, categoria ativa, endereço, bairro e, opcionalmente, latitude e longitude (as duas juntas ou nenhuma). |
| RF10 | Toda ocorrência nasce com status `ABERTA` e tem como autor o usuário logado. |
| RF11 | Qualquer pessoa pode listar ocorrências com filtros por bairro (sem diferenciar maiúsculas), categoria e status, com paginação e das mais recentes para as mais antigas. |
| RF12 | O usuário logado pode filtrar a lista para ver só as próprias ocorrências. |
| RF13 | Qualquer pessoa pode detalhar uma ocorrência, incluindo as fotos. |
| RF14 | O cidadão pode alterar e excluir apenas as próprias ocorrências e apenas enquanto estiverem `ABERTA`. O gestor pode alterar e excluir qualquer ocorrência. |
| RF15 | As respostas públicas mostram apenas o nome do autor, nunca o e-mail. |

### Status e histórico

| Id | Requisito |
|---|---|
| RF16 | Apenas o gestor pode mudar o status de uma ocorrência. |
| RF17 | As mudanças seguem o fluxo `ABERTA → EM_ANALISE → EM_ATENDIMENTO → RESOLVIDA`, com `ABERTA → REJEITADA` e `EM_ANALISE → REJEITADA`. `RESOLVIDA` e `REJEITADA` são estados finais. Qualquer outra transição é recusada. |
| RF18 | Rejeitar uma ocorrência exige comentário. |
| RF19 | Toda mudança de status, inclusive a criação, gera um registro de histórico com status anterior, status novo, responsável, comentário e data. |
| RF20 | Ao entrar em `RESOLVIDA`, a ocorrência registra a data e a hora da resolução. |
| RF21 | Qualquer pessoa pode consultar o histórico de status de uma ocorrência. |

### Fotos

| Id | Requisito |
|---|---|
| RF22 | O dono da ocorrência (enquanto `ABERTA`) e o gestor podem enviar e excluir fotos. |
| RF23 | São aceitos arquivos JPEG, PNG e WebP, identificados pelo conteúdo, com até 5 MB cada. |
| RF24 | Cada ocorrência pode ter no máximo 5 fotos. |
| RF25 | Excluir a foto ou a ocorrência remove o arquivo armazenado. |

### Indicadores

| Id | Requisito |
|---|---|
| RF26 | O gestor pode consultar: total de ocorrências, quantidade por status, por categoria e por bairro, taxa de resolução e tempo médio de resolução em horas. |
| RF27 | Os indicadores podem ser filtrados por período (data de criação). |

## Requisitos não funcionais

| Id | Categoria | Requisito |
|---|---|---|
| RNF01 | Arquitetura | API REST com JSON, prefixo `/api/v1`, organizada em camadas (rotas, serviços, repositórios, modelos e schemas). |
| RNF02 | Tecnologia | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2 e PostgreSQL 16. |
| RNF03 | Segurança | Senhas guardadas apenas como hash bcrypt. Autenticação por token JWT com validade configurável. |
| RNF04 | Segurança | Arquivos enviados são gravados com nome gerado pelo servidor (UUID), nunca com o nome enviado pelo cliente. |
| RNF05 | Privacidade | O e-mail dos usuários não aparece em respostas públicas. |
| RNF06 | Usabilidade da API | Erros seguem um formato único: `{"erro": {"codigo": "...", "mensagem": "..."}}`, com os códigos HTTP 400, 401, 403, 404, 409 e 422. |
| RNF07 | Documentação | Documentação interativa (Swagger) em `/docs` e coleção Postman com todos os endpoints. |
| RNF08 | Qualidade | Testes automatizados com pytest cobrindo autenticação, categorias, ocorrências, status, fotos e indicadores, em banco PostgreSQL isolado. |
| RNF09 | Portabilidade | Execução local com um comando (`docker compose up`), incluindo migrações e carga inicial. |
| RNF10 | Implantação | A mesma imagem Docker é publicada em serviço gratuito (Render) com PostgreSQL gerenciado. |
| RNF11 | Configuração | Toda configuração sensível vem de variáveis de ambiente; nenhum segredo fica no repositório. |
| RNF12 | Manutenibilidade | O armazenamento de fotos fica atrás de uma interface, permitindo trocar o disco por um serviço externo sem alterar as regras de negócio. |

## Regras de permissão

| Ação | Público | Cidadão | Gestor |
|---|---|---|---|
| Listar e ver ocorrências, categorias e histórico | sim | sim | sim |
| Criar ocorrência | não | sim | sim |
| Editar ou excluir ocorrência | não | só as próprias e só em `ABERTA` | sim |
| Enviar ou excluir foto | não | só das próprias e só em `ABERTA` | sim |
| Mudar status | não | não | sim |
| Criar, editar e excluir categoria | não | não | sim |
| Ver indicadores | não | não | sim |

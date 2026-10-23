# Guia passo a passo: rodar, testar e entregar a CidadeResolve

Este guia é para quem nunca usou FastAPI, Docker ou Postman. Basta seguir na ordem e copiar os comandos.

## 1. O que é este projeto, em poucas palavras

A CidadeResolve é um **backend**: um programa que fica rodando num servidor e responde a pedidos. Ainda não tem tela; a tela (front-end) é a próxima fase.

Pense num restaurante:

| Peça | No restaurante | No projeto |
|---|---|---|
| Banco de dados (PostgreSQL) | A despensa, onde tudo fica guardado | Guarda usuários, ocorrências, fotos e histórico |
| API (FastAPI) | O garçom, que recebe o pedido e traz a resposta | Recebe pedidos como "crie esta ocorrência" e responde |
| Postman | Um cliente de teste que faz pedidos ao garçom | Programa para mandar pedidos à API e ver a resposta |
| Swagger (`/docs`) | O cardápio, com tudo o que dá para pedir | Página no navegador que lista e testa cada pedido |
| Docker | Uma cozinha pronta, montada igual em qualquer lugar | Liga o banco e a API com um único comando |

O que a API faz: o **cidadão** cria uma conta, registra um problema da cidade (buraco, poste apagado, lixo) com foto e acompanha o andamento. O **gestor** muda o status (em análise, em atendimento, resolvida ou rejeitada) e vê os números de atendimento.

## 2. Instalar os programas (uma vez só)

1. **Git**: https://git-scm.com/download/win. Instale com as opções padrão.
2. **Docker Desktop**: https://www.docker.com/products/docker-desktop. Instale, reinicie o computador se pedir e abra o Docker Desktop. Espere aparecer "Engine running" no canto inferior esquerdo.
3. **Postman Desktop**: https://www.postman.com/downloads (você já tem).

Não é preciso instalar Python nem PostgreSQL: o Docker cuida disso.

## 3. Baixar o projeto

Abra o **Prompt de Comando** (tecla Windows, digite `cmd`, Enter) e rode:

```bash
cd %USERPROFILE%\Documents
git clone https://github.com/Jovemzs/CidadeResolveAPI.git
cd CidadeResolveAPI
```

Se já tiver baixado antes, entre na pasta e atualize com `git pull`.

## 4. Ligar a API

Com o Docker Desktop aberto, dentro da pasta do projeto:

```bash
docker compose up --build
```

Na primeira vez demora alguns minutos. Está pronto quando aparecer:

```
Uvicorn running on http://0.0.0.0:8000
```

Deixe essa janela aberta: fechá-la desliga a API. Para desligar, aperte `Ctrl + C`. Para ligar de novo depois, use `docker compose up` (sem `--build`).

Confira no navegador:

| Endereço | O que deve aparecer |
|---|---|
| http://localhost:8000/saude | `{"status":"ok"}` |
| http://localhost:8000/docs | A página do Swagger, com a lista de todos os pedidos |

## 5. Testar pelo navegador (Swagger)

É o jeito mais rápido de ver a API funcionando, sem instalar nada.

1. Abra http://localhost:8000/docs.
2. Clique em **POST /api/v1/auth/login** → **Try it out**.
3. No corpo, coloque o gestor que já vem cadastrado e clique em **Execute**:
   ```json
   { "email": "gestor@cidaderesolve.com", "senha": "gestor12345" }
   ```
4. Na resposta, copie o texto longo de `access_token` (sem as aspas).
5. Clique no botão **Authorize** (cadeado, no topo), cole o token e confirme. A partir daí, os pedidos saem como gestor.
6. Teste **GET /api/v1/categorias** → **Try it out** → **Execute**: aparecem as três categorias.
7. Teste **POST /api/v1/ocorrencias** com este corpo:
   ```json
   {
     "titulo": "Buraco grande na rua",
     "descricao": "Buraco fundo em frente ao número 120.",
     "categoria_id": 1,
     "endereco": "Rua das Flores, 120",
     "bairro": "Centro"
   }
   ```
8. Teste **GET /api/v1/indicadores** para ver os números.

Códigos que aparecem na resposta: **200/201/204** deu certo; **401** falta login; **403** sem permissão; **404** não existe; **409** conflito (por exemplo, e-mail já cadastrado); **422** dado preenchido errado. A mensagem de erro sempre explica o motivo.

## 6. Testar pelo Postman (exigência do projeto)

### Importar (uma vez só)

1. Abra o Postman e clique em **Import**.
2. Arraste os três arquivos `.json` da pasta `postman` do projeto.
3. No canto superior direito, troque **No environment** por **CidadeResolve - Local**.

### Rodar a demonstração completa

1. Na barra da esquerda, abra a coleção **CidadeResolve API** e a pasta **Fluxo de demonstração**.
2. Clique nos três pontinhos da pasta → **Run folder** → **Run CidadeResolve API**.
3. As 14 etapas devem ficar verdes. Elas fazem, em ordem: cria um cidadão, faz login, cria ocorrência, envia foto, o gestor muda o status até "resolvida" e mostra os indicadores.

A etapa **06. Enviar foto** precisa de um arquivo: abra essa requisição, vá em **Body**, e no campo `arquivo` clique em **Select files** e escolha `postman/exemplo.png` (ou qualquer foto JPEG ou PNG).

### Fazer pedidos um por um

As outras pastas (Autenticação, Categorias, Ocorrências, Fotos, Indicadores) têm um pedido para cada função da API. Clique no pedido e em **Send**. Os tokens e números de id são preenchidos sozinhos quando você roda o fluxo de demonstração antes.

## 7. Ver o banco de dados (exigência do projeto)

Use um programa de banco, como o **DBeaver** (https://dbeaver.io/download) ou o **pgAdmin**. Crie uma conexão PostgreSQL com:

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Porta | `5440` |
| Banco | `cidaderesolve` |
| Usuário | `cidaderesolve` |
| Senha | `cidaderesolve` |

As tabelas são `usuario`, `categoria`, `ocorrencia`, `foto` e `historico_status`. Depois de rodar o fluxo do Postman, abra `ocorrencia` e `historico_status` e você verá os registros criados. As senhas aparecem só como código embaralhado (hash), de propósito.

## 8. Rodar os testes automáticos (opcional)

São 110 testes que conferem todas as regras sozinhos. Precisa do Python 3.12 instalado.

```bash
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
```

O final deve mostrar `110 passed`.

## 9. Colocar na internet (Render)

1. Crie uma conta gratuita em https://render.com, entrando com a conta do GitHub dona do repositório.
2. Clique em **New** → **Blueprint** e escolha o repositório `CidadeResolveAPI`.
3. O Render vai pedir três valores:
   - `GESTOR_EMAIL`: o e-mail do gestor (por exemplo, `gestor@cidaderesolve.com`).
   - `GESTOR_SENHA`: uma senha forte, que só o grupo saiba.
   - `CORS_ORIGENS`: por enquanto, deixe `http://localhost:5173`. Quando o front-end estiver no ar, coloque o endereço dele aqui.
4. Clique em **Apply** e espere o deploy terminar (uns 5 a 10 minutos).
5. Abra `https://NOME-DO-SERVICO.onrender.com/docs`.
6. No Postman, escolha o ambiente **CidadeResolve - Render**, troque `base_url` pelo endereço do Render e rode o fluxo de demonstração de novo.

Avisos do plano gratuito:

- Depois de uns 15 minutos sem uso o serviço "dorme", e o primeiro pedido demora cerca de 1 minuto. Antes de apresentar, abra `/saude` e espere responder.
- Fotos enviadas no Render somem a cada novo deploy. Isso já está documentado como limitação do projeto.

## 10. Problemas comuns

| Problema | Solução |
|---|---|
| `docker` não é reconhecido, ou erro de "pipe" ou "daemon" | O Docker Desktop não está aberto. Abra e espere "Engine running". |
| `port is already allocated` | Outra coisa usa a porta. Rode `set API_PORT=8001` e `set DB_PORT=5441` antes do `docker compose up` e use as portas novas nos endereços. |
| Postman dá `Could not send request` | A API não está ligada. Volte ao passo 4. |
| Postman responde 401 | Rode antes o login (ou o fluxo de demonstração) para gerar o token. |
| Quero zerar o banco e começar de novo | `docker compose down -v` e depois `docker compose up`. Apaga todos os dados de teste. |

## 11. O que entregar ao professor

1. O link do repositório: https://github.com/Jovemzs/CidadeResolveAPI.
2. O link público do Render (`.../docs`), depois do passo 9.
3. A coleção Postman (pasta `postman/`), com a demonstração rodando verde.
4. Os documentos da pasta `docs/`: problema, requisitos, modelo de dados e cronograma.
5. Prints sugeridos: Swagger aberto, Runner do Postman todo verde, tabelas no DBeaver e testes passando.

## 12. Informações que preciso de vocês

Para fechar o backend e começar o front-end, respondam no chat (pode ser em tópicos, do jeito que der):

**Sobre a entrega**

1. O **enunciado do professor** (PDF, print ou texto). É o mais importante: confiro se não falta nenhum item obrigatório. Pode salvar na pasta `docs/` do projeto ou colar no chat.
2. **Data de entrega e da apresentação**, e os **nomes dos integrantes**, para ajustar o cronograma (`docs/04-cronograma.md`).
3. Se o professor exige **alguma tecnologia** específica no front-end (React, HTML puro etc.) ou se é livre.

**Sobre o deploy**

4. Quem vai criar a conta no **Render**. Siga o passo 9 e me mande o link gerado, ou o erro que aparecer. Nunca mande senhas pelo chat.

**Sobre o front-end (próxima fase)**

5. Preferências visuais: cores, logo, algum site que vocês achem bonito como referência. Se não tiverem, eu proponho.
6. Quais telas são indispensáveis. A sugestão inicial:
   - Cidadão: cadastro e login, mapa ou lista de ocorrências com filtros, criar ocorrência com foto, "minhas ocorrências" com o andamento.
   - Gestor: painel com as ocorrências para mudar o status, gestão de categorias e tela de indicadores com gráficos.

O backend já está pronto para o front-end: ele aceita pedidos vindos de um site no navegador (configuração `CORS_ORIGENS`).

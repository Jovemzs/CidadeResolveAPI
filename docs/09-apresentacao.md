# 9. Roteiro de apresentação e vídeo

Tempo sugerido: **10 minutos** de apresentação e **5 minutos** de demonstração. Adapte ao tempo que o professor definir.

## Antes de apresentar (checklist)

- [ ] Abrir o site publicado e esperar carregar (o plano gratuito "dorme"; a primeira visita demora cerca de 1 minuto).
- [ ] Ter a demonstração pronta: `docker compose exec api python -m app.demo` no ambiente local, ou cadastrar 3 ou 4 ocorrências no ambiente publicado.
- [ ] Postman aberto, com o ambiente certo selecionado.
- [ ] DBeaver (ou pgAdmin) conectado ao banco, com a tabela `ocorrencia` aberta.
- [ ] Uma foto no celular ou no computador para enviar ao vivo.
- [ ] Contas: cidadã de exemplo `maria.demo@cidaderesolve.com` / `demo12345` e o gestor.

## Slides

Um slide por tópico, com pouco texto e uma imagem ou captura de tela em cada.

| # | Slide | O que falar | Imagem sugerida |
|---|---|---|---|
| 1 | **CidadeResolve** | Nome do projeto, disciplina e autor | Logo (a placa azul) |
| 2 | **O problema** | Buraco, poste apagado e lixo: o morador vê primeiro, mas não sabe onde avisar nem tem retorno | Foto de um buraco ou poste apagado |
| 3 | **Causas e efeitos** | Canais dispersos, sem ciclo de vida, sem histórico, sem dados. Efeito: demora, retrabalho, sensação de abandono | Diagrama causa → efeito |
| 4 | **A solução** | Um Web Service REST: registrar, acompanhar e medir. Um site que consome a API | Captura da lista com mapa |
| 5 | **Requisitos** | Dois papéis (cidadão e gestor), CRUD completo, fluxo de status, fotos, indicadores | Tabela de permissões |
| 6 | **Arquitetura** | Python + FastAPI, PostgreSQL, camadas, Docker, Render | Diagrama de camadas de [08-boas-praticas.md](08-boas-praticas.md) |
| 7 | **Modelo de dados** | Cinco tabelas e seus relacionamentos | Diagrama de [03-modelo-de-dados.md](03-modelo-de-dados.md) |
| 8 | **Fluxo de status** | Cinco situações, transições bloqueadas, histórico | Diagrama de estados |
| 9 | **Demonstração** | (ao vivo, ver abaixo) | |
| 10 | **Testes** | 117 testes automatizados, Postman, Swagger, teste de carga com 200 usuários (mediana de 14 ms) | Captura do pytest e do relatório do Locust |
| 11 | **Boas práticas** | Camadas, SOLID, segurança, Git | Tabela SOLID |
| 12 | **Resultados e próximos passos** | Como cada causa foi atacada; melhorias propostas | Tabela de [07-resultados-e-impacto.md](07-resultados-e-impacto.md) |
| 13 | **Obrigado** | Links do repositório e do site | QR code do site |

## Demonstração ao vivo (5 minutos)

Ordem pensada para contar uma história, do cidadão ao gestor:

1. **Site, como visitante**: mostrar a lista, o mapa e filtrar por bairro. Abrir uma ocorrência resolvida e mostrar a linha de andamento e o histórico.
2. **Site, como cidadão**: entrar como Maria, registrar um problema novo marcando o ponto no mapa e enviando uma foto.
3. **Site, como gestor**: entrar como gestor, abrir a ocorrência recém-criada, movê-la para "em análise" com um comentário. Mostrar que tentar pular etapas não é permitido.
4. **Painel**: mostrar os indicadores atualizados.
5. **Swagger** (`/docs`): mostrar que a API está documentada e pode ser testada pelo navegador.
6. **Postman**: rodar a pasta *Fluxo de demonstração* pelo Runner e mostrar as 14 etapas verdes.
7. **Banco**: no DBeaver, atualizar a tabela `historico_status` e mostrar os registros que acabaram de ser gravados.

## Roteiro do vídeo (3 a 5 minutos)

Gravação de tela com narração. No Windows, a Barra de Jogos (`Windows + G`) ou o OBS Studio (gratuito) servem para gravar.

| Tempo | Cena | Narração |
|---|---|---|
| 0:00–0:30 | Foto de rua com buraco; depois, logo do CidadeResolve | "Todo mundo já viu um buraco ou um poste apagado e não soube onde avisar. O CidadeResolve resolve isso." |
| 0:30–1:00 | Lista de ocorrências com mapa | "Qualquer pessoa vê os problemas registrados na cidade, filtra por bairro e acompanha cada um." |
| 1:00–2:00 | Cadastro e registro de ocorrência com foto e mapa | "O cidadão cria uma conta e registra o problema em poucos passos, com foto e localização." |
| 2:00–2:45 | Gestor mudando o status; linha de andamento | "A equipe atualiza o andamento, sempre seguindo o fluxo, e cada mudança fica no histórico." |
| 2:45–3:15 | Painel de indicadores | "O gestor acompanha a taxa de resolução, o tempo médio e onde estão os problemas." |
| 3:15–4:00 | Swagger, Postman e terminal com testes | "Por trás, uma API REST em Python com FastAPI e PostgreSQL, documentada no Swagger, testada com Postman e com 117 testes automatizados." |
| 4:00–4:30 | Links do repositório e do site | "O código está no GitHub e o sistema está publicado. Obrigado!" |

## Perguntas que podem aparecer

| Pergunta | Resposta curta |
|---|---|
| Por que FastAPI? | Gera a documentação Swagger sozinha a partir do código, valida os dados de entrada e é rápido. |
| Onde ficam as fotos? | Em disco, atrás de uma interface. Trocar por armazenamento na nuvem não exige mudar as regras. |
| Como garante que o cidadão não muda o status? | A permissão é verificada no servidor; mesmo chamando a API direto pelo Postman, ele recebe 403. |
| E se dois gestores mudarem ao mesmo tempo? | A ocorrência é travada no banco durante a mudança; só o primeiro consegue, o outro recebe 409. Há um teste automatizado para isso. |
| Aguenta muitos usuários? | No teste de carga com 200 usuários simultâneos, metade das respostas saiu em até 14 ms, sem nenhum erro da API. |
| A senha fica salva? | Só o hash bcrypt. Nem quem tem acesso ao banco vê a senha. |

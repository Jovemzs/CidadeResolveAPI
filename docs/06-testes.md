# 6. Testes

O projeto passa por quatro tipos de teste: **funcionais automatizados**, **manuais pelo Postman e pelo Swagger**, **de performance** e **de usabilidade**.

| Tipo | Ferramenta | Onde está | Resultado |
|---|---|---|---|
| Funcional automatizado | pytest + TestClient | `tests/` | 117 testes passando |
| Manual / ponta a ponta | Postman (e newman) | `postman/` | 14 requisições, 23 verificações, nenhuma falha |
| Manual exploratório | Swagger | `/docs` | Todos os endpoints testáveis pelo navegador |
| Performance (carga) | Locust | `tests/performance/` | 200 usuários simultâneos com mediana de 14 ms |
| Usabilidade | Roteiro de tarefas + questionário SUS | Seção 4 deste documento | Aplicar com usuários antes da apresentação |

## 1. Testes funcionais automatizados

Rodam contra um PostgreSQL de teste separado (`cidaderesolve_test`), recriado do zero a cada execução pelas próprias migrações. Cada teste começa com as tabelas vazias e as fotos vão para uma pasta temporária, então um teste nunca interfere no outro.

```bash
docker compose up -d db
pytest
```

| Arquivo | O que cobre | Testes |
|---|---|---|
| `test_auth.py` | Cadastro, e-mail duplicado, login válido e inválido, token ausente ou inválido, formato único de erro, CORS | 12 |
| `test_categorias.py` | CRUD, nome duplicado, listar só ativas, bloqueio de exclusão em uso, bloqueio para cidadão e visitante | 10 |
| `test_ocorrencias.py` | CRUD, 8 validações de entrada, filtros, paginação, regra do dono e do status `ABERTA`, privacidade do e-mail | 29 |
| `test_status.py` | As 5 transições válidas, as 20 inválidas, comentário obrigatório ao rejeitar, histórico, `resolvido_em`, mudanças simultâneas | 38 |
| `test_fotos.py` | JPEG, PNG e WebP válidos, tipo falso, limite de 5 MB, limite de 5 fotos, permissões, remoção do arquivo do disco | 14 |
| `test_indicadores.py` | Valores calculados sobre um conjunto conhecido, filtro por período, acesso só para gestor | 7 |
| `test_seed.py` | Carga inicial idempotente | 1 |
| `test_site.py` | Site servido na raiz sem encobrir a API, mensagens de erro em português | 6 |

Exemplo de verificação precisa, em `test_indicadores.py`: seis ocorrências com datas definidas, duas delas resolvidas em 10 h e 20 h. O teste confere taxa de resolução de 33,33% e tempo médio de exatamente 15,0 h.

## 2. Testes manuais

**Postman.** A pasta *Fluxo de demonstração* percorre o caso de uso completo: registrar cidadão, fazer login, criar ocorrência, enviar foto, tentar mudar o status como cidadão (recusado com 403), gestor avançar até `RESOLVIDA`, tentar uma transição inválida (recusada com 409), consultar o histórico e os indicadores. Cada etapa tem verificações automáticas. Pela linha de comando:

```bash
npx newman run postman/CidadeResolve.postman_collection.json -e postman/CidadeResolve-Local.postman_environment.json --folder "Fluxo de demonstração"
```

**Swagger.** Em `/docs`, cada endpoint pode ser executado pelo navegador, com o botão *Authorize* para usar o token.

## 3. Teste de performance

### Como foi feito

O Locust simula usuários reais ao mesmo tempo, cada um com um perfil e pausas entre as ações (`tests/performance/locustfile.py`):

| Perfil | Proporção | O que faz |
|---|---|---|
| Visitante | 60% | Lista ocorrências, filtra por bairro e categoria, abre detalhes e histórico |
| Cidadão | 30% | Cria conta, entra, registra ocorrências e consulta as suas |
| Gestor | 10% | Consulta indicadores e move ocorrências abertas para análise |

Ambiente: API e PostgreSQL no Docker local (um processo do Uvicorn), notebook de desenvolvimento, em 23/10/2026. Duração de 90 segundos em cada cenário.

```bash
pip install -r requirements-dev.txt
locust -f tests/performance/locustfile.py --host http://localhost:8000 --headless -u 200 -r 20 -t 90s --html docs/performance/relatorio-200-usuarios.html
```

### Resultados

| Cenário | Requisições | Vazão | Mediana | 95% abaixo de | 99% abaixo de | Falhas da API |
|---|---|---|---|---|---|---|
| 50 usuários simultâneos | 1.856 | 20,8 req/s | 12 ms | 68 ms | 260 ms | 0 |
| 200 usuários simultâneos | 7.460 | 83,2 req/s | 14 ms | 83 ms | 290 ms | 0 |

Tempo por operação no cenário de 200 usuários (mediana):

| Operação | Mediana |
|---|---|
| Listar ocorrências | 13 ms |
| Detalhar ocorrência | 12 ms |
| Filtrar por bairro e categoria | 14 ms |
| Indicadores | 17 ms |
| Criar ocorrência | 67 ms |
| Mudar status | 70 ms |
| Login | 260 ms |
| Cadastro | 320 ms |

Os relatórios completos, com gráficos, estão em `docs/performance/` (abra os arquivos `.html` no navegador).

### Análise

- **Quadruplicar os usuários quase não mudou o tempo de resposta**: a mediana foi de 12 ms para 14 ms, e a vazão cresceu na mesma proporção dos usuários (20,8 para 83,2 req/s). A API não chegou perto do limite nesse cenário.
- **Login e cadastro são as operações mais lentas, de propósito.** A senha é protegida com bcrypt, que é lento por projeto para dificultar ataques de força bruta. Cerca de 260 ms por login é um valor normal e aceitável.
- **Os 409 do cenário de 200 usuários não são erros.** Foram 11 casos de gestores tentando mover a mesma ocorrência no mesmo instante: um consegue e os demais recebem "transição inválida", como manda a regra.
- **O teste encontrou e ajudou a corrigir um problema real.** No primeiro teste, duas mudanças de status simultâneas na mesma ocorrência poderiam ser gravadas em dobro. A correção trava a ocorrência no banco durante a mudança (`SELECT ... FOR UPDATE`), e um teste automatizado com 8 gestores simultâneos garante que só um vence.
- A única falha de conexão registrada ocorreu no segundo em que o teste foi encerrado, quando o Locust interrompe as requisições em andamento. Não aparece nenhum erro no log da API.

### Limites desta medição

O teste foi feito na máquina de desenvolvimento, não no servidor de produção. O plano gratuito do Render tem menos CPU e memória, então os tempos lá devem ser maiores. Para medir a produção, rode o mesmo comando trocando `--host` pelo endereço do Render, com poucos usuários, para não esgotar o plano gratuito.

## 4. Teste de usabilidade

O objetivo é verificar se pessoas que nunca viram o sistema conseguem usá-lo sem ajuda. O ideal é aplicar com 3 a 5 pessoas.

### Roteiro de tarefas

Peça para a pessoa realizar cada tarefa sem explicar como. Anote se conseguiu, quanto tempo levou e onde travou.

| # | Tarefa | Perfil | Sucesso quando |
|---|---|---|---|
| 1 | Crie uma conta | Cidadão | A pessoa chega à lista logada |
| 2 | Registre um poste apagado na sua rua, com o ponto no mapa e uma foto | Cidadão | A ocorrência aparece com foto e mapa |
| 3 | Encontre as ocorrências do bairro Centro que estão em análise | Visitante | A lista filtrada é exibida |
| 4 | Descubra em que etapa está a sua ocorrência e quando foi registrada | Cidadão | A pessoa lê a linha de andamento |
| 5 | Mude uma ocorrência para "em atendimento" com um comentário | Gestor | O histórico mostra a mudança |
| 6 | Diga qual bairro tem mais ocorrências | Gestor | A pessoa responde lendo o painel |

### Questionário SUS (System Usability Scale)

Depois das tarefas, a pessoa responde de 1 (discordo totalmente) a 5 (concordo totalmente):

1. Eu usaria este sistema com frequência.
2. Achei o sistema desnecessariamente complicado.
3. Achei o sistema fácil de usar.
4. Eu precisaria de ajuda de alguém técnico para usar o sistema.
5. As funções do sistema estão bem integradas.
6. Achei o sistema inconsistente.
7. Imagino que a maioria das pessoas aprenderia a usar o sistema rapidamente.
8. Achei o sistema confuso de usar.
9. Eu me senti confiante usando o sistema.
10. Precisei aprender muita coisa antes de conseguir usar o sistema.

**Cálculo:** nas perguntas ímpares, subtraia 1 da resposta; nas pares, subtraia a resposta de 5. Some os 10 resultados e multiplique por 2,5. A nota vai de 0 a 100; acima de 68 é considerada boa usabilidade.

### Registro dos resultados

| Participante | Tarefas concluídas (de 6) | Nota SUS | Principais dificuldades |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

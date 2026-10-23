# 7. Resultados, impacto e melhorias

## 1. Como a solução ataca cada causa do problema

Em [01-problema.md](01-problema.md) foram identificadas quatro causas. A tabela mostra o que o sistema faz contra cada uma e como dá para verificar.

| Causa | O que o CidadeResolve faz | Como verificar |
|---|---|---|
| Canais dispersos e informais | Um único ponto de registro (site e API) com campos padronizados: categoria, endereço, bairro, ponto no mapa e fotos | Toda ocorrência tem os mesmos campos obrigatórios; dados fora do padrão são recusados com mensagem explicando o motivo |
| Falta de um ciclo de vida definido | Cinco situações com fluxo fixo (Aberta → Em análise → Em atendimento → Resolvida, ou Rejeitada); transições fora do fluxo são bloqueadas | A linha de andamento no detalhe mostra ao cidadão em que etapa está; 25 testes automatizados cobrem as transições |
| Falta de registro das mudanças | Histórico com quem mudou, quando e por quê; comentário obrigatório para rejeitar | Qualquer pessoa consulta o histórico, sem login |
| Dados não estruturados | Dados no PostgreSQL, prontos para consulta | Painel com totais por situação, categoria e bairro, taxa de resolução e tempo médio |

## 2. Impacto esperado

**Para o cidadão**

- Registrar um problema leva poucos minutos e pode ser feito do celular, com foto e localização.
- Não precisa mais perguntar "e aí, alguém viu?": a página da ocorrência mostra a etapa, as datas e os comentários da equipe.
- Antes de registrar, consegue ver se o problema já foi informado no mesmo bairro, o que evita duplicidade.
- A transparência é pública: o histórico e a lista podem ser consultados por qualquer pessoa, sem conta.

**Para o gestor**

- Uma lista única, filtrável por bairro, categoria e situação, no lugar de mensagens espalhadas.
- Números prontos para decidir prioridades: qual bairro concentra mais problemas, quanto tempo leva para resolver, que parte das demandas foi resolvida.
- Regras que evitam erros: não dá para pular etapas, nem rejeitar sem justificativa.

**Indicadores para medir o impacto em uso real**

| Indicador | Onde ver | Sinal de melhora |
|---|---|---|
| Taxa de resolução | Painel do gestor | Aumenta ao longo dos meses |
| Tempo médio de resolução | Painel do gestor | Diminui |
| Ocorrências aguardando solução | Painel do gestor | Não acumula |
| Concentração por bairro | Painel do gestor | Orienta onde agir primeiro |
| Nota de usabilidade (SUS) | [06-testes.md](06-testes.md), seção 4 | Acima de 68 |

## 3. Limitações conhecidas

| Limitação | Por que existe | Contorno atual |
|---|---|---|
| Fotos se perdem no Render gratuito a cada novo deploy | O disco do plano gratuito é temporário | No ambiente local as fotos ficam em volume do Docker; o armazenamento está isolado numa interface (`ArmazenamentoFotos`), pronto para trocar |
| Serviço gratuito "dorme" após inatividade | Regra do plano gratuito do Render | Acessar `/saude` antes de usar |
| Sem aviso ao cidadão quando o status muda | Fora do escopo do protótipo | O cidadão acompanha pela página "Minhas" |
| Não detecta duplicadas automaticamente | Fora do escopo do protótipo | Filtro por bairro e categoria antes de registrar |
| Teste de performance feito só no ambiente local | Evitar esgotar o plano gratuito | Mesmo script pode ser rodado contra o Render |

## 4. Melhorias contínuas propostas

Ordenadas por impacto para o usuário em relação ao esforço.

| Prioridade | Melhoria | Benefício | Esforço |
|---|---|---|---|
| 1 | Guardar fotos em armazenamento de objetos (S3, Cloudinary) | Fotos persistem em produção | Baixo: basta uma nova classe de `ArmazenamentoFotos` |
| 2 | Notificar o cidadão por e-mail a cada mudança de status | Retorno ativo, sem precisar entrar no site | Médio |
| 3 | Sugerir ocorrências parecidas próximas antes de registrar | Menos duplicidade | Médio: busca por distância com as coordenadas que já existem |
| 4 | "Apoiar" uma ocorrência existente (eu também vi) | Mede a gravidade pela quantidade de pessoas afetadas | Baixo |
| 5 | Mapa de calor no painel do gestor | Mostra visualmente onde os problemas se concentram | Médio |
| 6 | Prazo esperado por categoria, com alerta de atraso | Cobra o cumprimento de prazos | Médio |
| 7 | Avaliação do atendimento pelo cidadão após a resolução | Mede a satisfação com o serviço | Baixo |

## 5. Coleta de feedback dos usuários

Para aprimorar o sistema com base em quem usa:

1. **Teste de usabilidade** com 3 a 5 pessoas, usando o roteiro de tarefas e o questionário SUS de [06-testes.md](06-testes.md). Registrar onde cada pessoa travou.
2. **Perguntas abertas** ao final do teste:
   - O que foi mais fácil?
   - O que foi mais difícil ou confuso?
   - Faltou alguma informação na página da ocorrência?
   - Você usaria isso no seu bairro? Por quê?
3. **Formulário online** (por exemplo, Google Forms) com as mesmas perguntas, divulgado com o link do sistema publicado.
4. **Transformar o feedback em melhorias**: cada dificuldade relatada por mais de uma pessoa vira um item da lista de melhorias, com a prioridade revista.

### Registro do feedback

| Data | Quem (perfil) | O que relatou | Melhoria gerada |
|---|---|---|---|
| | | | |

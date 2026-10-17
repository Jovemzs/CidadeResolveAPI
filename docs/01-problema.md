# 1. Definição do problema

## Contexto

Buracos na via, postes apagados e lixo descartado em local irregular fazem parte do dia a dia de qualquer bairro. Quem mora ali percebe o problema antes do poder público, mas raramente tem um caminho simples para avisar e, depois, saber o que aconteceu com o aviso.

A CidadeResolve API é um protótipo acadêmico (Projeto Integrador Web Services) que propõe esse caminho: um Web Service REST para registrar ocorrências urbanas, acompanhar o atendimento e consultar indicadores. Não há integração oficial com nenhuma prefeitura.

## Público-alvo

| Perfil | Quem é | O que precisa |
|---|---|---|
| Cidadão | Morador que encontra um problema no bairro | Registrar o problema em poucos passos e acompanhar o andamento |
| Gestor | Pessoa responsável por triar e encaminhar as demandas | Ver as ocorrências organizadas, atualizar o andamento e medir o atendimento |

## A dor

**Do cidadão**

- Não sabe onde registrar: telefone, redes sociais, balcão de atendimento, cada um com uma regra.
- Registra e não recebe retorno. Não sabe se alguém viu, se está em análise ou se foi descartado.
- Não consegue ver se o problema já foi informado por outro morador.
- Descrever o local só com palavras é impreciso; sem foto e sem localização o pedido perde força.

**Do gestor**

- Recebe as demandas por canais diferentes e em formatos diferentes, sem padrão de categoria ou de endereço.
- Não tem uma lista única para filtrar por bairro, tipo de problema ou situação.
- Não tem números para responder perguntas simples: quantas ocorrências estão abertas, qual bairro concentra mais problemas, quanto tempo leva para resolver.

## Causas

1. **Canais dispersos e informais.** Não existe um ponto único de entrada com dados padronizados.
2. **Falta de um ciclo de vida definido.** Sem estados claros (aberta, em análise, em atendimento, resolvida, rejeitada), ninguém sabe em que pé a demanda está.
3. **Falta de registro das mudanças.** Sem histórico, não há como saber quem alterou o quê e quando.
4. **Dados não estruturados.** Sem categoria, bairro e data registrados de forma consistente, não dá para gerar indicadores.

## Efeitos

- Problemas que demoram a ser resolvidos ou que nunca chegam a quem resolve.
- Registros duplicados e retrabalho na triagem.
- Sensação de abandono: o morador deixa de reportar porque acha que não adianta.
- Decisões de prioridade tomadas sem dados.

## Proposta

Um Web Service REST que oferece:

- **Ponto único de registro**, com categoria, endereço, bairro, localização opcional e fotos.
- **Transparência**: qualquer pessoa consulta as ocorrências e o histórico de status, sem precisar de login.
- **Fluxo de atendimento definido**, com histórico de cada mudança e comentário obrigatório quando a ocorrência é rejeitada.
- **Indicadores** para o gestor: totais por status, categoria e bairro, taxa de resolução e tempo médio de resolução.

Por ser uma API, a solução pode ser consumida no futuro por um site, um aplicativo ou outros sistemas, sem alterar as regras de negócio.

## Fora do escopo deste protótipo

Interface web ou aplicativo, integração com sistemas de prefeitura, notificações por e-mail ou push, teste de carga e armazenamento externo de fotos. Ver a seção de limitações no [README](../README.md).

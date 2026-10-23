import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { STATUS, numero } from "../ui.js";

const MAXIMO_BAIRROS = 8;

function barras(linhas, { classe = () => "" } = {}) {
  if (!linhas.length) return h`<p class="dica">Sem ocorrências no período.</p>`;
  const maior = Math.max(...linhas.map((l) => l.quantidade), 1);
  return h`
    <ul class="barras">
      ${linhas.map((l) => h`
        <li class="barra" title="${l.nome}: ${l.quantidade}">
          <span class="barra-nome">${l.nome}</span>
          <span class="barra-trilho"><span class="barra-preenchida ${classe(l)}" style="width:${(l.quantidade / maior) * 100}%"></span></span>
          <span class="barra-valor">${l.quantidade}</span>
        </li>`)}
    </ul>`;
}

function agruparBairros(porBairro) {
  if (porBairro.length <= MAXIMO_BAIRROS) return porBairro.map((b) => ({ nome: b.bairro, quantidade: b.quantidade }));
  const principais = porBairro.slice(0, MAXIMO_BAIRROS - 1).map((b) => ({ nome: b.bairro, quantidade: b.quantidade }));
  const outros = porBairro.slice(MAXIMO_BAIRROS - 1).reduce((soma, b) => soma + b.quantidade, 0);
  return [...principais, { nome: `Outros bairros (${porBairro.length - MAXIMO_BAIRROS + 1})`, quantidade: outros }];
}

export async function render(principal, ctx) {
  const inicio = ctx.consulta.get("data_inicio") || "";
  const fim = ctx.consulta.get("data_fim") || "";
  const ind = await api("/indicadores", { params: { data_inicio: inicio, data_fim: fim } });
  if (!ctx.ehAtual()) return;

  const emAndamento = ind.por_status.ABERTA + ind.por_status.EM_ANALISE + ind.por_status.EM_ATENDIMENTO;
  const porStatus = Object.keys(STATUS).map((s) => ({ nome: STATUS[s], status: s, quantidade: ind.por_status[s] }));
  const porCategoria = ind.por_categoria.map((c) => ({ nome: c.nome, quantidade: c.quantidade }));

  desenhar(principal, h`
    <header class="cabecalho-pagina">
      <div>
        <h1>Painel de indicadores</h1>
        <p>Como está o atendimento das ocorrências${inicio || fim ? " no período escolhido" : ""}.</p>
      </div>
    </header>

    <form class="filtro-periodo" id="periodo">
      <label class="campo"><span>Criadas a partir de</span><input type="date" name="data_inicio" value="${inicio}"></label>
      <label class="campo"><span>Até</span><input type="date" name="data_fim" value="${fim}"></label>
      <button class="botao" type="submit">Aplicar período</button>
      ${inicio || fim ? h`<a href="#/painel">Ver todo o período</a>` : ""}
    </form>

    <section class="numeros" aria-label="Resumo">
      <div class="numero"><span class="numero-valor">${numero(ind.total_ocorrencias)}</span>
        <span class="numero-rotulo">Ocorrências registradas</span></div>
      <div class="numero"><span class="numero-valor">${numero(emAndamento)}</span>
        <span class="numero-rotulo">Aguardando solução</span>
        <span class="numero-nota">Abertas, em análise ou em atendimento</span></div>
      <div class="numero"><span class="numero-valor">${numero(ind.taxa_resolucao, 1)}%</span>
        <span class="numero-rotulo">Taxa de resolução</span>
        <span class="numero-nota">${numero(ind.por_status.RESOLVIDA)} resolvida(s) do total</span></div>
      <div class="numero"><span class="numero-valor">${ind.tempo_medio_resolucao_horas === null ? "—" : `${numero(ind.tempo_medio_resolucao_horas, 1)} h`}</span>
        <span class="numero-rotulo">Tempo médio para resolver</span>
        <span class="numero-nota">${ind.tempo_medio_resolucao_horas === null ? "Nenhuma resolvida no período" : "Do registro até a solução"}</span></div>
    </section>

    <div class="graficos">
      <section class="caixa"><h2>Por situação</h2>${barras(porStatus, { classe: (l) => `status-${l.status.toLowerCase()}` })}</section>
      <section class="caixa"><h2>Por categoria</h2>${barras(porCategoria)}</section>
      <section class="caixa"><h2>Por bairro</h2>${barras(agruparBairros(ind.por_bairro))}</section>
    </div>
  `);

  const form = principal.querySelector("#periodo");
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const p = new URLSearchParams();
    if (form.elements.data_inicio.value) p.set("data_inicio", form.elements.data_inicio.value);
    if (form.elements.data_fim.value) p.set("data_fim", form.elements.data_fim.value);
    ctx.navegar(p.size ? `/painel?${p}` : "/painel");
  });
}

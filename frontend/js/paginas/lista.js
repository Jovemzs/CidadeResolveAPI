import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { criarMapa, marcarOcorrencias } from "../mapa.js";
import { STATUS, data, marcadorStatus, protocolo } from "../ui.js";

const POR_PAGINA = 10;

function cartao(o) {
  return h`
    <a class="cartao" href="#/ocorrencias/${o.id}">
      <div class="cartao-topo"><span class="protocolo">${protocolo(o.id)}</span>${marcadorStatus(o.status)}</div>
      <h2 class="cartao-titulo">${o.titulo}</h2>
      <p class="cartao-local">${o.endereco} · <strong>${o.bairro}</strong></p>
      <p class="cartao-meta">${o.categoria.nome} · registrada em ${data(o.criado_em)} por ${o.autor.nome}</p>
    </a>`;
}

export async function render(principal, ctx) {
  const { consulta, opcoes, sessao } = ctx;
  const base = opcoes.minhas ? "/minhas" : "/";
  const filtros = {
    bairro: consulta.get("bairro") || "",
    categoria_id: consulta.get("categoria_id") || "",
    status: consulta.get("status") || "",
  };
  const pagina = Math.max(1, Number(consulta.get("pagina")) || 1);
  const temFiltro = Object.values(filtros).some(Boolean);

  const [categorias, resultado] = await Promise.all([
    api("/categorias", { params: { incluir_inativas: true } }),
    api("/ocorrencias", { params: { ...filtros, minhas: opcoes.minhas || undefined, pagina, tamanho: POR_PAGINA } }),
  ]);
  if (!ctx.ehAtual()) return;

  const totalPaginas = Math.max(1, Math.ceil(resultado.total / POR_PAGINA));
  const endereco = (novaPagina) => {
    const p = new URLSearchParams({ ...Object.fromEntries(Object.entries(filtros).filter(([, v]) => v)), pagina: novaPagina });
    return `#${base}?${p}`;
  };

  const vazio = temFiltro
    ? h`<div class="caixa vazio"><h2>Nada encontrado com esses filtros</h2>
        <p>Tente outro bairro ou outra situação.</p><a class="botao botao-contorno" href="#${base}">Limpar filtros</a></div>`
    : opcoes.minhas
      ? h`<div class="caixa vazio"><h2>Você ainda não registrou ocorrências</h2>
          <p>Viu algum problema no bairro? Registre e acompanhe por aqui.</p><a class="botao" href="#/nova">Registrar ocorrência</a></div>`
      : h`<div class="caixa vazio"><h2>Nenhuma ocorrência registrada ainda</h2>
          <p>Seja a primeira pessoa a registrar um problema da cidade.</p><a class="botao" href="#/nova">Registrar ocorrência</a></div>`;

  desenhar(principal, h`
    ${!sessao.usuario && !opcoes.minhas ? h`
      <section class="chamada">
        <div><strong>Viu um buraco, um poste apagado ou lixo na calçada?</strong>
        <p>Registre o problema com foto e localização e acompanhe cada etapa até a solução.</p></div>
        <a class="botao" href="#/cadastrar">Criar conta grátis</a>
      </section>` : ""}

    <header class="cabecalho-pagina">
      <div>
        <h1>${opcoes.minhas ? "Minhas ocorrências" : "Ocorrências na cidade"}</h1>
        <p>${resultado.total === 1 ? "1 ocorrência" : `${resultado.total} ocorrências`}${temFiltro ? " com os filtros escolhidos" : ""}, das mais recentes para as mais antigas.</p>
      </div>
    </header>

    <form class="filtros" id="filtros" role="search">
      <label class="campo"><span>Bairro</span>
        <input type="search" name="bairro" value="${filtros.bairro}" placeholder="Ex.: Centro"></label>
      <label class="campo"><span>Categoria</span>
        <select name="categoria_id"><option value="">Todas</option>
          ${categorias.map((c) => h`<option value="${c.id}" ${String(c.id) === filtros.categoria_id ? h`selected` : ""}>${c.nome}</option>`)}
        </select></label>
      <label class="campo"><span>Situação</span>
        <select name="status"><option value="">Todas</option>
          ${Object.entries(STATUS).map(([valor, rotulo]) => h`<option value="${valor}" ${valor === filtros.status ? h`selected` : ""}>${rotulo}</option>`)}
        </select></label>
      <button class="botao" type="submit">Filtrar</button>
    </form>

    <div class="lista-com-mapa">
      <div>
        ${resultado.itens.length ? h`<div class="cartoes">${resultado.itens.map(cartao)}</div>` : vazio}
        ${totalPaginas > 1 ? h`
          <nav class="paginacao" aria-label="Páginas">
            ${pagina > 1 ? h`<a class="botao botao-contorno botao-pequeno" href="${endereco(pagina - 1)}">Anteriores</a>` : h`<span></span>`}
            <span>Página ${pagina} de ${totalPaginas}</span>
            ${pagina < totalPaginas ? h`<a class="botao botao-contorno botao-pequeno" href="${endereco(pagina + 1)}">Próximas</a>` : h`<span></span>`}
          </nav>` : ""}
      </div>
      <div class="mapa" id="mapa" aria-label="Mapa das ocorrências desta página"></div>
    </div>
  `);

  marcarOcorrencias(criarMapa(principal.querySelector("#mapa")), resultado.itens);

  const form = principal.querySelector("#filtros");
  const aplicar = () => {
    const dados = new FormData(form);
    const p = new URLSearchParams();
    for (const [chave, valor] of dados) if (String(valor).trim()) p.set(chave, String(valor).trim());
    ctx.navegar(p.size ? `${base}?${p}` : base);
  };
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    aplicar();
  });
  form.querySelectorAll("select").forEach((s) => s.addEventListener("change", aplicar));
}

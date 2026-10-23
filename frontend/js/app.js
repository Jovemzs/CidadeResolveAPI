import { api, limparToken, obterToken, salvarToken } from "./api.js";
import { desenhar, h } from "./html.js";
import * as cadastrar from "./paginas/cadastrar.js";
import * as categorias from "./paginas/categorias.js";
import * as detalhe from "./paginas/detalhe.js";
import * as entrar from "./paginas/entrar.js";
import * as formulario from "./paginas/formulario.js";
import * as lista from "./paginas/lista.js";
import * as painel from "./paginas/painel.js";

const ROTAS = [
  { padrao: /^\/$/, pagina: lista, titulo: "Ocorrências" },
  { padrao: /^\/minhas$/, pagina: lista, opcoes: { minhas: true }, exige: "login", titulo: "Minhas ocorrências" },
  { padrao: /^\/nova$/, pagina: formulario, exige: "login", titulo: "Registrar ocorrência" },
  { padrao: /^\/ocorrencias\/(\d+)$/, pagina: detalhe, titulo: "Ocorrência" },
  { padrao: /^\/ocorrencias\/(\d+)\/editar$/, pagina: formulario, exige: "login", titulo: "Editar ocorrência" },
  { padrao: /^\/entrar$/, pagina: entrar, titulo: "Entrar" },
  { padrao: /^\/cadastrar$/, pagina: cadastrar, titulo: "Criar conta" },
  { padrao: /^\/painel$/, pagina: painel, exige: "gestor", titulo: "Painel de indicadores" },
  { padrao: /^\/categorias$/, pagina: categorias, exige: "gestor", titulo: "Categorias" },
];

const sessao = { usuario: null };
const principal = document.getElementById("conteudo");
const nav = document.getElementById("nav");
let renderizacaoAtual = 0;

function navegar(caminho) {
  if (location.hash === `#${caminho}`) renderizar();
  else location.hash = `#${caminho}`;
}

function avisar(mensagem, tipo = "ok") {
  const aviso = document.createElement("div");
  aviso.className = tipo === "erro" ? "aviso aviso-erro" : "aviso";
  aviso.textContent = mensagem;
  document.getElementById("avisos").append(aviso);
  setTimeout(() => aviso.remove(), 4500);
}

async function carregarUsuario() {
  if (!obterToken()) {
    sessao.usuario = null;
    return;
  }
  try {
    sessao.usuario = await api("/auth/eu");
  } catch {
    limparToken();
    sessao.usuario = null;
  }
}

async function iniciarSessao(token) {
  salvarToken(token);
  await carregarUsuario();
}

function sair() {
  limparToken();
  sessao.usuario = null;
  avisar("Você saiu da sua conta.");
  navegar("/");
}

function desenharNav(caminho) {
  const u = sessao.usuario;
  const link = (destino, texto) =>
    h`<a href="#${destino}" ${caminho === destino ? h`aria-current="page"` : ""}>${texto}</a>`;
  desenhar(
    nav,
    h`
      ${link("/", "Ocorrências")}
      ${u ? link("/minhas", "Minhas") : ""}
      ${u?.papel === "GESTOR" ? [link("/painel", "Painel"), link("/categorias", "Categorias")] : ""}
      <a class="botao" href="#/nova">Registrar ocorrência</a>
      ${u
        ? h`<span class="nav-usuario">${u.nome}${u.papel === "GESTOR" ? h` <span class="etiqueta">Gestor</span>` : ""}</span>
            <button type="button" class="link" data-acao="sair">Sair</button>`
        : link("/entrar", "Entrar")}
    `,
  );
  nav.querySelector('[data-acao="sair"]')?.addEventListener("click", sair);
}

async function renderizar() {
  const [caminho, busca = ""] = (location.hash.slice(1) || "/").split("?");
  const consulta = new URLSearchParams(busca);
  const rota = ROTAS.find((r) => r.padrao.test(caminho));
  desenharNav(caminho);

  if (!rota) {
    document.title = "Página não encontrada · CidadeResolve";
    desenhar(principal, h`<section class="vazio"><h1>Página não encontrada</h1>
      <p>O endereço não corresponde a nenhuma página do CidadeResolve.</p>
      <a class="botao" href="#/">Ver ocorrências</a></section>`);
    return;
  }
  if (rota.exige && !sessao.usuario) {
    navegar(`/entrar?volta=${encodeURIComponent(caminho)}`);
    return;
  }
  if (rota.exige === "gestor" && sessao.usuario.papel !== "GESTOR") {
    desenhar(principal, h`<section class="vazio"><h1>Área de gestores</h1>
      <p>Esta página é usada pela equipe que atende as ocorrências.</p>
      <a class="botao" href="#/">Ver ocorrências</a></section>`);
    return;
  }

  document.title = `${rota.titulo} · CidadeResolve`;
  const numero = ++renderizacaoAtual;
  const contexto = {
    params: caminho.match(rota.padrao).slice(1),
    consulta,
    opcoes: rota.opcoes || {},
    sessao,
    navegar,
    avisar,
    iniciarSessao,
    ehAtual: () => numero === renderizacaoAtual,
  };

  desenhar(principal, h`<p class="carregando">Carregando…</p>`);
  window.scrollTo(0, 0);
  try {
    await rota.pagina.render(principal, contexto);
  } catch (erro) {
    if (!contexto.ehAtual()) return;
    desenhar(principal, h`<section class="vazio"><h1>Não foi possível abrir esta página</h1>
      <p>${erro.message}</p><a class="botao" href="#/">Voltar às ocorrências</a></section>`);
  }
  principal.focus({ preventScroll: true });
}

window.addEventListener("hashchange", renderizar);
window.addEventListener("sessao-expirada", () => {
  sessao.usuario = null;
  avisar("Sua sessão expirou. Entre de novo para continuar.", "erro");
  navegar("/entrar");
});

await carregarUsuario();
renderizar();

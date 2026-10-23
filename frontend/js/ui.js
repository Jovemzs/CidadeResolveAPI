import { esc, h } from "./html.js";

export const STATUS = {
  ABERTA: "Aberta",
  EM_ANALISE: "Em análise",
  EM_ATENDIMENTO: "Em atendimento",
  RESOLVIDA: "Resolvida",
  REJEITADA: "Rejeitada",
};

// Mesmo fluxo aplicado pela API. O servidor continua sendo quem decide.
export const PROXIMOS_STATUS = {
  ABERTA: ["EM_ANALISE", "REJEITADA"],
  EM_ANALISE: ["EM_ATENDIMENTO", "REJEITADA"],
  EM_ATENDIMENTO: ["RESOLVIDA"],
  RESOLVIDA: [],
  REJEITADA: [],
};

export const TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024;
export const MAXIMO_FOTOS = 5;

export function marcadorStatus(status) {
  return h`<span class="status status-${status.toLowerCase()}">${STATUS[status] || status}</span>`;
}

export function protocolo(id) {
  return `Nº ${String(id).padStart(4, "0")}`;
}

const formatoData = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
const formatoDataHora = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
});

export const data = (iso) => (iso ? formatoData.format(new Date(iso)) : "");
export const dataHora = (iso) => (iso ? formatoDataHora.format(new Date(iso)) : "");

export const numero = (valor, casas = 0) =>
  Number(valor).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

/** Mostra os erros devolvidos pela API junto dos campos do formulário. */
export function exibirErros(formulario, erro) {
  limparErros(formulario);
  const semCampo = [];
  for (const detalhe of erro.detalhes || []) {
    const campo = formulario.elements[detalhe.campo];
    if (campo && campo.type !== "hidden" && campo.insertAdjacentHTML) {
      campo.setAttribute("aria-invalid", "true");
      campo.insertAdjacentHTML("afterend", `<p class="erro-campo">${esc(detalhe.mensagem)}</p>`);
    } else {
      semCampo.push(detalhe.mensagem);
    }
  }
  const geral = formulario.querySelector(".erro-geral");
  if (!geral) return;
  if (erro.detalhes?.length) {
    geral.textContent = semCampo.length ? semCampo.join(" ") : "Corrija os campos destacados.";
  } else {
    geral.textContent = erro.message;
  }
  geral.hidden = false;
  formulario.querySelector('[aria-invalid="true"]')?.focus();
}

export function limparErros(formulario) {
  formulario.querySelectorAll(".erro-campo").forEach((e) => e.remove());
  formulario.querySelectorAll('[aria-invalid="true"]').forEach((e) => e.removeAttribute("aria-invalid"));
  const geral = formulario.querySelector(".erro-geral");
  if (geral) geral.hidden = true;
}

/** Desabilita o botão enquanto a ação roda, trocando o texto. */
export async function comCarregamento(botao, texto, acao) {
  const original = botao.textContent;
  botao.disabled = true;
  botao.textContent = texto;
  try {
    return await acao();
  } finally {
    botao.disabled = false;
    botao.textContent = original;
  }
}

/** Botão de ação destrutiva em dois cliques: o primeiro pede confirmação. */
export function confirmarEmDoisCliques(botao, textoConfirmar, acao) {
  const original = botao.textContent;
  let armado = false;
  let temporizador;
  botao.addEventListener("click", async () => {
    if (!armado) {
      armado = true;
      botao.textContent = textoConfirmar;
      temporizador = setTimeout(() => {
        armado = false;
        botao.textContent = original;
      }, 4000);
      return;
    }
    clearTimeout(temporizador);
    armado = false;
    botao.textContent = original;
    await acao();
  });
}

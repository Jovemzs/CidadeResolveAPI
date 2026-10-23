// Comunicação com a CidadeResolve API. O site e a API ficam no mesmo endereço.

const BASE = "/api/v1";
const CHAVE_TOKEN = "cidaderesolve.token";

export class ErroApi extends Error {
  constructor(status, erro) {
    super(erro?.mensagem || "Erro inesperado. Tente de novo.");
    this.status = status;
    this.codigo = erro?.codigo;
    this.detalhes = erro?.detalhes || [];
  }
}

export function obterToken() {
  try {
    return localStorage.getItem(CHAVE_TOKEN);
  } catch {
    return null;
  }
}

export function salvarToken(token) {
  try {
    localStorage.setItem(CHAVE_TOKEN, token);
  } catch {
    /* navegador sem armazenamento: a sessão dura só esta aba */
  }
}

export function limparToken() {
  try {
    localStorage.removeItem(CHAVE_TOKEN);
  } catch {
    /* nada a limpar */
  }
}

export async function api(caminho, { metodo = "GET", corpo, arquivo, params } = {}) {
  const url = new URL(BASE + caminho, location.origin);
  for (const [chave, valor] of Object.entries(params || {})) {
    if (valor !== undefined && valor !== null && valor !== "") url.searchParams.set(chave, valor);
  }

  const cabecalhos = {};
  const token = obterToken();
  if (token) cabecalhos.Authorization = `Bearer ${token}`;

  let body;
  if (arquivo) {
    body = new FormData();
    body.append("arquivo", arquivo);
  } else if (corpo !== undefined) {
    cabecalhos["Content-Type"] = "application/json";
    body = JSON.stringify(corpo);
  }

  let resposta;
  try {
    resposta = await fetch(url, { method: metodo, headers: cabecalhos, body });
  } catch {
    throw new ErroApi(0, { mensagem: "Não foi possível falar com o servidor. Verifique a conexão e tente de novo." });
  }

  if (resposta.status === 204) return null;
  const dados = await resposta.json().catch(() => null);
  if (!resposta.ok) {
    if (resposta.status === 401 && token) {
      limparToken();
      window.dispatchEvent(new CustomEvent("sessao-expirada"));
    }
    throw new ErroApi(resposta.status, dados?.erro);
  }
  return dados;
}

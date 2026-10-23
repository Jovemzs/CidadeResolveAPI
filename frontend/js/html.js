// Monta HTML com segurança: todo valor interpolado é escapado, a menos que venha de h`` ou raw().

const ENTIDADES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => ENTIDADES[c]);
}

class Html {
  constructor(texto) {
    this.texto = texto;
  }
  toString() {
    return this.texto;
  }
}

export const raw = (texto) => new Html(texto);

function formatar(valor) {
  if (valor instanceof Html) return valor.texto;
  if (Array.isArray(valor)) return valor.map(formatar).join("");
  if (valor === null || valor === undefined || valor === false) return "";
  return esc(valor);
}

export function h(partes, ...valores) {
  let saida = partes[0];
  valores.forEach((valor, i) => {
    saida += formatar(valor) + partes[i + 1];
  });
  return new Html(saida);
}

export function desenhar(elemento, conteudo) {
  elemento.innerHTML = String(conteudo);
}

import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { comCarregamento, confirmarEmDoisCliques, exibirErros, limparErros } from "../ui.js";

function linha(c) {
  return h`
    <tr data-id="${c.id}">
      <td><strong>${c.nome}</strong></td>
      <td>${c.descricao || h`<span class="dica">Sem descrição</span>`}</td>
      <td><span class="etiqueta ${c.ativa ? "" : "etiqueta-inativa"}">${c.ativa ? "Ativa" : "Desativada"}</span></td>
      <td><div class="acoes">
        <button type="button" class="botao botao-contorno botao-pequeno" data-acao="editar">Editar</button>
        <button type="button" class="botao botao-contorno botao-pequeno" data-acao="alternar">${c.ativa ? "Desativar" : "Ativar"}</button>
        <button type="button" class="botao botao-perigo botao-pequeno" data-acao="excluir">Excluir</button>
      </div></td>
    </tr>`;
}

function linhaEdicao(c) {
  return h`
    <tr data-id="${c.id}">
      <td colspan="4">
        <form class="nova-categoria" data-form="editar" novalidate>
          <label class="campo"><span>Nome</span><input type="text" name="nome" maxlength="80" value="${c.nome}" required></label>
          <label class="campo"><span>Descrição</span><input type="text" name="descricao" maxlength="255" value="${c.descricao || ""}"></label>
          <div class="acoes">
            <button class="botao botao-pequeno" type="submit">Salvar</button>
            <button class="link" type="button" data-acao="cancelar">Cancelar</button>
          </div>
          <p class="erro-geral" hidden style="grid-column:1/-1"></p>
        </form>
      </td>
    </tr>`;
}

export async function render(principal, ctx) {
  const categorias = await api("/categorias", { params: { incluir_inativas: true } });
  if (!ctx.ehAtual()) return;
  const porId = new Map(categorias.map((c) => [String(c.id), c]));
  const recarregar = () => ctx.navegar("/categorias");

  desenhar(principal, h`
    <header class="cabecalho-pagina">
      <div>
        <h1>Categorias</h1>
        <p>Os tipos de problema que o cidadão pode escolher. Categorias desativadas somem do formulário, mas as ocorrências antigas continuam com elas.</p>
      </div>
    </header>

    <section class="caixa">
      <h2>Nova categoria</h2>
      <form class="nova-categoria" id="form-nova" novalidate>
        <label class="campo"><span>Nome</span><input type="text" name="nome" maxlength="80" required placeholder="Ex.: Poda de árvore"></label>
        <label class="campo"><span>Descrição <span class="dica">(opcional)</span></span><input type="text" name="descricao" maxlength="255" placeholder="Ex.: Galhos sobre a via ou a fiação"></label>
        <button class="botao" type="submit">Criar categoria</button>
        <p class="erro-geral" hidden style="grid-column:1/-1"></p>
      </form>
    </section>

    <section class="caixa">
      <h2>Categorias cadastradas</h2>
      <div class="tabela-rolagem">
        <table>
          <thead><tr><th>Nome</th><th>Descrição</th><th>Situação</th><th><span class="pular">Ações</span></th></tr></thead>
          <tbody id="corpo">${categorias.map(linha)}</tbody>
        </table>
      </div>
    </section>
  `);

  const salvar = async (form, metodo, caminho, extra = {}) => {
    limparErros(form);
    const corpo = { nome: form.elements.nome.value, descricao: form.elements.descricao.value.trim() || null, ...extra };
    await comCarregamento(form.querySelector('button[type="submit"]'), "Salvando…", async () => {
      try {
        await api(caminho, { metodo, corpo });
        ctx.avisar(metodo === "POST" ? "Categoria criada." : "Categoria salva.");
        recarregar();
      } catch (erro) {
        exibirErros(form, erro);
      }
    });
  };

  principal.querySelector("#form-nova").addEventListener("submit", (evento) => {
    evento.preventDefault();
    salvar(evento.currentTarget, "POST", "/categorias");
  });

  const corpoTabela = principal.querySelector("#corpo");
  const ligarLinha = (tr) => {
    const c = porId.get(tr.dataset.id);
    tr.querySelector('[data-acao="editar"]')?.addEventListener("click", () => {
      tr.outerHTML = String(linhaEdicao(c));
      const nova = corpoTabela.querySelector(`tr[data-id="${c.id}"]`);
      const form = nova.querySelector("form");
      form.elements.nome.focus();
      form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        salvar(form, "PUT", `/categorias/${c.id}`, { ativa: c.ativa });
      });
      form.querySelector('[data-acao="cancelar"]').addEventListener("click", () => {
        nova.outerHTML = String(linha(c));
        ligarLinha(corpoTabela.querySelector(`tr[data-id="${c.id}"]`));
      });
    });
    tr.querySelector('[data-acao="alternar"]')?.addEventListener("click", async (evento) => {
      await comCarregamento(evento.currentTarget, "Salvando…", async () => {
        try {
          await api(`/categorias/${c.id}`, { metodo: "PUT", corpo: { nome: c.nome, descricao: c.descricao, ativa: !c.ativa } });
          ctx.avisar(c.ativa ? `"${c.nome}" desativada.` : `"${c.nome}" ativada.`);
          recarregar();
        } catch (erro) {
          ctx.avisar(erro.message, "erro");
        }
      });
    });
    const excluir = tr.querySelector('[data-acao="excluir"]');
    if (excluir) {
      confirmarEmDoisCliques(excluir, "Confirmar", async () => {
        try {
          await api(`/categorias/${c.id}`, { metodo: "DELETE" });
          ctx.avisar(`"${c.nome}" excluída.`);
          recarregar();
        } catch (erro) {
          ctx.avisar(erro.codigo === "CATEGORIA_EM_USO" ? `"${c.nome}" tem ocorrências. Use "Desativar" em vez de excluir.` : erro.message, "erro");
        }
      });
    }
  };
  corpoTabela.querySelectorAll("tr").forEach(ligarLinha);
}

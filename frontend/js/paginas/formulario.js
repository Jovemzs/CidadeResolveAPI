import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { criarSeletorDePonto } from "../mapa.js";
import { MAXIMO_FOTOS, TAMANHO_MAXIMO_FOTO, comCarregamento, exibirErros, limparErros } from "../ui.js";

export async function render(principal, ctx) {
  const id = ctx.params[0];
  const editando = Boolean(id);
  const usuario = ctx.sessao.usuario;

  const [categorias, ocorrencia] = await Promise.all([
    api("/categorias", { params: { incluir_inativas: editando || undefined } }),
    editando ? api(`/ocorrencias/${id}`) : null,
  ]);
  if (!ctx.ehAtual()) return;

  if (editando && usuario.papel !== "GESTOR" && (ocorrencia.autor.id !== usuario.id || ocorrencia.status !== "ABERTA")) {
    desenhar(principal, h`<section class="vazio"><h1>Esta ocorrência não pode ser editada</h1>
      <p>Só quem registrou pode editar, e apenas enquanto ela estiver aberta.</p>
      <a class="botao" href="#/ocorrencias/${id}">Voltar à ocorrência</a></section>`);
    return;
  }

  const valores = ocorrencia || { titulo: "", descricao: "", endereco: "", bairro: "", latitude: null, longitude: null, categoria: { id: null } };
  // Na edição, a categoria atual aparece mesmo se tiver sido desativada; as demais só se estiverem ativas.
  const opcoes = categorias.filter((c) => c.ativa || c.id === valores.categoria.id);

  desenhar(principal, h`
    <a class="voltar" href="${editando ? `#/ocorrencias/${id}` : "#/"}">← ${editando ? "Voltar à ocorrência" : "Todas as ocorrências"}</a>
    <header class="cabecalho-pagina">
      <div>
        <h1>${editando ? "Editar ocorrência" : "Registrar ocorrência"}</h1>
        <p>${editando ? "Corrija o que for preciso e salve." : "Conte o que está acontecendo e onde. Quanto mais preciso, mais fácil de resolver."}</p>
      </div>
    </header>

    <form class="formulario caixa" id="form-ocorrencia" novalidate>
      <label class="campo"><span>Título <span class="dica">(de 5 a 120 caracteres)</span></span>
        <input type="text" name="titulo" maxlength="120" required value="${valores.titulo}" placeholder="Ex.: Buraco grande na pista"></label>

      <label class="campo"><span>Categoria</span>
        <select name="categoria_id" required>
          <option value="">Escolha uma categoria</option>
          ${opcoes.map((c) => h`<option value="${c.id}" ${c.id === valores.categoria.id ? h`selected` : ""}>${c.nome}${c.ativa ? "" : " (desativada)"}</option>`)}
        </select></label>

      <label class="campo"><span>Descrição <span class="dica">(pelo menos 10 caracteres)</span></span>
        <textarea name="descricao" required placeholder="Ex.: Buraco de uns 50 cm na faixa da direita, em frente ao número 120. Já causou acidente com moto.">${valores.descricao}</textarea></label>

      <div class="linha-dupla">
        <label class="campo"><span>Endereço</span>
          <input type="text" name="endereco" maxlength="255" required value="${valores.endereco}" placeholder="Rua, número ou ponto de referência"></label>
        <label class="campo"><span>Bairro</span>
          <input type="text" name="bairro" maxlength="80" required value="${valores.bairro}" placeholder="Ex.: Centro"></label>
      </div>

      <div class="campo">
        <span class="rotulo">Local no mapa <span class="dica">(opcional: clique no mapa para marcar o ponto exato)</span></span>
        <div class="mapa" id="mapa"></div>
        <div class="acoes">
          <button type="button" class="botao botao-contorno botao-pequeno" id="minha-localizacao">Usar minha localização</button>
          <button type="button" class="link" id="remover-ponto">Remover ponto</button>
          <span class="dica" id="coordenadas"></span>
        </div>
        <input type="hidden" name="latitude">
        <input type="hidden" name="longitude">
      </div>

      ${editando ? "" : h`
        <label class="campo"><span>Fotos <span class="dica">(opcional: até ${MAXIMO_FOTOS}, JPEG, PNG ou WebP, 5 MB cada)</span></span>
          <input type="file" name="fotos" accept="image/jpeg,image/png,image/webp" multiple></label>`}

      <p class="erro-geral" hidden></p>
      <div class="acoes">
        <button class="botao" type="submit">${editando ? "Salvar alterações" : "Registrar ocorrência"}</button>
        <a href="${editando ? `#/ocorrencias/${id}` : "#/"}">Cancelar</a>
      </div>
    </form>
  `);

  const form = principal.querySelector("#form-ocorrencia");
  const coordenadas = principal.querySelector("#coordenadas");
  const seletor = criarSeletorDePonto(principal.querySelector("#mapa"), valores, (lat, lng) => {
    form.elements.latitude.value = lat ?? "";
    form.elements.longitude.value = lng ?? "";
    coordenadas.textContent = lat === null ? "Nenhum ponto marcado." : `Ponto marcado: ${lat}, ${lng}`;
  });
  if (valores.latitude === null) coordenadas.textContent = "Nenhum ponto marcado.";

  principal.querySelector("#remover-ponto").addEventListener("click", () => seletor.limpar());
  principal.querySelector("#minha-localizacao").addEventListener("click", () => {
    if (!navigator.geolocation) {
      ctx.avisar("Este navegador não informa a localização.", "erro");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (posicao) => seletor.definir(posicao.coords.latitude, posicao.coords.longitude, true),
      () => ctx.avisar("Não foi possível obter sua localização. Marque o ponto clicando no mapa.", "erro"),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  });

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(form);
    const campos = form.elements;
    const fotos = editando ? [] : Array.from(campos.fotos.files);
    if (fotos.length > MAXIMO_FOTOS) {
      ctx.avisar(`Escolha no máximo ${MAXIMO_FOTOS} fotos.`, "erro");
      return;
    }
    const grande = fotos.find((f) => f.size > TAMANHO_MAXIMO_FOTO);
    if (grande) {
      ctx.avisar(`A foto "${grande.name}" passa de 5 MB. Escolha uma imagem menor.`, "erro");
      return;
    }

    const corpo = {
      titulo: campos.titulo.value,
      descricao: campos.descricao.value,
      categoria_id: campos.categoria_id.value ? Number(campos.categoria_id.value) : null,
      endereco: campos.endereco.value,
      bairro: campos.bairro.value,
      latitude: campos.latitude.value ? Number(campos.latitude.value) : null,
      longitude: campos.longitude.value ? Number(campos.longitude.value) : null,
    };

    await comCarregamento(form.querySelector('button[type="submit"]'), "Salvando…", async () => {
      let salva;
      try {
        salva = editando
          ? await api(`/ocorrencias/${id}`, { metodo: "PUT", corpo })
          : await api("/ocorrencias", { metodo: "POST", corpo });
      } catch (erro) {
        exibirErros(form, erro);
        return;
      }

      const falhas = [];
      for (const arquivo of fotos) {
        try {
          await api(`/ocorrencias/${salva.id}/fotos`, { metodo: "POST", arquivo });
        } catch (erro) {
          falhas.push(`${arquivo.name}: ${erro.message}`);
        }
      }
      if (falhas.length) ctx.avisar(`Ocorrência salva, mas algumas fotos não foram enviadas. ${falhas.join(" ")}`, "erro");
      else ctx.avisar(editando ? "Alterações salvas." : "Ocorrência registrada. Acompanhe o andamento por aqui.");
      ctx.navegar(`/ocorrencias/${salva.id}`);
    });
  });
}

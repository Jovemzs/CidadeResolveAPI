import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { criarMapa, marcarOcorrencias } from "../mapa.js";
import {
  MAXIMO_FOTOS,
  PROXIMOS_STATUS,
  STATUS,
  TAMANHO_MAXIMO_FOTO,
  comCarregamento,
  confirmarEmDoisCliques,
  data,
  dataHora,
  exibirErros,
  limparErros,
  marcadorStatus,
  protocolo,
} from "../ui.js";

const PERCURSO = ["ABERTA", "EM_ANALISE", "EM_ATENDIMENTO", "RESOLVIDA"];

/** Andamento como linha de ônibus: as paradas já percorridas ficam preenchidas. */
function trilha(ocorrencia, historico) {
  const chegada = Object.fromEntries(historico.map((r) => [r.status_novo, r.criado_em]));
  const rejeitada = ocorrencia.status === "REJEITADA";
  const ultimaAntesDeRejeitar = rejeitada ? historico.at(-1)?.status_anterior : null;
  const atual = PERCURSO.indexOf(rejeitada ? ultimaAntesDeRejeitar : ocorrencia.status);
  const paradas = rejeitada ? PERCURSO.slice(0, atual + 1) : PERCURSO;

  const parada = (status, classe) => h`
    <li class="parada ${classe}" ${classe === "atual" || classe === "rejeitada" ? h`aria-current="step"` : ""}>
      <span class="parada-ponto" aria-hidden="true"></span>
      <span class="parada-nome">${STATUS[status]}</span>
      <span class="parada-data">${chegada[status] ? data(chegada[status]) : "—"}</span>
    </li>`;

  return h`
    <ol class="trilha" aria-label="Andamento da ocorrência">
      ${paradas.map((s, i) => parada(s, i < atual || rejeitada ? "feita" : i === atual ? "atual" : "futura"))}
      ${rejeitada ? parada("REJEITADA", "rejeitada") : ""}
    </ol>`;
}

function itemHistorico(r) {
  return h`
    <li>
      <span>${r.status_anterior ? h`${marcadorStatus(r.status_anterior)} → ` : "Registrada como "}${marcadorStatus(r.status_novo)}</span>
      <span class="quando">${dataHora(r.criado_em)} · ${r.alterado_por.nome}</span>
      ${r.comentario ? h`<blockquote>${r.comentario}</blockquote>` : ""}
    </li>`;
}

export async function render(principal, ctx) {
  const id = ctx.params[0];
  const [ocorrencia, historico] = await Promise.all([api(`/ocorrencias/${id}`), api(`/ocorrencias/${id}/historico`)]);
  if (!ctx.ehAtual()) return;

  const usuario = ctx.sessao.usuario;
  const ehGestor = usuario?.papel === "GESTOR";
  const ehDono = usuario?.id === ocorrencia.autor.id;
  const podeModificar = ehGestor || (ehDono && ocorrencia.status === "ABERTA");
  const proximos = PROXIMOS_STATUS[ocorrencia.status];
  const temPonto = ocorrencia.latitude !== null;
  const cabeMaisFotos = ocorrencia.fotos.length < MAXIMO_FOTOS;

  desenhar(principal, h`
    <a class="voltar" href="#/">← Todas as ocorrências</a>

    <section class="placa" aria-labelledby="titulo-ocorrencia">
      <div class="placa-interna">
        <span class="placa-sobre">${ocorrencia.bairro} · ${ocorrencia.categoria.nome}</span>
        <h1 class="placa-titulo" id="titulo-ocorrencia">${ocorrencia.titulo}</h1>
        <div class="placa-rodape">
          <span class="protocolo">Protocolo ${protocolo(ocorrencia.id)}</span>
          ${marcadorStatus(ocorrencia.status)}
        </div>
      </div>
    </section>

    ${trilha(ocorrencia, historico)}

    <div class="detalhe-grade">
      <div>
        <section class="caixa">
          <h2>O problema</h2>
          <p class="descricao">${ocorrencia.descricao}</p>
          <dl class="dados">
            <dt>Endereço</dt><dd>${ocorrencia.endereco}</dd>
            <dt>Bairro</dt><dd>${ocorrencia.bairro}</dd>
            <dt>Registrada por</dt><dd>${ocorrencia.autor.nome}, em ${dataHora(ocorrencia.criado_em)}</dd>
            ${ocorrencia.resolvido_em ? h`<dt>Resolvida em</dt><dd>${dataHora(ocorrencia.resolvido_em)}</dd>` : ""}
          </dl>
          ${podeModificar ? h`
            <div class="acoes" style="margin-top:20px">
              <a class="botao botao-contorno" href="#/ocorrencias/${ocorrencia.id}/editar">Editar ocorrência</a>
              <button type="button" class="botao botao-perigo" id="excluir">Excluir ocorrência</button>
            </div>` : ""}
          ${ehDono && !ehGestor && ocorrencia.status !== "ABERTA" ? h`
            <p class="dica" style="margin-top:16px">A ocorrência já está em atendimento, então não pode mais ser editada.</p>` : ""}
        </section>

        <section class="caixa">
          <h2>Fotos</h2>
          ${ocorrencia.fotos.length
            ? h`<div class="fotos">${ocorrencia.fotos.map((f, i) => h`
                <figure class="foto" style="margin:0">
                  <a href="${f.url}" target="_blank" rel="noopener"><img src="${f.url}" alt="Foto ${i + 1} da ocorrência" loading="lazy"></a>
                  ${podeModificar ? h`<button type="button" class="botao botao-perigo botao-pequeno" data-excluir-foto="${f.id}">Remover</button>` : ""}
                </figure>`)}</div>`
            : h`<p class="dica">Nenhuma foto enviada.</p>`}
          ${podeModificar && cabeMaisFotos ? h`
            <form class="envio-foto" id="form-foto">
              <label class="campo"><span>Adicionar foto <span class="dica">(JPEG, PNG ou WebP, até 5 MB; ${MAXIMO_FOTOS - ocorrencia.fotos.length} restante(s))</span></span>
                <input type="file" name="arquivo" accept="image/jpeg,image/png,image/webp" required></label>
              <button class="botao" type="submit">Enviar foto</button>
            </form>` : ""}
        </section>
      </div>

      <div>
        ${ehGestor ? h`
          <section class="caixa">
            <h2>Atualizar andamento</h2>
            ${proximos.length ? h`
              <form class="formulario" id="form-status">
                <fieldset class="opcoes-status"><legend>Próxima etapa</legend>
                  ${proximos.map((s, i) => h`
                    <label class="opcao"><input type="radio" name="status" value="${s}" ${i === 0 ? h`checked` : ""}> ${marcadorStatus(s)}</label>`)}
                </fieldset>
                <label class="campo"><span>Comentário <span class="dica">(obrigatório para rejeitar)</span></span>
                  <textarea name="comentario" maxlength="500" placeholder="Ex.: Equipe agendada para quinta-feira."></textarea></label>
                <p class="erro-geral" hidden></p>
                <button class="botao" type="submit">Salvar andamento</button>
              </form>`
            : h`<p>Esta ocorrência está encerrada como <strong>${STATUS[ocorrencia.status].toLowerCase()}</strong>.</p>`}
          </section>` : ""}

        <section class="caixa">
          <h2>Histórico</h2>
          <ol class="historico">${historico.map(itemHistorico)}</ol>
        </section>

        ${temPonto ? h`<section class="caixa"><h2>Localização</h2><div class="mapa" id="mapa"></div></section>` : ""}
      </div>
    </div>
  `);

  if (temPonto) marcarOcorrencias(criarMapa(principal.querySelector("#mapa")), [ocorrencia]);

  const recarregar = () => ctx.navegar(`/ocorrencias/${ocorrencia.id}`);

  const botaoExcluir = principal.querySelector("#excluir");
  if (botaoExcluir) {
    confirmarEmDoisCliques(botaoExcluir, "Clique de novo para excluir", async () => {
      try {
        await api(`/ocorrencias/${ocorrencia.id}`, { metodo: "DELETE" });
        ctx.avisar("Ocorrência excluída.");
        ctx.navegar(ehDono ? "/minhas" : "/");
      } catch (erro) {
        ctx.avisar(erro.message, "erro");
      }
    });
  }

  principal.querySelectorAll("[data-excluir-foto]").forEach((botao) => {
    confirmarEmDoisCliques(botao, "Confirmar", async () => {
      try {
        await api(`/fotos/${botao.dataset.excluirFoto}`, { metodo: "DELETE" });
        ctx.avisar("Foto removida.");
        recarregar();
      } catch (erro) {
        ctx.avisar(erro.message, "erro");
      }
    });
  });

  const formFoto = principal.querySelector("#form-foto");
  formFoto?.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const arquivo = formFoto.elements.arquivo.files[0];
    if (!arquivo) return;
    if (arquivo.size > TAMANHO_MAXIMO_FOTO) {
      ctx.avisar("A foto passa de 5 MB. Escolha uma imagem menor.", "erro");
      return;
    }
    await comCarregamento(formFoto.querySelector("button"), "Enviando…", async () => {
      try {
        await api(`/ocorrencias/${ocorrencia.id}/fotos`, { metodo: "POST", arquivo });
        ctx.avisar("Foto enviada.");
        recarregar();
      } catch (erro) {
        ctx.avisar(erro.message, "erro");
      }
    });
  });

  const formStatus = principal.querySelector("#form-status");
  formStatus?.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(formStatus);
    const status = formStatus.elements.status.value;
    const comentario = formStatus.elements.comentario.value.trim() || null;
    await comCarregamento(formStatus.querySelector("button"), "Salvando…", async () => {
      try {
        await api(`/ocorrencias/${ocorrencia.id}/status`, { metodo: "PATCH", corpo: { status, comentario } });
        ctx.avisar(`Andamento salvo: ${STATUS[status].toLowerCase()}.`);
        recarregar();
      } catch (erro) {
        exibirErros(formStatus, erro);
      }
    });
  });
}

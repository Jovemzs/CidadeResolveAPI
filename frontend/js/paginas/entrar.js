import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { comCarregamento, exibirErros, limparErros } from "../ui.js";

export function destinoSeguro(consulta) {
  const volta = consulta.get("volta") || "/";
  return volta.startsWith("/") && !volta.startsWith("//") ? volta : "/";
}

export async function render(principal, ctx) {
  const volta = destinoSeguro(ctx.consulta);
  desenhar(principal, h`
    <section class="estreito">
      <h1>Entrar</h1>
      <p>Entre para registrar ocorrências e acompanhar as suas.</p>
      <form class="formulario caixa" id="form-entrar" novalidate>
        <label class="campo"><span>E-mail</span>
          <input type="email" name="email" autocomplete="email" required></label>
        <label class="campo"><span>Senha</span>
          <input type="password" name="senha" autocomplete="current-password" required></label>
        <p class="erro-geral" hidden></p>
        <button class="botao" type="submit">Entrar</button>
        <p>Ainda não tem conta? <a href="#/cadastrar?volta=${encodeURIComponent(volta)}">Criar conta</a></p>
      </form>
    </section>
  `);

  const form = principal.querySelector("#form-entrar");
  form.elements.email.focus();
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(form);
    await comCarregamento(form.querySelector("button"), "Entrando…", async () => {
      try {
        const { access_token } = await api("/auth/login", {
          metodo: "POST",
          corpo: { email: form.elements.email.value.trim(), senha: form.elements.senha.value },
        });
        await ctx.iniciarSessao(access_token);
        ctx.avisar(`Olá, ${ctx.sessao.usuario.nome}!`);
        ctx.navegar(volta);
      } catch (erro) {
        exibirErros(form, erro);
      }
    });
  });
}

import { api } from "../api.js";
import { desenhar, h } from "../html.js";
import { comCarregamento, exibirErros, limparErros } from "../ui.js";
import { destinoSeguro } from "./entrar.js";

export async function render(principal, ctx) {
  const volta = destinoSeguro(ctx.consulta);
  desenhar(principal, h`
    <section class="estreito">
      <h1>Criar conta</h1>
      <p>Com uma conta você registra problemas do bairro e acompanha cada etapa do atendimento.</p>
      <form class="formulario caixa" id="form-cadastro" novalidate>
        <label class="campo"><span>Nome</span>
          <input type="text" name="nome" autocomplete="name" maxlength="120" required></label>
        <label class="campo"><span>E-mail</span>
          <input type="email" name="email" autocomplete="email" required></label>
        <label class="campo"><span>Senha <span class="dica">(pelo menos 8 caracteres)</span></span>
          <input type="password" name="senha" autocomplete="new-password" minlength="8" maxlength="72" required></label>
        <p class="erro-geral" hidden></p>
        <button class="botao" type="submit">Criar conta</button>
        <p>Já tem conta? <a href="#/entrar?volta=${encodeURIComponent(volta)}">Entrar</a></p>
      </form>
    </section>
  `);

  const form = principal.querySelector("#form-cadastro");
  form.elements.nome.focus();
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros(form);
    const dados = {
      nome: form.elements.nome.value,
      email: form.elements.email.value.trim(),
      senha: form.elements.senha.value,
    };
    await comCarregamento(form.querySelector("button"), "Criando conta…", async () => {
      try {
        await api("/auth/registro", { metodo: "POST", corpo: dados });
        const { access_token } = await api("/auth/login", {
          metodo: "POST",
          corpo: { email: dados.email, senha: dados.senha },
        });
        await ctx.iniciarSessao(access_token);
        ctx.avisar("Conta criada. Bem-vindo(a) ao CidadeResolve!");
        ctx.navegar(volta);
      } catch (erro) {
        exibirErros(form, erro);
      }
    });
  });
}

"""Dados de demonstração para apresentar o projeto. Uso: python -m app.demo

Cria um cidadão de exemplo e ocorrências em várias situações, passando pelas mesmas
regras de negócio da API. Pode ser executado mais de uma vez: se o cidadão de
exemplo já tiver ocorrências, não faz nada.
"""

from datetime import timedelta

from app.core.config import obter_configuracoes
from app.core.seguranca import gerar_hash_senha
from app.db.sessao import SessaoLocal
from app.models import Ocorrencia, Papel, StatusOcorrencia, Usuario
from app.repositories.categoria import CategoriaRepositorio
from app.repositories.usuario import UsuarioRepositorio
from app.schemas.ocorrencia import OcorrenciaEntrada, StatusEntrada
from app.seed import executar_carga
from app.services.armazenamento import ArmazenamentoFotosDisco
from app.services.ocorrencia import OcorrenciaServico

CIDADAO_EMAIL = "maria.demo@cidaderesolve.com"
CIDADAO_SENHA = "demo12345"

# (título, descrição, categoria, endereço, bairro, latitude, longitude, etapas, dias atrás, horas para concluir)
OCORRENCIAS = [
    ("Buraco grande na faixa da direita", "Buraco de uns 50 cm em frente ao número 120. Motos desviam para a contramão.",
     "Buraco na via", "Rua Augusta, 120", "Consolação", -23.5536, -46.6560,
     ["EM_ANALISE", "EM_ATENDIMENTO", "RESOLVIDA"], 12, 30),
    ("Poste apagado na esquina da praça", "O poste da esquina está apagado há uma semana e a praça fica escura à noite.",
     "Iluminação pública", "Praça da República, 1", "República", -23.5432, -46.6426,
     ["EM_ANALISE", "EM_ATENDIMENTO", "RESOLVIDA"], 9, 52),
    ("Entulho jogado na calçada", "Restos de obra ocupando a calçada inteira; pedestres andam pela rua.",
     "Descarte irregular de lixo", "Rua da Mooca, 850", "Mooca", -23.5580, -46.6000,
     ["EM_ANALISE", "EM_ATENDIMENTO"], 6, None),
    ("Sequência de buracos perto da escola", "Três buracos seguidos no trecho em frente à escola estadual.",
     "Buraco na via", "Avenida Paes de Barros, 400", "Mooca", -23.5625, -46.5930,
     ["EM_ANALISE"], 4, None),
    ("Lâmpada piscando sem parar", "A lâmpada do poste em frente ao número 33 pisca a noite inteira.",
     "Iluminação pública", "Rua Bresser, 33", "Brás", -23.5450, -46.6110,
     [], 2, None),
    ("Sofá abandonado no canteiro", "Um sofá e um colchão foram deixados no canteiro central.",
     "Descarte irregular de lixo", "Avenida Celso Garcia, 1500", "Belém", -23.5400, -46.5960,
     ["REJEITADA"], 3, None),
    ("Calçada afundada no ponto de ônibus", "A calçada afundou bem onde as pessoas esperam o ônibus.",
     "Buraco na via", "Rua Vergueiro, 2000", "Vila Mariana", -23.5800, -46.6380,
     [], 1, None),
]

COMENTARIOS = {
    "EM_ANALISE": "Equipe de vistoria vai avaliar o local.",
    "EM_ATENDIMENTO": "Serviço agendado com a equipe de manutenção.",
    "RESOLVIDA": "Serviço concluído e conferido.",
    "REJEITADA": "Local é área particular; o responsável foi notificado.",
}


def executar_demo() -> None:
    config = obter_configuracoes()
    with SessaoLocal() as db:
        executar_carga(db)
        usuarios = UsuarioRepositorio(db)
        gestor = usuarios.obter_por_email(config.gestor_email or "")
        if gestor is None or gestor.papel != Papel.GESTOR:
            raise SystemExit("Defina GESTOR_EMAIL e GESTOR_SENHA para criar a demonstração.")

        cidada = usuarios.obter_por_email(CIDADAO_EMAIL)
        if cidada is None:
            cidada = usuarios.adicionar(
                Usuario(nome="Maria Souza", email=CIDADAO_EMAIL, senha_hash=gerar_hash_senha(CIDADAO_SENHA))
            )
            db.commit()
        elif db.query(Ocorrencia).filter(Ocorrencia.autor_id == cidada.id).count():
            print("Demonstração já criada.")
            return

        categorias = {c.nome: c.id for c in CategoriaRepositorio(db).listar(incluir_inativas=True)}
        servico = OcorrenciaServico(db, ArmazenamentoFotosDisco(config.upload_dir))

        for titulo, descricao, categoria, endereco, bairro, lat, lng, etapas, dias, horas in OCORRENCIAS:
            ocorrencia = servico.criar(
                OcorrenciaEntrada(
                    titulo=titulo, descricao=descricao, categoria_id=categorias[categoria],
                    endereco=endereco, bairro=bairro, latitude=lat, longitude=lng,
                ),
                cidada,
            )
            for etapa in etapas:
                servico.mudar_status(
                    ocorrencia.id,
                    StatusEntrada(status=StatusOcorrencia(etapa), comentario=COMENTARIOS[etapa]),
                    gestor,
                )
            # Recua as datas para a demonstração ter um histórico realista.
            ocorrencia = db.get(Ocorrencia, ocorrencia.id)
            deslocamento = timedelta(days=dias)
            ocorrencia.criado_em -= deslocamento
            for registro in ocorrencia.historico:
                registro.criado_em -= deslocamento
            if horas is not None:
                ocorrencia.resolvido_em = ocorrencia.criado_em + timedelta(hours=horas)
                ocorrencia.historico[-1].criado_em = ocorrencia.resolvido_em
            db.commit()
            print(f"Ocorrência criada: {titulo}")

        print(f"Cidadã de exemplo: {CIDADAO_EMAIL} / {CIDADAO_SENHA}")


if __name__ == "__main__":
    executar_demo()

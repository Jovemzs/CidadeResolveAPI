"""Esquema inicial: usuario, categoria, ocorrencia, foto e historico_status

Revision ID: 0001
Revises:
Create Date: 2026-10-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

papel = postgresql.ENUM("CIDADAO", "GESTOR", name="papel", create_type=False)
status_ocorrencia = postgresql.ENUM(
    "ABERTA",
    "EM_ANALISE",
    "EM_ATENDIMENTO",
    "RESOLVIDA",
    "REJEITADA",
    name="status_ocorrencia",
    create_type=False,
)


def upgrade() -> None:
    conexao = op.get_bind()
    papel.create(conexao, checkfirst=True)
    status_ocorrencia.create(conexao, checkfirst=True)

    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("papel", papel, nullable=False, server_default="CIDADAO"),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(80), nullable=False, unique=True),
        sa.Column("descricao", sa.String(255), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "ocorrencia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column(
            "categoria_id",
            sa.Integer(),
            sa.ForeignKey("categoria.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "autor_id", sa.Integer(), sa.ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("status", status_ocorrencia, nullable=False, server_default="ABERTA"),
        sa.Column("endereco", sa.String(255), nullable=False),
        sa.Column("bairro", sa.String(80), nullable=False),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolvido_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ocorrencia_bairro", "ocorrencia", ["bairro"])

    op.create_table(
        "foto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ocorrencia_id",
            sa.Integer(),
            sa.ForeignKey("ocorrencia.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome_arquivo", sa.String(255), nullable=False),
        sa.Column("tipo_conteudo", sa.String(50), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_foto_ocorrencia_id", "foto", ["ocorrencia_id"])

    op.create_table(
        "historico_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ocorrencia_id",
            sa.Integer(),
            sa.ForeignKey("ocorrencia.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status_anterior", status_ocorrencia, nullable=True),
        sa.Column("status_novo", status_ocorrencia, nullable=False),
        sa.Column(
            "alterado_por_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("comentario", sa.String(500), nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_historico_status_ocorrencia_id", "historico_status", ["ocorrencia_id"])


def downgrade() -> None:
    op.drop_table("historico_status")
    op.drop_table("foto")
    op.drop_table("ocorrencia")
    op.drop_table("categoria")
    op.drop_table("usuario")
    conexao = op.get_bind()
    status_ocorrencia.drop(conexao, checkfirst=True)
    papel.drop(conexao, checkfirst=True)

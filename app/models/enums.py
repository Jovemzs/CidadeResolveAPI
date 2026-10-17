import enum


class Papel(str, enum.Enum):
    CIDADAO = "CIDADAO"
    GESTOR = "GESTOR"


class StatusOcorrencia(str, enum.Enum):
    ABERTA = "ABERTA"
    EM_ANALISE = "EM_ANALISE"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    RESOLVIDA = "RESOLVIDA"
    REJEITADA = "REJEITADA"

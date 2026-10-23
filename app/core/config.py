from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracoes(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_expira_minutos: int = 60
    upload_dir: str = "uploads"
    gestor_email: str | None = None
    gestor_senha: str | None = None
    # Origens (sites) autorizadas a chamar a API pelo navegador, separadas por vírgula.
    cors_origens: str = "http://localhost:5173,http://localhost:3000"

    @property
    def lista_cors_origens(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origens.split(",") if origem.strip()]

    @field_validator("database_url")
    @classmethod
    def usar_driver_psycopg(cls, valor: str) -> str:
        # O Render entrega a URL como postgres:// ou postgresql://, sem o driver.
        for prefixo in ("postgres://", "postgresql://"):
            if valor.startswith(prefixo):
                return "postgresql+psycopg://" + valor[len(prefixo):]
        return valor


@lru_cache
def obter_configuracoes() -> Configuracoes:
    return Configuracoes()

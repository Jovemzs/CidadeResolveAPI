from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import obter_configuracoes

engine = create_engine(obter_configuracoes().database_url, pool_pre_ping=True)
SessaoLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

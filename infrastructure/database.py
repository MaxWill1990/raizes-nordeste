from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cria o arquivo do banco SQLite direto na pasta do projeto
SQLALCHEMY_DATABASE_URL = "sqlite:///./raizes_nordeste.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função que abre e fecha a conexão a cada requisição da API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
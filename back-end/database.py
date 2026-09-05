from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///database/database.db"

# check_same_thread é necessário apenas para SQLite no FastAPI

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Gerador de sessão que o FastAPI usará para injetar a conexão nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
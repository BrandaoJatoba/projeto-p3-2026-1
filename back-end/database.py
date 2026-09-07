from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///database/database_ppgi.db"

# check_same_thread é necessário apenas para SQLite no FastAPI

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Habilita suporte a Foreign Keys no SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

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
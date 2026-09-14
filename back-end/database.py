from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///database/database_ppgi.db"

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
    """
    Gerador (Generator) de sessão do banco de dados para injeção de dependência no FastAPI.

    Abre uma nova sessão síncrona do SQLAlchemy (SessionLocal) a cada requisição HTTP e garante o fechamento automático da conexão ao finalizar o processamento da rota, mesmo em caso de exceções/erros.

    Yields:
        Session: Instância da sessão do SQLAlchemy pronta para execução de operações CRUD.

    Usage:
        Exemplo de uso em uma rota do FastAPI:

        @app.get("/usuarios")
        def listar_usuarios(db: Session = Depends(get_db)):
            return db.query(Usuario).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
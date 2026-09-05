from database import engine, Base
import models 

def criar_banco():
    print("Criando tabelas no banco de dados SQLite...")
    # O comando create_all varre os modelos registrados no Base e cria no banco
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

if __name__ == "__main__":
    criar_banco()
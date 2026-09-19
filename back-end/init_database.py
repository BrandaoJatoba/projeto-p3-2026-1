from database import engine, Base, SessionLocal
import models
import crud
import os

PERFIS_PADRAO = [
    {"nome_perfil": "ADMIN", "descricao": "Administrador com acesso total ao sistema"},
    {"nome_perfil": "SECRETARIA", "descricao": "Acesso operacional às rotas da Secretaria"},
    {"nome_perfil": "COORDENACAO", "descricao": "Acesso às rotas da Coordenação"},
    {"nome_perfil": "DISCENTE", "descricao": "Acesso limitado do Estudante"},
]

def garantir_diretorio_banco():
    pasta_banco = os.path.dirname("./database/database_ppgi.db")    
    if pasta_banco and not os.path.exists(pasta_banco):
        os.makedirs(pasta_banco, exist_ok=True)
        print(f"Pasta '{pasta_banco}' criada com sucesso!")

def inicializar_perfis(db):
    print("Verificando perfis padrão...")
    for perfil_info in PERFIS_PADRAO:
        perfil = db.query(models.Perfil).filter(models.Perfil.nome_perfil == perfil_info["nome_perfil"]).first()
        if not perfil:
            novo_perfil = models.Perfil(
                nome_perfil=perfil_info["nome_perfil"],
                descricao=perfil_info["descricao"]
            )
            db.add(novo_perfil)
    db.commit()

def vincular_perfil_usuario(db, id_usuario, nome_perfil):
    perfil = db.query(models.Perfil).filter(models.Perfil.nome_perfil == nome_perfil).first()
    if not perfil:
        return

    # Verifica se a associação já existe em USUARIOS_PERFIS
    vinculo_existente = db.query(models.UsuarioPerfil).filter(
        models.UsuarioPerfil.id_usuario == id_usuario,
        models.UsuarioPerfil.id_perfil == perfil.id_perfil
    ).first()

    if not vinculo_existente:
        novo_vinculo = models.UsuarioPerfil(
            id_usuario=id_usuario,
            id_perfil=perfil.id_perfil
        )
        db.add(novo_vinculo)
        db.commit()

def criar_banco():
    garantir_diretorio_banco()
    
    print("Criando tabelas no banco de dados SQLite...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas verificadas/criadas!")

    db = SessionLocal()
    try:
        # 1. Popula a tabela PERFIS se estiver vazia/incompleta
        inicializar_perfis(db)

        # 2. Cria o usuário Admin se não existir
        email_admin = "admin.ppgi@ic.ufal.br"
        admin = db.query(models.Usuario).filter(models.Usuario.email == email_admin).first()
        
        if not admin:
            print("Criando conta de usuário Admin...")
            admin = crud.criar_usuario(db, email_admin, "senha123")
            print(f"Admin criado com sucesso! ID: {admin.id_usuario}")
        else:
            print("Usuário Admin já existente.")

        # 3. Associa o usuário Admin ao perfil ADMIN em USUARIOS_PERFIS
        if admin:
            vincular_perfil_usuario(db, admin.id_usuario, "ADMIN")
            print("Perfil ADMIN vinculado ao usuário com sucesso!")

    finally:
        db.close()

if __name__ == "__main__":
    criar_banco()
from database import engine, Base, SessionLocal
import models
import usuario
import os

PERFIS_PADRAO = [
    {"nome_perfil": "ADMIN", "descricao": "Administrador com acesso total ao sistema"},
    {"nome_perfil": "SECRETARIA", "descricao": "Acesso operacional às rotas da Secretaria"},
    {"nome_perfil": "COORDENACAO", "descricao": "Acesso às rotas da Coordenação"},
    {"nome_perfil": "DISCENTE", "descricao": "Acesso limitado do Estudante"},
]

def garantir_diretorio_banco():
    pasta_banco = os.path.dirname("./dados/database_ppgi.db")    
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

        # 2 e 3. Cria um usuário para cada perfil e faz o vínculo
        for perfil_info in PERFIS_PADRAO:
            nome_perfil = perfil_info["nome_perfil"]
            email_usuario = f"{nome_perfil.lower()}.ppgi@ic.ufal.br"
            
            usuario_db = db.query(models.Usuario).filter(models.Usuario.email == email_usuario).first()
            
            if not usuario_db:
                print(f"Criando conta de usuário para o perfil {nome_perfil}...")
                usuario_db = usuario.criar_usuario(db, email_usuario, "senha123")
                print(f"Usuário {nome_perfil} criado com sucesso! ID: {usuario_db.id_usuario}")
            else:
                print(f"Usuário {email_usuario} já existente.")

            # Associa o usuário recém-criado/existente ao perfil em USUARIOS_PERFIS
            if usuario_db:
                vincular_perfil_usuario(db, usuario_db.id_usuario, nome_perfil)
                print(f"Perfil {nome_perfil} vinculado ao usuário {email_usuario} com sucesso!")

    finally:
        db.close()

if __name__ == "__main__":
    criar_banco()
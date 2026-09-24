import os
from db.database import engine, Base, SessionLocal
from db import models
from db import usuario

PERFIS_PADRAO = [
    {"nome_perfil": "ADMIN", "descricao": "Administrador com acesso total ao sistema"},
    {"nome_perfil": "SECRETARIA", "descricao": "Acesso operacional às rotas da Secretaria"},
    {"nome_perfil": "COORDENACAO", "descricao": "Acesso às rotas da Coordenação"},
    {"nome_perfil": "DISCENTE", "descricao": "Acesso limitado do Estudante"},
]

PRAZOS_E_GATILHOS_PADRAO = [
    {
        "codigo_prazo": "QUALIFICACAO",
        "nome_prazo": "Exame de Qualificação",
        "descricao": "Defesa de proposta até o 3º semestre letivo",
        "gatilhos": [
            {"dias": 90, "msg": "Atenção: Seu prazo limite para qualificação vence em 90 dias."},
            {"dias": 30, "msg": "Urgente: Faltam 30 dias para o prazo limite da sua qualificação."},
            {"dias": 0,  "msg": "Alerta: Hoje é o prazo limite para a realização da sua qualificação."}
        ]
    },
    {
        "codigo_prazo": "HOMOLOGACAO_BANCA",
        "nome_prazo": "Solicitação de Banca Examinadora",
        "descricao": "Envio do requerimento de banca à secretaria (mínimo 30 dias antes da defesa)",
        "gatilhos": [
            {"dias": 45, "msg": "Lembrete: A solicitação de banca de defesa deve ser submetida em breve (mínimo 30 dias antes da defesa)."},
            {"dias": 35, "msg": "Atenção: Faltam apenas 5 dias para o prazo limite de solicitação da banca examinadora."}
        ]
    },
    {
        "codigo_prazo": "DEFESA",
        "nome_prazo": "Defesa de Dissertação",
        "descricao": "Prazo máximo de conclusão do mestrado (24 meses)",
        "gatilhos": [
            {"dias": 180, "msg": "Aviso: Faltam 6 meses para o prazo limite de defesa da sua dissertação."},
            {"dias": 90,  "msg": "Atenção: Faltam 3 meses para a data limite da sua defesa de dissertação."},
            {"dias": 30,  "msg": "Urgente: Faltam 30 dias para o prazo final de defesa."}
        ]
    },
    {
        "codigo_prazo": "VERSAO_FINAL_DEFESA",
        "nome_prazo": "Entrega de Correções Pós-Defesa",
        "descricao": "Prazo de correções exigidas pela banca (30 ou 60 dias)",
        "gatilhos": [
            {"dias": 15, "msg": "Lembrete: Faltam 15 dias para o envio das correções da sua dissertação."},
            {"dias": 5,  "msg": "Urgente: Faltam 5 dias para o término do prazo de envio da versão corrigida."}
        ]
    },
    {
        "codigo_prazo": "DIPLOMA_POS_DEFESA",
        "nome_prazo": "Abertura de Processo de Diploma",
        "descricao": "Prazo de 60 dias corridos pós-defesa para inclusão de documentação no SIGAA",
        "gatilhos": [
            {"dias": 30, "msg": "Aviso: Faltam 30 dias para encerrar o prazo limite de envio dos documentos para expedição do diploma."},
            {"dias": 10, "msg": "Urgente: Faltam 10 dias para o prazo limite do processo de diploma."}
        ]
    }
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

def inicializar_prazos_e_gatilhos(db):
    print("Verificando tipos de prazos e gatilhos de alertas padrão...")
    for item in PRAZOS_E_GATILHOS_PADRAO:
        tipo = db.query(models.TipoPrazo).filter(models.TipoPrazo.codigo_prazo == item["codigo_prazo"]).first()
        if not tipo:
            tipo = models.TipoPrazo(
                codigo_prazo=item["codigo_prazo"],
                nome_prazo=item["nome_prazo"],
                descricao=item["descricao"]
            )
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
            
            # Adiciona os gatilhos para este tipo de prazo
            for g in item["gatilhos"]:
                gatilho = models.GatilhoAlerta(
                    id_tipo_prazo=tipo.id_tipo_prazo,
                    dias_antecedencia=g["dias"],
                    mensagem_template=g["msg"]
                )
                db.add(gatilho)
            db.commit()

def vincular_perfil_usuario(db, id_usuario, nome_perfil):
    perfil = db.query(models.Perfil).filter(models.Perfil.nome_perfil == nome_perfil).first()
    if not perfil:
        return

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

        # 2. Popula os TIPOS DE PRAZOS e GATILHOS se estiverem vazios
        inicializar_prazos_e_gatilhos(db)

        # 3. Cria um usuário para cada perfil e faz o vínculo
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

            if usuario_db:
                vincular_perfil_usuario(db, usuario_db.id_usuario, nome_perfil)
                print(f"Perfil {nome_perfil} vinculado ao usuário {email_usuario} com sucesso!")

    finally:
        db.close()

if __name__ == "__main__":
    criar_banco()
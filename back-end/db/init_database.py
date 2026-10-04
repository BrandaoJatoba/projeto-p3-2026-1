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

DISCIPLINAS_PADRAO = [
    # GRUPO 1
    {"codigo": "PPGI 001", "nome": "Teoria da Computação", "grupo": "BASICAS", "creditos": 4},
    {"codigo": "PPGI 002", "nome": "Projeto e Análise de Algoritmos", "grupo": "BASICAS", "creditos": 4},
    {"codigo": "PPGI 026", "nome": "Otimização Contínua e Combinatória", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 031", "nome": "Teoria dos Grafos", "grupo": "ELETIVAS", "creditos": 4},

    # GRUPO 2
    {"codigo": "PPGI 003", "nome": "Engenharia de Software", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 007", "nome": "Especificação e Verificação Formal de Sistemas", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 008", "nome": "Inteligência Artificial", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 009", "nome": "Computação Gráfica", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 010", "nome": "Processamento de Imagem", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 011", "nome": "Aprendizagem de Máquina", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 016-07", "nome": "Tópicos Especiais em Computação Visual e Inteligente – Visão Computacional", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 016-10", "nome": "Tópicos Especiais em Engenharia de Sistemas Computacionais – Testes de Software", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 016-12", "nome": "Tópicos Especiais em Engenharia de Sistemas Computacionais - Técnicas de Otimização Bioinspiradas", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 017-08", "nome": "Tópicos Especiais em Computação Visual e Inteligente: Exploração e Mineração de Dados", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 017-10", "nome": "Tópicos Especiais em Computação Visual e Inteligente: Aprendizagem Profunda", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 028", "nome": "Inteligência Artificial aplicada à Engenharia de Software", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 029", "nome": "Ciência de Dados", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 034", "nome": "Processamento de Linguagem Natural", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 035", "nome": "Qualidade de Software em Metodologias Ágeis", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 038", "nome": "Boas Práticas em Aprendizagem de Máquina", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 039", "nome": "Sistemas Suportados por Aprendizagem de Máquina", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 040", "nome": "Redes Neurais e Aprendizado Profundo", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 041", "nome": "Verificação e Validação de Sistemas Suportados por Aprendizagem de Máquina", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 043", "nome": "Estatística Aplicada à Pesquisa em Computação", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 046", "nome": "Informática na Educação", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 048", "nome": "Fundamentos de Inteligência Artificial Aplicados à Medicina", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 050", "nome": "Redes de Petri", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 051", "nome": "Engenharia de Software Experimental", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 052", "nome": "Visão Computacional", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 058", "nome": "Inteligência Artificial Generativa", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 063", "nome": "Agentes Inteligentes", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 065", "nome": "Sistemas de Controle Inteligente", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 066", "nome": "Inteligência Artificial na Educação", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 067", "nome": "Engenharia de Software Baseada em Evidências", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 069", "nome": "Meta-Aprendizagem", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 070", "nome": "Aprendizado de Máquina para Ambientes Não Estacionários", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 071", "nome": "Aprendizado por Reforço", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 072", "nome": "Fundamentos de Sistemas de Tempo Real", "grupo": "ELETIVAS", "creditos": 4},

    # GRUPO 3
    {"codigo": "PPGI 027", "nome": "Modelagem Computacional de Sistemas Biológicos", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 030", "nome": "Projeto e Implementação de Redes de Sensores", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 032", "nome": "Gamificação na Educação", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 033", "nome": "Projeto de Simulação e Experimentos em Redes de Sensores Sem Fio", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 036", "nome": "Engenharia de Feixes Acústicos", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 037", "nome": "Tecnologias Digitais Emergentes", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 042", "nome": "Gamificação Experimental", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 049", "nome": "Projeto de Banco de Dados: Fundamentos, Modelos e Tecnologias", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 054", "nome": "Gerência e Processamento de Dados em Larga Escala", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 060", "nome": "System of Systems Design and Architecture", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 064", "nome": "Aprendizagem de Máquina para Dispositivos de Borda", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 068", "nome": "Introdução à Identificação de Sistemas Dinâmicos", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 073", "nome": "Acessibilidade Digital: Fundamentos, Métodos e Tecnologias", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 074", "nome": "Simulação em Tempo Real e Hardware-in-the-Loop", "grupo": "ELETIVAS", "creditos": 4},

    # GRUPO 4
    {"codigo": "PPGI 016-04", "nome": "Tópicos: Computação Aplicada à Educação", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 016-11", "nome": "Tópicos Especiais Em Engenharia De Sistemas Computacionais: Navegação De Robôs", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 017-06", "nome": "Tópicos Especiais em Computação Visual e Inteligente: Bancos de Dados Não-relacionais (NoSQL)", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 017-11", "nome": "Metodologia Científica", "grupo": "TOPICOS_ESPECIAIS", "creditos": 4},
    {"codigo": "PPGI 053", "nome": "Metodologia Científica", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 056", "nome": "Introdução a Identificação de Sistemas", "grupo": "ELETIVAS", "creditos": 4},
    {"codigo": "PPGI 057", "nome": "Revisão Sistemática da Literatura", "grupo": "ELETIVAS", "creditos": 4},
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
            
            for g in item["gatilhos"]:
                gatilho = models.GatilhoAlerta(
                    id_tipo_prazo=tipo.id_tipo_prazo,
                    dias_antecedencia=g["dias"],
                    mensagem_template=g["msg"]
                )
                db.add(gatilho)
            db.commit()


def inicializar_disciplinas(db):
    print("Verificando catálogo de disciplinas padrão...")
    novas_count = 0
    for d in DISCIPLINAS_PADRAO:
        disciplina_existente = db.query(models.Disciplina).filter(
            models.Disciplina.codigo_disciplina == d["codigo"]
        ).first()

        if not disciplina_existente:
            nova_disciplina = models.Disciplina(
                codigo_disciplina=d["codigo"],
                nome_disciplina=d["nome"],
                grupo_disciplina=d["grupo"],
                creditos=d["creditos"]
            )
            db.add(nova_disciplina)
            novas_count += 1

    if novas_count > 0:
        db.commit()
        print(f"{novas_count} disciplinas inseridas no banco com sucesso!")
    else:
        print("Todas as disciplinas padrão já estão cadastradas.")


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
        # 1. Popula a tabela PERFIS
        inicializar_perfis(db)

        # 2. Popula os TIPOS DE PRAZOS e GATILHOS
        inicializar_prazos_e_gatilhos(db)

        # 3. Popula a tabela DISCIPLINAS
        inicializar_disciplinas(db)

        # 4. Cria um usuário para cada perfil e faz o vínculo
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
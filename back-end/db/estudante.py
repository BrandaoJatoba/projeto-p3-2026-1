""" ideia

# routers/estudantes.py

@router.post("/estudantes")
def criar_estudante(payload: EstudanteCreate, db: Session):
    # 1. Cria o Estudante
    novo_aluno = Estudante(**payload.dict())
    db.add(novo_aluno)
    db.flush() # Gera o id_estudante

    # 2. Cria a Dissertação base
    nova_dissertacao = Dissertacao(
        id_estudante=novo_aluno.id_estudante,
        data_inicio=semestre.data_inicio_real
    )
    db.add(nova_dissertacao)
    db.flush()

    # 3. Calcula e pré-inicializa os marcos com status PENDENTE
    prazos = AcademicTrackingService.calcular_prazos_iniciais(novo_aluno.id_semestre, db)

    db.add(Qualificacao(
        id_dissertacao=nova_dissertacao.id_dissertacao,
        prazo_maximo_qualificacao=prazos["qualificacao"],
        status_qualificacao="PENDENTE"
    ))

    db.add(Defesa(
        id_dissertacao=nova_dissertacao.id_dissertacao,
        prazo_maximo_defesa=prazos["defesa"],
        status_defesa="PENDENTE"
    ))

    db.commit()
    return novo_aluno


"""
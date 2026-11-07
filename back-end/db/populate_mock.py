import datetime
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db import models
import db.enumStatus as enumStatus

def criar_mock_data(db: Session):
    print("Iniciando a inserção de mock data...")

    # ==========================================
    # 1. SEMESTRES LETIVOS
    # ==========================================
    semestres_mock = [
        {"codigo": "2023.1", "inicio": datetime.date(2023, 3, 1), "fim": datetime.date(2023, 7, 15)},
        {"codigo": "2023.2", "inicio": datetime.date(2023, 8, 1), "fim": datetime.date(2023, 12, 15)},
        {"codigo": "2024.1", "inicio": datetime.date(2024, 3, 1), "fim": datetime.date(2024, 7, 15)},
        {"codigo": "2024.2", "inicio": datetime.date(2024, 8, 1), "fim": datetime.date(2024, 12, 15)},
    ]
    
    semestres_db = []
    for s in semestres_mock:
        sem = db.query(models.SemestreLetivo).filter_by(codigo_semestre=s["codigo"]).first()
        if not sem:
            sem = models.SemestreLetivo(
                codigo_semestre=s["codigo"],
                data_inicio_real=s["inicio"],
                data_fim_real=s["fim"],
                dias_letivos=100
            )
            db.add(sem)
        semestres_db.append(sem)
    db.commit()

    # ==========================================
    # 2. SUSPENSÕES DE CALENDÁRIO
    # ==========================================
    suspensao = db.query(models.SuspensaoCalendario).filter_by(motivo="Greve dos Servidores").first()
    if not suspensao:
        suspensao = models.SuspensaoCalendario(
            id_semestre=semestres_db[2].id_semestre, 
            motivo="Greve dos Servidores",
            data_inicio_suspensao=datetime.date(2024, 4, 10),
            data_fim_suspensao=datetime.date(2024, 5, 25),
            dias_suspensos=45
        )
        db.add(suspensao)
        db.commit()

    # ==========================================
    # 3. PROFESSORES E DISCIPLINAS
    # ==========================================
    nomes_professores = ["Alan Turing", "Ada Lovelace", "Donald Knuth", "Grace Hopper"]
    professores_db = []
    for nome in nomes_professores:
        prof = db.query(models.Professor).filter_by(nome_professor=nome).first()
        if not prof:
            prof = models.Professor(nome_professor=nome)
            db.add(prof)
        professores_db.append(prof)
    db.commit()

    disciplinas = db.query(models.Disciplina).all()
    if not disciplinas:
        print("Erro: Nenhuma disciplina encontrada. Execute o init_database.py primeiro.")
        return

    # ==========================================
    # 4. ESTUDANTES (Cenários Variados)
    # ==========================================
    cenarios_estudantes = [
        {
            "matricula": "20231001", "nome": "João Apto (Pronto para Defesa)", 
            "status": enumStatus.StatusEstudanteEnum.ATIVO, "semestre_idx": 0, "prof_idx": 0,
            "prazo_sigaa": datetime.date(2027, 3, 1)
        },
        {
            "matricula": "20241002", "nome": "Maria Iniciante (Faltam Créditos)", 
            "status": enumStatus.StatusEstudanteEnum.ATIVO, "semestre_idx": 2, "prof_idx": 1,
            "prazo_sigaa": datetime.date(2027, 8, 1)
        },
        {
            "matricula": "20232003", "nome": "Pedro Qualificado (Falta Artigo)", 
            "status": enumStatus.StatusEstudanteEnum.ATIVO, "semestre_idx": 1, "prof_idx": 2,
            "prazo_sigaa": datetime.date(2027, 8, 1)
        }
    ]

    for est_data in cenarios_estudantes:
        est = db.query(models.Estudante).filter_by(matricula=est_data["matricula"]).first()
        if not est:
            est = models.Estudante(
                matricula=est_data["matricula"],
                nome_discente=est_data["nome"],
                status_atual=est_data["status"],
                id_semestre=semestres_db[est_data["semestre_idx"]].id_semestre,
                id_orientador=professores_db[est_data["prof_idx"]].id_professor,
                eh_bolsista=True,
                prazo_conclusao_sigaa=est_data["prazo_sigaa"],
                email=f"aluno{est_data['matricula']}@ic.ufal.br"
            )
            db.add(est)
            db.commit()
            db.refresh(est)

            # ==========================================
            # CENÁRIO 1: JOÃO APTO (Tudo completo)
            # ==========================================
            if "Apto" in est.nome_discente:
                # Proficiência
                db.add(models.Proficiencia(id_estudante=est.id_estudante, status_certificado="ENTREGUE", consolidada_sigaa=True, data_entrega_certificado=datetime.date(2023, 5, 10)))
                
                # Estágio Docência (Atualizado)
                db.add(models.EstagioDocencia(
                    id_estudante=est.id_estudante, 
                    id_professor_supervisor=professores_db[0].id_professor, 
                    id_disciplina=disciplinas[0].id_disciplina, 
                    id_semestre=semestres_db[0].id_semestre, 
                    status_proposta="APROVADA",
                    data_entrega_proposta=datetime.date(2023, 4, 1),
                    status_relatorio="APROVADO",
                    data_entrega_relatorio=datetime.date(2023, 12, 1)
                ))
                
                # Artigo (Atualizado)
                db.add(models.SubmissaoArtigo(
                    titulo="Uso de IA em Testes", 
                    id_estudante=est.id_estudante, 
                    qualis="A2", 
                    tipo="PERIÓDICO",
                    status_comprovante="PUBLICADO",
                    data_entrega=datetime.date(2023, 10, 1),
                    status_validacao_colegiado="APROVADA"
                ))
                
                # Disciplinas
                for disc in disciplinas[:6]:
                    db.add(models.HistoricoDisciplina(id_estudante=est.id_estudante, id_disciplina=disc.id_disciplina, id_semestre=semestres_db[0].id_semestre, conceito="A", status_disciplina="APROVADO", creditos_integralizados=4))
                
                # Dissertação, Qualificação e Defesa (Atualizado)
                diss = models.Dissertacao(id_estudante=est.id_estudante, titulo="Dissertação do João", data_inicio=datetime.date(2023, 3, 1))
                db.add(diss)
                db.commit()
                db.add(models.Qualificacao(
                    id_dissertacao=diss.id_dissertacao, 
                    prazo_maximo_qualificacao=datetime.date(2024, 3, 1), 
                    status_qualificacao="ENTREGUE",
                    data_realizacao=datetime.date(2024, 2, 20)
                ))
                db.add(models.Defesa(id_dissertacao=diss.id_dissertacao, prazo_maximo_defesa=datetime.date(2025, 3, 1), status_defesa="PENDENTE"))
                
                # Prorrogação (João)
                db.add(models.ProrrogacaoHistorico(
                    id_estudante=est.id_estudante,
                    tipo_prazo="DEFESA",
                    quantidade_meses=3,
                    data_pedido=datetime.date(2024, 1, 15),
                    resultado_pedido="DEFERIDO"
                ))

            # ==========================================
            # CENÁRIO 2: MARIA INICIANTE
            # ==========================================
            elif "Iniciante" in est.nome_discente:
                for disc in disciplinas[:2]:
                    db.add(models.HistoricoDisciplina(id_estudante=est.id_estudante, id_disciplina=disc.id_disciplina, id_semestre=semestres_db[2].id_semestre, conceito="A", status_disciplina="APROVADO", creditos_integralizados=4))
                diss = models.Dissertacao(id_estudante=est.id_estudante, titulo="Projeto Inicial da Maria", data_inicio=datetime.date(2024, 3, 1))
                db.add(diss)

            # ==========================================
            # CENÁRIO 3: PEDRO QUALIFICADO
            # ==========================================
            elif "Qualificado" in est.nome_discente:
                db.add(models.Proficiencia(id_estudante=est.id_estudante, status_certificado="ENTREGUE", consolidada_sigaa=True))
                for disc in disciplinas[:4]:
                    db.add(models.HistoricoDisciplina(id_estudante=est.id_estudante, id_disciplina=disc.id_disciplina, id_semestre=semestres_db[1].id_semestre, conceito="B", status_disciplina="APROVADO", creditos_integralizados=4))
                
                # Dissertação e Qualificação (Atualizado)
                diss = models.Dissertacao(id_estudante=est.id_estudante, titulo="Redes Neurais Aplicadas", data_inicio=datetime.date(2023, 8, 1))
                db.add(diss)
                db.commit()
                db.add(models.Qualificacao(
                    id_dissertacao=diss.id_dissertacao, 
                    prazo_maximo_qualificacao=datetime.date(2024, 8, 1), 
                    status_qualificacao="ENTREGUE",
                    data_realizacao=datetime.date(2024, 7, 15)
                ))
                
                # Artigo (Atualizado)
                db.add(models.SubmissaoArtigo(
                    titulo="Artigo Inicial", 
                    id_estudante=est.id_estudante, 
                    qualis="B4", 
                    tipo="EVENTO",
                    status_comprovante="NEGADO",
                    data_entrega=datetime.date(2023, 11, 15),
                    status_validacao_colegiado="REPROVADA"
                ))

                # Prorrogação (Pedro)
                db.add(models.ProrrogacaoHistorico(
                    id_estudante=est.id_estudante,
                    tipo_prazo="QUALIFICACAO",
                    quantidade_meses=6,
                    data_pedido=datetime.date(2023, 11, 20),
                    resultado_pedido="INDEFERIDO"
                ))

            db.commit()

    print("Mock data inserido com sucesso e ajustado aos Enums!")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        criar_mock_data(db)
    finally:
        db.close()
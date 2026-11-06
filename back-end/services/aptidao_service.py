from sqlmodel import Session
from db.models import HistoricoDisciplina, Disciplina, Proficiencia, EstagioDocencia, Qualificacao, Dissertacao, SubmissaoArtigo
from db.enumStatus import enumStatus
from schemas import StatusDefesaResponse, DetalheCreditos, RequisitosDefesa

def calcular_aptidao_defesa(db: Session, id_estudante: int) -> StatusDefesaResponse:
    pendencias = []
    
    # ==========================================
    # 1. CÁLCULO DE CRÉDITOS E DISCIPLINAS
    # ==========================================
    historico_aprovado = db.query(HistoricoDisciplina, Disciplina).join(
        Disciplina, HistoricoDisciplina.id_disciplina == Disciplina.id_disciplina
    ).filter(
        HistoricoDisciplina.id_estudante == id_estudante,
        HistoricoDisciplina.status_disciplina == enumStatus.StatusDisciplina.APROVADO
    ).all()

    cred_basicas = 0
    cred_eletivas = 0
    cred_topicos = 0
    cred_estudo = 0
    qtd_obrigatorias_grupo1 = 0
    qtd_obrigatorias_grupos_1_2_3 = 0

    for hist, disc in historico_aprovado:
        # Agrupamento e soma de créditos baseados na nova estrutura de Enums
        
        # 1. Contabilização de Créditos por Natureza
        if disc.natureza_disciplina == enumStatus.NaturezaDisciplina.BASICAS:
            cred_basicas += hist.creditos_integralizados
                
        elif disc.natureza_disciplina == enumStatus.NaturezaDisciplina.ELETIVAS:
            cred_eletivas += hist.creditos_integralizados
                
        elif disc.natureza_disciplina == enumStatus.NaturezaDisciplina.TOPICOS_ESPECIAIS:
            cred_topicos += hist.creditos_integralizados
                
        elif disc.natureza_disciplina == enumStatus.NaturezaDisciplina.ESTUDO_DIRIGIDO:
            cred_estudo += hist.creditos_integralizados
            
        # 2. Verificação de Disciplinas Obrigatórias (Independente da Natureza)
        if getattr(disc, 'eh_obrigatoria', False):
            # Se for do Grupo 1
            if disc.grupo_pesquisa == enumStatus.GrupoPesquisa.GRUPO_1:
                qtd_obrigatorias_grupo1 += 1
                qtd_obrigatorias_grupos_1_2_3 += 1
                
            # Se for do Grupo 2 ou 3
            elif disc.grupo_pesquisa in (enumStatus.GrupoPesquisa.GRUPO_2, enumStatus.GrupoPesquisa.GRUPO_3):
                qtd_obrigatorias_grupos_1_2_3 += 1

    # Aplicação dos tetos (máximo de 8 para tópicos, máximo de 4 para estudo)
    cred_topicos_validos = min(cred_topicos, 8)
    cred_estudo_validos = min(cred_estudo, 4)
    total_creditos = cred_basicas + cred_eletivas + cred_topicos_validos + cred_estudo_validos

    # Validação das regras de créditos
    regra_creditos_ok = True
    if total_creditos < 24:
        pendencias.append(f"Créditos insuficientes: {total_creditos}/24.")
        regra_creditos_ok = False
    if cred_basicas < 4:
        pendencias.append(f"Faltam créditos em disciplinas básicas (Atual: {cred_basicas}, Mínimo: 4).")
        regra_creditos_ok = False
    if cred_eletivas < 4:
        pendencias.append(f"Faltam créditos em eletivas (Atual: {cred_eletivas}, Mínimo: 4).")
        regra_creditos_ok = False
        
    req_obrigatorias_ok = (qtd_obrigatorias_grupo1 >= 1) and (qtd_obrigatorias_grupos_1_2_3 >= 2)
    if not req_obrigatorias_ok:
        pendencias.append("Não cumpriu a regra de disciplinas obrigatórias (Mín. 1 do Grupo 1 e Mín. 2 nos Grupos 1, 2 ou 3).")
        regra_creditos_ok = False

    # ==========================================
    # 2. PROFICIÊNCIA
    # ==========================================
    proficiencia = db.query(Proficiencia).filter(
        Proficiencia.id_estudante == id_estudante,
        Proficiencia.status_certificado == enumStatus.StatusCertificadoProficiencia.ENTREGUE, # CORRIGIDO: ENTREGUE em vez de APROVADO
        Proficiencia.consolidada_sigaa == True
    ).first()
    regra_proficiencia_ok = proficiencia is not None
    if not regra_proficiencia_ok:
        pendencias.append("Proficiência em língua estrangeira pendente ou não consolidada.")

    # ==========================================
    # 3. ESTÁGIO DOCÊNCIA
    # ==========================================
    estagio = db.query(EstagioDocencia).filter(
        EstagioDocencia.id_estudante == id_estudante,
        EstagioDocencia.status_relatorio == enumStatus.StatusRelatorioEstagio.APROVADO
    ).first()
    regra_estagio_ok = estagio is not None
    if not regra_estagio_ok:
        pendencias.append("Relatório de Estágio Docência pendente ou não aprovado.")

    # ==========================================
    # 4. QUALIFICAÇÃO
    # ==========================================
    qualificacao = db.query(Qualificacao).join(Dissertacao).filter(
        Dissertacao.id_estudante == id_estudante,
        Qualificacao.status_qualificacao == enumStatus.StatusQualificacao.ENTREGUE # CORRIGIDO: ENTREGUE em vez de APROVADO
    ).first()
    regra_qualificacao_ok = qualificacao is not None
    if not regra_qualificacao_ok:
        pendencias.append("Proposta de dissertação (Qualificação) não aprovada.")

    # ==========================================
    # 5. ARTIGO (Qualis >= B2)
    # ==========================================
    qualis_validos = ["A1", "A2", "A3", "A4", "B1", "B2"]
    artigo = db.query(SubmissaoArtigo).filter(
        SubmissaoArtigo.id_estudante == id_estudante,
        SubmissaoArtigo.status_validacao_colegiado == enumStatus.StatusValidacaoColegiadoArtigo.APROVADA, # CORRIGIDO: APROVADA em vez de APROVADO
        SubmissaoArtigo.qualis.in_(qualis_validos)
    ).first()
    regra_artigo_ok = artigo is not None
    if not regra_artigo_ok:
        pendencias.append("Falta submissão de artigo aprovado com Qualis mínimo B2.")

    # ==========================================
    # CONSOLIDAÇÃO FINAL
    # ==========================================
    apto_geral = all([
        regra_creditos_ok, 
        regra_proficiencia_ok, 
        regra_estagio_ok, 
        regra_qualificacao_ok, 
        regra_artigo_ok
    ])

    return StatusDefesaResponse(
        id_estudante=id_estudante,
        apto_para_defesa=apto_geral,
        detalhe_creditos=DetalheCreditos(
            total_valido=total_creditos,
            basicas=cred_basicas,
            eletivas=cred_eletivas,
            topicos_especiais=cred_topicos,
            estudo_dirigido=cred_estudo,
            requisito_obrigatorias_cumprido=req_obrigatorias_ok
        ),
        requisitos=RequisitosDefesa(
            creditos=regra_creditos_ok,
            proficiencia=regra_proficiencia_ok,
            estagio_docencia=regra_estagio_ok,
            qualificacao=regra_qualificacao_ok,
            artigo=regra_artigo_ok
        ),
        pendencias_detalhadas=pendencias
    )
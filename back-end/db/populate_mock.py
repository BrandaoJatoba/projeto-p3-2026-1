"""
Carga inicial de dados sintéticos (mock) para desenvolvimento.

Pré-requisito: rodar o init_database.py antes (perfis, gatilhos e disciplinas).
Data de referência dos cenários: novembro/2026.

Os prazos NÃO são digitados à mão: cada estudante nasce com os prazos regimentais
(AcademicTrackingService) e, no fim, o prazos_service recalcula tudo com
prorrogações e suspensões. Assim o mock exercita as mesmas regras do sistema.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from db.database import SessionLocal
from db import models
import db.enumStatus as E
from services.academic_tracking_service import AcademicTrackingService
from services.prazos_service import recalcular_prazos_estudante

# ==========================================================================
# DADOS BASE
# ==========================================================================
SEMESTRES = [
    ("2023.1", date(2023, 3, 1), date(2023, 7, 15)),
    ("2023.2", date(2023, 8, 1), date(2023, 12, 15)),
    ("2024.1", date(2024, 3, 1), date(2024, 7, 15)),
    ("2024.2", date(2024, 8, 1), date(2024, 12, 15)),
    ("2025.1", date(2025, 3, 1), date(2025, 7, 15)),
    ("2025.2", date(2025, 8, 1), date(2025, 12, 15)),
    ("2026.1", date(2026, 3, 1), date(2026, 7, 15)),
    ("2026.2", date(2026, 8, 1), date(2026, 12, 15)),   # semestre corrente
    ("2027.1", date(2027, 3, 1), date(2027, 7, 15)),    # futuro (testar matrícula)
]
SEMESTRE_CORRENTE = "2026.2"
ULTIMO_SEMESTRE_CONCLUIDO = "2026.1"

# (motivo, semestre, início, fim, dias_suspensos)
SUSPENSOES = [
    ("Greve dos Servidores", "2024.1", date(2024, 4, 10), date(2024, 5, 25), 45),
    ("Paralisação Institucional (mock)", "2026.1", date(2026, 5, 4), date(2026, 5, 15), 11),
]

PROFESSORES = [
    "Alan Turing", "Ada Lovelace", "Donald Knuth",
    "Grace Hopper", "Edsger Dijkstra", "Barbara Liskov",
]

# ==========================================================================
# ESTUDANTES (cenários)
# ==========================================================================
# Cada chave de nível superior é opcional, exceto matricula/nome/status/semestre.
ESTUDANTES = [
    {
        "cenario": "Ingressante recente, ainda cursando disciplinas; SIGAA vazio",
        "matricula": "20252001", "nome": "Ana Beatriz Souza",
        "status": E.StatusEstudanteEnum.ATIVO, "semestre": "2025.2",
        "prof": 1, "bolsista": True, "sigaa": None,
        "titulo": "Detecção de Anomalias em Séries Temporais",
        "disciplinas": {"BASICAS": 1, "ELETIVAS": 2},
        "extras": [
            {"codigo": "PPGI 011", "semestre": "2026.2", "conceito": None, "status": "PENDENTE"},
            {"codigo": "PPGI 029", "semestre": "2026.2", "conceito": None, "status": "PENDENTE"},
        ],
        "proficiencia": {"status": "PENDENTE"},
        "estagio": {"status_proposta": "SUBMETIDA", "data_entrega_proposta": date(2026, 9, 15),
                    "status_relatorio": "PENDENTE", "data_entrega_relatorio": None,
                    "semestre": "2026.2", "supervisor": 0},
    },
    {
        "cenario": "Reta final: qualificada, banca solicitada, defesa prorrogada em 6 meses",
        "matricula": "20242002", "nome": "Bruno Carvalho Lima",
        "status": E.StatusEstudanteEnum.ATIVO, "semestre": "2024.2",
        "prof": 0, "bolsista": True, "sigaa": None,
        "titulo": "Testes Automatizados de Sistemas Baseados em IA",
        "disciplinas": {"BASICAS": 2, "ELETIVAS": 3, "TOPICOS_ESPECIAIS": 1},
        "proficiencia": {"status": "ENTREGUE", "data": date(2025, 5, 12), "sigaa": True},
        "estagio": {"status_proposta": "APROVADA", "data_entrega_proposta": date(2025, 4, 2),
                    "status_relatorio": "APROVADO", "data_entrega_relatorio": date(2025, 12, 5),
                    "semestre": "2025.1", "supervisor": 0},
        "artigos": [{"titulo": "Mutation Testing para Modelos de ML", "qualis": "B1", "tipo": "EVENTO",
                     "status_comprovante": "SUBMETIDA", "data_entrega": date(2026, 2, 10),
                     "status_validacao": "APROVADA"}],
        "qualificacoes": [{"tentativa": 1, "status": "ENTREGUE", "retorno": None,
                           "data_realizacao": date(2025, 12, 10)}],
        "defesa": {"status_defesa": "EM_HOMOLOGACAO", "status_homologacao_banca": "SOLICITADA",
                   "data_solicitacao_banca": date(2026, 10, 26)},
        "prorrogacoes": [
            {"tipo": "QUALIFICACAO", "meses": 3, "pedido": date(2025, 10, 1), "resultado": "INDEFERIDO"},
            {"tipo": "DEFESA", "meses": 6, "pedido": date(2026, 6, 10), "resultado": "DEFERIDO"},
        ],
    },
    {
        "cenario": "Titulada; ingressou ANTES da greve de 2024 (recebe +45 dias)",
        "matricula": "20241003", "nome": "Carla Mendes Rocha",
        "status": E.StatusEstudanteEnum.TITULADO, "semestre": "2024.1",
        "prof": 2, "bolsista": False, "sigaa": date(2026, 4, 15),
        "titulo": "Otimização Bioinspirada para Roteamento",
        "disciplinas": {"BASICAS": 2, "ELETIVAS": 3, "TOPICOS_ESPECIAIS": 1},
        "proficiencia": {"status": "ENTREGUE", "data": date(2024, 9, 3), "sigaa": True},
        "estagio": {"status_proposta": "APROVADA", "data_entrega_proposta": date(2024, 9, 20),
                    "status_relatorio": "APROVADO", "data_entrega_relatorio": date(2025, 2, 14),
                    "semestre": "2024.2", "supervisor": 2},
        "artigos": [{"titulo": "Bio-inspired Routing in WSN", "qualis": "A3", "tipo": "PERIÓDICO",
                     "status_comprovante": "PUBLICADO", "data_entrega": date(2025, 6, 30),
                     "status_validacao": "APROVADA"}],
        "qualificacoes": [{"tentativa": 1, "status": "ENTREGUE", "retorno": None,
                           "data_realizacao": date(2025, 9, 26)}],
        "defesa": {"status_defesa": "CONCLUIDO", "status_homologacao_banca": "APROVADA_COLEGIADO",
                   "data_solicitacao_banca": date(2026, 2, 20), "data_realizacao": date(2026, 4, 2),
                   "conceito_defesa": "APROVADO", "prazo_versao_final": date(2026, 5, 2),
                   "prazo_limite_processo_diploma": date(2026, 6, 1),
                   "status_processo_diploma": "PROCESSO_ABERTO"},
    },
    {
        "cenario": "Reprovado na 1ª qualificação, aprovado na 2ª; falta artigo; SIGAA manual divergente",
        "matricula": "20251004", "nome": "Diego Ferreira Alves",
        "status": E.StatusEstudanteEnum.ATIVO, "semestre": "2025.1",
        "prof": 3, "bolsista": True, "sigaa": date(2027, 3, 1),
        "titulo": "Classificação de Imagens Médicas com Poucos Dados",
        "disciplinas": {"BASICAS": 2, "ELETIVAS": 3},
        "extras": [{"codigo": "PPGI 040", "semestre": "2026.2", "conceito": None, "status": "PENDENTE"}],
        "proficiencia": {"status": "ENTREGUE", "data": date(2025, 9, 9), "sigaa": False},
        "estagio": {"status_proposta": "APROVADA", "data_entrega_proposta": date(2026, 3, 10),
                    "status_relatorio": "PENDENTE", "data_entrega_relatorio": None,
                    "semestre": "2026.1", "supervisor": 3},
        "qualificacoes": [
            {"tentativa": 1, "status": "REPROVADO", "retorno": "Cadastrou Banca",
             "data_realizacao": date(2026, 6, 10)},
            {"tentativa": 2, "status": "ENTREGUE", "retorno": None,
             "data_realizacao": date(2026, 9, 2)},
        ],
    },
    {
        "cenario": "Desligada: conceito D duas vezes na mesma disciplina e reprovação definitiva",
        "matricula": "20232005", "nome": "Elisa Nascimento Dias",
        "status": E.StatusEstudanteEnum.DESLIGADO, "semestre": "2023.2",
        "prof": 4, "bolsista": False, "sigaa": None,
        "titulo": "Modelagem de Sistemas de Tempo Real",
        "disciplinas": {"BASICAS": 1, "ELETIVAS": 1},
        "extras": [
            {"codigo": "PPGI 002", "semestre": "2023.2", "conceito": "D", "status": "REPROVADO"},
            {"codigo": "PPGI 002", "semestre": "2024.1", "conceito": "D", "status": "REPROVADO"},
        ],
        "proficiencia": {"status": "PENDENTE"},
        "qualificacoes": [
            {"tentativa": 1, "status": "REPROVADO", "retorno": None, "data_realizacao": date(2025, 2, 20)},
            {"tentativa": 2, "status": "REPROVADO_DEFINITIVO", "retorno": None,
             "data_realizacao": date(2025, 5, 15)},
        ],
        "defesa": {"status_defesa": "CANCELADO"},
    },
    {
        "cenario": "Qualificação vence em dias: prorrogação deferida + novo pedido em análise",
        "matricula": "20251006", "nome": "Gustavo Pereira Costa",
        "status": E.StatusEstudanteEnum.ATIVO, "semestre": "2025.1",
        "prof": 5, "bolsista": True, "sigaa": None,
        "titulo": "Agentes Inteligentes para Educação Adaptativa",
        "disciplinas": {"BASICAS": 2, "ELETIVAS": 2},
        "proficiencia": {"status": "ENTREGUE", "data": date(2025, 10, 20), "sigaa": True},
        "estagio": {"status_proposta": "APROVADA", "data_entrega_proposta": date(2025, 9, 15),
                    "status_relatorio": "SUBMETIDO", "data_entrega_relatorio": date(2026, 3, 20),
                    "semestre": "2025.2", "supervisor": 5},
        "qualificacoes": [{"tentativa": 1, "status": "PENDENTE", "retorno": "Solicitou Prorrogação",
                           "data_realizacao": None}],
        "prorrogacoes": [
            {"tipo": "QUALIFICACAO", "meses": 2, "pedido": date(2026, 8, 20), "resultado": "DEFERIDO"},
            {"tipo": "QUALIFICACAO", "meses": 3, "pedido": date(2026, 11, 5), "resultado": "EM ANÁLISE"},
        ],
    },
    {
        "cenario": "Ingressou DEPOIS das suspensões (não deve receber dias extras)",
        "matricula": "20262007", "nome": "Helena Barbosa Teixeira",
        "status": E.StatusEstudanteEnum.ATIVO, "semestre": "2026.2",
        "prof": 0, "bolsista": True, "sigaa": None,
        "titulo": None,
        "disciplinas": {},
        "extras": [
            {"codigo": "PPGI 001", "semestre": "2026.2", "conceito": None, "status": "PENDENTE"},
            {"codigo": "PPGI 002", "semestre": "2026.2", "conceito": None, "status": "PENDENTE"},
        ],
    },
    {
        "cenario": "Pós-defesa: aprovado condicionalmente, aguardando versão final (60 dias)",
        "matricula": "20242008", "nome": "Igor Tavares Santos",
        "status": E.StatusEstudanteEnum.POS_DEFESA, "semestre": "2024.2",
        "prof": 2, "bolsista": False, "sigaa": None,
        "titulo": "Aprendizado por Reforço em Ambientes Não Estacionários",
        "disciplinas": {"BASICAS": 2, "ELETIVAS": 3, "TOPICOS_ESPECIAIS": 1},
        "proficiencia": {"status": "ENTREGUE", "data": date(2025, 4, 8), "sigaa": True},
        "estagio": {"status_proposta": "APROVADA", "data_entrega_proposta": date(2025, 3, 25),
                    "status_relatorio": "APROVADO", "data_entrega_relatorio": date(2025, 11, 28),
                    "semestre": "2025.1", "supervisor": 2},
        "artigos": [{"titulo": "Non-stationary RL: a Survey", "qualis": "A2", "tipo": "PERIÓDICO",
                     "status_comprovante": "PUBLICADO", "data_entrega": date(2026, 1, 18),
                     "status_validacao": "APROVADA"}],
        "qualificacoes": [{"tentativa": 1, "status": "ENTREGUE", "retorno": None,
                           "data_realizacao": date(2025, 11, 20)}],
        "defesa": {"status_defesa": "AGUARDANDO_VERSAO_FINAL", "status_homologacao_banca": "APROVADA_COLEGIADO",
                   "data_solicitacao_banca": date(2026, 9, 10), "data_realizacao": date(2026, 10, 15),
                   "conceito_defesa": "APROVADO_CONDICIONALMENTE", "prazo_versao_final": date(2026, 12, 14),
                   "prazo_limite_processo_diploma": date(2026, 12, 14),
                   "status_processo_diploma": "PENDENTE"},
        "prorrogacoes": [{"tipo": "DEFESA", "meses": 3, "pedido": date(2026, 5, 20), "resultado": "DEFERIDO"}],
    },
]

# (matrícula, código do prazo, dias de antecedência, status, data de envio)
ALERTAS = [
    ("20251006", "QUALIFICACAO", 90, "ENVIADO", datetime(2026, 8, 14, 8, 0)),
    ("20251006", "QUALIFICACAO", 30, "ENVIADO", datetime(2026, 10, 13, 8, 0)),
    ("20251004", "QUALIFICACAO", 30, "FALHA", datetime(2026, 8, 3, 8, 0)),
    ("20242008", "DEFESA", 30, "ENVIADO", datetime(2026, 10, 13, 8, 0)),
]


# ==========================================================================
# FUNÇÕES AUXILIARES
# ==========================================================================
def _selecionar(lista, n, deslocamento):
    """Pega n itens da lista (circular), variando o ponto de partida por estudante."""
    if not lista or n <= 0:
        return []
    return [lista[(deslocamento + i) % len(lista)] for i in range(n)]


def _carregar_semestres(db: Session) -> dict:
    semestres = {}
    for codigo, inicio, fim in SEMESTRES:
        sem = db.query(models.SemestreLetivo).filter_by(codigo_semestre=codigo).first()
        if not sem:
            sem = models.SemestreLetivo(
                codigo_semestre=codigo, data_inicio_real=inicio,
                data_fim_real=fim, dias_letivos=100,
            )
            db.add(sem)
        semestres[codigo] = sem
    db.commit()
    return semestres


def _carregar_suspensoes(db: Session, semestres: dict):
    for motivo, cod_sem, inicio, fim, dias in SUSPENSOES:
        if not db.query(models.SuspensaoCalendario).filter_by(motivo=motivo).first():
            db.add(models.SuspensaoCalendario(
                id_semestre=semestres[cod_sem].id_semestre, motivo=motivo,
                data_inicio_suspensao=inicio, data_fim_suspensao=fim, dias_suspensos=dias,
            ))
    db.commit()


def _carregar_professores(db: Session) -> list:
    professores = []
    for nome in PROFESSORES:
        prof = db.query(models.Professor).filter_by(nome_professor=nome).first()
        if not prof:
            prof = models.Professor(nome_professor=nome)
            db.add(prof)
        professores.append(prof)
    db.commit()
    return professores


def _carregar_catalogo(db: Session) -> dict:
    naturezas = ["BASICAS", "ELETIVAS", "TOPICOS_ESPECIAIS", "ESTUDO_DIRIGIDO", "DOCENCIA"]
    return {
        n: db.query(models.Disciplina)
             .filter_by(natureza_disciplina=n)
             .order_by(models.Disciplina.id_disciplina).all()
        for n in naturezas
    }


def _criar_estudante(db, spec, indice, semestres, professores, catalogo):
    if db.query(models.Estudante).filter_by(matricula=spec["matricula"]).first():
        print(f"  - {spec['nome']}: já existe, ignorado.")
        return None

    sem = semestres[spec["semestre"]]
    codigos = [c for c, _, _ in SEMESTRES]

    # --- Estudante + Dissertação ---
    est = models.Estudante(
        matricula=spec["matricula"], nome_discente=spec["nome"], status_atual=spec["status"],
        id_semestre=sem.id_semestre, id_orientador=professores[spec["prof"]].id_professor,
        eh_bolsista=spec["bolsista"], prazo_conclusao_sigaa=spec["sigaa"],
        email=f"aluno{spec['matricula']}@ic.ufal.br",
    )
    db.add(est)
    db.flush()

    diss = models.Dissertacao(
        id_estudante=est.id_estudante, titulo=spec.get("titulo"), data_inicio=sem.data_inicio_real,
    )
    db.add(diss)
    db.flush()

    # --- Qualificação(ões) e Defesa, com prazos regimentais iniciais ---
    prazos = AcademicTrackingService.calcular_prazos_iniciais(sem.data_inicio_real)
    for q in spec.get("qualificacoes", [{"tentativa": 1, "status": "PENDENTE",
                                         "retorno": None, "data_realizacao": None}]):
        db.add(models.Qualificacao(
            id_dissertacao=diss.id_dissertacao,
            prazo_maximo_qualificacao=prazos.prazo_maximo_qualificacao,
            status_qualificacao=q["status"], retorno_qualificacao=q["retorno"],
            tentativa=q["tentativa"], data_realizacao=q["data_realizacao"],
        ))

    dados_defesa = {"status_defesa": "PENDENTE", **spec.get("defesa", {})}
    db.add(models.Defesa(
        id_dissertacao=diss.id_dissertacao,
        prazo_maximo_defesa=prazos.prazo_maximo_defesa, **dados_defesa,
    ))

    # --- Histórico de disciplinas ---
    aprovadas = []
    for natureza, qtd in spec.get("disciplinas", {}).items():
        aprovadas += _selecionar(catalogo[natureza], qtd, indice)
    idx_ingresso = codigos.index(spec["semestre"])
    idx_max = codigos.index(ULTIMO_SEMESTRE_CONCLUIDO)
    conceitos = ["A", "B", "A", "C"]
    for i, disc in enumerate(aprovadas):
        sem_hist = semestres[codigos[min(idx_ingresso + i // 2, idx_max)]]
        db.add(models.HistoricoDisciplina(
            id_estudante=est.id_estudante, id_disciplina=disc.id_disciplina,
            id_semestre=sem_hist.id_semestre, conceito=conceitos[i % len(conceitos)],
            status_disciplina="APROVADO",
        ))
    for ex in spec.get("extras", []):
        disc = db.query(models.Disciplina).filter_by(codigo_disciplina=ex["codigo"]).first()
        if disc:
            db.add(models.HistoricoDisciplina(
                id_estudante=est.id_estudante, id_disciplina=disc.id_disciplina,
                id_semestre=semestres[ex["semestre"]].id_semestre,
                conceito=ex["conceito"], status_disciplina=ex["status"],
            ))

    # --- Proficiência ---
    if "proficiencia" in spec:
        p = spec["proficiencia"]
        db.add(models.Proficiencia(
            id_estudante=est.id_estudante, status_certificado=p["status"],
            data_entrega_certificado=p.get("data"), consolidada_sigaa=p.get("sigaa", False),
        ))

    # --- Estágio docência ---
    if "estagio" in spec:
        g = spec["estagio"]
        disc_estagio = (catalogo["DOCENCIA"] or catalogo["ELETIVAS"])[0]
        db.add(models.EstagioDocencia(
            id_estudante=est.id_estudante,
            id_professor_supervisor=professores[g["supervisor"]].id_professor,
            id_disciplina=disc_estagio.id_disciplina, id_semestre=semestres[g["semestre"]].id_semestre,
            status_proposta=g["status_proposta"], data_entrega_proposta=g["data_entrega_proposta"],
            status_relatorio=g["status_relatorio"], data_entrega_relatorio=g["data_entrega_relatorio"],
        ))

    # --- Artigos ---
    for a in spec.get("artigos", []):
        db.add(models.SubmissaoArtigo(
            titulo=a["titulo"], id_estudante=est.id_estudante, qualis=a["qualis"], tipo=a["tipo"],
            status_comprovante=a["status_comprovante"], data_entrega=a["data_entrega"],
            status_validacao_colegiado=a["status_validacao"],
        ))

    # --- Prorrogações ---
    for p in spec.get("prorrogacoes", []):
        db.add(models.ProrrogacaoHistorico(
            id_estudante=est.id_estudante, tipo_prazo=p["tipo"], quantidade_meses=p["meses"],
            data_pedido=p["pedido"], resultado_pedido=p["resultado"],
        ))

    db.commit()
    return est


def _carregar_alertas(db: Session):
    for matricula, cod_prazo, dias, status, quando in ALERTAS:
        est = db.query(models.Estudante).filter_by(matricula=matricula).first()
        gatilho = (
            db.query(models.GatilhoAlerta)
            .join(models.TipoPrazo, models.TipoPrazo.id_tipo_prazo == models.GatilhoAlerta.id_tipo_prazo)
            .filter(models.TipoPrazo.codigo_prazo == cod_prazo,
                    models.GatilhoAlerta.dias_antecedencia == dias)
            .first()
        )
        if not est or not gatilho:
            continue
        ja_existe = db.query(models.HistoricoAlertaEnviado).filter_by(
            id_estudante=est.id_estudante, id_gatilho=gatilho.id_gatilho).first()
        if not ja_existe:
            db.add(models.HistoricoAlertaEnviado(
                id_estudante=est.id_estudante, id_gatilho=gatilho.id_gatilho,
                data_envio=quando, destinatario_email=est.email, status_envio=status,
            ))
    db.commit()


# ==========================================================================
# EXECUÇÃO
# ==========================================================================
def criar_mock_data(db: Session):
    print("Iniciando a inserção de mock data...")

    catalogo = _carregar_catalogo(db)
    if not catalogo["BASICAS"] and not catalogo["ELETIVAS"]:
        print("Erro: nenhuma disciplina encontrada. Execute o init_database.py primeiro.")
        return

    semestres = _carregar_semestres(db)
    _carregar_suspensoes(db, semestres)
    professores = _carregar_professores(db)

    criados = []
    for i, spec in enumerate(ESTUDANTES):
        est = _criar_estudante(db, spec, i, semestres, professores, catalogo)
        if est:
            criados.append(est)

    # Recalcula com as regras reais (prorrogações DEFERIDAS + suspensões aplicáveis)
    for est in criados:
        recalcular_prazos_estudante(db, est.id_estudante)

    # Prazo de solicitação da banca = 30 dias antes do prazo da defesa (Regimento, Art. 37, VI)
    for est in criados:
        diss = db.query(models.Dissertacao).filter_by(id_estudante=est.id_estudante).first()
        defesa = db.query(models.Defesa).filter_by(id_dissertacao=diss.id_dissertacao).first()
        if defesa and defesa.prazo_solicitacao_homologacao_banca is None:
            defesa.prazo_solicitacao_homologacao_banca = defesa.prazo_maximo_defesa - timedelta(days=30)
    db.commit()

    _carregar_alertas(db)

    # --- Resumo ---
    print("\nEstudantes criados (prazos após recálculo):")
    for est, spec in zip(criados, [s for s in ESTUDANTES
                                   if s["matricula"] in {e.matricula for e in criados}]):
        db.refresh(est)
        diss = db.query(models.Dissertacao).filter_by(id_estudante=est.id_estudante).first()
        qual = (db.query(models.Qualificacao).filter_by(id_dissertacao=diss.id_dissertacao)
                .order_by(models.Qualificacao.tentativa.desc()).first())
        defesa = db.query(models.Defesa).filter_by(id_dissertacao=diss.id_dissertacao).first()
        print(f"  {est.matricula} {est.nome_discente:<26} qualif: {qual.prazo_maximo_qualificacao} | "
              f"defesa: {defesa.prazo_maximo_defesa} | sigaa: {est.prazo_conclusao_sigaa}")
        print(f"      -> {spec['cenario']}")

    print("\nMock data inserido com sucesso!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        criar_mock_data(db)
    finally:
        db.close()
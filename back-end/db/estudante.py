from datetime import date
from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy import or_, func, case
from sqlalchemy.orm import Session, selectinload

from db import models
from db.models import Estudante, EstudanteOrientador, HistoricoDisciplina, Disciplina
from db.enumStatus import (
    StatusEstudanteEnum,
    StatusQualificacao,
    StatusDefesa,
    StatusDisciplina,
    ConceitoHistorico,
    TipoOrientacao,
)
from services.academic_tracking_service import AcademicTrackingService


def obter_resumo_creditos_por_perfil(db_connection: Session, id_estudante: int = None):
    """
    Agrupa os créditos integralizados por grupo de disciplina e identifica
    quantas vezes o discente obteve conceito 'D'.
    """
    soma_creditos = func.sum(
        case(
            (
                HistoricoDisciplina.status_disciplina == StatusDisciplina.APROVADO.value,
                HistoricoDisciplina.creditos_integralizados,
            ),
            else_=0,
        )
    ).label("total_creditos")

    qtd_conceito_d = func.sum(
        case(
            (HistoricoDisciplina.conceito == ConceitoHistorico.D.value, 1),
            else_=0,
        )
    ).label("qtd_conceito_d")

    query = (
        db_connection.query(
            Estudante.id_estudante,
            Estudante.nome_discente,
            Disciplina.grupo_disciplina,
            soma_creditos,
            qtd_conceito_d,
        )
        .join(HistoricoDisciplina, Estudante.id_estudante == HistoricoDisciplina.id_estudante)
        .join(Disciplina, HistoricoDisciplina.id_disciplina == Disciplina.id_disciplina)
        .group_by(
            Estudante.id_estudante,
            Estudante.nome_discente,
            Disciplina.grupo_disciplina,
        )
    )

    if id_estudante:
        query = query.filter(Estudante.id_estudante == id_estudante)

    return query.all()


# ==========================================================================
# GESTÃO DE ORIENTAÇÕES (N:N)
# ==========================================================================

def _opcoes_carregamento_orientacoes():
    """Carrega antecipadamente os vínculos de orientação e os dados dos professores."""
    return (
        selectinload(models.Estudante.orientacoes)
        .selectinload(models.EstudanteOrientador.professor)
    )


def _normalizar_lista_orientacoes(
    orientacoes: Optional[List[Any]] = None,
    id_orientador_legado: Optional[int] = None,
) -> List[Tuple[int, str]]:
    """
    Converte a lista de orientações (dicts ou schemas Pydantic) ou o atalho legado
    `id_orientador` em pares únicos `(id_professor, tipo_orientacao)`.
    """
    if orientacoes is not None:
        resultado: List[Tuple[int, str]] = []
        vistos = set()
        for item in orientacoes:
            if isinstance(item, dict):
                id_prof = item["id_professor"]
                papel = item.get("tipo_orientacao", TipoOrientacao.ORIENTADOR)
            else:
                id_prof = item.id_professor
                papel = item.tipo_orientacao

            papel_str = papel.value if isinstance(papel, TipoOrientacao) else str(papel)
            if id_prof in vistos:
                raise ValueError("Um mesmo professor não pode ser vinculado duas vezes ao mesmo discente.")
            vistos.add(id_prof)
            resultado.append((id_prof, papel_str))

        qtd_principais = sum(1 for _, papel in resultado if papel == TipoOrientacao.ORIENTADOR.value)
        if qtd_principais > 1:
            raise ValueError("Um discente pode ter no máximo 1 orientador principal (ORIENTADOR).")
        return resultado

    if id_orientador_legado is not None:
        return [(id_orientador_legado, TipoOrientacao.ORIENTADOR.value)]

    return []


def sincronizar_orientacoes_estudante(
    db_connection: Session,
    estudante: models.Estudante,
    orientacoes_normalizadas: List[Tuple[int, str]],
) -> None:
    """
    Sincroniza a coleção `estudante.orientacoes` com a lista informada sem fazer commit
    (para compor a mesma transação da criação ou atualização do estudante).

    Ordem segura para o índice único parcial `uq_estudante_orientador_principal`:
    1. Remove vínculos ausentes e rebaixa/ajusta papéis existentes com flush().
    2. Insere novos vínculos e promove o novo orientador principal.
    """
    ids_professores = [id_prof for id_prof, _ in orientacoes_normalizadas]
    if ids_professores:
        existentes = {
            p.id_professor
            for p in db_connection.query(models.Professor.id_professor)
            .filter(models.Professor.id_professor.in_(ids_professores))
            .all()
        }
        faltantes = set(ids_professores) - existentes
        if faltantes:
            raise ValueError(f"Professor(es) não encontrado(s): {sorted(faltantes)}")

    mapa_desejado = dict(orientacoes_normalizadas)
    atuais_por_prof = {v.id_professor: v for v in list(estudante.orientacoes)}

    # 1. Remove quem saiu e rebaixa quem deixou de ser ORIENTADOR principal
    for id_prof, vinculo in list(atuais_por_prof.items()):
        if id_prof not in mapa_desejado:
            db_connection.delete(vinculo)
        elif (
            vinculo.tipo_orientacao == TipoOrientacao.ORIENTADOR.value
            and mapa_desejado[id_prof] != TipoOrientacao.ORIENTADOR.value
        ):
            vinculo.tipo_orientacao = mapa_desejado[id_prof]

    db_connection.flush()

    # 2. Atualiza ou cria os vínculos desejados
    for id_prof, papel_str in orientacoes_normalizadas:
        if id_prof in atuais_por_prof:
            atuais_por_prof[id_prof].tipo_orientacao = papel_str
        else:
            db_connection.add(
                models.EstudanteOrientador(
                    id_estudante=estudante.id_estudante,
                    id_professor=id_prof,
                    tipo_orientacao=papel_str,
                )
            )

    db_connection.flush()


def vincular_orientador_estudante(
    db_connection: Session,
    estudante: models.Estudante,
    id_professor: int,
    tipo_orientacao: Union[TipoOrientacao, str] = TipoOrientacao.ORIENTADOR,
) -> models.Estudante:
    """Adiciona ou atualiza um vínculo individual de orientação/coorientação."""
    papel_str = (
        tipo_orientacao.value
        if isinstance(tipo_orientacao, TipoOrientacao)
        else str(tipo_orientacao)
    )
    lista_atual = [
        (v.id_professor, v.tipo_orientacao)
        for v in estudante.orientacoes
        if v.id_professor != id_professor
    ]
    lista_atual.append((id_professor, papel_str))
    normalizada = _normalizar_lista_orientacoes(
        [{"id_professor": pid, "tipo_orientacao": papel} for pid, papel in lista_atual]
    )

    try:
        sincronizar_orientacoes_estudante(db_connection, estudante, normalizada)
        db_connection.commit()
        return buscar_estudante_por_id(db_connection, estudante.id_estudante)
    except Exception:
        db_connection.rollback()
        raise


def remover_orientador_estudante(
    db_connection: Session,
    estudante: models.Estudante,
    id_professor: int,
) -> bool:
    """Remove o vínculo entre um professor e um estudante. Retorna False se não existia."""
    vinculo = next(
        (v for v in estudante.orientacoes if v.id_professor == id_professor),
        None,
    )
    if not vinculo:
        return False

    try:
        db_connection.delete(vinculo)
        db_connection.commit()
        db_connection.refresh(estudante)
        return True
    except Exception:
        db_connection.rollback()
        raise


# ==========================================================================
# CRIAÇÃO COM MARCOS (Eager Creation) — usada pelo POST /estudantes
# ==========================================================================

def criar_estudante_com_marcos(
    db_connection: Session,
    matricula: str,
    nome_discente: str,
    semestre: models.SemestreLetivo,
    id_orientador: Optional[int] = None,
    orientacoes: Optional[List[Any]] = None,
    eh_bolsista: bool = False,
    prazo_conclusao_sigaa: Optional[date] = None,
    email: Optional[str] = None,
) -> models.Estudante:
    """
    Cria, em UMA única transação, o estudante, seus vínculos de orientação (N:N)
    e seus registros de acompanhamento: DISSERTACOES, QUALIFICACOES e DEFESAS.
    """
    orientacoes_normalizadas = _normalizar_lista_orientacoes(orientacoes, id_orientador)

    try:
        # 1. Estudante
        novo_estudante = models.Estudante(
            matricula=matricula,
            nome_discente=nome_discente,
            id_semestre=semestre.id_semestre,
            status_atual=StatusEstudanteEnum.ATIVO,
            eh_bolsista=eh_bolsista,
            prazo_conclusao_sigaa=prazo_conclusao_sigaa,
            email=email,
        )
        db_connection.add(novo_estudante)
        db_connection.flush()

        # 2. Vínculos de orientação / coorientação
        if orientacoes_normalizadas:
            sincronizar_orientacoes_estudante(
                db_connection, novo_estudante, orientacoes_normalizadas
            )

        # 3. Dissertação base, iniciando na data real de início do semestre
        nova_dissertacao = models.Dissertacao(
            id_estudante=novo_estudante.id_estudante,
            data_inicio=semestre.data_inicio_real,
        )
        db_connection.add(nova_dissertacao)
        db_connection.flush()

        # 4. Prazos regimentais (+18 e +24 meses)
        prazos = AcademicTrackingService.calcular_prazos_iniciais(semestre.data_inicio_real)

        # 5. Qualificação pendente
        db_connection.add(models.Qualificacao(
            id_dissertacao=nova_dissertacao.id_dissertacao,
            prazo_maximo_qualificacao=prazos.prazo_maximo_qualificacao,
            status_qualificacao=StatusQualificacao.PENDENTE.value,
            tentativa=1,
        ))

        # 6. Defesa pendente
        db_connection.add(models.Defesa(
            id_dissertacao=nova_dissertacao.id_dissertacao,
            prazo_maximo_defesa=prazos.prazo_maximo_defesa,
            status_defesa=StatusDefesa.PENDENTE.value,
        ))

        db_connection.commit()
        return buscar_estudante_por_id(db_connection, novo_estudante.id_estudante)
    except Exception:
        db_connection.rollback()
        raise


def buscar_marcos_do_estudante(
    db_connection: Session,
    id_estudante: int,
) -> Tuple[Optional[models.Dissertacao], Optional[models.Qualificacao], Optional[models.Defesa]]:
    """
    Retorna (dissertacao, qualificacao, defesa) do estudante.
    """
    dissertacao = (
        db_connection.query(models.Dissertacao)
        .filter(models.Dissertacao.id_estudante == id_estudante)
        .first()
    )
    if dissertacao is None:
        return None, None, None

    qualificacao = (
        db_connection.query(models.Qualificacao)
        .filter(models.Qualificacao.id_dissertacao == dissertacao.id_dissertacao)
        .order_by(models.Qualificacao.tentativa.desc(), models.Qualificacao.id_qualificacao.desc())
        .first()
    )
    defesa = (
        db_connection.query(models.Defesa)
        .filter(models.Defesa.id_dissertacao == dissertacao.id_dissertacao)
        .order_by(models.Defesa.id_defesa.desc())
        .first()
    )
    return dissertacao, qualificacao, defesa


# ==========================================================================
# CONSULTAS
# ==========================================================================

def buscar_estudante_por_id(db_connection: Session, id_estudante: int) -> Optional[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.id_estudante == id_estudante)
        .first()
    )


def buscar_estudante_por_matricula(db_connection: Session, matricula: str) -> Optional[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.matricula == matricula)
        .first()
    )


def buscar_estudante_por_email(db_connection: Session, email: str) -> Optional[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.email == email)
        .first()
    )


def listar_estudantes_filtrados(
    db_connection: Session,
    status_atual: Optional[StatusEstudanteEnum] = None,
    id_semestre: Optional[int] = None,
    id_orientador: Optional[int] = None,
    tipo_orientacao: Optional[TipoOrientacao] = None,
    eh_bolsista: Optional[bool] = None,
    busca: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    ordenar_por: str = "nome_discente",
    ordem_desc: bool = False,
) -> Tuple[int, List[models.Estudante]]:
    """
    Listagem paginada com filtros COMBINÁVEIS.
    Quando `id_orientador` é informado, busca discentes vinculados ao professor
    (como orientador principal ou coorientador, salvo se `tipo_orientacao` restringir).
    """
    query = db_connection.query(models.Estudante).options(_opcoes_carregamento_orientacoes())

    if status_atual is not None:
        query = query.filter(models.Estudante.status_atual == status_atual)
    if id_semestre is not None:
        query = query.filter(models.Estudante.id_semestre == id_semestre)
    if id_orientador is not None:
        criterios_orientacao = [models.EstudanteOrientador.id_professor == id_orientador]
        if tipo_orientacao is not None:
            papel = (
                tipo_orientacao.value
                if isinstance(tipo_orientacao, TipoOrientacao)
                else str(tipo_orientacao)
            )
            criterios_orientacao.append(models.EstudanteOrientador.tipo_orientacao == papel)
        query = query.filter(models.Estudante.orientacoes.any(*criterios_orientacao))
    if eh_bolsista is not None:
        query = query.filter(models.Estudante.eh_bolsista == eh_bolsista)
    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                models.Estudante.nome_discente.ilike(termo),
                models.Estudante.matricula.ilike(termo),
            )
        )

    colunas_validas = {
        "nome_discente": models.Estudante.nome_discente,
        "matricula": models.Estudante.matricula,
        "status_atual": models.Estudante.status_atual,
    }

    coluna = colunas_validas.get(ordenar_por, models.Estudante.nome_discente)

    if ordem_desc:
        query = query.order_by(coluna.desc())
    else:
        query = query.order_by(coluna.asc())

    total = query.count()
    itens = query.offset(skip).limit(limit).all()
    return total, itens


# ==========================================================================
# ATUALIZAÇÃO
# ==========================================================================

def _aplicar_atualizacao_orientacoes(
    db_connection: Session,
    estudante: models.Estudante,
    updates: Dict[str, Any],
) -> None:
    """Trata `orientacoes` (lista completa) ou `id_orientador` (atalho legado)."""
    if "orientacoes" in updates:
        lista = updates["orientacoes"] or []
        normalizada = _normalizar_lista_orientacoes(lista)
        sincronizar_orientacoes_estudante(db_connection, estudante, normalizada)
    elif "id_orientador" in updates:
        novo_id_principal = updates["id_orientador"]
        # Preserva coorientadores existentes e substitui apenas o orientador principal
        coorientadores = [
            (v.id_professor, v.tipo_orientacao)
            for v in estudante.orientacoes
            if v.tipo_orientacao == TipoOrientacao.COORIENTADOR.value
            and v.id_professor != novo_id_principal
        ]
        nova_lista = []
        if novo_id_principal is not None:
            nova_lista.append((novo_id_principal, TipoOrientacao.ORIENTADOR.value))
        nova_lista.extend(coorientadores)
        sincronizar_orientacoes_estudante(db_connection, estudante, nova_lista)


def atualizar_estudante_por_id(
    db_connection: Session,
    estudante: models.Estudante,
    updates: Dict[str, Any],
) -> models.Estudante:
    """
    Aplica apenas os campos enviados (vindo de model_dump(exclude_unset=True)).
    Recebe o objeto já buscado pela rota, que é quem decide o 404.
    """
    campos_protegidos = {"id_estudante", "matricula", "id_semestre", "orientacoes", "id_orientador"}

    try:
        for key, value in updates.items():
            if hasattr(estudante, key) and key not in campos_protegidos:
                setattr(estudante, key, value)

        if "orientacoes" in updates or "id_orientador" in updates:
            _aplicar_atualizacao_orientacoes(db_connection, estudante, updates)

        db_connection.commit()
        return buscar_estudante_por_id(db_connection, estudante.id_estudante)
    except Exception:
        db_connection.rollback()
        raise


# ==========================================================================
# FUNÇÕES AUXILIARES DE COMPATIBILIDADE
# ==========================================================================

def criar_estudante(
    db_connection: Session,
    matricula: str,
    nome_discente: str,
    id_semestre: int,
    status_atual: StatusEstudanteEnum = StatusEstudanteEnum.ATIVO,
    id_orientador: Optional[int] = None,
    orientacoes: Optional[List[Any]] = None,
    eh_bolsista: bool = False,
    prazo_conclusao_sigaa: Optional[date] = None,
    email: Optional[str] = None,
) -> models.Estudante:
    orientacoes_normalizadas = _normalizar_lista_orientacoes(orientacoes, id_orientador)
    try:
        novo_estudante = models.Estudante(
            matricula=matricula,
            nome_discente=nome_discente,
            status_atual=status_atual,
            id_semestre=id_semestre,
            eh_bolsista=eh_bolsista,
            prazo_conclusao_sigaa=prazo_conclusao_sigaa,
            email=email,
        )
        db_connection.add(novo_estudante)
        db_connection.flush()

        if orientacoes_normalizadas:
            sincronizar_orientacoes_estudante(
                db_connection, novo_estudante, orientacoes_normalizadas
            )

        db_connection.commit()
        return buscar_estudante_por_id(db_connection, novo_estudante.id_estudante)
    except Exception:
        db_connection.rollback()
        raise


def atualizar_estudante(
    db_connection: Session,
    matricula: str,
    updates: Dict[str, Any],
) -> Optional[models.Estudante]:
    estudante = buscar_estudante_por_matricula(db_connection, matricula)
    if not estudante:
        return None

    campos_protegidos = {"id_estudante", "orientacoes", "id_orientador"}

    try:
        for key, value in updates.items():
            if hasattr(estudante, key) and key not in campos_protegidos:
                setattr(estudante, key, value)

        if "orientacoes" in updates or "id_orientador" in updates:
            _aplicar_atualizacao_orientacoes(db_connection, estudante, updates)

        db_connection.commit()
        return buscar_estudante_por_id(db_connection, estudante.id_estudante)
    except Exception:
        db_connection.rollback()
        raise


def listar_estudantes(db_connection: Session) -> List[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .all()
    )


def buscar_estudantes_por_orientador(
    db_connection: Session,
    id_orientador: int,
    tipo_orientacao: Optional[TipoOrientacao] = None,
) -> List[models.Estudante]:
    criterios = [models.EstudanteOrientador.id_professor == id_orientador]
    if tipo_orientacao is not None:
        papel = (
            tipo_orientacao.value
            if isinstance(tipo_orientacao, TipoOrientacao)
            else str(tipo_orientacao)
        )
        criterios.append(models.EstudanteOrientador.tipo_orientacao == papel)

    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.orientacoes.any(*criterios))
        .all()
    )


def buscar_estudantes_por_semestre(db_connection: Session, id_semestre: int) -> List[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.id_semestre == id_semestre)
        .all()
    )


def buscar_estudantes_por_status(
    db_connection: Session,
    status_atual: Union[StatusEstudanteEnum, str],
) -> List[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.status_atual == status_atual)
        .all()
    )


def buscar_estudantes_por_bolsa(db_connection: Session, eh_bolsista: bool) -> List[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.eh_bolsista == eh_bolsista)
        .all()
    )


def buscar_estudantes_por_prazo_conclusao(db_connection: Session, prazo_conclusao_sigaa: date) -> List[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .options(_opcoes_carregamento_orientacoes())
        .filter(models.Estudante.prazo_conclusao_sigaa <= prazo_conclusao_sigaa)
        .all()
    )
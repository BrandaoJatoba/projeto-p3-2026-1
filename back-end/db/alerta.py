from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from db import models
from db.enumStatus import StatusEnvioAlerta, TipoOrientacao


# ==========================================================================
# AUXILIARES DE E-MAIL (CC DOS ORIENTADORES E COORIENTADORES)
# ==========================================================================

def _normalizar_emails_cc(
    emails: Optional[Union[str, List[str]]],
    excluir_email: Optional[str] = None,
) -> Optional[str]:
    """
    Normaliza uma lista ou string separada por vírgulas em uma string única
    limpa (ex.: 'prof1@ufal.br, prof2@ufal.br'), removendo duplicados e vazios.
    """
    if not emails:
        return None

    brutos = emails.split(",") if isinstance(emails, str) else emails
    email_excluido = excluir_email.strip().lower() if excluir_email else None

    vistos = set()
    limpos: List[str] = []
    for item in brutos:
        if not item:
            continue
        endereco = item.strip()
        chave = endereco.lower()
        if not endereco or chave == email_excluido or chave in vistos:
            continue
        vistos.add(chave)
        limpos.append(endereco)

    return ", ".join(limpos) if limpos else None


def obter_emails_cc_orientadores(
    db_connection: Session,
    id_estudante: int,
    destinatario_email: Optional[str] = None,
) -> Optional[str]:
    """
    Coleta os e-mails cadastrados do orientador principal e dos coorientadores
    do estudante (orientador principal primeiro, coorientadores em seguida).
    Retorna None caso nenhum docente vinculado possua e-mail.
    """
    vinculos = (
        db_connection.query(models.EstudanteOrientador)
        .options(selectinload(models.EstudanteOrientador.professor))
        .filter(models.EstudanteOrientador.id_estudante == id_estudante)
        .all()
    )

    vinculos_ordenados = sorted(
        vinculos,
        key=lambda v: (
            0 if v.tipo_orientacao == TipoOrientacao.ORIENTADOR.value else 1,
            (v.professor.nome_professor if v.professor else "").lower(),
        ),
    )

    emails_docentes = [
        v.professor.email
        for v in vinculos_ordenados
        if v.professor is not None and v.professor.email
    ]

    return _normalizar_emails_cc(emails_docentes, excluir_email=destinatario_email)


# ==========================================================================
# VERIFICAÇÃO ANTI-DUPLICIDADE (ANTI-SPAM)
# ==========================================================================

def ja_enviou_alerta(
    db_connection: Session,
    id_estudante: int,
    id_gatilho: int,
    apenas_enviados: bool = True,
) -> bool:
    """
    Verifica se já existe registro de envio para o par (estudante, gatilho),
    evitando disparos duplicados pelo motor de alertas.
    """
    query = db_connection.query(models.HistoricoAlertaEnviado.id_historico_alerta).filter(
        models.HistoricoAlertaEnviado.id_estudante == id_estudante,
        models.HistoricoAlertaEnviado.id_gatilho == id_gatilho,
    )

    if apenas_enviados:
        query = query.filter(
            models.HistoricoAlertaEnviado.status_envio == StatusEnvioAlerta.ENVIADO.value
        )

    return query.first() is not None


# ==========================================================================
# CRIAÇÃO (CREATE)
# ==========================================================================

def criar_historico_alerta(
    db_connection: Session,
    id_estudante: int,
    id_gatilho: int,
    destinatario_email: Optional[str] = None,
    emails_cc: Optional[Union[str, List[str]]] = None,
    status_envio: Union[StatusEnvioAlerta, str] = StatusEnvioAlerta.ENVIADO,
    data_envio: Optional[datetime] = None,
    preencher_cc_automaticamente: bool = True,
    assunto: Optional[str] = None,
    corpo_mensagem: Optional[str] = None,
) -> models.HistoricoAlertaEnviado:
    """
    Registra um disparo de alerta no histórico.

    - Se `destinatario_email` não for informado, utiliza o e-mail cadastrado do estudante.
    - Se `emails_cc` for None e `preencher_cc_automaticamente=True`, preenche
      automaticamente com os e-mails dos orientadores e coorientadores do discente.
    """
    estudante = (
        db_connection.query(models.Estudante)
        .filter(models.Estudante.id_estudante == id_estudante)
        .first()
    )
    if estudante is None:
        raise ValueError(f"Estudante com ID {id_estudante} não encontrado.")

    gatilho = (
        db_connection.query(models.GatilhoAlerta)
        .filter(models.GatilhoAlerta.id_gatilho == id_gatilho)
        .first()
    )
    if gatilho is None:
        raise ValueError(f"Gatilho de alerta com ID {id_gatilho} não encontrado.")

    email_destino = (destinatario_email or estudante.email or "").strip()
    if not email_destino:
        raise ValueError("Destinatário sem e-mail cadastrado para registro do alerta.")

    if emails_cc is not None:
        cc_final = _normalizar_emails_cc(emails_cc, excluir_email=email_destino)
    elif preencher_cc_automaticamente:
        cc_final = obter_emails_cc_orientadores(
            db_connection,
            id_estudante=id_estudante,
            destinatario_email=email_destino,
        )
    else:
        cc_final = None

    status_str = (
        status_envio.value
        if isinstance(status_envio, StatusEnvioAlerta)
        else str(status_envio)
    )

    try:
        novo_registro = models.HistoricoAlertaEnviado(
            id_estudante=id_estudante,
            id_gatilho=id_gatilho,
            destinatario_email=email_destino,
            emails_cc=cc_final,
            status_envio=status_str,
            assunto=assunto,
            corpo_mensagem=corpo_mensagem,
        )
        if data_envio is not None:
            novo_registro.data_envio = data_envio

        db_connection.add(novo_registro)
        db_connection.commit()
        db_connection.refresh(novo_registro)
        return novo_registro
    except Exception:
        db_connection.rollback()
        raise


# ==========================================================================
# CONSULTAS (READ)
# ==========================================================================

def buscar_historico_alerta_por_id(
    db_connection: Session,
    id_historico_alerta: int,
) -> Optional[models.HistoricoAlertaEnviado]:
    return (
        db_connection.query(models.HistoricoAlertaEnviado)
        .filter(models.HistoricoAlertaEnviado.id_historico_alerta == id_historico_alerta)
        .first()
    )


def listar_historico_alertas_por_estudante(
    db_connection: Session,
    id_estudante: int,
) -> List[models.HistoricoAlertaEnviado]:
    return (
        db_connection.query(models.HistoricoAlertaEnviado)
        .filter(models.HistoricoAlertaEnviado.id_estudante == id_estudante)
        .order_by(
            models.HistoricoAlertaEnviado.data_envio.desc(),
            models.HistoricoAlertaEnviado.id_historico_alerta.desc(),
        )
        .all()
    )


def listar_historico_alertas_por_gatilho(
    db_connection: Session,
    id_gatilho: int,
) -> List[models.HistoricoAlertaEnviado]:
    return (
        db_connection.query(models.HistoricoAlertaEnviado)
        .filter(models.HistoricoAlertaEnviado.id_gatilho == id_gatilho)
        .order_by(
            models.HistoricoAlertaEnviado.data_envio.desc(),
            models.HistoricoAlertaEnviado.id_historico_alerta.desc(),
        )
        .all()
    )


# data_envio é gravado em UTC (CURRENT_TIMESTAMP do SQLite). Os filtros por dia
# usam o dia de Maceió (UTC-3, sem horário de verão desde 2019).
FUSO_PPGI = timezone(timedelta(hours=-3))


def _inicio_do_dia_em_utc(dia: date) -> datetime:
    """00:00 do dia em Maceió, convertido para UTC sem fuso (mesmo formato do banco)."""
    local = datetime.combine(dia, time.min, tzinfo=FUSO_PPGI)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def listar_historico_alertas_filtrados(
    db_connection: Session,
    id_estudante: Optional[int] = None,
    id_gatilho: Optional[int] = None,
    id_tipo_prazo: Optional[int] = None,
    status_envio: Optional[Union[StatusEnvioAlerta, str]] = None,
    data_inicio: Optional[Union[date, datetime]] = None,
    data_fim: Optional[Union[date, datetime]] = None,
    busca: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    ordem_desc: bool = True,
) -> Tuple[int, List[Tuple[models.HistoricoAlertaEnviado, str, str, str]]]:
    """
    Listagem paginada com filtros combináveis para auditoria de alertas enviados.

    Cada item vem enriquecido: (registro, nome_discente, matricula, nome_prazo).
    `data_inicio`/`data_fim` aceitam data (dia de Maceió, inclusive nas duas
    pontas) ou data-hora (comparada direto com o valor em UTC do banco).

    Retorna (total_sem_paginacao, itens_da_pagina).
    """
    Historico = models.HistoricoAlertaEnviado
    query = (
        db_connection.query(
            Historico,
            models.Estudante.nome_discente,
            models.Estudante.matricula,
            models.TipoPrazo.nome_prazo,
        )
        .join(models.Estudante, Historico.id_estudante == models.Estudante.id_estudante)
        .join(models.GatilhoAlerta, Historico.id_gatilho == models.GatilhoAlerta.id_gatilho)
        .join(models.TipoPrazo, models.GatilhoAlerta.id_tipo_prazo == models.TipoPrazo.id_tipo_prazo)
    )

    if id_estudante is not None:
        query = query.filter(Historico.id_estudante == id_estudante)

    if id_gatilho is not None:
        query = query.filter(Historico.id_gatilho == id_gatilho)

    if id_tipo_prazo is not None:
        query = query.filter(models.GatilhoAlerta.id_tipo_prazo == id_tipo_prazo)

    if status_envio is not None:
        status_str = (
            status_envio.value
            if isinstance(status_envio, StatusEnvioAlerta)
            else str(status_envio)
        )
        query = query.filter(Historico.status_envio == status_str)

    if data_inicio is not None:
        if not isinstance(data_inicio, datetime):
            data_inicio = _inicio_do_dia_em_utc(data_inicio)
        query = query.filter(Historico.data_envio >= data_inicio)

    if data_fim is not None:
        if isinstance(data_fim, datetime):
            query = query.filter(Historico.data_envio <= data_fim)
        else:
            # Dia inteiro: até antes da meia-noite do dia seguinte.
            limite = _inicio_do_dia_em_utc(data_fim + timedelta(days=1))
            query = query.filter(Historico.data_envio < limite)

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                models.Estudante.nome_discente.ilike(termo),
                models.Estudante.matricula.ilike(termo),
                Historico.destinatario_email.ilike(termo),
                Historico.emails_cc.ilike(termo),
            )
        )

    if ordem_desc:
        query = query.order_by(Historico.data_envio.desc(), Historico.id_historico_alerta.desc())
    else:
        query = query.order_by(Historico.data_envio.asc(), Historico.id_historico_alerta.asc())

    total = query.count()
    itens = query.offset(skip).limit(limit).all()
    return total, itens


def listar_orientadores_do_estudante(
    db_connection: Session,
    id_estudante: int,
) -> List[models.EstudanteOrientador]:
    """Vínculos de orientação do discente (principal primeiro), com o professor carregado."""
    vinculos = (
        db_connection.query(models.EstudanteOrientador)
        .options(selectinload(models.EstudanteOrientador.professor))
        .filter(models.EstudanteOrientador.id_estudante == id_estudante)
        .all()
    )
    return sorted(
        (v for v in vinculos if v.professor is not None),
        key=lambda v: (
            0 if v.tipo_orientacao == TipoOrientacao.ORIENTADOR.value else 1,
            v.professor.nome_professor.lower(),
        ),
    )


def buscar_estudante(db_connection: Session, id_estudante: int) -> Optional[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .filter(models.Estudante.id_estudante == id_estudante)
        .first()
    )


def buscar_gatilho(db_connection: Session, id_gatilho: int) -> Optional[models.GatilhoAlerta]:
    return (
        db_connection.query(models.GatilhoAlerta)
        .filter(models.GatilhoAlerta.id_gatilho == id_gatilho)
        .first()
    )


# ==========================================================================
# ATUALIZAÇÃO (UPDATE)
# ==========================================================================

def atualizar_historico_alerta(
    db_connection: Session,
    registro: models.HistoricoAlertaEnviado,
    updates: Dict[str, Any],
) -> models.HistoricoAlertaEnviado:
    """
    Atualiza campos mutáveis do registro de histórico (ex.: reprocessamento de
    um envio que estava com status 'FALHA' para 'ENVIADO').
    """
    campos_permitidos = {
        "destinatario_email", "emails_cc", "status_envio", "data_envio",
        "assunto", "corpo_mensagem",
    }

    try:
        for key, value in updates.items():
            if key not in campos_permitidos:
                continue
            if key == "status_envio" and isinstance(value, StatusEnvioAlerta):
                value = value.value
            elif key == "emails_cc" and value is not None:
                destino = updates.get("destinatario_email", registro.destinatario_email)
                value = _normalizar_emails_cc(value, excluir_email=destino)
            setattr(registro, key, value)

        db_connection.commit()
        db_connection.refresh(registro)
        return registro
    except Exception:
        db_connection.rollback()
        raise


# ==========================================================================
# REMOÇÃO (DELETE)
# ==========================================================================

def deletar_historico_alerta(
    db_connection: Session,
    id_historico_alerta: int,
) -> bool:
    """Remove um registro de histórico pelo ID. Retorna False se não existir."""
    registro = buscar_historico_alerta_por_id(db_connection, id_historico_alerta)
    if registro is None:
        return False

    try:
        db_connection.delete(registro)
        db_connection.commit()
        return True
    except Exception:
        db_connection.rollback()
        raise

# ==========================================================================
# VARREDURA (ALERT ENGINE) — CONSULTAS EM LOTE
# ==========================================================================

def listar_gatilhos_ativos_com_tipo(
    db_connection: Session,
) -> List[Tuple[models.GatilhoAlerta, models.TipoPrazo]]:
    """
    Retorna pares (gatilho, tipo_prazo) apenas dos gatilhos ativos,
    em uma única consulta (join), para o motor saber qual data-limite
    consultar em cada gatilho (via tipo_prazo.codigo_prazo).
    """
    return (
        db_connection.query(
            models.GatilhoAlerta, models.TipoPrazo
        )
        .join(
            models.TipoPrazo,
            models.GatilhoAlerta.id_tipo_prazo == models.TipoPrazo.id_tipo_prazo
        )
        .filter(
            models.GatilhoAlerta.ativo.is_(True)
        )
        .all()
    )

def listar_estudantes_para_varredura(
    db_connection: Session,
    status_permitidos: List[str],
) -> List[models.Estudante]:
    """
    Estudantes elegíveis à varredura (status permitido e e-mail preenchido),
    com orientações e professores já carregados para evitar N+1.
    """
    return (
        db_connection.query(models.Estudante)
        .options(
            selectinload(models.Estudante.orientacoes).selectinload(
                models.EstudanteOrientador.professor
            )
        )
        .filter(
            models.Estudante.status_atual.in_(status_permitidos),
            models.Estudante.email.isnot(None),
            models.Estudante.email != "",
        )
        .all()
    )


def obter_pares_alertas_enviados(db_connection: Session) -> set[tuple[int, int]]:
    """
    Conjunto {(id_estudante, id_gatilho)} com status ENVIADO, em uma única
    consulta. Usado pelo motor para não listar alertas já disparados.
    """
    linhas = (
        db_connection.query(
            models.HistoricoAlertaEnviado.id_estudante,
            models.HistoricoAlertaEnviado.id_gatilho,
        )
        .filter(
            models.HistoricoAlertaEnviado.status_envio == StatusEnvioAlerta.ENVIADO.value
        )
        .distinct()
        .all()
    )
    return {(id_estudante, id_gatilho) for id_estudante, id_gatilho in linhas}


def mapear_qualificacoes_atuais(
    db_connection: Session,
    ids_estudantes: List[int],
) -> Dict[int, models.Qualificacao]:
    """
    {id_estudante: qualificação mais recente}. Ordena da tentativa mais antiga
    para a mais nova, então a última atribuição no dicionário é a atual.
    """
    if not ids_estudantes:
        return {}

    linhas = (
        db_connection.query(models.Dissertacao.id_estudante, models.Qualificacao)
        .join(
            models.Qualificacao,
            models.Qualificacao.id_dissertacao == models.Dissertacao.id_dissertacao,
        )
        .filter(models.Dissertacao.id_estudante.in_(ids_estudantes))
        .order_by(models.Qualificacao.tentativa.asc(), models.Qualificacao.id_qualificacao.asc())
        .all()
    )
    return {id_estudante: qualificacao for id_estudante, qualificacao in linhas}


def mapear_defesas_atuais(
    db_connection: Session,
    ids_estudantes: List[int],
) -> Dict[int, models.Defesa]:
    """{id_estudante: defesa mais recente} (mesma lógica de mapear_qualificacoes_atuais)."""
    if not ids_estudantes:
        return {}

    linhas = (
        db_connection.query(models.Dissertacao.id_estudante, models.Defesa)
        .join(
            models.Defesa,
            models.Defesa.id_dissertacao == models.Dissertacao.id_dissertacao,
        )
        .filter(models.Dissertacao.id_estudante.in_(ids_estudantes))
        .order_by(models.Defesa.id_defesa.asc())
        .all()
    )
    return {id_estudante: defesa for id_estudante, defesa in linhas}


def mapear_titulos_dissertacao(
    db_connection: Session,
    ids_estudantes: List[int],
) -> Dict[int, Optional[str]]:
    """{id_estudante: título da dissertação} (None se o título não foi preenchido)."""
    if not ids_estudantes:
        return {}

    linhas = (
        db_connection.query(models.Dissertacao.id_estudante, models.Dissertacao.titulo)
        .filter(models.Dissertacao.id_estudante.in_(ids_estudantes))
        .all()
    )
    return {id_estudante: titulo for id_estudante, titulo in linhas}
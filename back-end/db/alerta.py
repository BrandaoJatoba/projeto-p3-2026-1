from datetime import datetime
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


def listar_historico_alertas_filtrados(
    db_connection: Session,
    id_estudante: Optional[int] = None,
    id_gatilho: Optional[int] = None,
    id_tipo_prazo: Optional[int] = None,
    status_envio: Optional[Union[StatusEnvioAlerta, str]] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    busca: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    ordem_desc: bool = True,
) -> Tuple[int, List[models.HistoricoAlertaEnviado]]:
    """
    Listagem paginada com filtros combináveis para auditoria de alertas enviados.
    Retorna (total_sem_paginacao, itens_da_pagina).
    """
    query = db_connection.query(models.HistoricoAlertaEnviado)

    if id_estudante is not None:
        query = query.filter(models.HistoricoAlertaEnviado.id_estudante == id_estudante)

    if id_gatilho is not None:
        query = query.filter(models.HistoricoAlertaEnviado.id_gatilho == id_gatilho)

    if id_tipo_prazo is not None:
        query = query.join(
            models.GatilhoAlerta,
            models.HistoricoAlertaEnviado.id_gatilho == models.GatilhoAlerta.id_gatilho,
        ).filter(models.GatilhoAlerta.id_tipo_prazo == id_tipo_prazo)

    if status_envio is not None:
        status_str = (
            status_envio.value
            if isinstance(status_envio, StatusEnvioAlerta)
            else str(status_envio)
        )
        query = query.filter(models.HistoricoAlertaEnviado.status_envio == status_str)

    if data_inicio is not None:
        query = query.filter(models.HistoricoAlertaEnviado.data_envio >= data_inicio)

    if data_fim is not None:
        query = query.filter(models.HistoricoAlertaEnviado.data_envio <= data_fim)

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.join(
            models.Estudante,
            models.HistoricoAlertaEnviado.id_estudante == models.Estudante.id_estudante,
        ).filter(
            or_(
                models.Estudante.nome_discente.ilike(termo),
                models.Estudante.matricula.ilike(termo),
                models.HistoricoAlertaEnviado.destinatario_email.ilike(termo),
                models.HistoricoAlertaEnviado.emails_cc.ilike(termo),
            )
        )

    if ordem_desc:
        query = query.order_by(
            models.HistoricoAlertaEnviado.data_envio.desc(),
            models.HistoricoAlertaEnviado.id_historico_alerta.desc(),
        )
    else:
        query = query.order_by(
            models.HistoricoAlertaEnviado.data_envio.asc(),
            models.HistoricoAlertaEnviado.id_historico_alerta.asc(),
        )

    total = query.count()
    itens = query.offset(skip).limit(limit).all()
    return total, itens


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
    campos_permitidos = {"destinatario_email", "emails_cc", "status_envio", "data_envio"}

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
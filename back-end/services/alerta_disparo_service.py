"""
Disparo de alertas por e-mail: individual, em lote e reenvio.

Regras:
- Todo envio tentado gera (ou atualiza) um registro em historico_alertas_enviados,
  com status ENVIADO ou FALHA. O assunto e o corpo enviados também são gravados,
  para permitir o reenvio da mesma mensagem.
- CC: orientador principal + coorientadores com e-mail válido, menos os ids em
  `ignorar_cc_ids`, mais os `cc_adicionais`. A lista final fica em `emails_cc`
  (fica registrada mesmo que o orientador mude depois).
- Anti-spam: um par (estudante, gatilho) que já tem registro ENVIADO não é enviado de novo.
- Lote: roda em background com sessão própria; a falha de um item registra FALHA
  só para ele e não interrompe os demais.

Este módulo não conhece HTTP: sinaliza erros com as exceções abaixo e a rota
escolhe o status code.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from email_validator import EmailNotValidError, validate_email
from sqlalchemy.orm import Session

from db import alerta as crud_alerta
from db import models
from db.database import SessionLocal
from db.enumStatus import StatusEnvioAlerta
from services import minuta_service
from services.email_service import ErroEnvioEmail, enviar_email

logger = logging.getLogger(__name__)


class RecursoNaoEncontrado(Exception):
    """Estudante, gatilho ou registro de histórico inexistente (rota → 404)."""


class ConflitoDisparo(Exception):
    """O disparo conflita com o estado atual, ex.: alerta já enviado (rota → 409)."""


class DisparoInvalido(Exception):
    """Dados insuficientes para disparar, ex.: discente sem e-mail (rota → 422)."""


# ==========================================================================
# AUXILIARES
# ==========================================================================

def email_valido(email: Optional[str]) -> bool:
    """Valida só o formato do e-mail (sem consultar DNS)."""
    if not email or not email.strip():
        return False
    try:
        validate_email(email.strip(), check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def _agora_utc() -> datetime:
    """Data-hora em UTC sem fuso, no mesmo padrão do CURRENT_TIMESTAMP do SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def resolver_cc(
    db_connection: Session,
    id_estudante: int,
    destinatario: str,
    cc_adicionais: Optional[List[str]] = None,
    ignorar_cc_ids: Optional[List[int]] = None,
) -> List[str]:
    """
    Monta a lista final de CC: orientadores com e-mail válido (principal primeiro),
    menos os ignorados, mais os adicionais. Remove duplicados e o próprio destinatário.
    """
    ignorados = set(ignorar_cc_ids or [])
    candidatos = [
        v.professor.email
        for v in crud_alerta.listar_orientadores_do_estudante(db_connection, id_estudante)
        if v.id_professor not in ignorados
    ]
    candidatos += list(cc_adicionais or [])

    destino = destinatario.strip().lower()
    vistos = set()
    finais: List[str] = []
    for email in candidatos:
        if not email_valido(email):
            continue
        chave = email.strip().lower()
        if chave == destino or chave in vistos:
            continue
        vistos.add(chave)
        finais.append(email.strip())
    return finais


def _tentar_envio(destinatario: str, assunto: str, corpo: str, cc: List[str]) -> StatusEnvioAlerta:
    """Tenta enviar e devolve ENVIADO ou FALHA (nunca lança erro de envio)."""
    if not email_valido(destinatario):
        logger.warning("Alerta não enviado: e-mail do destinatário inválido (%s).", destinatario)
        return StatusEnvioAlerta.FALHA
    try:
        enviar_email(
            destinatario,
            assunto,
            corpo,
            cc=cc or None,
            corpo_html=minuta_service.texto_para_html(corpo),
        )
        return StatusEnvioAlerta.ENVIADO
    except ErroEnvioEmail as erro:
        logger.warning("Falha ao enviar alerta para %s: %s", destinatario, erro)
        return StatusEnvioAlerta.FALHA


def _enviar_e_registrar(
    db_connection: Session,
    id_estudante: int,
    id_gatilho: int,
    destinatario: str,
    assunto: str,
    corpo: str,
    cc: List[str],
) -> models.HistoricoAlertaEnviado:
    """Envia e grava o histórico com o resultado (ENVIADO ou FALHA)."""
    status_envio = _tentar_envio(destinatario, assunto, corpo, cc)
    return crud_alerta.criar_historico_alerta(
        db_connection,
        id_estudante=id_estudante,
        id_gatilho=id_gatilho,
        destinatario_email=destinatario,
        emails_cc=cc,  # lista (mesmo vazia) → não preenche o CC automaticamente de novo
        status_envio=status_envio,
        assunto=assunto,
        corpo_mensagem=corpo,
    )


def _carregar_par(
    db_connection: Session, id_estudante: int, id_gatilho: int
) -> Tuple[models.Estudante, models.GatilhoAlerta]:
    estudante = crud_alerta.buscar_estudante(db_connection, id_estudante)
    if estudante is None:
        raise RecursoNaoEncontrado(f"Estudante {id_estudante} não encontrado.")
    gatilho = crud_alerta.buscar_gatilho(db_connection, id_gatilho)
    if gatilho is None:
        raise RecursoNaoEncontrado(f"Gatilho de alerta {id_gatilho} não encontrado.")
    return estudante, gatilho


# ==========================================================================
# DISPARO INDIVIDUAL
# ==========================================================================

def disparar_individual(
    db_connection: Session,
    id_estudante: int,
    id_gatilho: int,
    assunto: str,
    corpo_mensagem: str,
    email_destino: Optional[str] = None,
    cc_adicionais: Optional[List[str]] = None,
    ignorar_cc_ids: Optional[List[int]] = None,
) -> models.HistoricoAlertaEnviado:
    """
    Envia um alerta já revisado pela Secretaria e grava o histórico.

    Destinatário: `email_destino` (se a Secretaria sobrescreveu) ou o e-mail do discente.
    Retorna o registro criado; o resultado do envio está em `status_envio`.
    """
    estudante, _ = _carregar_par(db_connection, id_estudante, id_gatilho)

    if crud_alerta.ja_enviou_alerta(db_connection, id_estudante, id_gatilho):
        raise ConflitoDisparo("Este alerta já foi enviado para o discente.")

    destinatario = (email_destino or estudante.email or "").strip()
    if not destinatario:
        raise DisparoInvalido("Discente sem e-mail cadastrado e nenhum email_destino informado.")

    cc = resolver_cc(db_connection, id_estudante, destinatario, cc_adicionais, ignorar_cc_ids)
    return _enviar_e_registrar(
        db_connection, id_estudante, id_gatilho, destinatario, assunto, corpo_mensagem, cc
    )


# ==========================================================================
# DISPARO EM LOTE
# ==========================================================================

def validar_itens_lote(
    db_connection: Session, itens: List[dict]
) -> Tuple[List[dict], List[dict]]:
    """
    Separa os itens do lote em (aceitos, recusados) antes de enfileirar.

    Recusa: par repetido na requisição, estudante/gatilho inexistente,
    alerta já enviado e discente sem e-mail. Itens recusados não são enviados
    nem registrados (nenhum e-mail sai para eles).
    """
    aceitos: List[dict] = []
    recusados: List[dict] = []
    vistos = set()

    for item in itens:
        par = (item["id_estudante"], item["id_gatilho"])

        def recusar(motivo: str) -> None:
            recusados.append({"id_estudante": par[0], "id_gatilho": par[1], "motivo": motivo})

        if par in vistos:
            recusar("Item repetido na requisição.")
            continue
        vistos.add(par)

        try:
            estudante, _ = _carregar_par(db_connection, *par)
        except RecursoNaoEncontrado as erro:
            recusar(str(erro))
            continue

        if crud_alerta.ja_enviou_alerta(db_connection, *par):
            recusar("Este alerta já foi enviado para o discente.")
            continue

        if not (estudante.email or "").strip():
            recusar("Discente sem e-mail cadastrado.")
            continue

        aceitos.append(item)

    return aceitos, recusados


def _processar_item_lote(
    db_connection: Session,
    item: dict,
    minutas: Dict[Tuple[int, int], dict],
) -> None:
    id_estudante, id_gatilho = item["id_estudante"], item["id_gatilho"]

    # Confere de novo: entre a requisição e a execução outro disparo pode ter saído.
    if crud_alerta.ja_enviou_alerta(db_connection, id_estudante, id_gatilho):
        logger.info("Lote: alerta (%s, %s) já enviado; ignorado.", id_estudante, id_gatilho)
        return

    estudante = crud_alerta.buscar_estudante(db_connection, id_estudante)
    destinatario = (estudante.email or "").strip()
    cc = resolver_cc(
        db_connection, id_estudante, destinatario,
        item.get("cc_adicionais"), item.get("ignorar_cc_ids"),
    )

    minuta = minutas.get((id_estudante, id_gatilho), {})
    assunto = item.get("assunto") or minuta.get("assunto")
    corpo = item.get("corpo_mensagem") or minuta.get("corpo")

    if not assunto or not corpo:
        # Sem texto não há o que enviar (ex.: alerta saiu da janela do gatilho).
        logger.warning("Lote: sem assunto/corpo para (%s, %s); registrado como FALHA.",
                       id_estudante, id_gatilho)
        crud_alerta.criar_historico_alerta(
            db_connection,
            id_estudante=id_estudante,
            id_gatilho=id_gatilho,
            destinatario_email=destinatario,
            emails_cc=cc,
            status_envio=StatusEnvioAlerta.FALHA,
            assunto=assunto,
            corpo_mensagem=corpo,
        )
        return

    _enviar_e_registrar(db_connection, id_estudante, id_gatilho, destinatario, assunto, corpo, cc)


def processar_lote(itens: List[dict], template_global_override: Optional[str] = None) -> None:
    """
    Executa o lote em background (chamada pelo BackgroundTasks).

    Abre a própria sessão: a sessão da requisição (get_db) já foi fechada quando
    a background task roda. Itens sem assunto/corpo usam a minuta gerada a partir
    do template do gatilho (ou de `template_global_override`).
    """
    db_connection = SessionLocal()
    try:
        sem_texto = [
            (i["id_estudante"], i["id_gatilho"])
            for i in itens
            if not i.get("assunto") or not i.get("corpo_mensagem")
        ]
        minutas: Dict[Tuple[int, int], dict] = {}
        if sem_texto:
            try:
                resultado = minuta_service.gerar_minutas_selecionadas(
                    db_connection, sem_texto, template_global_override
                )
                minutas = {(m["id_estudante"], m["id_gatilho"]): m for m in resultado["minutas"]}
            except Exception:
                logger.exception("Lote: erro ao gerar minutas; itens sem texto viram FALHA.")

        for item in itens:
            try:
                _processar_item_lote(db_connection, item, minutas)
            except Exception:
                # Erro inesperado num item não pode parar o resto do lote.
                db_connection.rollback()
                logger.exception("Lote: erro inesperado no item (%s, %s).",
                                 item.get("id_estudante"), item.get("id_gatilho"))
    finally:
        db_connection.close()


# ==========================================================================
# REENVIO
# ==========================================================================

def reenviar(db_connection: Session, id_historico_alerta: int) -> models.HistoricoAlertaEnviado:
    """
    Reprocessa um registro com status FALHA, atualizando o próprio registro.

    Usa o mesmo destinatário e a mesma lista de CC gravados. A mensagem é a
    gravada no registro; registros antigos (sem assunto/corpo salvos) geram a
    minuta de novo, se o alerta ainda estiver pendente.
    """
    registro = crud_alerta.buscar_historico_alerta_por_id(db_connection, id_historico_alerta)
    if registro is None:
        raise RecursoNaoEncontrado(f"Registro de histórico {id_historico_alerta} não encontrado.")

    if registro.status_envio != StatusEnvioAlerta.FALHA.value:
        raise ConflitoDisparo("Só é possível reenviar alertas com status FALHA.")

    if crud_alerta.ja_enviou_alerta(db_connection, registro.id_estudante, registro.id_gatilho):
        raise ConflitoDisparo("Este alerta já foi enviado com sucesso em outro registro.")

    assunto, corpo = registro.assunto, registro.corpo_mensagem
    if not assunto or not corpo:
        resultado = minuta_service.gerar_minutas_selecionadas(
            db_connection, [(registro.id_estudante, registro.id_gatilho)]
        )
        if not resultado["minutas"]:
            raise ConflitoDisparo(
                "Registro sem mensagem salva e o alerta não está mais pendente. "
                "Dispare novamente pela Central de Alertas."
            )
        minuta = resultado["minutas"][0]
        assunto = assunto or minuta["assunto"]
        corpo = corpo or minuta["corpo"]

    cc = [e.strip() for e in (registro.emails_cc or "").split(",") if e.strip()]
    status_envio = _tentar_envio(registro.destinatario_email, assunto, corpo, cc)

    return crud_alerta.atualizar_historico_alerta(
        db_connection,
        registro,
        {
            "status_envio": status_envio,
            "data_envio": _agora_utc(),
            "assunto": assunto,
            "corpo_mensagem": corpo,
        },
    )

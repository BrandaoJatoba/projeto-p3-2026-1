"""
Envio de e-mails via SMTP.

As configurações vêm de variáveis de ambiente (nunca do código). Ver .env.example.

EMAIL_MODO controla o comportamento:
- "console" (padrão): não envia nada; imprime o e-mail no terminal do uvicorn.
  Use em desenvolvimento para não mandar e-mail para aluno de verdade.
- "smtp": envia de verdade pelo servidor configurado.

Contrato: enviar_email() não retorna nada quando dá certo e lança ErroEnvioEmail
quando falha. Quem chama (o disparo em lote) decide se registra FALHA e segue
para o próximo aluno.
"""

from logging import config
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from typing import List, Optional
import time
import html

MODOS_VALIDOS = ("console", "smtp")

MAX_TENTATIVAS = 3
ESPERA_INICIAL_SEGUNDOS = 1


class ErroEnvioEmail(Exception):
    """Falha ao enviar e-mail (configuração ausente, conexão, login ou recusa do servidor)."""


def obter_modo() -> str:
    """Modo atual de envio: "console" ou "smtp"."""
    modo = os.getenv("EMAIL_MODO", "console").strip().lower()
    if modo not in MODOS_VALIDOS:
        raise ErroEnvioEmail(f"EMAIL_MODO inválido: '{modo}'. Use 'console' ou 'smtp'.")
    return modo


def _carregar_config_smtp() -> dict:
    """Lê as variáveis SMTP_*; lança ErroEnvioEmail se faltar alguma obrigatória."""
    config = {
        "host": os.getenv("SMTP_HOST"),
        "porta": os.getenv("SMTP_PORTA", "587"),
        "usuario": os.getenv("SMTP_USUARIO"),
        "senha": os.getenv("SMTP_SENHA"),
        "remetente": os.getenv("SMTP_REMETENTE") or os.getenv("SMTP_USUARIO"),
        "nome_remetente": os.getenv("SMTP_NOME_REMETENTE", "Secretaria PPGI/UFAL"),
    }

    faltando = [nome for nome in ("host", "usuario", "senha") if not config[nome]]
    if faltando:
        variaveis = ", ".join(f"SMTP_{n.upper()}" for n in faltando)
        raise ErroEnvioEmail(f"Configuração SMTP incompleta. Faltam: {variaveis}")

    try:
        config["porta"] = int(config["porta"])
    except ValueError:
        raise ErroEnvioEmail("SMTP_PORTA deve ser um número (ex.: 587).")

    return config


def montar_mensagem(
    remetente: str,
    destinatario: str,
    assunto: str,
    corpo: str,
    cc: Optional[List[str]] = None,
    corpo_html: Optional[str] = None,
) -> EmailMessage:
    """
    Cria o objeto de e-mail em UTF-8. Se corpo_html vier, o e-mail leva as duas
    versões: o programa de e-mail mostra o HTML e usa o texto puro como reserva.
    """
    mensagem = EmailMessage()
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    if cc:
        mensagem["Cc"] = ", ".join(cc)
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)
    if corpo_html:
        mensagem.add_alternative(corpo_html, subtype="html")
    return mensagem


def _imprimir_no_console(mensagem: EmailMessage) -> None:
    linha = "=" * 70
    print(f"\n{linha}\n[EMAIL_MODO=console] E-mail NÃO enviado (modo de teste)")
    print(f"Para:    {mensagem['To']}")
    if mensagem["Cc"]:
        print(f"Cc:      {mensagem['Cc']}")
    print(f"Assunto: {mensagem['Subject']}\n")
    parte_texto = mensagem.get_body(preferencelist=("plain",))
    print(parte_texto.get_content())
    if mensagem.get_body(preferencelist=("html",)) is not None:
        print("(o e-mail também leva uma versão HTML)")
    print(f"{linha}\n")


def _aplicar_redirecionamento(destinatario, cc, assunto, corpo, corpo_html):
    """
    Em ambiente de teste, desvia TODO e-mail para um endereço só.

    Ativado pela variável EMAIL_REDIRECIONAR_PARA. O CC é removido e um aviso
    com os destinatários originais vai no topo do e-mail (texto e HTML).
    """
    redirecionar = os.getenv("EMAIL_REDIRECIONAR_PARA", "").strip()
    if not redirecionar:
        return destinatario, cc, assunto, corpo, corpo_html

    lista_cc = ", ".join(cc) if cc else "(nenhum)"
    aviso = f"[MODO TESTE] Este e-mail iria para: {destinatario} | CC: {lista_cc}"

    novo_assunto = f"[TESTE] {assunto}"
    novo_corpo = f"{aviso}\n\n{corpo}"
    novo_html = None
    if corpo_html:
        novo_html = f'<p style="color:#b00"><b>{html.escape(aviso)}</b></p>{corpo_html}'

    return redirecionar, [], novo_assunto, novo_corpo, novo_html


def enviar_email(
    destinatario: str,
    assunto: str,
    corpo: str,
    cc: Optional[List[str]] = None,
    corpo_html: Optional[str] = None,
) -> None:
    """
    Envia um e-mail. Não retorna nada se der certo; lança ErroEnvioEmail se falhar.

    Porta 465 usa SSL direto; qualquer outra porta (ex.: 587) usa STARTTLS.
    """
    if not destinatario:
        raise ErroEnvioEmail("Destinatário vazio.")

    modo = obter_modo()

    if modo == "console":
        remetente = os.getenv("SMTP_REMETENTE") or "nao-configurado@exemplo.com"
        _imprimir_no_console(montar_mensagem(remetente, destinatario, assunto, corpo, cc, corpo_html))
        return

    config = _carregar_config_smtp()
    destinatario, cc, assunto, corpo, corpo_html = _aplicar_redirecionamento(
        destinatario, cc, assunto, corpo, corpo_html
    )
    remetente = formataddr((config["nome_remetente"], config["remetente"]))
    mensagem = montar_mensagem(remetente, destinatario, assunto, corpo, cc, corpo_html)

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            _enviar_via_smtp(config, mensagem)
            return

        except smtplib.SMTPAuthenticationError as erro:
            raise ErroEnvioEmail("Falha de login no servidor SMTP (usuário ou senha de app).") from erro
        except smtplib.SMTPRecipientsRefused as erro:
            raise ErroEnvioEmail(f"Servidor recusou o destinatário: {destinatario}") from erro
        except (smtplib.SMTPException, OSError) as erro:
            # OSError cobre timeout, host inexistente e conexão recusada.
            if tentativa == MAX_TENTATIVAS:
                raise ErroEnvioEmail(
                    f"Erro ao enviar e-mail após {MAX_TENTATIVAS} tentativas: {erro.__class__.__name__}"
                ) from erro
            time.sleep(ESPERA_INICIAL_SEGUNDOS * 2 ** (tentativa - 1))  # 1s, 2s


def _enviar_via_smtp(config: dict, mensagem: EmailMessage) -> None:
    """Uma tentativa de envio. Porta 465 usa SSL direto; as outras usam STARTTLS."""
    contexto_ssl = ssl.create_default_context()

    if config["porta"] == 465:
        servidor = smtplib.SMTP_SSL(config["host"], config["porta"], context=contexto_ssl, timeout=20)
    else:
        servidor = smtplib.SMTP(config["host"], config["porta"], timeout=20)

    with servidor:
        if config["porta"] != 465:
            servidor.starttls(context=contexto_ssl)
        servidor.login(config["usuario"], config["senha"])
        servidor.send_message(mensagem)
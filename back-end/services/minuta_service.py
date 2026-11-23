"""
Gerador de minutas de e-mail dos alertas.

Recebe um alerta pendente (dict produzido por alerta_scanner_service) e devolve
a minuta pronta para a Secretaria revisar: destinatário, cópias, assunto e corpo.
Não envia nada e não grava nada.

Variáveis aceitas no template (chave simples):
    {nome_discente}       nome do discente
    {matricula}           matrícula do discente
    {nome_prazo}          nome do tipo de prazo (ex.: "Exame de Qualificação")
    {data_limite}         data limite no formato DD/MM/AAAA
    {dias_restantes}      número de dias até o prazo (negativo se já venceu)
    {situacao_prazo}      frase pronta: "vence em 5 dias", "vence hoje", "venceu há 3 dias"
    {orientador}          orientador principal ou "Não informado"
    {coorientadores}      coorientadores ("Ana e João") ou "Não possui"
    {lista_orientadores}  todos com o papel: "Ana (Orientador), João (Coorientador)"
                          ou "Não informado"
    {titulo_dissertacao}  título da dissertação ou "Não informado"
"""

import re
import html
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from db.enumStatus import TipoOrientacao
from services import alerta_scanner_service

PADRAO_VARIAVEL = re.compile(r"\{([a-z_]+)\}")

VARIAVEIS_DISPONIVEIS = [
    "nome_discente",
    "matricula",
    "nome_prazo",
    "data_limite",
    "dias_restantes",
    "orientador",
    "coorientadores",
    "lista_orientadores",
    "titulo_dissertacao",
    "situacao_prazo",
]

SEM_INFORMACAO = "Não informado"
SEM_COORIENTADOR = "Não possui"

# O corpo do e-mail é sempre: SAUDACAO + texto do gatilho + ENCERRAMENTO.
# A Secretaria edita só o miolo (mensagem_template); saudação e assinatura são fixas.
SAUDACAO = "Prezado(a) {nome_discente},\n\n"

ENCERRAMENTO = (
    "\n\nEm caso de dúvidas, entre em contato com a Secretaria do PPGI.\n\n"
    "Atenciosamente,\n"
    "Secretaria do PPGI/UFAL"
)

# Usado no miolo quando o gatilho não tem mensagem_template.
TEMPLATE_PADRAO = "Informamos que o prazo de {nome_prazo} tem data limite em {data_limite}. Caso ainda não tenha providenciado, procure seu(sua) orientador(a) e a Secretaria para dar andamento."


def _juntar_nomes(nomes: List[str]) -> str:
    """["Ana"] -> "Ana"; ["Ana", "João"] -> "Ana e João"; ["A", "B", "C"] -> "A, B e C"."""
    if not nomes:
        return ""
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def montar_contexto(alerta: dict) -> dict[str, str]:
    """
    Traduz o dict do scanner no texto que entra no lugar de cada variável.
    Dado ausente no banco nunca quebra a minuta: entra um texto padrão.
    """
    orientadores = alerta.get("orientadores") or []
    principais = [
        o["nome_professor"]
        for o in orientadores
        if o["tipo_orientacao"] == TipoOrientacao.ORIENTADOR.value
    ]
    coorientadores = [
        o["nome_professor"]
        for o in orientadores
        if o["tipo_orientacao"] == TipoOrientacao.COORIENTADOR.value
    ]
    lista_orientadores = [
        f"{o['nome_professor']} ({o['tipo_orientacao'].capitalize()})"
        for o in orientadores
    ]

    return {
        "nome_discente": alerta["nome_discente"],
        "matricula": alerta["matricula"],
        "nome_prazo": alerta["nome_prazo"],
        "data_limite": alerta["data_limite"].strftime("%d/%m/%Y"),
        "dias_restantes": str(alerta["dias_restantes"]),
        "situacao_prazo": _descrever_situacao(alerta["dias_restantes"]),
        "orientador": _juntar_nomes(principais) or SEM_INFORMACAO,
        "coorientadores": _juntar_nomes(coorientadores) or SEM_COORIENTADOR,
        "lista_orientadores": ", ".join(lista_orientadores) or SEM_INFORMACAO,
        "titulo_dissertacao": alerta.get("titulo_dissertacao") or SEM_INFORMACAO,
    }

def encontrar_variaveis_desconhecidas(template: str) -> List[str]:
    """Variáveis usadas no template que não estão na lista branca (sem repetição)."""
    usadas = PADRAO_VARIAVEL.findall(template)
    return sorted({v for v in usadas if v not in VARIAVEIS_DISPONIVEIS})


def renderizar_template(template: str, contexto: dict[str, str]) -> str:
    """Troca as variáveis conhecidas pelos valores; mantém as desconhecidas intactas."""

    def _substituir(match: re.Match) -> str:
        variavel = match.group(1)
        if variavel in contexto:
            return contexto[variavel]
        return match.group(0)  # texto original, com as chaves

    return PADRAO_VARIAVEL.sub(_substituir, template)


def _descrever_situacao(dias_restantes: int) -> str:
    """30 -> "vence em 30 dias"; 1 -> "vence amanhã"; 0 -> "vence hoje"; -3 -> "venceu há 3 dias"."""
    if dias_restantes > 1:
        return f"vence em {dias_restantes} dias"
    if dias_restantes == 1:
        return "vence amanhã"
    if dias_restantes == 0:
        return "vence hoje"
    if dias_restantes == -1:
        return "venceu ontem"
    return f"venceu há {abs(dias_restantes)} dias"


def montar_assunto(alerta: dict) -> str:
    """Ex.: "PPGI/UFAL – Prazo de Exame de Qualificação vence em 5 dias"."""
    situacao = _descrever_situacao(alerta["dias_restantes"])
    return f"PPGI/UFAL – Prazo de {alerta['nome_prazo']} {situacao}"

def texto_para_html(texto: str) -> str:
    """
    Converte o corpo em texto puro para HTML básico e seguro.

    - html.escape troca <, >, & e aspas por códigos (&lt; etc.), então qualquer
      tag digitada no template aparece como texto e não é executada.
    - Cada bloco separado por linha em branco vira um <p>; quebras simples viram <br>.
    """
    paragrafos = [p for p in texto.strip().split("\n\n") if p.strip()]
    return "\n".join(
        "<p>" + html.escape(p.strip()).replace("\n", "<br>") + "</p>"
        for p in paragrafos
    )


def gerar_minuta(alerta: dict, template: Optional[str] = None) -> dict:
    """
    Monta a minuta de um alerta pendente.

    O miolo vem do parâmetro ou, se não for passado, de alerta["mensagem_template"].
    Se os dois estiverem vazios, usa TEMPLATE_PADRAO. O miolo é sempre embrulhado
    com SAUDACAO e ENCERRAMENTO.

    Retorna um dict com: id_estudante, id_gatilho, nome_discente, destinatario,
    cc (lista de e-mails), assunto, corpo e avisos (lista de textos para a Secretaria).
    """
    texto = template if template is not None else alerta.get("mensagem_template")
    if not texto or not texto.strip():
        texto = TEMPLATE_PADRAO

    avisos: List[str] = []

    desconhecidas = encontrar_variaveis_desconhecidas(texto)
    if desconhecidas:
        lista = ", ".join("{" + v + "}" for v in desconhecidas)
        avisos.append(f"Variáveis desconhecidas no texto (não serão preenchidas): {lista}")

    if not alerta.get("email"):
        avisos.append("Discente sem e-mail cadastrado.")

    orientadores = alerta.get("orientadores") or []
    cc = [o["email"] for o in orientadores if o.get("email")]
    sem_email = [o["nome_professor"] for o in orientadores if not o.get("email")]
    if sem_email:
        avisos.append(f"Sem e-mail cadastrado (não vai em cópia): {_juntar_nomes(sem_email)}")

    corpo = renderizar_template(
        SAUDACAO + texto.strip() + ENCERRAMENTO,
        montar_contexto(alerta),
    )

    return {
        "id_estudante": alerta["id_estudante"],
        "id_gatilho": alerta["id_gatilho"],
        "nome_discente": alerta["nome_discente"],
        "destinatario": alerta.get("email"),
        "cc": cc,
        "destinatarios_cc": [o for o in orientadores if o.get("email")],
        "assunto": montar_assunto(alerta),
        "corpo": corpo,
        "corpo_html": texto_para_html(corpo),
        "avisos": avisos,
    }


def gerar_minutas_selecionadas(
    db_connection: Session,
    pares: List[Tuple[int, int]],
    template: Optional[str] = None,
    hoje: Optional[date] = None,
) -> dict:
    """
    Gera minutas para os pares (id_estudante, id_gatilho) selecionados.

    Só gera minuta para pares realmente pendentes (respeita o anti-spam do motor).
    Pares repetidos são processados uma vez; os não pendentes voltam em "ignorados".
    Usado pelo preview e, na sequência, pelo disparo de alertas.

    Retorna {"minutas": [...], "ignorados": [...]}.
    """
    pendentes = alerta_scanner_service.listar_alertas_pendentes(db_connection, hoje=hoje)
    por_par = {(a["id_estudante"], a["id_gatilho"]): a for a in pendentes}

    minutas: List[dict] = []
    ignorados: List[dict] = []
    vistos = set()

    for par in pares:
        if par in vistos:
            continue  # item repetido na requisição
        vistos.add(par)

        alerta = por_par.get(par)
        if alerta is None:
            ignorados.append({
                "id_estudante": par[0],
                "id_gatilho": par[1],
                "motivo": "Alerta não está pendente (já enviado, fora da janela do gatilho ou inexistente).",
            })
            continue

        minutas.append(gerar_minuta(alerta, template))

    return {"minutas": minutas, "ignorados": ignorados}

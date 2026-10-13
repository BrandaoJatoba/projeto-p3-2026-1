import calendar
from dataclasses import dataclass
from datetime import date

MESES_PARA_QUALIFICACAO = 18
MESES_PARA_DEFESA = 24


def somar_meses(data_base: date, meses: int) -> date:
    """
    Soma meses a uma data respeitando o último dia do mês.

    Por que não timedelta(days=30 * meses)? Porque meses têm tamanhos
    diferentes: 18 * 30 = 540 dias erra a data final em vários dias.

    Caso de borda: 31/08/2026 + 18 meses -> fevereiro/2028 não tem dia 31,
    então o resultado é 29/02/2028 (2028 é bissexto).
    """
    indice_mes = data_base.month - 1 + meses
    ano = data_base.year + indice_mes // 12
    mes = indice_mes % 12 + 1
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(data_base.day, ultimo_dia_do_mes))


@dataclass(frozen=True)
class PrazosRegimentais:
    """Objeto imutável com os prazos calculados (mais seguro que um dict solto)."""
    prazo_maximo_qualificacao: date
    prazo_maximo_defesa: date


class AcademicTrackingService:

    @staticmethod
    def calcular_prazos_iniciais(data_inicio: date) -> PrazosRegimentais:
        """
        Prazos padrão a partir do início real do semestre de ingresso:
        +18 meses para qualificação e +24 meses para defesa.

        Ainda NÃO desconta suspensões de calendário (greves) nem prorrogações:
        isso fica para o recálculo descrito nas ideias abaixo.
        """
        return PrazosRegimentais(
            prazo_maximo_qualificacao=somar_meses(data_inicio, MESES_PARA_QUALIFICACAO),
            prazo_maximo_defesa=somar_meses(data_inicio, MESES_PARA_DEFESA),
        )

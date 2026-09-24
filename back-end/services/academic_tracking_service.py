# services/academic_tracking_service.py

''' ideias para o futuro

class AcademicTrackingService:

    @staticmethod
    def recalcular_prazo(tipo_prazo_codigo: str, estudante_id: int, db: Session):
        
        # CASO 1: Âncora é o Ingresso (Defesa Final / Qualificação)
        if tipo_prazo_codigo == "DEFESA":
            data_ancora = obter_data_ingresso(estudante_id, db)
            # +24 meses + greves + prorrogações
            return calcular_prazo_defesa(data_ancora, estudante_id, db)

        # CASO 2: Âncora é a Data Prevista/Agendada para a Banca
        elif tipo_prazo_codigo == "HOMOLOGACAO_BANCA":
            defesa = db.query(Defesa).filter_by(id_estudante=estudante_id).first()
            if not defesa.data_agendada:
                return None # Prazo ainda não existe pois não agendou
            return defesa.data_agendada - timedelta(days=30)

        # CASO 3: Âncora é o Evento Concluído (Pós-Defesa / Diploma)
        elif tipo_prazo_codigo == "DIPLOMA_POS_DEFESA":
            defesa = db.query(Defesa).filter_by(id_estudante=estudante_id).first()
            if defesa.status_defesa != "Defendida" or not defesa.data_realizacao:
                return None # Só começa a contar após defender
            return defesa.data_realizacao + timedelta(days=60)
'''
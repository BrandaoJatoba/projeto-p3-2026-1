from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date
import models

# ==========================================
# CRUD: CONFIGURAÇÃO DE ALERTA
# ==========================================

def criar_configuracao_alerta(
    db_connection: Session, 
    tipo_prazo: str, 
    dias_alerta_1: int = 90, 
    dias_alerta_2: int = 30, 
    dias_alerta_3: int = 0
) -> models.ConfiguracaoAlerta:
    """Cria uma nova regra de parametrização de alertas de prazo."""
    nova_config = models.ConfiguracaoAlerta(
        tipo_prazo=tipo_prazo,
        dias_alerta_1=dias_alerta_1,
        dias_alerta_2=dias_alerta_2,
        dias_alerta_3=dias_alerta_3
    )
    db.add(nova_config)
    db.commit()
    db.refresh(nova_config)
    return nova_config

def buscar_configuracao_por_tipo(db_connection: Session, tipo_prazo: str) -> Optional[models.ConfiguracaoAlerta]:
    """Busca a regra de alerta utilizando o nome do tipo de prazo."""
    return db.query(models.ConfiguracaoAlerta).filter(models.ConfiguracaoAlerta.tipo_prazo == tipo_prazo).first()

def listar_configuracoes_alerta(db_connection: Session) -> List[models.ConfiguracaoAlerta]:
    """Retorna todas as parametrizações de alerta cadastradas."""
    return db.query(models.ConfiguracaoAlerta).all()

def atualizar_configuracao_alerta(db_connection: Session, id_config: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.ConfiguracaoAlerta]:
    """Modifica a quantidade de dias para o disparo dos alertas."""
    config = db.query(models.ConfiguracaoAlerta).filter(models.ConfiguracaoAlerta.id_config == id_config).first()
    if not config:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(config, chave):
            setattr(config, chave, valor)
            
    db.commit()
    db.refresh(config)
    return config

def deletar_configuracao_alerta(db_connection: Session, id_config: int) -> bool:
    """Exclui uma configuração de alerta do sistema[cite: 7]."""
    config = db.query(models.ConfiguracaoAlerta).filter(models.ConfiguracaoAlerta.id_config == id_config).first()
    if config:
        db.delete(config)
        db.commit()
        return True
    return False
from datetime import date
from sqlalchemy.orm import Session
from db import models



def criar_semestre(
    db_connection: Session,
    codigo_semestre: str,
    data_inicio_real: date,
    data_fim_real: date,
    dias_letivos: int
):
    semestre = models.SemestreLetivo(
        codigo_semestre=codigo_semestre,
        data_inicio_real=data_inicio_real,
        data_fim_real=data_fim_real,
        dias_letivos=dias_letivos
    )

    db_connection.add(semestre)
    db_connection.commit()
    db_connection.refresh(semestre)

    return semestre

def listar_semestres(db_connection: Session):
    return db_connection.query(models.SemestreLetivo).all()

def buscar_semestre_por_id(
    db_connection: Session,
    id_semestre: int
):
    return (
        db_connection.query(models.SemestreLetivo)
        .filter(models.SemestreLetivo.id_semestre == id_semestre)
        .first()
    )

def atualizar_semestre(
    db_connection: Session,
    semestre,
    data_inicio_real: date,
    data_fim_real: date,
    dias_letivos: int
):
    semestre.data_inicio_real = data_inicio_real
    semestre.data_fim_real = data_fim_real
    semestre.dias_letivos = dias_letivos

    db_connection.commit()
    db_connection.refresh(semestre)

    return semestre

def buscar_semestre_por_codigo(
    db_connection: Session,
    codigo_semestre: str
):
    return (
        db_connection.query(models.SemestreLetivo)
        .filter(models.SemestreLetivo.codigo_semestre == codigo_semestre)
        .first()
    )
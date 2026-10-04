from sqlalchemy.orm import Session
from db import models
from schemas import SubmissaoArtigoCreate, SubmissaoArtigoUpdate 
from typing import List, Optional

def criar_submissao_artigo(db: Session, submissao_artigo: SubmissaoArtigoCreate) -> models.SubmissaoArtigo:
    db_submissao = models.SubmissaoArtigo(**submissao_artigo.model_dump())
    db.add(db_submissao)
    db.commit()
    db.refresh(db_submissao)
    return db_submissao

def obter_submissoes_artigos(db: Session, skip: int = 0, limit: int = 100) -> List[models.SubmissaoArtigo]:
    return db.query(models.SubmissaoArtigo).offset(skip).limit(limit).all()


def obter_submissao_artigo_por_id(db: Session, id_artigo: int) -> Optional[models.SubmissaoArtigo]:
    return db.query(models.SubmissaoArtigo).filter(models.SubmissaoArtigo.id_artigo  == id_artigo).first() 

def atualizar_submissao_artigo(
    db: Session, 
    id_artigo: int, 
    atualizacoes: SubmissaoArtigoUpdate
) -> Optional[models.SubmissaoArtigo]:
    # 1. Busca a submissão pelo ID da chave primária (id_artigo)
    submissao_artigo = (
        db.query(models.SubmissaoArtigo)
        .filter(models.SubmissaoArtigo.id_artigo == id_artigo)
        .first()
    )
    if not submissao_artigo:
        return None

    # 2. Extrai apenas os campos que o cliente enviou explicitamente na requisição
    dados_atualizacao = atualizacoes.model_dump(exclude_unset=True)

    # 3. Atualiza dinamicamente os atributos da instância do ORM
    for chave, valor in dados_atualizacao.items():
        setattr(submissao_artigo, chave, valor)

    # 4. Persiste no banco de dados
    db.commit()
    db.refresh(submissao_artigo)
    return submissao_artigo

def deletar_submissao_artigo(db: Session, id_submissao: int) -> bool:
    submissao_artigo = db.query(models.SubmissaoArtigo).filter(models.SubmissaoArtigo.id_submissao == id_submissao).first()
    if submissao_artigo:
        db.delete(submissao_artigo)
        db.commit()
        return True
    return False


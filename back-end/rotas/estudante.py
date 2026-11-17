"""
Rotas de Estudantes (/estudantes).

Divisão de responsabilidades:
- Esta camada fala HTTP: recebe o schema, decide os códigos de erro
  (400, 404, 422) e devolve a resposta.
- db/estudante.py fala com o banco.
- services/academic_tracking_service.py conhece as regras de prazo.

Regra de negócio: NÃO existe rota DELETE para estudantes. A saída do programa
(desligamento, titulação etc.) é feita alterando status_atual via PUT,
preservando o histórico acadêmico.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import estudante as crud_estudante
from db import semestre as crud_semestre
from db import professor as crud_professor
from db.enumStatus import StatusEstudanteEnum, TipoOrientacao
from schemas import (
    EstudanteCreate,
    EstudanteUpdate,
    EstudanteResponse,
    EstudanteDetalhado,
    EstudantePaginado,
    EstudanteOrientadorCreate,
)
from security import autorizar


router = APIRouter(prefix="/estudantes", tags=["Estudantes"])

# Perfis que gerenciam discentes. Definido uma vez para não repetir em cada rota.
PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]


def _montar_detalhado(db_connection: Session, estudante) -> EstudanteDetalhado:
    """Junta os dados cadastrais (incluindo orientações N:N) com dissertação, qualificação e defesa."""
    dissertacao, qualificacao, defesa = crud_estudante.buscar_marcos_do_estudante(
        db_connection, estudante.id_estudante
    )
    base = EstudanteResponse.model_validate(estudante).model_dump(exclude={"id_orientador"})
    return EstudanteDetalhado(
        **base,
        dissertacao=dissertacao,
        qualificacao=qualificacao,
        defesa=defesa,
    )


def _validar_professores_existem(
    db_connection: Session,
    orientacoes: Optional[List[Any]] = None,
    id_orientador: Optional[int] = None,
) -> None:
    """Garante que todos os professores referenciados existem no banco (retorna 404 caso contrário)."""
    ids_para_validar = []

    if orientacoes:
        for item in orientacoes:
            id_prof = item["id_professor"] if isinstance(item, dict) else item.id_professor
            ids_para_validar.append(id_prof)

    if id_orientador is not None:
        ids_para_validar.append(id_orientador)

    for id_prof in dict.fromkeys(ids_para_validar):
        if crud_professor.buscar_professor_por_id(db_connection, id_prof) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor (orientador/coorientador) com ID {id_prof} não encontrado.",
            )


# --------------------------------------------------------------------------
# POST /estudantes — cadastro + inicialização dos marcos (transação única)
# --------------------------------------------------------------------------
@router.post(
    "",
    response_model=EstudanteDetalhado,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_estudante(
    dados: EstudanteCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    # 1. Matrícula única -> 400
    if crud_estudante.buscar_estudante_por_matricula(db_connection, dados.matricula):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um estudante com a matrícula {dados.matricula}.",
        )

    # 2. E-mail também é UNIQUE no modelo
    if dados.email and crud_estudante.buscar_estudante_por_email(db_connection, dados.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um estudante com este e-mail.",
        )

    # 3. Semestre precisa existir -> 404
    semestre = crud_semestre.buscar_semestre_por_id(db_connection, dados.id_semestre)
    if semestre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semestre letivo não encontrado.",
        )

    # 4. data_inicio_real é necessária para o cálculo dos prazos regimentais
    if semestre.data_inicio_real is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"O semestre {semestre.codigo_semestre} não tem data_inicio_real "
                "cadastrada; não é possível calcular os prazos regimentais."
            ),
        )

    # 5. Todos os orientadores/coorientadores informados precisam existir -> 404
    _validar_professores_existem(
        db_connection,
        orientacoes=dados.orientacoes,
        id_orientador=dados.id_orientador,
    )

    # 6. Criação atômica
    try:
        novo_estudante = crud_estudante.criar_estudante_com_marcos(
            db_connection,
            matricula=dados.matricula,
            nome_discente=dados.nome_discente,
            semestre=semestre,
            id_orientador=dados.id_orientador,
            orientacoes=dados.orientacoes,
            eh_bolsista=dados.eh_bolsista,
            email=dados.email,
            prazo_conclusao_sigaa=dados.prazo_conclusao_sigaa,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Matrícula, e-mail ou vínculo de orientação inválido.",
        )

    return _montar_detalhado(db_connection, novo_estudante)


# --------------------------------------------------------------------------
# GET /estudantes — listagem paginada com filtros combináveis
# --------------------------------------------------------------------------
@router.get("", response_model=EstudantePaginado)
def listar_estudantes(
    status_atual: Optional[StatusEstudanteEnum] = Query(None, description="Ex.: ATIVO, DESLIGADO"),
    id_semestre: Optional[int] = Query(None, description="Turma de ingresso"),
    id_orientador: Optional[int] = Query(None, description="Discentes vinculados a um docente"),
    tipo_orientacao: Optional[TipoOrientacao] = Query(
        None, description="Filtra o papel do docente (ORIENTADOR ou COORIENTADOR)"
    ),
    eh_bolsista: Optional[bool] = Query(None, description="Discentes bolsistas"),
    busca: Optional[str] = Query(None, min_length=1, max_length=100, description="Trecho do nome ou matrícula"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ordenar_por: str = Query("nome_discente", description="Coluna para ordenação (ex: nome_discente, matricula)"),
    ordem_desc: bool = Query(False, description="Ordem decrescente (True) ou crescente (False)"),
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    total, itens = crud_estudante.listar_estudantes_filtrados(
        db_connection,
        status_atual=status_atual,
        id_semestre=id_semestre,
        id_orientador=id_orientador,
        tipo_orientacao=tipo_orientacao,
        eh_bolsista=eh_bolsista,
        busca=busca,
        skip=skip,
        limit=limit,
        ordenar_por=ordenar_por,
        ordem_desc=ordem_desc,
    )
    return EstudantePaginado(total=total, skip=skip, limit=limit, itens=itens)


# --------------------------------------------------------------------------
# GET /estudantes/{id_estudante} — perfil detalhado
# --------------------------------------------------------------------------
@router.get("/{id_estudante}", response_model=EstudanteDetalhado)
def obter_estudante(
    id_estudante: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    estudante = crud_estudante.buscar_estudante_por_id(db_connection, id_estudante)
    if estudante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudante não encontrado.",
        )
    return _montar_detalhado(db_connection, estudante)


# --------------------------------------------------------------------------
# PUT /estudantes/{id_estudante} — dados cadastrais, orientadores e status
# --------------------------------------------------------------------------
@router.put("/{id_estudante}", response_model=EstudanteDetalhado)
def atualizar_estudante(
    id_estudante: int,
    dados: EstudanteUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    estudante = crud_estudante.buscar_estudante_por_id(db_connection, id_estudante)
    if estudante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudante não encontrado.",
        )

    updates = dados.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo enviado para atualização.",
        )

    for campo in ("nome_discente", "status_atual", "eh_bolsista"):
        if campo in updates and updates[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O campo '{campo}' não pode ser nulo.",
            )

    # Valida todos os docentes enviados em `orientacoes` ou no atalho legado `id_orientador`
    _validar_professores_existem(
        db_connection,
        orientacoes=updates.get("orientacoes"),
        id_orientador=updates.get("id_orientador"),
    )

    novo_email = updates.get("email")
    if novo_email:
        dono = crud_estudante.buscar_estudante_por_email(db_connection, novo_email)
        if dono is not None and dono.id_estudante != id_estudante:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro estudante com este e-mail.",
            )

    try:
        estudante = crud_estudante.atualizar_estudante_por_id(db_connection, estudante, updates)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar: violação de unicidade ou de chave estrangeira.",
        )

    return _montar_detalhado(db_connection, estudante)


# --------------------------------------------------------------------------
# POST /estudantes/{id_estudante}/orientadores — vincula ou atualiza papel
# --------------------------------------------------------------------------
@router.post(
    "/{id_estudante}/orientadores",
    response_model=EstudanteDetalhado,
    status_code=status.HTTP_200_OK,
)
def vincular_orientador(
    id_estudante: int,
    dados: EstudanteOrientadorCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    estudante = crud_estudante.buscar_estudante_por_id(db_connection, id_estudante)
    if estudante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudante não encontrado.",
        )

    if crud_professor.buscar_professor_por_id(db_connection, dados.id_professor) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado.",
        )

    try:
        estudante = crud_estudante.vincular_orientador_estudante(
            db_connection,
            estudante=estudante,
            id_professor=dados.id_professor,
            tipo_orientacao=dados.tipo_orientacao,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível vincular o orientador (violação de regra de unicidade).",
        )

    return _montar_detalhado(db_connection, estudante)


# --------------------------------------------------------------------------
# DELETE /estudantes/{id_estudante}/orientadores/{id_professor} — desvincula
# --------------------------------------------------------------------------
@router.delete(
    "/{id_estudante}/orientadores/{id_professor}",
    response_model=EstudanteDetalhado,
)
def desvincular_orientador(
    id_estudante: int,
    id_professor: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    estudante = crud_estudante.buscar_estudante_por_id(db_connection, id_estudante)
    if estudante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudante não encontrado.",
        )

    removido = crud_estudante.remover_orientador_estudante(
        db_connection,
        estudante=estudante,
        id_professor=id_professor,
    )
    if not removido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vínculo de orientação não encontrado para este estudante.",
        )

    estudante = crud_estudante.buscar_estudante_por_id(db_connection, id_estudante)
    return _montar_detalhado(db_connection, estudante)
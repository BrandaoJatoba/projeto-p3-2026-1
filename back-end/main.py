from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rotas import auth
from rotas import semestre

app = FastAPI(title="API PPGI")

# Libera o acesso para o Vue.js (Front-End)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# diz ao FastAPI que a função abaixo é responsável por tratar as
# requisições que vão para: o path / usando uma operação get
@app.get("/")
def home():
    return {"status": "API PPGI rodando com sucesso!"}

# Inclui o roteador de rotas
app.include_router(auth.router)
app.include_router(semestre.router)




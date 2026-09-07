# Sistema de Acompanhamento Acadêmico — PPGI
Repositório oficial do projeto desenvolvido para a disciplina de Programação 3 (P3) do Instituto de Computação.

# Responsável Técnico Back-End : Elis
# Respónsável Tecnico do Banco de Dados: João

# Módulo de Banco de Dados & Camada ORM (PPGI - UFAL)

Este módulo é responsável pela camada de persistência de dados da aplicação, utilizando **SQLAlchemy** e **SQLite**. Ele contém as definições das tabelas, configurações de conexão e funções utilitárias para manipulação do banco de dados (CRUD).

---

## 🛠️ Configuração do Ambiente e Instalação

### 1. Requisitos Previstos
Certifique-se de ter o Python 3.10+ instalado.

### 2. Instalar Dependências
Instale as bibliotecas necessárias para executar a camada de banco de dados e autenticação:

```bash
pip install sqlalchemy argon2-cffi
```

## 🚀 Inicializando o Banco de Dados
Para criar o diretório, o arquivo SQLite (database_ppgi.db), todas as tabelas e popular o usuário ADMIN inicial junto com os perfis padrão do sistema, execute o comando no terminal NA PASTA BACK-END:

```bash
python init_database.py
```

Credenciais de Teste Geradas:
E-mail Admin: admin.ppgi@ic.ufal.br
Senha: senha123

## 💻 Como Consumir o Banco de Dados no FastAPI
Para integrar o banco de dados às rotas do FastAPI, utilize a injeção de dependência (Depends) com a função get_db do módulo database.py.

## 📌 Guia Rápido do Retorno das Funções CRUD

```python
crud.validar_usuario(db, email, senha)
```

Retorna o objeto Usuario em caso de sucesso.

Retorna None se o e-mail não for localizado.

Retorna False se a senha estiver incorreta.

```python
crud.criar_usuario(db, email, senha)
```

Retorna o objeto Usuario cadastrado.

Retorna None caso ocorra erro de duplicidade do e-mail (IntegrityError).

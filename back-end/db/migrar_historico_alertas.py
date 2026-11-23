"""
Migração pontual: adiciona as colunas `assunto` e `corpo_mensagem` em
historico_alertas_enviados num banco JÁ existente (o projeto não usa Alembic).

Uso (dentro de back-end/):  py -m db.migrar_historico_alertas
Pode rodar mais de uma vez: só adiciona o que faltar. Bancos criados do zero
pelo init_database já nascem com as colunas.
"""

from sqlalchemy import inspect, text

from db.database import engine

COLUNAS_NOVAS = {
    "assunto": "VARCHAR(255)",
    "corpo_mensagem": "TEXT",
}


def migrar() -> None:
    existentes = {c["name"] for c in inspect(engine).get_columns("historico_alertas_enviados")}
    with engine.begin() as conexao:
        for nome, tipo in COLUNAS_NOVAS.items():
            if nome in existentes:
                print(f"Coluna '{nome}' já existe.")
                continue
            conexao.execute(text(f"ALTER TABLE historico_alertas_enviados ADD COLUMN {nome} {tipo}"))
            print(f"Coluna '{nome}' adicionada.")


if __name__ == "__main__":
    migrar()

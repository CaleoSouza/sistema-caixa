"""
database.py - Conexão e criação das tabelas do banco de dados SQLite.
Centraliza toda a estrutura do banco de dados do Sistema Caixa.
"""

import sqlite3
import os

# Caminho do arquivo do banco de dados (na raiz do projeto)
DB_PATH = os.path.join(os.path.dirname(__file__), "sistema_caixa.db")


def conectar():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    conn.execute("PRAGMA foreign_keys = ON")  # habilita integridade referencial
    return conn


def criar_tabelas():
    """Cria todas as tabelas do sistema, caso ainda não existam."""
    conn = conectar()
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # Tabela: configuracoes
    # Armazena preferências do sistema (nome da empresa, logo, etc.)
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT    UNIQUE NOT NULL,
            valor TEXT
        )
    """)

    # ------------------------------------------------------------------
    # Tabela: produtos
    # Cadastro de produtos com controle de estoque e código de barras
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nome             TEXT    NOT NULL,
            descricao        TEXT,
            categoria        TEXT,
            preco            REAL    NOT NULL DEFAULT 0.0,
            preco_custo      REAL             DEFAULT 0.0,
            quantidade       INTEGER NOT NULL DEFAULT 0,
            estoque_minimo   INTEGER          DEFAULT 5,
            codigo_barras    TEXT    UNIQUE,
            imagem           TEXT,
            ativo            INTEGER          DEFAULT 1,
            criado_em        TEXT             DEFAULT (datetime('now','localtime')),
            atualizado_em    TEXT             DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------
    # Tabela: clientes
    # Cadastro de clientes com suporte a crediário
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nome           TEXT    NOT NULL,
            cpf            TEXT,
            telefone       TEXT,
            email          TEXT,
            endereco       TEXT,
            foto           TEXT,
            tem_crediario  INTEGER          DEFAULT 0,
            limite_credito REAL             DEFAULT 0.0,
            debito_atual   REAL             DEFAULT 0.0,
            ativo          INTEGER          DEFAULT 1,
            criado_em      TEXT             DEFAULT (datetime('now','localtime')),
            atualizado_em  TEXT             DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------
    # Tabela: vendas
    # Cabeçalho de cada venda realizada
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id       INTEGER,
            total            REAL    NOT NULL DEFAULT 0.0,
            desconto         REAL             DEFAULT 0.0,
            total_final      REAL    NOT NULL DEFAULT 0.0,
            forma_pagamento  TEXT             DEFAULT 'dinheiro',
            status           TEXT             DEFAULT 'concluida',
            criado_em        TEXT             DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    # ------------------------------------------------------------------
    # Tabela: itens_venda
    # Detalhamento dos produtos de cada venda
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id        INTEGER NOT NULL,
            produto_id      INTEGER NOT NULL,
            quantidade      INTEGER NOT NULL,
            preco_unitario  REAL    NOT NULL,
            subtotal        REAL    NOT NULL,
            FOREIGN KEY (venda_id)   REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)

    # ------------------------------------------------------------------
    # Valores padrão das configurações do sistema
    # ------------------------------------------------------------------
    configs_padrao = [
        ("nome_empresa", "Nome da Empresa"),
        ("logo_empresa", ""),
        ("estoque_minimo_alerta", "5"),
        ("versao_sistema", "1.0.0"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)",
        configs_padrao,
    )

    conn.commit()
    conn.close()


# Permite inicializar o banco executando este arquivo diretamente
if __name__ == "__main__":
    criar_tabelas()
    print("Banco de dados inicializado com sucesso.")
    print(f"Arquivo: {DB_PATH}")

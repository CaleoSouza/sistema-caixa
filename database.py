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
            fornecedor       TEXT,
            preco            REAL    NOT NULL DEFAULT 0.0,
            preco_custo      REAL             DEFAULT 0.0,
            quantidade       INTEGER NOT NULL DEFAULT 0,
            estoque_minimo   INTEGER          DEFAULT 5,
            codigo_barras    TEXT    UNIQUE,
            data_validade    TEXT,
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
            taxa_cartao      REAL             DEFAULT 0.0,
            parcelas         INTEGER          DEFAULT 1,
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
    # Tabela: crediario_itens
    # Produtos/serviços anotados no crediário de cada cliente
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crediario_itens (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id      INTEGER NOT NULL,
            produto_nome    TEXT    NOT NULL,
            data            TEXT    NOT NULL,
            quantidade      INTEGER NOT NULL DEFAULT 1,
            preco_unitario  REAL    NOT NULL DEFAULT 0.0,
            total           REAL    NOT NULL DEFAULT 0.0,
            criado_em       TEXT             DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    # ------------------------------------------------------------------
    # Tabela: historico_pagamentos
    # Pagamentos realizados por clientes no crediário
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_pagamentos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id  INTEGER NOT NULL,
            data        TEXT    NOT NULL,
            tipo        TEXT    NOT NULL,
            valor       REAL    NOT NULL DEFAULT 0.0,
            criado_em   TEXT             DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    # ------------------------------------------------------------------
    # Tabela: despesas
    # Controle de despesas da empresa (contas, compras, pagamentos, etc.)
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao        TEXT    NOT NULL,
            data             TEXT    NOT NULL,
            responsavel      TEXT,
            valor            REAL    NOT NULL DEFAULT 0.0,
            forma_pagamento  TEXT             DEFAULT 'dinheiro',
            status           TEXT             DEFAULT 'em_aberto',
            criado_em        TEXT             DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------
    # Migração: adiciona colunas novas em bancos já existentes
    # Preserva todos os dados cadastrados anteriormente
    # ------------------------------------------------------------------
    _migrar_tabelas(conn)

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


def _migrar_tabelas(conn):
    """
    Adiciona colunas criadas após a versão inicial do banco.
    Usa ALTER TABLE para não perder dados já cadastrados.
    """
    # Migrações da tabela produtos
    colunas_produtos = [
        row[1] for row in conn.execute("PRAGMA table_info(produtos)")
    ]
    for nome, tipo in [("fornecedor", "TEXT"), ("data_validade", "TEXT")]:
        if nome not in colunas_produtos:
            conn.execute(f"ALTER TABLE produtos ADD COLUMN {nome} {tipo}")

    # Migrações da tabela clientes
    colunas_clientes = [
        row[1] for row in conn.execute("PRAGMA table_info(clientes)")
    ]
    for nome, tipo in [("cidade", "TEXT"), ("data_nascimento", "TEXT")]:
        if nome not in colunas_clientes:
            conn.execute(f"ALTER TABLE clientes ADD COLUMN {nome} {tipo}")

    # Migrações da tabela vendas
    colunas_vendas = [
        row[1] for row in conn.execute("PRAGMA table_info(vendas)")
    ]
    for nome, tipo in [("taxa_cartao", "REAL DEFAULT 0.0"), ("parcelas", "INTEGER DEFAULT 1")]:
        if nome not in colunas_vendas:
            conn.execute(f"ALTER TABLE vendas ADD COLUMN {nome} {tipo}")


# Permite inicializar o banco executando este arquivo diretamente
if __name__ == "__main__":
    criar_tabelas()
    print("Banco de dados inicializado com sucesso.")
    print(f"Arquivo: {DB_PATH}")

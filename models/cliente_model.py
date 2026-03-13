"""
cliente_model.py - Consultas ao banco de dados para a entidade Cliente.
Toda comunicação direta com o SQLite referente a clientes fica aqui.
"""

from database import conectar


# ------------------------------------------------------------------
# Leitura
# ------------------------------------------------------------------

def listar_em_atraso() -> list:
    """
    Retorna clientes ativos com crediário em atraso.
    Regra:
    - Com pagamentos: último pagamento há mais de 30 dias.
    - Sem pagamentos: item mais antigo há mais de 30 dias.
    """
    conn = conectar()
    rows = conn.execute(
        """SELECT id, nome, cpf, telefone, email, cidade, endereco,
                  foto, tem_crediario, limite_credito, debito_atual
           FROM clientes
           WHERE ativo = 1
             AND tem_crediario = 1
             AND debito_atual > 0
             AND (
               -- Com pagamentos: último pagamento passou de 30 dias
               (
                 EXISTS (
                   SELECT 1 FROM historico_pagamentos hp
                   WHERE hp.cliente_id = clientes.id
                 )
                 AND (
                   SELECT MAX(
                     substr(hp2.data,7,4)||'-'||substr(hp2.data,4,2)||'-'||substr(hp2.data,1,2)
                   )
                   FROM historico_pagamentos hp2
                   WHERE hp2.cliente_id = clientes.id
                 ) < date('now', '-30 days')
               )
               OR
               -- Sem pagamentos: item mais antigo passou de 30 dias
               (
                 NOT EXISTS (
                   SELECT 1 FROM historico_pagamentos hp
                   WHERE hp.cliente_id = clientes.id
                 )
                 AND EXISTS (
                   SELECT 1 FROM crediario_itens ci
                   WHERE ci.cliente_id = clientes.id
                     AND (
                       substr(ci.data,7,4)||'-'||substr(ci.data,4,2)||'-'||substr(ci.data,1,2)
                       < date('now', '-30 days')
                     )
                 )
               )
             )
           ORDER BY debito_atual DESC""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_clientes(busca: str = "") -> list:
    """
    Retorna lista de clientes ativos.
    Se 'busca' for informado, filtra por nome, CPF, telefone ou cidade.
    """
    conn = conectar()
    if busca:
        termo = f"%{busca}%"
        rows = conn.execute(
            """SELECT id, nome, cpf, telefone, email, cidade, endereco,
                      foto, tem_crediario, limite_credito, debito_atual
               FROM clientes
               WHERE ativo = 1
                 AND (nome LIKE ? OR cpf LIKE ? OR telefone LIKE ? OR cidade LIKE ?)
               ORDER BY nome""",
            (termo, termo, termo, termo),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT id, nome, cpf, telefone, email, cidade, endereco,
                      foto, tem_crediario, limite_credito, debito_atual
               FROM clientes
               WHERE ativo = 1
               ORDER BY nome""",
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_por_id(cliente_id: int) -> dict | None:
    """Retorna um cliente pelo ID ou None se não encontrado."""
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM clientes WHERE id = ? AND ativo = 1", (cliente_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ------------------------------------------------------------------
# Resumo para os cards da tela
# ------------------------------------------------------------------

def resumo_clientes() -> dict:
    """Retorna estatísticas para os 3 cards da tela de clientes."""
    conn = conectar()

    total = conn.execute(
        "SELECT COUNT(*) FROM clientes WHERE ativo = 1"
    ).fetchone()[0]

    # Em atraso: débito pendente E (sem pagamentos com item vencido OU último pagamento vencido)
    em_atraso = conn.execute(
        """SELECT COUNT(*) FROM clientes
           WHERE ativo = 1
             AND tem_crediario = 1
             AND debito_atual > 0
             AND (
               (
                 EXISTS (SELECT 1 FROM historico_pagamentos hp WHERE hp.cliente_id = clientes.id)
                 AND (
                   SELECT MAX(
                     substr(hp2.data,7,4)||'-'||substr(hp2.data,4,2)||'-'||substr(hp2.data,1,2)
                   )
                   FROM historico_pagamentos hp2
                   WHERE hp2.cliente_id = clientes.id
                 ) < date('now', '-30 days')
               )
               OR (
                 NOT EXISTS (SELECT 1 FROM historico_pagamentos hp WHERE hp.cliente_id = clientes.id)
                 AND EXISTS (
                   SELECT 1 FROM crediario_itens ci
                   WHERE ci.cliente_id = clientes.id
                     AND (
                       substr(ci.data,7,4)||'-'||substr(ci.data,4,2)||'-'||substr(ci.data,1,2)
                       < date('now', '-30 days')
                     )
                 )
               )
             )"""
    ).fetchone()[0]

    # Em dia: tem crediário mas não se enquadra em atraso
    em_dia = conn.execute(
        """SELECT COUNT(*) FROM clientes
           WHERE ativo = 1
             AND tem_crediario = 1
             AND (
               debito_atual = 0
               OR (
                 EXISTS (SELECT 1 FROM historico_pagamentos hp WHERE hp.cliente_id = clientes.id)
                 AND (
                   SELECT MAX(
                     substr(hp2.data,7,4)||'-'||substr(hp2.data,4,2)||'-'||substr(hp2.data,1,2)
                   )
                   FROM historico_pagamentos hp2
                   WHERE hp2.cliente_id = clientes.id
                 ) >= date('now', '-30 days')
               )
               OR (
                 NOT EXISTS (SELECT 1 FROM historico_pagamentos hp WHERE hp.cliente_id = clientes.id)
                 AND NOT EXISTS (
                   SELECT 1 FROM crediario_itens ci
                   WHERE ci.cliente_id = clientes.id
                     AND (
                       substr(ci.data,7,4)||'-'||substr(ci.data,4,2)||'-'||substr(ci.data,1,2)
                       < date('now', '-30 days')
                     )
                 )
               )
             )"""
    ).fetchone()[0]

    conn.close()
    return {"total": total, "em_dia": em_dia, "em_atraso": em_atraso}


# ------------------------------------------------------------------
# Escrita
# ------------------------------------------------------------------

def inserir_cliente(dados: dict) -> int:
    """Insere um novo cliente e retorna o ID gerado."""
    conn = conectar()
    cursor = conn.execute(
        """INSERT INTO clientes
               (nome, cpf, telefone, email, cidade, endereco, foto,
                tem_crediario, limite_credito, debito_atual, data_nascimento)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            dados.get("nome"),
            dados.get("cpf") or None,
            dados.get("telefone") or None,
            dados.get("email") or None,
            dados.get("cidade") or None,
            dados.get("endereco") or None,
            dados.get("foto") or None,
            int(dados.get("tem_crediario", 0)),
            float(dados.get("limite_credito", 0.0)),
            float(dados.get("debito_atual", 0.0)),
            dados.get("data_nascimento") or None,
        ),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def atualizar_cliente(cliente_id: int, dados: dict) -> bool:
    """Atualiza os dados de um cliente existente."""
    conn = conectar()
    conn.execute(
        """UPDATE clientes
           SET nome=?, cpf=?, telefone=?, email=?, cidade=?, endereco=?, foto=?,
               tem_crediario=?, limite_credito=?, debito_atual=?, data_nascimento=?,
               atualizado_em=datetime('now','localtime')
           WHERE id=? AND ativo=1""",
        (
            dados.get("nome"),
            dados.get("cpf") or None,
            dados.get("telefone") or None,
            dados.get("email") or None,
            dados.get("cidade") or None,
            dados.get("endereco") or None,
            dados.get("foto") or None,
            int(dados.get("tem_crediario", 0)),
            float(dados.get("limite_credito", 0.0)),
            float(dados.get("debito_atual", 0.0)),
            dados.get("data_nascimento") or None,
            cliente_id,
        ),
    )
    conn.commit()
    ok = conn.execute("SELECT changes()").fetchone()[0] > 0
    conn.close()
    return ok


def excluir_cliente(cliente_id: int) -> bool:
    """Exclusão lógica do cliente (ativo = 0)."""
    conn = conectar()
    conn.execute(
        "UPDATE clientes SET ativo = 0, atualizado_em = datetime('now','localtime') WHERE id = ?",
        (cliente_id,),
    )
    conn.commit()
    conn.close()
    return True

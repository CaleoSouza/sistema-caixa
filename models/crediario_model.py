"""
crediario_model.py - Consultas ao banco de dados para crediário e histórico de pagamentos.
Gerencia itens anotados no crediário e pagamentos dos clientes.
"""

from database import conectar


# ------------------------------------------------------------------
# Crediário — itens anotados
# ------------------------------------------------------------------

def listar_itens(cliente_id: int) -> list:
    """Retorna os itens do crediário de um cliente, do mais recente ao mais antigo."""
    conn = conectar()
    rows = conn.execute(
        """SELECT id, produto_nome, data, quantidade, preco_unitario, total
           FROM crediario_itens
           WHERE cliente_id = ?
           ORDER BY criado_em DESC""",
        (cliente_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def inserir_item(dados: dict) -> int:
    """Insere um item no crediário e sincroniza o débito do cliente."""
    conn = conectar()
    cursor = conn.execute(
        """INSERT INTO crediario_itens
               (cliente_id, produto_nome, data, quantidade, preco_unitario, total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            int(dados["cliente_id"]),
            dados["produto_nome"],
            dados["data"],
            int(dados["quantidade"]),
            float(dados["preco_unitario"]),
            float(dados["total"]),
        ),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    _sincronizar_debito(int(dados["cliente_id"]))
    return novo_id


def atualizar_item(item_id: int, dados: dict) -> bool:
    """Atualiza um item do crediário."""
    conn = conectar()
    conn.execute(
        """UPDATE crediario_itens
           SET produto_nome=?, data=?, quantidade=?, preco_unitario=?, total=?
           WHERE id=?""",
        (
            dados["produto_nome"],
            dados["data"],
            int(dados["quantidade"]),
            float(dados["preco_unitario"]),
            float(dados["total"]),
            item_id,
        ),
    )
    conn.commit()
    conn.close()
    _sincronizar_debito(int(dados["cliente_id"]))
    return True


def excluir_item(item_id: int, cliente_id: int) -> bool:
    """Remove um item do crediário."""
    conn = conectar()
    conn.execute("DELETE FROM crediario_itens WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    _sincronizar_debito(cliente_id)
    return True


# ------------------------------------------------------------------
# Histórico de pagamentos
# ------------------------------------------------------------------

def listar_pagamentos(cliente_id: int) -> list:
    """Retorna os pagamentos de um cliente, do mais recente ao mais antigo."""
    conn = conectar()
    rows = conn.execute(
        """SELECT id, data, tipo, valor
           FROM historico_pagamentos
           WHERE cliente_id = ?
           ORDER BY criado_em DESC""",
        (cliente_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def inserir_pagamento(dados: dict) -> int:
    """Registra um pagamento e sincroniza o débito do cliente."""
    conn = conectar()
    cursor = conn.execute(
        """INSERT INTO historico_pagamentos
               (cliente_id, data, tipo, valor)
           VALUES (?, ?, ?, ?)""",
        (
            int(dados["cliente_id"]),
            dados["data"],
            dados["tipo"],
            float(dados["valor"]),
        ),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    _sincronizar_debito(int(dados["cliente_id"]))
    return novo_id


def atualizar_pagamento(pag_id: int, dados: dict) -> bool:
    """Atualiza um registro de pagamento."""
    conn = conectar()
    conn.execute(
        """UPDATE historico_pagamentos
           SET data=?, tipo=?, valor=?
           WHERE id=?""",
        (dados["data"], dados["tipo"], float(dados["valor"]), pag_id),
    )
    conn.commit()
    conn.close()
    _sincronizar_debito(int(dados["cliente_id"]))
    return True


def excluir_pagamento(pag_id: int, cliente_id: int) -> bool:
    """Remove um registro de pagamento."""
    conn = conectar()
    conn.execute("DELETE FROM historico_pagamentos WHERE id=?", (pag_id,))
    conn.commit()
    conn.close()
    _sincronizar_debito(cliente_id)
    return True


# ------------------------------------------------------------------
# Cálculo do saldo devedor
# ------------------------------------------------------------------

def calcular_saldo(cliente_id: int) -> float:
    """
    Saldo devedor = total dos itens - total dos pagamentos.
    Retorna 0.0 se o cliente não deve nada (não permite saldo negativo).
    """
    conn = conectar()
    total_itens = conn.execute(
        "SELECT COALESCE(SUM(total), 0) FROM crediario_itens WHERE cliente_id=?",
        (cliente_id,),
    ).fetchone()[0]
    total_pags = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM historico_pagamentos WHERE cliente_id=?",
        (cliente_id,),
    ).fetchone()[0]
    conn.close()
    return max(0.0, float(total_itens) - float(total_pags))


def tem_debito_em_atraso(cliente_id: int) -> bool:
    """
    Retorna True se o cliente está em atraso, seguindo a regra:
    - Se já fez pagamentos: está em atraso se o último pagamento
      foi há mais de 30 dias (pagamento pontual reseta o prazo).
    - Se nunca pagou: está em atraso se o item mais antigo
      foi anotado há mais de 30 dias.
    """
    conn = conectar()

    # Data do último pagamento (ISO), se existir
    ultimo_pag = conn.execute(
        """SELECT MAX(
               substr(data,7,4)||'-'||substr(data,4,2)||'-'||substr(data,1,2)
           )
           FROM historico_pagamentos
           WHERE cliente_id = ?""",
        (cliente_id,),
    ).fetchone()[0]

    if ultimo_pag:
        # Tem pagamentos: atraso se o último pagamento passou de 30 dias
        row = conn.execute(
            "SELECT 1 WHERE ? < date('now', '-30 days')",
            (ultimo_pag,),
        ).fetchone()
    else:
        # Sem pagamentos: atraso se algum item tem mais de 30 dias
        row = conn.execute(
            """SELECT 1
               FROM crediario_itens
               WHERE cliente_id = ?
                 AND (
                   substr(data,7,4)||'-'||substr(data,4,2)||'-'||substr(data,1,2)
                   < date('now', '-30 days')
                 )
               LIMIT 1""",
            (cliente_id,),
        ).fetchone()

    conn.close()
    return row is not None


def _sincronizar_debito(cliente_id: int):
    """Atualiza debito_atual na tabela clientes com o saldo calculado."""
    saldo = calcular_saldo(cliente_id)
    conn = conectar()
    conn.execute(
        """UPDATE clientes
           SET debito_atual = ?,
               atualizado_em = datetime('now','localtime')
           WHERE id = ?""",
        (saldo, cliente_id),
    )
    conn.commit()
    conn.close()

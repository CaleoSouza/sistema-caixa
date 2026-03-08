"""
utils.py - Funções utilitárias do Sistema Caixa.
Centraliza formatações de moeda, datas e outros padrões brasileiros.
"""

from datetime import datetime


# ------------------------------------------------------------------
# Moeda (Real Brasileiro)
# ------------------------------------------------------------------

def formatar_moeda(valor) -> str:
    """
    Formata um número para o padrão monetário brasileiro.
    Exemplo: 1234.5 → 'R$ 1.234,50'
    """
    try:
        valor = float(valor)
        # Formata com 2 casas decimais, separador de milhar e vírgula decimal
        formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def desformatar_moeda(texto: str) -> float:
    """
    Converte string no padrão brasileiro de volta para float.
    Exemplo: 'R$ 1.234,50' → 1234.50
    """
    try:
        limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(limpo)
    except (ValueError, TypeError):
        return 0.0


# ------------------------------------------------------------------
# Datas (Padrão Brasileiro: dd/mm/aaaa)
# ------------------------------------------------------------------

def formatar_data(data_iso: str) -> str:
    """
    Converte data/datetime no formato ISO (do SQLite) para dd/mm/aaaa.
    Exemplo: '2026-03-08 14:30:00' → '08/03/2026'
             '2026-03-08'          → '08/03/2026'
    """
    if not data_iso:
        return ""
    try:
        # Tenta com data e hora
        dt = datetime.strptime(data_iso[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return data_iso


def formatar_data_hora(data_iso: str) -> str:
    """
    Converte datetime ISO para dd/mm/aaaa HH:MM.
    Exemplo: '2026-03-08 14:30:00' → '08/03/2026 14:30'
    """
    if not data_iso:
        return ""
    try:
        dt = datetime.strptime(data_iso[:16], "%Y-%m-%d %H:%M")
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return data_iso


def data_hoje_br() -> str:
    """Retorna a data atual no formato brasileiro. Exemplo: '08/03/2026'"""
    return datetime.now().strftime("%d/%m/%Y")


def data_hora_agora_br() -> str:
    """Retorna data e hora atual no formato brasileiro. Exemplo: '08/03/2026 14:30'"""
    return datetime.now().strftime("%d/%m/%Y %H:%M")


# ------------------------------------------------------------------
# CPF
# ------------------------------------------------------------------

def formatar_cpf(cpf: str) -> str:
    """
    Formata um CPF numérico para o padrão brasileiro.
    Exemplo: '12345678901' → '123.456.789-01'
    """
    digitos = "".join(filter(str.isdigit, cpf or ""))
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return cpf


# ------------------------------------------------------------------
# Telefone
# ------------------------------------------------------------------

def formatar_telefone(fone: str) -> str:
    """
    Formata telefone para o padrão brasileiro.
    Exemplo: '11999998888' → '(11) 99999-8888'
             '1133334444'  → '(11) 3333-4444'
    """
    digitos = "".join(filter(str.isdigit, fone or ""))
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return fone

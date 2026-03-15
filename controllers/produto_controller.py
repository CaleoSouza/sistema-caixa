"""
produto_controller.py - Lógica de negócio para Produtos.
Intermediário entre a view e o model. Valida dados antes de persistir.
"""

import os
import random
import shutil

from PIL import Image

from models.produto_model import (
    listar_produtos,
    listar_estoque_baixo,
    listar_proximos_vencer,
    buscar_por_id,
    buscar_por_codigo_barras,
    codigo_barras_existe,
    inserir_produto,
    atualizar_produto,
    excluir_produto,
    resumo_produtos,
)

# ------------------------------------------------------------------
# Caminhos de imagens dos produtos
# ------------------------------------------------------------------

# Raiz do projeto (pasta acima de controllers/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pasta onde as imagens dos produtos são armazenadas
PASTA_IMAGENS_PRODUTOS = os.path.join(_BASE_DIR, "imagens", "produtos")


# ------------------------------------------------------------------
# Consultas
# ------------------------------------------------------------------

def obter_lista(busca: str = "") -> list:
    """Retorna produtos com o campo 'status_estoque' calculado."""
    produtos = listar_produtos(busca)
    for p in produtos:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return produtos


def obter_estoque_baixo() -> list:
    """Retorna produtos com estoque baixo (quantidade ≤ estoque_minimo) e status calculado."""
    produtos = listar_estoque_baixo()
    for p in produtos:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return produtos


def obter_proximos_vencer() -> list:
    """Retorna produtos com data_validade nos próximos 30 dias e status calculado."""
    produtos = listar_proximos_vencer()
    for p in produtos:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return produtos


def obter_resumo() -> dict:
    """Retorna os dados dos 5 cards da tela de produtos."""
    return resumo_produtos()


def obter_por_id(produto_id: int) -> dict | None:
    """Retorna um produto pelo ID com status calculado."""
    p = buscar_por_id(produto_id)
    if p:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return p


def obter_por_codigo_barras(codigo: str) -> dict | None:
    """Retorna um produto pelo código de barras com status calculado."""
    p = buscar_por_codigo_barras(codigo)
    if p:
        p["status_estoque"] = _calcular_status(p["quantidade"], p["estoque_minimo"])
    return p


# ------------------------------------------------------------------
# Gravação
# ------------------------------------------------------------------

def salvar(dados: dict, produto_id: int = None) -> tuple[bool, str]:
    """
    Cria ou atualiza um produto após validação.
    Retorna (sucesso: bool, mensagem: str).
    """
    ok, msg = _validar(dados)
    if not ok:
        return False, msg

    if produto_id:
        ok = atualizar_produto(produto_id, dados)
        return ok, "Produto atualizado com sucesso!" if ok else "Erro ao atualizar produto."
    else:
        novo_id = inserir_produto(dados)
        return True, f"Produto cadastrado com sucesso! ID: #{novo_id:02d}"


def remover(produto_id: int) -> tuple[bool, str]:
    """Remove (exclusão lógica) um produto."""
    ok = excluir_produto(produto_id)
    return ok, "Produto removido com sucesso!" if ok else "Erro ao remover produto."


# ------------------------------------------------------------------
# Código de Barras EAN-13
# ------------------------------------------------------------------

def gerar_codigo_ean13(tentativas: int = 10) -> str:
    """
    Gera um código EAN-13 válido com prefixo brasileiro (789).
    Verifica unicidade no banco. Retorna o código gerado.
    """
    for _ in range(tentativas):
        # 789 (prefixo Brasil) + 9 dígitos aleatórios
        corpo = "789" + "".join(str(random.randint(0, 9)) for _ in range(9))
        digito = _calcular_checksum_ean13(corpo)
        codigo = corpo + str(digito)
        if not codigo_barras_existe(codigo):
            return codigo
    raise RuntimeError("Não foi possível gerar um código de barras único.")


def _calcular_checksum_ean13(doze_digitos: str) -> int:
    """
    Calcula o dígito verificador EAN-13.
    Posições ímpares (0-indexed pares): peso 1.
    Posições pares (0-indexed ímpares): peso 3.
    """
    total = sum(
        int(d) * (1 if i % 2 == 0 else 3)
        for i, d in enumerate(doze_digitos)
    )
    return (10 - (total % 10)) % 10


def validar_ean13(codigo: str) -> bool:
    """Verifica se um código EAN-13 é válido (13 dígitos + checksum correto)."""
    if not codigo or len(codigo) != 13 or not codigo.isdigit():
        return False
    esperado = _calcular_checksum_ean13(codigo[:12])
    return int(codigo[12]) == esperado


# ------------------------------------------------------------------
# Imagens dos Produtos
# ------------------------------------------------------------------

def salvar_imagem_produto(
    caminho_origem: str,
    nome_produto: str = "produto",
    produto_id: int = None,
    slot: int = 1,
) -> tuple[str | None, str]:
    """
    Copia e redimensiona a imagem para imagens/produtos/.
    Retorna (nome_arquivo, mensagem). nome_arquivo é None em caso de erro.
    Tamanho máximo aceito: 2 MB.
    O parâmetro slot (1, 2 ou 3) diferencia os nomes de arquivo de cada foto.
    """
    # Verificar tamanho antes de abrir
    if os.path.getsize(caminho_origem) > 2 * 1024 * 1024:
        return None, "Imagem excede o tamanho máximo permitido de 2 MB."

    try:
        os.makedirs(PASTA_IMAGENS_PRODUTOS, exist_ok=True)

        # Montar nome de arquivo único incluindo o slot
        ext = os.path.splitext(caminho_origem)[1].lower() or ".png"
        sufixo = str(produto_id) if produto_id else "novo"
        slug = nome_produto[:30].replace(" ", "_").lower()
        nome_arquivo = f"prod_{sufixo}_{slug}_f{slot}{ext}"
        destino = os.path.join(PASTA_IMAGENS_PRODUTOS, nome_arquivo)

        # Redimensionar para no máximo 400x400 preservando proporções
        img = Image.open(caminho_origem)
        img.thumbnail((400, 400), Image.LANCZOS)
        img.save(destino)

        return nome_arquivo, "Imagem salva com sucesso."
    except Exception as e:
        return None, f"Erro ao salvar imagem: {e}"


def excluir_imagem_produto(nome_arquivo: str) -> None:
    """Remove o arquivo de imagem do produto da pasta imagens/produtos/."""
    if not nome_arquivo:
        return
    caminho = os.path.join(PASTA_IMAGENS_PRODUTOS, nome_arquivo)
    if os.path.isfile(caminho):
        os.remove(caminho)


# ------------------------------------------------------------------
# Status do estoque
# ------------------------------------------------------------------

def _calcular_status(quantidade: int, estoque_minimo: int) -> str:
    """
    Retorna o status textual do estoque pelas faixas fixas:
    - 'sem_estoque'   → quantidade = 0
    - 'estoque_baixo' → quantidade de 1 a 4
    - 'em_estoque'    → quantidade de 5 a 25
    - 'estoque_alto'  → quantidade de 26 a 100.000
    """
    if quantidade <= 0:
        return "sem_estoque"
    if quantidade <= 4:
        return "estoque_baixo"
    if quantidade <= 25:
        return "em_estoque"
    return "estoque_alto"


# ------------------------------------------------------------------
# Validação
# ------------------------------------------------------------------

def _validar(dados: dict) -> tuple[bool, str]:
    """Valida os campos obrigatórios antes de salvar."""
    if not dados.get("nome", "").strip():
        return False, "O campo Nome é obrigatório."

    try:
        preco = float(dados.get("preco", 0))
        if preco < 0:
            raise ValueError
    except (ValueError, TypeError):
        return False, "Preço inválido. Informe um valor numérico positivo."

    try:
        qtd = int(dados.get("quantidade", 0))
        if qtd < 0:
            raise ValueError
    except (ValueError, TypeError):
        return False, "Quantidade inválida. Informe um número inteiro positivo."

    # Validação opcional do código de barras: se informado deve ser EAN-13 válido
    codigo = dados.get("codigo_barras", "")
    if codigo and not validar_ean13(codigo):
        return False, "Código de barras inválido. Deve ser EAN-13 (13 dígitos)."

    return True, ""

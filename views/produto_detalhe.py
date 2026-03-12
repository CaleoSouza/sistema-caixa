"""
produto_detalhe.py - Tela de visualização de detalhes de um Produto.
Exibida dentro da janela principal ao clicar em um item da listagem.
"""

import os
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from controllers.produto_controller import (
    obter_por_id,
    remover,
    PASTA_IMAGENS_PRODUTOS,
)
from utils import formatar_moeda, formatar_data


# ------------------------------------------------------------------
# Mapeamento de status → (texto, cor de fundo, cor do texto)
# ------------------------------------------------------------------
STATUS_BADGE = {
    "sem_estoque":   ("Sem Estoque",   "#fde8e8", "#e53935"),
    "estoque_baixo": ("Estoque Baixo", "#fef3cd", "#d97706"),
    "em_estoque":    ("Em Estoque",    "#e8f5e9", "#2e7d32"),
    "estoque_alto":  ("Estoque Alto",  "#e3f2fd", "#1565c0"),
}

# Ícone e tamanho da imagem de placeholder
_PLACEHOLDER_SIZE = (200, 200)
_PREVIEW_SIZE     = (220, 220)


class ProdutoDetalhe(ctk.CTkFrame):
    """
    Tela de detalhe de produto. Mostra todas as informações do produto
    com opções de editar ou excluir, e botão ← Voltar.
    """

    def __init__(self, parent, controller, produto_id: int, on_voltar=None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)

        self.controller  = controller
        self.produto_id  = produto_id
        self.on_voltar   = on_voltar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Carrega o produto antes de construir a UI
        self.produto = obter_por_id(produto_id)
        if not self.produto:
            messagebox.showerror("Erro", "Produto não encontrado.")
            self._voltar()
            return

        self._construir_ui()

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------

    def _construir_ui(self):
        p = self.produto

        # --- Cabeçalho ---
        self._criar_cabecalho(p)

        # --- Área de conteúdo (imagem + informações) ---
        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
        conteudo.grid_columnconfigure(0, weight=2)  # coluna imagem
        conteudo.grid_columnconfigure(1, weight=5)  # coluna info (maior)

        self._criar_card_imagem(conteudo, p)
        self._criar_card_info(conteudo, p)

    # ------------------------------------------------------------------
    # Cabeçalho: ← Voltar | Título | ✏️ Editar | 🗑️ Excluir
    # ------------------------------------------------------------------

    def _criar_cabecalho(self, p: dict):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=30, pady=(24, 12), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)  # título expande

        # Botão Voltar
        ctk.CTkButton(
            frame,
            text="← Voltar",
            width=100,
            height=36,
            fg_color="#888888",
            hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._voltar,
        ).grid(row=0, column=0, padx=(0, 16))

        # Título: nome do produto
        ctk.CTkLabel(
            frame,
            text=f"📦  {p['nome']}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1f6aa5",
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        # Botão Editar
        ctk.CTkButton(
            frame,
            text="✏️  Editar",
            width=110,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._editar,
        ).grid(row=0, column=2, padx=(8, 6))

        # Botão Excluir
        ctk.CTkButton(
            frame,
            text="🗑️  Excluir",
            width=110,
            height=36,
            fg_color="#e53935",
            hover_color="#c62828",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._excluir,
        ).grid(row=0, column=3)

    # ------------------------------------------------------------------
    # Card esquerdo: imagem do produto
    # ------------------------------------------------------------------

    def _criar_card_imagem(self, pai, p: dict):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        imagem_nome = p.get("imagem")
        if imagem_nome:
            caminho = os.path.join(PASTA_IMAGENS_PRODUTOS, imagem_nome)
            try:
                img = Image.open(caminho)
                img.thumbnail(_PREVIEW_SIZE, Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                lbl = ctk.CTkLabel(card, image=ctk_img, text="")
                lbl._image = ctk_img  # evita garbage collection
                lbl.grid(row=0, column=0, padx=20, pady=20)
                return
            except Exception:
                pass  # fallback para placeholder abaixo

        # Placeholder sem imagem
        ctk.CTkLabel(
            card,
            text="📦\nSem imagem",
            font=ctk.CTkFont(size=16),
            text_color="#cccccc",
            justify="center",
        ).grid(row=0, column=0, padx=20, pady=20)

    # ------------------------------------------------------------------
    # Card direito: informações do produto
    # ------------------------------------------------------------------

    def _criar_card_info(self, pai, p: dict):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=1, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        status = p.get("status_estoque", "em_estoque")
        badge_texto, badge_bg, badge_cor = STATUS_BADGE.get(
            status, ("Em Estoque", "#e8f5e9", "#2e7d32")
        )

        # ------------------------------------------------------------------
        # Campos exibidos: (rótulo, valor)
        # ------------------------------------------------------------------
        validade     = formatar_data(p.get("data_validade") or "") if p.get("data_validade") else "—"
        preco        = formatar_moeda(p.get("preco", 0))
        preco_custo  = formatar_moeda(p.get("preco_custo", 0))
        total_valor  = formatar_moeda(p.get("preco", 0) * p.get("quantidade", 0))
        cadastrado   = formatar_data(p.get("criado_em") or "") or "—"

        campos = [
            ("Categoria",        p.get("categoria")     or "—"),
            ("Fornecedor",       p.get("fornecedor")    or "—"),
            ("Código de Barras", p.get("codigo_barras") or "—"),
            ("Validade",         validade),
            ("Preço de Venda",   preco),
            ("Preço de Custo",   preco_custo),
            ("Quantidade",       str(p.get("quantidade", 0))),
            ("Estoque Mínimo",   str(p.get("estoque_minimo", 5))),
            ("Valor Total",      total_valor),
            ("Cadastrado em",    cadastrado),
        ]

        linha = 0
        pad_y = 4

        for rotulo, valor in campos:
            ctk.CTkLabel(
                card,
                text=rotulo + ":",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#555555",
                anchor="w",
            ).grid(row=linha, column=0, padx=(20, 8), pady=pad_y, sticky="w")

            ctk.CTkLabel(
                card,
                text=valor,
                font=ctk.CTkFont(size=13),
                text_color="#1a1a1a",
                anchor="w",
            ).grid(row=linha, column=1, padx=(0, 20), pady=pad_y, sticky="w")

            linha += 1

        # Badge de status
        ctk.CTkLabel(
            card,
            text="Status:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#555555",
            anchor="w",
        ).grid(row=linha, column=0, padx=(20, 8), pady=pad_y, sticky="w")

        badge = ctk.CTkFrame(card, fg_color=badge_bg, corner_radius=6)
        badge.grid(row=linha, column=1, padx=(0, 20), pady=pad_y, sticky="w")
        ctk.CTkLabel(
            badge,
            text=badge_texto,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=badge_cor,
        ).grid(padx=10, pady=3)

        linha += 1

        # Descrição (se houver)
        descricao = (p.get("descricao") or "").strip()
        if descricao:
            ctk.CTkLabel(
                card,
                text="Descrição:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#555555",
                anchor="nw",
            ).grid(row=linha, column=0, padx=(20, 8), pady=(10, 4), sticky="nw")

            caixa = ctk.CTkTextbox(
                card,
                fg_color="#f5f5f5",
                border_width=0,
                font=ctk.CTkFont(size=13),
                height=60,
                corner_radius=8,
                state="normal",
            )
            caixa.insert("1.0", descricao)
            caixa.configure(state="disabled")
            caixa.grid(row=linha, column=1, padx=(0, 20), pady=(6, 12), sticky="ew")

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _editar(self):
        """Navega para o formulário de edição do produto."""
        from views.produto_form import ProdutoForm

        def voltar_para_detalhe():
            self.controller.mostrar_tela(
                ProdutoDetalhe,
                produto_id=self.produto_id,
                on_voltar=self.on_voltar,
            )

        self.controller.mostrar_tela(
            ProdutoForm,
            produto_id=self.produto_id,
            on_voltar=voltar_para_detalhe,
        )

    def _excluir(self):
        """Confirmação e exclusão lógica do produto."""
        resposta = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja remover o produto '{self.produto['nome']}'?\nEssa ação não pode ser desfeita.",
        )
        if resposta:
            ok, msg = remover(self.produto_id)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                self._voltar()
            else:
                messagebox.showerror("Erro", msg)

    def _voltar(self):
        """Retorna para a tela anterior (listagem de produtos)."""
        if callable(self.on_voltar):
            self.on_voltar()

"""
produtos_view.py - Tela de listagem de Produtos.
Exibe tabela de produtos com busca, status de estoque e cards de resumo.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from controllers.produto_controller import obter_lista, obter_resumo, remover
from utils import formatar_moeda


# ------------------------------------------------------------------
# Mapeamento de status → (texto, cor)
# ------------------------------------------------------------------
STATUS_INFO = {
    "sem_estoque":   ("Sem estoque",   "#e53935"),
    "estoque_baixo": ("Estoque baixo", "#d97706"),
    "em_estoque":    ("Em estoque",    "#1a1a1a"),
    "estoque_alto":  ("Estoque Alto",  "#2e7d32"),
}


class ProdutosView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        # Layout: cabeçalho, busca, tabela (expande), cards
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # tabela cresce

        self._criar_cabecalho()
        self._criar_barra_busca()
        self._criar_tabela()
        self._criar_cards_resumo()

        self.carregar_produtos()

    # ------------------------------------------------------------------
    # Cabeçalho: título + botão Adicionar
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="📦  Produtos",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            frame,
            text="Adicionar Produto",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=160,
            height=36,
            command=self._abrir_formulario,
        ).grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------
    # Barra de busca
    # ------------------------------------------------------------------
    def _criar_barra_busca(self):
        frame = ctk.CTkFrame(self, fg_color="#cccccc", corner_radius=12)
        frame.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            frame,
            placeholder_text="Digite para buscar produtos em tempo real",
            font=ctk.CTkFont(size=13),
            height=40,
            border_width=0,
            fg_color="white",
            corner_radius=8,
        )
        self.entry_busca.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="ew")
        # Busca em tempo real ao digitar
        self.entry_busca.bind("<KeyRelease>", lambda e: self.carregar_produtos())

        ctk.CTkButton(
            frame,
            text="🔍  Buscar",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=110,
            height=40,
            command=self.carregar_produtos,
        ).grid(row=0, column=1, padx=(0, 12), pady=12)

    # ------------------------------------------------------------------
    # Tabela de produtos
    # ------------------------------------------------------------------
    def _criar_tabela(self):
        """Container branco com cabeçalho e lista scrollável."""
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # Título da tabela
        self.label_total = ctk.CTkLabel(
            container,
            text="Lista de Produtos",
            font=ctk.CTkFont(size=13),
            text_color="#444444",
        )
        self.label_total.grid(row=0, column=0, padx=20, pady=(14, 6), sticky="w")

        # Cabeçalho fixo usando Tkinter Canvas (mais controle visual)
        cabecalho = ctk.CTkFrame(container, fg_color="#f0f0f0", corner_radius=0, height=36)
        cabecalho.grid(row=1, column=0, sticky="ew", padx=10)
        cabecalho.grid_propagate(False)
        cabecalho.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

        colunas = ["ID", "Nome", "Quantidade", "Preço", "Total", "Status", "Ações"]
        for i, col in enumerate(colunas):
            ctk.CTkLabel(
                cabecalho,
                text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#555555",
            ).grid(row=0, column=i, padx=8, pady=6, sticky="w")

        # Área scrollável para as linhas
        self.scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="white",
            corner_radius=0,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

        container.grid_rowconfigure(2, weight=1)

    # ------------------------------------------------------------------
    # Cards de resumo (parte inferior)
    # ------------------------------------------------------------------
    def _criar_cards_resumo(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Labels de referência para atualizar valores depois
        self.lbl_cards = {}

        definicoes = [
            ("total",           "Total de Produtos",           "#1f6aa5"),
            ("itens_estoque",   "Itens em Estoque",            "#1f6aa5"),
            ("valor_total",     "Valor Total do Estoque",      "#1f6aa5"),
            ("estoque_baixo",   "Estoque Baixo",               "#1f6aa5"),
            ("proximos_vencer", "Produtos Próximo a\nVencer (30 dias)", "#1f6aa5"),
        ]

        for col, (chave, titulo, cor) in enumerate(definicoes):
            card = ctk.CTkFrame(self.master, fg_color="white", corner_radius=12)
            card = ctk.CTkFrame(frame, fg_color="white", corner_radius=12)
            card.grid(row=0, column=col, padx=6, sticky="ew", ipady=10)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=titulo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=cor,
                justify="center",
            ).grid(row=0, column=0, padx=10, pady=(14, 4))

            lbl = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color="#1a1a1a",
            )
            lbl.grid(row=1, column=0, padx=10, pady=(0, 14))
            self.lbl_cards[chave] = lbl

    # ------------------------------------------------------------------
    # Carregamento e renderização dos produtos
    # ------------------------------------------------------------------
    def carregar_produtos(self, *args):
        """Busca os produtos e renderiza as linhas da tabela."""
        busca = self.entry_busca.get().strip()
        produtos = obter_lista(busca)

        # Atualiza o título com o total
        total = len(produtos)
        self.label_total.configure(text=f"Lista de Produtos ({total} {'item' if total == 1 else 'itens'})")

        # Limpa as linhas anteriores
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Renderiza cada linha
        for linha, p in enumerate(produtos):
            bg = "white" if linha % 2 == 0 else "#f9f9f9"
            self._criar_linha(linha, p, bg)

        # Atualiza os cards de resumo
        self._atualizar_cards()

    def _criar_linha(self, linha: int, produto: dict, bg: str):
        """Renderiza uma linha de produto na tabela."""
        status = produto["status_estoque"]
        txt_status, cor_status = STATUS_INFO.get(status, ("Em estoque", "#1a1a1a"))
        total_valor = produto["preco"] * produto["quantidade"]

        dados_cols = [
            (f"#{produto['id']:02d}",              "#555555", False),
            (produto["nome"],                       "#1a1a1a", False),
            (str(produto["quantidade"]),            "#1a1a1a", False),
            (formatar_moeda(produto["preco"]),      "#1a1a1a", False),
            (formatar_moeda(total_valor),           "#1a1a1a", False),
            (txt_status,                            cor_status, True),
        ]

        for col, (texto, cor, negrito) in enumerate(dados_cols):
            ctk.CTkLabel(
                self.scroll_frame,
                text=texto,
                font=ctk.CTkFont(size=13, weight="bold" if negrito else "normal"),
                text_color=cor,
                anchor="w",
            ).grid(row=linha, column=col, padx=8, pady=6, sticky="w")

        # Botões de ação (editar e excluir)
        frame_acoes = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame_acoes.grid(row=linha, column=6, padx=8, pady=4, sticky="w")

        ctk.CTkButton(
            frame_acoes,
            text="✏️",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color="#e0e0e0",
            text_color="#1f6aa5",
            font=ctk.CTkFont(size=15),
            command=lambda pid=produto["id"]: self._abrir_formulario(pid),
        ).grid(row=0, column=0, padx=(0, 4))

        ctk.CTkButton(
            frame_acoes,
            text="🗑️",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color="#fde8e8",
            text_color="#e53935",
            font=ctk.CTkFont(size=15),
            command=lambda pid=produto["id"], nome=produto["nome"]: self._confirmar_exclusao(pid, nome),
        ).grid(row=0, column=1)

    def _atualizar_cards(self):
        """Atualiza os valores dos 5 cards de resumo."""
        dados = obter_resumo()
        self.lbl_cards["total"].configure(text=str(dados["total"]))
        self.lbl_cards["itens_estoque"].configure(text=str(dados["itens_estoque"]))
        self.lbl_cards["valor_total"].configure(text=formatar_moeda(dados["valor_total"]).replace("R$ ", ""))
        self.lbl_cards["estoque_baixo"].configure(text=str(dados["estoque_baixo"]))
        self.lbl_cards["proximos_vencer"].configure(text=str(dados["proximos_vencer"]))

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def _abrir_formulario(self, produto_id: int = None):
        """Abre o formulário de cadastro/edição (implementado na Etapa 2b)."""
        # Placeholder — será implementado na próxima parte
        messagebox.showinfo("Em breve", "Formulário de produto será implementado na próxima etapa.")

    def _confirmar_exclusao(self, produto_id: int, nome: str):
        """Pede confirmação antes de excluir o produto."""
        resposta = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja remover o produto '{nome}'?\nEssa ação não pode ser desfeita.",
        )
        if resposta:
            ok, msg = remover(produto_id)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                self.carregar_produtos()
            else:
                messagebox.showerror("Erro", msg)

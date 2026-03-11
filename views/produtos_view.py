"""
produtos_view.py - Tela de listagem de Produtos.
Exibe tabela de produtos com busca, status de estoque e cards de resumo.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from controllers.produto_controller import obter_lista, obter_estoque_baixo, obter_proximos_vencer, obter_resumo, remover
from views.produto_form import ProdutoForm
from views.produto_detalhe import ProdutoDetalhe
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

# ------------------------------------------------------------------
# Definição das colunas da tabela: (rótulo, largura_px)
# Larguras fixas garantem alinhamento perfeito entre cabeçalho e linhas
# ------------------------------------------------------------------
COLUNAS_TABELA = [
    ("ID",         70),
    ("Nome",      180),
    ("Quantidade", 100),
    ("Preço",     120),
    ("Total",     120),
    ("Status",    120),
    ("Ações",      90),
]

# Máximo de caracteres antes de truncar com "…" (por coluna)
_MAX_CHARS = [None, 22, None, None, None, None, None]


def _truncar(texto: str, max_chars: int | None) -> str:
    """Trunca texto longo com reticências para manter alinhamento da tabela."""
    if max_chars and len(texto) > max_chars:
        return texto[:max_chars - 1] + "…"
    return texto


class ProdutosView(ctk.CTkFrame):
    def __init__(self, parent, controller, filtro_inicial: str = None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        # Rastreia o filtro ativo: None | "estoque_baixo" | "proximos_vencer"
        self._filtro_ativo = filtro_inicial

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
        # Busca em tempo real ao digitar (limpa o filtro de card ao digitar)
        self.entry_busca.bind("<KeyRelease>", self._ao_digitar_busca)

        ctk.CTkButton(
            frame,
            text="🔍  Buscar",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=110,
            height=40,
            command=self.carregar_produtos,
        ).grid(row=0, column=1, padx=(0, 12), pady=12)

        # Badge que aparece quando um filtro de card está ativo
        self.lbl_filtro_ativo = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#d97706",
            fg_color="transparent",
        )
        self.lbl_filtro_ativo.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 6), sticky="w")

    def _ao_digitar_busca(self, event=None):
        """Ao digitar, limpa o filtro de card e faz a busca normal."""
        if self._filtro_ativo is not None:
            self._filtro_ativo = None
            self._atualizar_visual_cards()
        self.carregar_produtos()

    # ------------------------------------------------------------------
    # Tabela de produtos
    # ------------------------------------------------------------------
    def _criar_tabela(self):
        """Container branco com cabeçalho e lista scrollável alinhados por largura fixa."""
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.grid(row=2, column=0, padx=30, pady=(0, 10), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)

        # Título da tabela
        self.label_total = ctk.CTkLabel(
            container,
            text="Lista de Produtos",
            font=ctk.CTkFont(size=13),
            text_color="#444444",
        )
        self.label_total.grid(row=0, column=0, padx=20, pady=(14, 6), sticky="w")

        # Cabeçalho fixo — uma CTkLabel por coluna com largura exata
        cabecalho = ctk.CTkFrame(container, fg_color="#f0f0f0", corner_radius=0, height=36)
        cabecalho.grid(row=1, column=0, sticky="ew", padx=10)
        cabecalho.grid_propagate(False)

        for i, (rotulo, largura) in enumerate(COLUNAS_TABELA):
            cabecalho.grid_columnconfigure(i, minsize=largura, weight=0)
            ctk.CTkLabel(
                cabecalho,
                text=rotulo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#555555",
                width=largura,
                anchor="w",
            ).grid(row=0, column=i, padx=(8, 0), pady=6, sticky="w")
        # Coluna filler: expande para absorver o espaço da scrollbar e do container
        cabecalho.grid_columnconfigure(len(COLUNAS_TABELA), weight=1)

        # Área scrollável para as linhas — mesmas larguras de coluna
        self.scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color="white",
            corner_radius=0,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        for i, (_, largura) in enumerate(COLUNAS_TABELA):
            self.scroll_frame.grid_columnconfigure(i, minsize=largura, weight=0)
        # Coluna filler: absorve scrollbar e espaço extra, evita corte da última coluna
        self.scroll_frame.grid_columnconfigure(len(COLUNAS_TABELA), weight=1)

    # ------------------------------------------------------------------
    # Cards de resumo (parte inferior)
    # ------------------------------------------------------------------
    def _criar_cards_resumo(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Guarda referências para atualizar valores e visual later
        self.lbl_cards = {}
        self.frm_cards = {}

        # Chaves dos cards que são clicáveis (funcionam como filtro)
        CARDS_CLICAVEIS = {"estoque_baixo", "proximos_vencer"}

        definicoes = [
            ("total",           "Total de Produtos",                    "#1f6aa5"),
            ("itens_estoque",   "Itens em Estoque",                     "#1f6aa5"),
            ("valor_total",     "Valor Total do Estoque",               "#1f6aa5"),
            ("estoque_baixo",   "Estoque Baixo",                        "#d97706"),
            ("proximos_vencer", "Produtos Próximo a\nVencer (30 dias)", "#e53935"),
        ]

        for col, (chave, titulo, cor) in enumerate(definicoes):
            card = ctk.CTkFrame(frame, fg_color="white", corner_radius=12)
            card.grid(row=0, column=col, padx=6, sticky="ew", ipady=10)
            card.grid_columnconfigure(0, weight=1)
            self.frm_cards[chave] = card

            lbl_titulo = ctk.CTkLabel(
                card,
                text=titulo,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=cor,
                justify="center",
            )
            lbl_titulo.grid(row=0, column=0, padx=10, pady=(14, 4))

            lbl_valor = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color="#1a1a1a",
            )
            lbl_valor.grid(row=1, column=0, padx=10, pady=(0, 14))
            self.lbl_cards[chave] = lbl_valor

            # Cards filtráveis: cursor hand2 + clique
            if chave in CARDS_CLICAVEIS:
                for widget in (card, lbl_titulo, lbl_valor):
                    widget.configure(cursor="hand2")
                    widget.bind(
                        "<Button-1>",
                        lambda e, k=chave: self._aplicar_filtro(k),
                    )
                    widget.bind("<Enter>", lambda e, c=card: c.configure(fg_color="#f5f5f5"))
                    widget.bind("<Leave>", lambda e, c=card, k=chave: self._restaurar_cor_card(c, k))

    def _aplicar_filtro(self, filtro: str):
        """
        Ativa ou desativa o filtro do card.
        Clicar no card ativo remove o filtro (toggle).
        """
        if self._filtro_ativo == filtro:
            self._filtro_ativo = None  # toggle: desativa
        else:
            self._filtro_ativo = filtro
        self._atualizar_visual_cards()
        self.carregar_produtos()

    def _restaurar_cor_card(self, card: ctk.CTkFrame, chave: str):
        """Restaura a cor do card conforme se está ativo ou não."""
        if self._filtro_ativo == chave:
            card.configure(fg_color="#fff3cd")   # amarelo suave quando ativo
        else:
            card.configure(fg_color="white")

    def _atualizar_visual_cards(self):
        """Atualiza o highlight visual dos cards e o badge de filtro ativo."""
        NOMES_FILTRO = {
            "estoque_baixo":   "🟡  Filtro: Estoque Baixo — clique no card novamente para remover",
            "proximos_vencer": "🔴  Filtro: Próximos a Vencer — clique no card novamente para remover",
        }
        for chave, card in self.frm_cards.items():
            if self._filtro_ativo == chave:
                card.configure(fg_color="#fff3cd")
            else:
                card.configure(fg_color="white")

        texto_badge = NOMES_FILTRO.get(self._filtro_ativo, "")
        self.lbl_filtro_ativo.configure(text=texto_badge)

    # ------------------------------------------------------------------
    # Carregamento e renderização dos produtos
    # ------------------------------------------------------------------
    def carregar_produtos(self, *args):
        """Busca os produtos (com filtro de card ou busca textual) e renderiza as linhas."""
        # Prioridade: filtro de card > busca textual
        if self._filtro_ativo == "estoque_baixo":
            produtos = obter_estoque_baixo()
        elif self._filtro_ativo == "proximos_vencer":
            produtos = obter_proximos_vencer()
        else:
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

        # Atualiza visual dos cards (highlight do filtro ativo) e os valores
        self._atualizar_visual_cards()
        self._atualizar_cards()

    def _criar_linha(self, linha: int, produto: dict, bg: str):
        """Renderiza uma linha de produto na tabela. Clicar abre o detalhe."""
        status = produto["status_estoque"]
        txt_status, cor_status = STATUS_INFO.get(status, ("Em estoque", "#1a1a1a"))
        total_valor = produto["preco"] * produto["quantidade"]

        # Cada tupla: (texto, cor, negrito, largura_coluna)
        dados_cols = [
            (f"#{produto['id']:02d}",                     "#555555",  False, COLUNAS_TABELA[0][1]),
            (_truncar(produto["nome"], _MAX_CHARS[1]),    "#1f6aa5",  False, COLUNAS_TABELA[1][1]),
            (str(produto["quantidade"]),                  "#1a1a1a",  False, COLUNAS_TABELA[2][1]),
            (formatar_moeda(produto["preco"]),            "#1a1a1a",  False, COLUNAS_TABELA[3][1]),
            (formatar_moeda(total_valor),                 "#1a1a1a",  False, COLUNAS_TABELA[4][1]),
            (txt_status,                                  cor_status, True,  COLUNAS_TABELA[5][1]),
        ]

        widgets_linha = []

        for col, (texto, cor, negrito, largura) in enumerate(dados_cols):
            lbl = ctk.CTkLabel(
                self.scroll_frame,
                text=texto,
                font=ctk.CTkFont(size=13, weight="bold" if negrito else "normal"),
                text_color=cor,
                anchor="w",
                width=largura,
                cursor="hand2",
            )
            lbl.grid(row=linha, column=col, padx=(8, 0), pady=6, sticky="w")
            widgets_linha.append(lbl)
            lbl.bind("<Button-1>",
                     lambda e, pid=produto["id"]: self._abrir_detalhe(pid))

        # Efeito hover: sublinha o nome ao passar o mouse
        nome_lbl = widgets_linha[1]
        fonte_normal = ctk.CTkFont(size=13, underline=False)
        fonte_hover  = ctk.CTkFont(size=13, underline=True)
        nome_lbl.bind("<Enter>", lambda e: nome_lbl.configure(font=fonte_hover))
        nome_lbl.bind("<Leave>", lambda e: nome_lbl.configure(font=fonte_normal))

        # Botões de ação (editar e excluir) — na coluna 6 com largura fixa
        frame_acoes = ctk.CTkFrame(
            self.scroll_frame, fg_color="transparent",
            width=COLUNAS_TABELA[6][1])
        frame_acoes.grid(row=linha, column=6, padx=(8, 0), pady=4, sticky="w")

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
    def _abrir_detalhe(self, produto_id: int):
        """Navega para a tela de detalhe do produto."""
        from views.produtos_view import ProdutosView

        def voltar():
            self.controller.mostrar_tela(ProdutosView)

        self.controller.mostrar_tela(
            ProdutoDetalhe,
            produto_id=produto_id,
            on_voltar=voltar,
        )

    def _abrir_formulario(self, produto_id: int = None):
        """Navega para o formulário de cadastro (novo) ou edição dentro da janela principal."""
        from views.produtos_view import ProdutosView

        def voltar():
            self.controller.mostrar_tela(ProdutosView)

        self.controller.mostrar_tela(
            ProdutoForm,
            produto_id=produto_id,
            on_voltar=voltar,
        )

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

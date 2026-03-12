"""
carrinho_view.py - Tela do Carrinho de Compras (Etapa 4).
Painel esquerdo: Produtos Disponíveis + Itens no Carrinho.
Painel direito: Resumo do Pedido (implementado na Etapa 4 — Fase 2).
"""

import logging
import customtkinter as ctk
from tkinter import messagebox

from controllers.produto_controller import obter_lista
from utils import formatar_moeda

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Colunas das tabelas: (rótulo, largura_px)
# ------------------------------------------------------------------
COLS_DISP = [("ID", 44), ("Produto", 190), ("Qtd.", 82), ("Preço", 84), ("Ações", 75)]
COLS_CARR = [("ID", 44), ("Produto", 175), ("Qtd.", 65), ("Preço", 94), ("Ações", 60)]

# Cores dos botões de filtro: [inativo_fg, ativo_fg, inativo_hover, ativo_hover]
_FILTRO_CORES = {
    "todos":         ["#3a9adf", "#1f6aa5", "#2a7abf", "#104a85"],
    "promocao":      ["#f5a623", "#d97706", "#d48810", "#b06004"],
    "pouco_estoque": ["#f07070", "#e53935", "#cc3535", "#b01818"],
}


class CarrinhoView(ctk.CTkFrame):
    """
    Tela do Carrinho de Compras.
    Layout dividido em 2 colunas:
    - Esquerda (weight=5): Produtos Disponíveis + Itens no Carrinho
    - Direita  (weight=4): Resumo do Pedido (Fase 2)
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        # Filtro ativo: "todos" | "promocao" | "pouco_estoque"
        self._filtro: str = "todos"

        # Carrinho em memória: lista de dicts (produto_id, nome, quantidade, preco_unitario, subtotal)
        self._carrinho: list[dict] = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=0)  # título
        self.grid_rowconfigure(1, weight=1)  # conteúdo expande

        self._construir_ui()

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------
    def _construir_ui(self):
        # Título da tela
        frame_titulo = ctk.CTkFrame(self, fg_color="transparent")
        frame_titulo.grid(row=0, column=0, columnspan=2,
                          padx=20, pady=(18, 6), sticky="ew")
        ctk.CTkLabel(
            frame_titulo, text="🛒  Carrinho",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1f6aa5", anchor="w",
        ).grid(row=0, column=0, sticky="w")

        # Coluna esquerda
        esq = ctk.CTkFrame(self, fg_color="transparent")
        esq.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="nsew")
        esq.grid_columnconfigure(0, weight=1)
        esq.grid_rowconfigure(0, weight=3)
        esq.grid_rowconfigure(1, weight=2)

        self._criar_card_produtos(esq)
        self._criar_card_carrinho(esq)

        # Coluna direita — placeholder (Fase 2)
        self._criar_painel_direito()

    # ------------------------------------------------------------------
    # Painel direito — placeholder para a Fase 2
    # ------------------------------------------------------------------
    def _criar_painel_direito(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        card.grid(row=1, column=1, padx=(8, 16), pady=(0, 16), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)
        ctk.CTkLabel(
            card,
            text="📋\n\nResumo do Pedido\n\n(em desenvolvimento...)",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc",
            justify="center",
        ).grid(row=0, column=0)

    # ------------------------------------------------------------------
    # Card: Produtos Disponíveis
    # ------------------------------------------------------------------
    def _criar_card_produtos(self, pai):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=0, pady=(0, 8), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(4, weight=1)  # scroll expande

        # Título
        ctk.CTkLabel(
            card, text="Produtos Disponíveis",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        ).grid(row=0, column=0, padx=14, pady=(12, 8), sticky="w")

        # Barra de busca
        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        barra.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            barra,
            placeholder_text="Digite para buscar produtos...",
            height=36, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=13),
        )
        self.entry_busca.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.entry_busca.bind("<KeyRelease>", lambda e: self._carregar_produtos())

        ctk.CTkButton(
            barra, text="🔍 Buscar", width=92, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._carregar_produtos,
        ).grid(row=0, column=1)

        # Botões de filtro
        fb = ctk.CTkFrame(card, fg_color="transparent")
        fb.grid(row=2, column=0, padx=14, pady=(0, 8), sticky="w")

        self.btn_todos = ctk.CTkButton(
            fb, text="Todos", width=82, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_FILTRO_CORES["todos"][1],
            hover_color=_FILTRO_CORES["todos"][3],
            command=lambda: self._aplicar_filtro("todos"),
        )
        self.btn_todos.grid(row=0, column=0, padx=(0, 6))

        self.btn_promocao = ctk.CTkButton(
            fb, text="Promoção", width=90, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_FILTRO_CORES["promocao"][0],
            hover_color=_FILTRO_CORES["promocao"][2],
            command=lambda: self._aplicar_filtro("promocao"),
        )
        self.btn_promocao.grid(row=0, column=1, padx=(0, 6))

        self.btn_pouco_est = ctk.CTkButton(
            fb, text="Pouco Estoque", width=118, height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=_FILTRO_CORES["pouco_estoque"][0],
            hover_color=_FILTRO_CORES["pouco_estoque"][2],
            command=lambda: self._aplicar_filtro("pouco_estoque"),
        )
        self.btn_pouco_est.grid(row=0, column=2)

        # Cabeçalho fixo da tabela
        self._criar_cabecalho_tabela(card, COLS_DISP, row=3)

        # Área de rolagem dos produtos
        self.scroll_produtos = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0,
        )
        self.scroll_produtos.grid(row=4, column=0, padx=8, pady=(0, 8), sticky="nsew")
        for i, (_, larg) in enumerate(COLS_DISP):
            self.scroll_produtos.grid_columnconfigure(i, minsize=larg, weight=0)
        self.scroll_produtos.grid_columnconfigure(len(COLS_DISP), weight=1)

        self._carregar_produtos()

    # ------------------------------------------------------------------
    # Card: Itens no Carrinho
    # ------------------------------------------------------------------
    def _criar_card_carrinho(self, pai):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        self.lbl_titulo_carr = ctk.CTkLabel(
            card, text="Itens no Carrinho (0)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1a1a1a", anchor="w",
        )
        self.lbl_titulo_carr.grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        # Cabeçalho fixo da tabela
        self._criar_cabecalho_tabela(card, COLS_CARR, row=1)

        # Área de rolagem do carrinho
        self.scroll_carrinho = ctk.CTkScrollableFrame(
            card, fg_color="white", corner_radius=0,
        )
        self.scroll_carrinho.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")
        for i, (_, larg) in enumerate(COLS_CARR):
            self.scroll_carrinho.grid_columnconfigure(i, minsize=larg, weight=0)
        self.scroll_carrinho.grid_columnconfigure(len(COLS_CARR), weight=1)

        self._recarregar_carrinho()

    # ------------------------------------------------------------------
    # Utilitário: cabeçalho de tabela fixo
    # ------------------------------------------------------------------
    def _criar_cabecalho_tabela(self, pai, colunas: list, row: int):
        cab = ctk.CTkFrame(pai, fg_color="#f0f0f0", corner_radius=0, height=28)
        cab.grid(row=row, column=0, padx=8, sticky="ew")
        cab.grid_propagate(False)
        for i, (rot, larg) in enumerate(colunas):
            cab.grid_columnconfigure(i, minsize=larg, weight=0)
            ctk.CTkLabel(
                cab, text=rot,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#555555", width=larg, anchor="w",
            ).grid(row=0, column=i, padx=(6, 0), pady=2, sticky="w")
        cab.grid_columnconfigure(len(colunas), weight=1)

    # ------------------------------------------------------------------
    # Filtros e carregamento de produtos
    # ------------------------------------------------------------------
    def _aplicar_filtro(self, filtro: str):
        """Altera o filtro ativo, limpa a busca e recarrega a lista."""
        self._filtro = filtro
        self.entry_busca.delete(0, "end")
        self._carregar_produtos()

    def _carregar_produtos(self):
        """Atualiza a tabela de produtos conforme busca e filtro ativo."""
        busca  = self.entry_busca.get().strip()
        todos  = obter_lista(busca)

        # Contagens para os botões de filtro
        n_promo = sum(1 for p in todos if p.get("status_estoque") == "estoque_alto")
        n_pouco = sum(
            1 for p in todos
            if p.get("status_estoque") in ("estoque_baixo", "sem_estoque")
        )

        self.btn_todos.configure(text=f"Todos ({len(todos)})")
        self.btn_promocao.configure(text=f"Promoção ({n_promo})")
        self.btn_pouco_est.configure(text=f"Pouco Estoque ({n_pouco})")

        # Destaque visual do filtro ativo
        self._atualizar_cores_filtro()

        # Aplica o filtro selecionado
        if self._filtro == "promocao":
            produtos = [p for p in todos if p.get("status_estoque") == "estoque_alto"]
        elif self._filtro == "pouco_estoque":
            produtos = [
                p for p in todos
                if p.get("status_estoque") in ("estoque_baixo", "sem_estoque")
            ]
        else:
            produtos = todos

        # Limpa e preenche o scroll de produtos
        for w in self.scroll_produtos.winfo_children():
            w.destroy()

        if not produtos:
            ctk.CTkLabel(
                self.scroll_produtos,
                text="Nenhum produto encontrado.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=0, column=0, columnspan=len(COLS_DISP) + 1, pady=14)
            return

        for linha, p in enumerate(produtos):
            dados_cols = [
                (f"#{p['id']:02d}",          "#555555"),
                (p["nome"],                    "#1f6aa5"),
                (str(p["quantidade"]),         "#1a1a1a"),
                (formatar_moeda(p["preco"]),   "#1a1a1a"),
            ]
            for col, (texto, cor) in enumerate(dados_cols):
                ctk.CTkLabel(
                    self.scroll_produtos, text=texto,
                    font=ctk.CTkFont(size=12), text_color=cor,
                    width=COLS_DISP[col][1], anchor="w",
                ).grid(row=linha, column=col, padx=(6, 0), pady=2, sticky="w")

            ctk.CTkButton(
                self.scroll_produtos, text="+ Adic.", width=68, height=24,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda prod=p: self._adicionar_ao_carrinho(prod),
            ).grid(row=linha, column=4, padx=(4, 0), pady=2, sticky="w")

    def _atualizar_cores_filtro(self):
        """Aplica cor de destaque (escura) ao botão do filtro atualmente ativo."""
        mapa = {
            "todos":         self.btn_todos,
            "promocao":      self.btn_promocao,
            "pouco_estoque": self.btn_pouco_est,
        }
        for chave, btn in mapa.items():
            ativo      = (chave == self._filtro)
            idx_fg    = 1 if ativo else 0
            idx_hover = 3 if ativo else 2
            btn.configure(
                fg_color=_FILTRO_CORES[chave][idx_fg],
                hover_color=_FILTRO_CORES[chave][idx_hover],
            )

    # ------------------------------------------------------------------
    # Carrinho: adicionar, editar, remover
    # ------------------------------------------------------------------
    def _adicionar_ao_carrinho(self, produto: dict):
        """Adiciona produto ao carrinho; incrementa quantidade se já estiver."""
        for item in self._carrinho:
            if item["produto_id"] == produto["id"]:
                item["quantidade"] += 1
                item["subtotal"] = round(item["quantidade"] * item["preco_unitario"], 2)
                self._recarregar_carrinho()
                return

        self._carrinho.append({
            "produto_id":     produto["id"],
            "nome":           produto["nome"],
            "quantidade":     1,
            "preco_unitario": produto["preco"],
            "subtotal":       produto["preco"],
        })
        self._recarregar_carrinho()

    def _recarregar_carrinho(self):
        """Atualiza a tabela do carrinho e aciona a atualização do resumo."""
        for w in self.scroll_carrinho.winfo_children():
            w.destroy()

        n = len(self._carrinho)
        self.lbl_titulo_carr.configure(text=f"Itens no Carrinho ({n})")

        if not self._carrinho:
            ctk.CTkLabel(
                self.scroll_carrinho, text="Nenhum item no carrinho.",
                font=ctk.CTkFont(size=12), text_color="#888888",
            ).grid(row=0, column=0, columnspan=len(COLS_CARR) + 1, pady=14)
            self._atualizar_resumo()
            return

        for linha, item in enumerate(self._carrinho):
            dados_cols = [
                (f"#{item['produto_id']:02d}", "#555555"),
                (item["nome"],                  "#1f6aa5"),
                (str(item["quantidade"]),        "#1a1a1a"),
                (formatar_moeda(item["subtotal"]), "#1a1a1a"),
            ]
            for col, (texto, cor) in enumerate(dados_cols):
                ctk.CTkLabel(
                    self.scroll_carrinho, text=texto,
                    font=ctk.CTkFont(size=12), text_color=cor,
                    width=COLS_CARR[col][1], anchor="w",
                ).grid(row=linha, column=col, padx=(6, 0), pady=2, sticky="w")

            # Botões por linha: Editar e Excluir
            fa = ctk.CTkFrame(self.scroll_carrinho, fg_color="transparent")
            fa.grid(row=linha, column=4, padx=(2, 0), pady=2, sticky="w")

            ctk.CTkButton(
                fa, text="✏️", width=26, height=24,
                fg_color="transparent", hover_color="#e0e0e0",
                font=ctk.CTkFont(size=12),
                command=lambda i=linha: self._editar_item(i),
            ).grid(row=0, column=0)
            ctk.CTkButton(
                fa, text="🗑️", width=26, height=24,
                fg_color="transparent", hover_color="#fde8e8",
                font=ctk.CTkFont(size=12),
                command=lambda i=linha: self._remover_item(i),
            ).grid(row=0, column=1)

        self._atualizar_resumo()

    def _editar_item(self, indice: int):
        """Abre popup modal para editar quantidade e preço de um item do carrinho."""
        _EditarItemForm(self, self._carrinho[indice], self._recarregar_carrinho)

    def _remover_item(self, indice: int):
        """Remove um item do carrinho e atualiza a tabela."""
        self._carrinho.pop(indice)
        self._recarregar_carrinho()

    # ------------------------------------------------------------------
    # Resumo do Pedido — stub (completo na Fase 2)
    # ------------------------------------------------------------------
    def _atualizar_resumo(self):
        """
        Atualiza o painel de Resumo do Pedido com os totais do carrinho.
        Implementação completa na Fase 2 da Etapa 4.
        """
        pass

    def _limpar_carrinho(self):
        """Esvazia todo o carrinho."""
        self._carrinho.clear()
        self._recarregar_carrinho()


# ------------------------------------------------------------------
# Popup: editar item do carrinho
# ------------------------------------------------------------------

class _EditarItemForm(ctk.CTkToplevel):
    """Janela modal para editar quantidade e preço unitário de um item no carrinho."""

    def __init__(self, parent, item: dict, on_salvar):
        super().__init__(parent)
        self._item      = item
        self._on_salvar = on_salvar

        self.title("Editar Item do Carrinho")
        self.geometry("330x205")
        self.resizable(False, False)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        frame.grid_columnconfigure((0, 1), weight=1)

        # Quantidade
        ctk.CTkLabel(
            frame, text="Quantidade *",
            font=ctk.CTkFont(size=13), text_color="#333333",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_qtd = ctk.CTkEntry(
            frame, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
        )
        self.entry_qtd.insert(0, str(item["quantidade"]))
        self.entry_qtd.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        # Preço unitário
        ctk.CTkLabel(
            frame, text="Preço Unit. (R$) *",
            font=ctk.CTkFont(size=13), text_color="#333333",
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.entry_preco = ctk.CTkEntry(
            frame, height=36, fg_color="white",
            border_color="#cccccc", font=ctk.CTkFont(size=13),
        )
        self.entry_preco.insert(0, f"{item['preco_unitario']:.2f}".replace(".", ","))
        self.entry_preco.grid(row=1, column=1, sticky="ew")

        # Botões
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="e")

        ctk.CTkButton(
            btns, text="Cancelar", width=100, height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            btns, text="Salvar", width=100, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1)

        self.after(100, self.lift)

    def _salvar(self):
        # Valida quantidade
        try:
            qtd = int(self.entry_qtd.get().strip())
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Erro", "Informe uma quantidade válida maior que zero.", parent=self
            )
            return

        # Valida preço
        preco_str = self.entry_preco.get().strip().replace(",", ".")
        try:
            preco = float(preco_str)
            if preco <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Erro", "Informe um preço válido maior que zero.", parent=self
            )
            return

        self._item["quantidade"]     = qtd
        self._item["preco_unitario"] = preco
        self._item["subtotal"]       = round(qtd * preco, 2)

        self._on_salvar()
        self.destroy()

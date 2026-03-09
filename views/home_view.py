"""
home_view.py - Tela inicial (Dashboard) do Sistema Caixa.
Exibe o logo, nome da empresa e os cards de visão geral (Crediário, Produtos, Vendas).
"""

import os
import customtkinter as ctk
from PIL import Image
from database import conectar

# Tamanho fixo do logo na interface
LOGO_SIZE = 110


class HomeView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)
        self.controller = controller

        # Layout: row 0=cabeçalho, row 1=cards, row 2=espaço flexível, row 3=rodapé
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # espaço que empurra o rodapé para baixo

        self._criar_cabecalho()
        self._criar_visao_geral()
        self._criar_rodape()

    # ------------------------------------------------------------------
    # Cabeçalho: logo + nome da empresa + descrição
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        """Seção superior com logo da empresa, nome e descrição."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=60, pady=(50, 10), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        # --- Logo da empresa ---
        logo_img = self._carregar_logo()
        if logo_img:
            # Exibe a imagem sem fundo
            ctk.CTkLabel(
                frame,
                image=logo_img,
                text="",
                fg_color="transparent",
            ).grid(row=0, column=0, rowspan=2, padx=(0, 30))
        else:
            # Fallback: placeholder verde caso a imagem não exista
            logo_frame = ctk.CTkFrame(
                frame,
                width=LOGO_SIZE,
                height=LOGO_SIZE,
                fg_color="#4CAF50",
                corner_radius=12,
            )
            logo_frame.grid(row=0, column=0, rowspan=2, padx=(0, 30))
            logo_frame.grid_propagate(False)
            ctk.CTkLabel(
                logo_frame,
                text="Logo da\nempresa",
                text_color="white",
                font=ctk.CTkFont(size=13),
            ).place(relx=0.5, rely=0.5, anchor="center")

        # Nome da empresa (lido do banco de dados)
        nome_empresa = self._obter_config("nome_empresa") or "Nome da Empresa"
        ctk.CTkLabel(
            frame,
            text=nome_empresa,
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#1a1a1a",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            frame,
            text="Gerencie seus produtos, clientes, vendas e débitos de forma simples e eficiente.",
            font=ctk.CTkFont(size=14),
            text_color="#555555",
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

    # ------------------------------------------------------------------
    # Visão Geral: cards de resumo
    # ------------------------------------------------------------------
    def _criar_visao_geral(self):
        """Seção com container cinza e 3 cards: Crediário, Produtos e Vendas."""
        container = ctk.CTkFrame(self, fg_color="#cccccc", corner_radius=14)
        # sticky="ew" — container não cresce verticalmente
        container.grid(row=1, column=0, padx=60, pady=20, sticky="ew")
        container.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            container,
            text="Visão Geral",
            font=ctk.CTkFont(size=15),
            text_color="#444444",
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(18, 8), sticky="w")

        # Coleta os dados resumidos do banco de dados
        clientes_atraso, produtos_baixo, vendas_hoje = self._obter_resumo()

        # Definição dos cards: (icone, titulo, numero, descricao, cor_descricao)
        cards = [
            ("👤", "Crediário", str(clientes_atraso), "Clientes em atraso!",       "#d97706"),
            ("📦", "Produtos",  str(produtos_baixo),  "Produtos com\nbaixo estoque!","#d97706"),
            ("🛒", "Vendas",    str(vendas_hoje),     "Total de vendas hoje!",      "#1a1a1a"),
        ]

        for coluna, (icone, titulo, numero, descricao, cor_desc) in enumerate(cards):
            self._criar_card(container, icone, titulo, numero, descricao, cor_desc, coluna)

    def _criar_card(self, parent, icone, titulo, numero, descricao, cor_descricao, coluna):
        """Cria um card individual na seção Visão Geral."""
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=14)
        # sticky="ew" — card não cresce verticalmente, mantém tamanho fixo pelo conteúdo
        card.grid(row=1, column=coluna, padx=15, pady=(0, 20), sticky="ew", ipadx=10, ipady=10)
        card.grid_columnconfigure(0, weight=1)

        # Título com ícone
        ctk.CTkLabel(
            card,
            text=f"{icone}  {titulo}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, padx=20, pady=(22, 8))

        # Número em destaque
        ctk.CTkLabel(
            card,
            text=numero,
            font=ctk.CTkFont(size=46, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=1, column=0, padx=20, pady=4)

        # Descrição / alerta
        ctk.CTkLabel(
            card,
            text=descricao,
            font=ctk.CTkFont(size=13),
            text_color=cor_descricao,
        ).grid(row=2, column=0, padx=20, pady=(4, 22))

    # ------------------------------------------------------------------
    # Rodapé
    # ------------------------------------------------------------------
    def _criar_rodape(self):
        """Rodapé com crédito do desenvolvedor — fixo na parte inferior."""
        ctk.CTkLabel(
            self,
            text="Sistema desenvolvido por: Caléo Souza Santos",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).grid(row=3, column=0, pady=(8, 18))

    # ------------------------------------------------------------------
    # Carregamento do logo
    # ------------------------------------------------------------------
    def _carregar_logo(self) -> ctk.CTkImage | None:
        """
        Carrega a imagem de logo da pasta imagens/outros/.
        Redimensiona proporcionalmente para caber em LOGO_SIZE x LOGO_SIZE.
        Preserva transparência (PNG sem fundo).
        """
        caminho = os.path.join(
            os.path.dirname(__file__), "..", "imagens", "outros", "souza.png"
        )
        caminho = os.path.normpath(caminho)
        if not os.path.exists(caminho):
            return None
        try:
            img = Image.open(caminho).convert("RGBA")
            # Redimensiona mantendo proporção (thumbnail não distorce)
            img.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
            return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Consultas ao banco de dados
    # ------------------------------------------------------------------
    def _obter_config(self, chave):
        """Retorna o valor de uma configuração do banco de dados."""
        try:
            conn = conectar()
            row = conn.execute(
                "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
            ).fetchone()
            conn.close()
            return row["valor"] if row else None
        except Exception:
            return None

    def _obter_resumo(self):
        """Retorna (clientes_em_atraso, produtos_baixo_estoque, vendas_hoje)."""
        try:
            conn = conectar()

            clientes_atraso = conn.execute(
                "SELECT COUNT(*) FROM clientes WHERE tem_crediario = 1 AND debito_atual > 0 AND ativo = 1"
            ).fetchone()[0]

            produtos_baixo = conn.execute(
                "SELECT COUNT(*) FROM produtos WHERE quantidade <= estoque_minimo AND ativo = 1"
            ).fetchone()[0]

            vendas_hoje = conn.execute(
                """SELECT COUNT(*) FROM vendas
                   WHERE DATE(criado_em) = DATE('now','localtime')
                   AND status = 'concluida'"""
            ).fetchone()[0]

            conn.close()
            return clientes_atraso, produtos_baixo, vendas_hoje
        except Exception:
            return 0, 0, 0

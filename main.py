"""
main.py - Ponto de entrada do Sistema Caixa.
Inicializa a janela principal, sidebar de navegação e gerencia a troca de telas.
"""

import customtkinter as ctk
from database import criar_tabelas
from views.home_view import HomeView
from views.produtos_view import ProdutosView


# Configuração global do tema
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Inicializa o banco de dados na primeira execução
        criar_tabelas()

        self._configurar_janela()
        self._criar_layout()

        # Exibe a tela inicial (dashboard)
        self.tela_atual = None
        self.btn_ativo = None
        self.mostrar_tela(HomeView)

    # ------------------------------------------------------------------
    # Configurar janela
    # ------------------------------------------------------------------
    def _configurar_janela(self):
        """Define o título, ícone e tamanho da janela conforme a resolução."""
        self.title("Sistema Caixa - CSYSTEN")

        # Detecta a resolução do monitor e ajusta a janela
        largura_tela = self.winfo_screenwidth()

        if largura_tela >= 1920:
            self.geometry("1920x1080")
            ctk.set_widget_scaling(1.25)
        else:
            # HD (1280x720) ou semelhante
            self.geometry("1280x720")
            ctk.set_widget_scaling(1.0)

        self.minsize(1024, 600)

        # Tenta aplicar o ícone da janela
        try:
            self.iconbitmap("imagens/outros/CS_logo.ico")
        except Exception:
            pass  # Ícone ainda não disponível

    # ------------------------------------------------------------------
    # Layout principal: sidebar + área de conteúdo
    # ------------------------------------------------------------------
    def _criar_layout(self):
        """Cria a estrutura principal: sidebar esquerda e área de conteúdo à direita."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._criar_sidebar()

        # Área de conteúdo (ocupa o restante da tela)
        self.area_conteudo = ctk.CTkFrame(self, fg_color="#e8e8e8", corner_radius=0)
        self.area_conteudo.grid(row=0, column=1, sticky="nsew")
        self.area_conteudo.grid_columnconfigure(0, weight=1)
        self.area_conteudo.grid_rowconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Sidebar de navegação
    # ------------------------------------------------------------------
    def _criar_sidebar(self):
        """Cria a sidebar com título e botões de navegação."""
        self.sidebar = ctk.CTkFrame(self, width=215, corner_radius=0, fg_color="#d4d4d4")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(7, weight=1)  # empurra botões para cima

        # --- Título ---
        # "Menu" clicável → volta para o Home
        lbl_menu = ctk.CTkLabel(
            self.sidebar,
            text="Menu",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1a1a1a",
            cursor="hand2",
        )
        lbl_menu.grid(row=0, column=0, padx=25, pady=(35, 0), sticky="w")
        lbl_menu.bind("<Button-1>", lambda e: self.mostrar_tela(HomeView))
        lbl_menu.bind("<Enter>", lambda e: lbl_menu.configure(text_color="#1f6aa5"))
        lbl_menu.bind("<Leave>", lambda e: lbl_menu.configure(text_color="#1a1a1a"))

        ctk.CTkLabel(
            self.sidebar,
            text="Sistema Caixa",
            font=ctk.CTkFont(size=13),
            text_color="#555555",
        ).grid(row=1, column=0, padx=25, pady=(0, 25), sticky="w")

        # --- Botões de navegação ---
        # Formato: (texto, ícone unicode, classe da view)
        self.nav_botoes = [
            ("Carrinho",      "🛒", None),          # CarrinhoView (Etapa 4)
            ("Produtos",      "📦", ProdutosView),  # ✅ Etapa 2
            ("Clientes",      "👤", None),          # ClientesView (Etapa 3)
            ("Relatórios",    "📊", None),          # RelatoriosView (Etapa 5)
            ("Configurações", "⚙️", None),          # ConfiguracoesView (Etapa 6)
        ]

        self.btns_nav = {}
        for i, (nome, icone, view_cls) in enumerate(self.nav_botoes):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icone}  {nome}",
                anchor="w",
                width=175,
                height=38,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda v=view_cls, b=nome: self._navegar(v, b),
            )
            btn.grid(row=i + 2, column=0, padx=20, pady=6)
            self.btns_nav[nome] = btn

    def _navegar(self, view_cls, nome_btn):
        """Trata o clique nos botões da sidebar."""
        if view_cls is None:
            # View ainda não implementada
            return
        self.mostrar_tela(view_cls)

    # ------------------------------------------------------------------
    # Troca de telas
    # ------------------------------------------------------------------
    def mostrar_tela(self, TelaCls, **kwargs):
        """Destroi a tela atual e carrega a nova view na área de conteúdo."""
        if self.tela_atual is not None:
            self.tela_atual.destroy()

        self.tela_atual = TelaCls(self.area_conteudo, self, **kwargs)
        self.tela_atual.grid(row=0, column=0, sticky="nsew")


# ------------------------------------------------------------------
# Inicialização
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()

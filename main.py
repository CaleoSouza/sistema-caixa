""" 
main.py - Ponto de entrada do Sistema Caixa.
Inicializa a janela principal, sidebar de navegação e gerencia a troca de telas.
"""

import logging
import customtkinter as ctk
from database import criar_tabelas
from views.home_view import HomeView
from views.produtos_view import ProdutosView
from views.clientes_view import ClientesView
from views.carrinho_view import CarrinhoView
from views.despesas_view import DespesasView
from views.relatorios_view import RelatoriosView


# ------------------------------------------------------------------
# Configuração do sistema de logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("SistemaCaixa")


# ------------------------------------------------------------------
# Handler que envia logs para o painel visual do app
# ------------------------------------------------------------------
class _PainelLogHandler(logging.Handler):
    """Handler de logging que empurra mensagens para o CTkTextbox do painel."""

    def __init__(self, textbox: ctk.CTkTextbox):
        super().__init__()
        self._textbox = textbox
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))

    def emit(self, record):
        msg = self.format(record) + "\n"
        # Cores por nível
        cor = {"DEBUG": "#888888", "INFO": "#1a1a1a", "WARNING": "#d97706",
               "ERROR": "#e53935", "CRITICAL": "#b71c1c"}.get(record.levelname, "#1a1a1a")
        try:
            self._textbox.configure(state="normal")
            self._textbox.insert("end", msg)
            self._textbox.tag_add(record.levelname, f"end-{len(msg)+1}c", "end-1c")
            self._textbox.tag_config(record.levelname, foreground=cor)
            self._textbox.see("end")
            self._textbox.configure(state="disabled")
        except Exception:
            pass  # janela pode estar fechada


# ------------------------------------------------------------------
# Janela de log (temporária para desenvolvimento)
# ------------------------------------------------------------------
class PainelLog(ctk.CTkToplevel):
    """Janela flutuante com os logs do sistema em tempo real. Ctrl+L para abrir/fechar."""

    def __init__(self, master):
        super().__init__(master)
        self.title("🪵 Log do Sistema")
        self.geometry("800x400")
        self.resizable(True, True)
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Área de texto com scroll
        self._txt = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#1e1e1e",
            text_color="#d4d4d4",
            corner_radius=0,
            state="disabled",
        )
        self._txt.grid(row=0, column=0, sticky="nsew")

        # Barra inferior: botão limpar
        barra = ctk.CTkFrame(self, fg_color="#2d2d2d", height=36, corner_radius=0)
        barra.grid(row=1, column=0, sticky="ew")
        ctk.CTkButton(
            barra, text="🗑 Limpar", width=90, height=28,
            fg_color="#444", hover_color="#666",
            font=ctk.CTkFont(size=12),
            command=self._limpar,
        ).pack(side="right", padx=8, pady=4)

        ctk.CTkLabel(
            barra, text="Ctrl+L para fechar",
            font=ctk.CTkFont(size=11), text_color="#888888",
        ).pack(side="left", padx=10)

        # Registra o handler de logging nesta janela
        self._handler = _PainelLogHandler(self._txt)
        logging.getLogger().addHandler(self._handler)
        log.info("Painel de log aberto.")

        # Remove o handler ao fechar
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _limpar(self):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")

    def _fechar(self):
        logging.getLogger().removeHandler(self._handler)
        self.destroy()



# Configuração global do tema
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Inicializa o banco de dados na primeira execução
        criar_tabelas()
        log.info("Banco de dados inicializado.")

        self._painel_log = None  # referência ao painel de log (Ctrl+L)

        self._configurar_janela()
        self._criar_layout()

        # Atalho global: Ctrl+L abre/fecha o painel de log
        self.bind_all("<Control-l>", lambda e: self._toggle_painel_log())

        # Exibe a tela inicial (dashboard)
        self.tela_atual = None
        self.btn_ativo = None
        self.mostrar_tela(HomeView)
        log.info("Aplicação iniciada.")

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
        self.sidebar.grid_rowconfigure(8, weight=1)  # empurra botões para cima

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
        lbl_menu.bind("<Button-1>", lambda e: (self._set_btn_ativo(None), self.mostrar_tela(HomeView)))
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
            ("Carrinho",      "🛒", CarrinhoView),   # ✅ Etapa 4
            ("Produtos",      "📦", ProdutosView),   # ✅ Etapa 2
            ("Clientes",      "👤", ClientesView),   # ✅ Etapa 3
            ("Despesas",      "💸", DespesasView),   # ✅ Etapa 5
            ("Relatórios",    "📊", RelatoriosView), # ✅ Etapa 6
            ("Configurações", "⚙️", None),           # ConfiguracoesView (Etapa 7)
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
        """Trata o clique nos botões da sidebar e atualiza o destaque do botão ativo."""
        if view_cls is None:
            # View ainda não implementada
            return
        self._set_btn_ativo(nome_btn)
        self.mostrar_tela(view_cls)

    def _set_btn_ativo(self, nome_btn: str | None):
        """
        Atualiza o destaque visual dos botões da sidebar.
        - nome_btn: nome do botão a destacar, ou None para limpar todos.
        """
        COR_ATIVO  = ("#145a8a", "#0d4272")   # azul escuro — botão selecionado
        COR_NORMAL = ("#3B8ED0", "#1F6AA5")   # azul padrão do tema

        # Remove destaque do botão anterior
        if self.btn_ativo and self.btn_ativo in self.btns_nav:
            self.btns_nav[self.btn_ativo].configure(fg_color=COR_NORMAL)

        self.btn_ativo = nome_btn

        # Aplica destaque no novo botão ativo
        if nome_btn and nome_btn in self.btns_nav:
            self.btns_nav[nome_btn].configure(fg_color=COR_ATIVO)

    # ------------------------------------------------------------------
    # Troca de telas
    # ------------------------------------------------------------------
    def mostrar_tela(self, TelaCls, **kwargs):
        """Destroi a tela atual e carrega a nova view na área de conteúdo."""
        log.debug(f"Navegando para: {TelaCls.__name__}")
        if self.tela_atual is not None:
            self.tela_atual.destroy()

        self.tela_atual = TelaCls(self.area_conteudo, self, **kwargs)
        self.tela_atual.grid(row=0, column=0, sticky="nsew")


    def _toggle_painel_log(self):
        """Abre ou fecha o painel de log com Ctrl+L."""
        if self._painel_log is None or not self._painel_log.winfo_exists():
            self._painel_log = PainelLog(self)
        else:
            self._painel_log._fechar()
            self._painel_log = None


# ------------------------------------------------------------------
# Inicialização
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()

"""
despesa_auto_form.py - Popup modal para adicionar ou editar uma despesa automática (fixa mensal).
"""

import customtkinter as ctk
from tkinter import messagebox

from controllers.despesa_controller import salvar_auto, FORMAS_PAGAMENTO


class DespesaAutoForm(ctk.CTkToplevel):
    """
    Janela modal para cadastro/edição de despesa automática.
    - auto: dict com dados para pré-preencher (modo edição) ou None (modo novo)
    - on_salvar: callback chamado após salvar com sucesso
    """

    def __init__(self, parent, auto: dict | None, on_salvar):
        super().__init__(parent)
        self._auto      = auto
        self._on_salvar = on_salvar

        titulo = "Editar Despesa Automática" if auto else "Nova Despesa Automática"
        self.title(titulo)
        self.geometry("420x460")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self.grid_columnconfigure(0, weight=1)
        self._construir_ui()

        if auto:
            self._preencher(auto)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def _construir_ui(self):
        pad = {"padx": 20, "pady": (10, 0)}

        # Título interno
        ctk.CTkLabel(
            self,
            text="Editar Despesa Automática" if self._auto else "Nova Despesa",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#1f6aa5",
        ).grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        # Descrição
        ctk.CTkLabel(self, text="Descrição *", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=1, column=0, **pad, sticky="w")
        self.entry_descricao = ctk.CTkEntry(
            self, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="Ex: Aluguel, Fornecedor...",
        )
        self.entry_descricao.grid(row=2, column=0, padx=20, pady=(4, 0), sticky="ew")

        # Linha: Dia do mês + Responsável
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="ew")
        linha.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(linha, text="Data se repete todo mês", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(linha, text="Responsável", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=1, sticky="w")

        # Frame para "Dia" com label embutido
        frame_dia = ctk.CTkFrame(linha, fg_color="white", border_color="#cccccc",
                                 border_width=2, corner_radius=6)
        frame_dia.grid(row=1, column=0, padx=(0, 8), sticky="ew")
        frame_dia.grid_columnconfigure(0, weight=1)

        self.entry_dia = ctk.CTkEntry(
            frame_dia, height=28, fg_color="white", border_width=0,
            font=ctk.CTkFont(size=12), placeholder_text="Dia (1-31)",
        )
        self.entry_dia.grid(row=0, column=0, padx=(6, 0), pady=2, sticky="ew")
        ctk.CTkLabel(
            frame_dia, text="todo mês", font=ctk.CTkFont(size=10),
            text_color="#999999",
        ).grid(row=0, column=1, padx=(0, 6), pady=2)

        self.entry_responsavel = ctk.CTkEntry(
            linha, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="Nome do responsável",
        )
        self.entry_responsavel.grid(row=1, column=1, sticky="ew")

        # Linha: Valor + Forma de Pagamento
        linha2 = ctk.CTkFrame(self, fg_color="transparent")
        linha2.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")
        linha2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(linha2, text="Valor (R$) *", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(linha2, text="Forma de Pagamento", font=ctk.CTkFont(size=12),
                     text_color="#555555").grid(row=0, column=1, sticky="w")

        self.entry_valor = ctk.CTkEntry(
            linha2, height=32, fg_color="white", border_color="#cccccc",
            font=ctk.CTkFont(size=12), placeholder_text="0,00",
        )
        self.entry_valor.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        self.opt_pagamento = ctk.CTkOptionMenu(
            linha2, values=FORMAS_PAGAMENTO, height=32,
            font=ctk.CTkFont(size=12),
        )
        self.opt_pagamento.set("Dinheiro")
        self.opt_pagamento.grid(row=1, column=1, sticky="ew")

        # Aviso informativo
        ctk.CTkLabel(
            self,
            text="ℹ️  Esta despesa será lançada automaticamente todo mês.",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        ).grid(row=5, column=0, padx=20, pady=(14, 0), sticky="w")

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=6, column=0, padx=20, pady=20, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="Cancelar", height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="💾  Salvar", height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._salvar,
        ).grid(row=0, column=1, sticky="ew")

    # ------------------------------------------------------------------
    # Preenche campos no modo edição
    # ------------------------------------------------------------------
    def _preencher(self, d: dict):
        self.entry_descricao.delete(0, "end")
        self.entry_descricao.insert(0, d.get("descricao", ""))

        self.entry_dia.delete(0, "end")
        self.entry_dia.insert(0, str(d.get("dia_mes", 1)))

        self.entry_responsavel.delete(0, "end")
        self.entry_responsavel.insert(0, d.get("responsavel", "") or "")

        self.entry_valor.delete(0, "end")
        self.entry_valor.insert(0, str(d.get("valor", "0")).replace(".", ","))

        forma = d.get("forma_pagamento", "Dinheiro")
        if forma in FORMAS_PAGAMENTO:
            self.opt_pagamento.set(forma)

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------
    def _salvar(self):
        dados = {
            "id":              self._auto["id"] if self._auto else None,
            "descricao":       self.entry_descricao.get(),
            "dia_mes":         self.entry_dia.get().strip(),
            "responsavel":     self.entry_responsavel.get(),
            "valor":           self.entry_valor.get(),
            "forma_pagamento": self.opt_pagamento.get(),
        }

        ok, resultado = salvar_auto(dados)
        if not ok:
            messagebox.showerror("Erro", resultado, parent=self)
            return

        self.destroy()
        self._on_salvar()

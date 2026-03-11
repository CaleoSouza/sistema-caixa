"""
cliente_detalhe.py - Tela de visualização de detalhes de um Cliente.
Exibida dentro da janela principal ao clicar em um item da listagem.
"""

import os
import logging
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from controllers.cliente_controller import (
    obter_por_id,
    remover,
    PASTA_FOTOS_CLIENTES,
)
from utils import formatar_moeda, formatar_cpf, formatar_telefone, formatar_data_hora

log = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Mapeamento de status → (texto, cor de fundo, cor do texto)
# ------------------------------------------------------------------
STATUS_BADGE = {
    "sem_debitos": ("Sem débitos",  "#f0f0f0", "#555555"),
    "em_dia":      ("Em dia",       "#e8f5e9", "#2e7d32"),
    "em_atraso":   ("Em atraso",    "#fde8e8", "#e53935"),
}

_PREVIEW_SIZE = (220, 220)


class ClienteDetalhe(ctk.CTkFrame):
    """
    Tela de detalhe de cliente. Mostra todas as informações com opções
    de editar ou excluir, e botão ← Voltar.
    """

    def __init__(self, parent, controller, cliente_id: int, on_voltar=None):
        super().__init__(parent, fg_color="#e8e8e8", corner_radius=0)

        self.controller = controller
        self.cliente_id = cliente_id
        self.on_voltar  = on_voltar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.cliente = obter_por_id(cliente_id)
        if not self.cliente:
            messagebox.showerror("Erro", "Cliente não encontrado.")
            self._voltar()
            return

        self._construir_ui()
        log.info(f"ClienteDetalhe carregado: id={cliente_id}")

    # ------------------------------------------------------------------
    # Interface principal
    # ------------------------------------------------------------------
    def _construir_ui(self):
        c = self.cliente

        self._criar_cabecalho(c)

        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="ew")
        conteudo.grid_columnconfigure(0, weight=2)
        conteudo.grid_columnconfigure(1, weight=5)

        self._criar_card_foto(conteudo, c)
        self._criar_card_info(conteudo, c)

    # ------------------------------------------------------------------
    # Cabeçalho: ← Voltar | Nome | ✏️ Editar | 🗑️ Excluir
    # ------------------------------------------------------------------
    def _criar_cabecalho(self, c: dict):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, padx=30, pady=(24, 12), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame, text="← Voltar", width=100, height=36,
            fg_color="#888888", hover_color="#666666",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._voltar,
        ).grid(row=0, column=0, padx=(0, 16))

        ctk.CTkLabel(
            frame,
            text=f"👤  {c['nome']}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1f6aa5",
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            frame, text="✏️  Editar", width=110, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._editar,
        ).grid(row=0, column=2, padx=(8, 6))

        ctk.CTkButton(
            frame, text="🗑️  Excluir", width=110, height=36,
            fg_color="#e53935", hover_color="#c62828",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._excluir,
        ).grid(row=0, column=3)

    # ------------------------------------------------------------------
    # Card esquerdo: foto do cliente
    # ------------------------------------------------------------------
    def _criar_card_foto(self, pai, c: dict):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        foto_nome = c.get("foto")
        if foto_nome:
            caminho = os.path.join(PASTA_FOTOS_CLIENTES, foto_nome)
            try:
                img = Image.open(caminho)
                img.thumbnail(_PREVIEW_SIZE, Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                lbl = ctk.CTkLabel(card, image=ctk_img, text="")
                lbl._image = ctk_img
                lbl.grid(row=0, column=0, padx=20, pady=20)
                return
            except Exception:
                pass

        ctk.CTkLabel(
            card, text="👤\nSem foto",
            font=ctk.CTkFont(size=16), text_color="#cccccc", justify="center",
        ).grid(row=0, column=0, padx=20, pady=20)

    # ------------------------------------------------------------------
    # Card direito: informações do cliente
    # ------------------------------------------------------------------
    def _criar_card_info(self, pai, c: dict):
        card = ctk.CTkFrame(pai, fg_color="white", corner_radius=12)
        card.grid(row=0, column=1, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        status = c.get("status_credito", "sem_debitos")
        badge_texto, badge_bg, badge_cor = STATUS_BADGE.get(
            status, ("—", "#f0f0f0", "#555555")
        )

        # Campos principais
        campos = [
            ("CPF",               formatar_cpf(c.get("cpf") or "") or "—"),
            ("Telefone",          formatar_telefone(c.get("telefone") or "") or "—"),
            ("E-mail",            c.get("email") or "—"),
            ("Nascimento",        c.get("data_nascimento") or "—"),
            ("Cidade",            c.get("cidade") or "—"),
        ]

        linha = 0
        pad_y = 4

        for rotulo, valor in campos:
            ctk.CTkLabel(
                card, text=rotulo + ":",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#555555", anchor="w",
            ).grid(row=linha, column=0, padx=(20, 8), pady=pad_y, sticky="w")

            ctk.CTkLabel(
                card, text=valor,
                font=ctk.CTkFont(size=13), text_color="#1a1a1a", anchor="w",
            ).grid(row=linha, column=1, padx=(0, 20), pady=pad_y, sticky="w")
            linha += 1

        # Badge de status
        ctk.CTkLabel(
            card, text="Status:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#555555", anchor="w",
        ).grid(row=linha, column=0, padx=(20, 8), pady=pad_y, sticky="w")

        badge = ctk.CTkFrame(card, fg_color=badge_bg, corner_radius=6)
        badge.grid(row=linha, column=1, padx=(0, 20), pady=pad_y, sticky="w")
        ctk.CTkLabel(
            badge, text=badge_texto,
            font=ctk.CTkFont(size=12, weight="bold"), text_color=badge_cor,
        ).grid(padx=10, pady=3)
        linha += 1

        # Seção de crediário (só exibe se tem_crediario = 1)
        if c.get("tem_crediario"):
            separador = ctk.CTkFrame(card, fg_color="#e0e0e0", height=1)
            separador.grid(row=linha, column=0, columnspan=2,
                           padx=20, pady=(10, 6), sticky="ew")
            linha += 1

            ctk.CTkLabel(
                card, text="Crediário",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#1f6aa5", anchor="w",
            ).grid(row=linha, column=0, columnspan=2, padx=(20, 8), pady=(0, 4), sticky="w")
            linha += 1

            campos_cred = [
                ("Limite",       formatar_moeda(c.get("limite_credito", 0))),
                ("Débito Atual", formatar_moeda(c.get("debito_atual", 0))),
            ]
            for rotulo, valor in campos_cred:
                cor_val = "#e53935" if rotulo == "Débito Atual" and (c.get("debito_atual") or 0) > 0 else "#1a1a1a"
                ctk.CTkLabel(
                    card, text=rotulo + ":",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#555555", anchor="w",
                ).grid(row=linha, column=0, padx=(20, 8), pady=pad_y, sticky="w")
                ctk.CTkLabel(
                    card, text=valor,
                    font=ctk.CTkFont(size=13, weight="bold"), text_color=cor_val, anchor="w",
                ).grid(row=linha, column=1, padx=(0, 20), pady=pad_y, sticky="w")
                linha += 1

        # Endereço
        endereco = (c.get("endereco") or "").strip()
        if endereco:
            ctk.CTkLabel(
                card, text="Endereço:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#555555", anchor="nw",
            ).grid(row=linha, column=0, padx=(20, 8), pady=(8, 4), sticky="nw")

            caixa = ctk.CTkTextbox(
                card, fg_color="#f5f5f5", border_width=0,
                font=ctk.CTkFont(size=13), height=60, corner_radius=8, state="normal",
            )
            caixa.insert("1.0", endereco)
            caixa.configure(state="disabled")
            caixa.grid(row=linha, column=1, padx=(0, 20), pady=(8, 12), sticky="ew")

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def _editar(self):
        from views.cliente_form import ClienteForm

        def voltar_para_detalhe():
            self.controller.mostrar_tela(
                ClienteDetalhe,
                cliente_id=self.cliente_id,
                on_voltar=self.on_voltar,
            )

        self.controller.mostrar_tela(
            ClienteForm,
            cliente_id=self.cliente_id,
            on_voltar=voltar_para_detalhe,
        )

    def _excluir(self):
        resposta = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja remover o cliente '{self.cliente['nome']}'?\nEssa ação não pode ser desfeita.",
        )
        if resposta:
            ok, msg = remover(self.cliente_id)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                self._voltar()
            else:
                messagebox.showerror("Erro", msg)

    def _voltar(self):
        if self.on_voltar:
            self.on_voltar()

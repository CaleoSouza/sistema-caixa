
Sistema de Caixa

Linguagem: Python
Interface: CustomTkinter
Banco de Dados: SQLite
Builder: Pyinstaller (para criar o executável depois de finalizar o projeto.)
Sistema será Local, ou seja, não terá acesso remoto, apenas para uso em um computador específico.

--------------------

Categorias dos menus:
- Produtos (Adicionar, remover, editar produtos, etc.)
- Clientes (Adicionar, remover, editar clientes, etc.)
- Carrinho (Registrar vendas, consultar vendas, etc.)
- Relatórios (Gerar relatórios de vendas, produtos, clientes, etc.)
- Configurações (Configurações do sistema, como backup de dados, etc.)

--------------------

Estrutura de Pastas:

Sistema Caixa/
│
├── main.py                      # Ponto de entrada da aplicação (logging + painel Ctrl+L)
├── database.py                  # Conexão e criação das tabelas SQLite + migração
├── utils.py                     # Funções de formatação padrão brasileiro (moeda, data, CPF, etc.)
│
├── .github/
│   └── copilot-instructions.md  # Instruções do GitHub Copilot
│
├── artes/                       # ignore essa pasta, é apenas para rascunhos de design e testes de interface
│
├── views/                       # Telas (uma por categoria)
│   ├── home_view.py             # Tela inicial (dashboard com cards clicáveis)
│   ├── produtos_view.py         # Listagem de produtos com filtros e busca
│   ├── produto_form.py          # Formulário de cadastro/edição de produto (in-window)
│   ├── produto_detalhe.py       # Detalhe do produto com editar/excluir (in-window)
│   ├── clientes_view.py         # ✅ Listagem de clientes com filtros e busca (Etapa 3)
│   ├── cliente_form.py          # ✅ Formulário de cadastro/edição de cliente (Etapa 3)
│   ├── cliente_detalhe.py       # ✅ Detalhe do cliente — redesign com tabelas crediário e pagamentos (11/03/2026)
│   ├── crediario_item_form.py   # ✅ Popup CTkToplevel para adicionar/editar item do crediário
│   ├── pagamento_form.py        # ✅ Popup CTkToplevel para registrar/editar pagamento
│   ├── carrinho_view.py         # ✅ Carrinho completo — Fase 1+2 (11/03/2026)
│   ├── relatorios_view.py       # (Etapa 5 - pendente)
│   └── configuracoes_view.py    # (Etapa 6 - pendente)
│
├── controllers/                 # Lógica de negócio
│   ├── produto_controller.py    # CRUD produtos, EAN-13, status estoque, imagens
│   ├── cliente_controller.py    # ✅ CRUD clientes, status crediário, imagens (Etapa 3)
│   └── venda_controller.py      # ✅ finalizar_venda + baixa estoque + crediário (Etapa 4)
│
├── models/                      # Consultas ao banco de dados
│   ├── produto_model.py         # SQL produtos: listar, filtros, resumo, estoque baixo, próx. vencer
│   ├── cliente_model.py         # ✅ SQL clientes: listar, filtros, resumo, em atraso (Etapa 3)
│   ├── crediario_model.py       # ✅ CRUD crediario_itens + historico_pagamentos + calcular_saldo
│   └── venda_model.py           # ✅ CRUD vendas + itens_venda + totais do dia (Etapa 4)
│
├── imagens/                     # Imagens do sistema
│   ├── produtos/                # Fotos de upload dos produtos
│   ├── clientes/                # Fotos de upload dos clientes
│   └── outros/                  # Ícones, logos e imagens diversas
│       ├── souza.png            # Logo exibido na HomeView
│       └── CS_logo.png          # Logo do sistema (barra da janela / ícone .exe)
│
├── design-interface/            # Referência visual do projeto
│   └── complex_example.py
│
├── anotações.md                 # Registro de progresso, o que foi feito e o que falta
└── instruções.md

--------------------

Ordem de Desenvolvimento (por etapas):

Etapa 1 - Base
  - Estrutura de pastas
  - database.py (SQLite, criação de todas as tabelas)
  - main.py (janela principal com sidebar de navegação)

Etapa 2 - Produtos
  - CRUD completo (adicionar, editar, remover, listar)
  - Upload de imagem do produto
  - Controle de estoque
  - Código de Barras (gerar código de barras para cada produto e permitir consulta por código de barras na hora da venda)

Etapa 3 - Clientes
  - CRUD completo
  - Upload de foto do cliente
  - Crediário pertence aos clientes que aparecerá na tela inicial.

Etapa 4 - Carrinho ✅ (concluída em 11/03/2026)
  - Painel esquerdo: Produtos Disponíveis (busca, filtros, leitor de código de barras) + Itens no Carrinho
  - Painel direito: Resumo do Pedido (totais, desconto, cliente, forma de pagamento, troco, parcelas)
  - Formas de pagamento: Dinheiro/PIX (campo + troco em tempo real) | Prazo (lança no crediário) | Cartão (Débito/Crédito + parcelas)
  - Finalizar Compra → baixa estoque → crediário (se a_prazo) → limpa carrinho automaticamente
  - Arquivos: views/carrinho_view.py, controllers/venda_controller.py, models/venda_model.py
  - REGRA: crediario_model.inserir_item() DEVE ser chamado em conexão separada (após commit+close do estoque)
  - Taxas cartão são internas (referência do vendedor); NÃO afetam o total_final do cliente
  
Etapa 5 - Relatórios
  - Relatórios de vendas, produtos e clientes

Etapa 6 - Configurações
  - Backup do banco de dados
  - Preferências do sistema
  - Informações da empresa (nome, endereço, telefone, etc.)
  - alterar logo da empresa da tela inicial home_view.py
  - configurações da tela inicial para exibir e ocultar Visão Geral.

--------------------

Padrão Visual:
- Tema: Claro (Light)
- Cor dos botões: Azul (padrão CustomTkinter "blue")
- Fonte: Padrão do CustomTkinter
- Referência de design: design-interface/complex_example.py
- logo do sistema: Imagens/outros/CS_logo.png (para ser usado na barra da janela e no logo executável)

Resolução e Responsividade:
- Sistema exclusivamente Desktop
- Resoluções suportadas: HD (1280x720) e Full HD (1920x1080)
- O main.py deve detectar a resolução do monitor automaticamente e ajustar o tamanho da janela:
    HD (1280x720)   → janela em 1280x720
    Full HD         → janela em 1920x1080
- Usar grid() com weight para que os elementos se adaptem ao redimensionamento
- Escala dos widgets via customtkinter.set_widget_scaling() conforme a resolução detectada

--------------------





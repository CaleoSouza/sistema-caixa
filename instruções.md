
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
├── main.py                      # Ponto de entrada da aplicação
├── database.py                  # Conexão e criação das tabelas SQLite
│
├── views/                       # Telas (uma por categoria)
│   ├── home_view.py             # Tela inicial (dashboard com atalhos das categorias)
│   ├── produtos_view.py
│   ├── clientes_view.py
│   ├── carrinho_view.py
│   ├── relatorios_view.py
│   └── configuracoes_view.py
│
├── controllers/                 # Lógica de negócio
│   ├── produto_controller.py
│   ├── cliente_controller.py
│   └── venda_controller.py
│
├── models/                      # Consultas ao banco de dados
│   ├── produto_model.py
│   ├── cliente_model.py
│   └── venda_model.py
│
├── imagens/                     # Imagens do sistema
│   ├── produtos/                # Fotos de upload dos produtos
│   ├── clientes/                # Fotos de upload dos clientes
│   └── outros/                  # Ícones, logos e imagens diversas
│
├── design-interface/            # Referência visual do projeto
│   └── complex_example.py
│
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

Etapa 3 - Clientes
  - CRUD completo
  - Upload de foto do cliente

Etapa 4 - Carrinho
  - Registrar vendas
  - Aplicar descontos
  - Baixar estoque automaticamente ao vender

Etapa 5 - Relatórios
  - Relatórios de vendas, produtos e clientes

Etapa 6 - Configurações
  - Backup do banco de dados
  - Preferências do sistema

--------------------

Padrão Visual:
- Tema: Claro (Light)
- Cor dos botões: Azul (padrão CustomTkinter "blue")
- Referência de design: design-interface/complex_example.py

--------------------





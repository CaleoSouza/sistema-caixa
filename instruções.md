
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
├── artes/                       # ignore essa pasta, é apenas para rascunhos de design e testes de interface
|
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
│   ├── bootstrap-icons/         # Ícones do sistema (quando terminar o projeto será apagados os icones que não forem usados)
│   ├── produtos/                # Fotos de upload dos produtos
│   ├── clientes/                # Fotos de upload dos clientes
│   └── outros/                  # Ícones, logos e imagens diversas
|
 design-interface/            # Referência visual do projeto
│   └── complex_example.py
|
├── anotações.md                    # Anotações do que foi feito, o que falta fazer, ideias para o projeto, etc.
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

Etapa 4 - Carrinho
  - Registrar vendas
  - Aplicar descontos
  - Baixar estoque automaticamente ao vender
  
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





# **SOFIA REFACTOR CHALENGE**

## Estrutura seguida:

```
sofia/
├── README.md                   # Documentação do projeto
├── brain.py                    # Módulo principal refatorado
├── core/                       # Módulos centrais
│   ├── __init__.py
│   ├── responder.py           # Lógica de resposta
│   ├── intent_router.py       # Roteamento de intenções
│   └── cache.py               # Sistema de cache
├── handlers/                   # Handlers específicos por domínio
│   ├── __init__.py
│   ├── boards_handler.py      # Manipulação de boards
│   ├── file_handler.py        # Operações com arquivos
│   └── general_handler.py     # Handlers gerais
├── config/                     # Configurações
│   ├── __init__.py
│   └── prompts.py             # Centralização de prompts
└── utils/                      # Utilitários específicos
    ├── __init__.py
    └── helpers.py             # Funções auxiliares específicas
```
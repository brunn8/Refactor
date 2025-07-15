# **SOFIA REFACTOR CHALENGE**

## Estrutura seguida:

```
sofia/
├── README.md                   
├── brain.py                    
├── core/                       
│   ├── responder.py           
│   ├── intent_router.py       
│   └── cache.py               
├── handlers/                  
│   ├── boards_handler.py      
│   ├── file_handler.py        
│   └── general_handler.py   
├── config/                     
│   └── prompts.py             
└── utils/                      
    └── helpers.py            
```

## Explicações
Decidi seguir uma estrutura muito similar à sugerida.
-------------------
O módulo *utils* que carrega o Helper, o agente que carrega APIs e funcoes especificas de apoio.

Já o módulo *handlers* que carrega os Handlers de operações gerais, de AzureBoards ou arquivos.

Ainda, o módulo *config* que traz o agente de interpretação de prompts.

E, para completar, o *core* que traz as funções mais gerais e de triagem da Sofia.

Assim, em *Brain.py* ficam apenas as inicializações dos módulos que farão todos os processos.
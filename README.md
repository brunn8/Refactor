# **SOFIA REFACTOR CHALENGE**

## Informações
- Nome: Bruno Henrique de Sousa Mouro
- E-mail: b.h.mouro@gmail.com
---

## Estrutura seguida:

```
sofia/
├── README.md                   
├── brain.py                    
├── core/                       
    ├── __init__.py
    ├── responder.py           
    ├── intent_router.py       
    └── cache.py               
├── handlers/
    ├── __init__.py                  
    ├── boards_handler.py      
    ├── file_handler.py        
    └── general_handler.py   
├── config/
    ├── __init__.py                     
    └── prompts.py             
└── utils/
    ├── __init__.py                      
    └── helpers.py            
```

---

## Explicações

### Decidi seguir a estrutura sugerida.

#### O pacote *utils* que carrega o Helper, o agente que carrega APIs e funcoes especificas de apoio.

#### Já o pacote *handlers* que carrega os Handlers de operações gerais, de AzureBoards ou arquivos.

#### Ainda, o pacote *config* que traz o agente de interpretação de prompts.

#### E, para completar, o *core* que traz as funções mais gerais e de triagem da Sofia.

#### Assim, em *Brain.py* ficam apenas as inicializações dos módulos que farão todos os processos.

---
# *Obrigado pela atenção!*
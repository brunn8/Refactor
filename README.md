# **SOFIA REFACTOR CHALLENGE**

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
│   ├── __init__.py
│   ├── responder.py           
│   ├── intent_router.py       
│   └── cache.py               
├── handlers/
│   ├── __init__.py                  
│   ├── boards_handler.py      
│   ├── file_handler.py        
│   └── general_handler.py   
├── config/
│   ├── __init__.py                     
│   └── prompts.py             
└── utils/
    ├── __init__.py                      
    └── helpers.py            
```

---

## Explicações

### Decidi seguir a estrutura sugerida: 

* Temos o pacote *utils* que carrega o Helper, o agente que carrega APIs e funcoes especificas de apoio.

* Já o pacote *handlers* carrega os Handlers de operações gerais, de AzureBoards ou arquivos.

* Ainda, há o pacote *config* que traz o agente de interpretação de prompts.

* E, para completar, o pacote *core* que traz as funções mais gerais e de triagem da Sofia.

#### Assim, em *Brain.py* ficam apenas as inicializações dos módulos que farão todos os processos.

> **Além disso**, mantive comentários para cada função e pacote e padronizei os nomes das funções para inglês.

---
# *Obrigado pela atenção!*
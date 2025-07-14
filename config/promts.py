# 1. Importando bibliotecas padrao
from datetime import datetime, timedelta
from functools import lru_cache

# 3. Importando aplicacoes locais
from config.settings import SessionLocal
from database.fragments import (
    gerar_fragmento_empresa,
    gerar_fragmento_setores,
    gerar_fragmento_funcionarios,
    gerar_fragmento_gerentes,
    gerar_fragmento_persona,
    gerar_fragmento_conhecimentos,
    gerar_fragmento_cerimonias,
)
from database.fragments.projeto_fragment import gerar_fragmento_projetos
from database.fragments.participacao_fragment import gerar_fragmento_participacoes

# 5. Importando modulos locais
from utils import helpers

class PromptAgent:
    """Agente de processamento de Propmts."""

    def __init__(self, Helper: helpers.Helper) -> None:
        """Construtor do agente de prompts. Inicializando o Helper."""

        self.Helper = Helper

    ###################
    # Funcoes publicas
    ###################

    async def generate_greetings(self) -> str:
        """
        Gerando saudacoes.
        
        retorna String de saudacao
        """

        system_prompt = self.generate_system_prompt()
        return await self.Helper.openai_service.gerar_saudacao_personalizada(system_prompt)
    
    @lru_cache(maxsize=32)
    def generate_system_prompt(self, historico_conversa: str = "", tom: str = "neutro") -> str:
        """
        Processando Prompt geral com fragmentos.
        
        args:
            historico_conversa: String de historico da conversa
            tom: tom da resposta
        
        retorna uma String do prompt gerado
        """
        
        with SessionLocal() as db:
            fragmentos = [
                gerar_fragmento_persona(db),
                gerar_fragmento_empresa(db),
                gerar_fragmento_setores(db),
                gerar_fragmento_funcionarios(db),
                gerar_fragmento_gerentes(db),
                gerar_fragmento_projetos(db),  
                gerar_fragmento_participacoes(db),
                gerar_fragmento_conhecimentos(db),
                gerar_fragmento_cerimonias(db),
            ]
    
        data_hoje = datetime.now().strftime("%d de %B de %Y")
        fragmentos.append(
            f"A data de hoje é {data_hoje}. Você pode usar essa informação para responder perguntas como 'qual é o dia de hoje?'."
        )
    
        if tom == "animado":
            fragmentos.append(
                "Adote um tom leve, simpático, entusiasmado e espontâneo, como alguém bem-humorado e acessível, use emoticons para deixar a interação mais agradável. 😊"
            )
        elif tom == "sério":
            fragmentos.append(
                "Adote um tom mais formal, direto e profissional, mantendo cordialidade e clareza."
            )
        
        if historico_conversa:
            fragmentos.append("\n" + historico_conversa)
    
        return "\n\n".join(p for p in fragmentos if p.strip())
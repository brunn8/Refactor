# 1. Importando bibliotecas padrao
from datetime import datetime,timedelta
from typing import Dict, Any, Optional, List

# 2. Importando blibliotecas de terceiros
import pandas as pd

# 3. Importando aplicacoes locais
from src.services.module.boards.azure_boards_service import AzureBoardsService
from src.services.module.boards.processing import processar_work_items_df

# 4. Importando constantes
from src.services.constants import (
    # Padroes
    CLIENT_SEARCH_KEYWORDS,

    # Parametros
    CACHE_DURATION, CACHE_CLEANUP_INTERVAL
)

class CacheAgent:
    """Agente de manipulacao de cache de AzureBoards"""

    def __init__(self) -> None:
        """Construtor da classe. Inicializando cache."""

        self.boards_cache = {}
        self.cache_duration = CACHE_DURATION
        self._last_cache_cleanup = datetime.now()

    ###################
    # Funcoes privadas
    ###################

    def _cleanup_cache(self) -> None:
        """Limpando cache."""

        now = datetime.now()
        if (now - self._last_cache_cleanup).seconds > CACHE_CLEANUP_INTERVAL:
            expired_keys = [
                key for key, data in self.boards_cache.items()
                if (now - data['timestamp']).seconds > self.cache_duration
            ]
            for key in expired_keys:
                del self.boards_cache[key]
            self._last_cache_cleanup = now

    async def _get_boards_data_cached(self, projeto: str, pergunta_lower: str) -> Optional[pd.DataFrame]:
        """
        Obter cache armazenado no AzureBoards.
        
        args:
            projeto: String com o noome do projeto
            pergunta_lower: String da pergunta em minusculo

        retorna um DataFrame com os dados em cache ou None.
        """
        
        buscar_epicos = any(termo in pergunta_lower for termo in CLIENT_SEARCH_KEYWORDS)
        
        cache_key = f"{projeto}_{datetime.now().strftime('%Y%m%d_%H_%M')[:12]}"
        if buscar_epicos:
            cache_key += "_epicos"
        
        if cache_key in self.boards_cache:
            cached_data = self.boards_cache[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < self.cache_duration:
                return cached_data['dataframe']
        
        try:
            azure_service = AzureBoardsService(projeto)
            work_items = azure_service.buscar_work_items(batch_size=100)
            
            if not work_items:
                return None
            
            df = await processar_work_items_df(work_items, projeto=projeto, buscar_epicos=buscar_epicos)
            
            self.boards_cache[cache_key] = {
                'dataframe': df,
                'timestamp': datetime.now()
            }
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar boards: {e}")
            return None
    
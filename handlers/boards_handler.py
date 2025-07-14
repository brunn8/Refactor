# 1. Importando bibliotecas padrao
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# 2. Importando blibliotecas de terceiros
import pandas as pd

# 3. Importando aplicacoes locais
from src.services.module.boards.azure_boards_service import AzureBoardsService
from src.services.module.boards.processing import (
    cliente_com_mais_atividades,
    cliente_com_mais_atividades_sonar_labs,
    processar_work_items_df,
    obter_responsavel_com_mais_tarefas,
    formatar_lista_tarefas,
    tarefas_em_andamento,
    tarefas_a_fazer,
    tarefas_em_atraso,
    formatar_visao_geral,
    extrair_tarefas_por_colaborador_e_estado,
    extrair_tarefas_por_colaborador,
)

# 4. Importando constantes
from src.services.constants import (
    # Mensagens
    BOARDS_SELECTION_MESSAGE, BOARDS_HELP_MESSAGE, BOARDS_EXIT_MESSAGE,
    
    # Padroes
    MAPA_TIPOS_ITENS, BOARDS_COMMANDS, EXIT_COMMANDS, HELP_COMMANDS, 
    COLLABORATOR_REFERENCES, PROGRESS_KEYWORDS, TODO_KEYWORDS, COMPLETED_KEYWORDS, 
    OVERVIEW_KEYWORDS, OVERDUE_KEYWORDS, HIERARCHY_KEYWORDS, CLIENT_KEYWORDS, 
    ACTIVITY_KEYWORDS, TASK_COUNT_KEYWORDS, BOARD_PROJECTS, CLIENT_SEARCH_KEYWORDS,
)

# 5. Importando modulos locais
from core import cache

class BoardsHandler:
    """Agente Handler de AzureBoards."""

    def __init__(self, CacheHandler: cache.CacheAgent) -> None:
        """
        Construtor do agente. Inicializando variaveis de AzureBoards e carregando cache.
        
        args:
            CacheHandler: Agente de cache ativo.

        Constroi o Handler.
        """

        self.modo_analise_boards = {}
        self.ultimo_colaborador_consultado = {}
        self.ultimo_board_por_usuario = {}

        self.CacheHandler = CacheHandler

    ###################
    # Funcoes publicas
    ###################

    async def answer_with_boards(self, pergunta: str, user_id: str = "global", context=None) -> str:
        """
        Gerando resposta com AzureBoards.
        
        args:
            pergunta: String da pergunta a ser respondida com AzureBoards
            user_id: ID do usuario.
            context: None por padrao (funcao vai ser extendida?)

        retorna uma String de resposta com AzureBoards ou erro.
        """
        
        pergunta_lower = pergunta.lower()
        
        if pergunta_lower in HELP_COMMANDS:
            return self._get_boards_help_message()
        
        projeto = self._detect_board_project(pergunta_lower, user_id)
        if not projeto:
            return BOARDS_SELECTION_MESSAGE
        
        self.ultimo_board_por_usuario[user_id] = projeto
        nome_amigavel = "Operações" if projeto == "Sonar" else projeto

        df = await self._get_boards_data_cached(projeto, pergunta_lower)
        if df is None:
            return f"Erro ao consultar o Azure Boards de '{nome_amigavel}'"
        
        return self._process_boards_query(user_id, pergunta_lower, df, nome_amigavel)

    ###################
    # Funcoes privadas
    ###################

    async def _handle_boards_analysis(self, user_id: str, user_message: str) -> str:
        """
        Analizando AzureBoards.
        
        args:
            user_id: ID de usuario
            user_message: Mensagem que sera tratada com AzureBoards

        retorna uma String de resposta.
        """

        message_lower = user_message.lower()
        
        if any(comando in message_lower for comando in BOARDS_COMMANDS):
            self.modo_analise_boards[user_id] = True
            return BOARDS_SELECTION_MESSAGE
        
        if message_lower in EXIT_COMMANDS:
            if user_id in self.modo_analise_boards:
                del self.modo_analise_boards[user_id]
            return BOARDS_EXIT_MESSAGE
        
        return await self.answer_with_boards(user_message, user_id)
    
    def _get_boards_help_message(self) -> str:
        """
        Retornando mensagem de ajuda de AzureBoards.
        
        retorna a mensagem de ajuda.
        """

        return BOARDS_HELP_MESSAGE

    def _detect_board_project(self, pergunta_lower: str, user_id: str) -> Optional[str]:
        """
        Dectectando o ultimo AzureBoard do usuario.
        
        args:
            pergunta_lower: String da pergunta em caracteres minusculos
            user_id: ID de usuario

        retorna uma String ou erro.
        """

        for keyword, project in BOARD_PROJECTS.items():
            if keyword in pergunta_lower:
                return project
        return self.ultimo_board_por_usuario.get(user_id)

    async def _get_boards_data_cached(self, projeto: str, pergunta_lower: str) -> Optional[pd.DataFrame]:
        """
        Buscando cache de dados AzureBoards.
        
        args:
            projeto: String de identificacao do projeto
            pergunta_lower: String da pergunta em minusculo

        retorna um DataFrame pandas com os dados cache ou erro.
        """

        buscar_epicos = any(termo in pergunta_lower for termo in CLIENT_SEARCH_KEYWORDS)
        
        cache_key = f"{projeto}_{datetime.now().strftime('%Y%m%d_%H_%M')[:12]}"
        if buscar_epicos:
            cache_key += "_epicos"
        
        if cache_key in self.CacheHandler.boards_cache:
            cached_data = self.CacheHandler.boards_cache[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < self.CacheHandler.cache_duration:
                return cached_data['dataframe']
        
        try:
            azure_service = AzureBoardsService(projeto)
            work_items = azure_service.buscar_work_items(batch_size=100)
            
            if not work_items:
                return None
            
            df = await processar_work_items_df(work_items, projeto=projeto, buscar_epicos=buscar_epicos)
            
            self.CacheHandler.boards_cache[cache_key] = {
                'dataframe': df,
                'timestamp': datetime.now()
            }
            
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar boards: {e}")
            return None

    def _process_boards_query(self, user_id: str, pergunta_lower: str, df: pd.DataFrame, nome_amigavel: str) -> str:
        """
        Processando a busca de AzureBoards. Separa a busca em classes de cliente, colaborador ou geral.
        
        args:
            user_id: ID do usuario
            pergunta_lower: String da pergunta em minusculo
            df: Dataframe contendo itens AzureBoards
            nome_amigavel: identificador do projeto a ser pesquisado

        retorna String formatada de resposta a pesquisa
        """
        
        if self._is_client_activity_query(pergunta_lower):
            if "sonar labs" in nome_amigavel.lower():
                return cliente_com_mais_atividades_sonar_labs(df)
            else:
                return cliente_com_mais_atividades(df, projeto=nome_amigavel)
        
        nome_colaborador = self._detect_collaborator_in_query(pergunta_lower, user_id, df)
        
        if nome_colaborador:
            return self._process_collaborator_specific_query(pergunta_lower, df, nome_colaborador)
        else:
            return self._process_general_boards_query(pergunta_lower, df, nome_amigavel)
        
    def _is_client_activity_query(self, pergunta_lower: str) -> bool:
        """
        Identifica se a pergunta pede informacoes de atividade de cliente.
        
        args:
            pergunta_lower: String da pergunta em minusculo.

        retorna um booleano (True - se requer as informacoes do cliente).
        """

        return (any(word in pergunta_lower for word in CLIENT_KEYWORDS) and
                any(word in pergunta_lower for word in ACTIVITY_KEYWORDS))

    def _detect_collaborator_in_query(self, pergunta_lower: str, user_id: str, df: pd.DataFrame) -> Optional[str]:
        """
        Identifica se um colaborador esta sendo mencionado na pergunta.

        args:
            pergunta_lower: String da pergunta em minusculo
            user_id: ID do usuario perguntando
            df: DataFrame com itens AzureBoards e coluna 'responsavel'

        retorna o nome do colaborador ou None.
        """

        if any(termo in pergunta_lower for termo in COLLABORATOR_REFERENCES):
            return self.ultimo_colaborador_consultado.get(user_id)
        
        tokens_pergunta = set(pergunta_lower.split())
        for responsavel in df['responsavel'].dropna().unique():
            partes_nome = set(responsavel.lower().split())
            if tokens_pergunta & partes_nome:
                self.ultimo_colaborador_consultado[user_id] = responsavel
                return responsavel
        
        return None

    def _process_collaborator_specific_query(self, pergunta_lower: str, df: pd.DataFrame, nome_colaborador: str) -> str:
        """
        Processa perguntas sobre colaborador especifico.
        
        args:
            pergunta_lower: String da pergunta em minusculo
            df: DataFrame com informacoes AzureBoards dos colaboradores
            nome_colaborador: String com nome do colaborador a ser pesquisado

        retorna uma String formatada com as informacoes do colaborador
        """
        
        if any(t in pergunta_lower for t in PROGRESS_KEYWORDS):
            tarefas = extrair_tarefas_por_colaborador_e_estado(df, nome_colaborador, "em andamento")
            return formatar_lista_tarefas(tarefas, f"Tarefas em andamento de {nome_colaborador}")
        elif any(t in pergunta_lower for t in TODO_KEYWORDS):
            tarefas = extrair_tarefas_por_colaborador_e_estado(df, nome_colaborador, "a fazer")
            return formatar_lista_tarefas(tarefas, f"Tarefas a fazer de {nome_colaborador}")
        elif any(t in pergunta_lower for t in COMPLETED_KEYWORDS):
            tarefas = extrair_tarefas_por_colaborador_e_estado(df, nome_colaborador, "concluído")
            return formatar_lista_tarefas(tarefas, f"Tarefas concluídas de {nome_colaborador}")
        else:
            tarefas = extrair_tarefas_por_colaborador(df, nome_colaborador)
            return formatar_lista_tarefas(tarefas, f"Tarefas de {nome_colaborador}")

    def _process_general_boards_query(self, pergunta_lower: str, df: pd.DataFrame, nome_amigavel: str) -> str:
        """
        Processa uma pergunta geral sobre o AzureBoard.
        
        args:
            pergunta_lower: String da pergunta em minusculo
            df: DataFrame do Board
            nome_amigavel: idenficador do Board ou projeto

        retorna uma String com as informacoes pedidas
        """

        for chave, tipo in MAPA_TIPOS_ITENS.items():
            if f"quantos {chave}" in pergunta_lower or f"quantas {chave}" in pergunta_lower:
                total = len(df[df["tipo"].str.lower() == tipo])
                return f"🔢 Existem **{total}** item(ns) do tipo **{tipo.title()}** no board {nome_amigavel}."
    
        for chave, tipo in MAPA_TIPOS_ITENS.items():
            if chave in pergunta_lower:
                tarefas_tipo = df[df["tipo"].str.lower() == tipo]
                return formatar_lista_tarefas(tarefas_tipo, f"{tipo.title()}s do board {nome_amigavel}")
    
        if any(p in pergunta_lower for p in OVERVIEW_KEYWORDS):
            return formatar_visao_geral(df)
    
        elif any(t in pergunta_lower for t in TODO_KEYWORDS):
            tarefas = tarefas_a_fazer(df)
            return formatar_lista_tarefas(tarefas, f"Tarefas a fazer do board {nome_amigavel}")
    
        elif any(t in pergunta_lower for t in PROGRESS_KEYWORDS):
            tarefas = tarefas_em_andamento(df)
            return formatar_lista_tarefas(tarefas, f"Tarefas em andamento do board {nome_amigavel}")
    
        elif any(t in pergunta_lower for t in OVERDUE_KEYWORDS):
            tarefas = tarefas_em_atraso(df)
            return formatar_lista_tarefas(tarefas, f"Tarefas atrasadas do board {nome_amigavel}")
    
        elif any(t in pergunta_lower for t in TASK_COUNT_KEYWORDS):
            responsavel, quantidade = obter_responsavel_com_mais_tarefas(df)
            return f"O colaborador com mais tarefas no total é {responsavel}, com {quantidade} tarefas."
    
        elif any(t in pergunta_lower for t in HIERARCHY_KEYWORDS):
            return self._format_user_story_hierarchy(df)
    
        return formatar_visao_geral(df)
    
    def _format_user_story_hierarchy(self, df: pd.DataFrame) -> str:
        """
        Formata uma visualizacao hierarquica dos stories do usuario e suas informacoes.
        
        args:
            df: DataFrame com as informacoes do usuario

        retorna String formatada com as informacoes do usuario
        """

        user_stories = df[df["tipo"].str.lower() == "user story"]
        tasks = df[df["tipo"].str.lower() == "task"]
    
        if user_stories.empty:
            return "❌ Nenhuma User Story encontrada no board."
    
        linhas = []
        for _, us in user_stories.iterrows():
            linhas.append(f"🔹 **{us['titulo']}** (#{us['id']})")
            tarefas_us = tasks[tasks["area"] == us["area"]]
            if tarefas_us.empty:
                linhas.append("   • _(sem tasks registradas)_")
            else:
                for _, t in tarefas_us.iterrows():
                    linhas.append(f"   • {t['titulo']} (#{t['id']})")
    
        return "\n".join(linhas)
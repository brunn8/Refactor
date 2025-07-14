# 1. Importando bibliotecas padrao
import re
import traceback

# 4. Importando constantes
from src.services.constants import (
    # Mensagens
    NO_FILES_MESSAGE, FILE_NOT_FOUND_MESSAGE, ERROR_400_MESSAGE, 
    ERROR_401_MESSAGE, ERROR_TECHNICAL_MESSAGE, FILE_LIST_INSTRUCTIONS, 
    
    # Padroes
    FILE_REQUEST_PATTERNS, FILE_KEYWORDS, REGEX_PATTERNS,
    
    # Parametros
    DEFAULT_FILE_LIMIT, MAX_FILE_LIMIT, MAX_RELEVANT_WORDS, MIN_WORD_LENGTH,
)

# 5. Importando modulos locais
from utils import helpers
from handlers import general_handler

class FileHandler:
    """Handler de arquivos."""

    def __init__(self, Helper: helpers.Helper, GeneralHandler: general_handler.GeneralHandler) -> None:
        """
        Construtor do Handler. Recebe o Handler geral e Helper.
        
        args:
            Helper: Helper em uso.
            GeneralHandler: Handler geral em uso

        """

        self.GeneralHandler = GeneralHandler
        self.Helper = Helper

    ###################
    # Funcoes publicas
    ###################

    async def list_files(self, user_id: str, user_message: str, mensagem_lower: str, quantidade: int = 10) -> str:
        """
        Listando arquivos do SharePoint.
        
        args:
            user_id: ID do usuario
            user_message: mensagem original do usuario
            mensagem_lower: mensagem em minusculo
            quantidade: Int de limite de quantidade de arquivos
        
        retorna String formatada com arquivos ou erro.
        """

        try:
            if not self.Helper._validate_sharepoint_config():
                return self.Helper._get_sharepoint_config_error()
            
            print(f"[DEBUG] Solicitando {quantidade} arquivos...")
            
            arquivos = self.Helper.sharepoint_service.list_recent_files(limit=quantidade)
            
            if not arquivos:
                return self._get_no_files_message()
            
            resultados_formatados = self._format_file_list(arquivos)
            
            return self._build_file_list_response(quantidade, len(arquivos), resultados_formatados)
            
        except Exception as e:
            return self._handle_file_listing_error(e)

    ###################
    # Funcoes privadas
    ###################

    async def _handle_file_requests(self, user_id: str, user_message: str) -> str:
        """
        Lidando com listagem ou pesquisa de arquivos.
        
        args:
            user_id: ID do usuario
            user_message: mensagem do usuario

        retorna String formatada com informacoes do(s) arquivo(s) ou erro. 
        """

        message_lower = user_message.lower()
        quantidade = self._extract_quantity_listing(user_message)
        
        if any(pattern in message_lower for pattern in FILE_REQUEST_PATTERNS):
            return await self.list_files(user_id, user_message, message_lower, quantidade)
        
        termo_busca = self._extract_search_term(user_message)
        if termo_busca:
            return await self.GeneralHandler.search_sharepoint_files(user_id, termo_busca)
        
        return FILE_NOT_FOUND_MESSAGE
    
    def _extract_search_term(self, message: str) -> str:
        """
        Extraindo palvras mais relevantes na pesquisa de arquivos.
        
        args:
            message: String da mensagem a ser filtrada
        
        retorna os termos mais relevantes na pesquisa de arquivo
        """

        clean_message = re.sub(REGEX_PATTERNS['action_cleaning'], '', message, flags=re.IGNORECASE)
        clean_message = re.sub(REGEX_PATTERNS['articles_cleaning'], '', clean_message, flags=re.IGNORECASE)
        
        file_match = self.GeneralHandler.file_extension_pattern.search(clean_message)
        if file_match:
            words = clean_message.split()
            for word in words:
                if self.GeneralHandler.file_extension_pattern.search(word):
                    return word
        
        words = clean_message.strip().split()
        relevant_words = [w for w in words if len(w) > MIN_WORD_LENGTH and w.lower() not in FILE_KEYWORDS[:2]]
        
        return ' '.join(relevant_words[:MAX_RELEVANT_WORDS])

    def _extract_quantity_listing(self, message: str) -> int:
        """
        Extrai quantidade de arquivos pedidos na mensagem.
        
        args:
            message: String da mensagem do usuario

        retorna o int de quantidade de arquivos
        """

        message_lower = message.lower()
        
        for pattern in REGEX_PATTERNS['quantity_patterns']:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    quantidade = int(match.group(1))
                    return max(1, min(quantidade, MAX_FILE_LIMIT))
                except (ValueError, IndexError):
                    continue
        
        return DEFAULT_FILE_LIMIT
        
    def _format_file_list(self, arquivos: list) -> list:
        """
        Formatando lista de arquivos SharePoint.
        
        args:
            arquivos: list de diretorios de arquivos SharePoint

        retorna lista de Strings formatadas com informacoes dos arquivos
        """

        resultados_formatados = []
        
        for i, arquivo in enumerate(arquivos, 1):
            nome = arquivo.get("name", "Sem nome")
            url = self.Helper._get_valid_url(arquivo)
            data_modificacao = self.Helper._format_date_with_hour(
                arquivo.get("modified_time") or arquivo.get("lastModifiedDateTime")
            )
            
            if url and url != "#":
                resultados_formatados.append(
                    f"{i}. **[{nome}]({url})** 📄 {data_modificacao}"
                )
            else:
                resultados_formatados.append(
                    f"{i}. **{nome}** 📄 {data_modificacao} ⚠️ *Link indisponível*"
                )
        
        return resultados_formatados
    
    def _get_no_files_message(self) -> str:
        """Retorna mensagem de nenhum arquivo encontrado."""

        return NO_FILES_MESSAGE

    def _build_file_list_response(self, quantidade: int, total_arquivos: int, resultados_formatados: list) -> str:
        """
        Construindo String final de resposta com arquivos e informacoes.
        
        args:
            quantidade: int de quantidade de arquivos pedidos
            total_arquivos: int de quantidade de arquivos encontrados
            resultados_formatados: list formatada de arquivos e informacoes

        retorna a String formatada de resposta final
        """

        return (
            f"📂 **{quantidade} arquivos solicitados** ({total_arquivos} encontrados):\n\n"
            f"{chr(10).join(resultados_formatados)}\n\n"
            f"{FILE_LIST_INSTRUCTIONS}"
        )

    def _handle_file_listing_error(self, e: Exception) -> str:
        """
        Lida com erros na listagem de arquivos.
        
        args:
            e: Exception do erro obtido
        
        retorna String formatada de erro obtido
        """

        print(f"❌ [ERRO] Falha na listagem: {e}")
        traceback.print_exc()
        
        if "400" in str(e):
            return ERROR_400_MESSAGE
        elif "401" in str(e):
            return ERROR_401_MESSAGE
        else:
            return ERROR_TECHNICAL_MESSAGE
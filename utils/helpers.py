# 1. Importando bibliotecas padrao
import re
import traceback
from datetime import datetime, timedelta

# 3. Importando aplicacoes locais
from src.services.api.openai.openai_service import OpenAIService
from src.services.module.sharepoint.sharepoint_service import SharePointService
from src.services.history.conversation_history import ConversationHistory

# 4. Importando constantes
from src.services.constants import (
    # Mensagens
    IMAGE_ERROR_MESSAGE, SINGLE_FILE_CLICK_INSTRUCTION, MULTIPLE_FILES_CLICK_INSTRUCTION, 
    FILE_FOUND_MESSAGE, FILE_CONTENT_ANALYSIS_OFFER, SHAREPOINT_CONFIG_ERROR,
    SHAREPOINT_DRIVE_ERROR,
    
    # Padroes
    REGEX_PATTERNS, URL_VALIDATION_PATTERNS, INVALID_URL_PATTERNS,
    
    # Parametros
    URL_FIELDS
)

class Helper:
    """Agente geral Helper."""

    def __init__(self) -> None:
        self.openai_service = OpenAIService()
        self.conversation_history = ConversationHistory()
        self.sharepoint_service = SharePointService()

    ###################
    # Funcoes publicas
    ###################

    async def process_image(self, user_id: str, caminho_imagem: str, prompt: str) -> str:
        """
        Processando imagem com OpenAI API.
        
        args:
            user_id: ID de usuario
            caminho_imagem: localizacao do diretorio da imagem
            prompt: String de prompt indicado o que deve ser analizado

        retorna String de resposta de analise
        """

        resposta = await self.openai_service.processar_imagem_local(caminho_imagem, prompt)
        return self._log_interaction(user_id, "[Análise de imagem]", resposta)
    
    async def answer_with_image(self, user_id: str, caminho_imagem: str, prompt: str) -> str:
        """
        Analise de imagem com OpenAI.

        args:
            user_id: ID de usuario
            caminho_imagem: localizacao do diretorio da imagem
            prompt: String de prompt indicado o que deve ser analizado

        retorna String de resultado de analise        
        """

        try:
            resposta = await self.openai_service.analisar_imagem_com_prompt(
                pergunta=prompt,
                caminho_imagem=caminho_imagem
            )
            
            return self._log_interaction(user_id, f"[Análise de imagem]", resposta)
        except Exception as e:
            return self._log_interaction(
                user_id, 
                "[Erro ao processar imagem]", 
                IMAGE_ERROR_MESSAGE
            )

    async def process_document(self, user_id: str, caminho_documento: str, 
                               nome_arquivo: str, tipo_arquivo: str) -> str:
        """
        Processa documento com OpenIA.
        
        args:
            user_id: ID de usuario
            caminho_documento: localizacao do diretorio da imagem
            nome_arquivo: String com nome do arquivo
            tipo_arquivo: String de tipo do arquivo

        retorna String de resposta do processamento
        """

        resposta = await self.openai_service.processar_documento_completo(caminho_documento, nome_arquivo, tipo_arquivo)
        return self._log_interaction(user_id, f"[Documento: {nome_arquivo}]", resposta)

    def get_file_content(self, user_id: str, nome_arquivo: str) -> str:
        """
        Obtem e formata informacoes de arquivo no SharePoint.
        
        args:
            user_id: ID de usuario
            nome_arquivo: String de nome do arquivo

        retorna String de informacoes do arquivo ou None
        """

        arquivos = self.sharepoint_service.search_files(nome_arquivo)
        
        if not arquivos:
            variantes = [
                nome_arquivo.lower(),
                nome_arquivo.upper(),
                nome_arquivo.replace("_", " "),
                f"{nome_arquivo}.docx" if "." not in nome_arquivo else nome_arquivo,
                nome_arquivo.split(".")[0] if "." in nome_arquivo else nome_arquivo
            ]
            for variante in variantes:
                if variante != nome_arquivo:
                    arquivos = self.sharepoint_service.search_files(variante)
                    if arquivos:
                        break  
                        
        if not arquivos:
            resposta = f"Não encontrei nenhum arquivo com o nome '{nome_arquivo}'."
            self.conversation_history.add_interaction(user_id, f"Obter arquivo: {nome_arquivo}", resposta)
            return resposta
        
        arquivo = arquivos[0]
        nome = arquivo.get("name", "")
        arquivo_url = arquivo.get("web_url") or arquivo.get("server_url") or arquivo.get("url") or arquivo.get("id", "")
        
        if not arquivo_url:
            resposta = f"Encontrei o arquivo '{nome}', mas não consegui obter seu caminho. Tente novamente."
            self.conversation_history.add_interaction(user_id, f"Obter arquivo: {nome_arquivo}", resposta)
            return resposta
        
        data_modificacao = self._format_date_with_hour(arquivo.get("modified_time") or arquivo.get("lastModifiedDateTime"))
        
        resposta = (
            f"{FILE_FOUND_MESSAGE}"
            f"1. **[{nome}]({arquivo_url})** 📄 {data_modificacao}\n\n"
            f"{SINGLE_FILE_CLICK_INSTRUCTION}"
            f"{FILE_CONTENT_ANALYSIS_OFFER}"
        )
        
        self.conversation_history.add_interaction(user_id, f"Obter arquivo: {nome_arquivo}", resposta)
        return resposta

    ###################
    # Funcoes privadas
    ###################

    def _handle_error_response(self, e: Exception, intent: str, user_id: str) -> str:
        """
        Trata mensagens de erro e log dos erros.
        
        args:
            e: Exception obtida
            intent: String de intencao sendo processada quando ocorreu o erro
            user_id: ID de usuario

        retorna String formatada de mensagem de erro
        """

        erro_id = f"ERR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        mensagem_log = f"❌ [{erro_id}] Erro no handler de intenção '{intent}' para usuário '{user_id}': {type(e).__name__}: {e}"
        print(mensagem_log)
        traceback.print_exc()
    
        return (
            f"⚠️ Algo deu errado ao processar sua solicitação.\n"
            f"Código do erro: `{erro_id}`\n"
            f"Tente novamente em instantes ou avise o time técnico com esse código.")

    def _log_interaction(self, user_id: str, user_message: str, resposta: str) -> str:
        """
        Cria Log de interacao do usuario.

        args:
            user_id: ID do usuario
            user_message: String de mensagem do usuario
            resposta: String de resposta obtida

        retorna a resposta obtida sem alteracoes
        """

        self.conversation_history.add_interaction(user_id, user_message, resposta)
        return resposta

    def _format_search_results(self, user_id: str, termo_busca: str, arquivos: list) -> str:
        """
        Formata os resultados de busca de arquivo.
        
        args:
            user_id: ID de usuario (funcao vai ser extendida?)
            termo_busca: String de termos de busca usados
            arquivos: list de arquivos SharePoint

        retorna String formatada de resultados
        """

        if len(arquivos) == 1:
            return self._format_single_file_result(arquivos[0], termo_busca)
        else:
            return self._format_multiple_files_result(arquivos, termo_busca)
        
    def _format_single_file_result(self, arquivo: dict, termo_busca: str) -> str:
        """
        Formatando resultado de busca de arquivo unico.
        
        args:
            arquivo: dict com informacoes do arquivo no SharePoint
            termo_busca: String de termo de busca original
        
        retorna String formatada de informacoes
        """

        nome = arquivo.get("name", "Sem nome")
        url = self._get_valid_url(arquivo)
        data_modificacao = self._format_date_with_hour(
            str(arquivo.get("modified_time")) or str(arquivo.get("lastModifiedDateTime"))
        )
        
        return (
            f"📂 Encontrei **1 arquivo** para '**{termo_busca}**':\n\n"
            f"1. **[{nome}]({url})** 📄 {data_modificacao}\n\n"
            f"{SINGLE_FILE_CLICK_INSTRUCTION}"
        )
    
    def _format_multiple_files_result(self, arquivos: list, termo_busca: str) -> str:
        """
        Formatando resultado de busca com multiplos arquivos.

        args:
            arquivos: list de arquivos e informacoes
            termo_busca: String de termo de busca original
        
        retorna String formatada de informacoes
        """

        resultados = []
        
        for i, arquivo in enumerate(arquivos, 1):
            nome = arquivo.get('name', 'Sem nome')
            url = self._get_valid_url(arquivo)
            data_modificacao = self._format_date_with_hour(
                arquivo.get("modified_time") or arquivo.get("lastModifiedDateTime")
            )
            resultados.append(f"{i}. **[{nome}]({url})** 📄 {data_modificacao}")
        
        return (
            f"📂 Encontrei **{len(arquivos)} arquivo(s)** para '**{termo_busca}**':\n\n"
            f"{chr(10).join(resultados)}\n\n"
            f"{MULTIPLE_FILES_CLICK_INSTRUCTION}"
        )
    
    def _validate_url(self, url: str) -> bool:
        """
        Checa se URL e valida.
        
        args:
            url: String da URL a ser validada

        retorna bool de resultado da validacao
        """

        url_lower = url.lower().strip()
        
        for pattern in URL_VALIDATION_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        
        return url_lower not in INVALID_URL_PATTERNS

    def _get_valid_url(self, arquivo: dict) -> str:
        """
        Extrai a primeira URL valida de um arquivo.
        
        args:
            arquivo: dict com metadados de arquivo

        retorna String da primeira URL valida
        """

        for field in URL_FIELDS:
            url = arquivo.get(field)
            if url and isinstance(url, str) and url.strip():
                if self._validate_url(url):
                    return url
        
        return "#"

    def _format_legacy_file_response(self, resposta_bruta: str) -> str:
        """
        Formata uma resposta legacy.
        
        args:
            resposta_bruta: String de resposta bruta
        
        retorna String formatada com informacoes do arquivo
        """

        try:
            nome_match = re.search(REGEX_PATTERNS['legacy_file_name'], resposta_bruta)
            link_match = re.search(REGEX_PATTERNS['legacy_file_link'], resposta_bruta)
            nome = nome_match.group(1) if nome_match else "Arquivo"
            url = link_match.group(1) if link_match else "#"
            
            data_atual = f"📅 Última modificação: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
            
            return (
                f"📂 Encontrei **1 arquivo** relacionado a '**{nome}**':\n\n"
                f"1. **[{nome}]({url})** 📄 {data_atual}\n\n"
                f"{SINGLE_FILE_CLICK_INSTRUCTION}"
            )
        except Exception:
            return resposta_bruta
    
    def _validate_sharepoint_config(self) -> bool:
        """
        Validando configuracao de sharepoint.
        
        retorna bool de validacao
        """

        return (hasattr(self.sharepoint_service, 'token') and self.sharepoint_service.token and
                hasattr(self.sharepoint_service, 'drive_id') and self.sharepoint_service.drive_id)
    
    def _get_sharepoint_config_error(self) -> str:
        """
        Determina a mensagem correta de erro de configuracao de SharePoint.

        retorna a String da mensagem adequada
        """

        if not hasattr(self.sharepoint_service, 'token') or not self.sharepoint_service.token:
            return SHAREPOINT_CONFIG_ERROR
        else:
            return SHAREPOINT_DRIVE_ERROR

    def _format_date_with_hour(self, data_iso: str) -> str:
        """
        Formata uma data ISO com informacoes de hora

        args:
            data_iso: String de data em formato ISO

        retorna String de data formatada com hora  
        """

        if not data_iso:
            return f"📅 Última modificação: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        
        try:
            if 'T' in data_iso:
                if '.' in data_iso:
                    dt = datetime.strptime(data_iso[:19], "%Y-%m-%dT%H:%M:%S")
                else:
                    dt = datetime.strptime(data_iso, "%Y-%m-%dT%H:%M:%SZ")
            else:
                dt = datetime.strptime(data_iso[:10], "%Y-%m-%d")
            
            return f"📅 Última modificação: {dt.strftime('%d/%m/%Y às %H:%M')}"
        except Exception:
            return f"📅 Última modificação: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"

    
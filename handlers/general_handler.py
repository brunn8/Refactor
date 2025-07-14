# 1. Importando bibliotecas padrao
import re
from datetime import datetime, timedelta

# 3. Importando aplicacoes locais
from src.services.knowledge.knowledge_manager import (
    salvar_aprendizado_manual,
    listar_conhecimentos_manuais,
)

# 4. Importando constantes
from src.services.constants import (
    # Mensagens
    FILE_NOT_FOUND_MESSAGE, ADMIN_COMMAND_NOT_RECOGNIZED, LEARNING_ERROR_MESSAGE,
    LEARNING_QUESTION_PROMPT, LEARNING_ERROR_RETRY, OPENAI_FALLBACK_MESSAGE,
    COURTESY_RESPONSE, FILE_SEARCH_NO_RESULTS,
    GREETING_DEFAULT, GREETING_WELLBEING, DIAGNOSTIC_HEADER, DIAGNOSTIC_CONFIG_SECTION,
    DIAGNOSTIC_CONNECTIVITY_SECTION, DIAGNOSTIC_ENDPOINTS_SECTION,
    
    # Padroes
    LEARNING_TRIGGERS, FILE_KEYWORDS, POSITIVE_WORDS,
    FILE_CONTEXT_WORDS, CASUAL_INDICATORS, FILE_INTENT_INDICATORS,
    GREETING_WORDS, WELLBEING_PHRASES, REGEX_PATTERNS,
    
    # Parametros
    SEARCH_CACHE_DURATION, ENDPOINTS_TIMEOUT, MAX_RELEVANT_WORDS, 
    MIN_WORD_LENGTH, GRAPH_ENDPOINTS, LEARNING_STEPS
)

# 5. Importando modulos locais
from utils import helpers
from core import cache
from config import promts

class GeneralHandler:
    """Handler geral. Base para todos os Handlers."""

    def __init__(self, CacheAgent: cache.CacheAgent, Helper: helpers.Helper, 
                 PromptAgent: promts.PromptAgent) -> None:
        """
        Construtor do Handler geral.
        
        args:
            CacheAgent: CacheAgent ativo
            Helper: Helper ativo
            PropmtAgent: PromptAgent em uso

        """

        self.aprendizado_manual_ativo = {}
        self.etapa_aprendizado = {}

        self.CacheAgent = CacheAgent
        self.Helper = Helper
        self.PromptAgent = PromptAgent

        self._compile_regex_patterns()

    ###################
    # Funcoes publicas
    ###################

    def verify_manual_learning(self, user_id: str, user_message: str) -> bool:
        """
        Verifica se mensagem inicia/continua processo de aprendizado manual.

        args:
            user_id: ID de usuario que enviou a mensagem
            user_message: String de mensagem do usuario

        retorna booleano (1 - se a mensagem inicia ou continua aprendizado manual)
        """

        mensagem = user_message.strip().lower()
        if any(p in mensagem for p in LEARNING_TRIGGERS):
            self.aprendizado_manual_ativo[user_id] = True
            self.etapa_aprendizado[user_id] = LEARNING_STEPS['pergunta']
            return True
        return user_id in self.aprendizado_manual_ativo
    
    def process_manual_learning(self, user_id: str, user_message: str) -> str:
        """
        Processa o aprendizado manual.
        
        args:
            user_id: ID do usuario
            user_message: mensagem do usuario

        retorna String de resposta apropriada
        """

        etapa = self.etapa_aprendizado.get(user_id)
        if etapa == LEARNING_STEPS['pergunta']:
            self.aprendizado_manual_ativo[user_id] = {"pergunta": user_message}
            self.etapa_aprendizado[user_id] = LEARNING_STEPS['resposta']
            return LEARNING_QUESTION_PROMPT
        if etapa == LEARNING_STEPS['resposta']:
            pergunta = self.aprendizado_manual_ativo[user_id]["pergunta"]
            mensagem = salvar_aprendizado_manual(pergunta, user_message)
            del self.aprendizado_manual_ativo[user_id]
            del self.etapa_aprendizado[user_id]
            return mensagem
        return LEARNING_ERROR_RETRY
    
    def answer_with_manual_learnings(self, pergunta_usuario: str) -> str | None:
        """
        Obtendo as respostas do aprendizado manual.
        
        args:
            pergunta_usuario: String de pergunta original do usuario

        retorna String de resposta ou None.
        """

        pergunta = pergunta_usuario.strip().lower()
        for conhecimento in listar_conhecimentos_manuais(limit=50):
            if conhecimento.get("pergunta", "").strip().lower() in pergunta:
                return conhecimento.get("resposta")
        return None

    
    async def diagnose_complete_sharepoint(self, user_id: str, termo_teste: str = "Manifesto_Tribo_Sonar_Labs") -> str:
        """
        Executa diagnostico de conexao e configuracao de SharePoint.
        
        args:
            user_id: ID do usuario testando
            termo_teste: termo de pesquisa opcional

        retorna String de relatorio de diagnostico
        """
        
        relatorio = [DIAGNOSTIC_HEADER]
        
        try:
            relatorio.append(DIAGNOSTIC_CONFIG_SECTION)
            
            from config.settings import TENANT_ID, CLIENT_ID, CLIENT_SECRET, TARGET_DRIVE_NAME
            
            config_status = {
                "TENANT_ID": "✅ OK" if TENANT_ID else "❌ VAZIO",
                "CLIENT_ID": "✅ OK" if CLIENT_ID else "❌ VAZIO", 
                "CLIENT_SECRET": "✅ OK" if CLIENT_SECRET else "❌ VAZIO",
                "TARGET_DRIVE_NAME": "✅ OK" if TARGET_DRIVE_NAME else "❌ VAZIO"
            }
            
            for var, status in config_status.items():
                relatorio.append(f"• {var}: {status}")
                
            service_name = type(self.Helper.sharepoint_service).__name__
            relatorio.append(f"• SharePoint Service: {service_name}")
            
            has_token = (hasattr(self.Helper.sharepoint_service, 'token') and 
                         self.Helper.sharepoint_service.token)
            token_status = "✅ SIM" if has_token else "❌ NÃO"
            relatorio.append(f"• Token presente: {token_status}")
            
            has_site_id = (hasattr(self.Helper.sharepoint_service, 'site_id') and 
                           self.Helper.sharepoint_service.site_id)
            site_status = "✅ OK" if has_site_id else "❌ FALTANDO"
            relatorio.append(f"• Site ID: {site_status}")
            
            has_drive_id = (hasattr(self.Helper.sharepoint_service, 'drive_id') and 
                            self.Helper.sharepoint_service.drive_id)
            drive_status = "✅ OK" if has_drive_id else "❌ FALTANDO"
            relatorio.append(f"• Drive ID: {drive_status}")
            
        except Exception as e:
            relatorio.append(f"❌ **ERRO NA CONFIGURAÇÃO:** {e}")
            return "\n".join(relatorio)
        
        try:
            relatorio.append(DIAGNOSTIC_CONNECTIVITY_SECTION)
            
            arquivos_teste = self.Helper.sharepoint_service.list_recent_files(limit=3)
            
            if arquivos_teste:
                relatorio.append(f"✅ Conexão OK - {len(arquivos_teste)} arquivos acessíveis")
                for i, arquivo in enumerate(arquivos_teste[:3], 1):
                    nome = arquivo.get("name", "Nome não disponível")
                    relatorio.append(f"   {i}. `{nome}`")
            else:
                relatorio.append("⚠️ Conexão estabelecida mas nenhum arquivo encontrado")
                
            relatorio.extend(self._test_sharepoint_endpoints())
            
        except Exception as e:
            relatorio.append(f"❌ **ERRO DE CONECTIVIDADE:** {e}")
        
        return "\n".join(relatorio)
    
    async def search_sharepoint_files(self, user_id: str, termo_busca: str) -> str:
        """
        Pesquisa por arquivos no SharePoint.
        
        args:
            user_id: ID de usuario
            termo_busca: termo a ser pesquisado
        
        retorna String de resultados de busca
        """

        if not termo_busca.strip():
            return FILE_NOT_FOUND_MESSAGE
        
        cache_key = f"search_{termo_busca.lower().replace(' ', '_')}"
        if cache_key in self.CacheAgent.boards_cache:
            cached = self.CacheAgent.boards_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < SEARCH_CACHE_DURATION:
                return cached['result']
        
        try:
            # Estratégia 1: Busca direta
            arquivos = self.Helper.sharepoint_service.search_files(termo_busca)
            if arquivos:
                result = self.Helper._format_search_results(user_id, termo_busca, arquivos)
                self.CacheAgent.boards_cache[cache_key] = {'result': result, 'timestamp': datetime.now()}
                return result
        except Exception:
            pass
        
        try:
            # Estratégia 2: Interpretação AI (SEM LAMBDA!)
            arquivos = await self._search_with_ai_interpretation(termo_busca)  # ✅ await direto
            if arquivos:
                result = self.Helper._format_search_results(user_id, termo_busca, arquivos)
                self.CacheAgent.boards_cache[cache_key] = {'result': result, 'timestamp': datetime.now()}
                return result
        except Exception:
            pass
        
        try:
            # Estratégia 3: Variações
            arquivos = self._search_with_variations(termo_busca)
            if arquivos:
                result = self.Helper._format_search_results(user_id, termo_busca, arquivos)
                self.CacheAgent.boards_cache[cache_key] = {'result': result, 'timestamp': datetime.now()}
                return result
        except Exception:
            pass
        
        try:
            # Estratégia 4: Por palavras
            arquivos = self._search_by_words(termo_busca)
            if arquivos:
                result = self.Helper._format_search_results(user_id, termo_busca, arquivos)
                self.CacheAgent.boards_cache[cache_key] = {'result': result, 'timestamp': datetime.now()}
                return result
        except Exception:
            pass
        
        return FILE_SEARCH_NO_RESULTS.format(termo_busca)

    ###################
    # Funcoes privadas
    ###################

    def _compile_regex_patterns(self):
        """Carregando padroes de regex."""

        self.file_extension_pattern = re.compile(
            REGEX_PATTERNS['file_extension'], 
            re.IGNORECASE
        )
        self.file_naming_pattern = re.compile(REGEX_PATTERNS['file_naming'])
        self.greeting_pattern = re.compile(
            REGEX_PATTERNS['greeting'],
            re.IGNORECASE
        )

    async def _handle_admin_commands(self, user_id: str, user_message: str = None) -> str:
        """
        Processando comandos administrativos.
        
        args:
            user_id: ID de usuario
            user_message: mensagem original do usuario
        
        retorna String de diagnostico ou erro.
        """
        
        message_lower = user_message.lower()
        
        if message_lower == "diagnosticar sharepoint":
            return await self.diagnose_complete_sharepoint(user_id)
        elif "testar busca" in message_lower:
            termo = user_message.replace("testar busca", "").strip()
            return await self.diagnose_complete_sharepoint(user_id, termo or "Manifesto_Tribo_Sonar_Labs")
        
        return ADMIN_COMMAND_NOT_RECOGNIZED

    def _handle_learning(self, user_id: str, user_message: str) -> str:
        """
        Verificando se mensagem ativa apredizado manual, caso positivo, 
        processa o aprendizado.
        
        args:
            user_id: ID de usuario
            user_message: String de mensagem do usuario

        retorna String de resposta
        """

        if self.verify_manual_learning(user_id, user_message):
            return self.process_manual_learning(user_id, user_message)
        return LEARNING_ERROR_MESSAGE

    def _handle_greetings(self, user_message: str) -> str:
        """
        Processa mensagem de saudacao.
        
        args:
            user_message: String de mensagem do usuario
        
        retorna String de resposta adequada
        """

        message_lower = user_message.lower()
        
        if any(word in message_lower for word in GREETING_WORDS):
            return GREETING_DEFAULT
        elif any(phrase in message_lower for phrase in WELLBEING_PHRASES):
            return GREETING_WELLBEING
        else:
            return GREETING_DEFAULT

    async def _handle_general_questions(self, user_id: str, user_message: str, nome_usuario: str) -> str:
        """
        Processa mensagens gerais direcionando para o Handler adequado.

        args:
            user_id: ID de usuario da mensagem
            user_message: mensagem original do usuario
            nome_usuario: nome do usuario da mensagem

        retorna String de resposta apropriada a mensagem
        """

        message_lower = user_message.lower()
    
        if self._is_courtesy_message(message_lower):
            return COURTESY_RESPONSE
    
        if nome_usuario and "meu nome" in message_lower:
            return f"Claro! Você é {nome_usuario}, certo? 😄"
    
        resposta_manual = self.answer_with_manual_learnings(user_message)
        if resposta_manual:
            return resposta_manual
    
        is_casual = self._is_casual_conversation(message_lower)
        has_file_intent = self._has_file_intent(message_lower)
    
        if not is_casual and has_file_intent:
            termo_busca = self._extract_search_term(user_message)
            if termo_busca:
                return await self.search_sharepoint_files(user_id, termo_busca)
    
        return await self._process_with_openai(user_id, user_message)

    def _is_courtesy_message(self, message_lower: str) -> bool:
        """
        Classifica a mensagem como cortesia positiva e sem intencao com arquivos.
        
        args:
            message_lower: String de mensagem em minusculo
        
        retorna bool de classificacao como cortesia positiva apenas
        """

        has_positive = any(word in message_lower for word in POSITIVE_WORDS)
        has_file_context = any(word in message_lower for word in FILE_CONTEXT_WORDS)
        
        return has_positive and not has_file_context
    
    def _is_casual_conversation(self, message_lower: str) -> bool:
        """
        Classifica a mensagem como conversa casual.
        
        args:
            message_lower: String de mensagem em minusculo
        
        retorna bool de classificacao como conversa casual
        """

        return any(indicator in message_lower for indicator in CASUAL_INDICATORS)
    
    def _has_file_intent(self, message_lower: str) -> bool:
        """
        Verifica se a mensagem tem intencao relacionada a arquivos.
        
        args:
            message_lower: String de mensagem em minusculo
        
        retorna bool de intencao relacionada a arquivo (True se tem intencao com arquivo)
        """

        return any(indicator in message_lower for indicator in FILE_INTENT_INDICATORS)
    
    def _test_sharepoint_endpoints(self) -> list:
        """
        Testa endpoints de SharePoint.
        
        retorna list de linhas do diagnostico com os estados dos endpoints
        """

        relatorio = [DIAGNOSTIC_ENDPOINTS_SECTION]
        
        headers = {"Authorization": f"Bearer {self.Helper.sharepoint_service.token}"}
        test_endpoints = [
            GRAPH_ENDPOINTS[0].format(self.Helper.sharepoint_service.drive_id),
            GRAPH_ENDPOINTS[1].format(self.Helper.sharepoint_service.drive_id),
            GRAPH_ENDPOINTS[2].format(self.Helper.sharepoint_service.site_id)
        ]
        
        for endpoint in test_endpoints:
            try:
                import requests
                response = requests.get(endpoint, headers=headers, timeout=ENDPOINTS_TIMEOUT)
                relatorio.append(f"• {endpoint.split('/')[-1]}: Status {response.status_code}")
            except Exception as e:
                relatorio.append(f"• {endpoint.split('/')[-1]}: ❌ {str(e)[:50]}")
        
        return relatorio
    
    def _extract_search_term(self, message: str) -> str:
        """
        Extrai os termos relevantes para pesquisa da mensagem do usuario.
        
        args:
            message: String da mensagem original do usuario

        retorna uma String com os termos mais revelantes
        """

        clean_message = re.sub(REGEX_PATTERNS['action_cleaning'], '', message, flags=re.IGNORECASE)
        clean_message = re.sub(REGEX_PATTERNS['articles_cleaning'], '', clean_message, flags=re.IGNORECASE)
        
        file_match = self.file_extension_pattern.search(clean_message)
        if file_match:
            words = clean_message.split()
            for word in words:
                if self.file_extension_pattern.search(word):
                    return word
        
        words = clean_message.strip().split()
        relevant_words = [w for w in words if len(w) > MIN_WORD_LENGTH and w.lower() not in FILE_KEYWORDS[:2]]
        
        return ' '.join(relevant_words[:MAX_RELEVANT_WORDS])
        
    async def _search_with_ai_interpretation(self, termo_busca: str):
        """
        Amplia a busca de arquivos no SharePoint com interpretacao de IA do termo de busca.

        args:
            termo_busca: String de termo de busca

        retorna list de arquivos ou None.
        """

        try:
            termo_limpo = await self.Helper.openai_service.interpretar_termo_busca(termo_busca)
            if termo_limpo != termo_busca:
                return self.Helper.sharepoint_service.search_files(termo_limpo)
        except Exception:
            pass
        return None

    def _search_with_variations(self, termo_busca: str):
        """
        Busca arquivos no SharePoint com variacoes padrao do termo de busca.

        args:
            termo_busca: String do termo de busca

        retorna list de arquivos ou None.
        """

        variations = [
            termo_busca.replace(' ', '_'),
            termo_busca.replace(' ', '-'),
            termo_busca.replace('_', ' '),
            termo_busca.replace('-', ' '),
            termo_busca.lower(),
            termo_busca.title()
        ]
        
        for variation in variations:
            if variation != termo_busca:
                try:
                    arquivos = self.Helper.sharepoint_service.search_files(variation)
                    if arquivos:
                        return arquivos
                except Exception:
                    continue
        return None

    def _search_by_words(self, termo_busca: str):
        """
        Busca por arquivos no SharePoint separando os termos de busca e agrupando resultados.

        args:
            termo_busca: String de termo de busca

        retorna list de arquivos ou None.
        """

        words = [w.strip() for w in termo_busca.split() if len(w.strip()) > MIN_WORD_LENGTH]
        all_files = []
        
        for word in words:
            try:
                files = self.Helper.sharepoint_service.search_files(word)
                if files:
                    all_files.extend(files)
            except Exception:
                continue
        
        if all_files:
            unique_files = {f.get("name", ""): f for f in all_files if f.get("name")}
            return list(unique_files.values())
        
        return None
    
    async def _process_with_openai(self, user_id: str, user_message: str) -> str:
        """
        Processa mensagem do usuario com OpenAI API.
        
        args:
            user_id: ID de usuario da mensagem
            user_message: String de mensagem do usuario

        retorna String de resposta ou erro.
        """

        try:
            tom = await self.Helper.openai_service.classificar_tom_mensagem(user_message)
            print(f"🎨 [DEBUG] Tom detectado: {tom}")

            system_prompt = self.PromptAgent.generate_system_prompt(tom=tom)
            historico = self.Helper.conversation_history.format_for_prompt(user_id)

            resposta = await self.Helper.openai_service.gerar_resposta_geral(
                user_message=user_message,
                system_prompt=system_prompt,
                historico_formatado=historico,
                tom=tom
            )

            if resposta:
                return resposta
        except Exception as e:
            print(f"❌ Erro OpenAI: {e}")

        return OPENAI_FALLBACK_MESSAGE
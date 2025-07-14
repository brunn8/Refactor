
# 5. Importando modulos locais
from core import intent_router
from utils import helpers
from handlers import general_handler, boards_handler, file_handler

class Responder:
    """Agente que lida com respostas, direcionando cada pergunta a seu Handler designado."""

    def __init__(self, Helper: helpers.Helper, 
                 GeneralHandler: general_handler.GeneralHandler, 
                 BoardsHandler: boards_handler.BoardsHandler, 
                 FileHandler: file_handler.FileHandler) -> None:
        
        """Construtor do agente de respostas. Inicializando cada Handler e o interpretador."""

        self.IntentRouter = intent_router.IntentRouter(BoardsHandler)
        
        self.Helper = Helper
        self.GeneralHandler = GeneralHandler
        self.BoardsHandler = BoardsHandler
        self.FileHandler = FileHandler

    ###################
    # Funcoes publicas
    ###################

    async def answer(self, user_id: str, user_message: str, nome_usuario: str = "") -> str:
        """
        Processando mensagem do usuario e tratando em cada Handler designado.
        
        args:
            user_id: ID do usuario da mensagem
            user_message: String de mensagem do usuario
            nome_usuario: String de nome do usuario
        
        retorna uma String de resposta gerada
        """

        intent = self.IntentRouter._detect_intent(user_message,user_id)
        
        try:
            if intent == "admin":
                resposta = await self.GeneralHandler._handle_admin_commands(user_id, user_message)
            elif intent == "boards":
                resposta = await self.BoardsHandler._handle_boards_analysis(user_id, user_message)
            elif intent == "learning":
                resposta = self.GeneralHandler._handle_learning(user_id, user_message)
            elif intent == "file_list":
                quantidade = self.FileHandler._extract_quantity_listing(user_message)
                resposta = await self.FileHandler.list_files(user_id, user_message, user_message.lower(), quantidade)
            elif intent == "file":
                resposta = await self.FileHandler._handle_file_requests(user_id, user_message)
            elif intent == "greeting":
                resposta = self.GeneralHandler._handle_greetings(user_message)
            else:
                resposta = await self.GeneralHandler._handle_general_questions(user_id, user_message, nome_usuario)
            
        except Exception as e:
            resposta = self.Helper._handle_error_response(e, intent, user_id)
            
        return self.Helper._login_interaction(user_id, user_message, resposta)
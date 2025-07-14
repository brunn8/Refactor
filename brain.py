# 5. Importando modulos locais
from core import cache, responder
from utils import helpers
from handlers import general_handler, boards_handler, file_handler
from config import promts

class Sofia:
    """Sistema de IA conversacional Sofia - Assistente inteligente para gestão de conhecimento"""
 
    def __init__(self) -> None:
        self.CacheAgent = cache.CacheAgent()
        self.Helper = helpers.Helper()
        self.PromptAgent = promts.PromptAgent(self.Helper)

        self.BoardsHandler = boards_handler.BoardsHandler(self.CacheAgent)
        self.GeneralHandler = general_handler.GeneralHandler(self.CacheAgent, self.Helper, self.PromptAgent)
        self.FileHandler = file_handler.FileHandler(self.Helper, self.GeneralHandler)

        self.Responder = responder.Responder(self.Helper, self.GeneralHandler, self.BoardsHandler, self.FileHandler)   
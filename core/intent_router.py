# 1. Standard library imports
import re
from functools import lru_cache

# 4. Constants imports
from src.services.constants import (    
    # Patterns
    MAPA_TIPOS_ITENS, BOARDS_COMMANDS, LEARNING_TRIGGERS, LIST_PATTERNS,
    EXIT_COMMANDS, HELP_COMMANDS, ADMIN_COMMANDS, FILE_REQUEST_PATTERNS,
    FILE_KEYWORDS, ACTION_KEYWORDS, CASUAL_WORDS, POSITIVE_WORDS,
    FILE_CONTEXT_WORDS, CASUAL_INDICATORS, FILE_INTENT_INDICATORS,
    GREETING_WORDS, WELLBEING_PHRASES, COLLABORATOR_REFERENCES,
    PROGRESS_KEYWORDS, TODO_KEYWORDS, COMPLETED_KEYWORDS, OVERVIEW_KEYWORDS,
    OVERDUE_KEYWORDS, HIERARCHY_KEYWORDS, CLIENT_KEYWORDS, ACTIVITY_KEYWORDS,
    TASK_COUNT_KEYWORDS, BOARD_PROJECTS, CLIENT_SEARCH_KEYWORDS,
    REGEX_PATTERNS, URL_VALIDATION_PATTERNS, INVALID_URL_PATTERNS,
)

class IntentRouter:

    def __init__(self,BoardsHandler):
        self.modo_analise_boards = BoardsHandler.modo_analise_boards
        self.aprendizado_manual_ativo = BoardsHandler.aprendizado_manual_ativo

    @lru_cache(maxsize=256)
    def _calculate_file_score(self, message: str) -> float:
        message_lower = message.lower()
        score = 0.0
        
        if self.file_extension_pattern.search(message):
            score += 0.5
        
        score += sum(0.2 for keyword in FILE_KEYWORDS if keyword in message_lower)
        score += sum(0.15 for keyword in ACTION_KEYWORDS if keyword in message_lower)
        
        if self.file_naming_pattern.search(message):
            score += 0.2
        
        score -= sum(0.2 for word in CASUAL_WORDS if word in message_lower)
        
        return max(min(score, 1.0), 0.0)

    def _compile_regex_patterns(self):
        self.file_extension_pattern = re.compile(
            REGEX_PATTERNS['file_extension'], 
            re.IGNORECASE
        )
        self.file_naming_pattern = re.compile(REGEX_PATTERNS['file_naming'])
        self.greeting_pattern = re.compile(
            REGEX_PATTERNS['greeting'],
            re.IGNORECASE
        )

    def _detect_intent(self, message: str, user_id: str) -> str:
        message_lower = message.lower().strip()
        
        if any(cmd in message_lower for cmd in ADMIN_COMMANDS.keys()):
            return "admin"
        
        if any(cmd in message_lower for cmd in BOARDS_COMMANDS) or user_id in self.modo_analise_boards:
            return "boards"
        
        if any(trigger in message_lower for trigger in LEARNING_TRIGGERS) or user_id in self.aprendizado_manual_ativo:
            return "learning"
        
        if any(pattern in message_lower for pattern in LIST_PATTERNS):
            return "file_list"
        
        if len(message.split()) <= 6 and self.greeting_pattern.search(message):
            return "greeting"
        
        if self._calculate_file_score(message) > 0.7:
            return "file"
        
        return "general"
    


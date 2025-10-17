from typing import Dict, Callable, Awaitable
from telegram import Update
from telegram.ext import ContextTypes
import logging
import re

logger = logging.getLogger(__name__)

CallbackHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]

class CommandRegistry:
    """Registry для callback handlers с поддержкой паттернов"""
    
    def __init__(self):
        self._exact_commands: Dict[str, CallbackHandler] = {}
        self._pattern_commands: Dict[re.Pattern, CallbackHandler] = {}
    
    def register(self, pattern: str, handler: CallbackHandler):
        """Регистрация handler для pattern"""
        if '*' in pattern or '?' in pattern or '[' in pattern:
            # Pattern with wildcards - compile as regex
            regex_pattern = pattern.replace('*', '.*')
            compiled = re.compile(f"^{regex_pattern}$")
            self._pattern_commands[compiled] = handler
        else:
            # Exact match
            self._exact_commands[pattern] = handler
    
    async def dispatch(self, callback_data: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dispatch callback к соответствующему handler"""
        # Try exact match first
        if callback_data in self._exact_commands:
            handler = self._exact_commands[callback_data]
            await handler(update, context)
            return True
        
        # Try pattern match
        for pattern, handler in self._pattern_commands.items():
            if pattern.match(callback_data):
                await handler(update, context)
                return True
        
        logger.warning(f"No handler found for callback: {callback_data}")
        return False

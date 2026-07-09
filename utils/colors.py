# utils/colors.py   Цвета ддя вывода
from colorama import Fore, Style, init

# Инициализация colorama (для Windows обязательно)
init(autoreset=True)


class C:
    """Цветовые константы для красивого вывода"""
    # Заголовки и границы
    HEADER = Fore.MAGENTA + Style.BRIGHT
    BORDER = Fore.MAGENTA
    
    # Роли
    USER = Fore.GREEN + Style.BRIGHT
    AGENT = Fore.CYAN + Style.BRIGHT
    SYSTEM = Fore.WHITE + Style.DIM
    
    # Инструменты
    TOOL_CALL = Fore.YELLOW + Style.BRIGHT
    TOOL_RESULT = Fore.MAGENTA
    TOOL_ERROR = Fore.RED + Style.BRIGHT
    
    # Ответы
    FINAL = Fore.WHITE + Style.BRIGHT
    
    # Служебное
    ITERATION = Fore.BLUE + Style.BRIGHT
    ERROR = Fore.RED + Style.BRIGHT
    DEBUG = Fore.WHITE + Style.DIM
    
    # Сброс (обычно не нужен из-за autoreset=True)
    RESET = Style.RESET_ALL
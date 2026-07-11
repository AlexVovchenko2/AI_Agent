# agent/prompts.py
from pathlib import Path
from datetime import datetime

PROMPTS_DIR = Path("./prompts")

def load_prompt(template_name: str, **kwargs) -> str:
    """
    Загружает .md шаблон и подставляет переменные.
    
    Args:
        template_name: Имя файла без расширения (например, 'system')
        **kwargs: Переменные для подстановки (например, user_timezone='UTC+3')
    
    Returns:
        Готовый промпт с подставленными значениями
    """
    template_path = PROMPTS_DIR / f"{template_name}.md"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    
    template = template_path.read_text(encoding="utf-8")
    
    # Подстановка переменных
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        template = template.replace(placeholder, str(value))
    
    return template

def get_system_prompt(available_tools: list, user_timezone: str = "UTC") -> str:
    """
    Генерирует системный промпт с текущим контекстом.
    """
    # Формируем список доступных тулов
    tools_list = "\n".join([f"- {tool['function']['name']}: {tool['function']['description']}" 
                            for tool in available_tools])
    
    # Текущая дата
    current_date = datetime.now().strftime("%Y-%m-%d (%A)")
    
    # Загружаем шаблон
    return load_prompt(
        "system",
        available_tools=tools_list,
        user_timezone=user_timezone,
        current_date=current_date
    )
# agent/prompts.py
from pathlib import Path
from datetime import datetime
from config import WORKSPACE_ROOT, USER_TIMEZONE, AGENT_ROOT

PROMPTS_DIR = AGENT_ROOT / "prompts" 
def load_prompt(template_name: str, **kwargs) -> str:
    """Загружает .md шаблон и подставляет переменные."""
    template_path = PROMPTS_DIR / f"{template_name}.md"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    
    template = template_path.read_text(encoding="utf-8")
    
    # Подстановка переменных
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        template = template.replace(placeholder, str(value))
    
    return template

def get_system_prompt(
    available_tools: list,
    user_timezone: str = None,
    workspace_root: str = None
) -> str:
    """
    Генерирует системный промпт с текущим контекстом.
    
    Args:
        available_tools: Список схем инструментов
        user_timezone: Часовой пояс (опционально, по умолчанию из config)
        workspace_root: Путь к workspace (опционально, по умолчанию из config)
    
    Returns:
        Готовый системный промпт
    """
    # Используем переданные значения или дефолтные из config
    tz = user_timezone if user_timezone else USER_TIMEZONE
    ws = workspace_root if workspace_root else str(WORKSPACE_ROOT)
    
    # Формируем список доступных тулов
    tools_list = "\n".join([
        f"- {tool['function']['name']}: {tool['function']['description']}" 
        for tool in available_tools
    ])
    
    # Текущая дата
    current_date = datetime.now().strftime("%Y-%m-%d (%A)")
    
    # Загружаем шаблон
    return load_prompt(
        "system",
        workspace_root=ws,
        available_tools=tools_list,
        user_timezone=tz,
        current_date=current_date
    )
# tools/time_tool.py    Реализует получение текущего времени
from datetime import datetime, timezone

# JSON-схема для LLM
time_tool_json = {
    "type": "function", 
    "function": {
        "name": "get_current_time",
        "description": "Get the current date and time in UTC (Coordinated Universal Time / Greenwich Mean Time). Use this when you need to know what time it is now or what today's date is. The result is always in UTC timezone.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


def current_time_handler() -> str:
    """Возвращает текущую дату и время в читаемом фоормате"""
    now = datetime.now(timezone.utc)
    return now.strftime("%d/%m/%Y, %H:%M:%S UTC (%A)")

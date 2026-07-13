# tools/registry.py     Диспетчер инструментов
from .time_tool import time_tool_json, current_time_handler
from .file_manager import (
    file_manager_json, validate_path, read_file_handler, 
    write_file_handler, list_dir_handler, delete_file_handler, 
    get_workspace_structure_handler, create_directory_handler
    )

# список всех доступных тулов
tools_json = [
    time_tool_json, 
    *file_manager_json
]

# маппинг: имя функции <=> реальное имя в Python-коде
tool_map = {
    "get_current_time": current_time_handler,
    "read_file": read_file_handler,
    "write_file": write_file_handler,
    "list_directory": list_dir_handler,
    "delete_file": delete_file_handler,
    "get_workspace_structure": get_workspace_structure_handler,
    "create_directory": create_directory_handler
}


def execute_tool(tool_name: str, args: dict) -> str:
    """Выполняет инструмент <name> и возвращает результат в виде строки
    Аргументы:
        tool_name - имя функции
        args - аргументы функции (parameters)
    """

    if tool_name not in tool_map: return f"Ошибка: инструмент {tool_name} не найден!"
    
    try:
        result = tool_map[tool_name](**args)
        return str(result)
    except Exception as e:
        return f"Ошибка во время работы инструмента {tool_name}: {str(e)}"
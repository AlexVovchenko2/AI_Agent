# config.py
from pathlib import Path
import time
import os

# Путь к модели
MODEL_PATH = Path("./models/Qwen2.5-7B-Instruct-GGUF/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf")

# Параметры модели (под GTX 1650 Ti 4GB)
LLM_CONFIG = {
    "n_gpu_layers": 20,
    "n_ctx": 2048,
    "temperature": 0.1,
    "verbose": False
}

# Рабочая директория (устанавливается в main.py)
WORKSPACE_ROOT: Path = None

# Параметры агента
MAX_ITERATIONS = 10

# Часовой пояс пользователя
try:
    USER_TIMEZONE = time.tzname[0]  # Например, 'MSK'
    USER_UTC_OFFSET = -time.timezone // 3600  # Например, 3 для UTC+3
except:
    USER_TIMEZONE = "UTC"
    USER_UTC_OFFSET = 0

# Запрещённые директории (системные)
FORBIDDEN_PATHS = [
    Path("C:/"),
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/Users"),
    Path("/"),
    Path("/home"),
    Path("/etc"),
    Path("/usr"),
    Path("/var"),
]

def validate_workspace(path_str: str) -> Path:
    """
    Валидирует путь к рабочей директории.
    
    Args:
        path_str: Строка с путём
    
    Returns:
        Нормализованный Path объект
    
    Raises:
        ValueError: Если путь небезопасный
    """
    # Нормализуем путь
    path = Path(path_str).resolve()
    
    # Проверяем, что путь существует
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")
    
    # Проверяем, что это директория
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    # Проверяем, что путь не в запрещённом списке
    for forbidden in FORBIDDEN_PATHS:
        try:
            path.relative_to(forbidden)
            # Если путь внутри forbidden или равен ему
            if path == forbidden or len(path.relative_to(forbidden).parts) == 0:
                raise ValueError(
                    f"Access denied: '{path}' is a system directory. "
                    f"Choose a project folder instead."
                )
        except ValueError as e:
            if "Access denied" in str(e):
                raise
            continue
    
    # Проверяем права записи
    test_file = path / ".test_write_permission"
    try:
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        raise ValueError(f"No write permission for: {path}")
    
    return path

def set_workspace(path_str: str) -> Path:
    """Устанавливает рабочую директорию после валидации."""
    global WORKSPACE_ROOT
    WORKSPACE_ROOT = validate_workspace(path_str)
    return WORKSPACE_ROOT

def get_workspace() -> Path:
    """Возвращает текущую рабочую директорию."""
    if WORKSPACE_ROOT is None:
        raise ValueError("Workspace root is not set! Call set_workspace() first.")
    return WORKSPACE_ROOT
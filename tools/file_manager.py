# tools/file_manager.py
from pathlib import Path
import subprocess

# Корневая директория "песочницы"
WORKSPACE_ROOT = Path("./workspace").resolve()

# Разрешённые операции
ALLOWED_OPERATIONS = {
    "read": ["cat", "type", "head", "tail"],
    "write": ["echo", "write"],
    "list": ["ls", "dir"],
    "delete": ["rm", "del"],
    "info": ["stat", "wc"]
}

def validate_path(filepath: str) -> Path:
    """
    Проверяет, что путь внутри workspace.
    Возвращает нормализованный Path или raises ValueError.
    """
    # Нормализуем путь (убираем .., ., etc.)
    path = Path(filepath).resolve()
    
    # Проверяем, что путь внутри workspace
    try:
        path.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise ValueError(
            f"Access denied: '{filepath}' is outside workspace. "
            f"Use only paths inside ./workspace/"
        )
    
    return path

def read_file_handler(filepath: str) -> str:
    """Читает файл из workspace."""
    try:
        path = validate_path(filepath)
        if not path.exists():
            return f"Error: file '{filepath}' does not exist"
        if not path.is_file():
            return f"Error: '{filepath}' is not a file"
        
        content = path.read_text(encoding="utf-8")
        return content
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error reading file: {e}"

def write_file_handler(filepath: str, content: str, mode: str = "write") -> str:
    """Записывает файл в workspace/output/."""
    try:
        # Разрешаем запись только в output/
        output_dir = WORKSPACE_ROOT / "output"
        path = (output_dir / filepath).resolve()
        
        # Проверяем, что путь внутри output/
        try:
            path.relative_to(output_dir)
        except ValueError:
            return f"Error: writing allowed only in ./workspace/output/"
        
        # Создаём директорию
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup перед перезаписью
        if path.exists() and mode == "write":
            backup = path.with_suffix(path.suffix + ".backup")
            path.rename(backup)
        
        # Записываем
        write_mode = "w" if mode == "write" else "a"
        path.write_text(content, encoding="utf-8")
        
        return f"Successfully wrote to {path.relative_to(WORKSPACE_ROOT)}"
    except Exception as e:
        return f"Error writing file: {e}"

def list_dir_handler(dirpath: str = ".") -> str:
    """Показывает содержимое директории в workspace."""
    try:
        path = validate_path(dirpath)
        if not path.exists():
            return f"Error: directory '{dirpath}' does not exist"
        if not path.is_dir():
            return f"Error: '{dirpath}' is not a directory"
        
        items = []
        for item in sorted(path.iterdir()):
            prefix = "📁" if item.is_dir() else "📄"
            items.append(f"{prefix} {item.name}")
        
        return "\n".join(items) if items else "(empty directory)"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error listing directory: {e}"

def delete_file_handler(filepath: str) -> str:
    """Удаляет файл из workspace/output/."""
    try:
        output_dir = WORKSPACE_ROOT / "output"
        path = (output_dir / filepath).resolve()
        
        # Проверяем, что путь внутри output/
        try:
            path.relative_to(output_dir)
        except ValueError:
            return f"Error: deletion allowed only in ./workspace/output/"
        
        if not path.exists():
            return f"Error: file '{filepath}' does not exist"
        
        path.unlink()
        return f"Deleted {filepath}"
    except Exception as e:
        return f"Error deleting file: {e}"

# JSON-схемы для LLM
file_manager_schemas = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content of a file from workspace/input/ directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path like 'input/data.txt'"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in workspace/output/ directory. Creates backup before overwriting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path like 'result.txt'"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "write = overwrite (with backup), append = add to end"
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories in workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Relative path like 'input/' or '.' for root"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from workspace/output/ directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path like 'result.txt'"
                    }
                },
                "required": ["filepath"]
            }
        }
    }
]
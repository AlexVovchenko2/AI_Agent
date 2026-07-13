# tools/file_manager.py
from pathlib import Path
from config import get_workspace

# JSON-схемы для LLM
file_manager_json = [
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Create a new directory. Creates all missing parent directories automatically. Use this instead of creating dummy files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Relative path to the directory to create. Example: 'src/utils', 'A1/B2'"
                    }
                },
                "required": ["dirpath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Automatically creates all missing parent directories. DO NOT create dummy files to make directories exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path. Example: 'src/main.cpp'"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write. Use \\n for newlines. NEVER use triple quotes."
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "write = overwrite, append = add to end"
                    },
                    "create_backup": {
                        "type": "boolean",
                        "description": "If true and file exists, creates a .backup copy before overwriting. Default is false."
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content of a file from the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path from workspace root. Example: 'src/main.cpp', 'data.txt'"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Relative path from workspace root. Use '.' for root directory."
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
            "description": "Delete a file from the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Relative path from workspace root."
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_workspace_structure",
            "description": "Get the current directory tree structure of the workspace. Use this BEFORE writing files to understand the layout.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def create_directory_handler(dirpath: str) -> str:
    """Создаёт директорию (и все родительские, если их нет)."""
    try:
        path = validate_path(dirpath)
        path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory: {dirpath}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error creating directory: {e}"


def validate_path(filepath: str) -> Path:
    """
    Проверяет, что путь внутри WORKSPACE_ROOT.
    """
    workspace_root = get_workspace()
    
    # ВАЖНО: сначала склеиваем с корнем, потом делаем абсолютным
    path = (workspace_root / filepath).resolve()
    
    # Проверяем, что итоговый путь всё ещё внутри workspace
    try:
        path.relative_to(workspace_root)
    except ValueError:
        raise ValueError(
            f"Access denied: '{filepath}' is outside workspace. "
            f"Use only relative paths inside {workspace_root}"
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


def write_file_handler(filepath: str, content: str, mode: str = "write", create_backup: bool = False) -> str:
    """Записывает файл в workspace."""
    try:
        path = validate_path(filepath)
        
        # ВАЖНО: создаём директории автоматически
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Логика бэкапа (исправлена для Windows)
        if path.exists() and mode == "write" and create_backup:
            backup_path = path.with_suffix(path.suffix + ".backup")
            # replace() перезаписывает файл, в отличие от rename() на Windows
            path.replace(backup_path) 
        
        # Записываем
        write_mode = "w" if mode == "write" else "a"
        path.write_text(content, encoding="utf-8")
        
        return f"Successfully wrote to {filepath}"
    except ValueError as e:
        return str(e)
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
    """Удаляет файл из workspace."""
    try:
        path = validate_path(filepath)
        if not path.exists():
            return f"Error: file '{filepath}' does not exist"
        if not path.is_file():
            return f"Error: '{filepath}' is not a file"
        
        path.unlink()
        return f"Deleted {filepath}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error deleting file: {e}"


def get_workspace_structure_handler() -> str:
    """Возвращает дерево директорий и файлов workspace."""

    workspace_root = get_workspace()

    if workspace_root is None:
        return "Error: Workspace root is not set!"
    
    tree = []
    for path in sorted(workspace_root.rglob("*")):
        depth = len(path.relative_to(workspace_root).parts)
        indent = "    " * depth
        
        if path.is_dir():
            tree.append(f"{indent}📁 {path.name}/")
        else:
            tree.append(f"{indent} {path.name}")
    
    return "\n".join(tree) if tree else "Workspace is empty."
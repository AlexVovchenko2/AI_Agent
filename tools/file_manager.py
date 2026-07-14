# tools/file_manager.py
from pathlib import Path
from config import get_workspace

# JSON-схемы для LLM (оставляем как есть, они отличные)
file_manager_json = [
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Create a new directory. Creates all missing parent directories automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {"type": "string", "description": "Relative path. Example: 'src/utils'"}
                },
                "required": ["dirpath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Automatically creates all missing parent directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path. Example: 'src/main.kt'"},
                    "content": {"type": "string", "description": "Content to write. Use \\n for newlines."},
                    "mode": {"type": "string", "enum": ["write", "append"], "description": "write = overwrite, append = add to end"},
                    "create_backup": {"type": "boolean", "description": "If true, creates a .backup copy before overwriting."}
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
                    "filepath": {"type": "string", "description": "Relative path from workspace root."}
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
                    "dirpath": {"type": "string", "description": "Relative path. Use '.' for root."}
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
                    "filepath": {"type": "string", "description": "Relative path from workspace root."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_workspace_structure",
            "description": "Get the current directory tree structure of the workspace (max 4 levels deep).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]


def validate_path(filepath: str) -> Path:
    workspace_root = get_workspace()
    path = (workspace_root / filepath).resolve()
    
    try:
        path.relative_to(workspace_root)
    except ValueError:
        raise ValueError(f"Access denied: '{filepath}' is outside workspace.")
    
    return path


def write_file_handler(filepath: str, content: str, mode: str = "write", create_backup: bool = False) -> str:
    """Записывает файл в workspace."""
    try:
        path = validate_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.exists() and mode == "write" and create_backup:
            backup_path = path.with_suffix(path.suffix + ".backup")
            path.replace(backup_path) 
        
        write_mode = "w" if mode == "write" else "a"
        with open(path, write_mode, encoding="utf-8") as f:
            f.write(content)
        
        # ✅ FIX 1: Возвращаем АБСОЛЮТНЫЙ путь и размер. Это заставляет LLM остановиться.
        return f"SUCCESS: File written. Absolute path: {path.resolve()}. Bytes written: {len(content.encode('utf-8'))}."
        
    except ValueError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: Failed to write file. Details: {str(e)}"


def read_file_handler(filepath: str) -> str:
    try:
        path = validate_path(filepath)
        if not path.exists():
            return f"ERROR: File '{filepath}' does not exist"
        if not path.is_file():
            return f"ERROR: '{filepath}' is not a file"
        
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR: {str(e)}"


def list_dir_handler(dirpath: str = ".") -> str:
    try:
        path = validate_path(dirpath)
        if not path.exists() or not path.is_dir():
            return f"ERROR: Directory '{dirpath}' does not exist"
        
        items = []
        for item in sorted(path.iterdir()):
            prefix = "📁" if item.is_dir() else "📄"
            items.append(f"{prefix} {item.name}")
        
        return "\n".join(items) if items else "(empty directory)"
    except Exception as e:
        return f"ERROR: {str(e)}"


def delete_file_handler(filepath: str) -> str:
    try:
        path = validate_path(filepath)
        if not path.exists() or not path.is_file():
            return f"ERROR: File '{filepath}' does not exist"
        
        path.unlink()
        return f"SUCCESS: Deleted {filepath}"
    except Exception as e:
        return f"ERROR: {str(e)}"


def get_workspace_structure_handler() -> str:
    """Возвращает дерево директорий (ОГРАНИЧЕНО 4 уровнями глубины для защиты контекста)."""
    workspace_root = get_workspace()
    if workspace_root is None:
        return "ERROR: Workspace root is not set!"
    
    tree = []
    max_depth = 4 # ✅ FIX 2: Защита от переполнения контекста в больших проектах
    
    for path in sorted(workspace_root.rglob("*")):
        relative_parts = path.relative_to(workspace_root).parts
        if len(relative_parts) > max_depth:
            continue # Пропускаем слишком глубокие файлы (например, node_modules)
            
        depth = len(relative_parts)
        indent = "    " * depth
        
        if path.is_dir():
            tree.append(f"{indent}📁 {path.name}/")
        else:
            tree.append(f"{indent}📄 {path.name}")
    
    return "\n".join(tree) if tree else "Workspace is empty."


def create_directory_handler(dirpath: str) -> str:
    try:
        path = validate_path(dirpath)
        path.mkdir(parents=True, exist_ok=True)
        return f"SUCCESS: Created directory. Absolute path: {path.resolve()}"
    except Exception as e:
        return f"ERROR: {str(e)}"
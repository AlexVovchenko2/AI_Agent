# main.py
from llama_cpp import Llama
from config import MODEL_PATH, LLM_CONFIG, set_workspace
from agent.core import run_agent
from utils.colors import C
from pathlib import Path


def get_workspace_from_user() -> Path:
    """Запрашивает у пользователя рабочую директорию."""
    print(f"\n{C.HEADER}{'=' * 70}")
    print(f"{C.HEADER} { 'НАСТРОЙКА РАБОЧЕЙ ДИРЕКТОРИИ'} ")
    print(f"{C.HEADER}{'=' * 70}{C.RESET}\n")
    
    # Показываем текущую директорию как подсказку
    current_dir = Path.cwd()
    print(f"{C.SYSTEM}Текущая директория: {current_dir}{C.RESET}")
    print(f"{C.SYSTEM}Введите путь к проекту (или нажмите Enter для текущей):{C.RESET}\n")
    
    while True:
        try:
            user_input = input(f"{C.USER}Путь: {C.RESET}").strip()
            
            # Если пустой ввод — используем текущую директорию
            if not user_input:
                workspace = current_dir
            else:
                # Пробуем валидировать
                workspace = set_workspace(user_input)
            
            print(f"\n{C.TOOL_RESULT}✓ Рабочая директория: {workspace}{C.RESET}\n")
            return workspace
            
        except ValueError as e:
            print(f"\n{C.TOOL_ERROR}✗ Ошибка: {e}{C.RESET}")
            print(f"{C.SYSTEM}Попробуйте другой путь.{C.RESET}\n")
        except KeyboardInterrupt:
            print(f"\n{C.ERROR}Прервано. До свидания!{C.RESET}")
            exit(0)


def main():

    workspace = get_workspace_from_user()

    print(f"{C.HEADER}{'=' * 70}")
    print(f"{C.HEADER}{'ЗАГРУЗКА МОДЕЛИ...'}")
    print(f"{C.HEADER}{'=' * 70}{C.RESET}")
    
    llm = Llama(
        model_path=str(MODEL_PATH),
        **LLM_CONFIG
    )
    
    print(f"{C.HEADER}{'=' * 70}")
    print(f"{C.HEADER} { 'МОДЕЛЬ УСПЕШНО ЗАГРУЖЕНА!' }")
    print(f"{C.HEADER}{'=' * 70}{C.RESET}")
    
    print(f"\n{C.AGENT}Агент готов. Рабочая директория: {workspace}{C.RESET}")
    print(f"{C.SYSTEM}Доступные инструменты: get_current_time{C.RESET}\n")
    
    while True:
        try:
            # Цветное приглашение
            user_input = input(f"{C.USER}Пользователь: {C.RESET}").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q', 'выход']:
                print(f"\n{C.HEADER}До свидания!{C.RESET}")
                break
            
            # Запускаем агента
            response = run_agent(llm, user_input)
            
            # Красивый финальный ответ
            print(f"\n{C.HEADER}{'─' * 70}{C.RESET}")
            print(f"{C.FINAL}{response}{C.RESET}")
            print(f"{C.HEADER}{'─' * 70}{C.RESET}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{C.ERROR}Прервано пользователем. До свидания!{C.RESET}")
            break
        except Exception as e:
            print(f"\n{C.ERROR}Ошибка: {e}{C.RESET}")


if __name__ == "__main__":
    main()
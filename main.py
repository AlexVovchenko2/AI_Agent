# main.py
from llama_cpp import Llama
from config import MODEL_PATH, LLM_CONFIG
from agent.core import run_agent
from utils.colors import C


def main():
    print(f"{C.HEADER}{'=' * 70}")
    print(f"  ЗАГРУЗКА МОДЕЛИ...")
    print(f"{'=' * 70}{C.RESET}")
    
    llm = Llama(
        model_path=str(MODEL_PATH),
        **LLM_CONFIG
    )
    
    print(f"{C.HEADER}{'=' * 70}")
    print(f"  МОДЕЛЬ УСПЕШНО ЗАГРУЖЕНА!")
    print(f"{'=' * 70}{C.RESET}")
    
    print(f"\n{C.AGENT}Агент готов. Напишите 'exit' для выхода{C.RESET}")
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
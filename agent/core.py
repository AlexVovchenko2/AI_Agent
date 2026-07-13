# agent/core.py     Основная логика работы агента

from llama_cpp import Llama
from tools.registry import tools_json, execute_tool
from agent.prompts import get_system_prompt
from utils.colors import C
from config import USER_TIMEZONE, get_workspace, MAX_ITERATIONS
import json
import re


def extract_tool_calls_from_text(text: str) -> list:
    """
    Извлекает вызовы инструментов из текстового ответа модели.
    Обрабатывает форматы:
    - <tool_call>{"name": "...", "arguments": {...}}</tool_call>
    - {"name": "...", "arguments": {...}} (голый JSON)
    
    Также нормализует двойные скобки {{ }} → { }, которые появляются
    из-за особенностей chat template Qwen.
    """
    tool_calls = []
    
    # Нормализуем текст: заменяем {{ на { и }} на }
    normalized_text = text.replace('{{', '{').replace('}}', '}')
    normalized_text = normalized_text.replace('"""', '"')

    # Паттерн 1: теги <tool_call>...</tool_call>
    pattern = r'<tool_call>\s*({.*?})\s*</tool_call>'
    matches = re.findall(pattern, normalized_text, re.DOTALL)
    
    if matches:
        for match in matches:
            try:
                tool_data = json.loads(match)
                if "name" in tool_data:
                    tool_calls.append({
                        "function": {
                            "name": tool_data["name"],
                            "arguments": json.dumps(tool_data.get("arguments", {}))
                        },
                        "id": f"call_{len(tool_calls)}"
                    })
            except json.JSONDecodeError as e:
                print(f"{C.DEBUG}[DEBUG] JSON parse error: {e}{C.RESET}")
                print(f"{C.DEBUG}[DEBUG] Failed to parse: {match}{C.RESET}")
                continue
        return tool_calls
    
    # Паттерн 2: голый JSON в тексте (fallback)
    try:
        json_pattern = r'{[^{}]*"name"[^{}]*"arguments"[^{}]*}'
        json_matches = re.findall(json_pattern, normalized_text)
        for match in json_matches:
            try:
                tool_data = json.loads(match)
                if "name" in tool_data:
                    tool_calls.append({
                        "function": {
                            "name": tool_data["name"],
                            "arguments": json.dumps(tool_data.get("arguments", {}))
                        },
                        "id": f"call_{len(tool_calls)}"
                    })
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    
    return tool_calls


def clean_tool_call_text(text: str) -> str:
    """Удаляет вызовы инструментов из текста для финального ответа."""
    normalized = text.replace('{{', '{').replace('}}', '}')
    normalized = re.sub(r'<tool_call>.*?</tool_call>', '', normalized, flags=re.DOTALL)
    normalized = re.sub(r'{[^{}]*"name"[^{}]*"arguments"[^{}]*}', '', normalized)
    return normalized.strip()


def run_agent(llm: Llama, user_input: str, max_iterations: int = MAX_ITERATIONS) -> str:
    """Запускает основной цикл агента
    
    Аргументы:
        llm - экземпляр модели
        user_input - юзерпромпт
        max_iterations - защита от бесконечного цикла

    Возвращает финальный ответ агента
    """

    # Генерируем системный промпт
    system_prompt = get_system_prompt(
        available_tools=tools_json,
        user_timezone=USER_TIMEZONE,  
        workspace_root=get_workspace()
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    # Основной цикл
    for iter in range(max_iterations):
        # Красивый заголовок итерации
        print(f"\n{C.ITERATION}{'#' * 70}{C.RESET}")
        print(f"{C.ITERATION}{'Iteration ' + str(iter + 1) + ' of ' + str(max_iterations):^70}{C.RESET}")
        print(f"{C.ITERATION}{'#' * 70}{C.RESET}")

        response = llm.create_chat_completion(
            messages=messages,
            tools=tools_json,
            tool_choice='auto',
            temperature=0.1
        )

        assistant_message = response["choices"][0]["message"]
        raw_content = assistant_message.get("content") or ""

        # Пытаемся извлечь вызовы инструментов из текста
        tool_calls = extract_tool_calls_from_text(raw_content)
        
        # Также проверяем нативный tool_calls
        native_tool_calls = assistant_message.get("tool_calls", [])
        
        # Объединяем оба источника
        all_tool_calls = tool_calls + (native_tool_calls or [])

        if all_tool_calls:
            clean_content = clean_tool_call_text(raw_content)
            
            messages.append({
                "role": "assistant",
                "content": clean_content if clean_content else ""
            })

            # Красивый вывод вызовов инструментов
            print(f"\n{C.AGENT}[AGENT]:{C.RESET} Модель хочет использовать инструменты:")

            for tool_call in all_tool_calls:
                func_name = tool_call["function"]["name"]

                try:
                    func_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                print(f"  {C.TOOL_CALL} [TOOL]: Вызов{C.RESET} {func_name}({func_args})")

                tool_result = execute_tool(func_name, func_args)
                
                # Разный цвет для результата и ошибки
                if str(tool_result).startswith("Ошибка"):
                    print(f"  {C.TOOL_ERROR}[TOOL]: Результат - {C.RESET} {tool_result}")
                else:
                    print(f"  {C.TOOL_RESULT}[TOOL]: Результат - {C.RESET} {tool_result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(tool_result)
                })

        else:
            # Финальный ответ
            messages.append({
                "role": "assistant",
                "content": raw_content
            })
            print(f"\n{C.AGENT}[FINAL ANSWER]:{C.RESET}")
            return raw_content
        
    return f"{C.ERROR}Error: maximum iterations reached. Agent could not complete the task.{C.RESET}"
# agent/core.py
from llama_cpp import Llama
from tools.registry import tools_json, execute_tool
from agent.prompts import get_system_prompt
from utils.colors import C
from config import USER_TIMEZONE, get_workspace, MAX_ITERATIONS
import json
import re

def extract_and_parse_tool_calls(text: str):
    """
    Извлекает вызовы инструментов. 
    Возвращает: (список tool_calls, строка_ошибки_или_None)
    ВАЖНО: Если инструментов нет, это НЕ ошибка (это может быть финальный ответ).
    """
    normalized_text = text.replace('{{', '{').replace('}}', '}')
    
    # Ищем теги или markdown блоки
    pattern_tags = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
    matches = re.findall(pattern_tags, normalized_text, re.DOTALL)
    
    if not matches:
        pattern_md = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(pattern_md, normalized_text, re.DOTALL)
        
    if not matches:
        start = normalized_text.find('{')
        end = normalized_text.rfind('}')
        if start != -1 and end != -1 and end > start and '"name"' in normalized_text[start:end]:
            matches = [normalized_text[start:end+1]]

    # Если вообще ничего похожего на JSON нет, это НЕ ошибка. Это финальный ответ.
    if not matches:
        return [], None

    # А вот если мы нашли что-то похожее на инструмент, но не можем это распарсить, это ОШИБКА.
    parsed_calls = []
    for i, match in enumerate(matches):
        repaired_match = match.replace('\$', '\\$').replace('\n', '\\n')
        
        try:
            tool_data = json.loads(repaired_match)
            if "name" in tool_data:
                parsed_calls.append({
                    "function": {
                        "name": tool_data["name"],
                        "arguments": json.dumps(tool_data.get("arguments", {}))
                    },
                    "id": f"call_{i}"
                })
        except json.JSONDecodeError as e:
            # Вот это реальная ошибка: модель пыталась вызвать инструмент, но сломала JSON
            return [], f"JSON Parse Error: {str(e)}. Raw snippet: {match[:150]}..."

    return parsed_calls, None


def clean_tool_call_text(text: str) -> str:
    """Удаляет вызовы инструментов из текста для финального ответа."""
    normalized = text.replace('{{', '{').replace('}}', '}')
    normalized = re.sub(r'<tool_call>.*?</tool_call>', '', normalized, flags=re.DOTALL)
    # Грубая очистка от голых JSON, если они остались
    normalized = re.sub(r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}', '', normalized)
    return normalized.strip()


def run_agent(llm: Llama, user_input: str, max_iterations: int = MAX_ITERATIONS) -> str:
    system_prompt = get_system_prompt(
        available_tools=tools_json,
        user_timezone=USER_TIMEZONE,  
        workspace_root=get_workspace()
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    for iteration in range(max_iterations):
        print(f"\n{C.ITERATION}{'#' * 70}{C.RESET}")
        print(f"{C.ITERATION}{'Iteration ' + str(iteration + 1) + ' of ' + str(max_iterations):^70}{C.RESET}")
        print(f"{C.ITERATION}{'#' * 70}{C.RESET}")

        response = llm.create_chat_completion(
            messages=messages,
            tools=tools_json,
            tool_choice='auto',
            temperature=0.1
        )

        assistant_message = response["choices"][0]["message"]
        raw_content = assistant_message.get("content") or ""

        parsed_tool_calls, parse_error = extract_and_parse_tool_calls(raw_content)
        native_tool_calls = assistant_message.get("tool_calls", [])
        
        all_tool_calls = native_tool_calls if native_tool_calls else parsed_tool_calls

        # 1. Если была ошибка парсинга (модель пыталась, но сломала JSON)
        if parse_error:
            print(f"\n{C.TOOL_ERROR}[ERROR]: {parse_error}{C.RESET}")
            print(f"{C.AGENT}[AGENT]: Отправляю ошибку модели для исправления...{C.RESET}")
            
            messages.append({
                "role": "user",
                "content": f"CRITICAL ERROR: Your tool call JSON was invalid.\nError: {parse_error}\nFix it and try again."
            })
            continue

        # 2. Если инструменты есть, выполняем их
        if all_tool_calls:
            clean_content = re.sub(r'<tool_call>.*?</tool_call>', '', raw_content, flags=re.DOTALL).strip()
            
            messages.append({
                "role": "assistant",
                "content": clean_content if clean_content else ""
            })

            print(f"\n{C.AGENT}[AGENT]:{C.RESET} Модель использует инструменты:")

            for tool_call in all_tool_calls:
                func_name = tool_call["function"]["name"]
                try:
                    func_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                print(f"  {C.TOOL_CALL}[TOOL]: Вызов{C.RESET} {func_name}({func_args})")

                tool_result = execute_tool(func_name, func_args)
                
                if str(tool_result).startswith("ERROR") or str(tool_result).startswith("Ошибка"):
                    print(f"  {C.TOOL_ERROR}[TOOL]: Результат - {C.RESET}{tool_result}")
                else:
                    print(f"  {C.TOOL_RESULT}[TOOL]: Результат - {C.RESET}{tool_result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", "unknown_id"),
                    "content": str(tool_result)
                })

        # 3. ЕСЛИ ИНСТРУМЕНТОВ НЕТ И НЕТ ОШИБКИ — ЭТО ФИНАЛЬНЫЙ ОТВЕТ!
        else:
            print(f"\n{C.AGENT}[FINAL ANSWER]:{C.RESET}")
            return raw_content
        
    return f"{C.ERROR}Error: maximum iterations ({max_iterations}) reached.{C.RESET}"
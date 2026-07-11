#config.py   Конфигурация модели

from pathlib import Path
import time

MODEL_PATH = Path("./models/Qwen2.5-7B-Instruct-GGUF/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf")

LLM_CONFIG = {
    "n_gpu_layers": 20,     # количество слоёв модели, которые загружаются на видеокарту
    "n_ctx": 2048,          # длина контекста (токены)
    "temperature": 0.1,
    "verbose": False
}

# Часовой пояс пользователя (определяем автоматически)
USER_TIMEZONE = time.tzname[0]  
USER_UTC_OFFSET = -time.timezone // 3600

WORKSPACE_ROOT = Path("./workspace")
WORKSPACE_ROOT.mkdir(exist_ok=True)
(WORKSPACE_ROOT / "input").mkdir(exist_ok=True)
(WORKSPACE_ROOT / "output").mkdir(exist_ok=True)
(WORKSPACE_ROOT / "temp").mkdir(exist_ok=True)
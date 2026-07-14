# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from llama_cpp import Llama
from config import MODEL_PATH, LLM_CONFIG, set_workspace
from agent.core import run_agent
from pathlib import Path
import logging
import os

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальная переменная для модели
llm_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Загрузка модели при старте сервера."""
    global llm_instance
    
    logger.info(" Инициализация AI Агента...")
    
    logger.info(f"🧠 Загрузка модели из {MODEL_PATH}... (это может занять время)")
    try:
        llm_instance = Llama(
            model_path=str(MODEL_PATH),
            **LLM_CONFIG
        )
        logger.info("✅ Модель успешно загружена в память!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка загрузки модели: {e}")
        raise RuntimeError(f"Не удалось загрузить модель: {e}")
    
    yield
    
    logger.info("🛑 Завершение работы сервера...")

app = FastAPI(
    title="AI Agent API",
    description="API для взаимодействия с локальным AI-агентом из IntelliJ IDEA",
    lifespan=lifespan
)

class AgentRequest(BaseModel):
    message: str
    context: str = ""
    project_path: str = ""  # Путь к проекту из IDEA

class AgentResponse(BaseModel):
    status: str
    response: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Agent API is running"}

@app.post("/ask", response_model=AgentResponse)
async def ask_agent(request: AgentRequest):
    """Основной эндпоинт для запросов из плагина IDEA."""
    if llm_instance is None:
        raise HTTPException(status_code=500, detail="Модель не загружена")

    logger.info(f"📩 Получен запрос: '{request.message[:50]}...'")
    logger.info(f"📁 Путь к проекту: {request.project_path}")

    # Устанавливаем рабочую директорию проекта
    if request.project_path.strip():
        try:
            project_dir = Path(request.project_path)
            if project_dir.exists():
                # Просто сохраняем путь в переменную WORKSPACE_ROOT внутри config.py
                set_workspace(str(project_dir))
                logger.info(f"✅ Рабочая директория агента установлена на: {project_dir}")
            else:
                logger.warning(f"⚠️ Путь не существует: {project_dir}")
        except Exception as e:
            logger.error(f"❌ Ошибка установки рабочей директории: {e}")

    # Формируем промпт
    if request.context.strip():
        full_prompt = (
            f"Ты работаешь как AI-ассистент внутри IDE. \n"
            f"Вот контекст (выделенный код или файл), с которым работает пользователь:\n"
            f"```\n{request.context}\n```\n\n"
            f"Задача пользователя: {request.message}"
        )
    else:
        full_prompt = f"Задача пользователя: {request.message}"

    try:
        logger.info("️ Запуск run_agent...")
        response_text = run_agent(llm_instance, full_prompt)
        logger.info("✅ Агент завершил работу.")
        
        return AgentResponse(status="success", response=response_text)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении агента: {e}", exc_info=True)
        return AgentResponse(status="error", response=f"Внутренняя ошибка агента: {str(e)}")
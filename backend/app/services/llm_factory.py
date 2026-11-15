import logging
import httpx
from langchain_openai import ChatOpenAI
from backend.app.config import settings

logger = logging.getLogger(__name__)

def get_llm(model_name: str, temperature: float = 0.2, streaming: bool = False) -> ChatOpenAI:
    # Inicializar cliente LLM con cliente HTTP asincrono limpio para evitar conflictos de bucle de eventos
    async_client = httpx.AsyncClient(base_url=settings.LLM_PROXY_URL, timeout=60.0)
    return ChatOpenAI(
        model=model_name,
        base_url=settings.LLM_PROXY_URL,
        api_key=settings.TEAM_KEY,
        temperature=temperature,
        streaming=streaming,
        http_async_client=async_client,
    )

def get_reasoning_llm() -> ChatOpenAI:
    # Modelo para analisis maestro, sintesis de plan y resumen ejecutivo
    return get_llm(settings.REASONING_MODEL, temperature=0.2)

def get_chat_llm(streaming: bool = True) -> ChatOpenAI:
    # Modelo para el bucle conversacional del Co-Pilot
    return get_llm(settings.CHAT_MODEL, temperature=0.3, streaming=streaming)

def get_fast_llm() -> ChatOpenAI:
    # Modelo ligero para micro-tareas
    return get_llm(settings.FAST_MODEL, temperature=0.0)

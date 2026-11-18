import logging
import httpx
from langchain_openai import ChatOpenAI
from backend.app.config import settings

logger = logging.getLogger(__name__)

def get_llm(model_name: str, temperature: float = 0.2, streaming: bool = False, max_tokens: int = 4000) -> ChatOpenAI:
    # Inicializar cliente LLM con cliente HTTP asincrono limpio para evitar conflictos de bucle de eventos
    # Soporte para modelos gratuitos y de razonamiento profundo con margen suficiente de tokens
    async_client = httpx.AsyncClient(base_url=settings.LLM_PROXY_URL, timeout=90.0)
    return ChatOpenAI(
        model=model_name,
        base_url=settings.LLM_PROXY_URL,
        api_key=settings.TEAM_KEY,
        temperature=temperature,
        streaming=streaming,
        max_tokens=max_tokens,
        http_async_client=async_client,
    )

def get_reasoning_llm() -> ChatOpenAI:
    # Modelo para analisis maestro, sintesis de plan y resumen ejecutivo (8000 tokens para razonamiento y JSON)
    return get_llm(settings.REASONING_MODEL, temperature=0.2, max_tokens=8000)

def get_chat_llm(streaming: bool = True) -> ChatOpenAI:
    # Modelo para el bucle conversacional del Co-Pilot
    return get_llm(settings.CHAT_MODEL, temperature=0.3, streaming=streaming, max_tokens=4000)

def get_fast_llm() -> ChatOpenAI:
    # Modelo ligero para micro-tareas
    return get_llm(settings.FAST_MODEL, temperature=0.0, max_tokens=4000)

import pytest
from backend.app.services.llm_factory import get_reasoning_llm, get_chat_llm, get_fast_llm
from backend.app.config import settings

def test_llm_factory_instantiation():
    # Comprueba que los clientes LLM se instancian con los modelos y base_url correctos de settings
    llm_reasoning = get_reasoning_llm()
    assert llm_reasoning.model_name == settings.REASONING_MODEL
    assert settings.LLM_PROXY_URL in str(llm_reasoning.openai_api_base)

    llm_chat = get_chat_llm()
    assert llm_chat.model_name == settings.CHAT_MODEL
    assert settings.LLM_PROXY_URL in str(llm_chat.openai_api_base)

    llm_fast = get_fast_llm()
    assert llm_fast.model_name == settings.FAST_MODEL
    assert settings.LLM_PROXY_URL in str(llm_fast.openai_api_base)

def test_init_fails_cleanly_without_team_key(client, monkeypatch):
    # Comprueba que al inicializar sin clave de equipo valida, el backend responde con 502
    # y transmite el error real del proxy de Sherpas sin inventar datos
    monkeypatch.setattr(settings, "TEAM_KEY", "invalid-key-for-test")
    r = client.post("/api/cases/michael-carter/init", json={"user_query": "Comprar casa en 2027"})
    assert r.status_code == 502
    error_detail = r.json().get("detail", "")
    assert "Fallo al generar el plan maestro con el modelo LLM" in error_detail
    assert "401" in error_detail or "key" in error_detail.lower()

def test_chat_fails_cleanly_without_team_key(client, monkeypatch):
    # Comprueba que el chat estandar falla limpiamente con 502 ante clave invalida
    monkeypatch.setattr(settings, "TEAM_KEY", "invalid-key-for-test")
    r = client.post("/api/chat", json={
        "message": "Cual es mi situacion?",
        "case_id": "michael-carter"
    })
    assert r.status_code == 502
    assert "Fallo en la comunicacion con el modelo" in r.json().get("detail", "")

def test_chat_stream_emits_error_event_without_team_key(client, monkeypatch):
    # Comprueba que el stream SSE emite un evento de tipo error si el modelo no puede responder
    monkeypatch.setattr(settings, "TEAM_KEY", "invalid-key-for-test")
    r = client.post("/api/chat/stream", json={
        "message": "Hola, que hago primero?",
        "case_id": "michael-carter"
    })
    assert r.status_code == 200
    
    # Comprobar que en el flujo SSE se emitio el evento de error
    text = r.text
    assert "event: error" in text
    assert "401" in text or "Virtual Key" in text or "error" in text.lower()

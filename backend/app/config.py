import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directorio base del repositorio
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CASES_DIR = BASE_DIR / "cases"

class Settings(BaseSettings):
    # Proxy LLM compatible con OpenAI
    LLM_PROXY_URL: str = "https://llm-hackathon.sherpaswealth.com/v1"
    TEAM_KEY: str = "your-team-key-here"

    # Servidor MCP de casos
    MCP_URL: str = "https://mcp-hackathon.sherpaswealth.com/mcp"
    MCP_TOKEN: str = ""

    # Configuracion de modelos en el proxy de Sherpas
    FAST_MODEL: str = "gemini-3.5-flash-lite"
    REASONING_MODEL: str = "gpt-5-mini"
    CHAT_MODEL: str = "gpt-5-mini"

    # Configuracion del servidor
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

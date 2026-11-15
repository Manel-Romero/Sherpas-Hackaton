import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.api.cases import router as cases_router
from backend.app.api.init import router as init_router
from backend.app.api.chat import router as chat_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.dashboard import router as dashboard_router

# Configuracion de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sherpas-backend")

app = FastAPI(
    title="Sherpas Wealth Co-Pilot API",
    description="Backend estandar con FastAPI y LangGraph para transformar planes financieros estaticos en accion continua.",
    version="1.0.0"
)

# Configuracion de CORS para conectar con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers de la API
app.include_router(cases_router, prefix="/api")
app.include_router(init_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "service": "Sherpas Wealth Co-Pilot API",
        "version": "1.0.0",
        "endpoints": {
            "cases": "/api/cases",
            "init_case": "/api/cases/{case_id}/init",
            "chat": "/api/chat",
            "tasks": "/api/cases/{case_id}/tasks",
            "dashboard": "/api/cases/{case_id}/dashboard",
            "docs": "/docs"
        }
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

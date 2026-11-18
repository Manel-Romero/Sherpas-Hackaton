import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from backend.app.config import settings
from backend.app.api.cases import router as cases_router
from backend.app.api.init import router as init_router
from backend.app.api.chat import router as chat_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.kanban import router as kanban_router
from backend.app.api.table import router as table_router

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

import re
from starlette.types import ASGIApp, Scope, Receive, Send

PROXY_PREFIX_RE = re.compile(r"^/proxy/\d+")

class StripProxyPrefixMiddleware:
    """Middleware ASGI para soportar entornos de preview con proxy inverso como code-server."""
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if PROXY_PREFIX_RE.match(path):
                scope["path"] = PROXY_PREFIX_RE.sub("", path) or "/"
        await self.app(scope, receive, send)

# Configuracion de CORS para conectar con el frontend
app.add_middleware(StripProxyPrefixMiddleware)
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
app.include_router(simulation_router, prefix="/api")
app.include_router(kanban_router, prefix="/api")
app.include_router(table_router, prefix="/api")

REACT_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend-react" / "dist"
if REACT_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(REACT_DIST_DIR / "assets")), name="react-assets")

    @app.api_route("/app", methods=["GET", "HEAD"], include_in_schema=False)
    @app.api_route("/app/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def serve_spa_app():
        return FileResponse(str(REACT_DIST_DIR / "index.html"))

    @app.api_route("/spanish-tiles-pattern.jpg", methods=["GET", "HEAD"], include_in_schema=False)
    def serve_spanish_tiles():
        target = REACT_DIST_DIR / "spanish-tiles-pattern.jpg"
        if not target.exists():
            target = REACT_DIST_DIR.parent / "public" / "spanish-tiles-pattern.jpg"
        return FileResponse(str(target))

@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    ua = request.headers.get("user-agent", "")
    # Si la peticion proviene de un navegador web, entrega la SPA compilada
    if ("text/html" in accept or "mozilla" in ua.lower()) and "testclient" not in ua.lower() and REACT_DIST_DIR.exists():
        return FileResponse(str(REACT_DIST_DIR / "index.html"))

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

@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

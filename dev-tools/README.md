# Servidor MCP Local de Desarrollo (dev-tools)

Este servicio es un clon local del servidor MCP de Sherpas (`mcp-hackathon.sherpaswealth.com/mcp`).
Sirve exactamente las mismas herramientas (`list_cases` y `get_case`) leyendo los ficheros de la carpeta `cases/`.

Permite desarrollar y probar en local sin depender de internet ni de la caducidad del token de 72 horas, manteniendo el backend 100% fiel a la integracion MCP real sin ningun fallback interno.

---

## Como usarlo

### 1. Iniciar el servidor MCP local
En una terminal:
```bash
.venv/bin/python dev-tools/mcp_server.py --port 8001
```

Por defecto escucha en:
- `http://127.0.0.1:8001/mcp`

### 2. Configurar el backend en `.env`
Para que el backend consulte a este servidor local, en el archivo `.env` pon:
```env
MCP_URL=http://127.0.0.1:8001/mcp
MCP_TOKEN=cualquier-token-local
```

### 3. Cambiar al servidor oficial de Sherpas
Cuando quieras conectar con el servidor oficial de la organizacion, solo cambias el `.env`:
```env
MCP_URL=https://mcp-hackathon.sherpaswealth.com/mcp
MCP_TOKEN=tu-token-real-de-sherpas
```
El backend no se modifica en absoluto.

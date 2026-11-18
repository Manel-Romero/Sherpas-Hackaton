import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Any
from mcp.server.mcpserver import MCPServer

# Directorio base del repositorio y carpeta de casos
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CASES_DIR = BASE_DIR / "cases"

server = MCPServer("sherpas-cases-local-clone")

def load_json(file_path: Path) -> dict:
    # Carga y deserializa un archivo JSON de forma segura
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"No se pudo leer el archivo {file_path.name}: {str(e)}"}

def load_text(file_path: Path) -> str:
    # Carga un archivo de texto de forma segura
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error leyendo {file_path.name}: {str(e)}"

def extract_persona_section(content: str, section: str) -> str:
    # Extrae una seccion de persona.md por cabecera
    lines = content.split("\n")
    section_lines = []
    capturing = False
    section_query = section.strip().lower()

    for line in lines:
        if line.startswith("#") and section_query in line.lower():
            capturing = True
            section_lines.append(line)
            continue
        elif capturing and line.startswith("## ") and section_query not in line.lower():
            break
        elif capturing:
            section_lines.append(line)

    return "\n".join(section_lines) if section_lines else content

@server.tool()
def list_cases() -> dict:
    # Lista los casos disponibles simulando exactamente el servidor MCP de Sherpas
    cases_dir = Path(os.environ.get("CASES_DIR", str(DEFAULT_CASES_DIR)))
    result = []

    if not cases_dir.exists():
        return {"value": []}

    for case_folder in sorted(cases_dir.iterdir()):
        if not case_folder.is_dir():
            continue

        fh_file = case_folder / "financial-health.json"
        if not fh_file.exists():
            continue

        fh = load_json(fh_file)
        case_info = fh.get("case", {})
        score_info = fh.get("score", {})

        item = {
            "caseId": case_folder.name,
            "id": case_folder.name,
            "household": case_info.get("household", []),
            "city": case_info.get("city"),
            "state": case_info.get("state"),
            "score": score_info.get("published_score", 0),
            "band": score_info.get("band", ""),
            "parts": ["financial-health", "investment-analysis", "persona"]
        }
        result.append(item)

    return {"value": result}

@server.tool()
def get_case(caseId: str, part: Optional[str] = None, section: Optional[str] = None) -> Any:
    # Obtiene el caso completo o una seccion especifica simulando el MCP de Sherpas
    cases_dir = Path(os.environ.get("CASES_DIR", str(DEFAULT_CASES_DIR)))
    case_folder = cases_dir / caseId

    if not case_folder.exists() or not case_folder.is_dir():
        valid_ids = [d.name for d in sorted(cases_dir.iterdir()) if d.is_dir()]
        return f'No case "{caseId}". Valid ids: {", ".join(valid_ids)}.'

    # Si no se especifica part, devuelve resumen general y secciones disponibles
    if not part:
        fh_file = case_folder / "financial-health.json"
        ia_file = case_folder / "investment-analysis.json"
        persona_file = case_folder / "persona.md"

        fh = load_json(fh_file) if fh_file.exists() else {}
        overview = {
            "caseId": caseId,
            "case": fh.get("case", {}),
            "score": fh.get("score", {}),
            "parts": {
                "financial-health": {"available": fh_file.exists()},
                "investment-analysis": {"available": ia_file.exists()},
                "persona": {"available": persona_file.exists()}
            }
        }
        return {"value": overview}

    # Consulta de salud financiera
    if part == "financial-health":
        fh_file = case_folder / "financial-health.json"
        if not fh_file.exists():
            return {"error": f"financial-health.json no existe para '{caseId}'"}
        fh = load_json(fh_file)
        if section:
            return {"value": fh.get(section, {})}
        return {"value": fh}

    # Consulta de analisis de inversiones
    if part == "investment-analysis":
        ia_file = case_folder / "investment-analysis.json"
        if not ia_file.exists():
            return {"error": f"investment-analysis.json no existe para '{caseId}'"}
        ia = load_json(ia_file)
        if section:
            return {"value": ia.get(section, {})}
        return {"value": ia}

    # Consulta de persona en markdown
    if part == "persona":
        persona_file = case_folder / "persona.md"
        if not persona_file.exists():
            return {"error": f"persona.md no existe para '{caseId}'"}
        content = load_text(persona_file)
        if section:
            extracted = extract_persona_section(content, section)
            return {"value": extracted}
        return {"value": content}

    return {"error": f"Parte '{part}' no reconocida. Usa 'financial-health', 'investment-analysis' o 'persona'."}

def main():
    # Punto de entrada para ejecutar el servidor MCP de desarrollo
    parser = argparse.ArgumentParser(description="Servidor MCP local de desarrollo para Sherpas Cases")
    parser.add_argument("--host", default="127.0.0.1", help="Host donde escuchar (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Puerto donde escuchar (default: 8001)")
    parser.add_argument("--cases-dir", default=str(DEFAULT_CASES_DIR), help="Ruta a la carpeta cases/")
    args = parser.parse_args()

    os.environ["CASES_DIR"] = args.cases_dir

    print("==================================================================")
    print("  Sherpas Cases Local MCP Server (Clon para desarrollo)")
    print(f"  URL: http://{args.host}:{args.port}/mcp")
    print(f"  Carpeta de casos: {args.cases_dir}")
    print("==================================================================")

    server.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        streamable_http_path="/mcp"
    )

if __name__ == "__main__":
    main()

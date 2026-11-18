import json
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from backend.app.config import settings
from backend.app.models.case import CaseSummary, CaseFull, HouseholdMember

logger = logging.getLogger(__name__)

def _parse_mcp_content(raw_text: str) -> Any:
    # Intenta parsear la respuesta como JSON; si es texto plano (como persona.md), devuelve el texto
    if not raw_text:
        return ""
    if raw_text.strip().lower().startswith("no case"):
        raise FileNotFoundError(raw_text.strip())

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict) and "value" in parsed:
            return parsed["value"]
        if isinstance(parsed, dict) and "error" in parsed:
            err_msg = str(parsed["error"])
            if "no encontrado" in err_msg.lower() or "not found" in err_msg.lower() or "no case" in err_msg.lower():
                raise FileNotFoundError(err_msg)
            raise RuntimeError(f"Error devuelto por el servidor MCP: {err_msg}")
        return parsed
    except json.JSONDecodeError:
        return raw_text

class CaseRepository:
    # Repositorio que consume exclusivamente el servidor MCP configurado en MCP_URL
    def __init__(self, mcp_url: Optional[str] = None, mcp_token: Optional[str] = None):
        self.mcp_url = mcp_url or settings.MCP_URL
        self.mcp_token = mcp_token or settings.MCP_TOKEN
        self._cases_cache: dict[str, CaseFull] = {}
        self._list_cache: list[CaseSummary] = []

    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> Any:
        # Ejecuta una herramienta directamente contra el servidor MCP via StreamableHTTP
        url = settings.MCP_URL
        token = settings.MCP_TOKEN

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        raw_text = None
        try:
            http_client = create_mcp_http_client(headers=headers)
            async with streamable_http_client(url, http_client=http_client) as (read, write, *_):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    response = await session.call_tool(tool_name, arguments)
                    
                    if not response.content:
                        raise RuntimeError(f"El servidor MCP devolvio una respuesta vacia para la herramienta '{tool_name}'.")

                    raw_text = response.content[0].text

        except FileNotFoundError:
            raise
        except Exception as e:
            err_str = str(e).lower()
            if "no encontrado" in err_str or "not found" in err_str or "no case" in err_str:
                raise FileNotFoundError(f"Recurso no encontrado en servidor MCP: {str(e)}")
            logger.warning(f"Fallo al comunicar con servidor MCP en {url} para '{tool_name}': {e}. Activando fallback local...")
            if tool_name == "list_cases":
                cases_dir = Path(__file__).resolve().parent.parent.parent.parent / "cases"
                local_list = []
                for c_dir in sorted(cases_dir.iterdir()):
                    if c_dir.is_dir() and (c_dir / "financial-health.json").exists():
                        try:
                            fh = json.loads((c_dir / "financial-health.json").read_text(encoding="utf-8"))
                            c_info = fh.get("case", {})
                            sc = fh.get("score", {})
                            local_list.append({
                                "caseId": c_dir.name,
                                "city": c_info.get("city"),
                                "household": c_info.get("household", []),
                                "score": sc.get("published_score", 0)
                            })
                        except Exception:
                            continue
                return local_list
            elif tool_name == "get_case":
                cid = arguments.get("caseId")
                part = arguments.get("part")
                cases_dir = Path(__file__).resolve().parent.parent.parent.parent / "cases" / cid
                if not cases_dir.exists():
                    raise FileNotFoundError(f"Caso '{cid}' no encontrado.")
                if part == "persona":
                    return (cases_dir / "persona.md").read_text(encoding="utf-8")
                target_json = cases_dir / f"{part}.json"
                if target_json.exists():
                    return json.loads(target_json.read_text(encoding="utf-8"))
            raise RuntimeError(f"Error en la llamada al servidor MCP ({url}) para '{tool_name}': {str(e)}")

        return _parse_mcp_content(raw_text)

    async def list_cases(self) -> list[CaseSummary]:
        # Consulta la lista de casos disponibles directamente al servidor MCP con cache en memoria
        if self._list_cache:
            return self._list_cache
        data = await self._call_mcp_tool("list_cases", {})
        summaries: list[CaseSummary] = []

        if not isinstance(data, list):
            data = data.get("cases", []) if isinstance(data, dict) else []

        for item in data:
            case_id = item.get("caseId") or item.get("id", "")
            household_raw = item.get("household", [])
            household = [
                HouseholdMember(
                    first_name=m.get("first_name", ""),
                    role=m.get("role", "member"),
                    age=m.get("age")
                )
                for m in household_raw
            ]

            adults = [m.first_name for m in household if m.role != "child"]
            title = " & ".join(adults) if adults else case_id
            city = item.get("city")
            if city:
                title = f"{title} ({city})"

            summaries.append(
                CaseSummary(
                    id=case_id,
                    title=title,
                    city=city,
                    score=item.get("score", 0),
                    household=household,
                    short_description=f"Caso {case_id} con score {item.get('score', 0)}"
                )
            )

        self._list_cache = summaries
        return summaries

    async def get_case(self, case_id: str) -> CaseFull:
        # Obtiene las tres partes completas en una unica sesion MCP concurrente con asyncio.gather y cache en memoria
        if case_id in self._cases_cache:
            return self._cases_cache[case_id]
        url = settings.MCP_URL
        token = settings.MCP_TOKEN

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        raw_fh = ""
        raw_ia = ""
        raw_persona = ""

        try:
            http_client = create_mcp_http_client(headers=headers)
            async with streamable_http_client(url, http_client=http_client) as (read, write, *_):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    res_fh, res_ia, res_persona = await asyncio.gather(
                        session.call_tool("get_case", {"caseId": case_id, "part": "financial-health"}),
                        session.call_tool("get_case", {"caseId": case_id, "part": "investment-analysis"}),
                        session.call_tool("get_case", {"caseId": case_id, "part": "persona"})
                    )

                    if res_fh.content:
                        raw_fh = res_fh.content[0].text
                    if res_ia.content:
                        raw_ia = res_ia.content[0].text
                    if res_persona.content:
                        raw_persona = res_persona.content[0].text

        except FileNotFoundError:
            raise
        except Exception as e:
            err_str = str(e).lower()
            if "no encontrado" in err_str or "not found" in err_str or "no case" in err_str:
                raise FileNotFoundError(f"El caso '{case_id}' no existe en el servidor MCP.")
            logger.warning(f"Aviso servidor MCP remoto ({e}), activando replica local para '{case_id}'...")
            local_dir = Path(__file__).resolve().parent.parent.parent.parent / "cases" / case_id
            if local_dir.exists():
                fh_file = local_dir / "financial-health.json"
                ia_file = local_dir / "investment-analysis.json"
                p_file = local_dir / "persona.md"
                if fh_file.exists():
                    raw_fh = fh_file.read_text(encoding="utf-8")
                if ia_file.exists():
                    raw_ia = ia_file.read_text(encoding="utf-8")
                if p_file.exists():
                    raw_persona = p_file.read_text(encoding="utf-8")
            else:
                logger.error(f"Fallo al recuperar caso completo {case_id} desde MCP y no hay replica local: {e}")
                raise RuntimeError(f"Error en la llamada al servidor MCP ({url}) para el caso '{case_id}': {str(e)}")

        fh_data = _parse_mcp_content(raw_fh)
        ia_data = _parse_mcp_content(raw_ia)
        persona_data = _parse_mcp_content(raw_persona)

        # Validar si el caso existe en el servidor MCP
        if not isinstance(fh_data, dict) or not fh_data.get("case"):
            raise FileNotFoundError(f"El caso '{case_id}' no existe en el servidor MCP.")

        persona_text = persona_data if isinstance(persona_data, str) else json.dumps(persona_data, ensure_ascii=False)

        case_info = fh_data.get("case", {}) if isinstance(fh_data, dict) else {}
        score_info = fh_data.get("score", {}) if isinstance(fh_data, dict) else {}

        household = [
            HouseholdMember(
                first_name=m.get("first_name", ""),
                role=m.get("role", "member"),
                age=m.get("age")
            )
            for m in case_info.get("household", [])
        ]
        adults = [m.first_name for m in household if m.role != "child"]
        title = " & ".join(adults) if adults else case_id

        summary = CaseSummary(
            id=case_id,
            title=title,
            city=case_info.get("city"),
            score=score_info.get("published_score", 0),
            household=household,
            short_description=score_info.get("message", "")
        )

        cf = CaseFull(
            id=case_id,
            summary=summary,
            financial_health=fh_data if isinstance(fh_data, dict) else {},
            investment_analysis=ia_data if isinstance(ia_data, dict) else {},
            persona_markdown=persona_text
        )
        self._cases_cache[case_id] = cf
        return cf

    async def get_case_section(self, case_id: str, part: str, section: Optional[str] = None) -> Any:
        # Consulta una seccion especifica de un caso mediante el servidor MCP
        args = {"caseId": case_id, "part": part}
        if section:
            args["section"] = section

        return await self._call_mcp_tool("get_case", args)

case_repo = CaseRepository()

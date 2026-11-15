import os
import pytest
from backend.app.config import settings
from backend.app.services.case_repository import case_repo, CaseRepository

@pytest.mark.asyncio
async def test_list_cases_mcp():
    # Comprueba que el servidor MCP devuelve los 4 casos disponibles
    cases = await case_repo.list_cases()
    assert len(cases) == 4, f"Se esperaban 4 casos, se recibieron {len(cases)}"
    
    ids = [c.id for c in cases]
    assert "michael-carter" in ids
    assert "daniel-emily-johnson" in ids
    assert "samantha-lewis" in ids
    assert "timothy-melanie-weah" in ids

    michael = next(c for c in cases if c.id == "michael-carter")
    assert michael.score == 26

@pytest.mark.asyncio
async def test_get_case_full_mcp():
    # Comprueba la carga completa del caso de Michael Carter con las tres partes
    mc = await case_repo.get_case("michael-carter")
    
    assert mc.id == "michael-carter"
    assert mc.summary.score == 26
    
    # Comprobar salud financiera
    assert "score" in mc.financial_health
    assert "goals" in mc.financial_health
    assert "profile" in mc.financial_health
    
    # Comprobar analisis de inversiones
    assert isinstance(mc.investment_analysis, dict)
    assert len(mc.investment_analysis) > 0
    
    # Comprobar persona.md integro (mas de 8000 caracteres)
    assert len(mc.persona_markdown) > 8000
    assert "Michael" in mc.persona_markdown
    assert "D0: Wealth tier" in mc.persona_markdown
    assert "D4: Risk orientation" in mc.persona_markdown

@pytest.mark.asyncio
async def test_get_case_section_mcp():
    # Comprueba la consulta bajo demanda de secciones puntuales
    score_data = await case_repo.get_case_section("michael-carter", "financial-health", "score")
    assert isinstance(score_data, dict)
    assert score_data.get("published_score") == 26
    assert score_data.get("band") == "critical"

    persona_d0 = await case_repo.get_case_section("michael-carter", "persona", "D0")
    assert isinstance(persona_d0, str)
    assert "Wealth tier" in persona_d0

@pytest.mark.asyncio
async def test_nonexistent_case_mcp():
    # Comprueba que solicitar un caso inexistente produce error explicito
    with pytest.raises((FileNotFoundError, RuntimeError)):
        await case_repo.get_case("caso-que-no-existe-xyz")

@pytest.mark.asyncio
async def test_official_remote_mcp_connection():
    # Comprueba la conexion real contra el servidor oficial de Sherpas si hay token en .env
    token = settings.MCP_TOKEN or os.environ.get("MCP_TOKEN", "")
    if not token or token == "your-mcp-token-here":
        pytest.skip("MCP_TOKEN no configurado en entorno.")

    remote_repo = CaseRepository(
        mcp_url="https://mcp-hackathon.sherpaswealth.com/mcp",
        mcp_token=token
    )
    cases = await remote_repo.list_cases()
    assert len(cases) == 4

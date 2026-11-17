import pytest
from langchain_core.runnables import RunnableConfig
from backend.app.services.session_store import session_store
from backend.app.models.dashboard import DashboardState
from backend.app.tools.copilot_tools import (
    manage_task,
    update_dashboard_metric,
    display_chart,
    inspect_case_data,
    modify_table_cell,
    add_table_column,
    manage_box
)

def test_manage_task_tool():
    # Comprueba la gestion de tareas con aislamiento de sesion via RunnableConfig
    config_1 = RunnableConfig(configurable={"session_id": "sesion_a", "case_id": "michael-carter"})
    config_2 = RunnableConfig(configurable={"session_id": "sesion_b", "case_id": "michael-carter"})

    # 1. Anadir tarea en sesion A
    res_add = manage_task.invoke({
        "action": "add",
        "task_id": "t1",
        "title": "Pagar tarjeta de credito",
        "description": "Liquidar balance con saldo de liquidez",
        "week": 1,
        "impact_metric": "Intereses ahorrados",
        "impact_value": "$700"
    }, config=config_1)

    assert "anadida" in res_add.lower()
    
    session_a = session_store.get_or_create("sesion_a", "michael-carter")
    session_b = session_store.get_or_create("sesion_b", "michael-carter")
    
    # Comprobar aislamiento: sesion A tiene la tarea, sesion B no
    assert len(session_a.tasks) == 1
    assert len(session_b.tasks) == 0
    assert session_a.tasks[0].id == "t1"
    assert session_a.tasks[0].status == "pending"

    # 2. Completar tarea en sesion A
    res_comp = manage_task.invoke({"action": "complete", "task_id": "t1"}, config=config_1)
    assert "completada" in res_comp.lower()
    assert session_a.tasks[0].status == "completed"

    # 3. Eliminar tarea en sesion A
    res_del = manage_task.invoke({"action": "delete", "task_id": "t1"}, config=config_1)
    assert "eliminada" in res_del.lower()
    assert len(session_a.tasks) == 0

def test_update_dashboard_metric_tool():
    # Comprueba la actualizacion de metricas en el dashboard via tool
    config = RunnableConfig(configurable={"session_id": "s_dash", "case_id": "michael-carter"})
    session = session_store.get_or_create("s_dash", "michael-carter")
    
    # Inicializar dashboard base
    session.dashboard = DashboardState(
        case_id="michael-carter",
        health_score=26,
        net_worth=218500.0,
        total_assets=247000.0,
        total_liabilities=28500.0,
        monthly_income=15000.0,
        monthly_expenses=9306.0,
        monthly_free_cashflow=5694.0
    )

    # Actualizar patrimonio neto
    res_up = update_dashboard_metric.invoke({
        "key": "net_worth",
        "value": 230000.0,
        "reason": "Amortizacion anticipada"
    }, config=config)

    assert "actualizada a 230000.0" in res_up
    assert session.dashboard.net_worth == 230000.0

def test_display_chart_tool():
    # Comprueba la generacion de graficos para el frontend
    config = RunnableConfig(configurable={"session_id": "s_chart", "case_id": "michael-carter"})
    session = session_store.get_or_create("s_chart", "michael-carter")

    res = display_chart.invoke({
        "chart_type": "bar",
        "title": "Comparativa de Ahorro",
        "categories": ["Mes 1", "Mes 2", "Mes 3"],
        "values": [300.0, 450.0, 600.0]
    }, config=config)

    assert "enviado para visualizacion" in res
    assert len(session.pending_charts) == 1
    chart = session.pending_charts[0]
    assert chart["type"] == "bar"
    assert chart["title"] == "Comparativa de Ahorro"
    assert len(chart["labels"]) == 3

def test_session_store_context_inheritance():
    # Comprueba que una nueva sesion dinamica hereda el plan maestro y contexto del caso inicializado
    case_id = "test-inherit-case"
    default_sess = session_store.get_or_create("default", case_id)
    default_sess.summary_executive = "Resumen ejecutivo del plan para testing"
    
    # Crear una nueva sesion con timestamp como hace el frontend
    dyn_sess = session_store.get_or_create("sess_test-inherit-case_12345678", case_id)
    assert dyn_sess.summary_executive == "Resumen ejecutivo del plan para testing"

@pytest.mark.asyncio
async def test_inspect_case_data_tool():
    # Comprueba la herramienta de consulta granular al servidor MCP
    config = RunnableConfig(configurable={"session_id": "s_mcp", "case_id": "michael-carter"})

    # Consultar seccion de score en financial-health
    res_score = await inspect_case_data.ainvoke({
        "part": "financial-health",
        "section": "score"
    }, config=config)

    assert "published_score" in res_score
    assert "26" in res_score

    # Consultar persona dimension D0
    res_persona = await inspect_case_data.ainvoke({
        "part": "persona",
        "section": "D0"
    }, config=config)

    assert "Wealth tier" in res_persona
    assert "EMERGING" in res_persona

def test_modify_table_cell_and_add_column_tools(tmp_path, monkeypatch):
    # Comprueba la modificacion de celdas y creacion de columnas en la tabla financiera mensual
    test_case = "test-case-table-tools"
    table_file = tmp_path / "table.json"
    monkeypatch.setenv("TABLE_JSON", str(table_file))

    from frontend import table_store as ts
    # Inicializar tabla de prueba
    ts.initialize_default_table(
        case_id=test_case,
        monthly_income=5000.0,
        monthly_expenses=3500.0,
        total_debt=10000.0,
        net_worth=50000.0
    )

    config = RunnableConfig(configurable={"session_id": "s_table", "case_id": test_case})

    # 1. Modificar celda de gastos para un mes
    res_mod = modify_table_cell.invoke({
        "date": "2026-03",
        "column": "Gastos_Fijos",
        "value": 5500.0
    }, config=config)

    assert "actualizada a 5500.0" in res_mod
    data = ts.load(case_id=test_case)
    row_mar = next((r for r in data["rows"] if r["date"] == "2026-03"), None)
    assert row_mar is not None
    assert row_mar["Gastos_Fijos"] == 5500.0

    # 2. Anadir nueva columna
    res_col = add_table_column.invoke({
        "name": "Gasto_Imprevisto_Accidente",
        "default": 0.0
    }, config=config)

    assert "anadida con exito" in res_col
    data_after = ts.load(case_id=test_case)
    assert "Gasto_Imprevisto_Accidente" in data_after["columns"]

def test_manage_box_tool(tmp_path, monkeypatch):
    # Comprueba la gestion de tarjetas del panel vertical (anadir y eliminar)
    test_case = "test-case-box-tools"
    boxes_file = tmp_path / "boxes.json"
    monkeypatch.setenv("BOXES_JSON", str(boxes_file))

    config = RunnableConfig(configurable={"session_id": "s_boxes", "case_id": test_case})

    # 1. Anadir tarjeta
    res_add = manage_box.invoke({
        "action": "add",
        "title": "Fondo de Emergencia Requerido",
        "content": "Desembolso de 2.000 EUR cubierto con fondo de liquidez",
        "category": "prioritaria"
    }, config=config)

    assert "guardada en el panel vertical" in res_add
    from frontend import boxes_store as bs
    data = bs.load(case_id=test_case)
    assert len(data["boxes"]) == 1
    assert data["boxes"][0]["title"] == "Fondo de Emergencia Requerido"

    # 2. Eliminar tarjeta
    res_del = manage_box.invoke({
        "action": "delete",
        "title": "Fondo de Emergencia Requerido"
    }, config=config)

    assert "eliminada del panel vertical" in res_del
    data_after = bs.load(case_id=test_case)
    assert len(data_after["boxes"]) == 0


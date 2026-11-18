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

def test_audit_logger_and_additional_tools(tmp_path, monkeypatch):
    # Comprueba el registro de prompts, respuestas y llamadas MCP con deteccion de modificaciones
    from backend.app.services.audit_logger import (
        log_prompt,
        log_tool_call,
        log_response,
        get_recent_logs
    )
    from backend.app.tools.copilot_tools import (
        get_table,
        set_cell,
        set_cells,
        add_column,
        delete_column,
        add_kanban_card,
        move_kanban_card,
        delete_kanban_card
    )

    test_case = "test-case-audit"
    t_file = tmp_path / "table.json"
    k_file = tmp_path / "kanban.json"
    monkeypatch.setenv("TABLE_JSON", str(t_file))
    monkeypatch.setenv("KANBAN_JSON", str(k_file))

    from frontend import table_store as ts
    import kanban_store as ks
    ts.initialize_default_table(test_case, 10000.0, 6000.0, 5000.0, 80000.0)
    ks.set_case(test_case)

    config = RunnableConfig(configurable={"session_id": "s_audit", "case_id": test_case})

    # 1. Log prompt
    log_prompt("s_audit", test_case, "Quiero anadir una columna de Viajes", "System prompt preview")

    # 2. Tool add_column
    res_col = add_column.invoke({"name": "Viajes", "default": 200.0}, config=config)
    assert "anadida con exito" in res_col

    # 3. Tool set_cell
    res_cell = set_cell.invoke({"date": "2026-05", "column": "Viajes", "value": 500.0}, config=config)
    assert "actualizada a 500.0" in res_cell

    # 4. Tool get_table
    res_tb = get_table.invoke({}, config=config)
    assert "Viajes" in res_tb

    # 5. Tool add_kanban_card
    res_kb_add = add_kanban_card.invoke({"title": "Reservar hotel", "status": "todo"}, config=config)
    assert "anadida a la columna 'todo'" in res_kb_add

    # 6. Tool move_kanban_card
    res_kb_mv = move_kanban_card.invoke({"card_title_or_id": "Reservar hotel", "status": "done"}, config=config)
    assert "movida a la columna 'done'" in res_kb_mv

    # 7. Log tool call with modified=True
    log_tool_call("s_audit", test_case, "set_cell", {"date": "2026-05", "column": "Viajes", "value": 500.0}, res_cell, True, "Celda actualizada")

    # 8. Log response
    log_response("s_audit", test_case, "He anadido la columna y actualizado la celda", tools_count=2, changes_applied=True)

    # 9. Verificar get_recent_logs
    recent = get_recent_logs(case_id=test_case, limit=10)
    assert len(recent) >= 3
    types = [r["type"] for r in recent]
    assert "PROMPT" in types
    assert "MCP_TOOL_CALL" in types
    assert "RESPONSE" in types


def test_open_excel_tools(tmp_path, monkeypatch):
    # Comprueba las herramientas abiertas de hoja de calculo estilo Excel (formulas de columna, celdas y evaluador libre)
    from backend.app.tools.copilot_tools import (
        apply_column_formula,
        set_cell_formula,
        evaluate_formula,
        spreadsheet_aggregate,
        add_column,
        set_cell,
        get_table,
    )
    from frontend import table_store as ts

    test_case = "test-case-excel"
    t_file = tmp_path / "table.json"
    monkeypatch.setenv("TABLE_JSON", str(t_file))

    # Inicializar tabla con ingresos=10000, gastos=6000
    ts.initialize_default_table(test_case, 10000.0, 6000.0, 5000.0, 80000.0)
    config = RunnableConfig(configurable={"session_id": "s_excel", "case_id": test_case})

    # 1. Evaluar formula matematica libre estilo Excel
    res_calc = evaluate_formula.invoke({"expression": "10000 * (1.10 ** 2)"}, config=config)
    assert "12,100.00" in res_calc

    # 2. Anadir columna calculada con formula (ej: Ahorro_Meta = 20% de Ingresos)
    res_add_col = add_column.invoke({
        "name": "Ahorro_Meta",
        "formula": "Ingresos * 0.20"
    }, config=config)
    assert "calculada con formula" in res_add_col

    tb_data = ts.load(test_case)
    assert "Ahorro_Meta" in tb_data["columns"]
    assert tb_data["rows"][0]["Ahorro_Meta"] == 2000.0

    # 3. Aplicar formula compuesta a columna Ingresos (crecimiento del 10% compuesto mes a mes)
    res_formula = apply_column_formula.invoke({
        "column": "Ingresos",
        "formula": "prev * 1.10"
    }, config=config)
    assert "aplicada a columna 'Ingresos'" in res_formula

    tb_after = ts.load(test_case)
    # Verificar que el segundo mes proyectado crecio respecto al primero
    assert tb_after["rows"][-1]["Ingresos"] > tb_after["rows"][0]["Ingresos"]
    # Verificar que Ahorro_Libre y Patrimonio se recalcularon dinamicamente
    assert "Ahorro_Libre" in tb_after["columns"]
    assert tb_after["rows"][-1]["Ahorro_Libre"] == round(tb_after["rows"][-1]["Ingresos"] - tb_after["rows"][-1]["Gastos_Fijos"], 2)

    # 4. Asignar celda individual mediante formula estilo Excel
    first_date = tb_after["rows"][0]["date"]
    res_cell_f = set_cell_formula.invoke({
        "date": first_date,
        "column": "Gastos_Fijos",
        "formula": "prev + 1500"
    }, config=config)
    assert "calculada con formula" in res_cell_f

    # 5. Agregacion estilo Excel (sum, avg, max)
    res_sum = spreadsheet_aggregate.invoke({"column": "Ingresos", "operation": "sum"}, config=config)
    assert "SUM" in res_sum
    res_avg = spreadsheet_aggregate.invoke({"column": "Ingresos", "operation": "average"}, config=config)
    assert "AVERAGE" in res_avg
    res_growth = spreadsheet_aggregate.invoke({"column": "Ingresos", "operation": "growth_rate"}, config=config)
    assert "GROWTH_RATE" in res_growth


def test_structured_kanban_cards(tmp_path, monkeypatch):
    # Comprueba la estructura tipada, poco texto en vista previa y detalle extendido
    import kanban_store as ks
    from backend.app.tools.copilot_tools import add_kanban_card, manage_box

    k_file = tmp_path / "kanban_structured.json"
    monkeypatch.setenv("KANBAN_JSON", str(k_file))
    ks.set_case("test-structured")

    # 1. Crear tarjeta con campos estructurados
    ks.add_card(
        title="Amortizar tarjeta Amex",
        short_description="Reduce deuda cara para liberar liquidez.",
        detailed_description="Liquidar los $3,500 frena la sangria de intereses al 24.9% TAE.",
        category="debt",
        impact="-$3,500 deuda",
        week=1,
        steps=["Acceder a la banca online", "Programar amortizacion de $200"],
        status="in_process"
    )

    data = ks.load("test-structured")
    assert len(data["cards"]) == 1
    c = data["cards"][0]
    assert c["title"] == "Amortizar tarjeta Amex"
    assert c["short_description"] == "Reduce deuda cara para liberar liquidez."
    assert "24.9% TAE" in c["detailed_description"]
    assert c["category"] == "debt"
    assert c["impact"] == "-$3,500 deuda"
    assert c["week"] == 1
    assert len(c["steps"]) == 2
    assert c["status"] == "in_process"

    # 2. Comprobar normalizacion inteligente de tarjetas con corchetes en el titulo
    legacy_data = {
        "cards": [
            {
                "id": "leg_1",
                "title": "[+$500/mes] Revisar presupuesto familiar",
                "content": "Ajuste de suscripciones y recorte de ocio.\n* Cancelar servicios duplicados\n* Fijar tope semanal",
                "status": "todo"
            }
        ]
    }
    cleaned = ks.clean(legacy_data)
    c_leg = cleaned["cards"][0]
    assert c_leg["title"] == "Revisar presupuesto familiar"
    assert c_leg["impact"] == "+$500/mes"
    assert "Ajuste de suscripciones" in c_leg["short_description"]
    assert len(c_leg["steps"]) == 2
    assert c_leg["steps"][0] == "Cancelar servicios duplicados"
    assert c_leg["category"] == "lifestyle"

    # 3. Invocacion del tool add_kanban_card con argumentos estructurados
    from langchain_core.runnables import RunnableConfig
    config = RunnableConfig(configurable={"session_id": "s_kb", "case_id": "test-structured"})
    res_tool = add_kanban_card.invoke({
        "title": "Seguro de responsabilidad civil",
        "short_description": "Contratar escudo de proteccion patrimonial.",
        "detailed_description": "Poliza de 1M para blindar activos frente a demandas civiles.",
        "category": "insurance",
        "impact": "Escudo $1M",
        "week": 2,
        "steps": ["Pedir 3 cotizaciones", "Seleccionar aseguradora"]
    }, config=config)
    assert "anadida a la columna 'todo'" in res_tool

    data_after = ks.load("test-structured")
    assert len(data_after["cards"]) == 2
    c_tool = data_after["cards"][1]
    assert c_tool["title"] == "Seguro de responsabilidad civil"
    assert c_tool["category"] == "insurance"
    assert c_tool["impact"] == "Escudo $1M"


def test_simulate_scenario_tool():
    from backend.app.tools.copilot_tools import simulate_scenario
    config = RunnableConfig(configurable={"session_id": "s_sim_tool", "case_id": "michael-carter"})
    session = session_store.get_or_create("s_sim_tool", "michael-carter")

    res = simulate_scenario.invoke({
        "scenario_name": "Shock de $2,000 en taller",
        "emergency_expense": 2000.0,
        "horizon_months": 12
    }, config=config)

    assert "completada con exito" in res
    assert "Score proyectado" in res
    assert len(session.pending_charts) > 0
    assert "Simulacion" in session.pending_charts[-1]["title"]


@pytest.mark.asyncio
async def test_generate_advisor_report_tool():
    from backend.app.tools.copilot_tools import generate_advisor_report_tool
    config = RunnableConfig(configurable={"session_id": "s_rep_tool", "case_id": "michael-carter"})

    res = await generate_advisor_report_tool.ainvoke({}, config=config)
    assert "Ficha de acompanamiento generada" in res
    assert "Preguntas clave preparadas" in res





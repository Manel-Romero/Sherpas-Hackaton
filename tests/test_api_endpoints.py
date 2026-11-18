import pytest
from backend.app.services.session_store import session_store
from backend.app.models.dashboard import DashboardState, DashboardMetric

def test_root_and_health(client):
    # Comprueba los endpoints base de salud y documentacion
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["service"] == "Sherpas Wealth Co-Pilot API"

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

def test_api_list_cases(client):
    # Comprueba el endpoint GET /api/cases contra el servidor MCP
    r = client.get("/api/cases")
    assert r.status_code == 200
    cases = r.json()
    assert len(cases) == 4
    
    ids = [c["id"] for c in cases]
    assert "michael-carter" in ids
    assert "daniel-emily-johnson" in ids

def test_api_get_case_detail(client):
    # Comprueba la obtencion completa de un caso a traves del endpoint REST
    r = client.get("/api/cases/michael-carter")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "michael-carter"
    assert data["summary"]["score"] == 26
    assert "score" in data["financial_health"]
    assert len(data["persona_markdown"]) > 8000

def test_api_get_case_section(client):
    # Comprueba la consulta granular de secciones
    r = client.get("/api/cases/michael-carter/section?part=financial-health&section=score")
    assert r.status_code == 200
    section_data = r.json()
    assert section_data["case_id"] == "michael-carter"
    assert section_data["data"]["published_score"] == 26

def test_api_get_nonexistent_case(client):
    # Comprueba que un caso no existente responde con 404
    r = client.get("/api/cases/caso-inexistente-12345")
    assert r.status_code == 404
    assert "no encontrado" in r.json()["detail"].lower()

def test_api_tasks_crud(client):
    # Comprueba la creacion y actualizacion de tareas en la lista
    case_id = "michael-carter"
    
    # 1. Lista de tareas inicialmente vacia
    r_get = client.get(f"/api/cases/{case_id}/tasks")
    assert r_get.status_code == 200
    assert len(r_get.json()) == 0

    # 2. Crear una tarea
    r_create = client.post(
        f"/api/cases/{case_id}/tasks",
        json={
            "id": "task_demo_1",
            "title": "Configurar seguro de paraguas",
            "description": "Contratar poliza de 1M para elevar escudo de responsabilidad",
            "week": 1,
            "category": "insurance",
            "impact_metric": "Escudo de proteccion",
            "impact_value": "+5 pts score"
        }
    )
    assert r_create.status_code == 200
    created = r_create.json()
    assert created["id"] == "task_demo_1"
    assert created["status"] == "pending"

    # 3. Comprobar que la tarea aparece en la lista
    r_list = client.get(f"/api/cases/{case_id}/tasks")
    assert len(r_list.json()) == 1

    # 4. Actualizar estado de la tarea a completada
    r_patch = client.patch(
        f"/api/cases/{case_id}/tasks/task_demo_1",
        json={"status": "completed"}
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["status"] == "completed"

def test_api_dashboard_endpoints(client):
    # Comprueba la consulta y actualizacion del dashboard
    case_id = "michael-carter"
    session = session_store.get_or_create("default", case_id)
    
    # Simular estado inicial del dashboard en la sesion
    session.dashboard = DashboardState(
        case_id=case_id,
        health_score=26,
        net_worth=218500.0,
        total_assets=247000.0,
        total_liabilities=28500.0,
        monthly_income=15000.0,
        monthly_expenses=9306.0,
        monthly_free_cashflow=5694.0,
        metrics={
            "monthly_savings": DashboardMetric(
                id="monthly_savings",
                label="Ahorro Mensual",
                value=500.0,
                formatted_value="$500/mes",
                unit="$"
            )
        }
    )

    # 1. Obtener dashboard
    r_dash = client.get(f"/api/cases/{case_id}/dashboard")
    assert r_dash.status_code == 200
    assert r_dash.json()["health_score"] == 26
    assert r_dash.json()["net_worth"] == 218500.0

    # 2. Actualizar metrica mensual
    r_patch = client.patch(
        f"/api/cases/{case_id}/dashboard",
        json={
            "metric_key": "monthly_savings",
            "value": 250.0,
            "reason": "Ajuste temporal por gasto del taller"
        }
    )
    assert r_patch.status_code == 200
    updated_dash = r_patch.json()
    assert updated_dash["metrics"]["monthly_savings"]["value"] == 250.0
    assert updated_dash["metrics"]["monthly_savings"]["note"] == "Ajuste temporal por gasto del taller"


def test_api_scenarios_and_simulate(client):
    # Comprueba la obtencion de presets y la ejecucion de simulaciones What-If
    case_id = "michael-carter"
    
    # 1. Obtener presets
    r_pres = client.get(f"/api/cases/{case_id}/scenarios")
    assert r_pres.status_code == 200
    data_pres = r_pres.json()
    assert data_pres["case_id"] == case_id
    assert len(data_pres["presets"]) >= 3

    # 2. Ejecutar simulacion What-If
    sim_payload = {
        "scenario_name": "Shock de prueba",
        "params": {
            "emergency_expense": 2000.0,
            "horizon_months": 12
        }
    }
    r_sim = client.post(f"/api/cases/{case_id}/simulate", json=sim_payload)
    assert r_sim.status_code == 200
    res = r_sim.json()
    assert res["case_id"] == case_id
    assert "projected_score" in res
    assert len(res["timeline"]) == 12
    assert "verdict" in res


def test_api_handover_report(client):
    # Comprueba la generacion del informe de cliente y asesor
    case_id = "michael-carter"
    r_rep = client.get(f"/api/cases/{case_id}/report")
    assert r_rep.status_code == 200
    rep = r_rep.json()
    assert rep["case_id"] == case_id
    assert "markdown" in rep
    assert "html" in rep
    assert len(rep["advisor_questions"]) >= 3


def test_api_persona_insights(client):
    # Comprueba las dimensiones psicologicas y arquetipos
    case_id = "michael-carter"
    r_ins = client.get(f"/api/cases/{case_id}/persona-insights")
    assert r_ins.status_code == 200
    ins = r_ins.json()
    assert ins["case_id"] == case_id
    assert "wealth_tier" in ins
    assert "primary_tension" in ins
    assert len(ins["key_alerts"]) >= 2


def test_api_kanban_endpoints(client):
    # Comprueba los endpoints del tablero Kanban y el arrange de tarjetas
    case_id = "michael-carter"

    # 1. Obtener kanban
    r_get = client.get(f"/api/cases/{case_id}/kanban")
    assert r_get.status_code == 200
    kdata = r_get.json()
    assert kdata["case_id"] == case_id
    assert "cards" in kdata
    assert len(kdata["cards"]) > 0

    first_card = kdata["cards"][0]
    card_id = first_card["id"]

    # 2. Reorganizar / mover tarjeta de estado
    r_arr = client.post(
        f"/api/cases/{case_id}/kanban/arrange",
        json={"card_id": card_id, "to_status": "done", "to_index": 0}
    )
    assert r_arr.status_code == 200
    arr_data = r_arr.json()
    assert arr_data["success"] is True

    # 3. Anadir nueva tarjeta
    r_add = client.post(
        f"/api/cases/{case_id}/kanban/cards",
        json={
            "title": "Prueba de accion Kanban",
            "category": "savings",
            "impact": "+$100/mes",
            "week": 1,
            "steps": ["Paso 1 de prueba"]
        }
    )
    assert r_add.status_code == 200
    add_data = r_add.json()
    assert add_data["success"] is True
    new_cid = add_data["card"]["id"]

    # 4. Eliminar tarjeta creada
    r_del = client.delete(f"/api/cases/{case_id}/kanban/cards/{new_cid}")
    assert r_del.status_code == 200
    assert r_del.json()["success"] is True


def test_api_table_endpoints(client):
    # Comprueba la consulta y actualizacion de celdas en la tabla mensual
    case_id = "michael-carter"

    # 1. Obtener tabla
    r_tbl = client.get(f"/api/cases/{case_id}/table")
    assert r_tbl.status_code == 200
    tdata = r_tbl.json()
    assert "columns" in tdata
    assert "rows" in tdata
    assert len(tdata["rows"]) > 0

    # 2. Actualizar celda numerica
    first_date = tdata["rows"][0]["date"]
    r_cell = client.post(
        f"/api/cases/{case_id}/table/cell",
        json={"date": first_date, "column": "Gastos_Fijos", "value": 9306.0}
    )
    assert r_cell.status_code == 200
    assert r_cell.json()["success"] is True

    # 3. Obtener resumen de la tabla
    r_sum = client.get(f"/api/cases/{case_id}/table/summary")
    assert r_sum.status_code == 200
    sdata = r_sum.json()
    assert "net_worth" in sdata
    assert "free_cash_flow" in sdata



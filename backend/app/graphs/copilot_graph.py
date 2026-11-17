import logging
import json
from datetime import datetime
from typing import Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from backend.app.config import settings
from backend.app.graphs.state import CopilotState
from backend.app.services.session_store import session_store
from backend.app.services.llm_factory import get_chat_llm
from backend.app.services.audit_logger import log_prompt, log_tool_call, log_response
from backend.app.tools.copilot_tools import ALL_COPILOT_TOOLS

logger = logging.getLogger(__name__)

async def build_system_prompt(session_id: str, case_id: str) -> str:
    # Construye el prompt de sistema dinamicamente con el estado actual y datos reales del caso desde MCP
    session = session_store.get_or_create(session_id, case_id)
    summary = session.summary_executive or f"Caso activo: {case_id}."

    # Variables de inicializacion
    budget_breakdown_lines = []
    total_living_expenses = 0.0
    total_debt_payments = 0.0
    total_income_mo = 0.0
    score_published = "N/A"
    score_band = ""
    score_msg = ""
    net_worth_val = 0.0
    total_liabilities_val = 0.0
    total_assets_val = 0.0

    pillars_lines = []
    top_moves_lines = []
    goals_lines = []
    accounts_lines = []
    insurance_lines = []
    chart_expense_categories = []
    chart_expense_values = []
    asset_alloc_str = "Distribucion de activos en proceso de sincronizacion."
    cur_efc = {}
    tgt_efc = {}
    portfolio_conc_lines = []
    transition_alerts_str = ""
    objective_concerns_str = ""
    tensions_str = ""

    try:
        from backend.app.services.case_repository import case_repo
        raw_case = await case_repo.get_case(case_id)
        fh = raw_case.financial_health or {}
        prof = fh.get("profile", {})
        score_data = fh.get("score", {})
        score_published = score_data.get("published_score", "N/A")
        score_band = score_data.get("band", "")
        score_msg = score_data.get("message", "")
        km = fh.get("key_metrics", {})
        net_worth_val = float(km.get("net_worth") or 0.0)
        total_assets_val = float(km.get("total_assets") or 0.0)
        total_liabilities_val = float(km.get("total_liabilities") or 0.0)

        # 1. Pilares de Salud Financiera
        for p in score_data.get("pillars", []):
            p_name = p.get("pillar", "Pilar")
            p_pts = p.get("points_shown_in_app", "N/A")
            p_sc = p.get("score", 0)
            pillars_lines.append(f"  * {p_name}: {p_pts} (Rendimiento: {p_sc}%)")

        # 2. Top Moves (Acciones prioritarias calculadas por el algoritmo)
        for tm in score_data.get("top_moves", []):
            tm_title = tm.get("title", "")
            tm_action = tm.get("action", "")
            tm_effort = tm.get("effort", "medio")
            tm_before = tm.get("score_before", "")
            tm_after = tm.get("score_after", "")
            top_moves_lines.append(f"  * {tm_title} [Esfuerzo {tm_effort}]: {tm_action} (Impacto: {tm_before} -> {tm_after} pts)")

        # 3. Metas y Objetivos Vitales
        for g in fh.get("goals", {}).get("goalsSummary", []):
            g_val = g.get("value") or f"{g.get('goalType', 'Meta')}: ${g.get('amount', 0):,.0f}"
            goals_lines.append(f"  * {g_val}")

        # 4. Cuentas y Saldos
        for a in prof.get("accounts", []):
            a_name = a.get("name", "Cuenta")
            a_type = a.get("account_type", "")
            a_tax = a.get("tax_treatment", "")
            a_bal = float(a.get("balance", 0))
            a_contrib = float(a.get("yearly_contribution_total", 0))
            a_owner = ", ".join(a.get("owner", [])) if isinstance(a.get("owner"), list) else a.get("owner", "")
            owner_info = f" (Titular: {a_owner})" if a_owner else ""
            contrib_info = f" | Aporte anual: ${a_contrib:,.0f}" if a_contrib > 0 else ""
            accounts_lines.append(f"  * {a_name} ({a_type}, {a_tax}){owner_info}: Saldo ${a_bal:,.0f}{contrib_info}")

        # 5. Polizas de Seguro
        for ins in prof.get("insurance", []):
            ins_name = ins.get("name", "Seguro")
            ins_type = ins.get("type", "")
            ins_cov = ins.get("coverage", "No registrada")
            ins_cov_str = f"${float(ins_cov):,.0f}" if isinstance(ins_cov, (int, float)) else str(ins_cov)
            insurance_lines.append(f"  * {ins_name} ({ins_type}): Cobertura {ins_cov_str}")

        # 6. Gastos mensuales
        expenses_details = []
        for exp in prof.get("expenses", []):
            name = exp.get("name", "Gasto")
            m_amt = float(exp.get("monthly") or (exp.get("yearly", 0) / 12))
            total_living_expenses += m_amt
            expenses_details.append(f"  * {name}: ${m_amt:,.0f}/mes (${exp.get('yearly', m_amt*12):,.0f}/ano)")
            if m_amt > 0:
                chart_expense_categories.append(name)
                chart_expense_values.append(round(m_amt))

        # 7. Cuotas de deudas
        debts_details = []
        for d in prof.get("liabilities", []):
            d_name = d.get("name", "Deuda")
            d_pay = float(d.get("monthly_payment", 0))
            d_bal = float(d.get("balance", 0))
            d_rate = float(d.get("interest_rate", 0)) * 100
            total_debt_payments += d_pay
            debts_details.append(f"  * {d_name}: cuota ${d_pay:,.0f}/mes (saldo ${d_bal:,.0f}, TAE {d_rate:.1f}%)")
            if d_pay > 0:
                chart_expense_categories.append(f"Deuda: {d_name}")
                chart_expense_values.append(round(d_pay))

        # 8. Ingresos (diferenciando ingresos actuales de ingresos futuros de jubilacion/seguridad social)
        incomes_details = []
        future_incomes_details = []
        current_year = datetime.now().year
        for inc in prof.get("incomes", []):
            i_name = inc.get("name", "Salario")
            i_yr = float(inc.get("yearly", 0))
            i_mo = i_yr / 12
            starts = inc.get("starts")
            if starts and starts > current_year:
                future_incomes_details.append(f"  * {i_name} (proyectado a partir de {starts}): ${i_yr:,.0f}/ano (${i_mo:,.0f}/mes)")
            else:
                total_income_mo += i_mo
                incomes_details.append(f"  * {i_name}: ${i_mo:,.0f}/mes (${i_yr:,.0f}/ano)")

        total_outgoing = total_living_expenses + total_debt_payments
        free_cf = total_income_mo - total_outgoing

        budget_breakdown_lines.append(f"Score de Salud Financiera: {score_published}/100 ({score_band}) - {score_msg}")
        budget_breakdown_lines.append(f"Ingresos mensuales netos actuales ({current_year}): ${total_income_mo:,.0f}/mes")
        for i_line in incomes_details:
            budget_breakdown_lines.append(i_line)
        if future_incomes_details:
            budget_breakdown_lines.append("\nIngresos futuros proyectados (jubilacion/seguridad social):")
            for f_line in future_incomes_details:
                budget_breakdown_lines.append(f_line)
        budget_breakdown_lines.append(f"\nGastos mensuales de vida y vivienda: ${total_living_expenses:,.0f}/mes")
        for e_line in expenses_details:
            budget_breakdown_lines.append(e_line)
        budget_breakdown_lines.append(f"\nCuotas mensuales de deuda: ${total_debt_payments:,.0f}/mes")
        for d_line in debts_details:
            budget_breakdown_lines.append(d_line)
        budget_breakdown_lines.append(f"\nTOTAL SALIENTE REAL MENSUAL: ${total_outgoing:,.0f}/mes")
        budget_breakdown_lines.append(f"FLUJO LIBRE REAL MENSUAL: ${free_cf:,.0f}/mes")

        # 9. Inversiones y Asignacion de Activos (investment-analysis)
        ia = raw_case.investment_analysis or {}
        ia_summary = ia.get("analysis", {}).get("summary", {}).get("assetAllocation", {})
        cur_efc = ia_summary.get("currentEFC", {})
        tgt_efc = ia_summary.get("targetEFC", {})
        if cur_efc or tgt_efc:
            asset_alloc_str = (
                f"- Distribucion Actual: Renta Variable (Acciones) {cur_efc.get('equity', 0)*100:.1f}%, "
                f"Renta Fija (Bonos) {cur_efc.get('fixedIncome', 0)*100:.1f}%, Efectivo {cur_efc.get('cash', 0)*100:.1f}%\n"
                f"- Distribucion Objetivo de Sherpas: Renta Variable (Acciones) {tgt_efc.get('equity', 0)*100:.1f}%, "
                f"Renta Fija (Bonos) {tgt_efc.get('fixedIncome', 0)*100:.1f}%, Efectivo {tgt_efc.get('cash', 0)*100:.1f}%"
            )

        km_ia = ia.get("key_metrics", {}).get("concentrationAndDiversification", {})
        totals = km_ia.get("totals", {})
        if totals:
            portfolio_conc_lines.append(
                f"  * Cartera invertible: ${totals.get('investablePortfolioValue', 0):,.0f} "
                f"distribuida en {totals.get('holdings', 0)} posiciones (Exposicion en renta variable: ${totals.get('equityExposure', 0):,.0f})."
            )
        geography = km_ia.get("geographyByRegion", [])
        if len(geography) > 1:
            geo_parts = []
            for row in geography[1:]:
                if isinstance(row, list) and len(row) >= 2:
                    try:
                        geo_parts.append(f"{row[0]}: {float(row[1])*100:.1f}%")
                    except (ValueError, TypeError):
                        pass
            if geo_parts:
                portfolio_conc_lines.append(f"  * Sesgo geografico: {', '.join(geo_parts[:4])}")

        # 10. Perfil Conductual, Preocupaciones y Tensiones (persona.md)
        persona_text = raw_case.persona_markdown or ""
        if persona_text:
            t_alerts_idx = persona_text.find("## Transition alerts")
            sub_idx = persona_text.find("## Subjective concerns")
            obj_idx = persona_text.find("## Objective concerns")
            tens_idx = persona_text.find("## Tensions")
            class_idx = persona_text.find("```classification")

            if t_alerts_idx != -1:
                end_alert = sub_idx if sub_idx != -1 else (obj_idx if obj_idx != -1 else len(persona_text))
                raw_alert = persona_text[t_alerts_idx:end_alert].replace("## Transition alerts", "").strip()
                if raw_alert:
                    transition_alerts_str = raw_alert

            if obj_idx != -1:
                end_obj = tens_idx if tens_idx != -1 else (class_idx if class_idx != -1 else len(persona_text))
                raw_obj = persona_text[obj_idx:end_obj].replace("## Objective concerns", "").strip()
                if raw_obj:
                    objective_concerns_str = raw_obj

            if tens_idx != -1:
                end_tens = class_idx if class_idx != -1 else len(persona_text)
                raw_tens = persona_text[tens_idx:end_tens].replace("## Tensions", "").strip()
                if raw_tens:
                    tensions_str = raw_tens

    except Exception as e:
        logger.warning(f"No se pudo cargar el perfil detallado del caso {case_id}: {e}")

    budget_breakdown_text = "\n".join(budget_breakdown_lines) if budget_breakdown_lines else "Detalle de presupuesto en proceso de sincronizacion."
    pillars_text = "\n".join(pillars_lines) if pillars_lines else "Pillars no disponibles."
    top_moves_text = "\n".join(top_moves_lines) if top_moves_lines else "Top moves no disponibles."
    goals_text = "\n".join(goals_lines) if goals_lines else "Metas no especificadas."
    accounts_text = "\n".join(accounts_lines) if accounts_lines else "Cuentas en proceso de sincronizacion."
    insurance_text = "\n".join(insurance_lines) if insurance_lines else "Polizas en proceso de sincronizacion."
    portfolio_conc_text = "\n".join(portfolio_conc_lines) if portfolio_conc_lines else ""

    # Resumen del dashboard financiero
    if session.dashboard:
        db = session.dashboard
        dashboard_summary = (
            f"Health Score: {db.health_score}/100 | "
            f"Patrimonio Neto: ${db.net_worth:,.0f} | "
            f"Total Activos: ${db.total_assets:,.0f} | "
            f"Total Deudas: ${db.total_liabilities:,.0f} | "
            f"Ingreso Mensual: ${db.monthly_income:,.0f} | "
            f"Gastos Mensuales: ${db.monthly_expenses:,.0f} | "
            f"Cashflow Libre: ${db.monthly_free_cashflow:,.0f}"
        )
    elif total_living_expenses > 0 or total_income_mo > 0:
        tot_out = total_living_expenses + total_debt_payments
        dashboard_summary = (
            f"Health Score: {score_published}/100 | "
            f"Patrimonio Neto: ${net_worth_val:,.0f} | "
            f"Total Activos: ${total_assets_val:,.0f} | "
            f"Total Deudas: ${total_liabilities_val:,.0f} | "
            f"Ingreso Mensual: ${total_income_mo:,.0f} | "
            f"Gastos Mensuales: ${tot_out:,.0f} | "
            f"Cashflow Libre: ${(total_income_mo - tot_out):,.0f}"
        )
    else:
        dashboard_summary = "Dashboard aun no inicializado."

    # Resumen de la lista de tareas
    if session.tasks:
        tasks_lines = [
            f"- [{t.status.upper()}] {t.id}: {t.title} (Semana {t.week}) -> Impacto: {t.impact.value if t.impact else 'N/A'}"
            for t in session.tasks
        ]
        tasks_summary = "\n".join(tasks_lines)
    else:
        tasks_summary = "No hay tareas activas en este momento."

    # Estado actual de la hoja de calculo mensual (table_store)
    table_info_str = "No disponible"
    try:
        from frontend import table_store as ts
        tb_data = ts.load(case_id=case_id)
        tb_cols = tb_data.get("columns", [])
        tb_rows = tb_data.get("rows", [])
        dates_list = [r.get("date") for r in tb_rows if r.get("date")]
        dates_range_str = f"desde {dates_list[0]} hasta {dates_list[-1]}" if dates_list else "sin filas"
        table_info_str = (
            f"Columnas registradas: {tb_cols}\n"
            f"Meses disponibles: {dates_range_str} ({len(dates_list)} filas registradas)"
        )
    except Exception as e:
        table_info_str = f"Error leyendo tabla: {e}"

    # Estado actual del tablero Kanban (kanban_store)
    kanban_info_str = "No disponible"
    try:
        import kanban_store as ks
        kb_data = ks.load(case_id=case_id)
        kb_cards = kb_data.get("cards", [])
        card_summaries = [
            f"  * [{c.get('status')}] ID '{c.get('id')}': {c.get('title')}"
            for c in kb_cards
        ]
        kanban_info_str = "\n".join(card_summaries) if card_summaries else "Sin tarjetas en el tablero."
    except Exception as e:
        kanban_info_str = f"Error leyendo kanban: {e}"

    transition_alerts_section = f"\n=== ALERTAS DE TRANSICION Y CALENDARIO ===\n{transition_alerts_str}" if transition_alerts_str else ""
    objective_concerns_section = f"\n=== PREOCUPACIONES OBJETIVAS DETECTADAS ===\n{objective_concerns_str}" if objective_concerns_str else ""
    tensions_section = f"\n=== TENSIONES ESTRATEGICAS DEL CASO ===\n{tensions_str}" if tensions_str else ""

    chart_cat_json = json.dumps(chart_expense_categories, ensure_ascii=False) if chart_expense_categories else "['Gastos de Vida', 'Vivienda', 'Deudas']"
    chart_val_json = json.dumps(chart_expense_values) if chart_expense_values else "[5000, 2000, 1000]"

    cur_equity_pct = round(cur_efc.get('equity', 0)*100, 1)
    cur_fi_pct = round(cur_efc.get('fixedIncome', 0)*100, 1)
    cur_cash_pct = round(cur_efc.get('cash', 0)*100, 1)

    prompt = f"""Eres el Asesor Financiero Co-Pilot de Sherpas Wealth, guiando a la familia en tiempo real.
Tu mision es acompanar al usuario con empatia, responder sus preguntas con rigor, motivarle a actuar y mantener sincronizada la interfaz.

=== RESUMEN EJECUTIVO Y PERFIL DEL CASO ===
{summary}

=== PILARES DE SALUD FINANCIERA (SHERPAS HEALTH SCORE) ===
Score Global Publicado: {score_published}/100 ({score_band}) - {score_msg}
Desglose por Pilares:
{pillars_text}

=== TOP MOVES ALGORITMICOS DE SHERPAS (ACCIONES PRIORITARIAS CALCULADAS) ===
{top_moves_text}

=== OBJETIVOS FINANCIEROS Y METAS VITALES ===
{goals_text}
{transition_alerts_section}

=== CUENTAS, ACTIVOS Y COBERTURAS DE PROTECCION ===
Cuentas y Posiciones de Liquidez/Inversion:
{accounts_text}

Polizas y Coberturas de Seguro:
{insurance_text}

=== DESGLOSE OFICIAL DE INGRESOS, GASTOS Y DEUDAS ===
{budget_breakdown_text}

=== ASIGNACION DE ACTIVOS Y CARTERA DE INVERSIONES ===
{asset_alloc_str}
{portfolio_conc_text}

=== PREOCUPACIONES OBJETIVAS Y TENSIONES ESTRATEGICAS ===
{objective_concerns_section}
{tensions_section}

=== ESTADO ACTUAL DEL DASHBOARD FINANCIERO ===
{dashboard_summary}

=== LISTA DE TAREAS ACTUAL ===
{tasks_summary}

=== HOJA DE CALCULO MENSUAL ACTUAL (TABLE STORE) ===
{table_info_str}

=== TABLERO KANBAN ACTUAL (KANBAN STORE) ===
Columnas del tablero: 'todo' (To do), 'in_process' (In process), 'done' (Done)
Tarjetas actuales:
{kanban_info_str}

=== FECHA Y MES DE REFERENCIA ===
Mes actual de la sesion: {datetime.now().strftime("%Y-%m")}

=== CAPACIDADES Y HERRAMIENTAS MCP DISPONIBLES ===
Tienes herramientas nativas de hoja de calculo (tipo Excel) totalmente abiertas y flexibles para modelar cualquier escenario con creatividad y rigor, sin nada hardcodeado:
1. `get_table`: Devuelve la tabla mensual completa con todas sus columnas y filas en formato JSON para inspeccionar o verificar datos.
2. `set_cell` / `modify_table_cell`: Define o modifica manualmente una celda especifica (date 'YYYY-MM', column, value numerico directo).
3. `set_cells`: Define manualmente varias celdas a la vez con una lista de diccionarios con date, column y value.
4. `set_cell_formula`: Define una celda mediante una formula o expresion de Excel (ej: formula='prev * 1.10', 'Ingresos * 0.20', 'value + 1500').
5. `apply_column_formula`: Aplica una funcion o formula de Excel a toda una columna a traves de los meses (ej: formula='prev * 1.10' para interes o crecimiento compuesto, 'Ingresos - Gastos_Fijos' para balance, 'Ingresos * 0.15' para ahorro, 'max(0, prev - 500)' para amortizacion progresiva).
6. `add_column` / `add_table_column`: Anade una nueva columna a la tabla (ej: 'Ahorro_Vacaciones', 'Amortizacion_Extra', 'Inversion_Indexada') con valor por defecto o calculada mediante formula.
7. `delete_column`: Elimina una columna existente de la tabla mensual.
8. `set_row`: Crea o actualiza una fila mensual completa con un diccionario de columnas y valores.
9. `delete_row`: Elimina una fila mensual por su fecha 'YYYY-MM'.
10. `evaluate_formula`: Calculadora abierta para cualquier formula matematica o financiera de Excel (ej: '15000 * (1.10 ** 12)', 'PV * (1 + 0.07)**10').
11. `spreadsheet_aggregate`: Calcula agregaciones estilo Excel (sum, average, min, max, growth_rate) sobre cualquier columna.
12. `project_growth`: Aplica una proyeccion de crecimiento mensual (lineal o compuesto) a una columna en todos los meses registrados.
13. `manage_box`: Gestiona tarjetas estructuradas en el panel vertical y las sincroniza con el tablero Kanban.
14. `add_kanban_card`: Anade una tarjeta al tablero Kanban (title, content, status 'todo'/'in_process'/'done').
15. `move_kanban_card`: Mueve una tarjeta de columna en el tablero Kanban.
16. `delete_kanban_card`: Elimina una tarjeta del tablero Kanban.
17. `display_chart`: Muestra graficos interactivos en la interfaz (donut, bar, line).
18. `inspect_case_data`: Consulta detalles profundos del caso en el servidor MCP oficial de Sherpas (part: 'financial-health', 'investment-analysis', 'persona').
19. `manage_task`: Gestiona la lista de tareas pendientes (action: 'add', 'complete', 'delete').
20. `update_dashboard_metric`: Actualiza metricas globales del dashboard.

DIRECTRICES OPERATIVAS:
- HERRAMIENTAS ABIERTAS Y CREATIVIDAD ESTILO EXCEL (NADA HARDCODEADO):
  * Tienes total libertad para modelar escenarios usando formulas, definiendo celdas manuales, anadiendo columnas personalizadas o calculando series.
  * NUNCA te limites a decir en texto que 'lo has actualizado' o 'lo vas a anotar'.
  * SIEMPRE que el usuario reporte un gasto imprevisto, pida modificar un valor, proyectar un crecimiento, anadir una columna, mover una tarea o definir una formula, DEBES INVOCAR OBLIGATORIAMENTE LAS HERRAMIENTAS CORRESPONDIENTES MEDIANTE LLAMADAS DE FUNCION NATIVAS (tool_calls).
  * Si no ejecutas la llamada a la herramienta, el sistema registrara que NO se llamo al MCP y nada cambiara en la pantalla del usuario.
  * Ejemplos de uso de herramientas de Excel:
    - Crecimiento mensual compuesto (ej: 'aumenta un 10% cada mes. Es compuesto', 'ganare un 10% mas cada mes'):
      Llama a `apply_column_formula(column='Ingresos', formula='prev * 1.10')` o a `project_growth(column='Ingresos', rate_pct=10.0, compounding=True)`.
    - Ajuste manual de celdas o partidas:
      Llama a `set_cell` o `set_cell_formula` (o `set_cells` para multiples celdas).
    - Nueva partida o meta de ahorro:
      Llama a `add_column(name='Ahorro_Casa', formula='Ingresos * 0.15')` para crear y calcular la columna dinamicamente.
    - Imprevisto o gasto extraordinario:
      Llama a `set_cell` (o `set_cell_formula`) para reflejarlo en la tabla y a `manage_box` para anadir la tarjeta explicativa.
  * Si el usuario te indica 'no lo veo en el dashboard', 'no ha cambiado' o te insiste con una correccion:
    NUNCA respondas con preguntas evasivas ni digas que ya lo hiciste si no llamaste a las herramientas. DEBES EJECUTAR INMEDIATAMENTE `apply_column_formula`, `project_growth` o `set_cells` y `update_dashboard_metric` en esta misma llamada para que los datos queden grabados y sincronizados en vivo.
- IDENTIDAD INSTITUCIONAL (ERES EL ASESOR FINANCIERO DE SHERPAS WEALTH):
  * ERES el Asesor Financiero Personal del cliente dentro de la firma Sherpas Wealth. Tienes todo su expediente patrimonial delante.
  * NUNCA, bajo ningun concepto, le digas al cliente que 'consulte con un asesor financiero', 'hable con un planificador' o 'busque a un profesional externo'. TU Y SHERPAS WEALTH SOIS SU ASESORIA FINANCIERA!
  * Recomendar buscar un asesor externo es romper el personaje y un fallo grave de contexto: el cliente ya esta hablando contigo dentro de su plataforma contratada.
  * Asume siempre el rol activo de asesor patrimonial: analiza sus cuentas, dale recomendaciones directas de asignacion de activos, desglosa sus deudas y guiale paso a paso con autoridad profesional, rigor y empatia. Siempre dentro del plan de Sherpas Wealth.
- COMUNICACION CLARA Y ACCESIBLE (PARA NO TECNICOS): Explica los conceptos financieros de manera intuitiva y directa, sin tecnicismos ni jerga bancaria compleja. Usa analogias cotidianas cuando ayude a clarificar (ej: hablar de 'colchon de seguridad', 'lo que queda limpio a fin de mes' o 'el coste del interes' en lugar de terminos academicos).
- RESPETO Y EMPATIA (NUNCA HACER SENTIR ESTUPIDO AL CLIENTE): Trata al usuario como un adulto inteligente que simplemente no es experto en finanzas. Evita por completo tonos condescendientes, paternalistas o frases infantilizadoras (como 'esto es muy facilito' o reganos). Si el score es bajo o la situacion es delicada, enfoca la conversacion con serenidad y orientacion a soluciones, normalizando los baches y empoderando al cliente con pasos accionables.
- CONSULTAS SOBRE GASTOS Y PRESUPUESTO ("En que se me va el dinero?" o "En que gasto?"):
  * NUNCA inventes categorias genericas ni digas que "no tienes los detalles especificos". TIENES EL DESGLOSE OFICIAL EXACTO EN LA SECCION "DESGLOSE OFICIAL DE INGRESOS, GASTOS Y DEUDAS" DE ARRIBA.
  * NUNCA digas que sus gastos son 'ahorros e inversiones'. Sus gastos corresponden a partidas reales de vida, vivienda y servicio de deuda.
  * Explica con claridad y calidez humana las partidas reales del cliente mostrando con precision los gastos esenciales, vivienda y amortizacion de deudas.
  * Siempre que te pregunten en que se va el dinero o te pidan un desglose visual, INVOCA DIRECTAMENTE la herramienta `display_chart` mediante llamada a funcion nativa (tool_call). NUNCA escribas la llamada a display_chart en bloques de codigo markdown ni en texto plano.
    Parametros dinamicos para la herramienta display_chart:
    - chart_type: 'donut'
    - title: 'Distribucion Real de Gastos Mensuales (${total_outgoing:,.0f}/mes)'
    - categories: {chart_cat_json}
    - values: {chart_val_json}
  * Si te piden una comparativa entre ingresos y gastos o flujo libre (ej: el boton 'Comparativa visual'), invoca la herramienta `display_chart` mediante llamada a funcion nativa (tool_call) con:
    - chart_type: 'bar'
    - title: 'Ingresos vs Gastos y Flujo Libre Mensual'
    - categories: ['Ingresos Netos', 'Gastos de Vida', 'Pago de Deudas', 'Flujo Libre']
    - values: [{round(total_income_mo)}, {round(total_living_expenses)}, {round(total_debt_payments)}, {round(free_cf)}]
- CONSULTAS SOBRE INVERSIONES Y ASIGNACION DE ACTIVOS:
  * Utiliza los datos de la seccion "ASIGNACION DE ACTIVOS Y CARTERA DE INVERSIONES".
  * Explica con claridad la diferencia entre su asignacion actual y la asignacion objetivo recomendada por Sherpas (Renta Variable / Renta Fija / Efectivo), alertando sobre ineficiencias fiscales o falta de diversificacion si existen.
  * Si el cliente pide ver su asignacion de activos en grafico, invoca `display_chart` con:
    - chart_type: 'donut'
    - title: 'Asignacion Actual de Inversiones'
    - categories: ['Renta Variable (Acciones)', 'Renta Fija (Bonos)', 'Efectivo']
    - values: [{cur_equity_pct}, {cur_fi_pct}, {cur_cash_pct}]
- CONSULTAS SOBRE METAS VITALES Y TRANSICIONES (COMPRA DE VIVIENDA, JUBILACION, ETC.):
  * Utiliza los datos exactos de las secciones "OBJETIVOS FINANCIEROS Y METAS VITALES", "ALERTAS DE TRANSICION" y "TENSIONES ESTRATEGICAS".
  * Explica las tensiones de forma clara y constructiva (ej: para Michael Carter, como el pago inicial de $113,300 para la casa en 2027 compite directamente con el interes compuesto de la jubilacion y absorbe la liquidez disponible).
- CONSULTAS SOBRE CAMBIOS SALARIALES, CRECIMIENTO O PROYECCIONES MES A MES:
  * Si el usuario informa de un aumento salarial o proyeccion (ej: 'ganar un 10% cada mes durante los proximos anos', 'aumento de ingresos', 'es compuesto', 'aumenta un X% cada mes'):
    a) INVOCA DIRECTAMENTE la herramienta `project_growth` pasando column='Ingresos', rate_pct=porcentaje, compounding=True (o False si es lineal).
    b) En tu respuesta, explica de forma accesible y motivadora para gente no experta como esta progresion compuesta incrementa su flujo de caja libre cada mes, alivia la presion de sus metas vitales y acelera la creacion de patrimonio.
- REGLA DE EJECUCION DE HERRAMIENTAS: Todas las herramientas (`project_growth`, `display_chart`, `manage_box`, `set_cell`, `set_cells`, `update_dashboard_metric`, etc.) DEBEN ejecutarse exclusivamente mediante llamadas de funcion estructuradas (tool_calls). NUNCA escribas pseudocodigo ni nombres de herramientas en texto o bloques markdown.
- PROACTIVIDAD INMEDIATA ANTE IMPREVISTOS: Si el usuario te informa de un imprevisto, gasto o accidente ocurrido (ej: 'he tenido un accidente y he tenido que desembolsar 2k $' o 'tuve que pagar una averia'), NUNCA pidas permiso ni preguntes si quiere que lo anadas. DEBES INVOCAR DIRECTAMENTE las herramientas pertinentes en esta misma ejecucion:
  a) Usa `manage_box` para registrar una tarjeta visible con datos limpios y estructurados:
     - title: Titulo conciso sin corchetes ni emojis (ej: 'Fondo de contingencia por siniestro').
     - category: 'alerta' o 'immediate'.
     - description: Explicacion clara de la contingencia y de como se absorbe de forma sencilla.
     - impact: Impacto cuantificado si aplica (ej: '-$2,000 en liquidez').
     - steps: Lista Python de pasos a seguir (ej: ['Notificar al perito del seguro', 'Reasignar excedente de ahorro de este mes']). NUNCA unas los pasos con barras '|'.
  b) Usa `set_cell` o `modify_table_cell` para ajustar los gastos o ahorro del mes actual en la tabla.
  c) Si procede, usa `update_dashboard_metric` o `manage_task`.
- Despues de ejecutar las herramientas, en tu mensaje confirma de forma calida lo que acabas de actualizar en la interfaz, interesate por su bienestar y demuestra como el plan maestro absorbe el bache sin desviarse de los objetivos patrimoniales a largo plazo.
- IDIOMA Y ORTOGRAFIA: Responde siempre en castellano CON acentos y ortografia correcta en todos tus mensajes al cliente."""
    return prompt

async def agent_node(state: CopilotState, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
    # Nodo del agente: extrae contexto de config de forma aislada y ejecuta el modelo
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id") or state.get("case_id", "michael-carter")
    session_id = configurable.get("session_id") or state.get("session_id", "default")

    system_prompt = await build_system_prompt(session_id, case_id)
    raw_messages = state.get("messages", [])

    # Registrar el prompt del usuario en auditoria
    last_human = next((m.content for m in reversed(raw_messages) if isinstance(m, HumanMessage)), "")
    if last_human:
        log_prompt(session_id, case_id, str(last_human), system_prompt[:400])

    # Filtrar mensajes de sistema previos e inyectar el prompt actualizado al inicio
    conversation = [m for m in raw_messages if not isinstance(m, SystemMessage)]
    messages = [SystemMessage(content=system_prompt)] + conversation

    llm = get_chat_llm(streaming=True)
    llm_with_tools = llm.bind_tools(ALL_COPILOT_TOOLS)
    response = await llm_with_tools.ainvoke(messages, config=config)

    # Registrar respuesta si contiene contenido textual
    if response.content:
        log_response(
            session_id=session_id,
            case_id=case_id,
            reply=str(response.content),
            tools_count=len(response.tool_calls or [])
        )

    return {"messages": [response]}

async def audit_tools_node(state: CopilotState, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
    # Nodo de ejecucion de herramientas con deteccion de modificaciones reales y auditoria
    configurable = config.get("configurable", {}) if config else {}
    case_id = configurable.get("case_id") or state.get("case_id", "michael-carter")
    session_id = configurable.get("session_id") or state.get("session_id", "default")
    session = session_store.get_or_create(session_id, case_id)

    tool_map = {t.name: t for t in ALL_COPILOT_TOOLS}
    raw_messages = state.get("messages", [])
    last_message = raw_messages[-1] if raw_messages else None

    tool_messages = []
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        from frontend import table_store as ts
        from frontend import boxes_store as bs
        import kanban_store as ks

        for tc in last_message.tool_calls:
            t_name = tc.get("name")
            t_args = tc.get("args") or {}
            t_id = tc.get("id")

            # Snapshots previos
            ts_ver_before = ts.version(case_id)
            ts_data_before = ts.load(case_id)
            ks_ver_before = ks.version(case_id)
            ks_data_before = ks.load(case_id)
            bs_ver_before = bs.version(case_id)
            tasks_before = [t.model_dump() for t in session.tasks]
            dash_before = session.dashboard.model_dump() if session.dashboard else None
            charts_before = len(session.pending_charts)

            tool_obj = tool_map.get(t_name)
            if not tool_obj:
                res = f"Error: Herramienta '{t_name}' no encontrada."
            else:
                try:
                    if hasattr(tool_obj, "ainvoke"):
                        res = await tool_obj.ainvoke(t_args, config=config)
                    else:
                        res = tool_obj.invoke(t_args, config=config)
                except Exception as e:
                    res = f"Error ejecutando {t_name}: {str(e)}"

            # Snapshots posteriores
            ts_ver_after = ts.version(case_id)
            ts_data_after = ts.load(case_id)
            ks_ver_after = ks.version(case_id)
            ks_data_after = ks.load(case_id)
            bs_ver_after = bs.version(case_id)
            tasks_after = [t.model_dump() for t in session.tasks]
            dash_after = session.dashboard.model_dump() if session.dashboard else None
            charts_after = len(session.pending_charts)

            modified = False
            diff_parts = []
            if ts_ver_after != ts_ver_before or ts_data_after != ts_data_before:
                modified = True
                diff_parts.append(f"Tabla mensual modificada por {t_name}")
            if ks_ver_after != ks_ver_before or ks_data_after != ks_data_before:
                modified = True
                diff_parts.append(f"Tablero Kanban modificado por {t_name}")
            if bs_ver_after != bs_ver_before:
                modified = True
                diff_parts.append(f"Panel visual modificado por {t_name}")
            if tasks_after != tasks_before:
                modified = True
                diff_parts.append(f"Tareas actualizadas por {t_name}")
            if dash_after != dash_before:
                modified = True
                diff_parts.append(f"Dashboard actualizado por {t_name}")
            if charts_after > charts_before:
                modified = True
                diff_parts.append(f"Grafico interactivo preparado por {t_name}")

            diff_str = "; ".join(diff_parts) if modified else "Sin alteracion de datos (lectura o sin cambios)"

            # Registrar en auditoria persistente
            log_tool_call(
                session_id=session_id,
                case_id=case_id,
                tool_name=t_name,
                args=t_args,
                result=res,
                modified=modified,
                diff=diff_str
            )

            if modified:
                session.last_change_applied = diff_str

            session.recent_tool_audits.append({
                "tool": t_name,
                "args": t_args,
                "result": str(res),
                "modified": modified,
                "diff": diff_str
            })

            tool_messages.append(ToolMessage(content=str(res), tool_call_id=t_id, name=t_name))

    return {"messages": tool_messages}

from langgraph.checkpoint.memory import MemorySaver

# Definicion del grafo ciclico ReAct con auditoria y memoria persistente
copilot_builder = StateGraph(CopilotState)
copilot_builder.add_node("agent", agent_node)
copilot_builder.add_node("tools", audit_tools_node)

copilot_builder.add_edge(START, "agent")
# Si el agente emitio llamadas a herramientas vamos a tools. Si termino, vamos a END.
copilot_builder.add_conditional_edges("agent", tools_condition, ["tools", END])
# Desde tools volvemos ciclicamente a agent para razonar sobre los resultados
copilot_builder.add_edge("tools", "agent")

# Compilacion con checkpointer de memoria para persistir la conversacion por thread_id
copilot_checkpointer = MemorySaver()
copilot_graph = copilot_builder.compile(checkpointer=copilot_checkpointer)

"""Generador modular de informes ejecutivos de entrega al cliente y asesor (Handover Report).
Produce tanto formato Markdown como HTML imprimible de alta fidelidad,
facilitando la transicion de la planificacion digital a la reunion presencial.
"""
from typing import Optional, Any
from datetime import datetime
from backend.app.services.session_store import session_store
from backend.app.services.case_repository import case_repo


async def generate_client_handover_report(case_id: str, session_id: str = "default") -> dict[str, Any]:
    """Genera un informe completo para el cliente y el asesor con diagnostico,
    acciones completadas, proyecciones y preguntas clave para la sesion.
    """
    session = session_store.get_or_create(session_id, case_id)
    raw_case = await case_repo.get_case(case_id)

    fh = raw_case.financial_health or {}
    prof = fh.get("profile", {})
    score_data = fh.get("score", {})
    score_val = score_data.get("published_score", 0)
    score_band = score_data.get("band", "N/A")
    household_raw = raw_case.summary.household if raw_case.summary else []
    household_names = ", ".join([h.first_name for h in household_raw]) or raw_case.summary.title
    case_title = raw_case.summary.title if raw_case.summary else case_id
    case_city = raw_case.summary.city if raw_case.summary else ""

    # Datos financieros
    inc = prof.get("incomes", [])
    exp = prof.get("expenses", [])
    liab = prof.get("liabilities", [])

    tot_inc = sum(float(i.get("yearly", 0)) / 12 for i in inc)
    tot_exp = sum(float(e.get("monthly", 0)) or (float(e.get("yearly", 0)) / 12) for e in exp)
    tot_debt_pmt = sum(float(l.get("monthly_payment", 0)) for l in liab)
    tot_debt_bal = sum(float(l.get("balance", 0)) for l in liab)

    # Estado de tareas
    tasks = session.tasks
    completed_tasks = [t for t in tasks if t.status == "completed"]
    pending_tasks = [t for t in tasks if t.status != "completed"]

    # Objetivos declarados
    goals_list = [g.get("value") or g.get("goalType", "Meta") for g in fh.get("goals", {}).get("goalsSummary", [])]

    # Preguntas recomendadas segun el perfil
    advisor_questions = []
    if case_id == "michael-carter":
        advisor_questions = [
            "¿Como podemos armonizar la entrada de $113,300 para la vivienda en 2027 sin penalizar el interes compuesto de mi 401(k)?",
            "¿Que vehiculo de renta fija o cuenta de alto rendimiento (HYSA) me recomiendas para el capital de la entrada?",
            "Si liquido anticipadamente los $3,500 de la tarjeta de credito, ¿cual es el ritmo optimo para reponer el fondo de emergencia?"
        ]
    elif case_id == "timothy-melanie-weah":
        advisor_questions = [
            "Dado que contamos con $150k de liquidez, ¿cual es la estrategia fiscalmente mas eficiente para amortizar la tarjeta al 18% de inmediato?",
            "¿Que estructura de cartera (80/20 vs 70/30) nos permite conciliar la tolerancia al riesgo de Timothy con la necesidad de seguridad de Melanie?",
            "¿Conviene abrir planes 529 separados para Liam y Josh o centralizar el ahorro universitario?"
        ]
    elif case_id == "daniel-emily-johnson":
        advisor_questions = [
            "¿Que tipo de poliza de vida a termino fijo se adapta mejor para cubrir la brecha hasta los $1.6M recomendados?",
            "¿Como priorizamos entre la aportacion a la universidad de Oliver y Sophia y la amortizacion de la tarjeta al 24.9% TAE?",
            "¿Cual es el coste anual estimado de una cobertura umbrella de $1M para nuestro patrimonio inmobiliario?"
        ]
    else:  # Samantha Lewis
        advisor_questions = [
            "A pesar de mi score de 82, las proyecciones muestran agotamiento de liquidez a los 73 anos: ¿que ajustes de desacumulacion debemos hacer?",
            "¿Cual es la hoja de ruta para ejecutar aportaciones Backdoor Roth IRA y maximizar la cuenta HSA?",
            "¿Como escalonamos los pagos universitarios que inician este ano para no frenar la compra de vivienda en 2030?"
        ]

    now_str = datetime.now().strftime("%d/%m/%Y")

    # Construccion del documento en Markdown
    md_lines = [
        f"# Sherpas Wealth - Ficha de Acompanamiento Financiero",
        f"**Cliente / Hogar:** {case_title} ({case_city})  ",
        f"**Fecha del informe:** {now_str} | **Score de Salud:** {score_val}/100 ({score_band})  ",
        f"**Miembros del hogar:** {household_names}  ",
        "\n---",
        "\n## 1. Diagnostico Ejecutivo y Salud Financiera",
        f"- **Score Global:** {score_val}/100 ({score_band}). {score_data.get('message', '')}",
        f"- **Ingresos Mensuales Netos:** ${tot_inc:,.0f}/mes",
        f"- **Gastos de Vida y Vivienda:** ${tot_exp:,.0f}/mes",
        f"- **Servicio Mensual de Deuda:** ${tot_debt_pmt:,.0f}/mes (Deuda total viva: ${tot_debt_bal:,.0f})",
        f"- **Flujo de Caja Libre Estimado:** ${(tot_inc - (tot_exp + tot_debt_pmt)):,.0f}/mes",
        "\n## 2. Metas Vitales Registradas",
    ]
    for g in goals_list:
        md_lines.append(f"- 🎯 {g}")

    md_lines.extend([
        "\n## 3. Estado de Ejecucion del Plan de Accion",
        f"- **Tareas completadas ({len(completed_tasks)} de {len(tasks)}):**"
    ])
    if completed_tasks:
        for ct in completed_tasks:
            md_lines.append(f"  * [x] **{ct.title}** ({ct.category}) - Impacto: {ct.impact.value if ct.impact else 'Completada'}")
    else:
        md_lines.append("  * (Ninguna tarea completada todavia; plan inicial en curso)")

    md_lines.append(f"- **Proximas acciones prioritarias ({len(pending_tasks)}):**")
    for pt in pending_tasks[:4]:
        md_lines.append(f"  * [ ] **{pt.title}** (Semana {pt.week}, {pt.category}) - {pt.description}")

    md_lines.extend([
        "\n## 4. Preguntas Preparadas para la Sesion con el Asesor",
        "Lleva estas dudas clave a tu proxima reunion para maximizar el valor de la consulta:"
    ])
    for q in advisor_questions:
        md_lines.append(f"1. {q}")

    markdown_text = "\n".join(md_lines)

    # Version HTML estilizada e imprimible
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Sherpas Wealth - Informe de Acompanamiento: {case_title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  @page {{ size: A4; margin: 18mm; }}
  body {{
    font-family: 'Inter', -apple-system, sans-serif;
    color: #1e293b;
    line-height: 1.5;
    background: #ffffff;
    padding: 24px;
    max-width: 800px;
    margin: 0 auto;
  }}
  .header {{
    border-bottom: 2px solid #0f172a;
    padding-bottom: 14px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .logo {{ font-size: 22px; font-weight: 700; color: #0f172a; letter-spacing: -0.5px; }}
  .tagline {{ font-size: 12px; color: #64748b; }}
  .score-badge {{
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 16px;
  }}
  h2 {{
    font-size: 15px;
    color: #0f172a;
    border-left: 4px solid #3b82f6;
    padding-left: 8px;
    margin-top: 22px;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .grid-kpi {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
  }}
  .kpi-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
  }}
  .kpi-val {{ font-size: 16px; font-weight: 700; color: #0f172a; }}
  .kpi-lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; }}
  ul, ol {{ margin-top: 6px; padding-left: 20px; font-size: 13px; }}
  li {{ margin-bottom: 5px; }}
  .task-done {{ color: #166534; font-weight: 500; }}
  .task-pending {{ color: #1e293b; }}
  .footer {{
    margin-top: 30px;
    border-top: 1px solid #e2e8f0;
    padding-top: 10px;
    font-size: 11px;
    color: #94a3b8;
    display: flex;
    justify-content: space-between;
  }}
  @media print {{
    body {{ padding: 0; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="logo">Sherpas Wealth Co-Pilot</div>
      <div class="tagline">Ficha de Acompanamiento y Hoja de Ruta para Reunion de Asesoria</div>
    </div>
    <div class="score-badge">Score: {score_val}/100 ({score_band})</div>
  </div>

  <div style="font-size: 13px; margin-bottom: 16px;">
    <strong>Titular / Hogar:</strong> {case_title} ({case_city}) &bull; 
    <strong>Fecha:</strong> {now_str} &bull; 
    <strong>Participantes:</strong> {household_names}
  </div>

  <div class="grid-kpi">
    <div class="kpi-card">
      <div class="kpi-val">${tot_inc:,.0f}</div>
      <div class="kpi-lbl">Ingresos / Mes</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val">${tot_exp:,.0f}</div>
      <div class="kpi-lbl">Gastos / Mes</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val">${tot_debt_bal:,.0f}</div>
      <div class="kpi-lbl">Deuda Viva</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-val">${(tot_inc - (tot_exp + tot_debt_pmt)):,.0f}</div>
      <div class="kpi-lbl">Flujo Libre / Mes</div>
    </div>
  </div>

  <h2>1. Diagnostico y Metas Vitales</h2>
  <ul>
    <li><strong>Dictamen de salud financiera:</strong> {score_data.get('message', 'Plan activo')}</li>
    {''.join(f'<li>🎯 <strong>Meta:</strong> {g}</li>' for g in goals_list)}
  </ul>

  <h2>2. Progreso de Tareas del Plan</h2>
  <ul>
    {''.join(f'<li class="task-done">&#9989; <strong>{ct.title}:</strong> {ct.impact.value if ct.impact else "Completada"}</li>' for ct in completed_tasks) if completed_tasks else '<li>(Sin tareas completadas aun)</li>'}
    {''.join(f'<li class="task-pending">&#9744; <strong>{pt.title}</strong> (Semana {pt.week}): {pt.description}</li>' for pt in pending_tasks[:4])}
  </ul>

  <h2>3. Dudas Estrategicas para la Reunion con el Asesor</h2>
  <ol>
    {''.join(f'<li><strong>{q}</strong></li>' for q in advisor_questions)}
  </ol>

  <div class="footer">
    <span>Sherpas Wealth Management &bull; Confidencial</span>
    <span>Generado interactivamente con Sherpas Co-Pilot</span>
  </div>
</body>
</html>
"""

    return {
        "case_id": case_id,
        "title": case_title,
        "city": case_city,
        "score": score_val,
        "band": score_band,
        "markdown": markdown_text,
        "html": html_content,
        "advisor_questions": advisor_questions
    }

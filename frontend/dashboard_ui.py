"""Gráficos y resúmenes: KPIs del mes, proyección a 12 meses, progreso del plan y los
gráficos que genera el Co-Pilot en el chat."""
import time

import plotly.graph_objects as go
import streamlit as st

from compat import stretch

import kanban_store as ks
import table_store as ts

PALETTE = ["#4f8cff", "#22c55e", "#f59e0b", "#ec4899", "#a855f7",
           "#06b6d4", "#14b8a6", "#eab308", "#6366f1", "#f97316"]
GRID = "rgba(255,255,255,0.08)"


def _layout(fig: go.Figure, height: int, **extra) -> None:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f4f5f7", family="Inter"),
        margin=dict(l=10, r=10, t=30, b=10), height=height,
        xaxis=dict(showgrid=True, gridcolor=GRID, automargin=True, tickfont=dict(color="#f4f5f7")),
        yaxis=dict(showgrid=True, gridcolor=GRID, automargin=True, tickfont=dict(color="#f4f5f7")),
        **extra,
    )


def _money(v) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "—"


# ---------------------------------------------------------------- pestaña "Plan de acción"
def render_plan_progress() -> None:
    cards = ks.load().get("cards", [])
    if not cards:
        return
    done = sum(1 for c in cards if c.get("status") == "done")
    doing = sum(1 for c in cards if c.get("status") == "in_process")
    st.progress(done / len(cards), text=f"{done} de {len(cards)} tareas hechas · {doing} en curso")


# ---------------------------------------------------------------- pestaña "Proyección y datos"
def render_kpis(table: dict) -> None:
    rows = table.get("rows", [])
    if not rows:
        st.info("Todavía no hay datos. Pulsa **🚀 Cargar plan** o añade tu primer mes en la tabla.")
        return
    this_month = time.strftime("%Y-%m")
    row = next((r for r in rows if r.get("date") == this_month), rows[0])

    pills = [("Mes activo", row.get("date", "N/D"))]
    if "Patrimonio" in row:
        pills.append(("Patrimonio", _money(row["Patrimonio"])))
    if "Ingresos" in row and "Gastos_Fijos" in row:
        pills.append(("Flujo libre", _money(row["Ingresos"] - row["Gastos_Fijos"])))
    if "Deuda_Pendiente" in row:
        pills.append(("Deuda viva", _money(row["Deuda_Pendiente"])))

    cols = st.columns(len(pills))
    for col, (label, value) in zip(cols, pills):
        col.markdown(f"<div class='kpi-pill'>{label}<strong>{value}</strong></div>", unsafe_allow_html=True)


def render_projection(df) -> None:
    """Patrimonio, deuda y ahorro mes a mes. Reacciona a cualquier cambio de la tabla."""
    if df is None or df.empty or len(df) < 2:
        return
    fig = go.Figure()
    if "Patrimonio" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["Patrimonio"], name="Patrimonio neto",
                                 mode="lines+markers", line=dict(color="#4f8cff", width=3), marker=dict(size=6)))
    if "Deuda_Pendiente" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["Deuda_Pendiente"], name="Deuda pendiente",
                                 mode="lines+markers", line=dict(color="#ef4444", width=2, dash="dot"),
                                 marker=dict(size=6)))
    if "Ahorro_Libre" in df.columns:
        fig.add_trace(go.Bar(x=df["date"], y=df["Ahorro_Libre"], name="Ahorro mensual",
                             marker_color="rgba(34, 197, 94, 0.45)"))
    if not fig.data:                                  # tabla con otras columnas: dibujar las tres primeras
        for c in list(df.columns[1:4]):
            fig.add_trace(go.Scatter(x=df["date"], y=df[c], name=c, mode="lines+markers"))
    _layout(fig, 320, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(type="category")                 # "2026-11" son meses, no fechas con días
    fig.update_yaxes(tickprefix="$")
    with st.expander("📈 Proyección financiera mes a mes", expanded=True):
        st.caption("Se actualiza al editar la tabla de abajo o cuando el Co-Pilot cambia un dato.")
        st.plotly_chart(fig, theme=None, **stretch(st.plotly_chart))


def render_distribution(table: dict) -> None:
    """Reparto de ingresos del mes activo entre gastos fijos y ahorro, si la tabla lo permite."""
    rows = table.get("rows", [])
    if not rows:
        return
    row = next((r for r in rows if r.get("date") == time.strftime("%Y-%m")), rows[0])
    inc, fixed = row.get("Ingresos"), row.get("Gastos_Fijos")
    if not inc or fixed is None or inc <= 0:
        return
    saving = max(inc - fixed, 0)
    fig = go.Figure(go.Pie(labels=["Gastos fijos", "Ahorro libre"], values=[fixed, saving], hole=0.55,
                           marker=dict(colors=["#f59e0b", "#22c55e"]), textinfo="label+percent"))
    _layout(fig, 260, showlegend=False)
    with st.expander(f"🥧 ¿En qué se va tu dinero? ({row.get('date')})", expanded=False):
        st.plotly_chart(fig, theme=None, **stretch(st.plotly_chart))


# ---------------------------------------------------------------- gráficos del chat
def render_chart(chart: dict) -> None:
    """Gráfico pedido por el Co-Pilot: {type: bar|line|donut|pie, title, labels, values}."""
    if not chart:
        return
    kind = chart.get("type", "bar")
    labels = chart.get("labels") or chart.get("categories") or []
    values = chart.get("values") or []
    if not labels or not values:
        return
    fig = go.Figure()
    if kind == "line":
        fig.add_trace(go.Scatter(x=labels, y=values, mode="lines+markers",
                                 line=dict(color="#4f8cff", width=3), marker=dict(size=8, color="#22c55e")))
    elif kind in ("donut", "pie"):
        fig.add_trace(go.Pie(labels=labels, values=values, hole=0.45 if kind == "donut" else 0,
                             marker=dict(colors=PALETTE), textinfo="label+percent", textposition="inside"))
    else:
        fig.add_trace(go.Bar(x=labels, y=values, marker_color="#4f8cff", textposition="auto",
                             text=[f"${v:,.0f}" if isinstance(v, (int, float)) and v >= 100 else str(v) for v in values]))
    _layout(fig, 320, title=dict(text=chart.get("title", ""), font=dict(color="#f4f5f7", size=15)))
    st.plotly_chart(fig, theme=None, **stretch(st.plotly_chart))

# Graficos y resumenes: KPIs del mes, proyeccion a 12 meses, progreso del plan y graficos del Co-Pilot.
import time

import plotly.graph_objects as go
import streamlit as st

from compat import stretch

import kanban_store as ks
import table_store as ts

PALETTE = [
    "#2563eb", "#059669", "#ea580c", "#7c3aed", "#0891b2",
    "#e11d48", "#d97706", "#4f46e5", "#10b981", "#c026d3",
    "#0284c7", "#ca8a04", "#9333ea", "#0d9488", "#f43f5e",
    "#6366f1", "#16a34a", "#b45309"
]
GRID = "rgba(255, 255, 255, 0.06)"


def _layout(fig: go.Figure, height: int, **extra) -> None:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=35, b=10),
        height=height,
        legend=dict(
            font=dict(color="#ffffff", size=12, family="Inter, sans-serif"),
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor="#0e1626",
            font=dict(color="#ffffff", family="Inter, sans-serif"),
            bordercolor="rgba(255,255,255,0.15)"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            automargin=True,
            tickfont=dict(color="#ffffff", size=11, family="Inter, sans-serif"),
            titlefont=dict(color="#ffffff", size=12, family="Inter, sans-serif")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            automargin=True,
            tickfont=dict(color="#ffffff", size=11, family="Inter, sans-serif"),
            titlefont=dict(color="#ffffff", size=12, family="Inter, sans-serif")
        ),
        **extra,
    )


def _money(v) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "—"


# ---------------------------------------------------------------- pestana "Plan de accion"
def render_plan_progress() -> None:
    cards = ks.load().get("cards", [])
    if not cards:
        return
    done = sum(1 for c in cards if c.get("status") == "done")
    doing = sum(1 for c in cards if c.get("status") == "in_process")
    total = len(cards)
    ratio = done / total if total > 0 else 0
    st.progress(ratio, text=f"{done} de {total} tareas completadas · {doing} en curso")


# ---------------------------------------------------------------- pestana "Proyeccion y datos"
def render_kpis(table: dict) -> None:
    rows = table.get("rows", [])
    if not rows:
        st.info("Todavia no hay datos. Pulsa **🚀 Cargar plan** o anade tu primer mes en la tabla.")
        return
    this_month = time.strftime("%Y-%m")
    row = next((r for r in rows if r.get("date") == this_month), rows[0])

    pills = [("Mes activo", row.get("date", "N/D"), "#f8fafc")]
    if "Patrimonio" in row:
        pills.append(("Patrimonio neto", _money(row["Patrimonio"]), "#6586fc"))
    if "Ingresos" in row and "Gastos_Fijos" in row:
        pills.append(("Flujo libre mes", _money(row["Ingresos"] - row["Gastos_Fijos"]), "#34d399"))
    if "Deuda_Pendiente" in row:
        pills.append(("Deuda total viva", _money(row["Deuda_Pendiente"]), "#f87171"))

    cols = st.columns(len(pills))
    for col, (label, value, val_color) in zip(cols, pills):
        col.markdown(f"""
        <div class='kpi-pill'>
            <div style='font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em;'>{label}</div>
            <strong style='font-family:Poppins, sans-serif; font-size:1.25rem; color:{val_color}; font-weight:700;'>{value}</strong>
        </div>
        """, unsafe_allow_html=True)


def render_projection(df) -> None:
    """Patrimonio, deuda y ahorro mes a mes. Reacciona a cualquier cambio de la tabla."""
    if df is None or df.empty or len(df) < 2:
        return
    fig = go.Figure()
    if "Patrimonio" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["Patrimonio"], name="Patrimonio neto",
            mode="lines+markers", line=dict(color="#6586fc", width=3),
            marker=dict(size=6, color="#4565d6")
        ))
    if "Deuda_Pendiente" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["Deuda_Pendiente"], name="Deuda viva",
            mode="lines+markers", line=dict(color="#f87171", width=2, dash="dot"),
            marker=dict(size=6, color="#ef4444")
        ))
    if "Ahorro_Libre" in df.columns:
        fig.add_trace(go.Bar(
            x=df["date"], y=df["Ahorro_Libre"], name="Ahorro mensual",
            marker_color="rgba(16, 185, 129, 0.65)"
        ))
    if not fig.data:
        for c in list(df.columns[1:4]):
            fig.add_trace(go.Scatter(x=df["date"], y=df[c], name=c, mode="lines+markers"))

    _layout(fig, 320)
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickprefix="$")
    with st.expander("📈 Proyeccion financiera mes a mes", expanded=True):
        st.caption("Se actualiza al editar la tabla o cuando el Co-Pilot aplica ajustes.")
        st.plotly_chart(fig, theme=None, **stretch(st.plotly_chart))


def render_distribution(table: dict) -> None:
    """Reparto de ingresos del mes activo entre gastos fijos y ahorro."""
    rows = table.get("rows", [])
    if not rows:
        return
    row = next((r for r in rows if r.get("date") == time.strftime("%Y-%m")), rows[0])
    inc, fixed = row.get("Ingresos"), row.get("Gastos_Fijos")
    if not inc or fixed is None or inc <= 0:
        return
    saving = max(inc - fixed, 0)
    fig = go.Figure(go.Pie(
        labels=["Gastos fijos", "Ahorro libre"],
        values=[fixed, saving],
        hole=0.55,
        marker=dict(colors=["#f87171", "#34d399"]),
        textinfo="label+percent",
        textfont=dict(color="#ffffff", family="Inter, sans-serif")
    ))
    _layout(fig, 260, showlegend=False)
    with st.expander(f"🥧 Distribucion mensual ({row.get('date')})", expanded=False):
        st.plotly_chart(fig, theme=None, **stretch(st.plotly_chart))


# ---------------------------------------------------------------- graficos del chat
def render_chart(chart: dict) -> None:
    """Grafico solicitado por el Co-Pilot: {type: bar|line|donut|pie, title, labels, values}."""
    if not chart:
        return
    kind = chart.get("type", "bar")
    labels = chart.get("labels") or chart.get("categories") or []
    values = chart.get("values") or []
    if not labels or not values:
        return
    fig = go.Figure()
    if kind == "line":
        fig.add_trace(go.Scatter(
            x=labels, y=values, mode="lines+markers",
            line=dict(color="#6586fc", width=3),
            marker=dict(size=8, color="#34d399")
        ))
    elif kind in ("donut", "pie"):
        fig.add_trace(go.Pie(
            labels=labels, values=values, hole=0.45 if kind == "donut" else 0,
            marker=dict(colors=PALETTE, line=dict(color="#0f172a", width=1.5)),
            textinfo="label+percent", textposition="inside",
            hoverinfo="label+value+percent",
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>",
            textfont=dict(color="#ffffff", family="Inter, sans-serif")
        ))
    else:
        fig.add_trace(go.Bar(
            x=labels, y=values, marker_color="#4565d6", textposition="auto",
            textfont=dict(color="#ffffff"),
            text=[f"${v:,.0f}" if isinstance(v, (int, float)) and v >= 100 else str(v) for v in values]
        ))
    _layout(
        fig, 320,
        title=dict(text=chart.get("title", ""), font=dict(color="#ffffff", size=15, family="Poppins, sans-serif"))
    )
    st.plotly_chart(fig, theme=None, **stretch(st.plotly_chart))

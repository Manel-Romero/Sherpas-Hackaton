"""Ficha de datos clave de cada usuario: data/cases/<id>/profile.json.

Se crea UNA vez a partir del caso de Sherpas (informe + análisis de inversión + persona), con código y sin
IA, para que las cifras sean exactas. A partir de ahí es la fuente de los datos del hogar que usa el chat:
el Co-Pilot no vuelve a leer el caso entero y, cuando el usuario cuenta un cambio (paga una deuda, le suben
el sueldo, entra o sale dinero de una cuenta), lo apunta aquí con la herramienta `update_profile`.

Ficha y tabla coinciden por construcción:
  * la ficha guarda el DETALLE (cada deuda, cada ingreso, cada gasto, cada cuenta…);
  * la tabla mensual guarda los TOTALES de cada mes. La fila del mes en curso es «hoy» y se escribe desde
    la ficha cada vez que esta cambia (Ingresos, Gastos_Fijos, Deuda_Pendiente, Patrimonio). Los meses
    siguientes son la proyección: Patrimonio la calcula table_store a partir de hoy y la deuda se proyecta
    amortizando cada préstamo con su cuota y su interés.
Si alguien edita a mano los totales de hoy en la tabla, el chat ve las dos cifras y la diferencia.

El score es el del informe de Sherpas: no se recalcula al cambiar datos (se muestra así).
"""
import json
import os
import threading
from datetime import datetime
from pathlib import Path

import project_paths
import table_store as ts

_lock = threading.Lock()
CORE_COLUMNS = ("Ingresos", "Gastos_Fijos", "Deuda_Pendiente", "Patrimonio")
KINDS = ("debt", "income", "expense", "account", "asset", "insurance", "taxes", "goal", "note")
_HISTORY_MAX = 30


# ---------------------------------------------------------------- ficheros
def _path(case_id: str) -> Path:
    return project_paths.DATA_CASES_DIR / Path(case_id).name / "profile.json"


def load(case_id: str) -> dict | None:
    f = _path(case_id)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def save(case_id: str, profile: dict) -> dict:
    f = _path(case_id)
    f.parent.mkdir(parents=True, exist_ok=True)
    profile["updated_at"] = datetime.now().isoformat(timespec="seconds")
    with _lock:
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, f)
    return profile


# ---------------------------------------------------------------- creación desde el caso
def _num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _section(persona: str, start: str, ends: list[str]) -> str:
    i = persona.find(start)
    if i == -1:
        return ""
    stops = [persona.find(e, i + len(start)) for e in ends]
    stops = [s for s in stops if s != -1]
    return persona[i + len(start): min(stops) if stops else len(persona)].strip()


def build_from_case(financial_health: dict, investment_analysis: dict | None = None, persona: str = "") -> dict:
    """Extrae del caso los datos que usa el Co-Pilot. Solo código: cifras exactas del informe."""
    fh = financial_health or {}
    prof = fh.get("profile", {}) or {}
    sc = fh.get("score", {}) or {}

    p = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "Informe de Sherpas",
        "score": {
            "value": sc.get("published_score"),
            "band": sc.get("band", ""),
            "message": sc.get("message", ""),
            "pillars": [{"name": x.get("pillar", "Pilar"), "points": x.get("points_shown_in_app", ""),
                         "pct": x.get("score", 0)} for x in sc.get("pillars", [])],
        },
        "top_moves": [{"title": m.get("title", ""), "action": m.get("action", ""), "effort": m.get("effort", "medio"),
                       "before": m.get("score_before", ""), "after": m.get("score_after", "")}
                      for m in sc.get("top_moves", [])],
        "goals": [g.get("value") or f"{g.get('goalType', 'Meta')}: ${_num(g.get('amount')):,.0f}"
                  for g in (fh.get("goals", {}) or {}).get("goalsSummary", [])],
        "accounts": [], "assets": [], "insurance": [], "incomes": [], "expenses": [], "debts": [],
        "taxes_yearly": 0.0, "planned_savings_yearly": 0.0,
        "allocation": {}, "portfolio": [],
        "transition_alerts": "", "objective_concerns": "", "tensions": "",
        "notes": [], "history": [],
    }

    for a in prof.get("accounts", []):
        owner = a.get("owner", "")
        p["accounts"].append({
            "name": a.get("name", "Cuenta"), "type": a.get("account_type", ""), "tax": a.get("tax_treatment", ""),
            "owner": ", ".join(owner) if isinstance(owner, list) else (owner or ""),
            "balance": _num(a.get("balance")), "yearly_contribution": _num(a.get("yearly_contribution_total")),
        })
    for a in prof.get("other_assets", []):
        p["assets"].append({"name": a.get("name", "Bien"), "type": a.get("type", ""), "value": _num(a.get("value"))})
    for i in prof.get("insurance", []):
        cov = i.get("coverage", None)
        p["insurance"].append({"name": i.get("name", "Seguro"), "type": i.get("type", ""),
                               "coverage": cov if isinstance(cov, (int, float)) else (str(cov) if cov else "No registrada")})
    for i in prof.get("incomes", []):
        p["incomes"].append({"name": i.get("name", "Ingreso"), "yearly": _num(i.get("yearly")), "starts": i.get("starts")})
    for e in prof.get("expenses", []):
        monthly = _num(e.get("monthly")) or _num(e.get("yearly")) / 12
        p["expenses"].append({"name": e.get("name", "Gasto"), "monthly": round(monthly, 2)})
    for d in prof.get("liabilities", []):
        p["debts"].append({"name": d.get("name", "Deuda"), "balance": _num(d.get("balance")),
                           "rate_pct": round(_num(d.get("interest_rate")) * 100, 3),
                           "monthly_payment": _num(d.get("monthly_payment"))})

    # Impuestos, ahorro planificado y gastos que el informe cuenta pero no detalla en la lista de gastos
    cf = (fh.get("key_metrics", {}) or {}).get("cashflowStatement", {}) or {}
    outflows = {x.get("name"): _num(x.get("total")) for x in (cf.get("outflows", {}) or {}).get("items", [])}
    p["taxes_yearly"] = round(outflows.get("Taxes", 0.0), 2)
    p["planned_savings_yearly"] = round(outflows.get("Savings", 0.0), 2)
    spent_report = sum(v for k, v in outflows.items() if k not in ("Taxes", "Savings")) / 12
    spent_detail = sum(e["monthly"] for e in p["expenses"]) + sum(d["monthly_payment"] for d in p["debts"])
    if spent_report - spent_detail > 20:                       # p. ej. primas de seguros que no salen como gasto
        p["expenses"].append({"name": "Otros gastos del informe (sin desglosar)",
                              "monthly": round(spent_report - spent_detail, 2)})

    # Inversiones
    ia = investment_analysis or {}
    alloc = ((ia.get("analysis", {}) or {}).get("summary", {}) or {}).get("assetAllocation", {}) or {}
    cur, tgt = alloc.get("currentEFC", {}) or {}, alloc.get("targetEFC", {}) or {}
    if cur or tgt:
        p["allocation"] = {k: {"equity": _num(v.get("equity")), "fixed_income": _num(v.get("fixedIncome")),
                               "cash": _num(v.get("cash"))} for k, v in (("current", cur), ("target", tgt))}
    conc = ((ia.get("key_metrics", {}) or {}).get("concentrationAndDiversification", {}) or {})
    totals = conc.get("totals", {}) or {}
    if totals:
        p["portfolio"].append(f"Cartera invertible: ${_num(totals.get('investablePortfolioValue')):,.0f} "
                              f"distribuida en {totals.get('holdings', 0)} posiciones (Exposicion en renta variable: "
                              f"${_num(totals.get('equityExposure')):,.0f}).")
    geo = []
    for row in (conc.get("geographyByRegion", []) or [])[1:]:
        if isinstance(row, list) and len(row) >= 2:
            try:
                geo.append(f"{row[0]}: {float(row[1]) * 100:.1f}%")
            except (TypeError, ValueError):
                pass
    if geo:
        p["portfolio"].append(f"Sesgo geografico: {', '.join(geo[:4])}")

    # Persona: alertas, preocupaciones y tensiones (texto tal cual)
    persona = persona or ""
    p["transition_alerts"] = _section(persona, "## Transition alerts", ["## Subjective concerns", "## Objective concerns"])
    p["objective_concerns"] = _section(persona, "## Objective concerns", ["## Tensions", "```classification"])
    p["tensions"] = _section(persona, "## Tensions", ["```classification"])
    return p


# ---------------------------------------------------------------- totales («hoy»)
def _current_incomes(p: dict) -> list[dict]:
    year = datetime.now().year
    return [i for i in p.get("incomes", []) if not i.get("starts") or int(i["starts"]) <= year]


def totals(p: dict) -> dict:
    """Totales mensuales de hoy calculados a partir del detalle de la ficha."""
    gross = sum(_num(i.get("yearly")) for i in _current_incomes(p)) / 12
    taxes = _num(p.get("taxes_yearly")) / 12
    living = sum(_num(e.get("monthly")) for e in p.get("expenses", []))
    debt_pay = sum(_num(d.get("monthly_payment")) for d in p.get("debts", []))
    debt = sum(_num(d.get("balance")) for d in p.get("debts", []))
    owned = sum(_num(a.get("balance")) for a in p.get("accounts", [])) + sum(_num(a.get("value")) for a in p.get("assets", []))
    income = gross - taxes
    spend = living + debt_pay
    return {"gross_income": round(gross, 2), "taxes": round(taxes, 2), "income": round(income, 2),
            "living": round(living, 2), "debt_payments": round(debt_pay, 2), "spend": round(spend, 2),
            "free": round(income - spend, 2), "planned_savings": round(_num(p.get("planned_savings_yearly")) / 12, 2),
            "debt": round(debt, 2), "owned": round(owned, 2), "net_worth": round(owned - debt, 2)}


def _debt_projection(p: dict, months: int) -> list[float]:
    """Deuda total al final de cada uno de los próximos `months` meses, amortizando cada préstamo."""
    debts = [(_num(d.get("balance")), _num(d.get("rate_pct")) / 100 / 12, _num(d.get("monthly_payment")))
             for d in p.get("debts", [])]
    out = []
    for _ in range(months):
        debts = [(max(0.0, b * (1 + r) - pay) if pay > 0 else b, r, pay) for b, r, pay in debts]
        out.append(round(sum(b for b, _, _ in debts), 2))
    return out


def _today_index(rows: list[dict]) -> int | None:
    cur = datetime.now().strftime("%Y-%m")
    for i, r in enumerate(rows):
        if r.get("date") == cur:
            return i
    return None


def sync_table(case_id: str, p: dict, whole_table: bool = False) -> str:
    """Escribe en la tabla los totales de la ficha. Por defecto el mes en curso y los siguientes; con
    `whole_table` también los meses pasados (al crear el plan, cuando todo eran estimaciones)."""
    data = ts.load(case_id)
    rows = data.get("rows", [])
    i = _today_index(rows)
    if not rows or i is None:
        return "La tabla no tiene fila para el mes en curso: solo se ha actualizado la ficha."
    t = totals(p)
    for c in CORE_COLUMNS:
        if c not in data["columns"]:
            data["columns"].append(c)
    old_inc, old_sp = ts.to_number(rows[i].get("Ingresos")), ts.to_number(rows[i].get("Gastos_Fijos"))
    start = 0 if whole_table else i
    proj = _debt_projection(p, len(rows) - i - 1)
    for k in range(start, len(rows)):
        r = rows[k]
        if whole_table or k == i:
            r["Ingresos"], r["Gastos_Fijos"] = t["income"], t["spend"]
        else:          # meses futuros: se mueve lo que ya hubiera (crecimientos, planes…) en la misma diferencia
            r["Ingresos"] = round(ts.to_number(r.get("Ingresos")) + t["income"] - old_inc, 2)
            r["Gastos_Fijos"] = round(ts.to_number(r.get("Gastos_Fijos")) + t["spend"] - old_sp, 2)
        if k <= i:
            r["Deuda_Pendiente"] = t["debt"]
            r["Patrimonio"] = t["net_worth"]
        else:
            r["Deuda_Pendiente"] = proj[k - i - 1]
    ts.save(data, case_id)        # recalcula Ahorro_Libre y el Patrimonio de los meses siguientes desde hoy
    return ""


def table_today(case_id: str) -> tuple[str | None, dict | None]:
    data = ts.load(case_id)
    i = _today_index(data.get("rows", []))
    return (None, None) if i is None else (data["rows"][i]["date"], data["rows"][i])


def create(case_id: str, financial_health: dict, investment_analysis: dict | None, persona: str,
           sync: bool = True) -> dict:
    """Crea la ficha desde el caso, la guarda y (si `sync`) pone la tabla en línea con ella."""
    p = build_from_case(financial_health, investment_analysis, persona)
    save(case_id, p)
    if sync:
        sync_table(case_id, p, whole_table=True)
    return p


# ---------------------------------------------------------------- cambios (herramienta del Co-Pilot)
_LISTS = {"debt": "debts", "income": "incomes", "expense": "expenses", "account": "accounts",
          "asset": "assets", "insurance": "insurance"}


def _find(items: list[dict], name: str) -> int | None:
    n = name.strip().lower()
    for i, it in enumerate(items):
        if it.get("name", "").strip().lower() == n:
            return i
    hits = [i for i, it in enumerate(items) if n and (n in it.get("name", "").lower() or it.get("name", "").lower() in n)]
    return hits[0] if len(hits) == 1 else None


def _money(v: float) -> str:
    return f"${v:,.0f}"


def update(case_id: str, kind: str, name: str = "", action: str = "set", *, balance=None, monthly_payment=None,
           interest_rate_pct=None, yearly=None, monthly=None, value=None, coverage=None, text: str = "") -> str:
    """Aplica un cambio a la ficha, sincroniza la tabla y devuelve un resumen legible."""
    p = load(case_id)
    if p is None:
        return "Este usuario todavía no tiene ficha: genera el plan primero."
    if kind not in KINDS:
        return f"Tipo '{kind}' no válido. Usa uno de: {', '.join(KINDS)}."
    before = totals(p)
    what = ""

    if kind == "taxes":
        if yearly is None:
            return "Para 'taxes' indica 'yearly' (impuestos anuales)."
        p["taxes_yearly"] = float(yearly)
        what = f"impuestos anuales = {_money(float(yearly))}"
    elif kind in ("goal", "note"):
        key = "goals" if kind == "goal" else "notes"
        if action == "remove":
            idx = _find([{"name": g} for g in p.get(key, [])], name or text)
            if idx is None:
                return f"No encuentro '{name or text}' en {key}."
            removed = p[key].pop(idx)
            what = f"quitado de {key}: {removed}"
        else:
            if not text.strip():
                return "Indica el texto en 'text'."
            p.setdefault(key, []).append(text.strip())
            what = f"añadido a {key}: {text.strip()}"
    else:
        items = p.setdefault(_LISTS[kind], [])
        if not name.strip():
            return "Indica el nombre ('name') de la partida."
        idx = _find(items, name)
        if action == "remove":
            if idx is None:
                return f"No encuentro '{name}'. Partidas: {', '.join(i['name'] for i in items) or 'ninguna'}."
            items.pop(idx)
            what = f"eliminado {kind} '{name}'"
        else:
            new = idx is None
            it = {"name": name.strip()} if new else items[idx]
            if kind == "debt":
                if balance is not None:
                    it["balance"] = max(0.0, float(balance))
                if interest_rate_pct is not None:
                    it["rate_pct"] = float(interest_rate_pct)
                if monthly_payment is not None:
                    it["monthly_payment"] = max(0.0, float(monthly_payment))
                elif balance is not None and float(balance) <= 0:
                    it["monthly_payment"] = 0.0           # deuda pagada: ya no hay cuota
                it.setdefault("balance", 0.0); it.setdefault("rate_pct", 0.0); it.setdefault("monthly_payment", 0.0)
            elif kind == "income":
                if yearly is None and monthly is not None:
                    yearly = float(monthly) * 12
                if yearly is None and new:
                    return "Para un ingreso nuevo indica 'yearly' (bruto anual) o 'monthly'."
                if yearly is not None:
                    it["yearly"] = float(yearly)
                it.setdefault("starts", None)
            elif kind == "expense":
                if monthly is None and yearly is not None:
                    monthly = float(yearly) / 12
                if monthly is None:
                    return "Para un gasto indica 'monthly' (o 'yearly')."
                it["monthly"] = round(float(monthly), 2)
            elif kind == "account":
                if balance is None:
                    return "Para una cuenta indica 'balance' (saldo nuevo)."
                it["balance"] = float(balance)
                it.setdefault("type", ""); it.setdefault("tax", ""); it.setdefault("owner", ""); it.setdefault("yearly_contribution", 0.0)
            elif kind == "asset":
                v = value if value is not None else balance
                if v is None:
                    return "Para un bien indica 'value'."
                it["value"] = float(v)
                it.setdefault("type", "")
            elif kind == "insurance":
                if coverage is None:
                    return "Para un seguro indica 'coverage'."
                it["coverage"] = float(coverage)
                it.setdefault("type", "")
            if new:
                items.append(it)
            what = ("nuevo " if new else "") + f"{kind} '{it['name']}': " + ", ".join(
                f"{k}={v}" for k, v in it.items() if k != "name")

    after = totals(p)
    p.setdefault("history", []).append({"date": datetime.now().strftime("%Y-%m-%d"), "change": what})
    p["history"] = p["history"][-_HISTORY_MAX:]
    save(case_id, p)
    note = sync_table(case_id, p) if kind not in ("goal", "note", "insurance") else ""

    lines = [f"Ficha actualizada: {what}."]
    for key, label in (("income", "Ingresos netos/mes"), ("spend", "Gastos/mes"), ("debt", "Deuda total"),
                       ("net_worth", "Patrimonio neto")):
        if round(before[key]) != round(after[key]):
            lines.append(f"{label}: {_money(before[key])} -> {_money(after[key])}")
    if kind not in ("goal", "note", "insurance"):
        lines.append(note or "Tabla actualizada: el mes en curso coincide con la ficha y la proyección se ha recalculado.")
    return "\n".join(lines)


# ---------------------------------------------------------------- texto para el prompt del Co-Pilot
def prompt_context(case_id: str, p: dict) -> dict:
    """Variables de texto con las que se construye el prompt del chat (mismo formato que antes)."""
    sc = p.get("score", {}) or {}
    t = totals(p)
    year = datetime.now().year

    pillars = "\n".join(f"  * {x['name']}: {x['points']} (Rendimiento: {x['pct']}%)" for x in sc.get("pillars", [])) \
        or "Pillars no disponibles."
    moves = "\n".join(f"  * {m['title']} [Esfuerzo {m['effort']}]: {m['action']} (Impacto: {m['before']} -> {m['after']} pts)"
                      for m in p.get("top_moves", [])) or "Top moves no disponibles."
    goals = list(p.get("goals", []))
    goals_text = "\n".join(f"  * {g}" for g in goals) or "Metas no especificadas."
    accounts = "\n".join(
        f"  * {a['name']} ({a.get('type', '')}, {a.get('tax', '')})" + (f" (Titular: {a['owner']})" if a.get("owner") else "")
        + f": Saldo {_money(_num(a.get('balance')))}"
        + (f" | Aporte anual: {_money(_num(a['yearly_contribution']))}" if _num(a.get("yearly_contribution")) > 0 else "")
        for a in p.get("accounts", [])) or "Sin cuentas registradas."
    assets = "\n".join(f"  * {a['name']} ({a.get('type', '')}): Valor {_money(_num(a.get('value')))}" for a in p.get("assets", []))
    insurance = "\n".join(
        f"  * {i['name']} ({i.get('type', '')}): Cobertura "
        + (_money(i["coverage"]) if isinstance(i.get("coverage"), (int, float)) else str(i.get("coverage")))
        for i in p.get("insurance", [])) or "Sin polizas registradas."

    b = [f"Score de Salud Financiera (del informe de Sherpas, no se recalcula al cambiar datos): "
         f"{sc.get('value', 'N/A')}/100 ({sc.get('band', '')})",
         f"Ingresos brutos actuales ({year}): {_money(t['gross_income'])}/mes"]
    b += [f"  * {i['name']}: {_money(_num(i['yearly']) / 12)}/mes ({_money(_num(i['yearly']))}/ano)" for i in _current_incomes(p)]
    b.append(f"Impuestos: {_money(t['taxes'])}/mes")
    b.append(f"INGRESOS NETOS: {_money(t['income'])}/mes")
    fut = [i for i in p.get("incomes", []) if i not in _current_incomes(p)]
    if fut:
        b.append("\nIngresos futuros proyectados (jubilacion/seguridad social):")
        b += [f"  * {i['name']} (a partir de {i['starts']}): {_money(_num(i['yearly']))}/ano ({_money(_num(i['yearly']) / 12)}/mes)"
              for i in fut]
    b.append(f"\nGastos mensuales de vida y vivienda: {_money(t['living'])}/mes")
    b += [f"  * {e['name']}: {_money(_num(e['monthly']))}/mes" for e in p.get("expenses", [])]
    b.append(f"\nCuotas mensuales de deuda: {_money(t['debt_payments'])}/mes")
    b += [f"  * {d['name']}: cuota {_money(_num(d['monthly_payment']))}/mes (saldo {_money(_num(d['balance']))}, "
          f"TAE {_num(d['rate_pct']):.1f}%)" for d in p.get("debts", [])]
    b.append(f"\nTOTAL SALIENTE REAL MENSUAL: {_money(t['spend'])}/mes")
    b.append(f"AHORRO LIBRE MENSUAL (ingresos netos - gastos y cuotas): {_money(t['free'])}/mes")
    if t["planned_savings"]:
        b.append(f"  * De ahi salen las aportaciones de ahorro planificadas (401k, cuentas...): {_money(t['planned_savings'])}/mes; "
                 f"lo que queda despues: {_money(t['free'] - t['planned_savings'])}/mes")

    alloc = p.get("allocation") or {}
    if alloc:
        c, g = alloc.get("current", {}), alloc.get("target", {})
        alloc_text = (f"- Distribucion Actual: Renta Variable (Acciones) {c.get('equity', 0) * 100:.1f}%, "
                      f"Renta Fija (Bonos) {c.get('fixed_income', 0) * 100:.1f}%, Efectivo {c.get('cash', 0) * 100:.1f}%\n"
                      f"- Distribucion Objetivo de Sherpas: Renta Variable (Acciones) {g.get('equity', 0) * 100:.1f}%, "
                      f"Renta Fija (Bonos) {g.get('fixed_income', 0) * 100:.1f}%, Efectivo {g.get('cash', 0) * 100:.1f}%")
    else:
        alloc_text = "Sin datos de asignacion de activos."

    # «Hoy» según la tabla, comparado con la ficha
    date, row = table_today(case_id)
    if row:
        tb = {c: ts.to_number(row.get(c)) for c in CORE_COLUMNS}
        today = (f"Mes en curso ({date}) segun la tabla: Ingresos netos {_money(tb['Ingresos'])}/mes | "
                 f"Gastos y cuotas {_money(tb['Gastos_Fijos'])}/mes | Ahorro libre {_money(tb['Ingresos'] - tb['Gastos_Fijos'])}/mes | "
                 f"Deuda pendiente {_money(tb['Deuda_Pendiente'])} | Patrimonio neto {_money(tb['Patrimonio'])}")
        diffs = [f"{c} (tabla {_money(tb[c])}, desglose de la ficha {_money(v)})"
                 for c, v in (("Ingresos", t["income"]), ("Gastos_Fijos", t["spend"]),
                              ("Deuda_Pendiente", t["debt"]), ("Patrimonio", t["net_worth"])) if abs(tb[c] - v) > 1]
        if diffs:
            today += ("\nAVISO: la tabla y la ficha no coinciden en " + "; ".join(diffs) + ". La tabla manda (puede que el "
                      "usuario la haya editado a mano); si el usuario confirma el dato, actualiza la ficha con `update_profile`.")
    else:
        today = (f"Hoy (segun la ficha): Ingresos netos {_money(t['income'])}/mes | Gastos y cuotas {_money(t['spend'])}/mes | "
                 f"Ahorro libre {_money(t['free'])}/mes | Deuda total {_money(t['debt'])} | Patrimonio neto {_money(t['net_worth'])}")

    hist = p.get("history", [])[-8:]
    changes = "\n".join(f"  * {h['date']}: {h['change']}" for h in hist)
    notes = "\n".join(f"  * {n}" for n in p.get("notes", []))

    cats = [e["name"] for e in p.get("expenses", []) if _num(e.get("monthly")) > 0] + \
           [f"Deuda: {d['name']}" for d in p.get("debts", []) if _num(d.get("monthly_payment")) > 0]
    vals = [round(_num(e["monthly"])) for e in p.get("expenses", []) if _num(e.get("monthly")) > 0] + \
           [round(_num(d["monthly_payment"])) for d in p.get("debts", []) if _num(d.get("monthly_payment")) > 0]

    return {
        "score_published": sc.get("value", "N/A"), "score_band": sc.get("band", ""), "score_msg": sc.get("message", ""),
        "pillars_text": pillars, "top_moves_text": moves, "goals_text": goals_text,
        "accounts_text": accounts + (f"\n\nOtros bienes:\n{assets}" if assets else ""), "insurance_text": insurance,
        "budget_breakdown_text": "\n".join(b), "asset_alloc_str": alloc_text,
        "portfolio_conc_text": "\n".join(f"  * {x}" for x in p.get("portfolio", [])),
        "transition_alerts_str": p.get("transition_alerts", ""), "objective_concerns_str": p.get("objective_concerns", ""),
        "tensions_str": p.get("tensions", ""), "today_text": today,
        "changes_text": changes, "notes_text": notes,
        "chart_expense_categories": cats, "chart_expense_values": vals,
        "total_income_mo": t["income"], "total_living_expenses": t["living"], "total_debt_payments": t["debt_payments"],
        "total_outgoing": t["spend"], "free_cf": t["free"],
        "cur_efc": {"equity": (alloc.get("current") or {}).get("equity", 0),
                    "fixedIncome": (alloc.get("current") or {}).get("fixed_income", 0),
                    "cash": (alloc.get("current") or {}).get("cash", 0)},
    }

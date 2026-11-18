"""Tutorial y sugerencias personalizados con la información de cada usuario.

Fuentes (las mismas que usa el Co-Pilot, en cases/<caso>/):
    persona.md            D0-D6: qué tipo de hogar es. Aquí se usan D5 (cómo decide) y D6 (qué le mueve).
    financial-health.json score, pilares, "top moves", flujo de caja, patrimonio y la narrativa (summary_main).

Prioridad de contenido:
  1. Lo que generó "Cargar plan" (data/cases/<usuario>/summary.json): resumen ejecutivo, titular,
     primera acción y tareas. Lo escribe el Co-Pilot a partir de persona.md y del informe; aquí no se reescribe.
  2. Si el plan aún no se ha cargado: un resumen mínimo con el score, la persona (D5/D6) y las cifras del
     informe, sin llamar a ningún modelo (gratis).
Un usuario creado por copia (la pareja de Timothy, por ejemplo) hereda el caso base y el resumen,
pero se le habla por su propio nombre.
"""
import json
import re
from functools import lru_cache

import workspaces

CASES_DIR = workspaces.CASES_DIR

BAND_ES = {"critical": "crítico", "vulnerable": "vulnerable", "stable": "estable", "strong": "sólido"}
PILLAR_ES = {
    "Savings and cash flow": "ahorro mensual",
    "Debt": "deuda",
    "Investments": "inversiones",
    "Liquidity and emergency fund": "dinero de reserva para imprevistos",
    "Insurance and protection": "seguros y protección",
}
MOVE_ES = {
    "Add umbrella cover": "contratar un seguro paraguas (te protege si te reclaman una indemnización muy alta)",
    "Raise mortality coverage": "subir el seguro de vida",
    "Add life cover": "contratar más seguro de vida",
    "Raise annual savings": "aumentar el ahorro anual",
    "Lower the withdrawal rate": "planear retirar menos dinero al año cuando te jubiles",
    "Raise growth allocation toward glide": "ajustar el riesgo de tus inversiones a tu edad",
    "Reduce growth allocation toward glide": "ajustar el riesgo de tus inversiones a tu edad",
    "Pay down revolving card": "pagar parte de la tarjeta de crédito",
    "Close a coverage gap": "cubrir algo importante que tus seguros hoy no cubren",
    "Reduce single-name concentration": "no tener tanto dinero metido en una sola inversión",
}

# D6: lo que mueve al hogar -> cómo se le habla.  D5: cómo decide -> cómo se le guía.
ANCHOR_TEXT = {
    "FREEDOM": "Tu plan va de **libertad**: llegar a la fecha en la que tú decides, no la nómina.",
    "PROTECTION": "Tu plan va de **protección**: que, pase lo que pase, tu familia esté cubierta.",
    "DUTY": "Tu plan va de **responsabilidad**: cumplir con quienes dependen de ti.",
}
STYLE_TEXT = {
    "COLLABORATOR": "Te gusta decidir con alguien al lado: el Co-Pilot te propone opciones y tú eliges.",
    "DUAL": "Sois dos tomando decisiones: repartid las tareas y revisad juntos los cambios grandes.",
    "VALIDATOR": "Te gusta comprobar antes de actuar: pídele siempre al Co-Pilot el «por qué» de cada cifra.",
}


# ---------------------------------------------------------------- lectura de la persona
def parse_persona(text: str) -> dict:
    """Extrae de persona.md la etiqueta de cada dimensión: {'D0': 'EMERGING', 'D5': 'DUAL', ...}."""
    out = {}
    for m in re.finditer(r"^## (D\d)\b[^\n]*\n+(.*?)(?=^## |\Z)", text, re.M | re.S):
        dim, body = m.group(1), m.group(2).strip()
        head = re.match(r"([A-Z][A-Z ]*[A-Z])", body)
        if head:
            out[dim] = head.group(1).strip()
    for key, values in (("D5", STYLE_TEXT), ("D6", ANCHOR_TEXT)):     # solo valores conocidos
        if out.get(key) not in values:
            out.pop(key, None)
    m = re.search(r"D4c inferred:\*\*\s*([A-Z]+)", text)
    if m:
        out["D4c"] = m.group(1)
    return out


@lru_cache(maxsize=16)
def _load_case(case_id: str) -> tuple[dict, dict]:
    d = CASES_DIR / case_id
    try:
        fh = json.loads((d / "financial-health.json").read_text(encoding="utf-8"))
    except Exception:
        fh = {}
    try:
        persona = parse_persona((d / "persona.md").read_text(encoding="utf-8"))
    except Exception:
        persona = {}
    return fh, persona


def _money(v) -> str:
    try:
        return f"{abs(float(v)):,.0f} $".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _ratio(points: str) -> float:
    try:
        a, b = points.split("/")
        return float(a) / float(b)
    except Exception:
        return 1.0


def profile(user_id: str) -> dict:
    """Todo lo que el tutorial necesita saber de este usuario."""
    user = workspaces.get_user(user_id) or {}
    base = user.get("base_case") or workspaces.base_case_of(user_id)
    fh, persona = _load_case(base)
    label = user.get("label") or user_id

    household = fh.get("case", {}).get("household", [])
    adults = [m for m in household if m.get("role") != "child"]
    kids = [m.get("first_name", "") for m in household if m.get("role") == "child"]
    first = label.split()[0].lower() if label else ""
    me = next((m for m in adults if (m.get("first_name") or "").lower() == first), None) \
        or next((m for m in adults if m.get("role") == "client"), adults[0] if adults else {})
    others = [m.get("first_name", "") for m in adults if m is not me and m.get("first_name")]

    score = fh.get("score", {})
    pillars = [{"name": p.get("pillar", ""), "points": p.get("points_shown_in_app", ""),
                "ratio": _ratio(p.get("points_shown_in_app", ""))} for p in score.get("pillars", [])]
    km = fh.get("key_metrics", {})
    age, ret = me.get("age"), me.get("retirement_age")
    return {
        "id": user_id,
        "name": (label.split(" & ")[0] if " & " in label else label).strip(),
        "label": label,
        "base_case": base,
        "city": fh.get("case", {}).get("city", ""),
        "age": age,
        "retirement_age": ret,
        "years_to_retirement": (ret - age) if isinstance(age, int) and isinstance(ret, int) else None,
        "partner": others[0] if others else None,
        "kids": kids,
        "is_copy": bool(user.get("custom")),
        "copied_from": user.get("copied_from"),
        "score": score.get("published_score"),
        "band": score.get("band", ""),
        "capped": bool(score.get("caps_applied")),
        "pillars": pillars,
        "weakest": min(pillars, key=lambda p: p["ratio"]) if pillars else None,
        "strongest": max(pillars, key=lambda p: p["ratio"]) if pillars else None,
        "moves": score.get("top_moves", []),
        "net_worth": km.get("netWorthStatement", {}).get("netWorth", {}).get("total"),
        "free_cash_flow": km.get("cashflowStatement", {}).get("freeCashflow", {}).get("total"),
        "style": persona.get("D5"),
        "anchor": persona.get("D6"),
        "persona": persona,
        "has_data": bool(fh),
    }


# ---------------------------------------------------------------- textos
def _pillar(p: dict | None) -> str:
    return PILLAR_ES.get(p["name"], p["name"].lower()) if p else ""


def _move(m: dict) -> str:
    return MOVE_ES.get(m.get("title", ""), (m.get("title") or "").lower())


def _band_line(p: dict) -> str:
    s, band = p["score"], BAND_ES.get(p["band"], p["band"])
    line = f"Tu **score** es **{s}/100** ({band}): una nota de 0 a 100 sobre lo preparada que está tu economía."
    if p["band"] == "critical":
        line += " Suena duro, pero casi todo se arregla ordenando prioridades; para eso está el plan."
    elif p["band"] == "vulnerable":
        line += " Tienes una base real y huecos concretos que cerrar."
    elif p["band"] == "stable":
        line += " Vas bien encaminado" + (", con un tope puntual que se puede levantar." if p["capped"] else ".")
    elif p["band"] == "strong":
        line += " Partes de una posición fuerte; ahora se trata de afinar."
    return line


def condense(text: str, limit: int = 800) -> str:
    """Principio del resumen ejecutivo (que es largo): párrafos enteros hasta `limit` caracteres."""
    paras = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    paras = [x for x in paras if not re.fullmatch(r"#{1,6}\s.*", x)] or paras      # sin títulos sueltos
    out, n = [], 0
    for para in paras:
        if out and n + len(para) > limit:
            break
        out.append(para)
        n += len(para)
    res = "\n\n".join(out)
    if len(res) > limit * 1.5:                                  # un solo párrafo gigante: cortar en una frase
        cut = res[: int(limit * 1.2)]
        end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
        res = cut[: end + 1] if end > limit * 0.4 else cut
    return res


def steps(user_id: str) -> list[dict]:
    """Pasos del tutorial para este usuario: [{icon, title, body}]. Con datos reales de su caso."""
    p = profile(user_id)
    if not p["has_data"] or p["score"] is None:
        return GENERIC_STEPS

    name, who = p["name"], p["partner"]
    out = []

    # 1) Bienvenida con score, y lo que le mueve
    intro = [f"Hola, **{name}**. " + _band_line(p)]
    if p["anchor"]:
        intro.append(ANCHOR_TEXT[p["anchor"]])
    if p["style"]:
        intro.append(STYLE_TEXT[p["style"]])
    out.append({"title": f"Bienvenido, {name}", "body": "\n\n".join(intro)})

    plan = workspaces.load_plan_summary(user_id)
    if plan and plan.get("headline"):
        out[0]["body"] += f"\n\n> {plan['headline']}"

    # 2) Dónde estás
    if plan and plan.get("executive_summary"):
        full = plan["executive_summary"].strip()
        short = condense(full)
        out.append({"title": "Tu resumen", "body": short,
                    "more": full if len(short) < len(full) else "",
                    "speech": (plan.get("headline", "") + ". " + short)})
    else:
        facts = []
        if p["net_worth"] is not None:
            facts.append(f"- Lo que tienes, descontando lo que debes (tu patrimonio): **{_money(p['net_worth'])}**.")
        fcf = p["free_cash_flow"]
        if fcf is not None:
            facts.append(f"- Lo que te sobra al año después de pagar tus gastos: **{'-' if fcf < 0 else ''}{_money(fcf)}**"
                         + (" (gastas más de lo que ingresas)." if fcf < 0 else "."))
        if p["strongest"] and p["weakest"] and p["strongest"] is not p["weakest"]:
            facts.append(f"- Tu punto fuerte: **{_pillar(p['strongest'])}** ({p['strongest']['points']}).")
            facts.append(f"- Tu mayor hueco: **{_pillar(p['weakest'])}** ({p['weakest']['points']}).")
        if p["retirement_age"]:
            y = p["years_to_retirement"]
            facts.append(f"- Objetivo: jubilarte a los **{p['retirement_age']}**" + (f" (dentro de {y} años)." if y else "."))
        out.append({"title": "Dónde estás hoy",
                    "body": "Esto es lo que dice tu informe:\n\n" + "\n".join(facts)
                            + "\n\nEsto es la versión básica. Con tu plan generado (botón **Cargar plan**, arriba), el Co-Pilot lo convierte "
                              "en un resumen y un plan a tu medida, y este tutorial los muestra aquí."})

    # 3) Plan de acción
    if plan and (plan.get("immediate_action") or plan.get("tasks")):
        act = plan.get("immediate_action") or {}
        lines = []
        if act.get("title"):
            lines.append(f"**Para hoy:** {act['title']}" + (f" — {act['expected_impact']}" if act.get("expected_impact") else ""))
            if act.get("reason"):
                lines.append(f"\n{act['reason']}")
        tasks = [t for t in plan.get("tasks", []) if t.get("title")][:4]
        if tasks:
            lines.append("\nDespués, en tu tablero:\n")
            lines += [f"- {t['title']}" + (f" ({t['impact']})" if t.get("impact") else "") for t in tasks]
        lines.append("\n**Arrastra** una tarjeta entre *To do*, *In process* y *Done*, o haz clic para ver los pasos.")
        out.append({"title": "Tu plan de acción", "body": "\n".join(lines)})
    else:
        lines = ["Es un tablero con tus tareas, empezando por la más urgente. Las que más mueven tu score:\n"]
        for m in p["moves"][:3]:
            a, b = m.get("score_before"), m.get("score_after")
            gain = f" ({a} → {b})" if a is not None and b is not None and b != a else ""
            lines.append(f"- {_move(m).capitalize()}{gain}")
        lines.append("\n**Arrastra** una tarjeta entre *To do*, *In process* y *Done*, o haz clic para ver el detalle.")
        out.append({"title": "Tu plan de acción", "body": "\n".join(lines)})

    # 4) Proyección y datos
    ret_txt = (f" hasta tu jubilación a los {p['retirement_age']}" if p["retirement_age"] else "")
    body = (f"Aquí ves cuánto dinero tendrás{ret_txt}, contando lo que tienes menos lo que debes.\n\n"
            "- **Edita cualquier celda** de la tabla y el gráfico se actualiza al momento.\n"
            "- Añade una fila para un mes nuevo o una columna para seguir otra cifra.\n")
    fcf = p["free_cash_flow"]
    if fcf is not None and fcf < 0:
        body += "- Mira primero la columna de gastos: es donde puedes recortar para que tu dinero deje de bajar."
    elif p["weakest"]:
        body += f"- Prueba a cambiar el ahorro mensual y mira cómo se mueve el gráfico; tu hueco principal es {_pillar(p['weakest'])}."
    out.append({"title": "Proyección y datos", "body": body})

    # 5) Chat con ejemplos propios
    ex = suggestions(user_id)
    out.append({"title": "Pregunta al Co-Pilot",
                "body": "Conoce tu caso y puede **cambiar la tabla y las tareas por ti**. Con tus palabras, por ejemplo:\n\n"
                        + "\n".join(f"- *«{t}»*" for _, t in ex[:3])
                        + "\n\nCada respuesta tiene un botón **Escuchar** para escucharla."})

    # 6) Pareja / usuarios
    if p["is_copy"]:
        src = workspaces.get_user(p["copied_from"] or "")
        origin = f" de **{src['label']}**" if src else ""
        out.append({"title": "Tu propia copia",
                    "body": f"Estás en tu copia del plan{origin}. Empezó igual que el original y ahora es tuya: "
                            "lo que cambies aquí no afecta a nadie más. Tus datos de partida (lo que tienes, lo que debes, tus objetivos) "
                            f"siguen siendo los del hogar, así que el informe de arriba es el de {p['label'] if not who else 'vuestro hogar'}."})
    elif who:
        out.append({"title": f"{name} y {who}",
                    "body": f"Cada uno puede tener **su propio usuario**. Con **Usuarios** crea el de {who} "
                            "**copiando tus datos**: empieza igual y luego lo personaliza sin tocar el tuyo."})
    else:
        out.append({"title": "Si alguien más se une",
                    "body": "Con **Usuarios** puedes crear otro usuario **copiando tus datos** (una pareja, un asesor…). "
                            "Cada uno edita lo suyo sin afectar al otro."})
    if not plan:
        out[-1]["body"] += "\n\nPara tener el tutorial completo, pulsa **Cargar plan** (arriba) y el Co-Pilot lo genera."
    return out


def suggestions(user_id: str) -> list[tuple[str, str]]:
    """Cuatro ideas para el estado vacío del chat, con sus palabras y sus cifras."""
    p = profile(user_id)
    if not p["has_data"] or p["score"] is None:
        return []
    out = [("Explícame mi score",
            "Explícame mi score de salud financiera y cuál es mi principal cuello de botella, sin tecnicismos.")]
    plan = workspaces.load_plan_summary(user_id)
    first_task = ((plan or {}).get("immediate_action") or {}).get("title")
    if first_task:
        out.append(("Mi primera acción",
                    f"Explícame con detalle «{first_task}»: por qué es lo primero y qué pasos concretos tengo que dar hoy."))
    elif p["moves"]:
        m = p["moves"][0]
        out.append(("Mi primer paso",
                    f"Explícame con detalle cómo «{_move(m)}» mejora mi score y qué pasos concretos tengo que dar. "
                    "Si procede, añádelo a mis tareas."))
    if p["weakest"]:
        out.append((f"Mi punto más débil: {_pillar(p['weakest'])}",
                    f"Mi área más floja es {_pillar(p['weakest'])}. ¿Qué haría yo primero y qué cambiarías en mi tabla?"))
    out.append(("Me dan un bonus de 15.000 $",
                "Voy a recibir un bonus de 15.000 $. ¿Qué hago con él? Aplica los cambios que recomiendes en mi tabla."))
    return out[:4]


GENERIC_STEPS = [
    {"title": "Bienvenido a tu plan",
     "body": "Aquí tu plan financiero deja de ser un documento largo y se convierte en algo que puedes "
             "**mover, probar y preguntar**. En un minuto te enseñamos las tres pestañas."},
    {"title": "Plan de acción",
     "body": "Un tablero con las tareas del plan. **Arrastra** las tarjetas entre *To do*, *In process* y *Done*."},
    {"title": "Proyección y datos",
     "body": "Edita cualquier celda de la tabla y el gráfico se actualiza."},
    {"title": "Pregunta al Co-Pilot",
     "body": "Pregunta con tus palabras; puede **cambiar la tabla y las tareas por ti**. "
             "Cada respuesta tiene un botón **Escuchar** para escucharla."},
    {"title": "Usuarios",
     "body": "Con **Usuarios** puedes crear otro usuario copiando los datos de este. "
             "Si el plan está vacío, pulsa **Cargar plan**."},
]

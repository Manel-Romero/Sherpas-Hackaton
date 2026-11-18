"""Glosario: los términos financieros que aparecen en el tutorial y en el chat llevan un subrayado
punteado y, al pasar el ratón por encima, se ve su definición en lenguaje llano.

    annotate(texto_markdown) -> texto_markdown con <span class="gloss" data-def="...">término</span>

Pensado para escritorio (ratón). La definición se dibuja en una capa fija sobre la página (install()), así
que nunca la recorta el borde del tutorial ni del chat; si ese script no carga, queda un tooltip solo con CSS. Solo se marca la primera aparición de cada término en cada texto, para no
llenarlo de subrayados. Nunca toca código (``` o `…`) ni las direcciones de los enlaces Markdown. Los `<`
del texto se escapan, así que el HTML que pudiera venir del modelo no se interpreta.
"""
import html
import re

# término (en minúsculas) -> definición. Los términos más largos se buscan primero.
GLOSSARY: dict[str, str] = {
    "patrimonio neto": "Todo lo que tienes (casa, ahorros, inversiones) menos todo lo que debes.",
    "patrimonio": "Lo que tienes (casa, ahorros, inversiones). En «patrimonio neto» se le resta además lo que debes.",
    "flujo de caja libre": "El dinero que te sobra después de pagar todos tus gastos. Si es negativo, gastas más de lo que ingresas.",
    "flujo de caja": "La diferencia entre el dinero que entra y el que sale.",
    "fondo de emergencia": "Dinero apartado para imprevistos: perder el empleo, una avería, un gasto médico.",
    "liquidez": "Dinero que puedes usar ya, sin vender nada ni pagar penalizaciones.",
    "seguro paraguas": "Seguro de responsabilidad civil adicional: te cubre si te reclaman una indemnización mayor que la que cubren tus otros seguros.",
    "responsabilidad civil": "La obligación de pagar por un daño que causas a otra persona.",
    "seguro de vida": "Seguro que paga una cantidad a tu familia si falleces.",
    "tasa de retiro": "El porcentaje de tus ahorros que sacas cada año una vez jubilado.",
    "cartera": "El conjunto de tus inversiones.",
    "renta variable": "Inversiones en acciones: pueden subir o bajar mucho, pero a largo plazo suelen rendir más.",
    "renta fija": "Inversiones como bonos, que pagan un interés más estable y arriesgan menos.",
    "concentración": "Tener mucho dinero en una sola inversión o empresa: si le va mal, te afecta mucho.",
    "diversificación": "Repartir el dinero en inversiones distintas para no depender de una sola.",
    "diversificar": "Repartir el dinero en inversiones distintas para no depender de una sola.",
    "amortizar": "Devolver parte de una deuda antes de tiempo.",
    "amortización": "Devolver parte de una deuda antes de tiempo.",
    "interés compuesto": "Ganar intereses también sobre los intereses que ya has ganado: el dinero crece cada vez más rápido.",
    "inflación": "La subida general de los precios: con el tiempo, el mismo dinero compra menos.",
    "cuello de botella": "El punto que más frena tu situación financiera.",
    "score": "Nota de 0 a 100 que resume lo preparada que está tu economía: ahorro, deuda, inversión, reserva y seguros.",
    "401(k)": "Plan de ahorro para la jubilación que ofrece tu empresa en EE. UU., con ventajas fiscales.",
    "roth ira": "Cuenta personal de jubilación (EE. UU.): pagas los impuestos ahora y no al sacar el dinero.",
    "ira": "Cuenta personal de ahorro para la jubilación en EE. UU., con ventajas fiscales.",
    "roth": "Tipo de cuenta de jubilación (EE. UU.): pagas los impuestos ahora y no al sacar el dinero.",
    "hsa": "Cuenta de ahorro para gastos médicos (EE. UU.) con ventajas fiscales.",
    "plan 529": "Cuenta de ahorro para los estudios de tus hijos (EE. UU.) con ventajas fiscales.",
    "etf": "Fondo que cotiza en bolsa y agrupa muchas inversiones en un solo producto.",
    "tae": "El coste (o rendimiento) real de un préstamo o un ahorro en un año, contando intereses y comisiones.",
}

# Siglas que en minúsculas son palabras normales en castellano («ira», «tae»…): solo en mayúsculas.
_CASE_SENSITIVE = {"ira": "IRA", "roth ira": "Roth IRA", "hsa": "HSA", "etf": "ETF", "tae": "TAE"}

_TERMS = sorted(GLOSSARY, key=len, reverse=True)
_PATTERN = re.compile(
    r"(?<![\w])(" + "|".join(f"(?-i:{re.escape(_CASE_SENSITIVE[t])})" if t in _CASE_SENSITIVE else re.escape(t)
                             for t in _TERMS) + r")(?![\w])", re.IGNORECASE)
# Partes que no se tocan: bloques de código, código en línea y la dirección de los enlaces Markdown.
_PROTECTED = re.compile(r"(```.*?```|`[^`\n]*`|\]\([^)\s]*\))", re.S)


def _wrap(text: str, seen: set) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1).lower()
        if key in seen:
            return m.group(0)
        seen.add(key)
        return f'<span class="gloss" data-def="{html.escape(GLOSSARY[key], quote=True)}">{m.group(0)}</span>'
    return _PATTERN.sub(repl, text)


def annotate(text: str) -> str:
    """Devuelve `text` con cada término del glosario marcado la primera vez que aparece."""
    seen: set = set()
    parts = _PROTECTED.split(str(text or ""))
    for i, part in enumerate(parts):
        if i % 2 == 0:                                   # fuera de las partes protegidas
            parts[i] = _wrap(part.replace("<", "&lt;"), seen)
    return "".join(parts)


def markdown(st, text: str) -> None:
    """st.markdown con el glosario (se pasa el módulo `streamlit`)."""
    st.markdown(annotate(text), unsafe_allow_html=True)


# Capa de tooltip en la página principal. Se inyecta como <script> en el documento de la app (no en el
# iframe del componente), así sigue funcionando aunque Streamlit vuelva a dibujar el componente.
_TIP_JS = r"""
(function () {
  if (window.__glossTip) return;
  var tip = document.createElement('div');
  tip.className = 'gloss-tip';
  document.body.appendChild(tip);
  window.__glossTip = tip;
  document.documentElement.classList.add('gloss-js');
  function show(el) {
    tip.textContent = el.getAttribute('data-def') || '';
    tip.style.display = 'block';
    var r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    var x = Math.min(Math.max(8, r.left), window.innerWidth - w - 8);
    var y = r.bottom + 6;
    if (y + h > window.innerHeight - 8) y = r.top - h - 6;
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  }
  function term(e) { return e.target && e.target.closest ? e.target.closest('.gloss') : null; }
  document.addEventListener('mouseover', function (e) { var el = term(e); if (el) show(el); });
  document.addEventListener('mouseout', function (e) {
    var el = term(e);
    if (el && !(e.relatedTarget && el.contains(e.relatedTarget))) tip.style.display = 'none';
  });
  document.addEventListener('scroll', function () { tip.style.display = 'none'; }, true);
})();
"""


def install() -> None:
    """Instala la capa de tooltips en la página (una vez por pestaña del navegador). Llamar en cada ejecución."""
    import json
    import streamlit.components.v1 as components
    components.html(
        "<script>(function(){try{var D=window.parent.document;if(window.parent.__glossTip)return;"
        "var s=D.createElement('script');s.textContent=" + json.dumps(_TIP_JS) + ";D.head.appendChild(s);}"
        "catch(e){}})();</script>",
        height=0,
    )

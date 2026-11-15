# Propuesta de Idea - Hackathon Sherpas Wealth x Sigma Data Club

**Equipo:** [Nombre de tu equipo]  
**Fecha:** 13 de Noviembre, 2026 (Entrega 22:00)  
**Reto:** *"Haced que el diagnóstico hable"* (Llevar a la familia del plan a la acción)

---

### 1. Qué vamos a construir (What to build)
* Un **copiloto interactivo de diagnóstico financiero** orquestado con **FastAPI** y **LangGraph**, que transforma el reporte estático de Sherpas en un simulador guiado de toma de decisiones.
* Permite a familias como Timothy y Melanie interactuar mediante lenguaje natural y escenarios *"What-If"* interactivos (ej.: *"¿Qué pasa si amortizo hoy los 6.800 $ de la tarjeta al 18% con mi colchón de liquidez?"* o *"¿Y si me jubilo a los 64?"*), proyectando el impacto directo en su puntuación y patrimonio futuro.
* Interfaz funcional, ágil y visual desarrollada en **Streamlit** (o micro-frontend asistido), centrada en claridad radical, comparación visual antes/después y un botón de micro-compromiso de acción inmediata sin fricción.

### 2. Por qué (Why)
* **Ataca el problema real:** Sherpas ya calcula los números en 10 minutos; el cuello de botella es que el cliente entienda el plan y pase a la acción sin un asesor delante.
* **Garantía de fidelidad (Grounding):** LangGraph permite estructurar un flujo de estados determinista y seguro que consulta los datos del MCP/JSON del cliente (sin recalcular ni alucinar cifras financieras críticas).
* **Foco en el impacto y motivación:** En lugar de un informe abrumador de 40 páginas, reduce la fricción psicológica centrándose en el primer paso de alto impacto (la "Top Move": liquidar deuda tóxica al 18% con el exceso de liquidez).

### 3. Qué consideramos y descartamos, y por qué (Ruled out & trade-offs)
* **Voz en tiempo real / WebRTC con ElevenLabs como núcleo:**
  * *Considerado:* Usar el starter de voz provisto.
  * *Descartado:* Consume rápidamente el presupuesto de \$50 en créditos, añade latencia y riesgo en la demo en vivo, y las familias necesitan ver y verificar números y gráficos antes de tomar decisiones sobre su dinero.
* **Frontend complejo desde cero (React / Next.js pesado):**
  * *Considerado:* Diseñar una SPA completa desde cero.
  * *Descartado:* El equipo no cuenta con perfiles dedicados de frontend; gastar tiempo en CSS/JS restaría foco a la calidad del razonamiento, grounding y flujo de acción. Streamlit / UI asistida permite iterar rápido y garantizar una entrega 100% funcional.
* **Chatbot conversacional genérico:**
  * *Descartado:* Penalizado por los criterios de evaluación de Sherpas (un chat estándar ya existe). Nuestra propuesta se basa en simulación reactiva de decisiones y planes de acción accionables.

# 📚 Base de Conocimiento y Guía Maestra del Proyecto
## Hackathon Sherpas Wealth x UPV Sigma Data Club (Noviembre 2026)

---

## 1. El Reto y la Misión del Hackathon

### 1.1 Contexto de Negocio: Sherpas Wealth
Sherpas Wealth es una plataforma de Inteligencia Artificial creada para asesores financieros independientes que atienden a familias.
En el ciclo tradicional de un asesor existen **tres grandes trabajos**:
1. **Reunir los datos (Intake):** Extractos bancarios, nóminas, hipotecas, declaraciones de impuestos. *(Resuelto por el módulo Intake de Sherpas)*.
2. **Hacer los cálculos y proyecciones:** Plan financiero, cálculo de impuestos, proyecciones de jubilación y asignación de carteras. *(Resuelto por los agentes Paraplanner y Portfolio Analyst de Sherpas, reduciendo el proceso de 8 horas a 10 minutos por cliente)*.
3. **Explicárselo al cliente y llevarlo a la acción:** Resolver dudas, alinear expectativas entre cónyuges y lograr que ejecuten las recomendaciones. **Este paso sigue siendo 100% manual**, consume horas de reuniones y es donde muchos planes quedan archivados sin ejecutarse.

### 1.2 El Reto: *"Haced que el diagnóstico hable"*
* **Objetivo:** Construir una solución interactiva que tome el diagnóstico financiero generado por Sherpas y logre que la familia lo entienda a la primera y **se motive a dar el primer paso sin necesidad de tener al asesor delante**.
* **Regla de oro de los números (Grounding estricto):** **No se deben recalcular ni inventar cifras financieras**. El motor de Sherpas ya calculó las cifras con exactitud. El jurado evalúa la experiencia de usuario, la empatía y la comunicación, penalizando las alucinaciones numéricas.

### 1.3 Calendario y Entregables
* **12 Nov, 15:00:** Kick-off y clase magistral de MCP (Edificio 1E, Aula 2.3 UPV).
* **13 Nov, 22:00:** Entrega de la Idea / Plan del viernes vía Discord `/entrega` (1 página en bullets: qué construir, por qué y qué se descartó).
* **18 Nov, 23:59:** **Entrega Final** vía Discord `/entrega`:
  1. Enlace al repositorio público de GitHub.
  2. MVP funcional (enlace accesible o instrucciones claras de despliegue/ejecución en el README).
  3. Enlace a vídeo de 2 minutos (YouTube no listado o Google Drive).
  4. Documento explicativo de diseño (0.5 a 1 página) detallando qué se construyó, por qué y qué no funcionó.
* **19 Nov, 12:45:** **Demo Day** (Pitch en directo de 2 minutos por equipo ante el jurado).

### 1.4 Criterios de Evaluación del Jurado (100 Puntos)
| Criterio | Puntos | Enfoque clave |
|---|---|---|
| **Comprensión (Understanding)** | 20 pts | Que alguien sin base financiera entienda su diagnóstico y sepa qué hacer. |
| **Ganas de actuar (Motivation to act)** | 20 pts | Inspira un primer paso inmediato y facilita el seguimiento continuo. |
| **Cautivador (Captivating)** | 20 pts | Capta la atención en los primeros segundos y mantiene el interés. |
| **Personalizado (Personal)** | 15 pts | Adaptado a la dinámica psicológica y metas específicas del hogar. |
| **Creatividad (Creativity)** | 15 pts | Aporta valor real más allá de un simple chatbot conversacional o tour genérico. |
| **Plan del viernes (Friday Plan)** | 10 pts | Claridad, realismo y honestidad en el alcance y descartes iniciales. |

---

## 2. El Servidor MCP de Sherpas (Model Context Protocol)

El **MCP de Sherpas** es el servidor de datos oficial (de solo lectura) que provee los casos y planes financieros completos y fieles a la realidad para el hackathon.

Funciona sobre **HTTP POST con JSON-RPC 2.0** (`https://mcp-hackathon.sherpaswealth.com/mcp`) mediante autenticación Bearer (`Authorization: Bearer <MCP_TOKEN>`) y expone **2 herramientas principales**:

---

### 2.1 Herramienta 1: `list_cases`
Devuelve el listado de los **4 casos de familias** con sus metadatos básicos:
* **Identificadores**: `timothy-melanie-weah`, `michael-carter`, `daniel-emily-johnson`, `samantha-lewis`.
* **Datos demográficos**: Miembros del hogar, edades, ciudad, estado y estado de declaración de impuestos.
* **Score inicial y banda**: Puntuación de salud financiera (0-100) y categoría (`critical`, `vulnerable`, `stable`, `strong`).

---

### 2.2 Herramienta 2: `get_case(caseId, part, section)`
Permite consultar los datos profundos de cualquiera de las 4 familias. Cada caso se divide en **3 grandes bloques**:

1. **`persona`** *(Markdown)*:
   * **Perfil psicológico y de toma de decisiones**: Nivel de riqueza, etapa de vida, estilo de decisión, motivaciones y ancla emocional (`D0` a `D6`).
   * **Tensiones y preocupaciones**: Miedos subjetivos vs. problemas objetivos de cada miembro (ej. la aversión al riesgo de Melanie frente al deseo de crecimiento de Timothy).

2. **`financial-health`** *(JSON, ~20k tokens)*:
   * **Balance completo**: Ingresos, gastos fijos y variables, cuentas bancarias, inmuebles, deudas y seguros.
   * **Desglose de los 5 pilares**: Ahorro/flujo de caja, deuda, inversión, liquidez y protección/seguros.
   * **Hard caps (topes de score)**: Reglas que limitan el score (ej. tope de 60 por saldo en tarjeta de crédito cara o falta de seguro de vida).
   * **Proyecciones anuales**: Evolución patrimonial año a año hasta el final del plan.

3. **`investment-analysis`** *(JSON, ~25k tokens)*:
   * **Posiciones de cartera**: Tickers, cuentas (401k, IRA, taxable), pesos, clases de activos y comisiones.
   * **Asignación actual vs. objetivo**: Comparativa frente a la asignación recomendada (glidepaths EFC) y cálculo del *cash drag*.
   * **Arrastre fiscal (Tax Drag)**: Ineficiencias fiscales cuantificadas (ej. fondos de bonos de alto rendimiento mantenidos en cuentas no exentas de impuestos).
   * **Brecha de jubilación**: Capital necesario frente al proyectado.

> **Uso del parámetro `section`:** Como `financial-health` e `investment-analysis` son muy extensos (~20k-25k tokens), se puede especificar `section` (ej. `"score"`, `"narrative"`, `"D4"`) para extraer únicamente la subclave requerida y optimizar consumo y latencia.

---

### 2.3 ¿Para qué sirve en el reto?
Sherpas ya hace el cálculo numérico complejo; el MCP entrega ese resultado estructurado para que los equipos **no inventen cifras** y dediquen todo su esfuerzo a resolver el cuello de botella: **la experiencia de comunicación, comprensión y acción del cliente** (*"Bring the plan to life"*).

---

### 2.4 Autenticación, Caducidad y Fallback Offline
* **Obtención del Token:** Se genera con el email registrado en `https://mcp-hackathon.sherpaswealth.com/personal-token`.
* **Caducidad:** Expira a las **72 horas**. Requiere renovación periódica.
* **Fallback Offline (Recomendado):** En la carpeta local [`cases/`](file:///home/manel/Projects/Sherpas-Hackaton/cases/) se encuentran copias locales idénticas de los 3 archivos para cada caso (`financial-health.json`, `investment-analysis.json`, `persona.md` y `report.pdf`). No expiran y eliminan dependencias de red en pruebas y demos.

---

### 2.5 Ejemplo de Conexión MCP en Python
```python
import asyncio, json, os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

load_dotenv()

async def fetch_case():
    token = os.environ.get("MCP_TOKEN")
    http = create_mcp_http_client(headers={"Authorization": f"Bearer {token}"})
    async with streamable_http_client("https://mcp-hackathon.sherpaswealth.com/mcp", http_client=http) as (read, write, *_):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.call_tool("get_case", {
                "caseId": "timothy-melanie-weah",
                "part": "financial-health",
                "section": "score"
            })
            print(json.loads(response.content[0].text))

asyncio.run(fetch_case())
```

---

## 3. Proxy de Inteligencia Artificial (OpenAI-Compatible)

Sherpas proporciona un proxy compatible con la API de OpenAI financiado con créditos del hackathon.

### 3.1 Configuración de Conexión
* **Base URL:** `https://llm-hackathon.sherpaswealth.com/v1`
* **WebSocket URL (Realtime/Voz):** `wss://llm-hackathon.sherpaswealth.com/v1/realtime`
* **Autenticación:** Cabecera `Authorization: Bearer <TEAM_KEY>` (provisto por los mentores en Discord).
* **Monitorización de Consumo:**
  ```bash
  curl https://llm-hackathon.sherpaswealth.com/key/info -H "Authorization: Bearer $TEAM_KEY"
  ```
  Devuelve `info.spend` y `info.max_budget`.

### 3.2 Presupuesto y Reglas de Uso
* **Crédito Total:** **$50.00 USD** por equipo (válido hasta el 21 de noviembre).
* **Límite específico ElevenLabs:** Máximo **$1.40 USD** del presupuesto total puede gastarse en voz con ElevenLabs (TTS/STT). Si se agota, solo falla ElevenLabs; los demás modelos siguen operativos.
* **Límites de Ratio:** 60 peticiones por minuto; máximo 4 sesiones/peticiones concurrentes.

### 3.3 Catálogo de Modelos y Tarifas
| Modelo | Modalidad | Tarifa Proxy | Notas |
|---|---|---|---|
| `deepseek-flash` | Texto | $0.30 / $1.20 por 1M tokens | Ultrarrápido y muy económico. |
| `gemini-3.5-flash-lite` | Texto | $0.30 / $2.50 por 1M tokens | Excelente contexto y velocidad. |
| `gpt-5-mini` | Texto | $0.25 / $2.00 por 1M tokens | Omitir `max_tokens` o fijar $\ge 1000$ (los tokens de razonamiento consumen cuota). |
| `gpt-realtime-2.1-mini` | Voz Realtime | $10 / $20 (audio) \| $0.60 / $2.40 (texto) | Protocolo OpenAI Realtime WS. |
| `gemini-3.8-live` | Voz Realtime | $3 / $12 (audio) \| $0.75 / $4.50 (texto) | La opción más barata para voz continua. |
| `eleven-flash-v2.5` | TTS (ElevenLabs) | $0.04 por 1k caracteres | La opción de voz recomendada por coste. |
| `scribe-v2` | STT (ElevenLabs) | $0.22 por hora de audio | Transcripción de voz. |

---

## 4. Las 4 Familias Sintéticas (`cases/`)

### 4.1 Caso Estrella: Timothy y Melanie Weah (`timothy-melanie-weah`)
* **Datos Familiares:**
  * Timothy (40 años) y Melanie (38 años). Viven en San Francisco, CA.
  * Hijos: Liam (6 años, universidad en 2038) y Josh (3 años, universidad en 2041).
  * Jubilación planificada: Timothy a los 62 años, Melanie a los 60 (en 21 años).
* **Ingresos y Patrimonio:**
  * Ingreso bruto conjunto: **$270,000 / año** (Timothy $150k, Melanie $120k).
  * Activos Totales: **$788,500** | Patrimonio Neto: **$695,500** | Activos Líquidos: **$360,000**.
  * Desglose de Cuentas:
    * **Efectivo / Ahorros líquidos:** **$150,000** (en cuenta que rinde solo un ~0.1%, generando apenas $150/año).
    * **401(k) Tradicional:** $125,000 (Timothy $70k, Melanie $55k). Ambos maximizan el match patronal ($8k y $6k).
    * **401(k) Roth:** $45,000 (Timothy $25k, Melanie $20k).
    * **Brokerage imponible:** $40,000.
    * **Vivienda Principal:** Valorada en $350,000 con deuda hipotecaria de **$50,000** al 6%.
* **Las Deudas:**
  * **Tarjeta de crédito revolving (Chase):** **$18,000 al 18% TAE**.
  * Préstamo de estudios: $15,000 al 5.5%.
  * Préstamo vehículo: $10,000 al 4.5%.
  * Hipoteca: $50,000 al 6%.
  * **Total deuda:** $93,000.
* **La Gran Paradoja / Tensión Central (T3 & O2):**
  * Tienen **$150,000 ociosos en el banco** mientras pagan **18% de interés sobre $18,000 de tarjeta**, pagando $300/mes (¡donde ~$270/mes son puros intereses tirados a la basura!). A este ritmo terminarían de pagar la tarjeta en septiembre de 2039.
  * Su fondo de emergencia necesario es de ~$75,000 a $85,000 (8-9 meses). Tienen un **excedente de caja limpia de más de $60,000**.
* **Diagnóstico Sherpas (Financial Health Score):**
  * **Puntuación Publicada:** **60 / 100** (Banda *"Stable"*).
  * **¿Por qué está capada en 60?**
    1. **Cap 1:** El balance de tarjeta de crédito al 18% impone un techo duro en 60.
    2. **Cap 2:** Cobertura de vida muy baja para padres con hijos pequeños impone un techo en 62.
    * *Sin estos caps su puntuación real sería de ~68 a 78.*
  * **Pilares de Puntuación:**
    * *Liquidez y Emergencia:* 100/100 (15/15 pts) - Sobresaliente.
    * *Ahorro y Flujo de Caja:* 86/100 (26/30 pts).
    * *Deuda:* 58/100 (12/20 pts) - Afectada por la tarjeta al 18%.
    * *Inversiones:* 56/100 (8/15 pts).
    * *Seguros y Protección:* 37/100 (7/20 pts) - Crítico.
* **Top Moves Generadas por Sherpas:**
  1. **Pagar $6,800 de la tarjeta al 18%** de inmediato usando efectivo ocioso $\rightarrow$ Elimina la exposición revolving de alto riesgo y rompe el cap de la puntuación (sube de 60 a 62).
  2. **Añadir $235,000 en seguro de vida** $\rightarrow$ Eleva el ratio de mortalidad y rompe el segundo cap.
  3. **Añadir $1,000,000 de póliza Umbrella (Responsabilidad civil)** $\rightarrow$ Protege su patrimonio ante demandas.
* **Perfil Psicológico y Dinámica de Pareja (`persona.md`):**
  * *D0 (Nivel Patrimonial):* EMERGING.
  * *D4 (Orientación de Riesgo):* **Desalineada (Misaligned)**. Timothy es Crecimiento (4) y Melanie es Moderada (3). Timothy tiene un ETF apalancado (UPRO, 3x) en su Roth, mientras Melanie prefiere seguridad.
  * *D5 (Estilo de Decisión):* **Colaborador**. Ambos toman decisiones juntos; la solución debe explicar el razonamiento para ambos.
  * *D6 (Ancla Motivacional):* **Protección** (Familia e hijos pequeños).

---

### 4.2 Los Otros Tres Casos
* **Michael Carter (`michael-carter`):**
  * 37 años, soltero, Austin TX.
  * Salario: $180,000. Puntuación: **26 / 100** (Banda *"Critical"*).
  * Dilema: Quiere comprar una casa de $550k en 2027 y retirarse a los 58 años, pero tiene graves agujeros de liquidez y flujo de caja insostenible.
* **Daniel y Emily Johnson (`daniel-emily-johnson`):**
  * 44 y 42 años, Denver CO. Puntuación: **52 / 100** (Banda *"Vulnerable"*).
  * Hipoteca grande ($560k), tarjetas al 24.9% TAE y grave déficit de seguro de vida ($250k contratados vs $1.6M recomendados).
* **Samantha Lewis (`samantha-lewis`):**
  * 47 años, madre soltera con dos adolescentes, Miami FL.
  * Salario alto: $250,000. Puntuación: **82 / 100** (Banda *"Strong"*).
  * El problema oculto: A pesar de su excelente puntuación actual, sus proyecciones indican que **se quedará sin dinero a los 73 años** debido a su ritmo de gasto y falta de optimización fiscal.

---

## 5. Arquitectura Técnica y Estrategia del Equipo

### 5.1 Stack Tecnológico Seleccionado
* **Backend:** **Python + FastAPI**.
* **Orquestación de Agentes y Flujos:** **LangGraph**.
  * Permite crear una máquina de estados determinista (StateGraph) donde los nodos financieros no alucinan, sino que leen y transforman de forma reproducible los datos de Sherpas.
  * Flujo de nodos previsto:
    1. *Node Ingest / MCP Reader:* Carga el perfil del cliente y sus datos clave.
    2. *Node Financial What-If Simulator:* Aplica simulaciones lógicas ("¿Qué pasa si amortizo $6.8k de la tarjeta hoy?").
    3. *Node Empathy & Narrative Generator:* Traduce el impacto numérico a lenguaje llano y motivador usando `deepseek-flash` o `gemini-3.5-flash-lite`.
    4. *Node Action Driver:* Presenta la llamada a la acción en un único paso sin fricción.
* **Frontend:** **Streamlit** (o micro-interfaz web reactiva generada).
  * Prioriza la velocidad de desarrollo y la claridad visual sin desperdiciar tiempo en maquetación compleja CSS/JS.
  * Muestra:
    * Score antes vs. Score después en tiempo real con barras de progreso y comparativa visual.
    * Explicador del impacto monetario (ahorro de $3,240/año en intereses).
    * Simulador interactivo con sliders (aportación a la tarjeta, edad de jubilación).
    * Botón de micro-compromiso de acción.

### 5.2 Estructura del Repositorio
```text
Sherpas-Hackaton/
├── cases/                         # Datos JSON y Markdown de las 4 familias
│   ├── timothy-melanie-weah/      # Caso de estudio principal
│   ├── michael-carter/
│   ├── daniel-emily-johnson/
│   └── samantha-lewis/
├── examples/                      # Ejemplos provistos por Sherpas
│   └── voice/                     # Starter de audio WebSockets/OpenAI Realtime
├── ENTREGA_VIERNES.md             # Propuesta y trade-offs entregados el viernes
├── KNOWLEDGE_BASE.md              # Este documento maestro
├── README.md                      # Guía general del hackathon
└── .env                           # Variables: MCP_TOKEN, TEAM_KEY (no subir al repo)
```

---

## 6. Claves para la Evaluación y el Pitch Final (19 Noviembre)

1. **Impacto en los primeros 10 segundos:** Mostrar inmediatamente la paradoja de Timothy y Melanie ($150k en caja al 0.1% vs $18k al 18% de tarjeta).
2. **Demostración "What-If" en vivo:** Mover un slider o pulsar un botón que muestre instantáneamente cómo amortizar la deuda libera el "cap" del score (subiendo de 60 a 62) y ahorra miles de dólares en intereses.
3. **Fidelidad Absoluta (Grounding):** Todas las cifras mostradas en pantalla deben coincidir milimétricamente con el archivo `financial-health.json`.
4. **El Entregable en Discord `/entrega`:** Debe incluir el enlace a GitHub, el link o instrucciones del MVP, el vídeo de 2 minutos y la memoria de diseño de media página explicando qué no funcionó y lecciones aprendidas.
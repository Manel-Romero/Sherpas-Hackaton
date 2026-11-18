# Guía Rápida de Ejecución: Sherpas Co-Pilot

Instrucciones directas para levantar y probar la aplicación en local.

---

## 1. Requisitos Previos

- **Python 3.11+**
- Archivo `.env` en la raíz con las credenciales configuradas (ver `.env.example`).

---

## 2. Instalación (si arrancas desde cero)

Si ya dispones del entorno virtual `.venv`, puedes saltar al paso 3.

```bash
# Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias limpias
pip install -r requirements.txt
```

---

## 3. Lanzar la Aplicación

Se requieren **dos terminales** (una para el Backend y otra para el Frontend):

### Terminal 1: Backend (FastAPI + LangGraph)
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
> API disponible en: [http://localhost:8000](http://localhost:8000)  
> Documentación interactiva Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Terminal 2: Frontend (Streamlit)
```bash
source .venv/bin/activate
streamlit run frontend/app.py
```
> Interfaz web abierta automáticamente en: [http://localhost:8501](http://localhost:8501)

---

## 4. Ejecutar Tests (Opcional)

Para verificar que todos los endpoints, herramientas y lógica conversacional funcionan correctamente:

```bash
source .venv/bin/activate
pytest
```

---

## 5. Pistas Rápidas para la Demo

1. **Casos Precargados:** Los 4 perfiles (*Michael Carter*, *Daniel & Emily*, *Samantha Lewis*, *Timothy & Melanie*) ya cuentan con proyecciones y tarjetas pregeneradas en el selector superior.
2. **Pestañas:**
   - **📋 Plan de Acción:** Tarjetas ejecutables con la acción inmediata prioritaria y roadmap semanal.
   - **📊 Proyección & Datos:** Gráfico interactivo Plotly de evolución patrimonial/deuda y hoja de cálculo editable.
   - **💬 Chat Co-Pilot:** Asistente empático en streaming. Incluye 4 botones rápidos para la presentación (*Gasto imprevisto*, *Diagnóstico*, *Bonus de amortización*, y *Comparativa visual con gráficos*).


---

## Usuarios, tutorial y datos

- Al abrir la app eliges **usuario**: los 4 casos de Sherpas o uno que hayas creado.
- **👥 Usuarios → Crear usuario copiando este**: crea un usuario nuevo con una copia de la tabla y de las tareas
  de otro (pensado para parejas: cada uno personaliza lo suyo sin tocar lo del otro). El chat no se copia.
- El **tutorial** se abre la primera vez que entra un usuario; se repite con el botón **❔ Tutorial**.
- Los datos de cada usuario viven en `data/cases/<usuario>/` (tabla, tareas, chat y `meta.json`).
  Un usuario copiado apunta con `base_case` a su caso de Sherpas, y el backend lo usa para leer su informe.
- La conversación se guarda: al volver otro día sigue ahí. **🚀 Cargar plan** pide al backend que genere el plan.

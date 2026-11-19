# Guia Rapida de Ejecucion: Sherpas Wealth Architecture

Instrucciones directas para levantar y probar la plataforma en local de forma inmediata.

---

## 1. Requisitos Previos

- **Python 3.11+**
- **Node.js 18+ / npm** (solo requerido si deseas compilar o desarrollar en caliente el frontal React)
- Archivo `.env` en la raiz del proyecto con las credenciales configuradas (ver `.env.example`).

---

## 2. Opciones de Ejecucion

Tienes dos formas directas de arrancar la aplicacion segun tu objetivo:

---

### Opcion A (Recomendada: Todo en Uno)
El backend FastAPI ya tiene integrada y sirve directamente la aplicacion React compilada (`frontend-react/dist`) desde la raiz. **Solo necesitas una unica terminal:**

```bash
# Activar entorno virtual
source .venv/bin/activate

# Arrancar servidor principal
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Plataforma Web React (Pro):** [http://localhost:8000](http://localhost:8000)
- **Documentacion Interactiva Swagger API:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Opcion B (Modo Desarrollo Frontend con Hot-Reload)
Si deseas modificar componentes de React en tiempo real con recarga instantanea (HMR):

#### Terminal 1: Backend API (FastAPI)
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Servidor de Desarrollo React (Vite)
```bash
cd frontend-react
npm run dev
```

- **Aplicacion en Desarrollo (Vite):** [http://localhost:3000](http://localhost:3000)  
  *(Las llamadas a `/api/*` se redirigen automaticamente hacia el backend en el puerto 8000).*

---

## 3. Comprobacion Rapida del Estado

Para verificar en un segundo que ambos servicios responden correctamente:

```bash
# Comprobar backend
curl -s http://localhost:8000/health

# Comprobar frontend (en opcion A)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/

# Ejecutar suite de tests automatizados (31 tests)
source .venv/bin/activate
pytest tests/
```

---

## 4. Guia de Navegacion para la Demo ante el Jurado

1. **Selector de Dossier Familiar (Cabecera):**
   - Permite alternar instantaneamente entre los 4 casos del hackathon:
     - *Michael Carter (Austin)*: HENRY con dilema de compra de vivienda en 2027 vs retiro a los 58 anos.
     - *Timothy & Melanie Weah (San Francisco)*: Paradoja de $150k en cuenta corriente vs deuda de tarjeta al 18% TAE.
     - *Daniel & Emily Johnson (Denver)*: Vulnerabilidad severa de proteccion ($1.35M de brecha de seguro de vida).
     - *Samantha Lewis (Miami)*: Precipicio invisible de agotamiento patrimonial a los 73 anos a pesar de score alto (82).

2. **Atajos de Teclado:**
   - Pulsa `1`: **Plan de Accion** (Tablero Linear de ejecucion de roadmap y pilares financieros).
   - Pulsa `2`: **Proyeccion & Datos** (Modelo financiero actuarial a 12 meses y hoja de calculo editable).
   - Pulsa `3`: **Terminal Co-Pilot** (Consola de inteligencia actuarial con streaming SSE).

3. **Dossier Psico-Financiero:**
   - Haz clic en el boton superior **"Dossier Psico-Financiero"** para desplegar el panel con las dimensiones del marco Sherpas (D0 Wealth Tier, D4 Riesgo, D5 Decisorio, Tension Principal y Alertas Criticas).

4. **Consultas Estrategicas en 1 Clic:**
   - En la pestana **Terminal Co-Pilot**, utiliza los 4 gatillos estrategicos superiores especificos de cada familia para demostrar la resolucion en tiempo real de compensaciones y simulaciones What-If.

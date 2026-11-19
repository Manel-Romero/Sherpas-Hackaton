# Propuesta de Producto: Sherpas Co-Pilot

Documento de propuesta y enfoque de producto para el hackathon de Sherpas Wealth.

---

## 1. El problema: por que se abandonan los planes financieros

Los informes financieros actuales tienen un nivel de detalle tecnico muy alto. Para un asesor son la herramienta ideal, pero para el cliente final suelen convertirse en una barrera:

- **Sobrecarga de informacion:** Cincuenta paginas de tablas, proyecciones y terminologia tecnica provocan paralisis. La familia no sabe por donde empezar y aplaza las decisiones.
- **Estatismo frente a imprevistos:** La vida real rara vez sigue una proyeccion a 30 años sin sobresaltos. Si a las dos semanas surge un gasto imprevisto o cambian los ingresos, el documento en PDF queda desfasado y el cliente pierde la referencia.
- **Falta de conexion emocional:** Cada familia tiene prioridades y temores distintos. En muchas ocasiones, ver una puntuacion baja genera rechazo en lugar de motivacion, o las discrepancias de criterio entre conyuges paralizan cualquier avance.

El reto no es calcular mejor los numeros —eso Sherpas ya lo hace de forma precisa—, sino lograr que el cliente comprenda su situacion y de el primer paso.

---

## 2. Nuestra propuesta: un plan que se adapta a las circunstancias

La idea central de **Sherpas Co-Pilot** no es construir otro visor de PDFs ni un chatbot aislado, sino un entorno interactivo dividido en tres paneles sincronizados:

```
+------------------------+------------------------+------------------------+
|       Dashboard        |     Lista de tareas    |      Chat Co-Pilot     |
|                        |                        |                        |
| Metricas clave,        | Accion inmediata para  | Conversacion empatica, |
| patrimonio, deudas y   | arrancar en minutos,   | simulacion de dudas y  |
| tablas de proyeccion   | guia a 4 semanas con   | ejecucion de cambios   |
| actualizables en vivo. | impacto cuantificado.   | en la interfaz.        |
+------------------------+------------------------+------------------------+
```

### La clave: adaptabilidad controlada sin salirse del plan original
La principal ventaja de este enfoque es como reacciona ante los cambios cotidianos del cliente:

Si el usuario dice: *"Este mes tengo que pagar una reparacion del coche y solo puedo ahorrar 150 € en lugar de los 400 € previstos"*, el asistente no responde con frases vacias. Mediante sus herramientas internas:
1. Ajusta la variable de ahorro de ese mes en el dashboard.
2. Reprograma la tarea correspondiente para el siguiente periodo.
3. Muestra el impacto real de esa decision sobre sus metas a largo plazo (por ejemplo: *"Tu objetivo de compra de vivienda en 2027 apenas se retrasa dos semanas; el fondo de emergencia sigue cubierto"*).

El plan se flexibiliza para absorber la realidad del cliente, pero **se mantiene dentro de los margenes y recomendaciones de seguridad definidos en el informe original de Sherpas**.

---

## 3. Cobertura de los criterios de valoracion

### Comprension y claridad (They get it)
En lugar de forzar al cliente a interpretar ratios financieros complejos, el sistema traduce cada dato a implicaciones cotidianas: cuantos meses de gastos cubre el dinero en cuenta, que coste tienen los intereses de las tarjetas o que pasaria si surge un problema de salud imprevisto.

### Motivacion a la accion (They act)
Para evitar la paralisis inicial, el sistema extrae una **accion prioritaria inmediata** que puede completarse en pocos minutos (por ejemplo, automatizar una transferencia mensual de ahorro al recibir la nomina o tramitar una poliza basica). A partir de ahi, despliega un plan semanal con tareas concretas y el impacto estimado de cada una (ahorro mensual, deuda reducida o variacion en el score).

### Enfoque personal (Made for them)
El agente toma en cuenta el perfil psicologico y las tensiones documentadas en el caso (`persona.md`):
- Adapta el lenguaje segun el nivel de familiaridad financiera del usuario.
- Evita el tono alarmista en casos con puntuaciones bajas (como el caso de Michael Carter, score 26), enfocandose en mejoras rapidas.
- Facilita la mediacion en casos familiares con diferente aversion al riesgo (como Timothy y Melanie Weah).

### Rigor tecnico y viabilidad
La arquitectura backend esta desarrollada con FastAPI y LangGraph, desacoplando la logica actuarial de la interfaz. El frontend esta desarrollado en React 19 + TypeScript + Vite + Tailwind CSS + Framer Motion, con renderizado fluido, soporte de voz neuronal en tiempo real y modo demo resiliente con cache offline. Permite tanto ejecucion local como despliegue estatico en GitHub Pages.

---

## 4. Esquema de presentacion (2 minutos para demo day)

### Introduccion (0:00 - 0:30)
- Plantear el problema comun: el cliente recibe un informe financiero de 50 paginas, no sabe que hacer primero y, en cuanto surge un imprevisto, el documento se queda en un cajon.
- Mostrar la pantalla principal de Sherpas Co-Pilot con los tres paneles integrados.

### Demostracion practica (0:30 - 1:20)
- **El arranque:** Mostrar como el plan se presenta con una accion inmediata clara en lugar de abrumar al cliente.
- **La interaccion adaptativa:** Escribir en el chat una situacion habitual: un gasto imprevisto que reduce la capacidad de ahorro del mes.
- **La respuesta del sistema:** Observar como el agente actualiza la cifra en el dashboard, reprograma la tarea y proyecta la grafica correspondiente, demostrando que el objetivo principal sigue bajo control.

### Impacto y valor para el negocio (1:20 - 1:50)
- Explicar como esto beneficia tanto a la familia (acompañamiento continuo) como al asesor financiero (clientes que llegan a las reuniones habiendo dado los primeros pasos y con dudas mucho mas concretas).

### Cierre (1:50 - 2:00)
- Resumen final: la combinacion del rigor en el calculo financiero de Sherpas con una interfaz interactiva que acompaña y se adapta a la vida real del cliente.

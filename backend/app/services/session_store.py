from typing import Any, Optional
from datetime import datetime, timezone
from backend.app.models.plan import MasterPlan, TaskItem, TaskImpact
from backend.app.models.dashboard import DashboardState, DashboardMetric
from backend.app.models.chat import ChatMessage, ToolExecutionLog

class SessionData:
    # Contenedor de datos reactivos por sesion
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.master_plan: Optional[MasterPlan] = None
        self.tasks: list[TaskItem] = []
        self.dashboard: Optional[DashboardState] = None
        self.summary_executive: str = ""
        self.persona_highlights: str = ""
        self.chat_history: list[ChatMessage] = []
        self.pending_charts: list[dict[str, Any]] = []
        self.last_tools_executed: list[ToolExecutionLog] = []
        self.last_change_applied: Optional[str] = None
        self.recent_tool_audits: list[dict[str, Any]] = []

    def add_task(self, task: TaskItem) -> None:
        self.tasks.append(task)

    def update_task_status(self, task_id: str, status: str) -> bool:
        for t in self.tasks:
            if t.id == task_id or t.title.lower() == task_id.lower():
                t.status = status  # type: ignore
                return True
        return False

    def remove_task(self, task_id: str) -> bool:
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id and t.title.lower() != task_id.lower()]
        return len(self.tasks) < initial_len

    @staticmethod
    def _normalize_metric_key(key: str) -> str:
        k = key.lower().strip().replace(" ", "_").replace("-", "_")
        aliases = {
            "ingreso_mensual": "monthly_income",
            "ingresos_mensuales": "monthly_income",
            "ingreso": "monthly_income",
            "ingresos": "monthly_income",
            "salario": "monthly_income",
            "salario_mensual": "monthly_income",
            "sueldo": "monthly_income",
            "gasto_mensual": "monthly_expenses",
            "gastos_mensuales": "monthly_expenses",
            "gasto": "monthly_expenses",
            "gastos": "monthly_expenses",
            "gastos_fijos": "monthly_expenses",
            "patrimonio": "net_worth",
            "patrimonio_neto": "net_worth",
            "riqueza": "net_worth",
            "score": "health_score",
            "salud_financiera": "health_score",
            "score_salud": "health_score",
            "puntaje": "health_score",
            "flujo_libre": "monthly_free_cashflow",
            "flujo_caja": "monthly_free_cashflow",
            "flujo_de_caja": "monthly_free_cashflow",
            "cashflow": "monthly_free_cashflow",
            "ahorro_libre": "monthly_free_cashflow",
            "monthly_cashflow": "monthly_free_cashflow",
            "activos": "total_assets",
            "total_activos": "total_assets",
            "deudas": "total_liabilities",
            "total_deudas": "total_liabilities",
            "pasivos": "total_liabilities",
            "total_pasivos": "total_liabilities",
        }
        return aliases.get(k, k)

    def _ensure_dashboard(self) -> DashboardState:
        if self.dashboard:
            return self.dashboard
        defaults = {
            "michael-carter": (26, 218500.0, 247000.0, 28500.0, 15000.0, 9306.0),
            "daniel-emily-johnson": (52, 620000.0, 980000.0, 360000.0, 22000.0, 14200.0),
            "samantha-lewis": (82, 1150000.0, 1450000.0, 300000.0, 28000.0, 16500.0),
            "timothy-melanie-weah": (60, 480000.0, 750000.0, 270000.0, 19500.0, 13800.0),
        }
        sc, nw, ta, tl, inc, exp = defaults.get(self.case_id, (50, 200000.0, 250000.0, 50000.0, 15000.0, 9000.0))
        cf = inc - exp
        self.dashboard = DashboardState(
            case_id=self.case_id,
            health_score=sc,
            net_worth=nw,
            total_assets=ta,
            total_liabilities=tl,
            monthly_income=inc,
            monthly_expenses=exp,
            monthly_free_cashflow=cf,
            metrics={
                "health_score": DashboardMetric(
                    id="health_score",
                    label="Score de Salud Financiera",
                    value=sc,
                    formatted_value=f"{sc}/100",
                    unit="pts",
                    status="warning" if sc < 60 else "success"
                ),
                "net_worth": DashboardMetric(
                    id="net_worth",
                    label="Patrimonio Neto",
                    value=nw,
                    formatted_value=f"${nw:,.0f}",
                    unit="$",
                    status="neutral"
                ),
                "monthly_income": DashboardMetric(
                    id="monthly_income",
                    label="Ingresos Mensuales",
                    value=inc,
                    formatted_value=f"${inc:,.0f}/mes",
                    unit="$",
                    status="neutral"
                ),
                "monthly_expenses": DashboardMetric(
                    id="monthly_expenses",
                    label="Gastos Mensuales",
                    value=exp,
                    formatted_value=f"${exp:,.0f}/mes",
                    unit="$",
                    status="neutral"
                ),
                "monthly_cashflow": DashboardMetric(
                    id="monthly_cashflow",
                    label="Flujo de Caja Libre",
                    value=cf,
                    formatted_value=f"${cf:,.0f}/mes",
                    unit="$",
                    status="success" if cf > 0 else "danger"
                )
            }
        )
        return self.dashboard

    def update_dashboard_metric(self, key: str, value: float, reason: str = "") -> bool:
        db = self._ensure_dashboard()
        norm_key = self._normalize_metric_key(key)
        val_float = float(value)

        # 1. Actualizar campo nativo en DashboardState
        if hasattr(db, norm_key):
            setattr(db, norm_key, val_float)

        # 2. Recalcular flujo libre mensual si vario ingreso o gasto
        if norm_key in ("monthly_income", "monthly_expenses"):
            db.monthly_free_cashflow = round(db.monthly_income - db.monthly_expenses, 2)
            if "monthly_cashflow" in db.metrics:
                m_cf = db.metrics["monthly_cashflow"]
                m_cf.value = db.monthly_free_cashflow
                m_cf.formatted_value = f"${db.monthly_free_cashflow:,.0f}/mes"
                m_cf.status = "success" if db.monthly_free_cashflow > 0 else "danger"

        # 3. Actualizar tarjeta de metrica correspondiente
        metric_id = "monthly_cashflow" if norm_key == "monthly_free_cashflow" else norm_key
        if metric_id in db.metrics:
            m = db.metrics[metric_id]
            m.previous_value = m.value
            m.value = val_float
            unit_suffix = "/mes" if "monthly" in metric_id else ""
            m.formatted_value = f"${val_float:,.0f}{unit_suffix}" if m.unit == "$" else f"{val_float} {m.unit}"
            m.note = reason
        elif key in db.metrics:
            m = db.metrics[key]
            m.previous_value = m.value
            m.value = val_float
            m.formatted_value = f"${val_float:,.0f}" if m.unit == "$" else f"{val_float} {m.unit}"
            m.note = reason
        else:
            db.metrics[norm_key] = DashboardMetric(
                id=norm_key,
                label=key.replace("_", " ").capitalize(),
                value=val_float,
                formatted_value=f"${val_float:,.0f}",
                unit="$",
                note=reason
            )

        db.last_updated = datetime.now(timezone.utc).isoformat()
        return True

class SessionStore:
    # Almacen en memoria indexado por identificador de sesion y caso
    def __init__(self):
        self._sessions: dict[str, SessionData] = {}

    def get_or_create(self, session_id: str, case_id: str) -> SessionData:
        key = f"{session_id}:{case_id}"
        if key not in self._sessions:
            new_session = SessionData(case_id=case_id)
            # Si existe una sesion default previa para este caso con datos del plan, heredar el contexto
            default_session = self._sessions.get(f"default:{case_id}")
            if default_session and session_id != "default":
                new_session.master_plan = default_session.master_plan
                new_session.tasks = list(default_session.tasks)
                new_session.dashboard = default_session.dashboard
                new_session.summary_executive = default_session.summary_executive
                new_session.persona_highlights = default_session.persona_highlights
            self._sessions[key] = new_session
        return self._sessions[key]

    def get(self, session_id: str, case_id: str) -> Optional[SessionData]:
        return self._sessions.get(f"{session_id}:{case_id}")

    def save(self, session_id: str, case_id: str, data: SessionData) -> None:
        self._sessions[f"{session_id}:{case_id}"] = data

session_store = SessionStore()

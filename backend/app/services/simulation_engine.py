"""Motor de simulacion financiera para escenarios interactivos What-If.
Calcula proyecciones temporales de patrimonio, deuda, liquidez y score
de salud financiera sin dependencias circulares y de forma modular.
"""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ScenarioParams(BaseModel):
    # Parametros de simulacion configurables
    monthly_income_delta: float = Field(0.0, description="Variacion mensual de ingresos netos")
    monthly_expense_delta: float = Field(0.0, description="Variacion mensual de gastos de vida")
    emergency_expense: float = Field(0.0, description="Gasto puntual extraordinario inmediato")
    one_off_bonus: float = Field(0.0, description="Ingreso puntual extraordinario (bonus)")
    debt_extra_payment: float = Field(0.0, description="Amortizacion extra mensual a deuda")
    lump_sum_debt_payment: float = Field(0.0, description="Pago unico extraordinario a deuda")
    investment_annual_return: float = Field(0.07, description="Rendimiento anual estimado de cartera (0.07 = 7%)")
    house_downpayment: float = Field(0.0, description="Desembolso para entrada de vivienda")
    house_purchase_month: Optional[str] = Field(None, description="Mes previsto de compra YYYY-MM")
    horizon_months: int = Field(24, description="Numero de meses a proyectar (12 a 60)")


class MonthlyProjectionPoint(BaseModel):
    month: str
    income: float
    expenses: float
    free_cashflow: float
    total_debt: float
    net_worth: float
    emergency_months: float
    liquid_savings: float


class SimulationResult(BaseModel):
    case_id: str
    scenario_name: str
    initial_score: int
    projected_score: int
    score_delta: int
    debt_freedom_date: Optional[str]
    net_worth_12m: float
    net_worth_delta_12m: float
    timeline: list[MonthlyProjectionPoint]
    milestones: list[str]
    verdict: str


def calculate_dynamic_health_score(
    emergency_months: float,
    debt_to_income: float,
    savings_rate: float,
    protection_score: int = 60
) -> int:
    """Calcula un score de salud financiera normalizado (0-100)
    basado en los cuatro pilares fundamentales de Sherpas:
    1. Liquidez (30 pts): 3 a 6 meses de gastos cubiertos.
    2. Endeudamiento (30 pts): ratio de cuota/ingresos y volumen de pasivo.
    3. Tasa de ahorro (25 pts): ahorro libre / ingresos netos (meta >= 20%).
    4. Proteccion y diversificacion (15 pts).
    """
    # 1. Pilar Liquidez (max 30 pts)
    if emergency_months >= 6.0:
        liq_pts = 30.0
    elif emergency_months >= 3.0:
        liq_pts = 20.0 + ((emergency_months - 3.0) / 3.0) * 10.0
    elif emergency_months >= 1.0:
        liq_pts = 10.0 + ((emergency_months - 1.0) / 2.0) * 10.0
    else:
        liq_pts = max(0.0, emergency_months * 10.0)

    # 2. Pilar Endeudamiento (max 30 pts)
    # debt_to_income es la proporcion de ingresos consumida por deudas
    if debt_to_income <= 0.05:
        debt_pts = 30.0
    elif debt_to_income <= 0.20:
        debt_pts = 25.0 - ((debt_to_income - 0.05) / 0.15) * 10.0
    elif debt_to_income <= 0.40:
        debt_pts = 15.0 - ((debt_to_income - 0.20) / 0.20) * 10.0
    else:
        debt_pts = max(0.0, 5.0 - (debt_to_income - 0.40) * 10.0)

    # 3. Pilar Capacidad de Ahorro (max 25 pts)
    if savings_rate >= 0.25:
        sav_pts = 25.0
    elif savings_rate >= 0.15:
        sav_pts = 18.0 + ((savings_rate - 0.15) / 0.10) * 7.0
    elif savings_rate >= 0.05:
        sav_pts = 8.0 + ((savings_rate - 0.05) / 0.10) * 10.0
    elif savings_rate > 0.0:
        sav_pts = savings_rate * 160.0
    else:
        sav_pts = 0.0

    # 4. Pilar Proteccion (max 15 pts)
    prot_pts = min(15.0, max(0.0, protection_score * 0.15))

    total = int(round(liq_pts + debt_pts + sav_pts + prot_pts))
    return max(1, min(100, total))


def run_scenario_simulation(
    case_id: str,
    base_income: float,
    base_expenses: float,
    base_debt: float,
    base_net_worth: float,
    base_score: int,
    params: ScenarioParams,
    scenario_name: str = "Simulacion personalizada",
    start_year_month: Optional[str] = None
) -> SimulationResult:
    """Ejecuta una simulacion matematica mes a mes para el horizonte definido."""
    if not start_year_month:
        start_year_month = datetime.now().strftime("%Y-%m")

    y, m = [int(x) for x in start_year_month.split("-")]

    curr_income = base_income + params.monthly_income_delta
    curr_expenses = base_expenses + params.monthly_expense_delta
    curr_debt = max(0.0, base_debt - params.lump_sum_debt_payment)
    curr_nw = base_net_worth
    liquid_reserves = max(curr_nw * 0.15, 5000.0)

    # Aplicar shock inmediato o bonus en mes 1
    if params.emergency_expense > 0:
        liquid_reserves = max(0.0, liquid_reserves - params.emergency_expense)
        curr_nw = max(0.0, curr_nw - params.emergency_expense)

    if params.one_off_bonus > 0:
        liquid_reserves += params.one_off_bonus
        curr_nw += params.one_off_bonus

    monthly_roi = (1.0 + params.investment_annual_return) ** (1.0 / 12.0) - 1.0
    timeline: list[MonthlyProjectionPoint] = []
    debt_freedom_date: Optional[str] = None
    milestones: list[str] = []

    # Proyeccion mes a mes
    for step in range(params.horizon_months):
        step_m = (m - 1 + step) % 12 + 1
        step_y = y + (m - 1 + step) // 12
        date_str = f"{step_y:04d}-{step_m:02d}"

        # Compra de vivienda si coincide el mes
        if params.house_downpayment > 0 and params.house_purchase_month == date_str:
            liquid_reserves = max(0.0, liquid_reserves - params.house_downpayment)
            milestones.append(f"Mes {date_str}: Desembolso de ${params.house_downpayment:,.0f} para entrada de vivienda.")

        # Amortizacion de deuda
        debt_payment = min(curr_debt, (curr_income * 0.08) + params.debt_extra_payment)
        curr_debt = max(0.0, curr_debt - debt_payment)
        if curr_debt == 0.0 and debt_freedom_date is None and base_debt > 0:
            debt_freedom_date = date_str
            milestones.append(f"Mes {date_str}: ¡Deuda viva amortizada por completo (0 $)! Liberacion total del flujo de caja.")

        # Flujo libre y acumulacion de patrimonio
        free_cf = curr_income - (curr_expenses + debt_payment)
        investable_flow = max(0.0, free_cf * 0.70)
        cash_flow = max(0.0, free_cf * 0.30) if free_cf > 0 else free_cf

        liquid_reserves = max(0.0, liquid_reserves + cash_flow)
        investable_growth = (curr_nw - curr_debt) * monthly_roi
        curr_nw = round(curr_nw + free_cf + investable_growth, 2)

        emerg_months = round(liquid_reserves / max(1.0, curr_expenses), 1)

        timeline.append(MonthlyProjectionPoint(
            month=date_str,
            income=round(curr_income, 2),
            expenses=round(curr_expenses, 2),
            free_cashflow=round(free_cf, 2),
            total_debt=round(curr_debt, 2),
            net_worth=round(curr_nw, 2),
            emergency_months=emerg_months,
            liquid_savings=round(liquid_reserves, 2)
        ))

    # Metricas clave en mes 12
    pt_12m = timeline[min(11, len(timeline) - 1)]
    net_worth_12m = pt_12m.net_worth
    net_worth_delta_12m = net_worth_12m - base_net_worth

    # Score proyectado
    debt_ratio = pt_12m.total_debt / max(1.0, pt_12m.income * 12)
    savings_ratio = max(0.0, pt_12m.free_cashflow / max(1.0, pt_12m.income))
    projected_score = calculate_dynamic_health_score(
        emergency_months=pt_12m.emergency_months,
        debt_to_income=debt_ratio,
        savings_rate=savings_ratio,
        protection_score=base_score
    )
    score_delta = projected_score - base_score

    # Veredicto y comprensibilidad
    verdict_lines = []
    if score_delta > 0:
        verdict_lines.append(f"El plan simulado eleva la salud financiera en +{score_delta} puntos (de {base_score} a {projected_score}/100).")
    elif score_delta == 0:
        verdict_lines.append(f"La salud financiera se mantiene estable en {projected_score}/100.")
    else:
        verdict_lines.append(f"El escenario absorbe la tension con un descenso controlado de {score_delta} puntos ({projected_score}/100).")

    if debt_freedom_date:
        verdict_lines.append(f"Se alcanza la total liberacion de deudas en {debt_freedom_date}.")
    if pt_12m.emergency_months >= 3.0:
        verdict_lines.append(f"El colchon de seguridad permanece blindado cubriendo {pt_12m.emergency_months} meses de gastos.")
    else:
        verdict_lines.append(f"Atencion: La liquidez inmediata cubre {pt_12m.emergency_months} meses; se aconseja priorizar fondo de reserva.")

    return SimulationResult(
        case_id=case_id,
        scenario_name=scenario_name,
        initial_score=base_score,
        projected_score=projected_score,
        score_delta=score_delta,
        debt_freedom_date=debt_freedom_date,
        net_worth_12m=net_worth_12m,
        net_worth_delta_12m=round(net_worth_delta_12m, 2),
        timeline=timeline,
        milestones=milestones,
        verdict=" ".join(verdict_lines)
    )


def get_case_preset_scenarios(case_id: str) -> list[dict[str, Any]]:
    """Devuelve presets de escenarios realistas orientados a cada caso."""
    if case_id == "michael-carter":
        return [
            {
                "id": "compra_casa_2027",
                "title": "🏠 Compra de casa en 2027 ($113k entrada)",
                "description": "Evalua el impacto de desembolsar la entrada para la vivienda de $550k en junio de 2027.",
                "params": ScenarioParams(
                    house_downpayment=113300.0,
                    house_purchase_month="2027-06",
                    debt_extra_payment=300.0,
                    horizon_months=36
                )
            },
            {
                "id": "amortizacion_agresiva",
                "title": "💳 Amortizacion relampago Amex (-$3,500)",
                "description": "Destina flujo libre para liquidar de inmediato la deuda al 24.9% TAE.",
                "params": ScenarioParams(
                    lump_sum_debt_payment=3500.0,
                    monthly_expense_delta=-200.0,
                    horizon_months=24
                )
            },
            {
                "id": "shock_imprevisto",
                "title": "🚨 Imprevisto mecanico/medico (-$2,000)",
                "description": "Simula una averia urgente y comprueba la resiliencia del plan de ahorro.",
                "params": ScenarioParams(
                    emergency_expense=2000.0,
                    horizon_months=18
                )
            },
            {
                "id": "ascenso_salarial",
                "title": "🚀 Promocion laboral (+10% ingresos)",
                "description": "Impacto de un aumento neto de $1,500/mes destinado al colchon y ahorro.",
                "params": ScenarioParams(
                    monthly_income_delta=1500.0,
                    horizon_months=24
                )
            }
        ]
    elif case_id == "timothy-melanie-weah":
        return [
            {
                "id": "liquidar_tarjeta_18",
                "title": "💳 Liquidar tarjeta 18% con efectivo ($18,000)",
                "description": "Usar parte de los $150k en cuenta para terminar con el drenaje de intereses.",
                "params": ScenarioParams(
                    lump_sum_debt_payment=18000.0,
                    monthly_expense_delta=-350.0,
                    horizon_months=24
                )
            },
            {
                "id": "fondo_universidad_ninos",
                "title": "🎓 Fondo 529 para Liam y Josh (+$800/mes)",
                "description": "Canalizar ahorro hacia planes universitarios con ventaja fiscal.",
                "params": ScenarioParams(
                    monthly_expense_delta=800.0,
                    horizon_months=36
                )
            },
            {
                "id": "inversion_excedente",
                "title": "📈 Poner a trabajar el exceso de efectivo ($50,000)",
                "description": "Traspasar $50k de efectivo estancado a cartera diversificada 80/20.",
                "params": ScenarioParams(
                    one_off_bonus=0.0,
                    investment_annual_return=0.08,
                    horizon_months=36
                )
            }
        ]
    elif case_id == "daniel-emily-johnson":
        return [
            {
                "id": "blindaje_familiar",
                "title": "🛡️ Blindaje seguro de vida $1.6M + Umbrella",
                "description": "Aumentar prima mensual en $180 para asegurar el futuro de los menores.",
                "params": ScenarioParams(
                    monthly_expense_delta=180.0,
                    horizon_months=24
                )
            },
            {
                "id": "amortizar_tarjeta_24",
                "title": "💳 Amortizar tarjeta al 24.9% TAE ($18,000)",
                "description": "Erradicar los intereses toxicos que asfixian el ahorro mensual.",
                "params": ScenarioParams(
                    lump_sum_debt_payment=8000.0,
                    debt_extra_payment=500.0,
                    horizon_months=24
                )
            },
            {
                "id": "ahorro_universitario",
                "title": "🎓 Plan 529 Oliver y Sophia ($1,000/mes)",
                "description": "Proyectar la meta universitaria reduciendo gastos prescindibles.",
                "params": ScenarioParams(
                    monthly_expense_delta=500.0,
                    horizon_months=36
                )
            }
        ]
    else:  # Samantha Lewis
        return [
            {
                "id": "compra_vivienda_2030",
                "title": "🏡 Compra de vivienda en 2030 ($180k entrada)",
                "description": "Planificar la adquisicion patrimonial sin descapitalizar la jubilacion.",
                "params": ScenarioParams(
                    house_downpayment=180000.0,
                    house_purchase_month="2030-01",
                    horizon_months=48
                )
            },
            {
                "id": "optimizacion_fiscal",
                "title": "🏛️ Maximizacion HSA + Backdoor Roth IRA",
                "description": "Reducir carga tributaria canalizando $8,500 anuales a vehiculos protegidos.",
                "params": ScenarioParams(
                    monthly_income_delta=350.0,
                    horizon_months=24
                )
            },
            {
                "id": "acelerador_universidad",
                "title": "🎓 Facturas universitarias inminentes",
                "description": "Simula el desembolso de $25,000/ano en matriculas universitarias.",
                "params": ScenarioParams(
                    monthly_expense_delta=2080.0,
                    horizon_months=36
                )
            }
        ]

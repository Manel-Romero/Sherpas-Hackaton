import { KanbanState, TableState, TableSummary, PersonaInsights } from '../types';

export const FALLBACK_INSIGHTS: Record<string, PersonaInsights> = {
  'michael-carter': {
    case_id: 'michael-carter',
    title: 'Michael Carter',
    city: 'Austin',
    wealth_tier: 'D0: HENRY (High Earner, Not Rich Yet)',
    risk_profile: 'D4: Asimétrico (tolerancia alta en cripto/startups, aversión en deuda cara)',
    decision_style: 'D5: Analítico reactivo (busca validación técnica antes de ejecutar)',
    primary_tension: 'Dilema de compra de casa de 350k en 2027 vs horizonte de retiro a los 58 años sin precipicio de liquidez.',
    emotional_archetype: 'Pragmático ambicioso con sobrecarga decisional',
    key_alerts: [
      'Tarjeta Amex al 20% TAE con saldo $3,500 en rotativo.',
      'Brecha de seguro de vida: Cobertura insuficiente para compromisos hipotecarios previstos.',
      'Horizonte de retiro en 2047: Requiere acelerar aportes a 401(k) / IRA antes de 2028.'
    ]
  },
  'timothy-melanie-weah': {
    case_id: 'timothy-melanie-weah',
    title: 'Timothy & Melanie Weah',
    city: 'San Francisco',
    wealth_tier: 'D0: Mass Affluent ($280k ingreso conjunto)',
    risk_profile: 'D4: Conservador en liquidez, pasivo en optimización de pasivos',
    decision_style: 'D5: Consensual cauteloso',
    primary_tension: 'Acumulación defensiva de efectivo en cuenta corriente (0.01% TAE) conviviendo con deuda de consumo cara.',
    emotional_archetype: 'Defensivo familiar con aversión a la pérdida',
    key_alerts: [
      '$150,000 inmovilizados perdiendo poder adquisitivo frente a la inflación.',
      '$18,000 en tarjetas de crédito devengando ~$270/mes en intereses evitables.',
      'Fondos universitarios 529 de Liam y Josh sin aportes automatizados.'
    ]
  },
  'daniel-emily-johnson': {
    case_id: 'daniel-emily-johnson',
    title: 'Daniel & Emily Johnson',
    city: 'Denver',
    wealth_tier: 'D0: Middle-Class Solvente ($165k ingreso)',
    risk_profile: 'D4: Moderado defensivo',
    decision_style: 'D5: Familiar pragmático',
    primary_tension: 'Falsa sensación de seguridad por ahorro constante mientras existe una brecha crítica de seguro de vida.',
    emotional_archetype: 'Protector familiar responsable',
    key_alerts: [
      'Brecha de cobertura de seguro de vida de $1,350,000.',
      'Falta de testamento y designación cruzada de poderes de tutela.',
      'Fondo de emergencia en 2.8 meses (recomendado: 6 meses por carga familiar).'
    ]
  },
  'samantha-lewis': {
    case_id: 'samantha-lewis',
    title: 'Samantha Lewis',
    city: 'Miami',
    wealth_tier: 'D0: High Net Worth ($1.8M patrimonio)',
    risk_profile: 'D4: Crecimiento balanceado con sesgo inmobiliario',
    decision_style: 'D5: Independiente delegadora',
    primary_tension: 'Alta salud aparente hoy pero tasa de retiro de fondos superior a la rentabilidad neta real post-inflación.',
    emotional_archetype: 'Autónoma sofisticada con sesgo patrimonial físico',
    key_alerts: [
      'Riesgo de longevidad: Descenso brusco de capital a partir de los 72 años.',
      'Concentración patrimonial del 58% en activos inmobiliarios ilíquidos.',
      'Ausencia de fideicomiso revocable para estructuración sucesoria de Ethan y Ava.'
    ]
  }
};

export const FALLBACK_KANBAN: Record<string, KanbanState> = {
  'michael-carter': {
    case_id: 'michael-carter',
    version: Date.now(),
    statuses: { todo: 'To do', in_process: 'In process', done: 'Done' },
    cards: [
      {
        id: 'mc-1',
        title: 'Congela la tarjeta Amex Platinum',
        short_description: 'Es tu deuda más cara al 20% TAE y la fuga prioritaria a frenar hoy.',
        detailed_description: 'No necesitas pagar los $3,500 de golpe ahora: lo primordial es eliminarla de Apple Pay y congelar el plástico para evitar nuevos cargos.',
        category: 'immediate',
        impact: '-$3,500 deuda al 20% deja de crecer; +$700 ahorro anual en intereses',
        week: 1,
        steps: [
          'Abre la app de Amex y desvincula la tarjeta de Apple Pay / Google Wallet.',
          'Configura pago automático mínimo de $200/mes para proteger score crediticio.',
          'Guarda el plástico fuera de la cartera habitual.'
        ],
        status: 'in_process',
        content: 'Detener la fuga financiera más cara de forma inmediata.'
      },
      {
        id: 'mc-2',
        title: 'Reasignar excedente de $500/mes a amortización acelerada',
        short_description: 'Liquidar el balance total en 6 meses usando ahorro libre mensual.',
        detailed_description: 'Dirige $500 del excedente mensual de nómina directamente al saldo pendiente de la tarjeta de crédito.',
        category: 'debt',
        impact: 'Deuda liquidada al 100% en mes 6; liberas $200/mes de flujo',
        week: 2,
        steps: ['Configurar transferencia programada mensual de $500 el día siguiente al cobro de nómina.'],
        status: 'todo',
        content: 'Acelerar desendeudamiento.'
      },
      {
        id: 'mc-3',
        title: 'Calibrar fondo para entrada de vivienda 2027',
        short_description: 'Separar ahorro para compra en cuenta de alta rentabilidad (HYSA 4.5%).',
        detailed_description: 'Crear subcuenta dedicada exclusivamente a los $70,000 requeridos para el 20% de entrada de la vivienda en Austin.',
        category: 'savings',
        impact: '+$3,150/año en rendimientos seguros y aislamiento de capital',
        week: 3,
        steps: ['Apertura de subcuenta HYSA al 4.5% TAE etiquetada "Casa Austin 2027".'],
        status: 'todo',
        content: 'Planificación de compra inmobiliaria.'
      },
      {
        id: 'mc-4',
        title: 'Cotizar ampliación de póliza de vida a término ($750k)',
        short_description: 'Cubrir futuros pasivos hipotecarios y proteger patrimonio.',
        detailed_description: 'Establecer póliza de seguro de vida a 20 años para respaldar la compra inmobiliaria proyectada.',
        category: 'insurance',
        impact: 'Brecha de cobertura reducida a $0 por solo $42/mes',
        week: 4,
        steps: ['Comparar tres cotizaciones de seguro a término 20 años con cobertura $750k.'],
        status: 'done',
        content: 'Blindaje patrimonial.'
      }
    ]
  }
};

export const FALLBACK_TABLE: Record<string, TableState> = {
  'michael-carter': {
    case_id: 'michael-carter',
    version: Date.now(),
    columns: ['Ingresos', 'Gastos_Fijos', 'Ahorro_Libre', 'Deuda_Pendiente', 'Patrimonio'],
    rows: [
      { date: '2026-09', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 28500, Patrimonio: 218500 },
      { date: '2026-10', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 28000, Patrimonio: 224194 },
      { date: '2026-11', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 27500, Patrimonio: 229888 },
      { date: '2026-12', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 27000, Patrimonio: 235582 },
      { date: '2027-01', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 26500, Patrimonio: 241276 },
      { date: '2027-02', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 26000, Patrimonio: 246970 },
      { date: '2027-03', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 25500, Patrimonio: 252664 },
      { date: '2027-04', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 25000, Patrimonio: 258358 },
      { date: '2027-05', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 24500, Patrimonio: 264052 },
      { date: '2027-06', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 24000, Patrimonio: 269746 },
      { date: '2027-07', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 23500, Patrimonio: 275440 },
      { date: '2027-08', Ingresos: 15000, Gastos_Fijos: 9306, Ahorro_Libre: 5694, Deuda_Pendiente: 23000, Patrimonio: 281134 }
    ]
  }
};

export const FALLBACK_SUMMARY: Record<string, TableSummary> = {
  'michael-carter': {
    active_month: '2026-09',
    net_worth: 218500,
    monthly_income: 15000,
    monthly_expenses: 9306,
    free_cash_flow: 5694,
    debt_balance: 28500
  }
};

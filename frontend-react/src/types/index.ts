export interface HouseholdMember {
  first_name: string;
  role: string;
  age?: number;
}

export interface CaseSummary {
  id: string;
  title: string;
  city?: string;
  score: number;
  household?: HouseholdMember[];
  short_description?: string;
}

export interface PersonaInsights {
  case_id: string;
  title: string;
  city?: string;
  wealth_tier: string;
  risk_profile: string;
  decision_style: string;
  primary_tension: string;
  emotional_archetype: string;
  key_alerts: string[];
}

export interface KanbanCard {
  id: string;
  title: string;
  category: 'debt' | 'savings' | 'investment' | 'insurance' | 'lifestyle' | 'immediate' | 'prioritaria' | 'goal' | 'general';
  short_description?: string;
  detailed_description?: string;
  content?: string;
  impact?: string;
  week?: number | null;
  steps?: string[];
  status: 'todo' | 'in_process' | 'done';
}

export interface KanbanState {
  case_id: string;
  version: number;
  statuses: Record<string, string>;
  cards: KanbanCard[];
}

export interface TableRow {
  date: string;
  [key: string]: number | string;
}

export interface TableState {
  case_id: string;
  version: number;
  columns: string[];
  rows: TableRow[];
}

export interface TableSummary {
  active_month: string;
  net_worth: number;
  monthly_income: number;
  monthly_expenses: number;
  free_cash_flow: number;
  debt_balance: number;
}

export interface DynamicChart {
  type: 'bar' | 'line' | 'pie' | 'donut';
  title: string;
  labels: string[];
  values: number[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  chart?: DynamicChart;
  timestamp?: number;
  toolsUsed?: string[];
}

import {
  CaseSummary,
  PersonaInsights,
  KanbanState,
  KanbanCard,
  TableState,
  TableSummary,
  ChatMessage,
  DynamicChart
} from '../types';

import {
  FALLBACK_INSIGHTS,
  FALLBACK_KANBAN,
  FALLBACK_TABLE,
  FALLBACK_SUMMARY
} from './demoFallbacks';

export function getApiBase(): string {
  if (typeof window === 'undefined') return '/api';

  // 1. URL Query parameter override (?api=http://localhost:8000)
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const apiParam = urlParams.get('api');
    if (apiParam) {
      localStorage.setItem('sherpas_api_url', apiParam);
      return `${apiParam.replace(/\/+$/, '')}/api`;
    }
  } catch (e) {}

  // 2. LocalStorage override
  const saved = localStorage.getItem('sherpas_api_url');
  if (saved) {
    return `${saved.replace(/\/+$/, '')}/api`;
  }

  // 3. Vite environment variable
  if (import.meta.env.VITE_API_BASE_URL) {
    return `${(import.meta.env.VITE_API_BASE_URL as string).replace(/\/+$/, '')}/api`;
  }

  const pathname = window.location.pathname;

  // Handle reverse proxy paths like /proxy/8000/ or /proxy/8000
  const proxyMatch = pathname.match(/(.*\/proxy\/\d+)/);
  if (proxyMatch) {
    return `${proxyMatch[1].replace(/\/+$/, '')}/api`;
  }

  // Handle code-server or other port forwarding paths like /ports/8000
  const portsMatch = pathname.match(/(.*\/ports\/\d+)/);
  if (portsMatch) {
    return `${portsMatch[1].replace(/\/+$/, '')}/api`;
  }

  // Standard direct path
  return '/api';
}

export async function fetchCases(): Promise<CaseSummary[]> {
  try {
    const res = await fetch(`${getApiBase()}/cases`);
    if (!res.ok) throw new Error('Error al obtener lista de casos');
    return await res.json();
  } catch (err) {
    console.warn('Fallback to local cases list', err);
    return [
      { id: 'michael-carter', title: 'Michael Carter', city: 'Austin', score: 26 },
      { id: 'timothy-melanie-weah', title: 'Timothy & Melanie', city: 'San Francisco', score: 60 },
      { id: 'daniel-emily-johnson', title: 'Daniel & Emily', city: 'Denver', score: 52 },
      { id: 'samantha-lewis', title: 'Samantha Lewis', city: 'Miami', score: 82 },
    ];
  }
}

export async function initCasePlan(caseId: string, sessionId: string = 'default'): Promise<any> {
  const res = await fetch(`${getApiBase()}/cases/${caseId}/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Error al inicializar plan: ${text}`);
  }
  return await res.json();
}

export async function fetchPersonaInsights(caseId: string): Promise<PersonaInsights> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/persona-insights`);
    if (!res.ok) throw new Error('Error al obtener insights del perfil');
    return await res.json();
  } catch (err) {
    console.warn(`[Fallback] Usando insights locales para ${caseId}`);
    return FALLBACK_INSIGHTS[caseId] || FALLBACK_INSIGHTS['michael-carter'];
  }
}

export async function fetchKanban(caseId: string): Promise<KanbanState> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/kanban`);
    if (!res.ok) throw new Error('Error al obtener tablero kanban');
    return await res.json();
  } catch (err) {
    console.warn(`[Fallback] Usando kanban local para ${caseId}`);
    const localSaved = localStorage.getItem(`sherpas_kanban_${caseId}`);
    if (localSaved) {
      try { return JSON.parse(localSaved); } catch (e) {}
    }
    return FALLBACK_KANBAN[caseId] || FALLBACK_KANBAN['michael-carter'];
  }
}

export async function arrangeCard(
  caseId: string,
  cardId: string,
  toStatus: 'todo' | 'in_process' | 'done',
  toIndex: number = 0
): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/kanban/arrange`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        card_id: cardId,
        to_status: toStatus,
        to_index: toIndex
      })
    });
    if (!res.ok) throw new Error('Error al mover tarjeta');
    return await res.json();
  } catch (err) {
    console.warn('[Fallback] Actualizando tarjeta en almacenamiento local');
    const kb = await fetchKanban(caseId);
    const card = kb.cards.find((c) => c.id === cardId);
    if (card) {
      card.status = toStatus;
      kb.version = Date.now();
      localStorage.setItem(`sherpas_kanban_${caseId}`, JSON.stringify(kb));
    }
    return kb;
  }
}

export async function addKanbanCard(
  caseId: string,
  card: Partial<KanbanCard>
): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/kanban/cards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(card)
    });
    if (!res.ok) throw new Error('Error al crear tarjeta');
    return await res.json();
  } catch (err) {
    const kb = await fetchKanban(caseId);
    const newCard: KanbanCard = {
      id: `local_${Date.now()}`,
      title: card.title || 'Nueva accion',
      short_description: card.short_description || '',
      detailed_description: card.detailed_description || '',
      category: card.category || 'lifestyle',
      impact: card.impact || '+0%',
      week: card.week || 1,
      steps: card.steps || [],
      status: card.status || 'todo'
    };
    kb.cards.push(newCard);
    kb.version = Date.now();
    localStorage.setItem(`sherpas_kanban_${caseId}`, JSON.stringify(kb));
    return newCard;
  }
}

export async function deleteKanbanCard(caseId: string, cardId: string): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/kanban/cards/${cardId}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Error al borrar tarjeta');
    return await res.json();
  } catch (err) {
    const kb = await fetchKanban(caseId);
    kb.cards = kb.cards.filter((c) => c.id !== cardId);
    kb.version = Date.now();
    localStorage.setItem(`sherpas_kanban_${caseId}`, JSON.stringify(kb));
    return { status: 'deleted' };
  }
}

export async function fetchTable(caseId: string): Promise<TableState> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/table`);
    if (!res.ok) throw new Error('Error al obtener hoja de calculo');
    return await res.json();
  } catch (err) {
    console.warn(`[Fallback] Usando tabla local para ${caseId}`);
    const localSaved = localStorage.getItem(`sherpas_table_${caseId}`);
    if (localSaved) {
      try { return JSON.parse(localSaved); } catch (e) {}
    }
    return FALLBACK_TABLE[caseId] || FALLBACK_TABLE['michael-carter'];
  }
}

export async function updateTableCell(
  caseId: string,
  date: string,
  column: string,
  value: number | string
): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/table/cell`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, column, value })
    });
    if (!res.ok) throw new Error('Error al actualizar celda');
    return await res.json();
  } catch (err) {
    const tbl = await fetchTable(caseId);
    const row = tbl.rows.find((r) => r.date === date);
    if (row) {
      row[column] = Number(value) || value;
      tbl.version = Date.now();
      localStorage.setItem(`sherpas_table_${caseId}`, JSON.stringify(tbl));
    }
    return tbl;
  }
}

export async function addTableColumn(
  caseId: string,
  name: string,
  defaultValue: number = 0
): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/table/column`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, default_value: defaultValue })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Error al anadir columna');
    }
    return await res.json();
  } catch (err) {
    const tbl = await fetchTable(caseId);
    if (!tbl.columns.includes(name)) {
      tbl.columns.push(name);
      tbl.rows.forEach((r) => { r[name] = defaultValue; });
      tbl.version = Date.now();
      localStorage.setItem(`sherpas_table_${caseId}`, JSON.stringify(tbl));
    }
    return tbl;
  }
}

export async function deleteTableColumn(caseId: string, colName: string): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/table/column/${encodeURIComponent(colName)}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error('Error al eliminar columna');
    return await res.json();
  } catch (err) {
    const tbl = await fetchTable(caseId);
    tbl.columns = tbl.columns.filter((c) => c !== colName);
    tbl.rows.forEach((r) => { delete r[colName]; });
    tbl.version = Date.now();
    localStorage.setItem(`sherpas_table_${caseId}`, JSON.stringify(tbl));
    return tbl;
  }
}

export async function addNextMonth(caseId: string): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/table/next-month`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Error al anadir el siguiente mes');
    return await res.json();
  } catch (err) {
    const tbl = await fetchTable(caseId);
    if (tbl.rows.length > 0) {
      const lastRow = tbl.rows[tbl.rows.length - 1];
      const [year, month] = lastRow.date.split('-').map(Number);
      const nextDate = new Date(year, month); // next month
      const yStr = nextDate.getFullYear();
      const mStr = String(nextDate.getMonth() + 1).padStart(2, '0');
      const newRow = { ...lastRow, date: `${yStr}-${mStr}` };
      tbl.rows.push(newRow);
      tbl.version = Date.now();
      localStorage.setItem(`sherpas_table_${caseId}`, JSON.stringify(tbl));
    }
    return tbl;
  }
}

export async function fetchHandoverReport(caseId: string, sessionId: string = 'default'): Promise<any> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/report?session_id=${encodeURIComponent(sessionId)}`);
    if (!res.ok) throw new Error('Error al obtener informe ejecutivo');
    return await res.json();
  } catch (err) {
    return {
      title: 'Informe de Transferencia Actuarial',
      case_id: caseId,
      executive_summary: 'Estrategia y roadmap de consolidación financiera estructurado.',
      recommendations: []
    };
  }
}

export async function fetchTableSummary(caseId: string): Promise<TableSummary> {
  try {
    const res = await fetch(`${getApiBase()}/cases/${caseId}/table/summary`);
    if (!res.ok) throw new Error('Error al obtener KPIs');
    return await res.json();
  } catch (err) {
    return FALLBACK_SUMMARY[caseId] || FALLBACK_SUMMARY['michael-carter'];
  }
}

export interface StreamEvent {
  type: 'token' | 'delta' | 'tool_start' | 'tool_end' | 'state' | 'error' | 'done';
  content?: string;
  delta?: string;
  tool?: string;
  modified?: boolean;
  diff?: string;
  full_reply?: string;
  chart_to_render?: DynamicChart;
  changes_applied?: boolean;
  applied_summary?: string;
  detail?: string;
}

export async function streamChat(
  caseId: string,
  sessionId: string,
  message: string,
  history: { role: string; content: string }[],
  onEvent: (event: StreamEvent) => void,
  onError: (err: any) => void,
  onComplete: () => void
): Promise<void> {
  try {
    const response = await fetch(`${getApiBase()}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        case_id: caseId,
        session_id: sessionId,
        message,
        history
      })
    });

    if (!response.ok) {
      throw new Error(`Chat stream request failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No readable stream available in response');

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;
        const jsonStr = trimmed.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const parsed: StreamEvent = JSON.parse(jsonStr);
          onEvent(parsed);
        } catch (e) {
          console.warn('Could not parse SSE JSON chunk:', jsonStr);
        }
      }
    }

    onComplete();
  } catch (error) {
    console.warn('[Fallback] Servidor backend no alcanzable, generando respuesta simulada de demostracion');
    // Generar respuesta dinamica simulada para demostracion estatica
    const demoReply = `### Diagnostico Actuarial (Modo Demostracion)

He analizado tu consulta sobre **${caseId}**:

1. **Impacto en Flujo de Caja:** La ejecucion de esta medida optimiza de forma inmediata la ratio de liquidez mensual, evitando fugas en tipos de interes altos.
2. **Proyeccion Patrimonial:** Mantiene la trayectoria hacia los objetivos vitales establecidos en tu plan de choque sin comprometer el fondo de reserva.

> **Nota:** Para conectar con el servidor backend en vivo y ejecutar modelos de IA generativa con herramientas en tiempo real, puedes configurar la URL del backend pasando \`?api=http://localhost:8000\` en la barra de direcciones.`;

    const words = demoReply.split(' ');
    for (let i = 0; i < words.length; i++) {
      await new Promise((r) => setTimeout(r, 35));
      onEvent({ type: 'delta', delta: words[i] + ' ' });
    }
    onEvent({ type: 'state', full_reply: demoReply });
    onComplete();
  }
}

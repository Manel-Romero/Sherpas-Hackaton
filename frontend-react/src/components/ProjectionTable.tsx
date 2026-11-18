import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import {
  TrendingUp,
  CreditCard,
  Wallet,
  Calendar,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  FileSpreadsheet
} from 'lucide-react';
import { TableState, TableSummary } from '../types';
import { audioService } from '../services/audioService';

interface ProjectionTableProps {
  table: TableState;
  summary: TableSummary | null;
  onUpdateCell: (date: string, column: string, value: number | string) => Promise<void>;
  onAddColumn: (name: string, defaultValue: number) => Promise<void>;
  onDeleteColumn: (colName: string) => Promise<void>;
  onAddNextMonth?: () => Promise<void>;
  onConsultColumn?: (colName: string) => void;
  isLoading?: boolean;
}

const COLUMN_PRESETS = [
  { name: 'Fondo_Emergencia', defaultVal: 500, label: '🛡️ Fondo Emergencia' },
  { name: 'Educacion_529', defaultVal: 400, label: '🎓 Educacion 529' },
  { name: 'Inversion_Indexada', defaultVal: 600, label: '📈 Inversion Indexada' },
  { name: 'Cuenta_HSA', defaultVal: 350, label: '🏛️ Cuenta HSA' },
  { name: 'Aportacion_401k', defaultVal: 750, label: '💼 Plan 401(k)' },
  { name: 'Ahorro_Vacaciones', defaultVal: 200, label: '🏖️ Vacaciones' },
];

export const ProjectionTable: React.FC<ProjectionTableProps> = ({
  table,
  summary,
  onUpdateCell,
  onAddColumn,
  onDeleteColumn,
  onAddNextMonth,
  onConsultColumn
}) => {
  const [editingCell, setEditingCell] = useState<{ date: string; column: string; val: string } | null>(null);
  const [isAddColModalOpen, setIsAddColModalOpen] = useState(false);
  const [isAddingMonth, setIsAddingMonth] = useState(false);
  const [newColName, setNewColName] = useState('');
  const [newColDefault, setNewColDefault] = useState<number>(0);

  // Series visibility toggles
  const [showNetWorth, setShowNetWorth] = useState(true);
  const [showDebt, setShowDebt] = useState(true);
  const [showSavings, setShowSavings] = useState(true);

  const rows = table?.rows || [];
  const columns = table?.columns || [];

  const handleCellSave = async () => {
    if (!editingCell) return;
    audioService.playSound('task_done');
    await onUpdateCell(editingCell.date, editingCell.column, editingCell.val);
    setEditingCell(null);
  };

  const handleAddColumnSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    audioService.playSound('task_done');
    await onAddColumn(newColName.trim(), Number(newColDefault) || 0);
    setNewColName('');
    setNewColDefault(0);
    setIsAddColModalOpen(false);
  };

  const chartData = rows.map((r) => ({
    date: r.date,
    Patrimonio: typeof r['Patrimonio'] === 'number' ? r['Patrimonio'] : parseFloat(r['Patrimonio'] as string) || 0,
    Deuda: typeof r['Deuda_Pendiente'] === 'number' ? r['Deuda_Pendiente'] : parseFloat(r['Deuda_Pendiente'] as string) || 0,
    Ahorro: typeof r['Ahorro_Libre'] === 'number' ? r['Ahorro_Libre'] : parseFloat(r['Ahorro_Libre'] as string) || 0,
  }));

  const formatCurrency = (val: number | string | undefined) => {
    if (val === undefined || val === null) return '-';
    const num = typeof val === 'number' ? val : parseFloat(val);
    if (isNaN(num)) return String(val);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(num);
  };

  return (
    <div className="space-y-5">
      {/* 4 Minimalist KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-2xl liquid-glass-card shadow-sm">
          <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5 font-display">
            <span className="w-1.5 h-1.5 rounded-full bg-[#7d7568] dark:bg-[#b0a89a]" />
            Mes Activo
          </div>
          <div className="text-2xl font-light text-slate-900 dark:text-white font-mono mt-0.5">{summary?.active_month || '2026-01'}</div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Punto de partida del modelo</p>
        </div>

        <div className="p-4 rounded-2xl liquid-glass-card shadow-sm">
          <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5 font-display">
            <span className="w-1.5 h-1.5 rounded-full bg-[#526e5e] dark:bg-[#8ba898]" />
            Patrimonio Neto
          </div>
          <div className="text-2xl font-light text-slate-900 dark:text-white font-mono num-tabular mt-0.5">
            {formatCurrency(summary?.net_worth)}
          </div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Activos netos consolidados</p>
        </div>

        <div className="p-4 rounded-2xl liquid-glass-card shadow-sm">
          <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5 font-display">
            <span className="w-1.5 h-1.5 rounded-full bg-[#526e5e] dark:bg-[#8ba898]" />
            Flujo Libre / Mes
          </div>
          <div className="text-2xl font-light text-[#526e5e] dark:text-[#8ba898] font-mono num-tabular mt-0.5">
            {formatCurrency(summary?.free_cash_flow)}
          </div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Capacidad mensual de maniobra</p>
        </div>

        <div className="p-4 rounded-2xl liquid-glass-card shadow-sm">
          <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5 font-display">
            <span className="w-1.5 h-1.5 rounded-full bg-[#875f52] dark:bg-[#b38a7c]" />
            Deuda Pendiente
          </div>
          <div className="text-2xl font-light text-[#875f52] dark:text-[#b38a7c] font-mono num-tabular mt-0.5">
            {formatCurrency(summary?.debt_balance)}
          </div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Pasivos en curso de extinción</p>
        </div>
      </div>

      {/* Projections Chart */}
      {chartData.length > 0 && (
        <div className="p-5 rounded-3xl liquid-glass shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2 font-display">
                <TrendingUp className="w-4 h-4 text-[#526e5e] dark:text-[#8ba898]" />
                <span>Curva Actuarial Proyectada a 12 Meses</span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Evolución patrimonial, acumulación de liquidez y desendeudamiento</p>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setShowNetWorth(!showNetWorth)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  showNetWorth ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white shadow-sm font-semibold' : 'text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#526e5e] dark:bg-[#8ba898]" />
                <span>Patrimonio</span>
              </button>
              <button
                onClick={() => setShowDebt(!showDebt)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  showDebt ? 'bg-[#875f52]/15 text-[#875f52] dark:text-[#b38a7c] shadow-sm font-semibold' : 'text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#875f52] dark:bg-[#b38a7c]" />
                <span>Deuda</span>
              </button>
              <button
                onClick={() => setShowSavings(!showSavings)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  showSavings ? 'bg-[#526e5e]/15 text-[#526e5e] dark:text-[#8ba898] shadow-sm font-semibold' : 'text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#526e5e] dark:bg-[#8ba898]" />
                <span>Ahorro Mensual</span>
              </button>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPatrimonio" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#526e5e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#526e5e" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-black/[0.04] dark:text-white/[0.05]" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis 
                  stroke="#64748b" 
                  tick={{ fontSize: 10 }} 
                  tickLine={false}
                  tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} 
                />
                <Tooltip
                  formatter={(value: any) => [formatCurrency(value), '']}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  wrapperStyle={{ paddingBottom: '12px' }}
                  formatter={(val) => <span className="text-slate-700 dark:text-slate-200 text-[11px] font-medium">{val}</span>}
                />
                {showSavings && (
                  <Bar dataKey="Ahorro" name="Ahorro Libre Mensual" fill="#6e8c7b" fillOpacity={0.5} radius={[4, 4, 0, 0]} />
                )}
                {showNetWorth && (
                  <Area
                    type="monotone"
                    dataKey="Patrimonio"
                    name="Patrimonio Neto"
                    stroke="#526e5e"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorPatrimonio)"
                  />
                )}
                {showDebt && (
                  <Line
                    type="monotone"
                    dataKey="Deuda"
                    name="Deuda Pendiente"
                    stroke="#875f52"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={{ r: 3, fill: '#875f52' }}
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Spreadsheet Table */}
      <div className="p-5 rounded-3xl liquid-glass shadow-sm overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-[#406a4b] dark:text-[#7fa988]" />
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white font-display">Matriz Financiera Mensual Reactiva</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Haz clic en cualquier celda para editar su valor o ingresar una fórmula actuarial</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onAddNextMonth && (
              <button
                onClick={async () => {
                  setIsAddingMonth(true);
                  try {
                    await onAddNextMonth();
                  } finally {
                    setIsAddingMonth(false);
                  }
                }}
                disabled={isAddingMonth}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] rounded-full shadow-sm transition-all cursor-pointer disabled:opacity-50"
                title="Extender la proyección al siguiente mes consecutivo"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>{isAddingMonth ? 'Proyectando...' : 'Proyectar Mes Siguiente'}</span>
              </button>
            )}
            <button
              onClick={() => setIsAddColModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.07] dark:hover:bg-white/[0.1] border border-black/10 dark:border-white/10 rounded-full transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
              <span>Añadir Columna</span>
            </button>
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-black/10 dark:border-white/10">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-black/[0.02] dark:bg-white/[0.03] border-b border-black/10 dark:border-white/10">
                <th className="px-3.5 py-3 font-semibold text-slate-700 dark:text-slate-300 sticky left-0 bg-white/90 dark:bg-[#121620]/90 backdrop-blur-md z-10 w-28 border-r border-black/10 dark:border-white/10 font-display">
                  Periodo
                </th>
                {columns.map((col) => (
                  <th key={col} className="px-3.5 py-3 font-semibold text-slate-800 dark:text-slate-100 min-w-[130px] group border-r border-black/[0.04] dark:border-white/[0.05] font-display">
                    <div className="flex items-center justify-between gap-1">
                      <span className="truncate">{col}</span>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {onConsultColumn && (
                          <button
                            onClick={() => onConsultColumn(col)}
                            title={`Consultar al Co-Pilot sobre ${col}`}
                            className="p-0.5 text-slate-400 hover:text-[#406a4b] dark:hover:text-[#7fa988] transition-colors cursor-pointer"
                          >
                            <TrendingUp className="w-3 h-3 text-[#406a4b] dark:text-[#7fa988]" />
                          </button>
                        )}
                        {col !== 'Patrimonio' && col !== 'Ingresos' && (
                          <button
                            onClick={() => onDeleteColumn(col)}
                            title={`Eliminar columna ${col}`}
                            className="p-0.5 text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04] dark:divide-white/[0.04] font-mono">
              {rows.map((row) => (
                <tr key={row.date} className="hover:bg-black/[0.015] dark:hover:bg-white/[0.02] transition-colors">
                  <td className="px-3.5 py-2.5 font-semibold text-slate-700 dark:text-slate-300 sticky left-0 bg-white/95 dark:bg-[#0c110d]/95 z-10 border-r border-black/[0.04] dark:border-white/[0.05]">
                    {row.date}
                  </td>
                  {columns.map((col) => {
                    const isEditing = editingCell?.date === row.date && editingCell?.column === col;
                    const val = row[col];

                    return (
                      <td
                        key={col}
                        onClick={() => {
                          if (!isEditing) {
                            setEditingCell({ date: row.date, column: col, val: String(val ?? '') });
                          }
                        }}
                        className="px-3.5 py-2.5 cursor-pointer hover:bg-[#5e8967]/10 transition-colors border-r border-black/[0.04] dark:border-white/[0.05] relative group text-right num-tabular"
                      >
                        {isEditing ? (
                          <div className="flex items-center gap-1 justify-end">
                            <input
                              autoFocus
                              type="text"
                              value={editingCell.val}
                              onChange={(e) => setEditingCell({ ...editingCell, val: e.target.value })}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleCellSave();
                                if (e.key === 'Escape') setEditingCell(null);
                              }}
                              className="w-full px-2 py-1 bg-white dark:bg-[#141b15] border border-[#5e8967] rounded text-xs text-slate-900 dark:text-white focus:outline-none font-mono text-right shadow-sm"
                            />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCellSave();
                              }}
                              className="p-1 text-[#2e9e5b] dark:text-[#5eb87a] hover:bg-[#5e8967]/20 rounded cursor-pointer"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingCell(null);
                              }}
                              className="p-1 text-slate-400 hover:bg-black/5 dark:hover:bg-white/10 rounded cursor-pointer"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            <span className={typeof val === 'number' && val < 0 ? 'text-[#c97342] dark:text-[#e07a5f]' : 'text-slate-800 dark:text-slate-200'}>
                              {formatCurrency(val)}
                            </span>
                            <Edit2 className="w-3 h-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity ml-1" />
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Column Modal (Centered via Headless UI layout pattern) */}
      <AnimatePresence>
        {isAddColModalOpen && (
          <div
            className="fixed inset-0 z-50 overflow-y-auto bg-black/50 dark:bg-black/75 backdrop-blur-md"
            onClick={() => setIsAddColModalOpen(false)}
          >
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.16, ease: 'easeOut' }}
                onClick={(e) => e.stopPropagation()}
                className="relative w-full max-w-sm transform overflow-hidden rounded-3xl liquid-glass-elevated p-6 text-left shadow-2xl transition-all"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white font-display">Añadir Nueva Columna</h3>
                  <button
                    onClick={() => setIsAddColModalOpen(false)}
                    className="p-1.5 text-slate-400 hover:text-slate-800 dark:hover:text-white rounded-lg hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleAddColumnSubmit} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-semibold text-slate-500 dark:text-slate-400 mb-1.5 uppercase tracking-wider font-display">
                      Plantillas sugeridas:
                    </label>
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {COLUMN_PRESETS.map((p) => (
                        <button
                          key={p.name}
                          type="button"
                          onClick={() => {
                            setNewColName(p.name);
                            setNewColDefault(p.defaultVal);
                          }}
                          className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-black/[0.03] dark:bg-white/[0.05] hover:bg-[#5e8967]/15 dark:hover:bg-[#5e8967]/25 border border-black/5 dark:border-white/10 text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>

                    <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Nombre de la Columna</label>
                    <input
                      type="text"
                      required
                      placeholder="Ej: Fondo_Universidad o Aportacion_HSA"
                      value={newColName}
                      onChange={(e) => setNewColName(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-black/[0.03] dark:bg-white/[0.05] border border-black/10 dark:border-white/10 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-[#5e8967]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Valor por Defecto ($)</label>
                    <input
                      type="number"
                      value={newColDefault}
                      onChange={(e) => setNewColDefault(Number(e.target.value))}
                      className="w-full px-3 py-2 text-sm bg-black/[0.03] dark:bg-white/[0.05] border border-black/10 dark:border-white/10 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-[#5e8967]"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsAddColModalOpen(false)}
                      className="px-4 py-2 text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white transition-colors cursor-pointer"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] rounded-full shadow-sm transition-all cursor-pointer"
                    >
                      Crear Columna
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProjectionTable;

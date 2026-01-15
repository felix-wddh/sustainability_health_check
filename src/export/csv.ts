import type { KPIResult, Snapshot } from '../state/types';

function toCSV(rows: (string|number|null|undefined)[][]): string {
  const esc = (v: any) => {
    const s = v === null || v === undefined ? '' : String(v);
    if (/[",
]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  };
  return rows.map((r) => r.map(esc).join(',')).join('\r\n');
}

export function downloadCSVFromKPIs(kpis: KPIResult[], filename = 'kpis.csv') {
  const header = ['Product','Category','Transport_kgCO2e','Materials_kgCO2e','Production_kgCO2e','Use_CO2e','Total_CO2e','Use_Share_%'];
  const rows = kpis.map(k => [k.Product, k.Category, k.stageBreakdown.Transport, k.stageBreakdown.Materials, k.stageBreakdown.Production, k.stageBreakdown.Use, k.Total_CO2e, k.UsePhase_Share_Pct]);
  const csv = toCSV([header, ...rows]);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href);
}

export function downloadSnapshotJSON(s: Snapshot, filename = 'snapshot.json') {
  const blob = new Blob([JSON.stringify(s, null, 2)], { type: 'application/json;charset=utf-8' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href);
}


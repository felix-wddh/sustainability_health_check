import type { MapSuggestion, MappedRecord, MappingForSheet, ProductCategory } from '../state/types';
import { synonymTable, normalizeHeader } from './synonyms';

const requiredTargets = ['Product','Category','Transport_kgCO2e','Materials_kgCO2e','Production_kgCO2e','Use_kWh_per_year'] as const;

export function suggestMapping(headers: string[]): MapSuggestion[] {
  const suggestions: MapSuggestion[] = [];
  const norm = headers.map((h) => ({ raw: h, n: normalizeHeader(h) }));
  for (const target of Object.keys(synonymTable) as Array<keyof typeof synonymTable>) {
    let best: { from: string | null; score: number } = { from: null, score: 0 };
    const syns = [normalizeHeader(target), ...synonymTable[target].map(normalizeHeader)];
    for (const h of norm) {
      const score = syns.some((s) => h.n.includes(s)) ? 1 : 0;
      const exact = syns.includes(h.n) ? 0.5 : 0;
      if (score + exact > best.score) best = { from: h.raw, score: score + exact };
    }
    suggestions.push({ target: target as any, fromHeader: best.from, confidence: Math.min(1, best.score) });
  }
  return suggestions;
}

export function applyMapping(rows: any[], mapping: MappingForSheet): { records: MappedRecord[]; missing: string[] } {
  const fieldFrom: Record<string,string|undefined> = Object.fromEntries(mapping.suggestions.map(s => [s.target, s.fromHeader || undefined]));
  const missing = requiredTargets.filter((t) => !fieldFrom[t]);
  const toNum = (v: any): number | null => {
    if (v === null || v === undefined || v === '') return null;
    if (typeof v === 'number') return v;
    const str = String(v).replace(/,/g, '.').replace(/[^0-9.-]/g, '');
    const n = Number(str);
    return isFinite(n) ? n : null;
  };
  const toCat = (v: any): ProductCategory => {
    const s = String(v || '').toLowerCase();
    if (s.startsWith('cook')) return 'Cooking';
    if (s.startsWith('cool') || s.includes('fridge')) return 'Cooling';
    if (s.startsWith('wash')) return 'Washing';
    return 'Unknown';
  };
  const recs: MappedRecord[] = rows.map((r) => ({
    Product: String(fieldFrom['Product'] ? r[fieldFrom['Product']] : r['Product'] ?? ''),
    Category: toCat(fieldFrom['Category'] ? r[fieldFrom['Category']] : r['Category']),
    Transport_kgCO2e: toNum(r[fieldFrom['Transport_kgCO2e']!]),
    Materials_kgCO2e: toNum(r[fieldFrom['Materials_kgCO2e']!]),
    Production_kgCO2e: toNum(r[fieldFrom['Production_kgCO2e']!]),
    Use_kWh_per_year: toNum(r[fieldFrom['Use_kWh_per_year']!]),
    Water_L: toNum(r[fieldFrom['Water_L']!]),
    Recycling_Quota_%: toNum(r[fieldFrom['Recycling_Quota_%']!]),
    Local_Quota_%: toNum(r[fieldFrom['Local_Quota_%']!]),
    EU_Label: String(r[fieldFrom['EU_Label']!] ?? '') || null
  }));
  return { records: recs, missing: missing as unknown as string[] };
}


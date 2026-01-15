/// <reference lib="webworker" />
import * as XLSX from 'xlsx';

type InMsg =
  | { type: 'parse'; file: ArrayBuffer; fileName: string }
  | { type: 'parseDummy'; name: string };

type OutMsg =
  | { type: 'meta'; value: { name: string; sheetNames: string[] } }
  | { type: 'sheet'; value: { sheet: string; headerRowIndex: number; headers: string[]; rows: any[] } }
  | { type: 'error'; error: string }
  | { type: 'done' };

function autoDetectHeaderRow(rows: any[][]): number {
  let bestIdx = 0; let bestScore = -Infinity;
  const keywordHints = ['transport', 'materials', 'production', 'use', 'kwh', 'product'];
  rows.slice(0, Math.min(20, rows.length)).forEach((r, i) => {
    const score = r.reduce((acc: number, cell: any) => {
      const v = String(cell ?? '').toLowerCase();
      const hits = keywordHints.some((k) => v.includes(k)) ? 1 : 0;
      const len = v.length > 0 ? 0.2 : 0;
      return acc + hits + len;
    }, 0);
    if (score > bestScore) { bestScore = score; bestIdx = i; }
  });
  return bestIdx;
}

function post(msg: OutMsg) { (self as any).postMessage(msg); }

async function handleParse(buf: ArrayBuffer, fileName: string) {
  try {
    const wb = XLSX.read(buf, { type: 'array' });
    post({ type: 'meta', value: { name: fileName, sheetNames: wb.SheetNames } });
    for (const s of wb.SheetNames) {
      const ws = wb.Sheets[s];
      const aoa = XLSX.utils.sheet_to_json<any[]>(ws, { header: 1, raw: true });
      const headerRowIndex = autoDetectHeaderRow(aoa);
      const headers = (aoa[headerRowIndex] || []).map((h) => String(h ?? ''));
      const rows = aoa.slice(headerRowIndex + 1);
      const chunkSize = 1000;
      for (let i = 0; i < rows.length; i += chunkSize) {
        const slice = rows.slice(i, i + chunkSize).map((r) => Object.fromEntries(headers.map((h, idx) => [h, r[idx]])));
        post({ type: 'sheet', value: { fileName, sheet: s, headerRowIndex, headers, rows: slice } });
      }
    }
    post({ type: 'done' });
  } catch (e: any) {
    post({ type: 'error', error: e?.message || String(e) });
  }
}

function makeDummy(name: string) {
  const rows = [
    ['Product','Category','Transport_kgCO2e','Materials_kgCO2e','Production_kgCO2e','Use_kWh_per_year','Water_L','Recycling_Quota_%','Local_Quota_%','EU_Label'],
    ['Cooker A','Cooking', 50, 180, 120, 150, 200, 30, 40, 'A++'],
    ['Fridge B','Cooling', 70, 220, 150, 200, 150, 25, 20, 'A+'],
    ['Washer C','Washing', 40, 160, 100, 180, 300, 35, 60, 'A']
  ];
  return { name, sheetNames: ['Data'], sheets: { Data: rows } };
}

async function handleParseDummy(name: string) {
  try {
    const d = makeDummy(name);
    post({ type: 'meta', value: { name: d.name, sheetNames: d.sheetNames } });
    const rows = d.sheets['Data'];
    post({ type: 'sheet', value: {
      sheet: 'Data',
      headerRowIndex: 0,
      headers: rows[0] as string[],
      rows: rows.slice(1).map((r) => Object.fromEntries((rows[0] as string[]).map((h, i) => [h, r[i]])))
    }});
    post({ type: 'done' });
  } catch (e: any) {
    post({ type: 'error', error: e?.message || String(e) });
  }
}

self.onmessage = (ev: MessageEvent<InMsg>) => {
  const msg = ev.data;
  if (msg.type === 'parse') handleParse(msg.file, msg.fileName);
  if (msg.type === 'parseDummy') handleParseDummy(msg.name);
};

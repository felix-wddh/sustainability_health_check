import type { MappedRecord, ValidationIssue, DataQualitySummary } from '../state/types';

export function validate(records: MappedRecord[]): DataQualitySummary {
  const issues: ValidationIssue[] = [];
  records.forEach((r, idx) => {
    const row = idx + 1;
    const req: Array<keyof MappedRecord> = ['Transport_kgCO2e','Materials_kgCO2e','Production_kgCO2e','Use_kWh_per_year'];
    for (const f of req) {
      const v = r[f] as unknown as number | null;
      if (v === null || Number.isNaN(v)) issues.push({ rowIndex: row, field: String(f), severity: 'error', message: 'Missing required value' });
      else if (v < 0) issues.push({ rowIndex: row, field: String(f), severity: 'error', message: 'Negative value' });
      else if (v > 1e7) issues.push({ rowIndex: row, field: String(f), severity: 'warning', message: 'Suspiciously large' });
    }
  });
  const status: DataQualitySummary['status'] = issues.some(i => i.severity==='error') ? 'red' : issues.length ? 'amber' : 'green';
  return { status, issues };
}


import { describe, it, expect } from 'vitest';
import { validate } from '../src/validation/validator';

describe('validation', () => {
  it('flags missing and negative values', () => {
    const recs: any[] = [{
      Product: 'X', Category: 'Cooking',
      Transport_kgCO2e: null, Materials_kgCO2e: -5, Production_kgCO2e: 0, Use_kWh_per_year: 1e8
    }];
    const dq = validate(recs as any);
    expect(dq.issues.some(i => i.field==='Transport_kgCO2e' && i.severity==='error')).toBe(true);
    expect(dq.issues.some(i => i.field==='Materials_kgCO2e' && i.severity==='error')).toBe(true);
    expect(dq.issues.some(i => i.severity==='warning')).toBe(true);
  });
});


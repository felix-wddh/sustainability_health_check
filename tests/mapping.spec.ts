import { describe, it, expect } from 'vitest';
import { suggestMapping, applyMapping } from '../src/mapping/mapper';

describe('mapping', () => {
  it('suggests headers with confidence', () => {
    const headers = ['Product','Category','Transport kgCO2e','Materials kgCO2e','Production kgCO2e','kWh per year'];
    const sug = suggestMapping(headers);
    expect(sug.find(s => s.target==='Transport_kgCO2e')?.fromHeader).toBeTruthy();
  });
  it('applies mapping and normalizes numbers', () => {
    const headers = ['Product','Category','Transport kgCO2e','Materials kgCO2e','Production kgCO2e','kWh per year'];
    const suggestions = suggestMapping(headers);
    const mapping = { sheetName: 'S', headerRowIndex: 0, suggestions };
    const rows = [{ 'Product':'A','Category':'Cooking','Transport kgCO2e':'1,200','Materials kgCO2e':'50','Production kgCO2e':5,'kWh per year':'100' }];
    const { records, missing } = applyMapping(rows, mapping as any);
    expect(missing.length).toBe(0);
    expect(records[0].Transport_kgCO2e).toBe(1200);
    expect(records[0].Use_kWh_per_year).toBe(100);
  });
});


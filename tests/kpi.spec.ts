import { describe, it, expect } from 'vitest';
import { computeKPIs } from '../src/kpi/engine';

describe('kpi', () => {
  it('computes totals and shares', () => {
    const recs: any[] = [{
      Product: 'X', Category: 'Cooking',
      Transport_kgCO2e: 10, Materials_kgCO2e: 20, Production_kgCO2e: 30, Use_kWh_per_year: 100
    }];
    const kpis = computeKPIs(recs as any, { region: 'EU-27', factor: 0.25 }, { Cooking: 10 } as any, { usePhasePercentRed: 60, materialsKgRed: 200, productionKgGreen: 100 });
    expect(kpis[0].Total_CO2e).toBeGreaterThan(60);
    expect(kpis[0].UsePhase_Share_Pct).toBeGreaterThan(0);
  });
});


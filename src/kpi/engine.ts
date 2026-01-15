import type { KPIResult, MappedRecord, GridFactors, Thresholds } from '../state/types';

export function computeKPIs(records: MappedRecord[], grid: GridFactors, lifetimeYears: Record<string, number>, thresholds: Thresholds): KPIResult[] {
  const res: KPIResult[] = records.map((r) => {
    const life = lifetimeYears[r.Category] ?? 10;
    const use = (r.Use_kWh_per_year ?? 0) * (grid.factor ?? 0.25) * life / 1000; // kWh * kgCO2/kWh -> kg
    const transport = r.Transport_kgCO2e ?? 0;
    const materials = r.Materials_kgCO2e ?? 0;
    const production = r.Production_kgCO2e ?? 0;
    const total = transport + materials + production + use;
    const share = total > 0 ? (use / total) * 100 : 0;
    const status = {
      UsePhase: share >= thresholds.usePhasePercentRed ? 'red' : share >= thresholds.usePhasePercentRed * 0.7 ? 'amber' : 'green',
      Materials: materials >= thresholds.materialsKgRed ? 'red' : materials >= thresholds.materialsKgRed * 0.7 ? 'amber' : 'green',
      Production: production <= thresholds.productionKgGreen ? 'green' : production <= thresholds.productionKgGreen * 1.5 ? 'amber' : 'red'
    } as const;
    return {
      Product: r.Product,
      Category: r.Category,
      UsePhase_CO2e: round(use),
      Total_CO2e: round(total),
      UsePhase_Share_Pct: round(share),
      stageBreakdown: { Transport: round(transport), Materials: round(materials), Production: round(production), Use: round(use) },
      status
    };
  });
  return res;
}

function round(n: number) { return Math.round(n * 100) / 100; }


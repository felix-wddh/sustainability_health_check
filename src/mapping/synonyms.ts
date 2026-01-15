export const synonymTable: Record<string, string[]> = {
  Product: ['product', 'sku', 'item', 'model'],
  Category: ['category', 'segment', 'family', 'type'],
  Transport_kgCO2e: ['transport co2', 'transport kgco2e', 'co2e transport', 'logistics co2', 'shipping co2'],
  Materials_kgCO2e: ['materials co2', 'materials kgco2e', 'co2e materials', 'material footprint', 'bom co2'],
  Production_kgCO2e: ['production co2', 'production kgco2e', 'co2e production', 'manufacturing co2', 'factory co2'],
  Use_kWh_per_year: ['use kwh', 'kwh per year', 'annual kwh', 'energy use', 'electricity use'],
  Water_L: ['water', 'water_l', 'water (l)', 'liters', 'consumption water'],
  Recycling_Quota_%: ['recycling quota', 'recycling %', 'recycling rate'],
  Local_Quota_%: ['local quota', 'local %', 'local share'],
  EU_Label: ['eu label', 'energy label']
};

export function normalizeHeader(h: string): string {
  return h.toLowerCase().replace(/\s+|[_-]+/g, ' ').trim();
}


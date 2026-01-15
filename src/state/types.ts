export type ProductCategory = 'Cooking' | 'Cooling' | 'Washing' | 'Unknown';

export interface RawFileMeta {
  name: string;
  source: 'Upload' | 'Dummy';
  sheetNames: string[];
}

export interface DetectedProduct {
  product: string;
  category: ProductCategory;
  sourceFile: string;
  status: 'Parsed' | 'Mapped' | 'Validated' | 'Error';
  message?: string;
  sheet?: string;
}

export type RequiredFields = {
  Transport_kgCO2e: number | null;
  Materials_kgCO2e: number | null;
  Production_kgCO2e: number | null;
  Use_kWh_per_year: number | null;
};

export type OptionalFields = {
  Water_L?: number | null;
  Recycling_Quota_%?: number | null;
  Local_Quota_%?: number | null;
  EU_Label?: string | null;
};

export type MappedRecord = RequiredFields & OptionalFields & {
  Product: string;
  Category: ProductCategory;
};

export interface MapSuggestion {
  target: keyof (RequiredFields & OptionalFields) | 'Product' | 'Category';
  fromHeader: string | null;
  confidence: number; // 0..1
}

export interface MappingForSheet {
  sheetName: string;
  headerRowIndex: number; // 0-based
  suggestions: MapSuggestion[];
}

export interface ValidationIssue {
  rowIndex: number;
  field: string;
  severity: 'error' | 'warning';
  message: string;
}

export interface DataQualitySummary {
  status: 'red' | 'amber' | 'green';
  issues: ValidationIssue[];
}

export interface GridFactors {
  region: 'Mexico' | 'EU-27' | 'USA' | 'Renewables' | 'Custom';
  factor: number;
}

export interface Thresholds {
  usePhasePercentRed: number; // X%
  materialsKgRed: number; // Y kg
  productionKgGreen: number; // Z kg
}

export interface KPIResult {
  Product: string;
  Category: ProductCategory;
  UsePhase_CO2e: number;
  Total_CO2e: number;
  UsePhase_Share_Pct: number;
  stageBreakdown: {
    Transport: number;
    Materials: number;
    Production: number;
    Use: number;
  };
  status: {
    UsePhase: 'red' | 'amber' | 'green';
    Materials: 'red' | 'amber' | 'green';
    Production: 'red' | 'amber' | 'green';
  };
}

export interface Snapshot {
  at: string; // ISO
  kpis: KPIResult[];
  totals: { count: number; totalCO2e: number };
  thresholds: Thresholds;
}

export interface WizardState {
  stepIndex: number; // 0..4
  files: RawFileMeta[];
  detected: DetectedProduct[];
  mappings: Record<string, MappingForSheet>; // key: fileName::sheet
  sheets: Record<string, { headers: string[]; rows: any[] }>;
  records: MappedRecord[];
  dataQuality?: DataQualitySummary;
  gridFactor: GridFactors;
  lifetimeYears: Record<ProductCategory, number>;
  thresholds: Thresholds;
  kpis: KPIResult[];
  lockedSnapshot?: Snapshot;
  busy: boolean;
  error?: string;
}

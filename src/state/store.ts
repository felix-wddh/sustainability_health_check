import type { WizardState, ProductCategory, DetectedProduct, MappingForSheet, MappedRecord, KPIResult, Snapshot, GridFactors, Thresholds } from './types';

type Listener = () => void;

const defaultThresholds: Thresholds = {
  usePhasePercentRed: 60,
  materialsKgRed: 200,
  productionKgGreen: 100
};

const init: WizardState = {
  stepIndex: 0,
  files: [],
  detected: [],
  mappings: {},
  sheets: {},
  records: [],
  gridFactor: { region: 'EU-27', factor: 0.25 },
  lifetimeYears: { Cooking: 12, Cooling: 10, Washing: 8, Unknown: 10 },
  thresholds: defaultThresholds,
  kpis: [],
  busy: false
};

const persistedRaw = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('nx_state') : null;
let state: WizardState = persistedRaw ? { ...init, ...JSON.parse(persistedRaw) } : init;
const listeners: Listener[] = [];

function notify() { listeners.forEach((l) => l()); }

export const store = {
  get: () => state,
  set(patch: Partial<WizardState>) {
    state = { ...state, ...patch };
    notify();
  },
  update(mutator: (s: WizardState) => void) {
    const next = structuredClone(state);
    mutator(next);
    state = next;
    notify();
  },
  subscribe(fn: Listener) {
    listeners.push(fn);
    return () => {
      const i = listeners.indexOf(fn);
      if (i >= 0) listeners.splice(i, 1);
    };
  },
  nextStep() {
    store.update((s) => { s.stepIndex = Math.min(4, s.stepIndex + 1); });
  },
  prevStep() {
    store.update((s) => { s.stepIndex = Math.max(0, s.stepIndex - 1); });
  },
  resetError() { store.set({ error: undefined }); },
  setBusy(b: boolean) { store.set({ busy: b }); },
  addFile(meta: WizardState['files'][number]) { store.update((s) => { s.files.push(meta); }); },
  addDetected(dp: DetectedProduct[]) { store.update((s) => { s.detected.push(...dp); }); },
  setMapping(key: string, map: MappingForSheet) { store.update((s) => { s.mappings[key] = map; }); },
  setSheet(key: string, data: { headers: string[]; rows: any[] }) { store.update((s) => { s.sheets[key] = data; }); },
  setRecords(records: MappedRecord[]) { store.set({ records }); },
  setKPIs(kpis: KPIResult[]) { store.set({ kpis }); },
  lock() {
    const snapshot: Snapshot = {
      at: new Date().toISOString(),
      kpis: state.kpis,
      totals: { count: state.kpis.length, totalCO2e: state.kpis.reduce((a, b) => a + b.Total_CO2e, 0) },
      thresholds: state.thresholds
    };
    store.set({ lockedSnapshot: snapshot });
  },
  setGridFactor(gf: GridFactors) { store.set({ gridFactor: gf }); },
  setThresholds(t: Thresholds) { store.set({ thresholds: t }); },
  setLifetime(cat: ProductCategory, years: number) { store.update((s) => { s.lifetimeYears[cat] = years; }); }
};

// Persist lightweight state in-session (avoid large rows)
function persist() {
  const light = {
    stepIndex: state.stepIndex,
    gridFactor: state.gridFactor,
    lifetimeYears: state.lifetimeYears,
    thresholds: state.thresholds
  } as Partial<WizardState>;
  try { sessionStorage.setItem('nx_state', JSON.stringify(light)); } catch {}
}

listeners.push(persist);

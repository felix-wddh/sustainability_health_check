import { store } from '../../state/store';
import { computeKPIs } from '../../kpi/engine';

export function renderStep3(root: HTMLElement) {
  const s = store.get();
  const wrap = document.createElement('div');
  const disabled = (s.records?.length ?? 0) === 0;
  wrap.innerHTML = `
    <div class="row">
      <h3 style="margin:0">KPI Computation & Benchmarking</h3>
      <div class="spacer"></div>
      <button id="computeBtn" class="btn primary" ${disabled ? 'disabled' : ''}>Compute KPIs</button>
    </div>
    <div style="height:8px"></div>
    <div class="grid">
      <div class="card col-12">
        <div id="kpiTable"></div>
      </div>
    </div>
  `;
  root.appendChild(wrap);

  const computeBtn = wrap.querySelector('#computeBtn')! as HTMLButtonElement;
  const kpiDiv = wrap.querySelector('#kpiTable')! as HTMLDivElement;

  computeBtn.addEventListener('click', () => {
    const st = store.get();
    const kpis = computeKPIs(st.records, st.gridFactor, st.lifetimeYears as any, st.thresholds);
    store.setKPIs(kpis);
    renderTable();
    store.nextStep();
  });

  function renderTable() {
    const k = store.get().kpis;
    if (!k.length) { kpiDiv.innerHTML = '<div class="help">No KPIs yet. Click Compute.</div>'; return; }
    const rows = k.map(x => `<tr>
      <td>${x.Product}</td><td>${x.Category}</td>
      <td>${x.stageBreakdown.Transport}</td><td>${x.stageBreakdown.Materials}</td><td>${x.stageBreakdown.Production}</td><td>${x.stageBreakdown.Use}</td>
      <td>${x.Total_CO2e}</td><td>${x.UsePhase_Share_Pct}%</td>
      <td><span class="status-light ${cls(x.status.UsePhase)}"></span></td>
      <td><span class="status-light ${cls(x.status.Materials)}"></span></td>
      <td><span class="status-light ${cls(x.status.Production)}"></span></td>
    </tr>`).join('');
    kpiDiv.innerHTML = `<table>
      <thead><tr><th>Product</th><th>Category</th><th>Transport</th><th>Materials</th><th>Production</th><th>Use</th><th>Total CO₂e</th><th>Use Share</th><th>UsePhase</th><th>Materials</th><th>Production</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }
  function cls(s: 'red'|'amber'|'green') { return s==='green'?'status-green':s==='amber'?'status-amber':'status-red'; }

  renderTable();
}


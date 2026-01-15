import { store } from '../../state/store';

export function renderStep4(root: HTMLElement) {
  const wrap = document.createElement('div');
  const disabled = (store.get().kpis?.length ?? 0) === 0;
  wrap.innerHTML = `
    <div class="row">
      <h3 style="margin:0">Expert Review & Lock</h3>
      <div class="spacer"></div>
      <button id="lockBtn" class="btn primary" ${disabled ? 'disabled' : ''}>Lock Baseline</button>
    </div>
    <div style="height:8px"></div>
    <div class="grid">
      <div class="card col-12" id="dashboards"></div>
    </div>
  `;
  root.appendChild(wrap);

  const lockBtn = wrap.querySelector('#lockBtn')! as HTMLButtonElement;
  const dashboards = wrap.querySelector('#dashboards')! as HTMLDivElement;

  lockBtn.addEventListener('click', () => {
    store.lock();
    renderDashboards();
    store.nextStep();
  });

  function renderDashboards() {
    const snap = store.get().lockedSnapshot;
    if (!snap) { dashboards.innerHTML = '<div class="help">Lock baseline to see dashboards.</div>'; return; }
    const sections = ['Overview','Transport','Materials','Production','Use Phase','Recycling'];
    dashboards.innerHTML = sections.map((name) => `
      <div class="card" style="margin-bottom:12px">
        <h4 style="margin:0 0 6px 0">${name}</h4>
        ${renderSection(name)}
      </div>
    `).join('');
  }

  function renderSection(name: string) {
    const snap = store.get().lockedSnapshot!;
    const k = snap.kpis;
    const bars = k.map(x => {
      const total = x.Total_CO2e || 1;
      const segments = {
        Transport: (x.stageBreakdown.Transport/total)*100,
        Materials: (x.stageBreakdown.Materials/total)*100,
        Production: (x.stageBreakdown.Production/total)*100,
        Use: (x.stageBreakdown.Use/total)*100
      };
      return `<div style="margin:6px 0">${x.Product}
        <div class="progressbar"><div style="--w:${segments.Use.toFixed(2)}%"></div></div>
        <div class="help">Use-phase share: ${x.UsePhase_Share_Pct}%</div>
      </div>`;
    }).join('');
    return `<div>${bars}</div>`;
  }

  renderDashboards();
}


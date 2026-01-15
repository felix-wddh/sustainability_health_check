import { store } from '../../state/store';
import { downloadCSVFromKPIs, downloadSnapshotJSON } from '../../export/csv';

export function renderStep5(root: HTMLElement) {
  const wrap = document.createElement('div');
  const snap = store.get().lockedSnapshot;
  const disabled = !snap;
  wrap.innerHTML = `
    <div class="row">
      <h3 style="margin:0">Exports</h3>
      <div class="spacer"></div>
      <button id="csvBtn" class="btn" ${disabled ? 'disabled' : ''}>Download CSV</button>
      <button id="jsonBtn" class="btn" ${disabled ? 'disabled' : ''}>Download JSON</button>
    </div>
    <div style="height:8px"></div>
    <div class="card">
      <div class="help">PPT export is intentionally disabled for this release. CSV and JSON are produced from the frozen snapshot.</div>
    </div>
  `;
  root.appendChild(wrap);

  const csvBtn = wrap.querySelector('#csvBtn')! as HTMLButtonElement;
  const jsonBtn = wrap.querySelector('#jsonBtn')! as HTMLButtonElement;
  csvBtn.addEventListener('click', () => { const s = store.get().lockedSnapshot; if (s) downloadCSVFromKPIs(s.kpis); });
  jsonBtn.addEventListener('click', () => { const s = store.get().lockedSnapshot; if (s) downloadSnapshotJSON(s); });
}

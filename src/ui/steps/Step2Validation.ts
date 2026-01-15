import { store } from '../../state/store';
import { applyMapping } from '../../mapping/mapper';
import { validate } from '../../validation/validator';

export function renderStep2(root: HTMLElement) {
  const s = store.get();
  const wrap = document.createElement('div');
  const canProceed = Object.keys(s.mappings).length > 0;
  wrap.innerHTML = `
    <div class="row">
      <h3 style="margin:0">Completeness & Consistency</h3>
      <div class="spacer"></div>
      <button id="mapBtn" class="btn primary" ${canProceed ? '' : 'disabled'}>Apply Mapping & Validate</button>
    </div>
    <div style="height:8px"></div>
    <div class="grid">
      <div class="card col-6">
        <h4 style="margin:0 0 8px 0">Auto Mapping</h4>
        <div id="mapping"></div>
      </div>
      <div class="card col-6">
        <h4 style="margin:0 0 8px 0">Data Quality</h4>
        <div id="dq"></div>
      </div>
    </div>
  `;
  root.appendChild(wrap);

  const mapDiv = wrap.querySelector('#mapping')!;
  const dqDiv = wrap.querySelector('#dq')!;
  const mapBtn = wrap.querySelector('#mapBtn')! as HTMLButtonElement;

  // Show mapping suggestions (simplified UI)
  mapDiv.innerHTML = Object.entries(s.mappings).map(([key, m]) => {
    const headers = store.get().sheets[key]?.headers ?? [];
    const options = ['(none)', ...headers];
    const rows = m.suggestions.map((sug, idx) => {
      const opts = options.map(h => `<option value="${h}">${h}</option>`).join('');
      return `<tr>
        <td>${sug.target}</td>
        <td>
          <select data-key="${key}" data-idx="${idx}" class="input">${opts}</select>
        </td>
        <td>${Math.round(sug.confidence*100)}%</td>
      </tr>`;
    }).join('');
    return `<div class="card" style="margin-bottom:8px">
      <div><strong>Sheet:</strong> ${m.sheetName}</div>
      <table><thead><tr><th>Target</th><th>From Header</th><th>Confidence</th></tr></thead>
      <tbody>${rows}</tbody></table>
    </div>`;
  }).join('');

  // initialize selects to current mapping
  mapDiv.querySelectorAll('select').forEach((sel) => {
    const select = sel as HTMLSelectElement;
    const key = select.getAttribute('data-key')!;
    const idx = Number(select.getAttribute('data-idx')!);
    const current = store.get().mappings[key].suggestions[idx].fromHeader ?? '(none)';
    select.value = current;
    select.addEventListener('change', () => {
      const m = store.get().mappings[key];
      const suggestions = m.suggestions.slice();
      suggestions[idx] = { ...suggestions[idx], fromHeader: select.value === '(none)' ? null : select.value };
      store.setMapping(key, { ...m, suggestions });
    });
  });

  mapBtn.addEventListener('click', () => {
    // In this MVP, we assume one sheet parsed via Step 1 worker and stored only as detected list.
    // We now retain sheet rows in store.sheets for mapping.
    const bufferKey = Object.keys(s.mappings)[0];
    if (!bufferKey) return;
    const sheet = store.get().sheets[bufferKey];
    const rows = sheet?.rows ?? [];
    const mapping = s.mappings[bufferKey];
    const { records, missing } = applyMapping(rows as any[], mapping);
    if (missing.length) {
      dqDiv.innerHTML = `<div class="badge warn">Missing required: ${missing.join(', ')}</div>`;
    }
    const dq = validate(records);
    store.set({ records, dataQuality: dq });
    dqDiv.innerHTML = `<div>Overall: <span class="status-light ${dq.status==='green'?'status-green':dq.status==='amber'?'status-amber':'status-red'}"></span> ${dq.status.toUpperCase()}</div>
      <div style="height:6px"></div>
      <div style="max-height:220px; overflow:auto">
        <table><thead><tr><th>Row</th><th>Field</th><th>Severity</th><th>Message</th></tr></thead>
        <tbody>${dq.issues.map(i => `<tr><td>${i.rowIndex}</td><td>${i.field}</td><td>${i.severity}</td><td>${i.message}</td></tr>`).join('')}</tbody></table>
      </div>`;
    if (dq.status !== 'red') store.nextStep();
  });
}

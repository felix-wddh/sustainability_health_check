import { store } from '../../state/store';
import type { MappingForSheet } from '../../state/types';
import { parseFile, parseDummy } from '../../ingestion/parser';
import { suggestMapping } from '../../mapping/mapper';

export function renderStep1(root: HTMLElement) {
  const s = store.get();
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <div class="row" role="group" aria-label="Data intake controls">
      <div>
        <label for="fileInput">Upload Excel Files</label><br/>
        <input id="fileInput" type="file" class="input" aria-label="Upload Excel files" multiple accept=".xlsx,.xls,.csv" />
      </div>
      <button id="dummyBtn" class="btn">Use Dummy Data</button>
      <div class="spacer"></div>
      <div class="card" style="min-width:280px;">
        <div class="row">
          <div>
            <label for="region">Country grid factor</label><br/>
            <select id="region" class="input">
              <option>EU-27</option>
              <option>Mexico</option>
              <option>USA</option>
              <option>Renewables</option>
              <option>Custom</option>
            </select>
          </div>
          <div>
            <label for="factor">Factor kgCO2/kWh</label><br/>
            <input id="factor" class="input" type="number" step="0.01" />
          </div>
        </div>
      </div>
    </div>
    <div style="height:8px"></div>
    <div class="card">
      <h3 style="margin-top:0">Detected products</h3>
      <table aria-label="Detected products table">
        <thead><tr><th>Product</th><th>Source</th><th>Sheet</th><th>Status</th></tr></thead>
        <tbody id="detectedBody"></tbody>
      </table>
    </div>
  `;
  root.appendChild(wrap);

  const region = wrap.querySelector('#region') as HTMLSelectElement;
  const factor = wrap.querySelector('#factor') as HTMLInputElement;
  region.value = s.gridFactor.region;
  factor.value = String(s.gridFactor.factor);
  region.addEventListener('change', () => {
    const map: Record<string, number> = { 'EU-27':0.25, 'Mexico':0.42, 'USA':0.40, 'Renewables':0.10, 'Custom': s.gridFactor.factor };
    const reg = region.value as any;
    const f = reg === 'Custom' ? Number(factor.value) : map[reg] ?? 0.25;
    factor.value = String(f);
    store.setGridFactor({ region: reg, factor: f });
  });
  factor.addEventListener('input', () => {
    store.setGridFactor({ region: region.value as any, factor: Number(factor.value) });
  });

  const detectedBody = wrap.querySelector('#detectedBody')! as HTMLTableSectionElement;
  const fileInput = wrap.querySelector('#fileInput')! as HTMLInputElement;
  const dummyBtn = wrap.querySelector('#dummyBtn')! as HTMLButtonElement;

  function addDetectedRows() {
    detectedBody.innerHTML = '';
    store.get().detected.forEach((d) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${d.product}</td><td>${d.sourceFile}</td><td>${d.sheet ?? ''}</td><td><span class="badge ok">${d.status}</span></td>`;
      detectedBody.appendChild(tr);
    });
  }
  addDetectedRows();

  async function handleProgress(ev: any) {
    if (ev.type === 'sheet') {
      const headers = ev.value.headers as string[];
      const suggestions = suggestMapping(headers);
      const fileName = ev.value.fileName ?? 'Upload';
      const key = `${fileName}::${ev.value.sheet}`;
      const map: MappingForSheet = { sheetName: ev.value.sheet, headerRowIndex: ev.value.headerRowIndex, suggestions };
      store.setMapping(key, map);
      const rows: any[] = ev.value.rows;
      const existing = store.get().sheets[key];
      const combined = existing ? existing.rows.concat(rows) : rows;
      store.setSheet(key, { headers, rows: combined });
      rows.forEach((r: any) => {
        store.addDetected([{ product: String(r['Product'] ?? r['product'] ?? 'Unknown'), category: 'Unknown', sourceFile: fileName, status: 'Parsed', sheet: ev.value.sheet }]);
      });
      addDetectedRows();
      // enable next step
      if (store.get().stepIndex === 0) store.nextStep();
    }
    if (ev.type === 'error') {
      store.set({ error: ev.error });
    }
  }

  fileInput.addEventListener('change', async () => {
    if (!fileInput.files || fileInput.files.length === 0) return;
    store.setBusy(true);
    for (const f of Array.from(fileInput.files)) {
      try { await parseFile(f, handleProgress); } catch (e: any) { store.set({ error: e.message }); }
    }
    store.setBusy(false);
  });

  dummyBtn.addEventListener('click', async () => {
    store.setBusy(true);
    try { await parseDummy('DummyData.xlsx', handleProgress); } catch (e: any) { store.set({ error: e.message }); }
    store.setBusy(false);
  });
}

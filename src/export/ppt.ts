// Simple PPT export (6 slides) using PptxGenJS
import PptxGenJS from 'pptxgenjs';
import type { Snapshot } from '../state/types';

export async function exportPPTX(snapshot: Snapshot) {
  const pptx = new PptxGenJS();
  pptx.author = 'NEONEX LCA Wizard';
  pptx.company = 'NEONEX';
  pptx.layout = 'LAYOUT_16x9';

  const titleSlide = pptx.addSlide();
  titleSlide.addText('LCA Baseline', { x:1, y:1, fontSize:32, color:'00FF66', bold:true });
  titleSlide.addText(new Date(snapshot.at).toLocaleString(), { x:1, y:2, fontSize:14, color:'666666' });
  titleSlide.addText(`Products: ${snapshot.totals.count}  Total CO₂e: ${snapshot.totals.totalCO2e.toLocaleString()} kg`, { x:1, y:2.6, fontSize:18 });

  const slides = ['Overview','Transport','Materials','Production','Use Phase','Recycling'] as const;
  slides.forEach((name, i) => {
    const s = pptx.addSlide();
    s.addText(name, { x:0.5, y:0.4, fontSize:24, color:'00FF66', bold:true });
    const k = snapshot.kpis;
    const headers = ['Product','Transport','Materials','Production','Use','Total'];
    const rows = k.map(x => [x.Product, x.stageBreakdown.Transport, x.stageBreakdown.Materials, x.stageBreakdown.Production, x.stageBreakdown.Use, x.Total_CO2e]);
    s.addTable([headers, ...rows], { x:0.5, y:1.1, w:9, fontSize:12 });
  });

  await pptx.writeFile({ fileName: 'NEONEX_LCA_Wizard.pptx' });
}


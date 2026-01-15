import { store } from '../state/store';
import { renderStep1 } from './steps/Step1Intake';
import { renderStep2 } from './steps/Step2Validation';
import { renderStep3 } from './steps/Step3KPI';
import { renderStep4 } from './steps/Step4Lock';
import { renderStep5 } from './steps/Step5Export';

const steps = [
  { id: 0, title: 'Intake & Model Setup', render: renderStep1 },
  { id: 1, title: 'Completeness & Consistency', render: renderStep2 },
  { id: 2, title: 'KPI Computation & Benchmark', render: renderStep3 },
  { id: 3, title: 'Expert Review & Lock', render: renderStep4 },
  { id: 4, title: 'One-Click PPT Export', render: renderStep5 }
];

export function renderWizard(root: HTMLElement) {
  const container = document.createElement('div');
  container.className = 'wizard';

  const nav = document.createElement('nav');
  nav.className = 'wizard-nav';

  const content = document.createElement('section');
  content.className = 'wizard-content';
  content.setAttribute('tabindex', '0');

  root.appendChild(container);
  container.appendChild(nav);
  container.appendChild(content);

  function sync() {
    const s = store.get();
    nav.innerHTML = '';
    steps.forEach((step, idx) => {
      const btn = document.createElement('button');
      btn.textContent = `${idx+1}. ${step.title}`;
      const canGo = idx <= s.stepIndex;
      btn.disabled = !canGo;
      if (idx === s.stepIndex) btn.classList.add('active');
      btn.addEventListener('click', () => { if (canGo) store.set({ stepIndex: idx }); });
      nav.appendChild(btn);
    });

    const render = steps[s.stepIndex].render;
    content.innerHTML = '';
    render(content);
  }

  sync();
  store.subscribe(sync);
}


import { renderWizard } from './ui/Wizard';
import { store } from './state/store';

function updateProgress() {
  const stepsDone = store.get().stepIndex;
  const total = 5;
  const el = document.getElementById('progress');
  if (!el) return;
  el.innerHTML = `
    <div class="progressbar" role="progressbar" aria-valuemin="0" aria-valuemax="${total}" aria-valuenow="${stepsDone}">
      <div style="--w:${(stepsDone/total)*100}%"></div>
    </div>
  `;
}

store.subscribe(() => {
  updateProgress();
  const err = store.get().error;
  const banner = document.getElementById('banner');
  if (banner) {
    if (err) { banner.textContent = err; banner.removeAttribute('hidden'); }
    else { banner.setAttribute('hidden',''); }
  }
});

renderWizard(document.getElementById('app')!);
updateProgress();

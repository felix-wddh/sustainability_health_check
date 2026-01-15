import workerUrl from '../workers/xlsxWorker.ts?worker&url';
import type { RawFileMeta } from '../state/types';

export function parseFile(file: File, onProgress: (ev: any) => void): Promise<RawFileMeta> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(workerUrl, { type: 'module' });
    worker.onmessage = (ev) => {
      onProgress(ev.data);
      if (ev.data.type === 'meta') {
        resolve({ name: ev.data.value.name, sheetNames: ev.data.value.sheetNames, source: 'Upload' });
      }
      if (ev.data.type === 'error') reject(new Error(ev.data.error));
    };
    worker.onerror = (e) => reject(e);
    file.arrayBuffer().then((buf) => worker.postMessage({ type: 'parse', file: buf, fileName: file.name }));
  });
}

export function parseDummy(name: string, onProgress: (ev: any) => void): Promise<RawFileMeta> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(workerUrl, { type: 'module' });
    worker.onmessage = (ev) => {
      onProgress(ev.data);
      if (ev.data.type === 'meta') {
        resolve({ name: ev.data.value.name, sheetNames: ev.data.value.sheetNames, source: 'Dummy' });
      }
      if (ev.data.type === 'error') reject(new Error(ev.data.error));
    };
    worker.onerror = (e) => reject(e);
    worker.postMessage({ type: 'parseDummy', name });
  });
}


import { useState, useEffect, useRef } from 'preact/hooks';
import { track } from '@/lib/analytics';
import { WorkerPool } from '@/lib/batch/workerPool';
import type { PoolTask, PoolOutcome } from '@/lib/batch/workerPool';
import {
  isFsaSupported,
  pickDirectory,
  listFiles as listDirFiles,
  writeFile as fsWriteFile,
  queryPermission,
  requestPermission,
} from '@/lib/batch/fsAccess';
import type { DirFile } from '@/lib/batch/fsAccess';
import {
  saveDir,
  saveHistory,
  getHistory,
  getDirs,
  markProcessed,
  getProcessedKeys,
  markerKey,
} from '@/lib/batch/storage';
import type { DirRecord } from '@/lib/batch/storage';
import type { BatchHistoryRecord } from '@/lib/batch/types';
import { exportToZip } from '@/lib/batch/zipExport';
import type { BatchSettings } from '@/lib/batch/types';
import type { OutputFormat, ResizeMethod } from '@/lib/compress/types';

interface T {
  title: string;
  description: string;
  choose_folder: string;
  choose_folder_desc: string;
  add_files: string;
  add_files_desc: string;
  format: string;
  original: string;
  quality: string;
  resize: string;
  resize_none: string;
  resize_fit: string;
  resize_scale: string;
  resize_cover: string;
  resize_thumb: string;
  width: string;
  height: string;
  percent: string;
  concurrency: string;
  concurrency_hint: string;
  overwrite: string;
  skip_processed: string;
  output_mode: string;
  output_same: string;
  output_mirror: string;
  output_subdir: string;
  start: string;
  cancel: string;
  done: string;
  export_zip: string;
  files_col: string;
  size_col: string;
  result_col: string;
  saved_col: string;
  status_queued: string;
  status_processing: string;
  status_done: string;
  status_error: string;
  status_skipped: string;
  progress: string;
  speed: string;
  recent_title: string;
  no_history: string;
  open: string;
  saved: string;
  note_fsa: string;
  pick_cancelled: string;
  unsupported: string;
}

const FORMAT_EXT: Record<OutputFormat, string> = { jpeg: '.jpg', png: '.png', webp: '.webp' };

const DEFAULT_SETTINGS: BatchSettings = {
  format: 'original',
  quality: 80,
  resizeMethod: 'none',
  resizeWidth: 1920,
  resizeHeight: 1080,
  resizePercent: 50,
  concurrency: 4,
  overwrite: true,
  skipProcessed: false,
  outputMode: 'same',
  outputSubdir: 'tinyopt-out',
};

type RowStatus = 'queued' | 'processing' | 'done' | 'error' | 'skipped';

interface Row {
  id: number;
  name: string;
  relPath: string;
  size: number;
  file?: File;
  handle?: FileSystemFileHandle;
  status: RowStatus;
  resultSize?: number;
  error?: string;
}

const STATUS_STYLES: Record<RowStatus, string> = {
  queued: 'text-gray-400',
  processing: 'text-primary-600',
  done: 'text-green-600',
  error: 'text-red-500',
  skipped: 'text-yellow-600',
};

function resolveOutputFormat(setting: BatchSettings['format'], name: string): OutputFormat {
  if (setting !== 'original') return setting;
  const ext = name.toLowerCase();
  if (ext.endsWith('.jpg') || ext.endsWith('.jpeg')) return 'jpeg';
  if (ext.endsWith('.png')) return 'png';
  return 'webp';
}

function outputRelPath(relPath: string, fmt: OutputFormat): string {
  const dot = relPath.lastIndexOf('.');
  const base = dot > 0 ? relPath.slice(0, dot) : relPath;
  return base + FORMAT_EXT[fmt];
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function BatchCompressTool({ t }: { t: T }) {
  const fsaSupported = isFsaSupported();
  const [dirName, setDirName] = useState('');
  const dirHandleRef = useRef<FileSystemDirectoryHandle | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [settings, setSettings] = useState<BatchSettings>(DEFAULT_SETTINGS);
  const [running, setRunning] = useState(false);
  const [doneCount, setDoneCount] = useState(0);
  const [finished, setFinished] = useState(false);
  const [note, setNote] = useState('');
  const [history, setHistory] = useState<BatchHistoryRecord[]>([]);
  const [dirs, setDirs] = useState<DirRecord[]>([]);
  const [now, setNow] = useState(0);
  const zipRef = useRef<{ relPath: string; data: ArrayBuffer }[]>([]);
  const poolRef = useRef<WorkerPool | null>(null);
  const rowsRef = useRef<Row[]>([]);
  const runningRef = useRef(false);
  const startedAtRef = useRef(0);
  rowsRef.current = rows;

  const set = (patch: Partial<BatchSettings>) => setSettings((prev) => ({ ...prev, ...patch }));

  const markRow = (index: number, patch: Partial<Row>) =>
    setRows((prev) => prev.map((r) => (r.id === index ? { ...r, ...patch } : r)));

  useEffect(() => () => poolRef.current?.cancel(), []);

  // Surface unexpected main-thread errors while a batch is running.
  useEffect(() => {
    const onError = (ev: ErrorEvent) => {
      if (runningRef.current) setNote(ev.message || 'Unknown error');
    };
    const onRejection = (ev: PromiseRejectionEvent) => {
      if (runningRef.current) {
        const msg = ev.reason instanceof Error ? ev.reason.message : String(ev.reason);
        setNote(msg || 'Unhandled rejection');
      }
    };
    window.addEventListener('error', onError);
    window.addEventListener('unhandledrejection', onRejection);
    return () => {
      window.removeEventListener('error', onError);
      window.removeEventListener('unhandledrejection', onRejection);
    };
  }, []);

  useEffect(() => {
    getHistory().then((h) => setHistory(h.sort((a, b) => b.date - a.date)));
    getDirs().then((d) => setDirs(d.sort((a, b) => b.date - a.date)));
  }, []);

  useEffect(() => {
    if (!running) return;
    const iv = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(iv);
  }, [running]);

  const addRowsFromFiles = (files: File[]) => {
    const base = rowsRef.current.length;
    setRows([
      ...rowsRef.current,
      ...files.map((f, i) => ({
        id: base + i,
        name: f.name,
        relPath: f.name,
        size: f.size,
        file: f,
        status: 'queued' as RowStatus,
      })),
    ]);
  };

  const addRowsFromDir = (files: DirFile[]) => {
    const base = rowsRef.current.length;
    setRows([
      ...rowsRef.current,
      ...files.map((f, i) => ({
        id: base + i,
        name: f.name,
        relPath: f.relPath,
        size: f.size,
        handle: f.handle,
        status: 'queued' as RowStatus,
      })),
    ]);
  };

  const refreshDirs = async () => {
    setDirs((await getDirs()).sort((a, b) => b.date - a.date));
  };

  const pickFolder = async () => {
    if (!fsaSupported || runningRef.current) return;
    try {
      const handle = await pickDirectory(true);
      if ((await queryPermission(handle)) !== 'granted') {
        await requestPermission(handle);
      }
      dirHandleRef.current = handle;
      setDirName(handle.name);
      await saveDir({ id: `dir-${Date.now()}`, name: handle.name, date: Date.now(), handle });
      await refreshDirs();
      const files = await listDirFiles(handle);
      addRowsFromDir(files);
      track('batch_select_folder', { files: files.length });
    } catch (err) {
      if ((err as DOMException)?.name === 'AbortError') setNote(t.pick_cancelled);
      else setNote(t.unsupported);
    }
  };

  const openDir = async (rec: DirRecord) => {
    if (runningRef.current) return;
    try {
      if ((await queryPermission(rec.handle)) !== 'granted') {
        if ((await requestPermission(rec.handle)) !== 'granted') {
          setNote(t.unsupported);
          return;
        }
      }
      dirHandleRef.current = rec.handle;
      setDirName(rec.name);
      const files = await listDirFiles(rec.handle);
      addRowsFromDir(files);
    } catch {
      setNote(t.unsupported);
    }
  };

  const onFileInput = (e: Event) => {
    const input = e.target as HTMLInputElement;
    if (input.files?.length && !runningRef.current) addRowsFromFiles(Array.from(input.files));
    input.value = '';
  };

  const resolveOutputRel = (relPath: string, fmt: OutputFormat) => {
    const base = outputRelPath(relPath, fmt);
    return settings.outputMode === 'mirror'
      ? `${settings.outputSubdir || 'tinyopt-out'}/${base}`
      : base;
  };

  const start = async () => {
    if (runningRef.current || rowsRef.current.length === 0) return;
    try {
      setRunning(true);
      setFinished(false);
      setNote('');
      zipRef.current = [];
      setDoneCount(0);
      runningRef.current = true;
      startedAtRef.current = Date.now();

    const dirHandle = dirHandleRef.current;
    const processed = new Set(settings.skipProcessed ? await getProcessedKeys() : []);
    const tasks: PoolTask[] = [];
    const plan = new Map<number, { relPath: string; fmt: OutputFormat; size: number; srcRel: string; srcSize: number }>();

    for (const row of rowsRef.current) {
      const mKey = markerKey(row.relPath, row.size);
      if (settings.skipProcessed && processed.has(mKey)) {
        markRow(row.id, { status: 'skipped' });
        continue;
      }
      const fmt = resolveOutputFormat(settings.format, row.name);
      const input = row.file ?? (row.handle ? await row.handle.getFile() : undefined);
      if (!input) continue;
      const resize =
        settings.resizeMethod === 'none'
          ? undefined
          : {
              method: settings.resizeMethod,
              width: settings.resizeWidth,
              height: settings.resizeHeight,
              percent: settings.resizePercent,
            };
      tasks.push({
        index: row.id,
        input,
        size: row.size,
        name: row.name,
        options: { format: fmt, quality: settings.quality, resize },
      });
      plan.set(row.id, {
        relPath: resolveOutputRel(row.relPath, fmt),
        fmt,
        size: row.size,
        srcRel: row.relPath,
        srcSize: row.size,
      });
      markRow(row.id, { status: 'processing' });
    }

    if (tasks.length === 0) {
      setRunning(false);
      setFinished(true);
      runningRef.current = false;
      return;
    }

    const isZipMode = !dirHandle;

    const pool = new WorkerPool({
      concurrency: settings.concurrency,
      onOutcome: (outcome: PoolOutcome) => {
        const item = plan.get(outcome.index);
        if (!item) return;
        if (outcome.error || !outcome.data) {
          markRow(outcome.index, { status: 'error', error: outcome.error });
          setDoneCount((d) => d + 1);
          return;
        }
        const data = outcome.data;
        if (isZipMode) {
          zipRef.current.push({ relPath: item.relPath, data });
          markRow(outcome.index, { status: 'done', resultSize: data.byteLength });
          setDoneCount((d) => d + 1);
        } else {
          const dir = dirHandleRef.current!;
          void fsWriteFile(dir, item.relPath, data, settings.overwrite).then((st) => {
            if (st === 'ok') {
              markRow(outcome.index, { status: 'done', resultSize: data.byteLength });
              void markProcessed(markerKey(item.srcRel, item.srcSize)).catch(()=>{});
            } else if (st === 'skipped') {
              markRow(outcome.index, { status: 'skipped' });
            } else {
              markRow(outcome.index, { status: 'error', error: 'write failed' });
            }
            setDoneCount((d) => d + 1);
          });
        }
        track('batch_file_done', { format: outcome.format });
      },
      onComplete: (cancelled) => {
        setRunning(false);
        setFinished(true);
        runningRef.current = false;
        if (!cancelled) {
          const list = rowsRef.current;
          const rec: BatchHistoryRecord = {
            id: `batch-${Date.now()}`,
            dirName: dirName || 'zip',
            dirId: '',
            date: Date.now(),
            total: tasks.length,
            ok: list.filter((r) => r.status === 'done').length,
            failed: list.filter((r) => r.status === 'error').length,
            skipped: list.filter((r) => r.status === 'skipped').length,
            savedBytes: list.reduce((s, r) => s + (r.resultSize ?? 0), 0),
          };
          void saveHistory(rec).catch(()=>{});
          setHistory((prev) => [rec, ...prev].sort((a, b) => b.date - a.date));
          track('batch_completed', { total: tasks.length, zip: isZipMode });
        }
      },
    });
    poolRef.current = pool;
    pool.run(tasks);
    } catch (err) {
      runningRef.current = false;
      setRunning(false);
      setFinished(true);
      const msg = err instanceof Error ? err.message : String(err);
      setNote(`${t.unsupported}: ${msg}`);
      console.error('Batch start failed:', err);
    }
  };

  const cancel = () => {
    poolRef.current?.cancel();
    setRunning(false);
    setFinished(true);
    runningRef.current = false;
  };

  const downloadZip = async () => {
    await exportToZip(zipRef.current, 'tinyopt-batch.zip');
  };

  const total = rows.length;
  const ok = rows.filter((r) => r.status === 'done').length;
  const failed = rows.filter((r) => r.status === 'error').length;
  const skipped = rows.filter((r) => r.status === 'skipped').length;
  const elapsedMin = Math.max((now - startedAtRef.current) / 60000, 0.0001);
  const speed = running ? Math.round(doneCount / elapsedMin) : 0;
  const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;
  const errorMessages = Array.from(new Set(rows.filter((r) => r.error).map((r) => r.error as string)));

  const statusLabel = (s: RowStatus) =>
    s === 'queued' ? t.status_queued : s === 'processing' ? t.status_processing : s === 'done' ? t.status_done : s === 'error' ? t.status_error : t.status_skipped;

  return (
    <div class="w-full max-w-6xl mx-auto px-4 py-8">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">{t.title}</h1>
        <p class="text-gray-500">{t.description}</p>
      </div>

      {/* Source selection */}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
        <button
          type="button"
          disabled={!fsaSupported || running}
          onClick={pickFolder}
          class={`rounded-xl border p-6 text-center transition-colors disabled:opacity-50 ${
            fsaSupported
              ? 'border-dashed border-gray-300 hover:border-primary-500 hover:bg-primary-50/30 cursor-pointer'
              : 'border-gray-200 bg-gray-50 cursor-not-allowed'
          }`}
        >
          <div class="text-3xl mb-2">&#128193;</div>
          <p class="font-semibold text-gray-800">{t.choose_folder}</p>
          <p class="text-xs text-gray-400 mt-1">{dirName ? `${dirName} ✓` : t.choose_folder_desc}</p>
        </button>

        <label class="block">
          <input type="file" multiple accept="image/*" class="hidden" onChange={onFileInput} disabled={running} />
          <div class="rounded-xl border border-dashed border-gray-300 hover:border-primary-500 hover:bg-primary-50/30 p-6 text-center transition-colors cursor-pointer">
            <div class="text-3xl mb-2">&#128196;</div>
            <p class="font-semibold text-gray-800">{t.add_files}</p>
            <p class="text-xs text-gray-400 mt-1">{t.add_files_desc}</p>
          </div>
        </label>
      </div>
      <p class="text-xs text-gray-400 mb-4">{t.note_fsa}</p>
      {note && <p class="text-sm text-red-500 mb-4">{note}</p>}

      {/* Files table */}
      {rows.length > 0 && (
        <div class="bg-white rounded-xl border border-gray-200 overflow-hidden mb-6">
          <div class="px-4 py-3 bg-gray-50 flex items-center text-xs font-semibold text-gray-500">
            <span class="flex-1">{t.files_col}</span>
            <span class="w-24 text-right">{t.size_col}</span>
            <span class="w-24 text-right">{t.saved_col}</span>
            <span class="w-28 text-right">{t.result_col}</span>
          </div>
          <div class="max-h-80 overflow-y-auto divide-y divide-gray-100">
            {rows.map((r) => (
              <div key={r.id} class="px-4 py-2 flex items-center text-sm text-gray-700">
                <span class="flex-1 truncate pr-2" title={r.relPath}>
                  <span class="block truncate">{r.relPath}</span>
                  {r.error && <span class="block truncate text-xs text-red-500">{r.error}</span>}
                </span>
                <span class="w-24 text-right text-gray-500">{formatSize(r.size)}</span>
                <span class="w-24 text-right text-gray-400">
                  {r.resultSize !== undefined ? formatSize(r.resultSize) : ''}
                </span>
                <span class="w-28 text-right">
                  <span class={`font-medium ${STATUS_STYLES[r.status]}`}>{statusLabel(r.status)}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settings */}
      <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{t.format}</label>
            <select
              value={settings.format}
              onChange={(e) => set({ format: (e.target as HTMLSelectElement).value as BatchSettings['format'] })}
              class="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/30"
            >
              <option value="original">{t.original}</option>
              <option value="jpeg">JPEG</option>
              <option value="png">PNG</option>
              <option value="webp">WebP</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{t.quality}</label>
            <input
              type="range" min="1" max="100" value={settings.quality}
              onInput={(e) => set({ quality: parseInt((e.target as HTMLInputElement).value) })}
              class="w-full accent-primary-600"
            />
            <span class="text-xs text-gray-500">{settings.quality}</span>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{t.resize}</label>
            <select
              value={settings.resizeMethod}
              onChange={(e) => set({ resizeMethod: (e.target as HTMLSelectElement).value as ResizeMethod })}
              class="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="none">{t.resize_none}</option>
              <option value="fit">{t.resize_fit}</option>
              <option value="scale">{t.resize_scale}</option>
              <option value="cover">{t.resize_cover}</option>
              <option value="thumb">{t.resize_thumb}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{t.concurrency}</label>
            <select
              value={settings.concurrency}
              onChange={(e) => set({ concurrency: parseInt((e.target as HTMLSelectElement).value) })}
              class="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
            <p class="text-xs text-gray-400 mt-1">{t.concurrency_hint}</p>
          </div>
        </div>

        {settings.resizeMethod !== 'none' && (
          <div class="mt-3 flex flex-wrap items-end gap-4">
            {settings.resizeMethod === 'scale' ? (
              <div>
                <label class="block text-sm text-gray-500 mb-1">{t.percent}</label>
                <input
                  type="number" min="1" max="500" value={settings.resizePercent}
                  onInput={(e) => set({ resizePercent: parseInt((e.target as HTMLInputElement).value) || 100 })}
                  class="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                />
              </div>
            ) : (
              <>
                <div>
                  <label class="block text-sm text-gray-500 mb-1">{t.width}</label>
                  <input
                    type="number" min="1" value={settings.resizeWidth}
                    onInput={(e) => set({ resizeWidth: parseInt((e.target as HTMLInputElement).value) || 1 })}
                    class="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                  />
                </div>
                <div>
                  <label class="block text-sm text-gray-500 mb-1">{t.height}</label>
                  <input
                    type="number" min="1" value={settings.resizeHeight}
                    onInput={(e) => set({ resizeHeight: parseInt((e.target as HTMLInputElement).value) || 1 })}
                    class="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                  />
                </div>
              </>
            )}
          </div>
        )}

        <div class="mt-4 border-t border-gray-100 pt-3 flex flex-col gap-2 text-sm text-gray-700">
          {dirHandleRef.current && (
            <>
              <label class="flex items-center gap-2">
                <input type="checkbox" checked={settings.overwrite} onChange={(e) => set({ overwrite: (e.target as HTMLInputElement).checked })} /> {t.overwrite}
              </label>
              <label class="flex items-center gap-2">
                <input type="checkbox" checked={settings.skipProcessed} onChange={(e) => set({ skipProcessed: (e.target as HTMLInputElement).checked })} /> {t.skip_processed}
              </label>
              <div class="flex items-center gap-3 mt-1">
                <span class="font-medium">{t.output_mode}:</span>
                <label class="flex items-center gap-1">
                  <input type="radio" name="out" checked={settings.outputMode === 'same'} onChange={() => set({ outputMode: 'same' })} />{t.output_same}
                </label>
                <label class="flex items-center gap-1">
                  <input type="radio" name="out" checked={settings.outputMode === 'mirror'} onChange={() => set({ outputMode: 'mirror' })} />{t.output_mirror}
                </label>
              </div>
              {settings.outputMode === 'mirror' && (
                <input
                  type="text" value={settings.outputSubdir} placeholder={t.output_subdir}
                  onInput={(e) => set({ outputSubdir: (e.target as HTMLInputElement).value })}
                  class="w-64 border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* Progress */}
      {running && total > 0 && (
        <div class="mb-6">
          <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>{t.progress.replace('{done}', String(doneCount)).replace('{total}', String(total))}</span>
            <span>{t.speed.replace('{n}', String(speed))}</span>
          </div>
          <div class="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full bg-primary-600 transition-all duration-300" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}

      {/* Actions */}
      <div class="flex items-center gap-4 mb-6">
        {!running ? (
          <button
            onClick={start}
            disabled={rows.length === 0}
            class="px-6 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {t.start} ({total})
          </button>
        ) : (
          <button onClick={cancel} class="px-6 py-2.5 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors">
            {t.cancel}
          </button>
        )}
        {!running && finished && zipRef.current.length > 0 && (
          <button onClick={downloadZip} class="px-6 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors">
            {t.export_zip} ({zipRef.current.length})
          </button>
        )}
      </div>

      {!running && finished && total > 0 && (
        <div class="mb-6 text-sm text-gray-600">
          {t.done}: <span class="text-green-600">{ok}</span> {t.status_done},
          <span class="text-yellow-600"> {skipped}</span> {t.status_skipped},
          <span class="text-red-500"> {failed}</span> {t.status_error}
          {errorMessages.length > 0 && (
            <div class="mt-2 rounded-lg bg-red-50 border border-red-200 p-3">
              {errorMessages.slice(0, 5).map((m, i) => (
                <p key={i} class="text-xs text-red-600">{m}</p>
              ))}
              {errorMessages.length > 5 && (
                <p class="text-xs text-gray-400 mt-1">+{errorMessages.length - 5} more</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Recent batches */}
      {(dirs.length > 0 || history.length > 0) && (
        <section class="bg-white rounded-xl border border-gray-200 p-4">
          <h2 class="mb-3 text-lg font-semibold text-gray-900">{t.recent_title}</h2>
          {dirs.length > 0 && (
            <div class="mb-4">
              <p class="text-xs text-gray-500 mb-2">{t.choose_folder_desc}</p>
              <div class="flex flex-wrap gap-2">
                {dirs.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => openDir(d)}
                    disabled={running}
                    class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    {t.open} · {d.name}
                  </button>
                ))}
              </div>
            </div>
          )}
          {history.length > 0 ? (
            <div class="divide-y divide-gray-100">
              {history.slice(0, 10).map((h) => (
                <div key={h.id} class="py-2 flex items-center justify-between text-sm text-gray-600">
                  <span class="truncate">{new Date(h.date).toLocaleString()} · {h.dirName}</span>
                  <span class="shrink-0 text-gray-400">
                    {h.total} · <span class="text-green-600">{h.ok}</span> ok · <span class="text-yellow-600">{h.skipped}</span> · <span class="text-red-500">{h.failed}</span> · {formatSize(h.savedBytes)} {t.saved}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p class="text-sm text-gray-400">{t.no_history}</p>
          )}
        </section>
      )}
    </div>
  );
}

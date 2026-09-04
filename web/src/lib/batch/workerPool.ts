import type { CompressOptions } from '../compress/types';

export interface PoolTask {
  index: number;
  /** File-backed Blob reference (preferred for memory) or raw ArrayBuffer. */
  input: Blob | ArrayBuffer;
  /** Input size in bytes, used for memory-aware scheduling. */
  size: number;
  name: string;
  options: CompressOptions;
}

export interface PoolOutcome {
  index: number;
  data?: ArrayBuffer;
  format?: string;
  mimeType?: string;
  width?: number;
  height?: number;
  error?: string;
}

const LARGE_FILE_BYTES = 8 * 1024 * 1024;
const INFLIGHT_BUDGET_BYTES = 512 * 1024 * 1024;
const MAX_SMALL_CONCURRENCY = 4;

export interface WorkerPoolOptions {
  concurrency: number;
  onOutcome: (outcome: PoolOutcome) => void;
  onComplete?: (cancelled: boolean) => void;
}

interface WorkerSlot {
  worker: Worker;
  currentMsgId: number | null;
}

interface Inflight {
  task: PoolTask;
  msgId: number;
  slot: WorkerSlot;
}

/**
 * Memory-aware Web Worker pool.
 * - Concurrency is bounded by `options.concurrency`.
 * - Small files (< 8MB) run in parallel, capped at MAX_SMALL_CONCURRENCY.
 * - Large files (>= 8MB) run at most one at a time so multiple giant images
 *   never decode into memory simultaneously.
 * - A global in-flight byte budget guards total memory usage.
 */
export class WorkerPool {
  private slots: WorkerSlot[] = [];
  private queue: PoolTask[] = [];
  private inflight = new Map<number, Inflight>();
  private msgCounter = 0;
  private done = 0;
  private total = 0;
  private inflightBytes = 0;
  private inflightLarge = 0;
  private cancelled = false;
  private completed = false;

  constructor(private readonly options: WorkerPoolOptions) {}

  run(tasks: PoolTask[]): void {
    this.total = tasks.length;
    this.queue = tasks.slice();
    const spawnCount = Math.min(this.options.concurrency, tasks.length);
    for (let i = 0; i < spawnCount; i++) this.spawnSlot();
    this.tryDispatch();
  }

  private spawnSlot(): void {
    const worker = new Worker(new URL('../compress/worker.ts', import.meta.url), { type: 'module' });
    const slot: WorkerSlot = { worker, currentMsgId: null };
    worker.onmessage = (e) => this.handleMessage(slot, e);
    worker.onerror = () => this.handleWorkerError(slot);
    this.slots.push(slot);
  }

  private handleMessage(slot: WorkerSlot, e: MessageEvent): void {
    const resp = e.data as {
      id?: number;
      error?: string;
      data?: ArrayBuffer;
      format?: string;
      mimeType?: string;
      width?: number;
      height?: number;
    };
    let taskByIndex: PoolTask | undefined;
    if (typeof resp.id === 'number' && this.inflight.has(resp.id)) {
      const infl = this.inflight.get(resp.id)!;
      taskByIndex = infl.task;
      this.inflight.delete(resp.id);
      this.inflightBytes = Math.max(0, this.inflightBytes - infl.task.size);
      if (infl.task.size >= LARGE_FILE_BYTES) this.inflightLarge = Math.max(0, this.inflightLarge - 1);
      slot.currentMsgId = null;
    }
    this.done++;
    this.options.onOutcome({
      index: taskByIndex?.index ?? -1,
      data: resp.data,
      format: resp.format,
      mimeType: resp.mimeType,
      width: resp.width,
      height: resp.height,
      error: resp.error,
    });
    if (!this.cancelled) {
      this.tryDispatch();
    }
  }

  private handleWorkerError(slot: WorkerSlot): void {
    if (slot.currentMsgId != null) {
      const infl = this.inflight.get(slot.currentMsgId);
      if (infl) {
        this.inflight.delete(slot.currentMsgId);
        this.inflightBytes = Math.max(0, this.inflightBytes - infl.task.size);
        if (infl.task.size >= LARGE_FILE_BYTES) this.inflightLarge = Math.max(0, this.inflightLarge - 1);
        this.done++;
        this.options.onOutcome({ index: infl.task.index, error: 'Worker error' });
      }
    }
    slot.currentMsgId = null;
    const idx = this.slots.indexOf(slot);
    if (idx >= 0) this.slots.splice(idx, 1);
    slot.worker.terminate();
    if (!this.cancelled && this.slots.length < this.options.concurrency) {
      this.spawnSlot();
    }
    this.tryDispatch();
  }

  private tryDispatch(): void {
    if (this.cancelled) return;
    while (this.queue.length > 0) {
      const slot = this.slots.find((s) => s.currentMsgId === null);
      if (!slot) break;
      const taskIdx = this.findSchedulableIndex();
      if (taskIdx < 0) break;
      const task = this.queue[taskIdx];
      this.queue.splice(taskIdx, 1);
      const msgId = ++this.msgCounter;
      this.inflight.set(msgId, { task, msgId, slot });
      this.inflightBytes += task.size;
      if (task.size >= LARGE_FILE_BYTES) this.inflightLarge++;
      slot.currentMsgId = msgId;
      const payload: Record<string, unknown> = { id: msgId, options: task.options, input: task.input };
      const transfer: Transferable[] = [];
      if (task.input instanceof ArrayBuffer) transfer.push(task.input);
      slot.worker.postMessage(payload, transfer);
    }
    if (this.queue.length === 0 && this.inflight.size === 0 && !this.completed) {
      this.completed = true;
      this.cleanup();
      this.options.onComplete?.(false);
    }
  }

  private findSchedulableIndex(): number {
    for (let i = 0; i < this.queue.length; i++) {
      const t = this.queue[i];
      if (this.inflightBytes + t.size > INFLIGHT_BUDGET_BYTES) continue;
      if (t.size >= LARGE_FILE_BYTES) {
        if (this.inflightLarge < 1) return i;
      } else {
        let small = 0;
        for (const infl of this.inflight.values()) {
          if (infl.task.size < LARGE_FILE_BYTES) small++;
        }
        if (small < MAX_SMALL_CONCURRENCY) return i;
      }
    }
    return -1;
  }

  cancel(): void {
    if (this.cancelled || this.completed) return;
    this.cancelled = true;
    this.queue.length = 0;
    for (const s of this.slots) s.worker.terminate();
    this.slots = [];
    this.inflight.clear();
    if (!this.completed) {
      this.completed = true;
      this.options.onComplete?.(true);
    }
  }

  private cleanup(): void {
    for (const s of this.slots) s.worker.terminate();
    this.slots = [];
  }
}

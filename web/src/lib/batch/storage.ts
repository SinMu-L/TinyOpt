import type { BatchHistoryRecord } from './types';

const DB_NAME = 'tinyopt';
const DB_VERSION = 2;

const STORE_DIRS = 'dirs';
const STORE_HISTORY = 'history';
const STORE_MARKERS = 'markers';

let dbPromise: Promise<IDBDatabase> | null = null;

function openDb(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_DIRS)) {
        db.createObjectStore(STORE_DIRS, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORE_HISTORY)) {
        db.createObjectStore(STORE_HISTORY, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORE_MARKERS)) {
        db.createObjectStore(STORE_MARKERS);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

function tx<T>(store: string, mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return openDb().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const t = db.transaction(store, mode);
        const req = fn(t.objectStore(store));
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }),
  );
}

/* ─── Directory handles ─────────────────────────────────────── */

export interface DirRecord {
  id: string;
  name: string;
  date: number;
  handle: FileSystemDirectoryHandle;
}

export async function saveDir(record: DirRecord): Promise<void> {
  await tx(STORE_DIRS, 'readwrite', (s) => s.put(record));
}

export async function getDirs(): Promise<DirRecord[]> {
  return tx(STORE_DIRS, 'readonly', (s) => s.getAll() as IDBRequest<DirRecord[]>);
}

export async function removeDir(id: string): Promise<void> {
  await tx(STORE_DIRS, 'readwrite', (s) => s.delete(id));
}

/* ─── Batch history ─────────────────────────────────────────── */

export async function saveHistory(record: BatchHistoryRecord): Promise<void> {
  await tx(STORE_HISTORY, 'readwrite', (s) => s.put(record));
}

export async function getHistory(): Promise<BatchHistoryRecord[]> {
  return tx(STORE_HISTORY, 'readonly', (s) => s.getAll() as IDBRequest<BatchHistoryRecord[]>);
}

/* ─── Processed markers (cross-session "skip already-processed") ─── */

export function markerKey(relPath: string, size: number): string {
  return `${relPath}|${size}`;
}

export async function markProcessed(key: string): Promise<void> {
  await tx(STORE_MARKERS, 'readwrite', (s) => s.put(Date.now(), key));
}

export async function isProcessed(key: string): Promise<boolean> {
  const v = await tx(STORE_MARKERS, 'readonly', (s) => s.get(key));
  return v !== undefined;
}

export async function getProcessedKeys(): Promise<string[]> {
  const keys = await tx(STORE_MARKERS, 'readonly', (s) => s.getAllKeys() as IDBRequest<IDBValidKey[]>);
  return keys.map(String);
}
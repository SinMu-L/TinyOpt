import type { OutputFormat, ResizeMethod } from '../compress/types';

export interface BatchSettings {
  format: OutputFormat | 'original';
  quality: number;
  resizeMethod: ResizeMethod;
  resizeWidth: number;
  resizeHeight: number;
  resizePercent: number;
  concurrency: number;
  overwrite: boolean;
  skipProcessed: boolean;
  outputMode: 'same' | 'mirror';
  outputSubdir: string;
}

export interface SourceFile {
  /** Display name (file name with extension). */
  name: string;
  /** Relative path inside the picked/mirror root. */
  relPath: string;
  /** Size in bytes. */
  size: number;
}

export interface BatchResult {
  path: string;
  name: string;
  originalSize: number;
  compressedSize: number;
  format: OutputFormat;
  mimeType: string;
  status: 'ok' | 'error' | 'skipped';
  error?: string;
}

export interface BatchProgress {
  done: number;
  total: number;
  currentName: string;
  ok: number;
  failed: number;
  skipped: number;
}

export interface BatchHistoryRecord {
  id: string;
  dirName: string;
  dirId: string;
  date: number;
  total: number;
  ok: number;
  failed: number;
  skipped: number;
  savedBytes: number;
}

export interface DirectoryEntry {
  handle: FileSystemDirectoryHandle;
  name: string;
  root: string;
}
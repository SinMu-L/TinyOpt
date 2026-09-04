/**
 * File System Access API helpers. Provides real local-directory access on
 * desktop Chromium only. Everything degrades gracefully when unsupported.
 */

export interface DirFile {
  handle: FileSystemFileHandle;
  name: string;
  relPath: string;
  size: number;
}

export function isFsaSupported(): boolean {
  return typeof window !== 'undefined' && 'showDirectoryPicker' in window;
}

/** Open the directory picker in read-write mode. Throws on cancel (AbortError). */
export async function pickDirectory(readwrite = true): Promise<FileSystemDirectoryHandle> {
  const w = window as any;
  return w.showDirectoryPicker({ mode: readwrite ? 'readwrite' : 'read' });
}

export async function queryPermission(handle: FileSystemDirectoryHandle): Promise<PermissionState> {
  try {
    if ((handle as any).queryPermission) {
      return (await (handle as any).queryPermission({ mode: 'readwrite' })) as PermissionState;
    }
    return 'denied';
  } catch {
    return 'denied';
  }
}

export async function requestPermission(handle: FileSystemDirectoryHandle): Promise<PermissionState> {
  try {
    if ((handle as any).requestPermission) {
      return (await (handle as any).requestPermission({ mode: 'readwrite' })) as PermissionState;
    }
    return 'granted';
  } catch {
    return 'denied';
  }
}

const SUPPORTED_FILE_EXTS = [
  '.jpg', '.jpeg', '.png', '.webp', '.avif', '.bmp', '.gif', '.tiff', '.tif',
];

export function isSupportedImage(name: string): boolean {
  const lower = name.toLowerCase();
  return SUPPORTED_FILE_EXTS.some((ext) => lower.endsWith(ext));
}

/** Recursively walk a directory tree and collect image files with relative paths. */
export async function listFiles(dirHandle: FileSystemDirectoryHandle, relPath = ''): Promise<DirFile[]> {
  const out: DirFile[] = [];
  for await (const [name, handle] of (dirHandle as any).entries()) {
    const childRel = relPath ? `${relPath}/${name}` : name;
    if (handle.kind === 'directory') {
      out.push(...(await listFiles(handle, childRel)));
    } else if (handle.kind === 'file' && isSupportedImage(name)) {
      const file = await handle.getFile();
      out.push({ handle, name, relPath: childRel, size: file.size });
    }
  }
  return out;
}

/** Check whether a file exists at relPath under the directory. */
export async function existsFile(dirHandle: FileSystemDirectoryHandle, relPath: string): Promise<boolean> {
  try {
    await dirHandle.getFileHandle(relPath);
    return true;
  } catch {
    return false;
  }
}

/** Write data to a (possibly nested) path. Returns write status. */
export async function writeFile(
  dirHandle: FileSystemDirectoryHandle,
  relPath: string,
  data: ArrayBuffer | Blob,
  overwrite = true,
): Promise<'ok' | 'skipped' | 'error'> {
  try {
    const segments = relPath.split('/');
    const fileName = segments.pop()!;
    let current: FileSystemDirectoryHandle = dirHandle;
    for (const seg of segments) {
      current = await current.getDirectoryHandle(seg, { create: true });
    }
    if (!overwrite && (await existsFile(current, fileName))) {
      return 'skipped';
    }
    const fileHandle = await current.getFileHandle(fileName, { create: true });
    const writable = await (fileHandle as any).createWritable();
    await writable.write(data);
    await writable.close();
    return 'ok';
  } catch {
    return 'error';
  }
}

/** Remove a file at relPath (reserved for the future batch-rename tool). */
export async function removeFile(dirHandle: FileSystemDirectoryHandle, relPath: string): Promise<boolean> {
  try {
    const segments = relPath.split('/');
    const fileName = segments.pop()!;
    let current: FileSystemDirectoryHandle = dirHandle;
    for (const seg of segments) {
      current = await current.getDirectoryHandle(seg);
    }
    await current.removeEntry(fileName);
    return true;
  } catch {
    return false;
  }
}
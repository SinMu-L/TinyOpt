import JSZip from 'jszip';

export interface ZipItem {
  relPath: string;
  data: ArrayBuffer;
}

/** Bundle processed files into a zip and trigger a download (fallback for non-FSA browsers). */
export async function exportToZip(items: ZipItem[], zipName = 'tinyopt-batch.zip'): Promise<void> {
  const zip = new JSZip();
  for (const item of items) {
    zip.file(item.relPath, new Blob([item.data]));
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = zipName;
  a.click();
  URL.revokeObjectURL(url);
}

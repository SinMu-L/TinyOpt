import { getCodec } from './codecs/registry';
import type { CompressResponse, OutputFormat } from './types';

interface WorkerMessage {
  id: number;
  buffer: ArrayBuffer;
  format: OutputFormat;
  quality: number;
}

self.onmessage = async (e: MessageEvent<WorkerMessage>) => {
  const { id, buffer, format, quality } = e.data;

  try {
    if (typeof OffscreenCanvas === 'undefined') {
      self.postMessage({ id, error: 'Your browser does not support this tool. Please use Chrome, Edge, or Opera.' });
      return;
    }

    const blob = new Blob([buffer]);
    const bitmap = await createImageBitmap(blob);

    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(bitmap, 0, 0);
    const imageData = ctx.getImageData(0, 0, bitmap.width, bitmap.height);

    const codec = getCodec(format);
    const compressed = await codec.encode(imageData, quality, bitmap.width, bitmap.height);

    const response: CompressResponse = {
      id,
      data: compressed.buffer,
      originalSize: buffer.byteLength,
      compressedSize: compressed.byteLength,
      format,
      mimeType: codec.mimeType,
      width: bitmap.width,
      height: bitmap.height,
    };

    self.postMessage(response, { transfer: [compressed.buffer] });
    bitmap.close();
  } catch (err) {
    self.postMessage({ id, error: (err as Error).message || 'Compression failed' });
  }
};

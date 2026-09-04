import { getCodec } from './codecs/registry';
import type { CompressResponse, CompressOptions, OutputFormat, ResizeOptions } from './types';

/** Above this pixel count we skip imagequant for PNG and use lossless Canvas output. */
const MAX_QUANT_PIXELS = 8_000_000;

interface WorkerRequest {
  id: number;
  // New protocol passes a `File`/Blob reference (batch) or raw buffer (legacy single tool).
  input?: Blob;
  buffer?: ArrayBuffer;
  // New protocol (batch) uses `options`; legacy sends `format`/`quality` directly.
  options?: CompressOptions;
  format?: OutputFormat;
  quality?: number;
  resize?: ResizeOptions;
}

function computeTarget(srcW: number, srcH: number, resize?: ResizeOptions): { w: number; h: number } {
  const m = resize?.method;
  if (!m || m === 'none') {
    return { w: srcW, h: srcH };
  }
  if (m === 'scale') {
    const p = resize?.percent ?? 100;
    return {
      w: Math.max(1, Math.round((srcW * p) / 100)),
      h: Math.max(1, Math.round((srcH * p) / 100)),
    };
  }

  let bw = resize?.width;
  let bh = resize?.height;
  if (!bw && !bh) return { w: srcW, h: srcH };
  if (!bh) bh = Math.round((bw! * srcH) / srcW);
  if (!bw) bw = Math.round((bh! * srcW) / srcH);

  if (m === 'fit') {
    const scale = Math.min(bw / srcW, bh / srcH);
    return {
      w: Math.max(1, Math.round(srcW * scale)),
      h: Math.max(1, Math.round(srcH * scale)),
    };
  }

  // cover / thumb: fill exactly, center-crop
  return { w: bw, h: bh };
}

/** Center-crop source to exactly fill the target box (cover semantics). */
function drawCover(
  ctx: OffscreenCanvasRenderingContext2D,
  img: ImageBitmap,
  srcW: number,
  srcH: number,
  tgtW: number,
  tgtH: number,
): void {
  const srcRatio = srcW / srcH;
  const tgtRatio = tgtW / tgtH;
  let sw: number, sh: number, sx: number, sy: number;
  if (srcRatio > tgtRatio) {
    sh = srcH;
    sw = Math.round(srcH * tgtRatio);
    sx = Math.round((srcW - sw) / 2);
    sy = 0;
  } else {
    sw = srcW;
    sh = Math.round(srcW / tgtRatio);
    sx = 0;
    sy = Math.round((srcH - sh) / 2);
  }
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, tgtW, tgtH);
}

function applyResize(
  ctx: OffscreenCanvasRenderingContext2D,
  img: ImageBitmap,
  srcW: number,
  srcH: number,
  target: { w: number; h: number },
  resize?: ResizeOptions,
): void {
  const m = resize?.method;
  if (!m || m === 'none' || m === 'scale' || m === 'fit') {
    ctx.drawImage(img, 0, 0, target.w, target.h);
    return;
  }
  drawCover(ctx, img, srcW, srcH, target.w, target.h);
}

self.onmessage = async (e: MessageEvent<WorkerRequest>) => {
  const { id, input, buffer } = e.data;
  const options: CompressOptions = e.data.options ?? {
    format: e.data.format ?? 'jpeg',
    quality: e.data.quality ?? 80,
    resize: e.data.resize,
  };
  const sourceBytes = input?.size ?? buffer?.byteLength ?? 0;

  try {
    if (typeof OffscreenCanvas === 'undefined') {
      self.postMessage({ id, error: 'Your browser does not support this tool. Please use Chrome, Edge, or Opera.' });
      return;
    }

    if (!input && !buffer) {
      self.postMessage({ id, error: 'No input data' });
      return;
    }

    const blob = input ?? new Blob([buffer as ArrayBuffer]);
    const bitmap = await createImageBitmap(blob);
    const srcW = bitmap.width;
    const srcH = bitmap.height;

    const target = computeTarget(srcW, srcH, options.resize);
    const canvas = new OffscreenCanvas(target.w, target.h);
    const ctx = canvas.getContext('2d')!;
    applyResize(ctx, bitmap, srcW, srcH, target, options.resize);

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

    let compressed: Uint8Array;
    if (options.format === 'png' && canvas.width * canvas.height > MAX_QUANT_PIXELS) {
      const b = await canvas.convertToBlob({ type: 'image/png' });
      compressed = new Uint8Array(await b.arrayBuffer());
    } else {
      const codec = getCodec(options.format);
      compressed = await codec.encode(imageData, options.quality, canvas.width, canvas.height);
    }

    const response: CompressResponse = {
      id,
      data: compressed.buffer as ArrayBuffer,
      originalSize: sourceBytes,
      compressedSize: compressed.byteLength,
      format: options.format,
      mimeType: getCodec(options.format).mimeType,
      width: canvas.width,
      height: canvas.height,
    };

    self.postMessage(response, { transfer: [compressed.buffer] });
    bitmap.close();
  } catch (err) {
    self.postMessage({ id, error: (err as Error).message || 'Compression failed' });
  }
};
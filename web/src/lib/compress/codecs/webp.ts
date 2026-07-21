import type { Codec } from '../types';

const codec: Codec = {
  format: 'webp',
  extension: 'webp',
  mimeType: 'image/webp',
  supportsAlpha: true,

  async encode(imageData: ImageData, quality: number, width: number, height: number): Promise<Uint8Array> {
    const canvas = new OffscreenCanvas(width, height);
    const ctx = canvas.getContext('2d')!;
    ctx.putImageData(imageData, 0, 0);
    const blob = await canvas.convertToBlob({ type: 'image/webp', quality: quality / 100 });
    const buf = await blob.arrayBuffer();
    return new Uint8Array(buf);
  },
};

export default codec;

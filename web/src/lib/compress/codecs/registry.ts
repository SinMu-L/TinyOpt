import type { OutputFormat, Codec } from '../types';
import jpegCodec from './jpeg';
import pngCodec from './png';
import webpCodec from './webp';

const registry = new Map<OutputFormat, Codec>();

registry.set('jpeg', jpegCodec);
registry.set('png', pngCodec);
registry.set('webp', webpCodec);

export function getCodec(format: OutputFormat): Codec {
  const codec = registry.get(format);
  if (!codec) throw new Error(`Unsupported format: ${format}`);
  return codec;
}

export function getSupportedFormats(): OutputFormat[] {
  return Array.from(registry.keys());
}

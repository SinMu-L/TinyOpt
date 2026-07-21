export type OutputFormat = 'jpeg' | 'png' | 'webp';

export interface CompressOptions {
  format: OutputFormat;
  quality: number;
}

export interface CompressRequest {
  id: number;
  buffer: ArrayBuffer;
  options: CompressOptions;
}

export interface CompressResponse {
  id: number;
  data: ArrayBuffer;
  originalSize: number;
  compressedSize: number;
  format: OutputFormat;
  mimeType: string;
  width: number;
  height: number;
}

export interface Codec {
  readonly format: OutputFormat;
  readonly extension: string;
  readonly mimeType: string;
  readonly supportsAlpha: boolean;
  encode(imageData: ImageData, quality: number, width: number, height: number): Promise<Uint8Array>;
}

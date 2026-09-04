export type OutputFormat = 'jpeg' | 'png' | 'webp';

export type ResizeMethod = 'none' | 'fit' | 'scale' | 'cover' | 'thumb';

export interface ResizeOptions {
  method: ResizeMethod;
  width?: number;
  height?: number;
  percent?: number;
}

export interface CompressOptions {
  format: OutputFormat;
  quality: number;
  resize?: ResizeOptions;
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
  error?: string;
}

export interface Codec {
  readonly format: OutputFormat;
  readonly extension: string;
  readonly mimeType: string;
  readonly supportsAlpha: boolean;
  encode(imageData: ImageData, quality: number, width: number, height: number): Promise<Uint8Array>;
}
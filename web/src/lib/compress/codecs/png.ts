import type { Codec } from '../types';

let wasmExports: any = null;
let initPromise: Promise<any> | null = null;

async function ensureWasm(): Promise<any> {
  if (wasmExports) return wasmExports;
  if (!initPromise) {
    initPromise = (async () => {
      const response = await fetch('/codecs/imagequant_bg.wasm');
      let instance: WebAssembly.Instance;

      try {
        const result = await WebAssembly.instantiateStreaming(response, {
          wbg: {
            __wbg_buffer_609cc3eee51ed158: (arg0: any) => arg0.buffer,
            __wbg_new_405e22f390576ce2: () => ({}),
            __wbg_new_a12002a7f91c75be: (arg0: any) => new Uint8Array(arg0),
            __wbg_newwithbyteoffsetandlength_d97e637ebe145a9a: (arg0: any, arg1: number, arg2: number) =>
              new Uint8Array(arg0, arg1 >>> 0, arg2 >>> 0),
            __wbg_set_bb8cecf6a62b9f46: (_arg0: any, _arg1: any, _arg2: any) => {
              try { return Reflect.set(_arg0, _arg1, _arg2); } catch (e) { return e; }
            },
            __wbindgen_error_new: (_arg0: number, _arg1: number) => new Error(),
            __wbindgen_init_externref_table: function () {
              const table = (instance.exports as any).__wbindgen_export_2 as WebAssembly.Table;
              const offset = table.grow(4);
              table.set(0, undefined);
              table.set(offset + 0, undefined);
              table.set(offset + 1, null);
              table.set(offset + 2, true);
              table.set(offset + 3, false);
            },
            __wbindgen_memory: () => (instance.exports as any).memory,
            __wbindgen_string_new: () => '',
            __wbindgen_throw: (ptr: number, len: number) => {
              let msg = '';
              try {
                msg = new TextDecoder('utf-8').decode(new Uint8Array((instance.exports as any).memory.buffer, ptr >>> 0, len >>> 0));
              } catch {
                // keep the fallback message below
              }
              throw new Error('imagequant error' + (msg ? `: ${msg}` : ''));
            },
          },
        });
        instance = result.instance;
      } catch {
        const bytes = await response.clone().arrayBuffer();
        const result = await WebAssembly.instantiate(bytes, {
          wbg: {
            __wbg_buffer_609cc3eee51ed158: (arg0: any) => arg0.buffer,
            __wbg_new_405e22f390576ce2: () => ({}),
            __wbg_new_a12002a7f91c75be: (arg0: any) => new Uint8Array(arg0),
            __wbg_newwithbyteoffsetandlength_d97e637ebe145a9a: (arg0: any, arg1: number, arg2: number) =>
              new Uint8Array(arg0, arg1 >>> 0, arg2 >>> 0),
            __wbg_set_bb8cecf6a62b9f46: (_arg0: any, _arg1: any, _arg2: any) => {
              try { return Reflect.set(_arg0, _arg1, _arg2); } catch (e) { return e; }
            },
            __wbindgen_error_new: (_arg0: number, _arg1: number) => new Error(),
            __wbindgen_init_externref_table: function () {
              const table = (instance.exports as any).__wbindgen_export_2 as WebAssembly.Table;
              const offset = table.grow(4);
              table.set(0, undefined);
              table.set(offset + 0, undefined);
              table.set(offset + 1, null);
              table.set(offset + 2, true);
              table.set(offset + 3, false);
            },
            __wbindgen_memory: () => (instance.exports as any).memory,
            __wbindgen_string_new: () => '',
            __wbindgen_throw: (ptr: number, len: number) => {
              let msg = '';
              try {
                msg = new TextDecoder('utf-8').decode(new Uint8Array((instance.exports as any).memory.buffer, ptr >>> 0, len >>> 0));
              } catch {
                // keep the fallback message below
              }
              throw new Error('imagequant error' + (msg ? `: ${msg}` : ''));
            },
          },
        });
        instance = result;
      }

      (instance.exports as any).__wbindgen_start();
      return instance.exports;
    })();
  }
  wasmExports = await initPromise;
  return wasmExports;
}

function allocBuffer(wasm: any, data: Uint8Array): number {
  const ptr = (wasm.__wbindgen_malloc as (size: number, align: number) => number)(data.length, 1) >>> 0;
  new Uint8Array(wasm.memory.buffer).set(data, ptr);
  return ptr;
}

function passArray8(wasm: any, data: Uint8Array): { ptr: number; len: number } {
  const ptr = allocBuffer(wasm, data);
  return { ptr, len: data.length };
}

function getUint8FromWasm(wasm: any, ptr: number, len: number): Uint8Array {
  return new Uint8Array(wasm.memory.buffer, ptr, len).slice();
}

function quantizeImage(wasm: any, pixels: Uint8Array, width: number, height: number, maxColors: number): number {
  const { ptr, len } = passArray8(wasm, pixels);
  const ret = (wasm.quantize_image as (ptr: number, len: number, w: number, h: number, mc: number) => number[])(ptr, len, width, height, maxColors);
  return ret[0];
}

function remapPaletteToRGBA(
  wasm: any,
  resultPtr: number,
  imgWidth: number,
  imgHeight: number,
): Uint8ClampedArray {
  const palettePtr = (wasm.quantresult_palette_ptr as (p: number) => number)(resultPtr);
  const paletteLen = (wasm.quantresult_palette_len as (p: number) => number)(resultPtr);
  const indicesPtr = (wasm.quantresult_indices_ptr as (p: number) => number)(resultPtr);
  const indicesLen = (wasm.quantresult_indices_len as (p: number) => number)(resultPtr);

  const memoryBuf = wasm.memory.buffer;
  const palette = new Uint8Array(memoryBuf, palettePtr, paletteLen);
  const indices = new Uint8Array(memoryBuf, indicesPtr, indicesLen);

  const pixelCount = imgWidth * imgHeight;
  const rgba = new Uint8ClampedArray(pixelCount * 4);

  for (let i = 0; i < pixelCount && i < indicesLen; i++) {
    const colorIdx = indices[i] * 4;
    const outIdx = i * 4;
    rgba[outIdx] = palette[colorIdx] ?? 0;
    rgba[outIdx + 1] = palette[colorIdx + 1] ?? 0;
    rgba[outIdx + 2] = palette[colorIdx + 2] ?? 0;
    rgba[outIdx + 3] = 255;
  }

  return rgba;
}

function freeQuantResult(wasm: any, ptr: number): void {
  (wasm.__wbg_quantresult_free as (p: number, flag: number) => void)(ptr, 0);
}

const codec: Codec = {
  format: 'png',
  extension: 'png',
  mimeType: 'image/png',
  supportsAlpha: true,

  async encode(imageData: ImageData, quality: number, width: number, height: number): Promise<Uint8Array> {
    try {
      const wasm = await ensureWasm();

      const maxColors = Math.max(2, Math.min(256, Math.round(256 * quality / 100)));
      const { data } = imageData;

      const resultPtr = quantizeImage(wasm, new Uint8Array(data.buffer, data.byteOffset, data.byteLength), width, height, maxColors);
      if (!resultPtr) return fallbackPng(imageData, width, height);

      const paletteLen = (wasm.quantresult_palette_len as (p: number) => number)(resultPtr);
      const indicesLen = (wasm.quantresult_indices_len as (p: number) => number)(resultPtr);
      if (paletteLen === 0 || indicesLen === 0) return fallbackPng(imageData, width, height);

      const rgba = remapPaletteToRGBA(wasm, resultPtr, width, height);
      try { freeQuantResult(wasm, resultPtr); } catch { /* glue mismatch — leak it */ }

      const id = new ImageData(rgba, width, height);
      const canvas = new OffscreenCanvas(width, height);
      const ctx = canvas.getContext('2d')!;
      ctx.putImageData(id, 0, 0);
      const blob = await canvas.convertToBlob({ type: 'image/png' });
      const buf = await blob.arrayBuffer();
      return new Uint8Array(buf);
    } catch {
      // imagequant can fail or return empty on edge-case images / glue mismatch —
      // fall back to a lossless canvas PNG so the file still processes.
      return fallbackPng(imageData, width, height);
    }
  },
};

async function fallbackPng(imageData: ImageData, width: number, height: number): Promise<Uint8Array> {
  const canvas = new OffscreenCanvas(width, height);
  const ctx = canvas.getContext('2d')!;
  ctx.putImageData(imageData, 0, 0);
  const blob = await canvas.convertToBlob({ type: 'image/png' });
  return new Uint8Array(await blob.arrayBuffer());
}

export default codec;

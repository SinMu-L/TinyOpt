import { useState, useEffect, useRef, useCallback } from 'preact/hooks';

type OutputFormat = 'jpeg' | 'png' | 'webp';
type Status = 'idle' | 'processing' | 'done' | 'error';

interface CompressResult {
  data: ArrayBuffer;
  originalSize: number;
  compressedSize: number;
  format: OutputFormat;
  mimeType: string;
}

const FORMAT_LABELS: Record<OutputFormat, string> = {
  jpeg: 'JPEG',
  png: 'PNG',
  webp: 'WebP',
};

const FORMAT_EXTENSIONS: Record<OutputFormat, string> = {
  jpeg: '.jpg',
  png: '.png',
  webp: '.webp',
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatPercent(saved: number): string {
  return `${saved > 0 ? '-' : ''}${Math.abs(saved).toFixed(1)}%`;
}

export default function CompressTool() {
  const [file, setFile] = useState<File | null>(null);
  const [ogUrl, setOgUrl] = useState<string>('');
  const [format, setFormat] = useState<OutputFormat>('jpeg');
  const [quality, setQuality] = useState(80);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');
  const [result, setResult] = useState<CompressResult | null>(null);
  const [cmpUrl, setCmpUrl] = useState<string>('');
  const workerRef = useRef<Worker | null>(null);
  const msgIdRef = useRef(0);
  const pendingRef = useRef(false);

  useEffect(() => {
    const worker = new Worker(
      new URL('../lib/compress/worker.ts', import.meta.url),
      { type: 'module' }
    );
    worker.onmessage = (e) => {
      pendingRef.current = false;
      if (e.data.error) {
        setStatus('error');
        setError(e.data.error);
        return;
      }
      const res: CompressResult = {
        data: e.data.data,
        originalSize: e.data.originalSize,
        compressedSize: e.data.compressedSize,
        format: e.data.format as OutputFormat,
        mimeType: e.data.mimeType,
      };
      setResult(res);
      if (cmpUrl) URL.revokeObjectURL(cmpUrl);
      const blob = new Blob([res.data], { type: res.mimeType });
      setCmpUrl(URL.createObjectURL(blob));
      setStatus('done');
    };
    worker.onerror = () => {
      pendingRef.current = false;
      setStatus('error');
      setError('Worker error');
    };
    workerRef.current = worker;
    return () => { worker.terminate(); };
  }, []);

  const doCompress = useCallback((f: File, fmt: OutputFormat, q: number) => {
    if (!workerRef.current) return;
    if (pendingRef.current) return;
    pendingRef.current = true;
    setStatus('processing');
    setError('');
    const reader = new FileReader();
    reader.onload = () => {
      const id = ++msgIdRef.current;
      workerRef.current!.postMessage({
        id,
        buffer: reader.result as ArrayBuffer,
        format: fmt,
        quality: q,
      }, { transfer: [(reader.result as ArrayBuffer)] });
    };
    reader.readAsArrayBuffer(f);
  }, []);

  useEffect(() => {
    if (file && result === null) {
      doCompress(file, format, quality);
    }
  }, [file]);

  useEffect(() => {
    if (file && result) {
      const timer = setTimeout(() => doCompress(file, format, quality), 300);
      return () => clearTimeout(timer);
    }
  }, [format, quality]);

  const handleFile = (f: File | null) => {
    if (!f) return;
    if (!f.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    if (ogUrl) URL.revokeObjectURL(ogUrl);
    if (cmpUrl) URL.revokeObjectURL(cmpUrl);
    setFile(f);
    setOgUrl(URL.createObjectURL(f));
    setResult(null);
    setCmpUrl('');
    setError('');
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer?.files?.[0];
    handleFile(f ?? null);
  };

  const handleInput = (e: Event) => {
    const input = e.target as HTMLInputElement;
    handleFile(input.files?.[0] ?? null);
  };

  const handleDownload = () => {
    if (!result || !file) return;
    const ext = FORMAT_EXTENSIONS[result.format];
    const name = file.name.replace(/\.[^.]+$/, '') + ext;
    const blob = new Blob([result.data], { type: result.mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const savedPercent = result
    ? ((1 - result.compressedSize / result.originalSize) * 100)
    : 0;

  return (
    <div class="w-full max-w-6xl mx-auto px-4 py-8">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Online Image Compressor</h1>
        <p class="text-gray-500">Compress JPEG, PNG, WebP images directly in your browser</p>
      </div>

      {/* Upload Area */}
      {!file && (
        <div
          class="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50/30 transition-colors"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <div class="text-4xl mb-3 text-gray-400">&#128247;</div>
          <p class="text-gray-600 font-medium">Click or drag an image here</p>
          <p class="text-gray-400 text-sm mt-1">Supports PNG, JPEG, WebP, AVIF, GIF, BMP, TIFF</p>
          <input
            id="file-input"
            type="file"
            accept="image/*"
            class="hidden"
            onChange={handleInput}
          />
        </div>
      )}

      {/* Controls */}
      {file && (
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Original */}
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-gray-800">Original</h3>
              <button
                class="text-sm text-primary-600 hover:text-primary-700 font-medium"
                onClick={() => { setFile(null); setResult(null); }}
              >
                Change Image
              </button>
            </div>
            <div class="aspect-video bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
              <img src={ogUrl} alt="Original" class="max-w-full max-h-full object-contain" />
            </div>
            <div class="mt-2 flex items-center gap-3 text-sm text-gray-500">
              <span>{file.name}</span>
              <span>{formatSize(file.size)}</span>
            </div>
          </div>

          {/* Right: Result */}
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-gray-800">Compressed</h3>
              {status === 'done' && savedPercent > 0 && (
                <span class="text-sm font-semibold text-green-600">
                  {formatPercent(savedPercent)}
                </span>
              )}
              {status === 'done' && savedPercent <= 0 && (
                <span class="text-sm text-gray-400">No reduction</span>
              )}
            </div>
            <div class="aspect-video bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden relative">
              {status === 'processing' && (
                <div class="absolute inset-0 bg-white/60 flex items-center justify-center">
                  <div class="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
              {status === 'done' && cmpUrl && (
                <img src={cmpUrl} alt="Compressed" class="max-w-full max-h-full object-contain" />
              )}
              {status === 'error' && (
                <p class="text-red-500 text-sm">{error}</p>
              )}
              {status === 'idle' && !cmpUrl && (
                <p class="text-gray-400 text-sm">Processing...</p>
              )}
            </div>
            {result && (
              <div class="mt-2 flex items-center justify-between text-sm">
                <span class="text-gray-500">{formatSize(result.compressedSize)}</span>
                <button
                  onClick={handleDownload}
                  class="px-4 py-1.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
                >
                  Download
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Settings */}
      {file && (
        <div class="mt-6 bg-white rounded-xl border border-gray-200 p-4">
          <div class="flex flex-wrap items-center gap-6">
            {/* Format */}
            <div class="flex items-center gap-2">
              <label class="text-sm font-medium text-gray-700">Format:</label>
              <select
                value={format}
                onChange={(e) => setFormat((e.target as HTMLSelectElement).value as OutputFormat)}
                class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500"
              >
                <option value="jpeg">JPEG</option>
                <option value="png">PNG</option>
                <option value="webp">WebP</option>
              </select>
            </div>

            {/* Quality */}
            <div class="flex items-center gap-2 flex-1 min-w-[200px]">
              <label class="text-sm font-medium text-gray-700 shrink-0">Quality:</label>
              <input
                type="range"
                min="1"
                max="100"
                value={quality}
                onInput={(e) => setQuality(parseInt((e.target as HTMLInputElement).value))}
                class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <span class="text-sm font-mono text-gray-600 w-8 text-right">{quality}</span>
            </div>
          </div>

          {/* Format-specific notes */}
          {format === 'png' && (
            <p class="mt-3 text-xs text-gray-400">
              PNG uses color quantization — lower quality = fewer colors = smaller file.
              The image will always be full resolution and sharp, just with a reduced color palette.
            </p>
          )}
          {format === 'jpeg' && (
            <p class="mt-3 text-xs text-gray-400">
              JPEG removes fine details at lower quality settings. Quality 80+ is recommended for photos.
            </p>
          )}
          {format === 'webp' && (
            <p class="mt-3 text-xs text-gray-400">
              WebP offers better compression than JPEG/PNG. Supports both lossy and lossless modes.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
